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
    from film.suppliers import config as sup_config
    from apps.worker import handlers
    queue = build_queue()
    worker = Worker(queue)
    handler = handlers.make_handler(sup_config.load_from_env())
    done = worker.run_until_empty(handler)
    print("processed_jobs=%d" % done)


if __name__ == "__main__":
    main()
