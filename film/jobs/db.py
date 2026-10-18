"""SQLAlchemy 数据模型 + 队列持久化（slice 3）。

对齐 docs/designs/数据模型.md 二、任务与可靠性表。JSON 用 SQLAlchemy JSON 类型
（PG 落 JSONB，SQLite 落 TEXT）。SKIP LOCKED 并发 SQL 见 film/jobs/sql.py。
"""
import datetime as _dt

from sqlalchemy import DateTime, Float, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from . import state_machine


class Base(DeclarativeBase):
    pass


def _now():
    return _dt.datetime.utcnow()


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("project_id", "idempotency_key", name="uq_jobs_idem"),
        Index("ix_jobs_status_available", "status", "available_at"),
        Index("ix_jobs_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False)
    episode_id: Mapped[int] = mapped_column(Integer, nullable=True)
    shot_id: Mapped[int] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(64), nullable=True)
    error_class: Mapped[str] = mapped_column(String(32), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    attempt_limit: Mapped[int] = mapped_column(Integer, default=2)
    available_at: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[int] = mapped_column(Integer, nullable=True)
    lease_epoch: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str] = mapped_column(String(512), nullable=False)
    provider_task_id: Mapped[str] = mapped_column(String(128), nullable=True)
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Project(Base):
    """立项（M1）。"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    logline: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=True)
    rating: Mapped[str] = mapped_column(String(16), nullable=True)
    genre: Mapped[str] = mapped_column(String(64), nullable=True)
    style: Mapped[str] = mapped_column(String(32), nullable=True)
    episodes: Mapped[int] = mapped_column(Integer, nullable=True)
    minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    episode_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    source_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    delivery_spec: Mapped[dict] = mapped_column(JSON, default=dict)
    pilot_mode: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Shot(Base):
    """镜头（M4 分镜表 + M5 契约字段）。"""
    __tablename__ = "shots"
    __table_args__ = (
        Index("ix_shots_project_episode", "project_id", "episode_id", "shot_no"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_id: Mapped[int] = mapped_column(Integer, nullable=True)
    shot_no: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_no: Mapped[int] = mapped_column(Integer, nullable=True)
    size: Mapped[str] = mapped_column(String(8), nullable=True)
    angle: Mapped[str] = mapped_column(String(16), nullable=True)
    move: Mapped[str] = mapped_column(String(8), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    characters: Mapped[dict] = mapped_column(JSON, default=list)
    dialogue: Mapped[str] = mapped_column(String(512), nullable=True)
    prompt: Mapped[str] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="待生成")
    image_key: Mapped[str] = mapped_column(String(256), nullable=True)
    continuity: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class Candidate(Base):
    """镜头生成候选（抽卡，M5.1/F02 多候选 + 选择位）。"""
    __tablename__ = "candidates"
    __table_args__ = (Index("ix_candidates_shot", "shot_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    image_key: Mapped[str] = mapped_column(String(256), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    selected: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class Script(Base):
    """剧本（M2）：Step Outline 场次 + 结构校验状态。"""
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_id: Mapped[int] = mapped_column(Integer, nullable=True)
    form: Mapped[str] = mapped_column(String(16), nullable=True)
    scenes: Mapped[dict] = mapped_column(JSON, default=list)
    structure: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class PlaygroundTask(Base):
    """Playground 独立生成任务（图像/视频/音频，无需项目上下文）。"""
    __tablename__ = "playground_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    prompt: Mapped[str] = mapped_column(String(1024), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="已完成")
    result_key: Mapped[str] = mapped_column(String(256), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class Character(Base):
    """角色（M3 选角：锚点图集 + 音色绑定 + 定妆门禁）。"""
    __tablename__ = "characters"
    __table_args__ = (Index("ix_characters_project", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    voice_key: Mapped[str] = mapped_column(String(64), nullable=True)
    anchors: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="待定妆")
    source_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class ProviderCall(Base):
    """供应商调用记录（M17.5-F02：提交/查询/下载三段式）。"""
    __tablename__ = "provider_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    stage: Mapped[str] = mapped_column(String(16), nullable=False)  # 提交/查询/下载
    status: Mapped[str] = mapped_column(String(16), default="成功")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class ModuleParams(Base):
    """项目级模块参数（每个模块的关键输入，未填用推荐默认值）。"""
    __tablename__ = "module_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ProjectModelRoute(Base):
    """项目级模型路由：覆盖全局供应商的 model/api_url（Key 仍取全局配置）。"""
    __tablename__ = "project_model_routes"
    __table_args__ = (UniqueConstraint("project_id", "kind", name="uq_project_model_kind"),
                      Index("ix_project_model_project", "project_id"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=True)
    api_url: Mapped[str] = mapped_column(String(256), nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class SubtitleTrack(Base):
    """字幕轨：项目/分集/语言 + 状态 + 时间轴文本（SRT 可导入导出）。"""
    __tablename__ = "subtitle_tracks"
    __table_args__ = (UniqueConstraint("project_id", "episode_id", "language",
                                       name="uq_subtitle_track"),
                      Index("ix_subtitles_project", "project_id"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_id: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    source_language: Mapped[str] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="待翻译")
    cues: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Distribution(Base):
    """分发记录：项目 → 渠道，排期/发布状态与运营数据（未接平台 API 时为 Mock）。"""
    __tablename__ = "distributions"
    __table_args__ = (Index("ix_distributions_project", "project_id"),
                      Index("ix_distributions_channel", "channel_key"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_key: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="待排期")
    scheduled_at: Mapped[_dt.datetime] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[_dt.datetime] = mapped_column(DateTime, nullable=True)
    external_url: Mapped[str] = mapped_column(String(512), nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class HitCase(Base):
    """爆款案例库：题材、配方、钩子/断章结构、热度备注与来源说明。"""
    __tablename__ = "hit_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), default="红果漫剧")
    genre: Mapped[str] = mapped_column(String(64), nullable=True)
    heat_note: Mapped[str] = mapped_column(String(512), nullable=True)
    play_count: Mapped[int] = mapped_column(Integer, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False)
    formula: Mapped[str] = mapped_column(String(32), nullable=True)
    hook_type: Mapped[str] = mapped_column(String(32), nullable=True)
    cliffhanger_type: Mapped[str] = mapped_column(String(32), nullable=True)
    structure: Mapped[dict] = mapped_column(JSON, default=dict)
    visual: Mapped[str] = mapped_column(String(512), nullable=True)
    why_text: Mapped[str] = mapped_column(String(1024), nullable=True)
    source_note: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Settlement(Base):
    """商业化结算台账：IAP/IAA/订阅/分成（本地登记，未接平台财务 API）。"""
    __tablename__ = "settlements"
    __table_args__ = (Index("ix_settlements_project", "project_id"),
                      Index("ix_settlements_channel", "channel_key"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_key: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(64), nullable=False)
    revenue_type: Mapped[str] = mapped_column(String(16), default="IAP")
    amount: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    period: Mapped[str] = mapped_column(String(7), nullable=True)
    note: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class User(Base):
    """平台用户与角色（多用户登录、权限控制）。"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="writer")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Template(Base):
    """模板/提示词库：分镜、运镜、风格、对白等可复用模板。"""
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="分镜")
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Review(Base):
    """审核记录：项目/剧集/镜头/交付的提交、通过、驳回与意见。"""
    __tablename__ = "reviews"
    __table_args__ = (Index("ix_reviews_project", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), default="project")
    target_ref: Mapped[str] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="待审")
    reviewer: Mapped[str] = mapped_column(String(64), nullable=True)
    comment: Mapped[str] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Novel(Base):
    """导入的小说原文（TXT）：用于小说改编立项与后续拆章。"""
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=True)
    title: Mapped[str] = mapped_column(String(128), nullable=True)
    author: Mapped[str] = mapped_column(String(128), nullable=True)
    chapters: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    encoding: Mapped[str] = mapped_column(String(32), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class ModelConfig(Base):
    """模型供应商配置（G2）：明文存库；API 永不回传明文（见 /api/models/config）。"""
    __tablename__ = "model_configs"

    kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    model: Mapped[str] = mapped_column(String(128), nullable=True)
    api_url: Mapped[str] = mapped_column(String(256), nullable=True)
    api_key: Mapped[str] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Run(Base):
    """流水线运行记录（每次 run_pipeline 落一行，供工作台回看）。"""
    __tablename__ = "runs"
    __table_args__ = (Index("ix_runs_project", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class Intent(Base):
    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    client_op_id: Mapped[str] = mapped_column(String(128), nullable=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_frozen: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="intended")
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Outbox(Base):
    __tablename__ = "outbox"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_outbox_idem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(512), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[_dt.datetime] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[_dt.datetime] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[_dt.datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, default=_now)


class QueueError(Exception):
    """队列持久化操作非法。"""


class SqlQueue:
    """SQLAlchemy 持久化队列（portable 语义；SKIP LOCKED 并发 SQL 见 sql.py）。"""

    def __init__(self, session_factory, lease_sec=90 * 60):
        self.session_factory = session_factory
        self.lease_sec = lease_sec

    def enqueue(self, **job):
        """幂等入队：同 (project_id, idempotency_key) 已存在则返回既有（不复活）。"""
        from sqlalchemy import select
        with self.session_factory() as s:
            existing = s.scalars(select(Job).where(
                Job.project_id == job["project_id"],
                Job.idempotency_key == job["idempotency_key"])).first()
            if existing:
                return existing
            row = Job(**job)
            s.add(row)
            s.commit()
            return row

    def claim(self, now=0):
        from sqlalchemy import select
        with self.session_factory() as s:
            row = s.scalars(select(Job).where(
                Job.status == "queued", Job.available_at <= now)
                .order_by(Job.priority.desc(), Job.id.asc()).limit(1)).first()
            if row is None:
                return None
            row.status = "running"
            row.attempts += 1
            row.lease_epoch += 1
            row.locked_until = now + self.lease_sec
            s.commit()
            return row

    def _fenced(self, s, job_id, epoch):
        row = s.get(Job, job_id)
        if row is None:
            raise QueueError("任务不存在：%s" % (job_id,))
        if epoch != row.lease_epoch:
            raise QueueError("fencing 拒绝：epoch=%s 当前=%s" % (epoch, row.lease_epoch))
        return row

    def heartbeat(self, job_id, epoch, now):
        with self.session_factory() as s:
            row = self._fenced(s, job_id, epoch)
            row.locked_until = now + self.lease_sec
            s.commit()
            return row

    def complete(self, job_id, epoch, checkpoint=None):
        with self.session_factory() as s:
            row = self._fenced(s, job_id, epoch)
            state_machine.require_transition(row.status, "completed")
            row.status = "completed"
            if checkpoint is not None:
                row.checkpoint = checkpoint
            s.commit()
            return row

    def fail(self, job_id, epoch, error_class, error_code=None):
        with self.session_factory() as s:
            row = self._fenced(s, job_id, epoch)
            state_machine.require_transition(row.status, "failed")
            row.status = "failed"
            row.error_class = error_class
            row.error_code = error_code
            s.commit()
            return row

    def cancel(self, job_id, epoch):
        with self.session_factory() as s:
            row = self._fenced(s, job_id, epoch)
            state_machine.require_transition(row.status, "cancelled")
            row.status = "cancelled"
            s.commit()
            return row

    def wait_human(self, job_id, epoch):
        """门禁阻塞任务（M13.5-F01）：running → waiting_human，释放租约。"""
        with self.session_factory() as s:
            row = self._fenced(s, job_id, epoch)
            state_machine.require_transition(row.status, "waiting_human")
            row.status = "waiting_human"
            row.locked_until = None
            s.commit()
            return row

    def resolve_human(self, job_id, approve, reason_code=None):
        """人工裁决：通过→completed；驳回→failed(gate_rejected)。"""
        with self.session_factory() as s:
            row = s.get(Job, job_id)
            if row is None:
                raise QueueError("任务不存在：%s" % (job_id,))
            state_machine.require_transition(row.status, "completed" if approve else "failed")
            if approve:
                row.status = "completed"
            else:
                row.status = "failed"
                row.error_class = "gate_rejected"
                row.error_code = reason_code
            s.commit()
            return row

    def reclaim_stale(self, now):
        from sqlalchemy import select
        with self.session_factory() as s:
            rows = s.scalars(select(Job).where(
                Job.status == "running", Job.locked_until < now)).all()
            ids = []
            for row in rows:
                cp = row.checkpoint or {}
                if cp.get("produced_keys"):
                    row.status = "completed"
                elif row.attempts < row.attempt_limit + 1:
                    row.status = "queued"
                    row.lease_epoch += 1
                else:
                    row.status = "retry_exhausted"
                ids.append(row.id)
            s.commit()
            return ids
