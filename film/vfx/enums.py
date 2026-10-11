"""M19 VFX 契约层 · 封闭枚举。"""

# VFX 类型（M19.1-F01）
VFX_TYPES = ("repair", "particle", "sky", "cleanup", "screen_replace", "composite")

# 物理骨架触发器（M19.1-F03 / E-63）
PHYSICS_TRIGGERS = ("high_dynamic", "load_bearing", "collision")

# 修复优先级（M19.1-F04 / E-35）：局部修复 → 局部重生成 → 整镜重抽
REPAIR_ORDER = ("local_repair", "local_regen", "full_resample")

# 变形宽银幕三项特征（M19.4-F05）
ANAMORPHIC_FEATURES = ("oval_bokeh", "horizontal_flare", "2.39:1")
