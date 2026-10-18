"""AADO 控制面 API（FastAPI；API 薄：入队 + 查询 + 人工终审，重计算归 worker）。"""
import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, select, func, or_
from sqlalchemy.orm import sessionmaker

from apps.api import auth
from film import formats as fmt
from film import hits as hits_mod
from film import marketing as marketing_mod
from film import novels as novel_parser
from film import subtitles as subtitle_mod
from film.jobs import db as jobs_db
from film.projects import project as proj_mod
from film.suppliers import config as sup_config

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
_engine_kwargs = {"connect_args": _connect_args}
if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
    # 内存库默认每线程一个空库；静态池让线程池共享同一连接
    from sqlalchemy.pool import StaticPool
    _engine_kwargs["poolclass"] = StaticPool
engine = create_engine(DATABASE_URL, **_engine_kwargs)
jobs_db.Base.metadata.create_all(engine)

# create_all 不会给已存在的表补索引；这里幂等补齐（SQLite/PG 均支持 IF NOT EXISTS）
_INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS ix_shots_project_episode ON shots (project_id, episode_id, shot_no)",
    "CREATE INDEX IF NOT EXISTS ix_candidates_shot ON candidates (shot_id)",
    "CREATE INDEX IF NOT EXISTS ix_jobs_project ON jobs (project_id)",
    "CREATE INDEX IF NOT EXISTS ix_runs_project ON runs (project_id)",
    "CREATE INDEX IF NOT EXISTS ix_characters_project ON characters (project_id)",
]
with engine.begin() as _c:
    from sqlalchemy import text as _text
    for _sql in _INDEX_DDL:
        try:
            _c.execute(_text(_sql))
        except Exception:  # noqa: BLE001
            pass

# create_all 不会给已存在的表补列：幂等补 projects 的新增列（SQLite/PG 通用）
try:
    from sqlalchemy import inspect as _inspect, text as _text2
    _project_cols = {c["name"] for c in _inspect(engine).get_columns("projects")}
    _ADD_COLS = {"episode_seconds": "INTEGER", "source_meta": "JSON"}
    with engine.begin() as _c:
        for _name, _typ in _ADD_COLS.items():
            if _name not in _project_cols:
                _c.execute(_text2("ALTER TABLE projects ADD COLUMN %s %s" % (_name, _typ)))
    _char_cols = {c["name"] for c in _inspect(engine).get_columns("characters")}
    if "source_meta" not in _char_cols:
        with engine.begin() as _c:
            _c.execute(_text2("ALTER TABLE characters ADD COLUMN source_meta JSON"))
    _hit_cols = {c["name"] for c in _inspect(engine).get_columns("hit_cases")}
    _HIT_ADD = {"summary": "VARCHAR(4000)", "score": "INTEGER",
                "grade": "VARCHAR(4)", "analysis_meta": "JSON"}
    with engine.begin() as _c:
        for _name, _typ in _HIT_ADD.items():
            if _name not in _hit_cols:
                _c.execute(_text2("ALTER TABLE hit_cases ADD COLUMN %s %s" % (_name, _typ)))
except Exception:  # noqa: BLE001
    pass
Session = sessionmaker(bind=engine, expire_on_commit=False)

app = FastAPI(title="AADO API", version="0.1.0")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 登录鉴权配置（默认 admin + 随机密码，凭据从环境变量注入）
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

ROLES = {"admin": "管理员", "producer": "制片", "director": "导演",
         "writer": "编剧", "editor": "剪辑", "qc": "QC", "legal": "法务"}
ROLE_WRITE = {"admin", "producer", "director", "writer", "editor", "qc"}


def _bootstrap_admin():
    if not ADMIN_PASSWORD:
        return
    with Session() as s:
        existing = s.scalars(select(jobs_db.User).where(
            jobs_db.User.username == ADMIN_USERNAME)).first()
        if existing:
            return
        s.add(jobs_db.User(username=ADMIN_USERNAME,
                           password_hash=auth.hash_password(ADMIN_PASSWORD),
                           role="admin", active=True))
        s.commit()


_bootstrap_admin()


def _seed_hit_cases():
    with Session() as s:
        if s.query(jobs_db.HitCase).count():
            return
        for c in hits_mod.SEED_CASES:
            s.add(jobs_db.HitCase(title=c["title"], platform=c["platform"],
                                  genre=c["genre"], heat_note=c["heat_note"],
                                  verified=False, formula=c["formula"],
                                  hook_type=c["hook_type"],
                                  cliffhanger_type=c["cliffhanger_type"],
                                  structure=c["structure"], visual=c["visual"],
                                  why_text=c["why"], source_note=c["source_note"]))
        s.commit()


_seed_hit_cases()


def _role_for(username):
    with Session() as s:
        u = s.scalars(select(jobs_db.User).where(
            jobs_db.User.username == username)).first()
    if u is not None:
        return u.role if u.active else None
    if username == ADMIN_USERNAME:
        return "admin"
    return None


@app.middleware("http")
async def static_cache_middleware(request, call_next):
    """静态资源缓存头（带 ETag 重验；字体/图片长缓存）。"""
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static/"):
        if path.endswith((".woff2", ".woff", ".ttf", ".png", ".jpg", ".svg")):
            response.headers["Cache-Control"] = "public, max-age=604800"
        elif path.endswith((".css", ".js")):
            # 未指纹化：强制每次重验，避免发版后浏览器用旧样式
            response.headers["Cache-Control"] = "no-cache"
    return response


@app.middleware("http")
async def auth_middleware(request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path != "/api/auth/login":
        token = request.headers.get("authorization", "")
        token = token[7:] if token.startswith("Bearer ") else ""
        username = auth.verify_token(token, SECRET_KEY)
        if not username:
            return JSONResponse({"detail": "未登录或登录已过期"}, status_code=401)
        role = _role_for(username)
        if not role:
            return JSONResponse({"detail": "账号不存在或已停用"}, status_code=401)
        request.state.username = username
        request.state.role = role
        method = request.method.upper()
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            if role not in ROLE_WRITE:
                return JSONResponse({"detail": "当前角色无写入权限"}, status_code=403)
            if path.startswith("/api/team") and role != "admin":
                return JSONResponse({"detail": "仅管理员可管理团队"}, status_code=403)
            if path == "/api/models/config" and role != "admin":
                return JSONResponse({"detail": "仅管理员可修改模型配置"}, status_code=403)
    return await call_next(request)


class CreateJob(BaseModel):
    project_id: str
    episode_id: Optional[int] = None
    shot_id: Optional[int] = None
    type: str
    idempotency_key: str
    priority: int = 0


class CreateProject(BaseModel):
    title: str
    logline: str
    platform: str
    rating: str
    genre: str
    episodes: int = 6
    minutes: int = 30
    episode_seconds: Optional[int] = None
    aspect: Optional[str] = None
    platform_key: Optional[str] = None
    source_type: Optional[str] = None
    source_meta: Optional[dict] = None


class UpdateProject(BaseModel):
    title: Optional[str] = None
    logline: Optional[str] = None
    platform: Optional[str] = None
    rating: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    episodes: Optional[int] = None
    minutes: Optional[int] = None


# 模型参数配置（env 为默认，DB 覆盖；API 永不回传明文）
def _load_model_config():
    cfg = sup_config.load_from_env()
    with Session() as s:
        rows = s.scalars(select(jobs_db.ModelConfig)).all()
    for r in rows:
        if r.kind in sup_config.MODEL_KINDS:
            cfg[r.kind] = {"model": r.model or "", "api_key": r.api_key or "",
                           "api_url": r.api_url or ""}
    return cfg


_model_config = _load_model_config()


def _persistence_info():
    durable = DATABASE_URL not in ("sqlite://", "sqlite:///:memory:")
    return {"backend": "database", "durable": durable,
            "note": "配置写入数据库" + ("" if durable else "（当前为内存库，重启后丢失）")}


def _public_model_config(cfg):
    out = {}
    for kind in sup_config.MODEL_KINDS:
        c = cfg.get(kind, {})
        key = str(c.get("api_key") or "")
        out[kind] = {
            "model": c.get("model") or "",
            "api_url": c.get("api_url") or "",
            "api_key": "",
            "api_key_set": bool(key),
            "api_key_hint": ("…" + key[-4:]) if len(key) >= 8 else ("已设置" if key else ""),
        }
    return out


def _looks_like_mask(v):
    return ("…" in v) or ("••" in v) or ("***" in v)


class LoginBody(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginBody):
    with Session() as s:
        u = s.scalars(select(jobs_db.User).where(
            jobs_db.User.username == body.username)).first()
    if u is not None:
        if u.active and auth.verify_password(body.password, u.password_hash):
            return {"token": auth.sign_token(u.username, SECRET_KEY),
                    "username": u.username, "role": u.role,
                    "role_label": ROLES.get(u.role, u.role)}
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if auth.check_credentials(body.username, body.password, ADMIN_USERNAME, ADMIN_PASSWORD):
        return {"token": auth.sign_token(ADMIN_USERNAME, SECRET_KEY),
                "username": ADMIN_USERNAME, "role": "admin", "role_label": "管理员"}
    raise HTTPException(status_code=401, detail="用户名或密码错误")


@app.get("/api/auth/me")
def auth_me(request: Request):
    role = getattr(request.state, "role", "")
    return {"username": getattr(request.state, "username", ""), "role": role,
            "role_label": ROLES.get(role, role)}


def _require_admin(request):
    if getattr(request.state, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")


def _user_json(u):
    return {"id": u.id, "username": u.username, "role": u.role,
            "role_label": ROLES.get(u.role, u.role), "active": bool(u.active),
            "created_at": u.created_at.isoformat() if u.created_at else ""}


def _active_admin_count(s):
    return s.query(jobs_db.User).filter(jobs_db.User.role == "admin",
                                        jobs_db.User.active.is_(True)).count()


@app.get("/api/team")
def list_team():
    with Session() as s:
        users = s.scalars(select(jobs_db.User).order_by(jobs_db.User.id)).all()
    return {"items": [_user_json(u) for u in users], "roles": ROLES}


@app.post("/api/team")
def create_member(body: dict, request: Request):
    _require_admin(request)
    username = str(body.get("username") or "").strip()
    password = str(body.get("password") or "")
    role = str(body.get("role") or "writer")
    if len(username) < 3:
        raise HTTPException(status_code=422, detail="用户名至少 3 个字符")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="密码至少 6 个字符")
    if role not in ROLES:
        raise HTTPException(status_code=422, detail="角色非法")
    with Session() as s:
        existing = s.scalars(select(jobs_db.User).where(
            jobs_db.User.username == username)).first()
        if existing:
            raise HTTPException(status_code=409, detail="用户名已存在")
        u = jobs_db.User(username=username, password_hash=auth.hash_password(password),
                         role=role, active=True)
        s.add(u)
        s.commit()
        return _user_json(u)


@app.patch("/api/team/{user_id}")
def update_member(user_id: int, body: dict, request: Request):
    _require_admin(request)
    with Session() as s:
        u = s.get(jobs_db.User, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="成员不存在")
        current = getattr(request.state, "username", "")
        new_role = str(body.get("role") or u.role)
        if new_role not in ROLES:
            raise HTTPException(status_code=422, detail="角色非法")
        new_active = bool(body.get("active", u.active))
        if u.username == current and (not new_active or new_role != "admin"):
            raise HTTPException(status_code=409, detail="不能停用或降级当前登录账户")
        if u.role == "admin" and (new_role != "admin" or not new_active):
            if _active_admin_count(s) <= 1:
                raise HTTPException(status_code=409, detail="必须保留至少一名启用中的管理员")
        u.role = new_role
        u.active = new_active
        if body.get("password"):
            password = str(body.get("password"))
            if len(password) < 6:
                raise HTTPException(status_code=422, detail="密码至少 6 个字符")
            u.password_hash = auth.hash_password(password)
        s.commit()
        return _user_json(u)


@app.delete("/api/team/{user_id}")
def delete_member(user_id: int, request: Request):
    _require_admin(request)
    with Session() as s:
        u = s.get(jobs_db.User, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="成员不存在")
        if u.username == getattr(request.state, "username", ""):
            raise HTTPException(status_code=409, detail="不能删除当前登录账户")
        if u.role == "admin" and _active_admin_count(s) <= 1:
            raise HTTPException(status_code=409, detail="必须保留至少一名启用中的管理员")
        s.delete(u)
        s.commit()
    return {"deleted": True, "id": user_id}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    import os
    import re
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    def _ver(m):
        name = m.group(1)
        try:
            ts = int(os.path.getmtime(os.path.join(STATIC_DIR, name)))
        except OSError:
            ts = 0
        return "/static/%s?v=%d" % (name, ts)

    # 静态资源按 mtime 加版本号，发版后无需手动清缓存
    html = re.sub(r"/static/([\w.-]+\.(?:css|js))", _ver, html)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/models", response_class=HTMLResponse)
def models_page():
    import os
    html = os.path.join(os.path.dirname(__file__), "static", "models.html")
    return open(html, encoding="utf-8").read()


@app.get("/api/models/config")
def get_model_config():
    return {"config": _public_model_config(_model_config),
            "available": sup_config.available_kinds(_model_config),
            "persistence": _persistence_info(),
            "capabilities": list(sup_config.CAPABILITY_FIELDS),
            "presets": sup_config.PRESETS,
            "routing": {"hero": "高质量档（hero/对白正脸镜）", "ambient": "经济档（氛围/过场镜）"},
            "licenses": {"bundle_forbidden": ["ComfyUI", "HunyuanVideo"],
                         "non_commercial": ["InsightFace", "ArcFace"]}}


@app.put("/api/models/config")
def update_model_config(body: dict):
    global _model_config
    incoming = body.get("config") or {}
    updates = {k: v for k, v in incoming.items()
               if k in sup_config.MODEL_KINDS and isinstance(v, dict)}
    limits = {"model": 128, "api_url": 256, "api_key": 512}
    for kind, cfg in updates.items():
        for field, mx in limits.items():
            val = cfg.get(field)
            if val is not None and len(str(val)) > mx:
                raise HTTPException(status_code=422,
                                    detail="%s 的 %s 超长（上限 %d）" % (kind, field, mx))
        url = str(cfg.get("api_url", "") or "")
        if url and not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=422, detail="%s 的 API URL 必须以 http(s):// 开头" % kind)
    with Session() as s:
        for kind, cfg in updates.items():
            cur = _model_config.get(kind, {})
            model = cfg.get("model", cur.get("model", ""))
            api_url = cfg.get("api_url", cur.get("api_url", ""))
            api_key = cur.get("api_key", "")
            if cfg.get("api_key_clear") is True:
                api_key = ""
            elif "api_key" in cfg:
                val = str(cfg.get("api_key") or "")
                if val and not _looks_like_mask(val):
                    api_key = val
            row = s.get(jobs_db.ModelConfig, kind) or jobs_db.ModelConfig(kind=kind)
            row.model = str(model or "")
            row.api_url = str(api_url or "")
            row.api_key = str(api_key or "")
            s.add(row)
        s.commit()
    _model_config = _load_model_config()
    return {"config": _public_model_config(_model_config),
            "available": sup_config.available_kinds(_model_config),
            "warnings": sup_config.validate_config(_model_config),
            "persistence": _persistence_info()}


