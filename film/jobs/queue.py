"""队列语义 · 内存后端（slice 2 · 与 PG SKIP LOCKED 同语义的确定性测试双）。

语义对齐 docs/designs/任务编排设计.md §二/§六：
- claim：仅领 queued 且 available_at<=now；按 priority 降序、FIFO（id 升序）保底；
  领取即 running、lease_epoch+1、attempts+1、locked_until=now+lease_sec。
- complete/fail/cancel：必须带 lease_epoch，旧 epoch 写入被拒（fencing）。
- reclaim_stale：running 且租约过期 → checkpoint 有 durable 产出则翻 completed；
  否则 attempts 未耗尽则 requeue，耗尽则 retry_exhausted。
"""
from . import enums, state_machine


class QueueError(Exception):
    """队列操作非法（fencing / 任务不存在）。"""


class InMemoryQueue:
    def __init__(self, lease_sec=90 * 60, retry_limit=enums.AUTO_RETRY_LIMIT):
        self.lease_sec = lease_sec
        self.retry_limit = retry_limit
        self._jobs = {}
        self._seq = 0

    def enqueue(self, job):
        """幂等入队：同 idempotency_key 已存在则返回既有 job（不复活已完成）。"""
        for existing in self._jobs.values():
            if existing["idempotency_key"] == job["idempotency_key"]:
                return existing
        self._seq += 1
        job["id"] = self._seq
        job["status"] = "queued"
        self._jobs[job["id"]] = job
        return job

    def claim(self, now=0):
        candidates = [j for j in self._jobs.values()
                      if j["status"] == "queued" and j.get("available_at", 0) <= now]
        if not candidates:
            return None
        job = sorted(candidates, key=lambda x: (-x.get("priority", 0), x["id"]))[0]
        job["status"] = "running"
        job["attempts"] += 1
        job["lease_epoch"] += 1
        job["locked_until"] = now + self.lease_sec
        return job

    def _get_fenced(self, job_id, epoch):
        job = self._jobs.get(job_id)
        if job is None:
            raise QueueError("任务不存在：%s" % (job_id,))
        if epoch != job["lease_epoch"]:
            raise QueueError("fencing 拒绝：epoch=%s 当前=%s" % (epoch, job["lease_epoch"]))
        return job

    def complete(self, job_id, epoch, checkpoint=None):
        job = self._get_fenced(job_id, epoch)
        state_machine.require_transition(job["status"], "completed")
        job["status"] = "completed"
        if checkpoint is not None:
            job["checkpoint"] = checkpoint
        return job

    def fail(self, job_id, epoch, error_class, error_code=None):
        job = self._get_fenced(job_id, epoch)
        state_machine.require_transition(job["status"], "failed")
        job["status"] = "failed"
        job["error_class"] = error_class
        job["error_code"] = error_code
        return job

    def cancel(self, job_id, epoch):
        job = self._get_fenced(job_id, epoch)
        state_machine.require_transition(job["status"], "cancelled")
        job["status"] = "cancelled"
        return job

    def retry(self, job_id):
        """人工/自动重试：failed → queued（受 attempts 上限约束）。"""
        job = self._jobs.get(job_id)
        if job is None:
            raise QueueError("任务不存在：%s" % (job_id,))
        if job["status"] != "failed":
            raise state_machine.StateError("仅 failed 可重试：%s" % (job["status"],))
        if job["attempts"] >= self.retry_limit + 1:
            state_machine.require_transition(job["status"], "retry_exhausted")
            job["status"] = "retry_exhausted"
            return False
        state_machine.require_transition(job["status"], "queued")
        job["status"] = "queued"
        return True

    def reclaim_stale(self, now):
        """僵尸回收：回收前用 checkpoint 校验是否已有 durable 产出，避免重复付费。"""
        reclaimed = []
        for job in list(self._jobs.values()):
            if job["status"] != "running":
                continue
            if (job.get("locked_until") or 0) > now:
                continue
            cp = job.get("checkpoint") or {}
            if cp.get("produced_keys"):
                job["status"] = "completed"
            elif job["attempts"] < self.retry_limit + 1:
                job["status"] = "queued"
                job["lease_epoch"] += 1
            else:
                job["status"] = "retry_exhausted"
            reclaimed.append(job["id"])
        return reclaimed

    def get(self, job_id):
        return self._jobs.get(job_id)
