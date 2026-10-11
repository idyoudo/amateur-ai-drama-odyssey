#!/usr/bin/env python3
"""M13 PG 集成复测（联调阶段）。

用 DATABASE_URL 环境变量连真实 PostgreSQL，验证 SqlQueue 持久化语义 + SKIP LOCKED 并发抢占。
凭据不物化进仓库：部署/CI 通过环境变量注入。
用法：DATABASE_URL='postgresql+psycopg2://aado:PW@host:5433/AADO' .venv/bin/python tools/verify_pg.py
退出码：0 通过；1 违规；2 环境缺失。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

URL = os.environ.get("DATABASE_URL")
if not URL:
    print("缺少 DATABASE_URL 环境变量（联调阶段注入真实凭据）", file=sys.stderr)
    sys.exit(2)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from film.jobs import db
from film.jobs.sql import CLAIM_SQL

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


engine = create_engine(URL)
db.Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)
q = db.SqlQueue(Session, lease_sec=10)

# 清空测试残留（独立测试库场景）
with Session() as s:
    s.execute(text("DELETE FROM outbox"))
    s.execute(text("DELETE FROM intents"))
    s.execute(text("DELETE FROM jobs"))
    s.commit()

# ---------------- 幂等入队 ----------------
j1 = q.enqueue(project_id="pgtest", episode_id=1, shot_id=1, type="shot_video",
               idempotency_key="pg:1:1:shot_video:fp1", priority=5)
dup = q.enqueue(project_id="pgtest", episode_id=1, shot_id=1, type="shot_video",
                idempotency_key="pg:1:1:shot_video:fp1", priority=5)
check("PG 幂等入队同一 id", dup.id == j1.id)

# ---------------- claim / complete / fail ----------------
c = q.claim(now=0)
check("PG claim 高优先级", c.id == j1.id and c.status == "running")
check("PG claim 置 epoch/attempts", c.lease_epoch == 1 and c.attempts == 1)
try:
    q.complete(j1.id, 0)
    check("PG fencing 旧 epoch 拒绝", False)
except db.QueueError:
    check("PG fencing 旧 epoch 拒绝", True)
q.complete(j1.id, 1, checkpoint={"produced_keys": ["obj/pg"]})
with Session() as s:
    check("PG complete->completed", s.get(db.Job, j1.id).status == "completed")

# ---------------- SKIP LOCKED 并发抢占 ----------------
# 两个并发连接各领一个 queued 任务，不得领到同一个
for i in (2, 3):
    q.enqueue(project_id="pgtest", episode_id=1, shot_id=i, type="shot_video",
              idempotency_key="pg:1:%d:shot_video:fp%d" % (i, i), priority=0)
claim = text(CLAIM_SQL)
c1 = engine.connect()
c2 = engine.connect()
try:
    with c1.begin():
        r1 = c1.execute(claim, {"now": 0, "lease": 10}).fetchone()
    with c2.begin():
        r2 = c2.execute(claim, {"now": 0, "lease": 10}).fetchone()
    check("SKIP LOCKED 两个连接领到不同任务", r1 is not None and r2 is not None and r1.id != r2.id)
finally:
    c1.close()
    c2.close()

# ---------------- reclaim_stale ----------------
with Session() as s:
    rows = s.query(db.Job).filter(db.Job.status == "running").all()
    for r in rows:
        r.locked_until = 0  # 使租约过期
    s.commit()
ids = q.reclaim_stale(now=100)
check("PG reclaim 回收 running 过期任务", len(ids) == 2)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M13-pg-integration", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
