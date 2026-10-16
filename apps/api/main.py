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
        s.commit()
    return result


@app.get("/api/dramas/{project_id}/jobs")
def list_jobs(project_id: str) -> List[dict]:
    with Session() as s:
        rows = s.scalars(select(jobs_db.Job).where(
            jobs_db.Job.project_id == project_id).order_by(jobs_db.Job.id)).all()
    return [{"id": r.id, "type": r.type, "status": r.status, "shot_id": r.shot_id} for r in rows]
