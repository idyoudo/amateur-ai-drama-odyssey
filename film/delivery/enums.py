"""M12 交付契约层 · 封闭枚举与阈值。"""

# 主母版规格（M12.1-F01 / D1/D3/D4/D5）
MASTER_ASPECT = "2.39:1"
MASTER_FPS = 24
MASTER_LUFS = -23.0
MASTER_LUFS_TOL = 0.5
MASTER_DBTP = -1.0

# 字幕来源（M12.2-F01 / E-31）：tts/asr/estimate；禁止标 provider
CUE_SOURCES = ("tts", "asr", "estimate")

# 字幕排版（M12.2-F02 / B-05/B-06）
SUBTITLE_MAX_CHARS = 23
SUBTITLE_MIN_SEC = 0.833
VERTICAL_MAX_LINES = 3

# 交付单可选交付标注（EL-11）
DELIVERY_STATUS = ("guaranteed", "optional", "needs_confirmation")
