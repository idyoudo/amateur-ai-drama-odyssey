"""AADO worker（PG SKIP LOCKED 队列消费者；重计算在此，不 import API）。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from film.jobs import db as jobs_db
from film.jobs.worker import Worker


def build_queue():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("缺少 DATABASE_URL（worker 需要真实 PG）")
    engine = create_engine(url)
    jobs_db.Base.metadata.create_all(engine)
    return jobs_db.SqlQueue(sessionmaker(bind=engine, expire_on_commit=False))


def main():
    import time
    from apps.worker import handlers
    from film.suppliers import config as sup_config
    queue = build_queue()
    worker = Worker(queue)
    handler = handlers.make_handler(sup_config.load_from_env())
    poll_ms = float(os.environ.get("WORKER_POLL_MS", "5000"))
    print("worker started (poll %dms)" % poll_ms, flush=True)
    while True:
        job = worker.run_once(handler)
        if job is None:
            time.sleep(poll_ms / 1000.0)
        else:
            print("processed job_id=%s type=%s" % (job.id, job.type), flush=True)


if __name__ == "__main__":
    main()