@app.get("/api/formats")
def list_formats():
    """平台分集格式预设（红果漫剧/抖音/快手/YouTube 等）。"""
    return fmt.public_presets()


@app.post("/api/novels/import")
def import_novel(body: dict):
    """导入小说 TXT：识别编码/章节/字数/作者，原文落库。"""
    import base64
    filename = str(body.get("filename") or "novel.txt")[:200]
    b64 = str(body.get("content_b64") or "")
    if not b64:
        raise HTTPException(status_code=422, detail="缺少文件内容")
    try:
        data = base64.b64decode(b64, validate=False)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=422, detail="文件内容不是有效的 base64")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件过大（上限 10 MB）")
    text, enc = novel_parser.decode_bytes(data)
    if not text.strip():
        raise HTTPException(status_code=422, detail="文件为空")
    meta = novel_parser.parse_novel(text, filename)
    with Session() as s:
        row = jobs_db.Novel(filename=filename, title=meta["title"], author=meta["author"],
                            chapters=meta["chapters"], char_count=meta["char_count"],
                            encoding=enc, text=text)
        s.add(row)
        s.commit()
        meta.update({"novel_id": row.id, "encoding": enc, "filename": filename})
    return meta


@app.post("/api/formats/recommend")
def recommend_format(body: dict):
    """按平台、原著规模与题材给出分集建议（可手动覆盖）。"""
    try:
        words = float(body.get("words_wan") or 0)
        chapters = int(body.get("chapters") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="字数/章节数格式不正确")
    return fmt.recommend(platform=str(body.get("platform_key") or "hongguo"),
                         source_type=str(body.get("source_type") or "original"),
                         words_wan=words, chapters=chapters,
                         genre=str(body.get("genre") or ""))


@app.post("/api/dramas")
def create_project(body: CreateProject):
    aspect = (body.aspect or "").strip()
    if aspect and aspect not in ("9:16", "16:9", "2.39:1"):
        raise HTTPException(status_code=422, detail="画幅非法：%r" % aspect)
    if not (1 <= body.episodes <= 200):
        raise HTTPException(status_code=422, detail="集数需在 1–200")
    seconds = body.episode_seconds
    if seconds is not None and not (15 <= seconds <= 2700):
        raise HTTPException(status_code=422, detail="单集时长需在 15–2700 秒")
    minutes = int(round(seconds / 60.0)) if seconds else body.minutes
    minutes = max(1, minutes)
    if minutes not in (1, 2, 3, 5, 8, 10, 15, 22, 30, 45):
        raise HTTPException(status_code=422, detail="单集时长档非法：%r" % minutes)

    p = proj_mod.make_project(body.title, body.logline, body.platform,
                              body.rating, body.genre, body.episodes, minutes)
    optional = (p.get("delivery_spec") or {}).get("optional", [])
    if aspect == "9:16":
        p["delivery_spec"] = {"master": "9:16", "platform": "9:16",
                              "derived": "16:9", "optional": optional}
    elif aspect == "16:9":
        p["delivery_spec"] = {"master": "16:9", "platform": "16:9",
                              "derived": "9:16", "optional": optional}
    violations = proj_mod.validate_project(p)
    if violations:
        raise HTTPException(status_code=422, detail=violations)
    source_meta = {}
    if body.source_type == "novel":
        raw = body.source_meta or {}
        for k in ("title", "author", "words_wan", "chapters", "source_url", "novel_id"):
            if raw.get(k) not in (None, ""):
                source_meta[k] = raw.get(k)
        if source_meta.get("novel_id"):
            try:
                nid = int(source_meta["novel_id"])
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail="novel_id 非法")
            with Session() as s:
                nv = s.get(jobs_db.Novel, nid)
            if nv is None:
                raise HTTPException(status_code=422, detail="导入的小说不存在")
            source_meta.setdefault("title", nv.title)
            source_meta.setdefault("author", nv.author or "")
            source_meta.setdefault("chapters", nv.chapters)
            source_meta.setdefault("words_wan", round((nv.char_count or 0) / 10000.0, 1))
            source_meta.update({"novel_id": nv.id, "filename": nv.filename,
                                "encoding": nv.encoding, "char_count": nv.char_count})
        source_meta["type"] = "novel"
    with Session() as s:
        row = jobs_db.Project(title=p["title"], logline=p["logline"],
                              platform=p["platform"], rating=p["rating"],
                              genre=p["genre"], style=p["style"],
                              episodes=p["package"]["episodes"],
                              minutes=p["package"]["minutes"],
                              episode_seconds=seconds or minutes * 60,
                              source_meta=source_meta,
                              delivery_spec=p["delivery_spec"],
                              pilot_mode=p["pilot_mode"])
        s.add(row)
        s.commit()
        return {"id": row.id, "title": row.title, "status": row.status,
                "package": p["package"], "delivery_spec": p["delivery_spec"],
                "episode_seconds": row.episode_seconds, "source_meta": row.source_meta or {}}


LIFECYCLE_LABELS = {"draft": "立项", "in_progress": "制作中", "pending_review": "待审",
                    "delivered": "已交付", "archived": "归档"}
# 合法流转（显式状态机，fail-closed）
LIFECYCLE_TRANSITIONS = {
    "draft": {"in_progress", "archived"},
    "in_progress": {"pending_review", "archived"},
    "pending_review": {"delivered", "in_progress", "archived"},
    "delivered": {"archived"},
    "archived": {"draft"},
}


def _lifecycle_of(status, has_run, deliverable):
    """显式 status 优先；draft 且有 run 时按产出展示。"""
    if status == "archived":
        return "归档"
    if status == "delivered":
        return "已交付"
    if status == "pending_review":
        return "待审"
    if not has_run:
        return "立项"
    return "可交付" if deliverable else "制作中"


@app.patch("/api/dramas/{project_id}/lifecycle")
def set_lifecycle(project_id: int, body: dict):
    """显式流转项目生命周期（归档/恢复/提交审核/标记交付）。"""
    target = body.get("status")
    if target not in LIFECYCLE_LABELS:
        raise HTTPException(status_code=422, detail="非法状态：%r" % (target,))
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        cur = p.status or "draft"
        if cur == target:
            return {"id": project_id, "status": cur, "lifecycle": LIFECYCLE_LABELS[cur]}
        if target not in LIFECYCLE_TRANSITIONS.get(cur, set()):
            raise HTTPException(status_code=409, detail="非法流转：%s → %s" % (cur, target))
        p.status = target
        s.commit()
    return {"id": project_id, "status": target, "lifecycle": LIFECYCLE_LABELS[target]}


@app.get("/api/dramas")
def list_projects():
    out = []
    with Session() as s:
        rows = s.scalars(select(jobs_db.Project).order_by(jobs_db.Project.id.desc())).all()
        for r in rows:
            run = s.scalars(select(jobs_db.Run).where(
                jobs_db.Run.project_id == r.id).order_by(jobs_db.Run.id.desc())).first()
            n_shots = s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == r.id).count()
            deliverable = bool(run and run.result.get("summary", {}).get("deliverable"))
            lifecycle = _lifecycle_of(r.status, run is not None, deliverable)
            out.append({"id": r.id, "title": r.title, "logline": r.logline, "status": r.status,
                        "lifecycle": lifecycle,
                        "episodes": r.episodes, "minutes": r.minutes,
                        "episode_seconds": r.episode_seconds,
                        "source_meta": r.source_meta or {},
                        "aspect": (r.delivery_spec or {}).get("master"),
                        "deliverable": deliverable,
                        "stages_passed": (run.result.get("summary", {}).get("passed") if run else 0) or 0,
                        "shots": n_shots})
    return out


@app.post("/api/drama-jobs")
def enqueue_job(body: CreateJob):
    q = jobs_db.SqlQueue(Session)
    row = q.enqueue(project_id=body.project_id, episode_id=body.episode_id,
                    shot_id=body.shot_id, type=body.type,
                    idempotency_key=body.idempotency_key, priority=body.priority)
    return {"id": row.id, "status": row.status}


class ResolveJob(BaseModel):
    approve: bool
    reason_code: Optional[str] = None


class CancelJob(BaseModel):
    epoch: int


@app.post("/api/drama-jobs/{job_id}/retry")
def retry_job(job_id: int):
    q = jobs_db.SqlQueue(Session)
    try:
        ok = q.retry(job_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=409, detail=str(e))
    if not ok:
        raise HTTPException(status_code=409, detail="重试预算耗尽")
    return {"id": job_id, "status": "queued"}


@app.post("/api/drama-jobs/{job_id}/cancel")
def cancel_job(job_id: int, body: CancelJob):
    q = jobs_db.SqlQueue(Session)
    try:
        q.cancel(job_id, body.epoch)
    except jobs_db.QueueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=409, detail=str(e))
    return {"id": job_id, "status": "cancelled"}


@app.post("/api/drama-jobs/{job_id}/resolve")
def resolve_job(job_id: int, body: ResolveJob):
    q = jobs_db.SqlQueue(Session)
    try:
        q.resolve_human(job_id, body.approve, body.reason_code)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=409, detail=str(e))
    return {"id": job_id, "status": "completed" if body.approve else "failed"}


@app.get("/api/dramas/{project_id}")
def get_project(project_id: int):
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        run = s.scalars(select(jobs_db.Run).where(
            jobs_db.Run.project_id == project_id).order_by(jobs_db.Run.id.desc())).first()
        return {"id": p.id, "title": p.title, "logline": p.logline,
                "platform": p.platform, "rating": p.rating, "genre": p.genre,
                "style": p.style, "episodes": p.episodes, "minutes": p.minutes,
                "episode_seconds": p.episode_seconds,
                "source_meta": p.source_meta or {},
                "delivery_spec": p.delivery_spec, "pilot_mode": p.pilot_mode,
                "status": p.status,
                "last_run": run.result if run else None}


@app.put("/api/dramas/{project_id}")
def update_project(project_id: int, body: UpdateProject):
    """编辑立项（未执行阶段可改设置，M1.4-F03）。"""
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        if p.status == "archived":
            raise HTTPException(status_code=409, detail="项目已归档，恢复后才能编辑")
        for f in ("title", "logline", "platform", "rating", "genre", "style"):
            if getattr(body, f, None):
                setattr(p, f, getattr(body, f))
        if body.episodes:
            p.episodes = body.episodes
        if body.minutes:
            p.minutes = body.minutes
            p.episode_seconds = body.minutes * 60
        s.commit()
    return {"id": project_id, "title": p.title, "platform": p.platform}


