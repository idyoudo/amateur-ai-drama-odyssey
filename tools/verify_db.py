#!/usr/bin/env python3
"""M13 SQLAlchemy 数据模型 · 独立复测（SQLite 内存库，portable 语义）。

只 import film/jobs/db，验证模型/幂等入队/claim/complete/fail/reclaim。
SKIP LOCKED 并发 SQL（film/jobs/sql.py）在联调阶段用真实 PG 测，不在此处断言。
退出码：0 通过；1 违规。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from film.jobs import db

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


engine = create_engine("sqlite:///:memory:")
db.Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)
q = db.SqlQueue(Session, lease_sec=10)


def status_of(job_id):
    with Session() as s:
        return s.get(db.Job, job_id).status


# ---------------- 幂等入队 ----------------
j1 = q.enqueue(project_id="p", episode_id=1, shot_id=1, type="shot_video",
               idempotency_key="p:1:1:shot_video:fp1", priority=5)
dup = q.enqueue(project_id="p", episode_id=1, shot_id=1, type="shot_video",
                idempotency_key="p:1:1:shot_video:fp1", priority=5)
check("幂等入队同一 id", dup.id == j1.id)
with Session() as s:
    check("库中仅 1 条", len(s.scalars(select(db.Job)).all()) == 1)

# ---------------- claim 优先级 + 状态 ----------------
j2 = q.enqueue(project_id="p", episode_id=1, shot_id=2, type="shot_video",
               idempotency_key="p:1:2:shot_video:fp2", priority=1)
c = q.claim(now=0)
check("claim 高优先级", c.id == j1.id)
check("claim 置 running", c.status == "running")
check("claim attempts/epoch", c.attempts == 1 and c.lease_epoch == 1)

# ---------------- fencing ----------------
try:
    q.complete(j1.id, 0)
    check("旧 epoch 被拒", False)
except db.QueueError:
    check("旧 epoch 被拒", True)

# ---------------- complete ----------------
q.complete(j1.id, 1, checkpoint={"produced_keys": ["obj/a"]})
check("complete->completed", status_of(j1.id) == "completed")

# ---------------- fail ----------------
c2 = q.claim(now=0)
check("claim 第二个", c2.id == j2.id)
q.fail(j2.id, c2.lease_epoch, "network", "E_NET")
check("fail->failed", status_of(j2.id) == "failed")
with Session() as s:
    row = s.get(db.Job, j2.id)
    check("fail 记录 error_class", row.error_class == "network" and row.error_code == "E_NET")

# ---------------- reclaim_stale：有 durable 产出 -> completed ----------------
j3 = q.enqueue(project_id="p", episode_id=1, shot_id=3, type="shot_video",
               idempotency_key="p:1:3:shot_video:fp3")
q.claim(now=0)  # locked_until = 10
with Session() as s:
    row = s.get(db.Job, j3.id)
    row.checkpoint = {"produced_keys": ["obj/x"]}
    s.commit()
q.reclaim_stale(now=100)
check("reclaim 有产出->completed", status_of(j3.id) == "completed")

# ---------------- reclaim_stale：无产出 -> requeue ----------------
j4 = q.enqueue(project_id="p", episode_id=1, shot_id=4, type="shot_video",
               idempotency_key="p:1:4:shot_video:fp4")
q.claim(now=0)
q.reclaim_stale(now=100)
check("reclaim 无产出->requeue", status_of(j4.id) == "queued")

# ---------------- intent / outbox 表存在 ----------------
with Session() as s:
    s.add(db.Intent(job_id=j1.id, provider="p", fingerprint="f", request_id="r"))
    s.add(db.Outbox(topic="t", payload={"x": 1}, idempotency_key="ob1"))
    s.commit()
    check("intent 表可写", s.scalars(select(db.Intent)).first().request_id == "r")
    check("outbox 表可写", s.scalars(select(db.Outbox)).first().topic == "t")

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M13-db-models", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
