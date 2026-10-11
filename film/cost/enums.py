"""M14 成本契约层 · 封闭枚举与阈值。"""

# 四级预算（M14.2-F01）
BUDGET_LEVELS = ("project", "episode", "pod", "shot")
# 分级预警（M14.2-F01）：50%/80%/100%
WARN_THRESHOLDS = {"warn_50": 0.5, "warn_80": 0.8, "blocked": 1.0}

# 降级矩阵（M14.5-F02）：不改变叙事结构/镜头数/门禁节点
DEGRADE_STEPS = ("high_model", "econ_model", "reduce_candidates",
                 "reduce_resolution", "defer_optional")
