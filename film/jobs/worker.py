"""Worker 循环（M13：claim → 执行 → complete/fail，门禁阻塞任务走 wait_human）。"""


class JobError(Exception):
    """任务执行失败（携带失败分类，供重试判定）。"""

    def __init__(self, error_class, error_code=None, message=""):
        super().__init__(message)
        self.error_class = error_class
        self.error_code = error_code


def _job_id(job):
    return job["id"] if isinstance(job, dict) else job.id


def _job_epoch(job):
    return job["lease_epoch"] if isinstance(job, dict) else job.lease_epoch


class Worker:
    """队列消费者：领取任务，执行 handler，按结果 complete/fail。

    handler(job) 返回 dict 视为 checkpoint，或返回 None；抛 JobError 走分类失败。
    """

    def __init__(self, queue, heartbeat_sec=20):
        self.queue = queue
        self.heartbeat_sec = heartbeat_sec

    def run_once(self, handler, now=0):
        job = self.queue.claim(now)
        if job is None:
            return None
        jid, epoch = _job_id(job), _job_epoch(job)
        try:
            result = handler(job)
            checkpoint = result if isinstance(result, dict) else None
            self.queue.complete(jid, epoch, checkpoint)
        except JobError as e:
            self.queue.fail(jid, epoch, e.error_class, e.error_code)
        except Exception as e:  # noqa: BLE001
            self.queue.fail(jid, epoch, "system", str(e)[:64])
        return job

    def run_until_empty(self, handler, now=0, max_jobs=1000):
        done = 0
        for _ in range(max_jobs):
            if self.run_once(handler, now) is None:
                break
            done += 1
        return done
