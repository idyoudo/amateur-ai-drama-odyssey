"""M9 剪辑契约层 · 封闭枚举与阈值。"""

# 唯一时间线帧率（D5/EL-09）
TIMELINE_FPS = 24

# ASL 参考带（E-53 当代主流 2–4 s/镜）
ASL_REF_BAND = (2.0, 4.0)

# Murch 六规则权重（E-55）：只作排序与解释依据，不写死为切点阈值
MURCH_WEIGHTS = {
    "emotion": 0.51, "story": 0.23, "rhythm": 0.10,
    "eyeline": 0.07, "space2d": 0.05, "space3d": 0.04,
}

# 交换格式 reel 名上限（B-42）：CMX3600 仅 8 字符；Avid 32
REEL_MAX = {"cmx3600": 8, "avid": 32}
