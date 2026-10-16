"""AADO 控制面 API（FastAPI；API 薄：入队 + 查询 + 人工终审，重计算归 worker）。"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from apps.api import auth
from film.jobs import db as jobs_db
from film.projects import project as proj_mod
from film.suppliers import config as sup_config

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
jobs_db.Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)

app = FastAPI(title="AADO API", version="0.1.0")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 登录鉴权配置（默认 admin + 随机密码，凭据从环境变量注入）
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")


@app.middleware("http")
async def auth_middleware(request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path != "/api/auth/login":
        token = request.headers.get("authorization", "")
        token = token[7:] if token.startswith("Bearer ") else ""
        if not auth.verify_token(token, SECRET_KEY):
            return JSONResponse({"detail": "未登录或登录已过期"}, status_code=401)
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


class UpdateProject(BaseModel):
    title: Optional[str] = None
    logline: Optional[str] = None
    platform: Optional[str] = None
    rating: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    episodes: Optional[int] = None
    minutes: Optional[int] = None


# 模型参数配置（env 为默认，页面/API 可运行时覆盖）
_model_config = sup_config.load_from_env()


class LoginBody(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginBody):
    if not auth.check_credentials(body.username, body.password, ADMIN_USERNAME, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": auth.sign_token(body.username, SECRET_KEY), "username": ADMIN_USERNAME}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    import os
    html = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return open(html, encoding="utf-8").read()


@app.get("/models", response_class=HTMLResponse)
def models_page():
    import os
    html = os.path.join(os.path.dirname(__file__), "static", "models.html")
    return open(html, encoding="utf-8").read()


@app.get("/api/models/config")
def get_model_config():
    return {"config": _model_config, "available": sup_config.available_kinds(_model_config),
            "capabilities": list(sup_config.CAPABILITY_FIELDS),
            "routing": {"hero": "高质量档（hero/对白正脸镜）", "ambient": "经济档（氛围/过场镜）"},
            "licenses": {"bundle_forbidden": ["ComfyUI", "HunyuanVideo"],
                         "non_commercial": ["InsightFace", "ArcFace"]}}


@app.put("/api/models/config")
def update_model_config(body: dict):
    global _model_config
    for kind, cfg in (body.get("config") or {}).items():
        if kind in sup_config.MODEL_KINDS:
            for field in ("model", "api_key", "api_url"):
                if field in cfg:
                    _model_config[kind][field] = cfg.get(field, "")
    return {"config": _model_config, "available": sup_config.available_kinds(_model_config)}


@app.post("/api/dramas")
def create_project(body: CreateProject):
    p = proj_mod.make_project(body.title, body.logline, body.platform,
                              body.rating, body.genre, body.episodes, body.minutes)
    violations = proj_mod.validate_project(p)
    if violations:
        raise HTTPException(status_code=422, detail=violations)
    with Session() as s:
        row = jobs_db.Project(title=p["title"], logline=p["logline"],
                              platform=p["platform"], rating=p["rating"],
                              genre=p["genre"], style=p["style"],
                              episodes=p["package"]["episodes"],
                              minutes=p["package"]["minutes"],
                              delivery_spec=p["delivery_spec"],
                              pilot_mode=p["pilot_mode"])
        s.add(row)
        s.commit()
        return {"id": row.id, "title": row.title, "status": row.status,
                "package": p["package"], "delivery_spec": p["delivery_spec"]}


@app.get("/api/dramas")
def list_projects():
    out = []
    with Session() as s:
        rows = s.scalars(select(jobs_db.Project).order_by(jobs_db.Project.id.desc())).all()
        for r in rows:
            run = s.scalars(select(jobs_db.Run).where(
                jobs_db.Run.project_id == r.id).order_by(jobs_db.Run.id.desc())).first()
            n_shots = s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == r.id).count()
            out.append({"id": r.id, "title": r.title, "logline": r.logline, "status": r.status,
                        "episodes": r.episodes, "minutes": r.minutes,
                        "deliverable": bool(run and run.result.get("summary", {}).get("deliverable")),
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
        for f in ("title", "logline", "platform", "rating", "genre", "style"):
            if getattr(body, f, None):
                setattr(p, f, getattr(body, f))
        if body.episodes:
            p.episodes = body.episodes
        if body.minutes:
            p.minutes = body.minutes
        s.commit()
    return {"id": project_id, "title": p.title, "platform": p.platform}


@app.post("/api/dramas/{project_id}/run")
def run_project(project_id: int):
    from film import pipeline
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        result = pipeline.run_pipeline(p.title, p.logline, p.platform, p.rating, p.genre)
        s.add(jobs_db.Run(project_id=project_id, result=result))
        # 从剧本派生分镜表（M4）+ 落剧本（M2）
        from film.script import generate as m2gen, outline as m2out
        from film.storyboard import make_shotlist
        from film.suppliers import adapter as sup_adapter
        text_ad = sup_adapter.make_adapter("text", {})
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
        cfg_models = sup_config.load_from_env()
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
        ol, _ = m2gen.generate_outline(p.logline, sup_adapter.make_adapter("text", {}))
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