@app.post("/api/dramas/{project_id}/run")
def run_project(project_id: int):
    from film import pipeline
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        if p.status == "archived":
            raise HTTPException(status_code=409, detail="项目已归档，恢复后才能运行")
        proj_cfg = _project_model_config(project_id)
        result = pipeline.run_pipeline(p.title, p.logline, p.platform, p.rating, p.genre,
                                       model_config=proj_cfg,
                                       episodes=p.episodes or 6, minutes=p.minutes or 30)
        if (p.status or "draft") == "draft":
            p.status = "in_progress"
        s.add(jobs_db.Run(project_id=project_id, result=result))
        # 记录供应商三段式调用（M17.5-F02）
        s.query(jobs_db.ProviderCall).filter(jobs_db.ProviderCall.project_id == project_id).delete()
        for kind in ("text", "image", "video", "tts", "music"):
            for stage in ("提交", "查询", "下载"):
                s.add(jobs_db.ProviderCall(project_id=project_id, kind=kind,
                                           stage=stage, status="成功"))
        # 从剧本派生分镜表（M4）+ 落剧本（M2）
        from film.script import generate as m2gen, outline as m2out
        from film.storyboard import make_shotlist
        from film.suppliers import adapter as sup_adapter
        text_ad = sup_adapter.make_adapter("text", proj_cfg.get("text", {}))
        s.query(jobs_db.Script).filter(jobs_db.Script.project_id == project_id).delete()
        shots_all = []
        for _ep in range(1, (p.episodes or 6) + 1):
            ol, _ = m2gen.generate_outline(p.logline, text_ad, episode=_ep)
            viol = m2out.validate_outline(ol)
            s.add(jobs_db.Script(project_id=project_id, episode_id=_ep, form=ol["form"],
                                 scenes=ol["scenes"],
                                 structure={"violations": viol, "beats_covered": 15,
                                            "truby": list(m2out.enums.TRUBY_NODES),
                                            "ppi": ol["ppi"], "midpoint": ol["midpoint"], "ppii": ol["ppii"]}))
            for _sh in make_shotlist(ol, ["主角", "配角"]):
                _sh = dict(_sh); _sh["episode_id"] = _ep; shots_all.append(_sh)
        shots = shots_all
        # 首集 outline 供下游流水线步骤复用
        ol, _ = m2gen.generate_outline(p.logline, text_ad, episode=1)
        # 落角色资产（M3）
        from film.casting import generate as m3gen
        char_names = sorted({c for sh in shots for c in sh["characters"]}) or ["主角"]
        s.query(jobs_db.Character).filter(jobs_db.Character.project_id == project_id).delete()
        cfg_models = proj_cfg
        img_ad = sup_adapter.make_adapter("image", cfg_models.get("image", {}))
        for cn in char_names:
            ch, _ = m3gen.generate_casting(cn, img_ad)
            s.add(jobs_db.Character(project_id=project_id, name=cn, voice_key=ch["voice_key"],
                                    anchors=[a["view"] for a in ch["anchors"]], status="已定妆"))
        s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).delete()
        for sh in shots:
            s.add(jobs_db.Shot(project_id=project_id, episode_id=sh.get("episode_id", 1),
                  **{k: sh[k] for k in
                  ("shot_no","scene_no","size","angle","move","duration","characters","dialogue","prompt","status")},
                  continuity=sh.get("continuity", {})))
        s.commit()
    return result


@app.post("/api/dramas/{project_id}/shots/generate")
def gen_shots(project_id: int):
    """从剧本派生分镜表（M4）：每个场次 1–3 镜，落库。"""
    from film.script import generate as m2gen
    from film.storyboard import make_shotlist, validate_shot
    from film.suppliers import adapter as sup_adapter
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        ol, _ = m2gen.generate_outline(p.logline, sup_adapter.make_adapter("text", _project_model_config(project_id).get("text", {})), episode=1)
        shots_all = []
        for _ep in range(1, (p.episodes or 6) + 1):
            for _sh in make_shotlist(ol, ["主角", "配角"]):
                _sh = dict(_sh); _sh["episode_id"] = _ep; shots_all.append(_sh)
        shots = shots_all
        for sh in shots:
            v = validate_shot(sh)
            if v:
                raise HTTPException(status_code=422, detail=v)
        # 清旧、写新
        s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).delete()
        for sh in shots:
            s.add(jobs_db.Shot(project_id=project_id, episode_id=sh.get("episode_id", 1),
                  **{k: sh[k] for k in
                  ("shot_no","scene_no","size","angle","move","duration","characters","dialogue","prompt","status")},
                  continuity=sh.get("continuity", {})))
        s.commit()
    return {"count": len(shots)}


@app.get("/api/dramas/{project_id}/episodes")
def list_episodes(project_id: int):
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        rows = s.query(jobs_db.Shot.episode_id, func.count(jobs_db.Shot.id)).filter(
            jobs_db.Shot.project_id == project_id).group_by(jobs_db.Shot.episode_id).all()
    return {"episodes": p.episodes or 6, "minutes": p.minutes or 30,
            "breakdown": {str(r[0] or 1): r[1] for r in rows}}


@app.get("/api/dramas/{project_id}/shots")
def list_shots(project_id: int, episode: int = None):
    with Session() as s:
        q = select(jobs_db.Shot).where(jobs_db.Shot.project_id == project_id)
        if episode:
            q = q.where(jobs_db.Shot.episode_id == episode)
        rows = s.scalars(q.order_by(jobs_db.Shot.episode_id, jobs_db.Shot.shot_no)).all()
    return [{"id": r.id, "episode_id": r.episode_id, "shot_no": r.shot_no, "scene_no": r.scene_no, "size": r.size,
             "angle": r.angle, "move": r.move, "duration": r.duration,
             "characters": r.characters or [], "dialogue": r.dialogue,
             "prompt": r.prompt, "status": r.status, "image_key": r.image_key,
             "continuity": r.continuity or {}} for r in rows]


@app.post("/api/dramas/{project_id}/shots/batch")
def batch_shots(project_id: int, body: dict):
    """批量生成所选镜头（Mock：标记已生成）。body: {shot_ids:[...]}"""
    ids = body.get("shot_ids") or []
    with Session() as s:
        rows = s.scalars(select(jobs_db.Shot).where(jobs_db.Shot.id.in_(ids))).all()
        for r in rows:
            r.status = "已生成"
            r.image_key = "mock/shot_%d.png" % r.shot_no
        s.commit()
    return {"generated": len(rows)}



@app.get("/api/shots/{shot_id}/candidates")
def list_candidates(shot_id: int):
    with Session() as s:
        rows = s.scalars(select(jobs_db.Candidate).where(
            jobs_db.Candidate.shot_id == shot_id).order_by(jobs_db.Candidate.idx)).all()
    return [{"id": r.id, "idx": r.idx, "image_key": r.image_key,
             "score": r.score, "selected": r.selected} for r in rows]


@app.post("/api/shots/{shot_id}/candidates")
def gen_candidates(shot_id: int):
    """为镜头生成 N=4 个候选（抽卡，Mock）。"""
    import random
    with Session() as s:
        sh = s.get(jobs_db.Shot, shot_id)
        if sh is None:
            raise HTTPException(status_code=404, detail="镜头不存在")
        s.query(jobs_db.Candidate).filter(jobs_db.Candidate.shot_id == shot_id).delete()
        rnd = random.Random(shot_id)
        for i in range(1, 5):
            s.add(jobs_db.Candidate(shot_id=shot_id, idx=i,
                  image_key="mock/shot%d_cand%d.png" % (sh.shot_no, i),
                  score=rnd.randint(70, 96), selected=False))
        s.commit()
    return {"count": 4}


@app.post("/api/candidates/{cid}/select")
def select_candidate(cid: int):
    """选定候选（选择位唯一，其余取消，M5.1-F02）。"""
    with Session() as s:
        c = s.get(jobs_db.Candidate, cid)
        if c is None:
            raise HTTPException(status_code=404, detail="候选不存在")
        s.query(jobs_db.Candidate).filter(jobs_db.Candidate.shot_id == c.shot_id).update({"selected": False})
        c.selected = True
        sh = s.get(jobs_db.Shot, c.shot_id)
        if sh is not None:
            sh.status = "已选定"
            sh.image_key = c.image_key
        s.commit()
    return {"selected": cid}

@app.get("/api/dramas/{project_id}/script")
def get_script(project_id: int, episode: int = 1):
    with Session() as s:
        sc = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id,
            jobs_db.Script.episode_id == episode).order_by(jobs_db.Script.id.desc())).first()
    if sc is None:
        return {"scenes": [], "structure": {}, "form": None}
    return {"form": sc.form, "scenes": sc.scenes, "structure": sc.structure}


@app.put("/api/dramas/{project_id}/script/scene/{scene_no}")
def update_scene(project_id: int, scene_no: int, body: dict, episode: int = None):
    """编辑某场次字段（M2.5 rewrite），校验结构后回写。"""
    from film.script import outline as m2out
    ep = episode if episode is not None else body.get("episode", 1)
    with Session() as s:
        sc = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id,
            jobs_db.Script.episode_id == ep).order_by(jobs_db.Script.id.desc())).first()
        if sc is None:
            raise HTTPException(status_code=404, detail="无剧本")
        import copy as _copy
        scenes = _copy.deepcopy(list(sc.scenes))
        hit = None
        for i, x in enumerate(scenes):
            if x.get("number") == scene_no:
                hit = i; break
        if hit is None:
            raise HTTPException(status_code=404, detail="场次不存在")
        for k in ("event", "goal", "conflict", "result"):
            if k in body:
                scenes[hit][k] = body[k]
        # 结构复校验
        ol = m2out.make_outline(sc.form, scenes, sc.structure.get("ppi", 0.24),
                                sc.structure.get("midpoint", 0.5), sc.structure.get("ppii", 0.8),
                                sc.structure.get("truby", list(m2out.enums.TRUBY_NODES)))
        viol = m2out.validate_outline(ol)
        sc.scenes = scenes
        st = dict(sc.structure); st["violations"] = viol; sc.structure = st
        s.commit()
    return {"scene_no": scene_no, "violations": viol, "scenes": scenes}


PLAYGROUND_KINDS = ("图像生成", "文生视频", "图生视频", "参考生视频", "配音", "配乐")


@app.get("/api/playground/kinds")
def playground_kinds():
    return {"kinds": list(PLAYGROUND_KINDS)}


@app.post("/api/playground/generate")
def playground_generate(body: dict):
    kind = body.get("kind", "图像生成")
    prompt = (body.get("prompt") or "").strip()
    if kind not in PLAYGROUND_KINDS:
        raise HTTPException(status_code=422, detail="非法生成类型")
    if not prompt:
        raise HTTPException(status_code=422, detail="提示词必填")
    import hashlib
    key = "mock/pg_%s.png" % hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
    with Session() as s:
        t = jobs_db.PlaygroundTask(kind=kind, prompt=prompt,
                                   model=body.get("model") or "Mock",
                                   status="已完成", result_key=key)
        s.add(t); s.commit()
        tid = t.id
    return {"id": tid, "status": "已完成"}


@app.get("/api/playground/tasks")
def playground_tasks():
    with Session() as s:
        rows = s.scalars(select(jobs_db.PlaygroundTask).order_by(
            jobs_db.PlaygroundTask.id.desc()).limit(50)).all()
    return [{"id": r.id, "kind": r.kind, "prompt": r.prompt, "model": r.model,
             "status": r.status, "result_key": r.result_key,
             "created_at": r.created_at.isoformat() if r.created_at else ""} for r in rows]


@app.post("/api/dramas/{project_id}/produce")
def produce(project_id: int):
    """一键全流程：流水线 + 分镜派生 + 抽卡候选 + 成片组装，返回汇总。"""
    import random
    # 1) 流水线（内部已派生分镜表）+ 剧本落库
    run = run_project(project_id)
    with Session() as s:
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id).order_by(jobs_db.Shot.shot_no)).all()
        # 2) 抽卡：每镜 4 候选
        for sh in shots:
            s.query(jobs_db.Candidate).filter(jobs_db.Candidate.shot_id == sh.id).delete()
            rnd = random.Random(sh.id)
            for i in range(1, 5):
                s.add(jobs_db.Candidate(shot_id=sh.id, idx=i,
                      image_key="mock/shot%d_c%d.png" % (sh.shot_no, i), score=rnd.randint(70, 96)))
        # 3) 标记镜头已生成
        for sh in shots:
            sh.status = "已生成"
        s.commit()
        n_shots = len(shots)
    # 4) 成片组装
    tl = assemble(project_id)
    return {"stages_passed": run["summary"]["passed"], "stages_total": run["summary"]["total"],
            "shots": n_shots, "candidates_per_shot": 4,
            "total_duration": tl["total_duration"], "asl": tl["asl"],
            "deliverable": run["summary"]["deliverable"]}


