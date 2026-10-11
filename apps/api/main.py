"""AADO 控制面 API（FastAPI；API 薄：入队 + 查询 + 人工终审，重计算归 worker）。"""
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from film.jobs import db as jobs_db
from film.projects import project as proj_mod

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
jobs_db.Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)

app = FastAPI(title="AADO API", version="0.1.0")


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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/dramas")
def create_project(body: CreateProject):
    p = proj_mod.make_project(body.title, body.logline, body.platform,
                              body.rating, body.genre, body.episodes, body.minutes)
    violations = proj_mod.validate_project(p)
    if violations:
        raise HTTPException(status_code=422, detail=violations)
    return {"title": p["title"], "package": p["package"], "delivery_spec": p["delivery_spec"]}


@app.post("/api/drama-jobs")
def enqueue_job(body: CreateJob):
    q = jobs_db.SqlQueue(Session)
    row = q.enqueue(project_id=body.project_id, episode_id=body.episode_id,
                    shot_id=body.shot_id, type=body.type,
                    idempotency_key=body.idempotency_key, priority=body.priority)
    return {"id": row.id, "status": row.status}


@app.get("/api/dramas/{project_id}/jobs")
def list_jobs(project_id: str) -> List[dict]:
    with Session() as s:
        rows = s.scalars(select(jobs_db.Job).where(
            jobs_db.Job.project_id == project_id).order_by(jobs_db.Job.id)).all()
    return [{"id": r.id, "type": r.type, "status": r.status, "shot_id": r.shot_id} for r in rows]
