"""M7 表演契约层 · 封闭枚举与阈值。"""

# 情绪（M7.4-F03：未知情绪整条回落 neutral，禁止静默吞掉）
EMOTIONS = ("neutral", "happy", "sad", "angry", "fearful", "surprised", "disgusted")

# 音色四维标签（M7.3-F01 / A-16）
VOICE_DIMS = ("gender", "age", "timbre", "persona")
# 音色能力位（M7.3-F01 / A-17）
VOICE_CAPABILITIES = ("ssml", "instruct", "timestamp")

# 旁白提示（M7.2-F02：旁白独立成轨）
NARRATION_HINTS = ("旁白", "画外音", "OS", "V.O.", "NARRATOR", "narration")

# 音画同步（M7.5-F04 / B-26）：工程目标 ≤±25ms；ITU 容差 +90/-185ms
SYNC_ENGINE_MS = 25
SYNC_ITU_PLUS_MS = 90
SYNC_ITU_MINUS_MS = -185

# 角色间对白电平差上限（M7.6-F03）
LEVEL_MAX_DIFF_DB = 1.0