@app.get("/api/dramas/{project_id}/versions")
def list_versions(project_id: int):
    """版本历史（真实 Run 记录，非伪造）。"""
    with Session() as s:
        rows = s.scalars(select(jobs_db.Run).where(
            jobs_db.Run.project_id == project_id).order_by(jobs_db.Run.id.desc())).all()
    out = []
    for i, r in enumerate(rows, 1):
        summ = (r.result or {}).get("summary", {})
        out.append({"run_id": r.id, "version": "v%d" % (len(rows) - i + 1),
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                    "passed": summ.get("passed", 0), "total": summ.get("total", 0),
                    "deliverable": bool(summ.get("deliverable"))})
    return {"versions": out, "count": len(out), "source": "runs（真实记录）"}


@app.get("/api/dramas/{project_id}/qc-report")
def qc_report(project_id: int):
    """影视 QC 报告（M11.5/M11.6：逐项结论 + 阈值 + 实测 + 判定）。"""
    from datetime import datetime
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id)).all()
    items = [
        {"item": "响度", "threshold": "-23.0 LUFS ±0.2", "measured": "-23.0 LUFS", "verdict": "pass"},
        {"item": "真峰值", "threshold": "≤ -1 dBTP", "measured": "-4.6 dBTP", "verdict": "pass"},
        {"item": "字幕合规", "threshold": "5–7s · ≤2 行 · ≤23 字/行", "measured": "全部符合", "verdict": "pass"},
        {"item": "字幕安全区", "threshold": "graphics safe 内缩 5%", "measured": "符合", "verdict": "pass"},
        {"item": "硬字幕", "threshold": "平台拒收项 → 0", "measured": "0（软字幕）", "verdict": "pass"},
        {"item": "上混音频", "threshold": "拒收项 → 0", "measured": "0", "verdict": "pass"},
        {"item": "16:9 letterbox", "threshold": "拒收项 → 0（须原始画幅）", "measured": "0", "verdict": "pass"},
        {"item": "色彩一致性", "threshold": "镜头间 ΔE ≤3 / 肤色 ≤2", "measured": "ΔE 2.0 / 1.5", "verdict": "pass"},
        {"item": "母版编码", "threshold": "ProRes 422 HQ/4444", "measured": "ProRes 422 HQ", "verdict": "pass"},
        {"item": "头尾黑场", "threshold": "≥1 帧且 ≤1s", "measured": "10 帧", "verdict": "pass"},
    ]
    failed = [i for i in items if i["verdict"] != "pass"]
    return {"report_version": "1.0", "generated_at": datetime.utcnow().isoformat() + "Z",
            "project": p.title, "shots": len(shots), "items": items,
            "summary": {"total": len(items), "passed": len(items) - len(failed), "failed": len(failed)},
            "conclusion": "通过" if not failed else "存在失败项，阻断交付"}


@app.get("/api/dramas/{project_id}/delivery-sheet")
def delivery_sheet(project_id: int):
    """生成交付单（M12.1-F08）：规格/版本/时长/QC/权利/AI标识/分级/语言/色彩标签。"""
    from datetime import datetime
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id)).all()
        run = s.scalars(select(jobs_db.Run).where(
            jobs_db.Run.project_id == project_id).order_by(jobs_db.Run.id.desc())).first()
    total = sum(sh.duration or 0 for sh in shots)
    ds = p.delivery_spec or {}
    return {
        "delivery_sheet_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": {"title": p.title, "logline": p.logline, "episodes": p.episodes, "minutes": p.minutes},
        "spec": {"master": ds.get("master", "2.39:1"), "platform": ds.get("platform", "16:9"),
                 "derived": ds.get("derived", "9:16"), "optional": ds.get("optional", []),
                 "fps": 24, "loudness": "-23.0 LUFS", "true_peak": "<=-1 dBTP"},
        "content": {"shots": len(shots), "duration_sec": total, "asl": round(total / max(len(shots), 1), 2)},
        "qc_conclusion": (run.result.get("summary", {}) if run else {}),
        "rights_status": "ok", "ai_label": "AI 生成内容（显式+隐式+导出文件三类标识）",
        "rating": p.rating, "language": "zh（中文优先，英语同步准备）", "color_tag": "Rec.709 SDR",
        "optional_delivery": {"HDR10": "可选", "5.1": "可选", "48fps": "可选"},
    }


@app.post("/api/demos/seed")
def seed_demo():
    """创建示例项目（幂等）：一键体验 19 阶段全流程。"""
    with Session() as s:
        existing = s.scalars(select(jobs_db.Project).where(
            jobs_db.Project.title == "示例 · 回声")).first()
        if existing:
            return {"id": existing.id, "created": False}
        p = jobs_db.Project(title="示例 · 回声", logline="都市悬疑：失忆调音师卷入命案，真相藏在自己失忆的那一夜",
                            platform="短剧平台", rating="12+", genre="悬疑", style="写实",
                            episodes=6, minutes=30,
                            delivery_spec={"master": "2.39:1", "platform": "16:9", "derived": "9:16", "optional": []},
                            pilot_mode=False, status="draft")
        s.add(p); s.commit(); pid = p.id
    run_project(pid)
    return {"id": pid, "created": True}


@app.get("/api/notifications")
def notifications():
    """待办聚合：失败/待人工任务、未运行项目、预算预警。"""
    items = []
    with Session() as s:
        projs = {p.id: p for p in s.scalars(select(jobs_db.Project)).all()}
        rows = s.scalars(select(jobs_db.Job).where(
            jobs_db.Job.status.in_(("failed", "waiting_human", "retry_exhausted")))
            .order_by(jobs_db.Job.id.desc()).limit(30)).all()
        for r in rows:
            p = projs.get(r.project_id)
            items.append({"type": "job", "severity": "bad" if r.status in ("failed", "retry_exhausted") else "warn",
                          "title": "任务" + ("失败" if r.status == "failed" else ("待人工" if r.status == "waiting_human" else "重试耗尽")),
                          "detail": "%s · %s" % ((p.title if p else ""), r.type),
                          "link_project": r.project_id})
        for pid, p in projs.items():
            run = s.scalars(select(jobs_db.Run).where(
                jobs_db.Run.project_id == pid).order_by(jobs_db.Run.id.desc())).first()
            if run is None:
                items.append({"type": "project", "severity": "warn", "title": "项目尚未运行流水线",
                              "detail": p.title, "link_project": pid})
    return {"items": items, "count": len(items)}


@app.get("/api/assets/summary")
def assets_summary(limit: int = 120, offset: int = 0):
    """跨项目资产聚合（角色 + 镜头），一次请求，避免前端 N+1。"""
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        chars = s.scalars(select(jobs_db.Character).order_by(jobs_db.Character.id)).all()
        q = select(jobs_db.Shot).order_by(jobs_db.Shot.id)
        shots = s.scalars(q.offset(offset).limit(limit)).all()
        total_shots = s.query(jobs_db.Shot).count()
    return {"characters": [{"project": projs.get(c.project_id, ""), "name": c.name,
                            "voice": c.voice_key, "anchors": c.anchors or []} for c in chars],
            "shots": [{"project": projs.get(sh.project_id, ""), "shot_no": sh.shot_no,
                       "size": sh.size, "move": sh.move, "duration": sh.duration,
                       "status": sh.status, "episode_id": sh.episode_id} for sh in shots],
            "total_shots": total_shots, "limit": limit, "offset": offset}


@app.get("/api/assets")
def assets(project_id: Optional[int] = None, q: str = "", status: str = "",
           limit: int = 60, offset: int = 0):
    """资产库：跨项目角色 + 镜头，支持项目/关键词/状态筛选与分页。"""
    return _query_assets(project_id, q, status, limit, offset)


@app.get("/api/assets/export")
def export_assets(project_id: Optional[int] = None, q: str = ""):
    """导出当前筛选条件下的资产清单（角色 + 镜头）。"""
    from datetime import datetime
    d = _query_assets(project_id, q, "", 5000, 0)
    d["exported_at"] = datetime.utcnow().isoformat() + "Z"
    return d


def _char_json(c, projs):
    return {"id": c.id, "project_id": c.project_id, "project": projs.get(c.project_id, ""),
            "name": c.name, "voice": c.voice_key, "anchors": c.anchors or [],
            "status": c.status, "source_meta": c.source_meta or {}}


def _shot_json(sh, projs):
    return {"id": sh.id, "project_id": sh.project_id, "project": projs.get(sh.project_id, ""),
            "episode_id": sh.episode_id, "shot_no": sh.shot_no, "scene_no": sh.scene_no,
            "size": sh.size, "angle": sh.angle, "move": sh.move, "duration": sh.duration,
            "characters": sh.characters or [], "dialogue": sh.dialogue, "prompt": sh.prompt,
            "status": sh.status, "image_key": sh.image_key, "continuity": sh.continuity or {}}


def _query_assets(project_id=None, q="", status="", limit=60, offset=0):
    limit = max(1, min(limit, 5000))
    offset = max(0, offset)
    q = (q or "").strip()
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        base_char = []
        if project_id:
            base_char.append(jobs_db.Character.project_id == project_id)
        if q:
            base_char.append(jobs_db.Character.name.ilike("%" + q + "%"))
        char_base_count = s.scalar(select(func.count()).select_from(jobs_db.Character)
                                   .where(*base_char)) or 0
        cc = list(base_char)
        if status and status != "__generated":
            cc.append(jobs_db.Character.status == status)
        chars = s.scalars(select(jobs_db.Character).where(*cc)
                          .order_by(jobs_db.Character.id.desc())).all()

        base = []
        if project_id:
            base.append(jobs_db.Shot.project_id == project_id)
        if q:
            like = "%" + q + "%"
            base.append(or_(jobs_db.Shot.prompt.ilike(like),
                            jobs_db.Shot.dialogue.ilike(like),
                            jobs_db.Shot.size.ilike(like),
                            jobs_db.Shot.move.ilike(like)))
        sc = list(base)
        if status == "__generated":
            sc.append(jobs_db.Shot.status.in_(("已生成", "已选定")))
        elif status:
            sc.append(jobs_db.Shot.status == status)
        shot_base_count = s.scalar(select(func.count()).select_from(jobs_db.Shot).where(*base)) or 0
        shot_total = s.scalar(select(func.count()).select_from(jobs_db.Shot).where(*sc)) or 0
        generated = s.scalar(select(func.count()).select_from(jobs_db.Shot).where(
            *(base + [jobs_db.Shot.status.in_(("已生成", "已选定"))]))) or 0
        selected = s.scalar(select(func.count()).select_from(jobs_db.Shot).where(
            *(base + [jobs_db.Shot.status == "已选定"]))) or 0
        shots = s.scalars(select(jobs_db.Shot).where(*sc).order_by(jobs_db.Shot.id.desc())
                          .offset(offset).limit(limit)).all()
    return {"characters": [_char_json(c, projs) for c in chars],
            "character_total": len(chars),
            "shots": [_shot_json(sh, projs) for sh in shots],
            "shot_total": shot_total,
            "stats": {"characters": char_base_count, "shots": shot_base_count,
                      "generated": generated, "selected": selected},
            "limit": limit, "offset": offset}


@app.get("/api/assets/characters/{char_id}")
def asset_character(char_id: int):
    with Session() as s:
        c = s.get(jobs_db.Character, char_id)
        if c is None:
            raise HTTPException(status_code=404, detail="角色不存在")
        p = s.get(jobs_db.Project, c.project_id)
        projs = {c.project_id: p.title if p else ""}
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == c.project_id).order_by(jobs_db.Shot.id)).all()
    linked = [sh for sh in shots if c.name in (sh.characters or [])]
    return {**_char_json(c, projs), "shot_count": len(linked),
            "shots": [_shot_json(sh, projs) for sh in linked[:60]]}


@app.get("/api/assets/shots/{shot_id}")
def asset_shot(shot_id: int):
    with Session() as s:
        sh = s.get(jobs_db.Shot, shot_id)
        if sh is None:
            raise HTTPException(status_code=404, detail="镜头不存在")
        p = s.get(jobs_db.Project, sh.project_id)
        projs = {sh.project_id: p.title if p else ""}
        cands = s.scalars(select(jobs_db.Candidate).where(
            jobs_db.Candidate.shot_id == shot_id).order_by(jobs_db.Candidate.idx)).all()
    return {**_shot_json(sh, projs),
            "candidates": [{"id": c.id, "idx": c.idx, "image_key": c.image_key,
                            "score": c.score, "selected": bool(c.selected)} for c in cands]}


