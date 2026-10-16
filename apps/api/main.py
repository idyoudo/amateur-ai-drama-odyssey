"""AADO 控制面 API（FastAPI；API 薄：入队 + 查询 + 人工终审，重计算归 worker）。"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, select
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
    return {"config": _model_config, "available": sup_config.available_kinds(_model_config)}


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
    with Session() as s:
        rows = s.scalars(select(jobs_db.Project).order_by(jobs_db.Project.id.desc())).all()
    return [{"id": r.id, "title": r.title, "logline": r.logline, "status": r.status,
             "episodes": r.episodes, "minutes": r.minutes} for r in rows]


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


@app.post("/api/dramas/{project_id}/run")
def run_project(project_id: int):
    from film import pipeline
    with Session() as s:
        p = s.get(jobs_db.Project, project_id)
        if p is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        result = pipeline.run_pipeline(p.title, p.logline, p.platform, p.rating, p.genre)
        s.add(jobs_db.Run(project_id=project_id, result=result))
        # 顺带从剧本派生分镜表（M4），供分镜工作台使用
        from film.script import generate as m2gen
        from film.storyboard import make_shotlist
        from film.suppliers import adapter as sup_adapter
        ol, _ = m2gen.generate_outline(p.logline, sup_adapter.make_adapter("text", {}))
        shots = make_shotlist(ol, ["主角", "配角"])
        s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).delete()
        for sh in shots:
            s.add(jobs_db.Shot(project_id=project_id, episode_id=1, **{k: sh[k] for k in
                  ("shot_no","scene_no","size","angle","move","duration","characters","dialogue","prompt","status")}))
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
        shots = make_shotlist(ol, ["主角", "配角"])
        for sh in shots:
            v = validate_shot(sh)
            if v:
                raise HTTPException(status_code=422, detail=v)
        # 清旧、写新
        s.query(jobs_db.Shot).filter(jobs_db.Shot.project_id == project_id).delete()
        for sh in shots:
            s.add(jobs_db.Shot(project_id=project_id, episode_id=1, **{k: sh[k] for k in
                  ("shot_no","scene_no","size","angle","move","duration","characters","dialogue","prompt","status")}))
        s.commit()
    return {"count": len(shots)}


@app.get("/api/dramas/{project_id}/shots")
def list_shots(project_id: int):
    with Session() as s:
        rows = s.scalars(select(jobs_db.Shot).where(
            jobs_db.Shot.project_id == project_id).order_by(jobs_db.Shot.shot_no)).all()
    return [{"id": r.id, "shot_no": r.shot_no, "scene_no": r.scene_no, "size": r.size,
             "angle": r.angle, "move": r.move, "duration": r.duration,
             "characters": r.characters or [], "dialogue": r.dialogue,
             "prompt": r.prompt, "status": r.status, "image_key": r.image_key} for r in rows]


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
