"""M13 任务编排契约层 · 封闭枚举。

设计原则（对齐 film/enums.py）：任务状态、阶段、失败分类、重试处置是**唯一事实来源**；
枚举封闭，未知值一律拒绝（禁止静默回落）。依据：PRD/M13、docs/designs/任务编排设计.md §一/§七。
"""

# 任务级状态机（任务编排设计 §一：禁止字符串码混搭，用 PG enum）
JOB_STATUS = ("queued", "running", "waiting_human", "completed", "failed", "retry_exhausted", "cancelled", "unknown")

# 阶段枚举（Development→Delivery 五段，PRD M13.2）
SEGMENTS = {
    "dev": ("adapt", "script_revise"),
    "prepro": ("casting", "board", "animatic"),
    "production": ("keyframe", "shot_video", "performance"),
    "post": ("edit", "sound_design", "mix", "grade", "master"),
    "delivery": ("qc", "derive", "deliver"),
}
STAGE_ORDER = tuple(
    s for seg in ("dev", "prepro", "production", "post", "delivery") for s in SEGMENTS[seg]
)

# 失败分类树（M13.7-F03：失败 100% 有分类，周报可聚合）
ERROR_CLASS = ("network", "timeout", "rate_limit", "content_reject",
               "asset_missing", "budget_exceeded", "gate_rejected",
               "supplier_circuit", "system")

# 重试处置（任务编排设计 §七：网络类可重试，内容类不自动重试）
RETRY = ("retry", "no_retry", "human", "terminate")

ERROR_RETRY = {
    "network": "retry",
    "timeout": "retry",
    "rate_limit": "retry",
    "supplier_circuit": "human",   # 熔断 → 切备用/转人工（与 M14 联动）
    "content_reject": "no_retry",
    "asset_missing": "no_retry",
    "budget_exceeded": "human",
    "gate_rejected": "no_retry",
    "system": "retry",
}

# 单镜自动重试硬上限 K≤2（任务编排设计 §七）
AUTO_RETRY_LIMIT = 2
