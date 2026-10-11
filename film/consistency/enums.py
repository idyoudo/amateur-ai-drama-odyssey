"""M6 一致性契约层 · 封闭枚举。"""

SCREEN_DIRECTIONS = ("left", "right")
EYELINES = ("left", "right", "center", "off")
AXIS_SIDES = ("A", "B", "on_axis")
ALERT_LEVELS = ("info", "attention", "needs_decision")

# 人脸相似度阈值（M6.3-F02，待标定初值）
FACE_PASS = 0.45
FACE_FAIL = 0.30

# 同框角色硬上限（M6.2-F05 / A-07）
MAX_SAME_FRAME_CHARACTERS = 3