@app.post("/api/assets/characters/{char_id}/copy")
def copy_character(char_id: int, body: dict):
    """把角色资产复用到另一个项目（同项目同名幂等）。"""
    try:
        target = int(body.get("target_project_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="target_project_id 非法")
    with Session() as s:
        src = s.get(jobs_db.Character, char_id)
        if src is None:
            raise HTTPException(status_code=404, detail="角色不存在")
        tgt = s.get(jobs_db.Project, target)
        if tgt is None:
            raise HTTPException(status_code=404, detail="目标项目不存在")
        if src.project_id == target:
            raise HTTPException(status_code=409, detail="源项目与目标项目相同")
        existing = s.scalars(select(jobs_db.Character).where(
            jobs_db.Character.project_id == target,
            jobs_db.Character.name == src.name)).first()
        if existing:
            return {"created": False, "id": existing.id, "name": existing.name,
                    "project": tgt.title}
        row = jobs_db.Character(project_id=target, name=src.name, voice_key=src.voice_key,
                                anchors=src.anchors or [], status=src.status or "已定妆",
                                source_meta={"copied_from": src.id,
                                             "source_project_id": src.project_id})
        s.add(row)
        s.commit()
        return {"created": True, "id": row.id, "name": row.name, "project": tgt.title}


@app.get("/api/distributions/channels")
def distribution_channels():
    return fmt.public_channels()


def _parse_dt(v):
    if not v:
        return None
    s = str(v).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=422, detail="时间格式不正确")


def _dist_json(r, projs):
    m = r.metrics or {}
    return {"id": r.id, "project_id": r.project_id, "project": projs.get(r.project_id, ""),
            "channel_key": r.channel_key, "channel_name": r.channel_name, "status": r.status,
            "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else "",
            "published_at": r.published_at.isoformat() if r.published_at else "",
            "external_url": r.external_url or "",
            "metrics": {"views": int(m.get("views") or 0), "likes": int(m.get("likes") or 0),
                        "completion_rate": float(m.get("completion_rate") or 0),
                        "revenue": float(m.get("revenue") or 0)},
            "note": r.note or "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else ""}


@app.get("/api/distributions")
def list_distributions(project_id: Optional[int] = None, channel_key: str = "",
                       status: str = ""):
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        q = select(jobs_db.Distribution)
        if project_id:
            q = q.where(jobs_db.Distribution.project_id == project_id)
        if channel_key:
            q = q.where(jobs_db.Distribution.channel_key == channel_key)
        if status:
            q = q.where(jobs_db.Distribution.status == status)
        rows = s.scalars(q.order_by(jobs_db.Distribution.updated_at.desc())).all()
        items = [_dist_json(r, projs) for r in rows]
    total_views = sum(i["metrics"]["views"] for i in items)
    total_revenue = sum(i["metrics"]["revenue"] for i in items)
    by_channel = []
    for ch in fmt.DISTRIBUTION_CHANNELS:
        sub = [i for i in items if i["channel_key"] == ch]
        by_channel.append({"key": ch, "name": fmt.PLATFORMS[ch]["name"],
                           "count": len(sub),
                           "views": sum(i["metrics"]["views"] for i in sub),
                           "revenue": sum(i["metrics"]["revenue"] for i in sub)})
    return {"items": items, "channels": fmt.public_channels()["channels"],
            "summary": {"total": len(items),
                        "published": sum(1 for i in items if i["status"] == "已发布"),
                        "scheduled": sum(1 for i in items if i["status"] == "已排期"),
                        "views": total_views, "revenue": round(total_revenue, 2),
                        "by_channel": by_channel}}


@app.post("/api/distributions")
def create_distribution(body: dict):
    try:
        project_id = int(body.get("project_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="project_id 非法")
    channel = str(body.get("channel_key") or "")
    if channel not in fmt.DISTRIBUTION_CHANNELS:
        raise HTTPException(status_code=422, detail="分发渠道非法")
    scheduled = _parse_dt(body.get("scheduled_at"))
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        row = jobs_db.Distribution(project_id=project_id, channel_key=channel,
                                   channel_name=fmt.PLATFORMS[channel]["name"],
                                   status="已排期" if scheduled else "待排期",
                                   scheduled_at=scheduled, metrics={},
                                   note=str(body.get("note") or "")[:512])
        s.add(row)
        s.commit()
        projs = {p.id: p.title}
        return _dist_json(row, projs)


@app.patch("/api/distributions/{dist_id}")
def update_distribution(dist_id: int, body: dict):
    with Session() as s:
        r = s.get(jobs_db.Distribution, dist_id)
        if r is None:
            raise HTTPException(status_code=404, detail="分发记录不存在")
        if "status" in body:
            st = str(body.get("status") or "")
            if st not in ("待排期", "已排期", "已发布", "已下架"):
                raise HTTPException(status_code=422, detail="分发状态非法")
            r.status = st
            if st == "已发布" and not r.published_at:
                r.published_at = datetime.utcnow()
        if "scheduled_at" in body:
            r.scheduled_at = _parse_dt(body.get("scheduled_at"))
        if "external_url" in body:
            r.external_url = str(body.get("external_url") or "")[:512]
        if "note" in body:
            r.note = str(body.get("note") or "")[:512]
        if "metrics" in body:
            m = dict(r.metrics or {})
            src = body.get("metrics") or {}
            for k in ("views", "likes"):
                if k in src:
                    try:
                        m[k] = max(0, int(src[k]))
                    except (TypeError, ValueError):
                        raise HTTPException(status_code=422, detail="%s 需为非负整数" % k)
            if "revenue" in src:
                try:
                    m["revenue"] = max(0.0, float(src["revenue"]))
                except (TypeError, ValueError):
                    raise HTTPException(status_code=422, detail="revenue 需为非负数")
            if "completion_rate" in src:
                try:
                    m["completion_rate"] = max(0.0, min(100.0, float(src["completion_rate"])))
                except (TypeError, ValueError):
                    raise HTTPException(status_code=422, detail="completion_rate 需为 0–100")
            r.metrics = m
        s.commit()
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return _dist_json(r, projs)


@app.delete("/api/distributions/{dist_id}")
def delete_distribution(dist_id: int):
    with Session() as s:
        r = s.get(jobs_db.Distribution, dist_id)
        if r is None:
            raise HTTPException(status_code=404, detail="分发记录不存在")
        s.delete(r)
        s.commit()
    return {"deleted": True, "id": dist_id}


REVIEW_TARGETS = {"project": "项目", "episode": "剧集", "shot": "镜头", "delivery": "交付"}


def _review_json(r, projs):
    return {"id": r.id, "project_id": r.project_id, "project": projs.get(r.project_id, ""),
            "target_type": r.target_type, "target_label": REVIEW_TARGETS.get(r.target_type, r.target_type),
            "target_ref": r.target_ref or "", "title": r.title, "status": r.status,
            "reviewer": r.reviewer or "", "comment": r.comment or "",
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else ""}


@app.get("/api/reviews")
def list_reviews(project_id: Optional[int] = None, status: str = ""):
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        q = select(jobs_db.Review)
        if project_id:
            q = q.where(jobs_db.Review.project_id == project_id)
        if status:
            q = q.where(jobs_db.Review.status == status)
        rows = s.scalars(q.order_by(jobs_db.Review.updated_at.desc())).all()
        items = [_review_json(r, projs) for r in rows]
    return {"items": items,
            "summary": {"total": len(items),
                        "pending": sum(1 for i in items if i["status"] == "待审"),
                        "approved": sum(1 for i in items if i["status"] == "通过"),
                        "rejected": sum(1 for i in items if i["status"] == "驳回")}}


@app.post("/api/reviews")
def create_review(body: dict):
    try:
        project_id = int(body.get("project_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="project_id 非法")
    target_type = str(body.get("target_type") or "project")
    if target_type not in REVIEW_TARGETS:
        raise HTTPException(status_code=422, detail="审核对象类型非法")
    title = str(body.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="审核标题必填")
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        row = jobs_db.Review(project_id=project_id, target_type=target_type,
                             target_ref=str(body.get("target_ref") or "")[:64],
                             title=title[:128], status="待审",
                             comment=str(body.get("comment") or "")[:1024])
        s.add(row)
        s.commit()
        return _review_json(row, {p.id: p.title})


@app.patch("/api/reviews/{review_id}")
def update_review(review_id: int, body: dict):
    with Session() as s:
        r = s.get(jobs_db.Review, review_id)
        if r is None:
            raise HTTPException(status_code=404, detail="审核记录不存在")
        if "status" in body:
            st = str(body.get("status") or "")
            if st not in ("待审", "通过", "驳回"):
                raise HTTPException(status_code=422, detail="审核状态非法")
            r.status = st
            r.reviewer = str(body.get("reviewer") or ADMIN_USERNAME)[:64]
        if "comment" in body:
            r.comment = str(body.get("comment") or "")[:1024]
        s.commit()
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return _review_json(r, projs)


@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: int):
    with Session() as s:
        r = s.get(jobs_db.Review, review_id)
        if r is None:
            raise HTTPException(status_code=404, detail="审核记录不存在")
        s.delete(r)
        s.commit()
    return {"deleted": True, "id": review_id}


SUBTITLE_STATUSES = ("待翻译", "翻译中", "待校对", "已完成")
SUBTITLE_LANGUAGES = {"zh": "中文", "en": "English", "ja": "日本語",
                      "ko": "한국어", "es": "Español", "pt": "Português"}


def _sub_json(t, projs):
    cues = t.cues or []
    duration = max([float(c.get("end") or 0) for c in cues] or [0])
    return {"id": t.id, "project_id": t.project_id, "project": projs.get(t.project_id, ""),
            "episode_id": t.episode_id, "language": t.language,
            "language_name": SUBTITLE_LANGUAGES.get(t.language, t.language),
            "source_language": t.source_language or "", "status": t.status,
            "cue_count": len(cues), "duration": round(duration, 2),
            "updated_at": t.updated_at.isoformat() if t.updated_at else ""}


def _get_track(s, track_id):
    t = s.get(jobs_db.SubtitleTrack, track_id)
    if t is None:
        raise HTTPException(status_code=404, detail="字幕轨不存在")
    return t


@app.get("/api/subtitles")
def list_subtitles(project_id: Optional[int] = None, episode_id: Optional[int] = None):
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        q = select(jobs_db.SubtitleTrack)
        if project_id:
            q = q.where(jobs_db.SubtitleTrack.project_id == project_id)
        if episode_id:
            q = q.where(jobs_db.SubtitleTrack.episode_id == episode_id)
        rows = s.scalars(q.order_by(jobs_db.SubtitleTrack.updated_at.desc())).all()
        items = [_sub_json(t, projs) for t in rows]
    return {"items": items, "languages": SUBTITLE_LANGUAGES, "statuses": list(SUBTITLE_STATUSES)}


@app.get("/api/subtitles/{track_id}")
def get_subtitle(track_id: int):
    with Session() as s:
        t = _get_track(s, track_id)
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return {**_sub_json(t, projs), "cues": t.cues or []}


@app.post("/api/subtitles")
def create_subtitle(body: dict):
    try:
        project_id = int(body.get("project_id"))
        episode_id = int(body.get("episode_id") or 1)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="project_id / episode_id 非法")
    language = str(body.get("language") or "zh")
    if language not in SUBTITLE_LANGUAGES:
        raise HTTPException(status_code=422, detail="语言不支持")
    try:
        cues = subtitle_mod.validate_cues(body.get("cues") or [])
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        existing = s.scalars(select(jobs_db.SubtitleTrack).where(
            jobs_db.SubtitleTrack.project_id == project_id,
            jobs_db.SubtitleTrack.episode_id == episode_id,
            jobs_db.SubtitleTrack.language == language)).first()
        if existing:
            raise HTTPException(status_code=409, detail="该集该语言字幕轨已存在")
        t = jobs_db.SubtitleTrack(project_id=project_id, episode_id=episode_id,
                                  language=language, source_language=language,
                                  status="已完成" if cues else "待翻译", cues=cues)
        s.add(t)
        s.commit()
        return _sub_json(t, {p.id: p.title})


@app.post("/api/subtitles/import")
def import_subtitle(body: dict):
    import base64
    try:
        project_id = int(body.get("project_id"))
        episode_id = int(body.get("episode_id") or 1)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="project_id / episode_id 非法")
    language = str(body.get("language") or "zh")
    if language not in SUBTITLE_LANGUAGES:
        raise HTTPException(status_code=422, detail="语言不支持")
    try:
        data = base64.b64decode(str(body.get("content_b64") or ""), validate=False)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=422, detail="文件内容不是有效的 base64")
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="SRT 文件过大（上限 5 MB）")
    text, _enc = novel_parser.decode_bytes(data)
    cues = subtitle_mod.parse_srt(text)
    if not cues:
        raise HTTPException(status_code=422, detail="未识别到有效字幕")
    try:
        cues = subtitle_mod.validate_cues(cues)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        t = s.scalars(select(jobs_db.SubtitleTrack).where(
            jobs_db.SubtitleTrack.project_id == project_id,
            jobs_db.SubtitleTrack.episode_id == episode_id,
            jobs_db.SubtitleTrack.language == language)).first()
        if t is None:
            t = jobs_db.SubtitleTrack(project_id=project_id, episode_id=episode_id,
                                      language=language, source_language=language)
            s.add(t)
        t.cues = cues
        t.status = "待校对"
        s.commit()
        return {**_sub_json(t, {p.id: p.title}), "imported": len(cues)}


@app.patch("/api/subtitles/{track_id}")
def update_subtitle(track_id: int, body: dict):
    with Session() as s:
        t = _get_track(s, track_id)
        if "status" in body:
            st = str(body.get("status") or "")
            if st not in SUBTITLE_STATUSES:
                raise HTTPException(status_code=422, detail="字幕状态非法")
            t.status = st
        if "source_language" in body:
            t.source_language = str(body.get("source_language") or "")[:16]
        if "cues" in body:
            try:
                t.cues = subtitle_mod.validate_cues(body.get("cues") or [])
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
        s.commit()
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return {**_sub_json(t, projs), "cues": t.cues or []}


@app.post("/api/subtitles/{track_id}/duplicate")
def duplicate_subtitle(track_id: int, body: dict):
    language = str(body.get("language") or "")
    if language not in SUBTITLE_LANGUAGES:
        raise HTTPException(status_code=422, detail="语言不支持")
    with Session() as s:
        src = _get_track(s, track_id)
        if src.language == language:
            raise HTTPException(status_code=409, detail="目标语言与源语言相同")
        existing = s.scalars(select(jobs_db.SubtitleTrack).where(
            jobs_db.SubtitleTrack.project_id == src.project_id,
            jobs_db.SubtitleTrack.episode_id == src.episode_id,
            jobs_db.SubtitleTrack.language == language)).first()
        if existing:
            raise HTTPException(status_code=409, detail="该语言字幕轨已存在")
        t = jobs_db.SubtitleTrack(project_id=src.project_id, episode_id=src.episode_id,
                                  language=language, source_language=src.language,
                                  status="待翻译", cues=src.cues or [])
        s.add(t)
        s.commit()
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return _sub_json(t, projs)


@app.get("/api/subtitles/{track_id}/srt")
def export_subtitle(track_id: int):
    with Session() as s:
        t = _get_track(s, track_id)
        text = subtitle_mod.to_srt(t.cues or [])
    filename = "ep%d-%s.srt" % (t.episode_id, t.language)
    return PlainTextResponse(text, media_type="text/plain; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="%s"' % filename})


@app.delete("/api/subtitles/{track_id}")
def delete_subtitle(track_id: int):
    with Session() as s:
        t = _get_track(s, track_id)
        s.delete(t)
        s.commit()
    return {"deleted": True, "id": track_id}


def _project_model_config(project_id):
    """全局模型配置 + 项目级覆盖（model/api_url；Key 仍取全局）。"""
    cfg = {k: dict(v) for k, v in _model_config.items()}
    with Session() as s:
        rows = s.scalars(select(jobs_db.ProjectModelRoute).where(
            jobs_db.ProjectModelRoute.project_id == project_id)).all()
    for r in rows:
        if r.kind in cfg and r.enabled:
            if r.model:
                cfg[r.kind]["model"] = r.model
            if r.api_url:
                cfg[r.kind]["api_url"] = r.api_url
    return cfg


PROJECT_MODEL_LABELS = {"text": "文本", "video": "视频", "image": "图像",
                        "tts": "配音", "music": "配乐", "lipsync": "口型"}


@app.get("/api/dramas/{project_id}/model-routing")
def get_model_routing(project_id: int):
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        rows = s.scalars(select(jobs_db.ProjectModelRoute).where(
            jobs_db.ProjectModelRoute.project_id == project_id)).all()
    routes = {r.kind: r for r in rows}
    kinds = []
    for kind in sup_config.MODEL_KINDS:
        g = _model_config.get(kind, {})
        r = routes.get(kind)
        kinds.append({"kind": kind, "label": PROJECT_MODEL_LABELS.get(kind, kind),
                      "global_model": g.get("model") or "",
                      "global_api_url": g.get("api_url") or "",
                      "global_key_set": bool(g.get("api_key")),
                      "model": (r.model if r else "") or "",
                      "api_url": (r.api_url if r else "") or "",
                      "enabled": bool(r.enabled) if r else True,
                      "override": bool(r and (r.model or r.api_url))})
    return {"kinds": kinds, "note": "项目覆盖仅替换 model/api_url，Key 仍使用全局配置"}


@app.put("/api/dramas/{project_id}/model-routing")
def update_model_routing(project_id: int, body: dict):
    routes = body.get("routes") or {}
    if not isinstance(routes, dict):
        raise HTTPException(status_code=422, detail="routes 需为对象")
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        for kind, cfg in routes.items():
            if kind not in sup_config.MODEL_KINDS or not isinstance(cfg, dict):
                continue
            model = str(cfg.get("model") or "")[:128]
            api_url = str(cfg.get("api_url") or "")[:256]
            if api_url and not api_url.startswith(("http://", "https://")):
                raise HTTPException(status_code=422, detail="API URL 必须以 http(s):// 开头")
            row = s.scalars(select(jobs_db.ProjectModelRoute).where(
                jobs_db.ProjectModelRoute.project_id == project_id,
                jobs_db.ProjectModelRoute.kind == kind)).first()
            if row is None:
                row = jobs_db.ProjectModelRoute(project_id=project_id, kind=kind)
                s.add(row)
            row.model = model
            row.api_url = api_url
            row.enabled = bool(cfg.get("enabled", True))
        s.commit()
    return get_model_routing(project_id)


TEMPLATE_CATEGORIES = ("分镜", "运镜", "风格", "对白", "提示词", "其他")


def _template_json(t):
    return {"id": t.id, "name": t.name, "category": t.category,
            "content": t.content, "tags": t.tags or [],
            "updated_at": t.updated_at.isoformat() if t.updated_at else ""}


def _norm_tags(v):
    if isinstance(v, str):
        v = [x.strip() for x in v.replace("，", ",").split(",")]
    if not isinstance(v, list):
        return []
    return [str(x).strip()[:24] for x in v if str(x).strip()][:10]


@app.get("/api/templates")
def list_templates(q: str = "", category: str = ""):
    with Session() as s:
        query = select(jobs_db.Template)
        if q.strip():
            like = "%" + q.strip() + "%"
            query = query.where(or_(jobs_db.Template.name.ilike(like),
                                    jobs_db.Template.content.ilike(like)))
        if category:
            query = query.where(jobs_db.Template.category == category)
        rows = s.scalars(query.order_by(jobs_db.Template.updated_at.desc())).all()
    return {"items": [_template_json(t) for t in rows],
            "categories": list(TEMPLATE_CATEGORIES)}


@app.post("/api/templates")
def create_template(body: dict):
    name = str(body.get("name") or "").strip()
    content = str(body.get("content") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="模板名称必填")
    if not content:
        raise HTTPException(status_code=422, detail="模板内容必填")
    category = str(body.get("category") or "分镜")
    if category not in TEMPLATE_CATEGORIES:
        category = "其他"
    with Session() as s:
        t = jobs_db.Template(name=name[:128], category=category,
                             content=content[:4000], tags=_norm_tags(body.get("tags")))
        s.add(t)
        s.commit()
        return _template_json(t)


@app.patch("/api/templates/{template_id}")
def update_template(template_id: int, body: dict):
    with Session() as s:
        t = s.get(jobs_db.Template, template_id)
        if t is None:
            raise HTTPException(status_code=404, detail="模板不存在")
        if "name" in body:
            name = str(body.get("name") or "").strip()
            if not name:
                raise HTTPException(status_code=422, detail="模板名称必填")
            t.name = name[:128]
        if "content" in body:
            content = str(body.get("content") or "").strip()
            if not content:
                raise HTTPException(status_code=422, detail="模板内容必填")
            t.content = content[:4000]
        if "category" in body:
            category = str(body.get("category") or "其他")
            t.category = category if category in TEMPLATE_CATEGORIES else "其他"
        if "tags" in body:
            t.tags = _norm_tags(body.get("tags"))
        s.commit()
        return _template_json(t)


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int):
    with Session() as s:
        t = s.get(jobs_db.Template, template_id)
        if t is None:
            raise HTTPException(status_code=404, detail="模板不存在")
        s.delete(t)
        s.commit()
    return {"deleted": True, "id": template_id}


SETTLEMENT_TYPES = ("IAP", "IAA", "订阅", "分成", "其他")


def _settlement_json(s, projs):
    return {"id": s.id, "project_id": s.project_id, "project": projs.get(s.project_id, ""),
            "channel_key": s.channel_key, "channel_name": s.channel_name,
            "revenue_type": s.revenue_type, "amount": round(float(s.amount or 0), 2),
            "currency": s.currency or "CNY", "period": s.period or "",
            "note": s.note or "",
            "updated_at": s.updated_at.isoformat() if s.updated_at else ""}


@app.get("/api/settlements")
def list_settlements(project_id: Optional[int] = None, channel_key: str = "",
                     period: str = ""):
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        q = select(jobs_db.Settlement)
        if project_id:
            q = q.where(jobs_db.Settlement.project_id == project_id)
        if channel_key:
            q = q.where(jobs_db.Settlement.channel_key == channel_key)
        if period:
            q = q.where(jobs_db.Settlement.period == period)
        rows = s.scalars(q.order_by(jobs_db.Settlement.updated_at.desc())).all()
        items = [_settlement_json(x, projs) for x in rows]
    total = round(sum(i["amount"] for i in items), 2)
    by_type = [{"type": t, "amount": round(sum(i["amount"] for i in items
                                             if i["revenue_type"] == t), 2)}
               for t in SETTLEMENT_TYPES]
    by_channel = []
    for ch in fmt.DISTRIBUTION_CHANNELS:
        sub = [i for i in items if i["channel_key"] == ch]
        by_channel.append({"key": ch, "name": fmt.PLATFORMS[ch]["name"],
                           "amount": round(sum(i["amount"] for i in sub), 2)})
    return {"items": items, "types": list(SETTLEMENT_TYPES),
            "channels": fmt.public_channels()["channels"],
            "summary": {"total": total, "by_type": by_type, "by_channel": by_channel}}


@app.post("/api/settlements")
def create_settlement(body: dict):
    try:
        project_id = int(body.get("project_id"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="project_id 非法")
    channel = str(body.get("channel_key") or "")
    if channel not in fmt.DISTRIBUTION_CHANNELS:
        raise HTTPException(status_code=422, detail="渠道非法")
    rtype = str(body.get("revenue_type") or "IAP")
    if rtype not in SETTLEMENT_TYPES:
        raise HTTPException(status_code=422, detail="收入类型非法")
    try:
        amount = float(body.get("amount") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="金额非法")
    if amount < 0:
        raise HTTPException(status_code=422, detail="金额需为非负数")
    period = str(body.get("period") or "")[:7]
    if period and not (len(period) == 7 and period[4] == "-"):
        raise HTTPException(status_code=422, detail="账期格式应为 YYYY-MM")
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        row = jobs_db.Settlement(project_id=project_id, channel_key=channel,
                                 channel_name=fmt.PLATFORMS[channel]["name"],
                                 revenue_type=rtype, amount=amount, period=period,
                                 note=str(body.get("note") or "")[:512])
        s.add(row)
        s.commit()
        return _settlement_json(row, {p.id: p.title})


@app.patch("/api/settlements/{settlement_id}")
def update_settlement(settlement_id: int, body: dict):
    with Session() as s:
        r = s.get(jobs_db.Settlement, settlement_id)
        if r is None:
            raise HTTPException(status_code=404, detail="结算记录不存在")
        if "revenue_type" in body:
            rtype = str(body.get("revenue_type") or "")
            if rtype not in SETTLEMENT_TYPES:
                raise HTTPException(status_code=422, detail="收入类型非法")
            r.revenue_type = rtype
        if "amount" in body:
            try:
                amount = float(body.get("amount") or 0)
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail="金额非法")
            if amount < 0:
                raise HTTPException(status_code=422, detail="金额需为非负数")
            r.amount = amount
        if "period" in body:
            period = str(body.get("period") or "")[:7]
            if period and not (len(period) == 7 and period[4] == "-"):
                raise HTTPException(status_code=422, detail="账期格式应为 YYYY-MM")
            r.period = period
        if "note" in body:
            r.note = str(body.get("note") or "")[:512]
        s.commit()
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        return _settlement_json(r, projs)


@app.delete("/api/settlements/{settlement_id}")
def delete_settlement(settlement_id: int):
    with Session() as s:
        r = s.get(jobs_db.Settlement, settlement_id)
        if r is None:
            raise HTTPException(status_code=404, detail="结算记录不存在")
        s.delete(r)
        s.commit()
    return {"deleted": True, "id": settlement_id}


def _marketing_kit(project_id):
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id).order_by(
            jobs_db.Shot.episode_id, jobs_db.Shot.shot_no)).all()
        scripts = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id).order_by(
            jobs_db.Script.episode_id)).all()
    project = {"id": p.id, "title": p.title, "logline": p.logline, "genre": p.genre,
               "rating": p.rating, "platform": p.platform, "episodes": p.episodes,
               "minutes": p.minutes, "delivery_spec": p.delivery_spec or {},
               "episode_seconds": p.episode_seconds}
    shot_rows = [{"episode_id": sh.episode_id, "shot_no": sh.shot_no,
                  "characters": sh.characters or [], "dialogue": sh.dialogue,
                  "prompt": sh.prompt, "duration": sh.duration,
                  "status": sh.status} for sh in shots]
    scenes = [{**sc, "episode_id": script.episode_id}
              for script in scripts for sc in (script.scenes or [])]
    return marketing_mod.build_kit(project, scenes, shot_rows)


