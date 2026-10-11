"""M2 结构校验契约层 · 封闭枚举。"""

# Save the Cat 15 拍（M2.4-F04 / E-44）
BEATS_15 = ("Opening Image", "Theme Stated", "Set-up", "Catalyst", "Debate",
            "Break into Two", "B Story", "Fun and Games", "Midpoint",
            "Bad Guys Close In", "All Is Lost", "Dark Night of the Soul",
            "Break into Three", "Finale", "Final Image")

# Truby 四节点（M2.4-F05 / E-45）
TRUBY_NODES = ("Ghost", "Weakness", "Need", "Self-Revelation")

# Harmon 8 步（M2.4-F06 / E-46）
HARMON_8 = ("comfort", "want", "unfamiliar", "adapt", "get", "price", "return", "changed")

# 剧集形态（M2.4-F09 / B-89 / E-50 / E-51）
FORMS = ("feature", "pilot_1h", "half_hour")
SCENE_RANGES = {"feature": (50, 100), "pilot_1h": (25, 50), "half_hour": (12, 25)}

# 三幕节拍位置（M2.4-F03 / E-43）
BEAT_WINDOWS = {"ppi": (0.22, 0.25), "midpoint": (0.48, 0.52), "ppii": (0.78, 0.82)}

# A/B/C 线（M2.4-F07 / E-52）
STORY_LINES = ("A", "B", "C")
