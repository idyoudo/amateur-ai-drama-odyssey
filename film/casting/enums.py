"""M3 选角契约层 · 封闭枚举。"""

# 锚点视角（M3.2-F03：正/侧/3-4/全身/表情，最少覆盖 3 视角）
ANCHOR_VIEWS = ("front", "side", "back", "3_4", "full_body", "expression")

# 音色能力位（M3.7-F02）
VOICE_CAPABILITIES = ("gender", "age", "timbre", "persona", "ssml", "instruct", "timestamp")