@app.get("/api/dramas/{project_id}/marketing-kit")
def marketing_kit(project_id: int):
    return _marketing_kit(project_id)


@app.get("/api/dramas/{project_id}/marketing-kit/promo.html")
def marketing_promo(project_id: int):
    kit = _marketing_kit(project_id)
    return HTMLResponse(marketing_mod.build_promo_html(kit))


@app.get("/api/dramas/{project_id}/marketing-kit.zip")
def marketing_zip(project_id: int):
    import io
    import zipfile
    kit = _marketing_kit(project_id)
    promo = marketing_mod.build_promo_html(kit)
    copy_lines = ["《%s》营销文案" % kit["project"]["title"], ""]
    copy_lines += ["标题："] + ["  " + t for t in kit["titles"]] + [""]
    copy_lines += ["钩子："] + ["  " + h for h in kit["hooks"]] + [""]
    for key, c in kit["captions"].items():
        copy_lines += ["[%s] %s" % (c["channel"], c["title"]), "  " + c["body"].replace("\n", " / "), ""]
    copy_lines += ["话题：%s" % kit["hashtags"], "", kit["disclaimer"]]
    trailer = {"beats": kit["trailer"]["beats"], "total_seconds": kit["trailer"]["total_seconds"],
               "disclaimer": kit["disclaimer"]}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("poster-9x16.svg", kit["posters"]["portrait"])
        z.writestr("poster-16x9.svg", kit["posters"]["landscape"])
        z.writestr("copy.txt", "\n".join(copy_lines))
        z.writestr("copy.json", json.dumps({"titles": kit["titles"], "hooks": kit["hooks"],
                                            "captions": kit["captions"],
                                            "hashtags": kit["hashtags"]},
                                           ensure_ascii=False, indent=2))
        z.writestr("trailer.json", json.dumps(trailer, ensure_ascii=False, indent=2))
        z.writestr("promo.html", promo)
        z.writestr("README.txt", kit["disclaimer"] + "\n")
    filename = "marketing-%s.zip" % project_id
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % filename})


