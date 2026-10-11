"""Job 数据模型（Python 侧，对齐 docs/designs/数据模型.md jobs 表）。"""
from . import state_machine


def make_job(project_id, episode_id, shot_id, job_type, idempotency_key, priority=0):
    return {
        "id": None,
        "project_id": project_id,
        "episode_id": episode_id,
        "shot_id": shot_id,
        "type": job_type,
        "status": "queued",
        "progress": 0,
        "error_code": None,
        "error_class": None,
        "attempts": 0,
        "attempt_limit": 2,
        "available_at": 0,
        "locked_until": None,
        "lease_epoch": 0,
        "idempotency_key": idempotency_key,
        "provider_task_id": None,
        "checkpoint": {},
        "priority": priority,
    }


def transition(job, dst):
    """按合法状态机转移（fail-closed）。返回 job。"""
    state_machine.require_transition(job["status"], dst)
    job["status"] = dst
    return job
