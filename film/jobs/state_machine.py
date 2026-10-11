"""M13 任务状态机 · 合法转移（fail-closed）。

转移在 claim 层强校验；乱序提交一律拒绝（M13.1-F02「任何乱序提交被拒绝」）。
对账语义：unknown ──对账──▶ completed（resolved）或 queued（requeued），绝不直接重投。
"""

TRANSITIONS = {
    "queued": ("running", "cancelled"),
    "running": ("completed", "failed", "unknown", "cancelled", "waiting_human"),
    "waiting_human": ("completed", "failed"),   # 人工通过/驳回（驳回→failed→retry 返工）
    "failed": ("queued", "retry_exhausted"),   # 可重试→queued；耗尽→retry_exhausted
    "unknown": ("completed", "queued"),
    "retry_exhausted": (),
    "cancelled": (),
    "completed": (),
}


class StateError(Exception):
    """状态转移非法（fail-closed）。"""


def can_transition(src, dst):
    return dst in TRANSITIONS.get(src, ())


def require_transition(src, dst):
    if not can_transition(src, dst):
        raise StateError("非法状态转移：%r -> %r" % (src, dst))
    return dst