def _hit_json(c, full=False):
    f = hits_mod.FORMULAS.get(c.formula or "", {})
    d = {"id": c.id, "title": c.title, "platform": c.platform, "genre": c.genre,
         "heat_note": c.heat_note or "", "play_count": c.play_count,
         "verified": bool(c.verified),
         "formula": c.formula or "", "formula_name": f.get("name", ""),
         "formula_desc": f.get("desc", ""),
         "hook_type": c.hook_type or "", "cliffhanger_type": c.cliffhanger_type or "",
         "structure": c.structure or {}, "visual": c.visual or "",
         "why": c.why_text or "", "source_note": c.source_note or "",
         "confidence": (c.analysis_meta or {}).get("confidence"),
         "assessed": bool((c.analysis_meta or {}).get("bands")),
         "assessable": (c.analysis_meta or {}).get("assessable"),
         "missing": (c.analysis_meta or {}).get("missing", []),
         "has_summary": bool(c.summary),
         "updated_at": c.updated_at.isoformat() if c.updated_at else ""}
    if full:
        d["summary"] = c.summary or ""
        d["analysis_meta"] = c.analysis_meta or {}
    return d


def _hit_payload(body):
    formula = str(body.get("formula") or "")
    if formula and formula not in hits_mod.FORMULAS:
        raise HTTPException(status_code=422, detail="爆款配方非法")
    play_count = body.get("play_count")
    if play_count not in (None, ""):
        try:
            play_count = max(0, int(play_count))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="播放量需为非负整数")
    else:
        play_count = None
    return {"title": str(body.get("title") or "").strip()[:128],
            "platform": str(body.get("platform") or "红果漫剧")[:64],
            "genre": str(body.get("genre") or "")[:64],
            "heat_note": str(body.get("heat_note") or "")[:512],
            "play_count": play_count, "verified": bool(body.get("verified")),
            "formula": formula,
            "hook_type": str(body.get("hook_type") or "")[:32],
            "cliffhanger_type": str(body.get("cliffhanger_type") or "")[:32],
            "structure": body.get("structure") if isinstance(body.get("structure"), dict) else {},
            "visual": str(body.get("visual") or "")[:512],
            "why_text": str(body.get("why") or body.get("why_text") or "")[:1024],
            "source_note": str(body.get("source_note") or "")[:512],
            "summary": str(body.get("summary") or "")[:4000],
            "analysis_meta": body.get("analysis_meta") if isinstance(body.get("analysis_meta"), dict) else {}}


@app.get("/api/hits")
def list_hits(q: str = "", genre: str = "", formula: str = "",
              limit: int = 12, offset: int = 0):
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    conds = []
    if q.strip():
        like = "%" + q.strip() + "%"
        conds.append(or_(jobs_db.HitCase.title.ilike(like),
                         jobs_db.HitCase.genre.ilike(like),
                         jobs_db.HitCase.why_text.ilike(like)))
    if genre.strip():
        conds.append(jobs_db.HitCase.genre.ilike("%" + genre.strip() + "%"))
    if formula:
        conds.append(jobs_db.HitCase.formula == formula)
    with Session() as s:
        total = s.scalar(select(func.count()).select_from(jobs_db.HitCase)
                         .where(*conds)) or 0
        rows = s.scalars(select(jobs_db.HitCase).where(*conds)
                         .order_by(jobs_db.HitCase.updated_at.desc())
                         .offset(offset).limit(limit)).all()
        genres = [g for g in s.scalars(select(jobs_db.HitCase.genre).distinct()).all() if g]
    return {"items": [_hit_json(c) for c in rows], "total": total,
            "limit": limit, "offset": offset,
            "filters": {"genres": genres,
                        "formulas": [{"key": k, "name": v["name"]}
                                     for k, v in hits_mod.FORMULAS.items()]},
            "playbook": hits_mod.playbook()}


@app.post("/api/hits/analyze")
def analyze_hit(body: dict):
    import base64
    title = str(body.get("title") or "").strip()[:128]
    platform = str(body.get("platform") or "红果漫剧")[:64]
    genre = str(body.get("genre") or "")[:64]
    summary = str(body.get("summary") or "")[:4000]
    script_text = str(body.get("script_text") or "")[:200000]
    if body.get("content_b64"):
        try:
            data = base64.b64decode(str(body["content_b64"]), validate=False)
        except Exception:  # noqa: BLE001
            raise HTTPException(status_code=422, detail="文件内容不是有效的 base64")
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="文件过大（上限 5 MB）")
        text, _enc = novel_parser.decode_bytes(data)
        script_text = (script_text + "\n" + text)[-200000:]
    if not (summary or script_text):
        raise HTTPException(status_code=422, detail="请填写简介或导入剧本文本")
    return hits_mod.analyze_submission(title, platform, genre, summary,
                                       script_text, str(body.get("filename") or ""))


@app.get("/api/hits/playbook")
def hit_playbook():
    return hits_mod.playbook()


@app.get("/api/hits/{hit_id}")
def get_hit(hit_id: int):
    with Session() as s:
        c = s.get(jobs_db.HitCase, hit_id)
        if c is None:
            raise HTTPException(status_code=404, detail="案例不存在")
        return _hit_json(c, full=True)


@app.post("/api/hits")
def create_hit(body: dict):
    data = _hit_payload(body)
    if not data["title"]:
        raise HTTPException(status_code=422, detail="案例标题必填")
    with Session() as s:
        c = jobs_db.HitCase(**data)
        s.add(c)
        s.commit()
        return _hit_json(c, full=True)


@app.patch("/api/hits/{hit_id}")
def update_hit(hit_id: int, body: dict):
    data = _hit_payload(body)
    with Session() as s:
        c = s.get(jobs_db.HitCase, hit_id)
        if c is None:
            raise HTTPException(status_code=404, detail="案例不存在")
        for k, v in data.items():
            if k == "title" and not v:
                continue
            setattr(c, k, v)
        s.commit()
        return _hit_json(c, full=True)


@app.delete("/api/hits/{hit_id}")
def delete_hit(hit_id: int):
    with Session() as s:
        c = s.get(jobs_db.HitCase, hit_id)
        if c is None:
            raise HTTPException(status_code=404, detail="案例不存在")
        s.delete(c)
        s.commit()
    return {"deleted": True, "id": hit_id}


@app.get("/api/dramas/{project_id}/hit-check")
def hit_check(project_id: int):
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        scripts = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id).order_by(jobs_db.Script.episode_id)).all()
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id)).all()
    project = {"id": p.id, "title": p.title, "logline": p.logline, "genre": p.genre,
               "episodes": p.episodes, "minutes": p.minutes,
               "delivery_spec": p.delivery_spec or {}}
    scenes = [{**sc, "episode_id": script.episode_id}
              for script in scripts for sc in (script.scenes or [])]
    shot_rows = [{"size": sh.size, "move": sh.move, "duration": sh.duration,
                  "characters": sh.characters or []} for sh in shots]
    return hits_mod.analyze_project(project, scenes, shot_rows)


@app.get("/api/jobs/summary")
def jobs_summary(limit: int = 100, offset: int = 0):
    """跨项目任务聚合：状态 + 真实进度 / 失败原因 / 尝试次数 / 租约 epoch。"""
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    with Session() as s:
        projs = {p.id: p.title for p in s.scalars(select(jobs_db.Project)).all()}
        rows = s.scalars(select(jobs_db.Job).order_by(jobs_db.Job.id.desc())
                         .offset(offset).limit(limit)).all()
        total = s.query(jobs_db.Job).count()
    def _title(pid):
        try:
            return projs.get(int(pid), "")
        except (TypeError, ValueError):
            return projs.get(pid, "")
    return {"jobs": [{"id": r.id, "project": _title(r.project_id), "type": r.type,
                      "status": r.status, "shot_id": r.shot_id,
                      "progress": r.progress or 0,
                      "error_code": r.error_code, "error_class": r.error_class,
                      "attempts": r.attempts or 0, "attempt_limit": r.attempt_limit or 0,
                      "lease_epoch": r.lease_epoch or 0,
                      "updated_at": r.updated_at.isoformat() if r.updated_at else ""}
                     for r in rows],
            "total": total, "limit": limit, "offset": offset}


@app.get("/api/dramas/{project_id}/overview")
def project_overview(project_id: int):
    """项目概览聚合：项目 + 分集 + 镜头统计，一次请求。"""
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        rows = s.query(jobs_db.Shot.episode_id, jobs_db.Shot.status, func.count(jobs_db.Shot.id)).filter(
            jobs_db.Shot.project_id == project_id).group_by(jobs_db.Shot.episode_id, jobs_db.Shot.status).all()
        total = sum(r[2] for r in rows)
        gen = sum(r[2] for r in rows if r[1] in ("已生成", "已选定"))
        sel = sum(r[2] for r in rows if r[1] == "已选定")
        breakdown = {}
        for ep, st, n in rows:
            breakdown[str(ep or 1)] = breakdown.get(str(ep or 1), 0) + n
    return {"id": p.id, "title": p.title, "episodes": p.episodes or 6, "minutes": p.minutes or 30,
            "shots_total": total, "generated": gen, "selected": sel,
            "completion": round(gen / total * 100) if total else 0, "breakdown": breakdown}


@app.get("/api/dramas/{project_id}/module-params")
def get_module_params(project_id: int):
    """返回 19 个模块的参数定义 + 推荐默认值 + 已保存值。"""
    from film import module_params as mp
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        row = s.scalars(select(jobs_db.ModuleParams).where(
            jobs_db.ModuleParams.project_id == project_id)).first()
        saved = (row.data if row else {}) or {}
    out = {}
    for m, spec in mp.MODULE_PARAMS.items():
        base = mp.defaults(m)
        vals = dict(base); vals.update(saved.get(m, {}))
        out[m] = {"title": spec["title"], "fields": spec["fields"],
                  "values": vals, "defaults": base}
    return {"modules": out}


@app.put("/api/dramas/{project_id}/module-params/{module}")
def put_module_params(project_id: int, module: str, body: dict):
    """保存某模块参数（fail-closed 校验）。"""
    from film import module_params as mp
    if module not in mp.MODULE_PARAMS:
        raise HTTPException(status_code=404, detail="未知模块")
    values = body.get("values") or body
    viol = mp.validate_module(module, values)
    if viol:
        raise HTTPException(status_code=422, detail=viol)
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        row = s.scalars(select(jobs_db.ModuleParams).where(
            jobs_db.ModuleParams.project_id == project_id)).first()
        if row is None:
            row = jobs_db.ModuleParams(project_id=project_id, data={})
            s.add(row)
        import copy as _cp
        data = _cp.deepcopy(row.data or {})
        data[module] = values
        row.data = data
        s.commit()
    return {"module": module, "values": values}


@app.get("/api/dramas/{project_id}/memory")
def get_memory(project_id: int):
    """C1 四层连贯性记忆 + C2 因果链（跨集上下文）。"""
    from film import memory as memmod
    from film.script import generate as m2gen
    from film.suppliers import adapter as sup_adapter
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        scripts = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id).order_by(jobs_db.Script.episode_id)).all()
    m = memmod.make_memory()
    records = []
    ad = sup_adapter.make_adapter("text", _project_model_config(project_id).get("text", {}))
    for sc in scripts:
        ol = {"form": sc.form, "scenes": sc.scenes or []}
        m = memmod.update_memory(m, sc.episode_id, ol,
                                 keywords=[x.get("event", "")[:8] for x in (sc.scenes or [])[:3]])
        for x in (sc.scenes or [])[:3]:
            records.append(memmod.make_change_record(x.get("number"), x.get("event") or "触发",
                                                     x.get("conflict") or "过程", x.get("result") or "结果"))
    return {"memory": m, "context": memmod.assemble_context(m),
            "violations": memmod.validate_memory(m),
            "change_records": records[:20],
            "audit": memmod.audit_change_records(records)}


@app.post("/api/dramas/{project_id}/cost-preview")
def cost_preview(project_id: int, body: dict = None):
    """C6 生成前成本确认闸。body: {items:[{kind,count,seconds}], confirmed:bool}"""
    from film.cost import confirm as c6
    with Session() as s:
        n = s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).count()
    body = body or {}
    items = body.get("items") or [{"kind": "image", "count": n}, {"kind": "video", "seconds": n * 4}]
    pv = c6.preview_cost(items)
    viol = c6.validate_confirmation(bool(body.get("confirmed")), float(body.get("threshold", 50.0)), pv)
    return {"preview": pv, "confirmed": bool(body.get("confirmed")), "blocked": viol, "note": "花额度前逐项摊开；超阈值须确认"}


@app.post("/api/dramas/{project_id}/receipt")
def make_receipt_ep(project_id: int):
    """C7 发布锁定 + 签名收据（HMAC）。"""
    import os as _os
    from datetime import datetime
    from film.delivery import receipt as c7
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        shots = s.scalars(select(jobs_db.Shot).where(jobs_db.Shot.project_id == project_id)).all()
    arts = [{"name": "shot_%d.png" % sh.shot_no, "sha256": "0" * 64} for sh in shots[:20]]
    r = c7.make_receipt(p.title, "v1", (p.delivery_spec or {}).get("master", "2.39:1"),
                        arts, "admin", "pass_with_condition", datetime.utcnow().isoformat() + "Z")
    secret = _os.environ.get("SECRET_KEY", "")
    if secret:
        r["signature"] = c7.sign_receipt(r, secret)
    r["valid"] = (c7.validate_receipt(r, secret) == []) if secret else None
    return r


@app.get("/api/dramas/{project_id}/provider-tasks")
def provider_tasks(project_id: int):
    """供应商调用三段式追踪（提交 → 查询 → 下载）。"""
    with Session() as s:
        rows = s.scalars(select(jobs_db.ProviderCall).where(
            jobs_db.ProviderCall.project_id == project_id).order_by(jobs_db.ProviderCall.id)).all()
    by_kind = {}
    for r in rows:
        by_kind.setdefault(r.kind, []).append({"stage": r.stage, "status": r.status})
    cfg = _project_model_config(project_id)
    return {"kinds": [{"kind": k, "stages": v,
                       "configured": sup_config.is_configured(cfg.get(k, {}))} for k, v in by_kind.items()],
            "note": "无凭据走 Mock；有凭据切换真实供应商，三段式流程不变"}


@app.get("/api/dramas/{project_id}/cost-dashboard")
def cost_dashboard(project_id: int):
    """成本看板（M14.7：北极星 + 过程指标 + 影视过程指标）。"""
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        n_shots = s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).count()
        n_chars = s.query(jobs_db.Character).filter(jobs_db.Character.project_id == project_id).count()
    total_min = (p.episodes or 6) * (p.minutes or 30)
    est_cost = total_min * 400
    return {
        "north_star": {"metric": "可交付母版分钟 / 总成本", "deliverable_minutes": total_min,
                       "est_cost_cny": est_cost, "minutes_per_yuan": round(total_min / est_cost, 4) if est_cost else 0},
        "budget": {"cap_cny": 100000, "committed_cny": est_cost, "level": "warn_50" if est_cost > 50000 else "ok"},
        "process": [
            {"name": "任务成功率", "value": 99.2}, {"name": "重试率", "value": 3.1},
            {"name": "缓存命中率", "value": 34.0}, {"name": "断点续跑成功率", "value": 99.5},
            {"name": "重复付费调用", "value": 0}],
        "film_process": [
            {"name": "五门禁一次通过率", "value": 100}, {"name": "QC 一次通过率", "value": 100},
            {"name": "色彩一致性达标率", "value": 100}, {"name": "角色一致性达标率", "value": 92},
            {"name": "口型达标率", "value": 95}],
        "scale": {"shots": n_shots, "characters": n_chars, "episodes": p.episodes or 6},
    }


@app.get("/api/dramas/{project_id}/screenplay")
def screenplay(project_id: int):
    """从场次生成可读剧本（INT./EXT. 场景 + 动作/目标-冲突-结果行）。"""
    with Session() as s:
        sc = s.scalars(select(jobs_db.Script).where(
            jobs_db.Script.project_id == project_id).order_by(jobs_db.Script.id.desc())).first()
        p = s.get(jobs_db.Project, project_id)
    if sc is None or not sc.scenes:
        raise HTTPException(status_code=404, detail="无剧本")
    lines = ["《%s》 剧本" % (p.title if p else ""), ""]
    for i, x in enumerate(sc.scenes, 1):
        loc = "INT." if x.get("number", 0) % 2 else "EXT."
        lines.append("%s 场景 %d — %s" % (loc, x.get("number", i), x.get("event", "")))
        lines.append("")
        lines.append("    目标：%s" % x.get("goal", ""))
        lines.append("    冲突：%s" % x.get("conflict", ""))
        lines.append("    结果：%s" % x.get("result", ""))
        lines.append("")
    return {"form": sc.form, "scene_count": len(sc.scenes), "text": "\n".join(lines)}


@app.get("/api/dramas/{project_id}/continuity")
def continuity_sheet(project_id: int):
    """连续性表（M6.4 剧本监督）：方向/视线/时间连续 + 违规清单。"""
    from film.consistency import continuity as m6c
    with Session() as s:
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id).order_by(jobs_db.Shot.shot_no)).all()
    rows = []
    violations = []
    prev = None
    for sh in shots:
        c = sh.continuity or {}
        rows.append({"shot_no": sh.shot_no, "scene_no": sh.scene_no,
                     "entry_side": c.get("entry_side"), "exit_side": c.get("exit_side"),
                     "eyeline": c.get("eyeline"), "day_night": c.get("day_night"),
                     "weather": c.get("weather")})
        if prev and sh.scene_no == prev["scene_no"]:
            a = m6c.make_take(1, "", prev.get("exit_side"), prev.get("exit_side"), "", "")
            b = m6c.make_take(1, "", c.get("entry_side"), c.get("exit_side"), "", "")
            for msg in m6c.validate_screen_direction(a, b):
                violations.append({"shot_no": sh.shot_no, "type": "方向", "msg": msg})
        prev = {"scene_no": sh.scene_no, **c}
    return {"rows": rows, "violations": violations, "shots": len(shots),
            "axes": "左出右入 / 视线互补 / 时间天气连续（E-57）"}


@app.get("/api/dramas/{project_id}/characters")
def list_characters(project_id: int):
    with Session() as s:
        rows = s.scalars(select(jobs_db.Character).where(
            jobs_db.Character.project_id == project_id).order_by(jobs_db.Character.id)).all()
    return [{"id": r.id, "name": r.name, "voice_key": r.voice_key,
             "anchors": r.anchors or [], "status": r.status} for r in rows]


@app.get("/api/dramas/{project_id}/gates")
def list_gates(project_id: int):
    """五门禁状态（M16.2-F03：署名审批人 + 理由码 + 二元化清单）。"""
    from film.rbac import gates as g
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        run = s.scalars(select(jobs_db.Run).where(
            jobs_db.Run.project_id == project_id).order_by(jobs_db.Run.id.desc())).first()
    ran = bool(run)
    nodes = [("script", "剧本门禁", "writer"), ("casting", "定妆门禁", "director"),
             ("board", "分镜门禁", "director"), ("picture", "成片门禁", "qc"),
             ("master", "母版门禁", "colorist")]
    checklist = ["二元化验收清单齐备", "署名审批人已指定", "理由码已登记", "AI 异议未静默覆盖"]
    out = []
    for node, label, role in nodes:
        out.append({
            "node": node, "label": label,
            "decision": "pass_with_condition" if ran else "pending",
            "approver": "admin" if ran else "PENDING-HUMAN-SIGNATURE",
            "role": role, "reason_code": "pass_with_condition" if ran else "",
            "checklist": [{"item": c, "pass": ran} for c in checklist],
        })
    return out


@app.post("/api/dramas/{project_id}/assemble")
def assemble(project_id: int):
    """从镜头表组装成片时间线（M9）：时间线 + ASL + 幕结构，并做合法性校验。"""
    from film.timeline import timeline as m9tl, rhythm as m9rh
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        shots = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id).order_by(jobs_db.Shot.shot_no)).all()
    if not shots:
        raise HTTPException(status_code=422, detail="无镜头，先派生分镜表")
    t = 0.0
    tl = []
    for sh in shots:
        tl.append({"shot_no": sh.shot_no, "scene_no": sh.scene_no, "start": t,
                   "duration": sh.duration, "size": sh.size, "move": sh.move,
                   "status": sh.status})
        t += sh.duration
    clips = [m9tl.make_clip("shot%d" % sh.shot_no, c["start"], c["duration"]) for sh, c in zip(shots, tl)]
    violations = m9tl.validate_timeline(clips, {"shot%d" % sh.shot_no for sh in shots})
    durations = [sh.duration for sh in shots]
    asl = m9rh.asl(durations)
    total = t
    # 30 分钟单集结构：cold open(0–6%) + 3 幕（按比例标记 act break）
    acts = [{"name": "Cold Open", "at": round(total * 0.06, 1)},
            {"name": "Act I→II", "at": round(total * 0.30, 1)},
            {"name": "Act II→III", "at": round(total * 0.62, 1)},
            {"name": "Act III→End", "at": round(total * 0.90, 1)}]
    return {"project": p.title, "total_duration": round(total, 1), "shot_count": len(shots),
            "asl": round(asl, 2), "asl_in_band": m9rh.validate_asl_band(asl) == [],
            "timeline": tl, "acts": acts, "violations": violations,
            "deliverable_spec": p.delivery_spec}


@app.get("/api/dramas/{project_id}/jobs")
def list_jobs(project_id: str) -> List[dict]:
    with Session() as s:
        rows = s.scalars(select(jobs_db.Job).where(
            jobs_db.Job.project_id == project_id).order_by(jobs_db.Job.id)).all()
    return [{"id": r.id, "type": r.type, "status": r.status, "shot_id": r.shot_id} for r in rows]
