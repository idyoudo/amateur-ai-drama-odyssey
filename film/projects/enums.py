"""M1 立项契约层 · 封闭枚举。"""

# 分级预估（M1.0-F01）
RATINGS = ("全龄", "12+", "16+")
# 风格预设（M1.1-F05）
STYLES = ("写实", "日漫", "3D", "国风")
# 单集时长三档（D2 / M1.0-F02）
EPISODE_MINUTES = (22, 30, 45)
# 模型档位（M1.4-F01）
MODEL_TIERS = ("经济", "标准", "精品")
# 交付画幅（D1 / M1.0-F03：三画幅必交）
DELIVERY_ASPECTS = ("2.39:1", "16:9", "9:16")
# 可选交付（EL-11 / M1.0-F03）
OPTIONAL_DELIVERY = ("HDR10", "5.1", "48fps")

# 参数边界（M1.1-F04）
TITLE_MAX = 128
EPISODES_MIN, EPISODES_MAX = 1, 50
SECONDS_MIN, SECONDS_MAX = 15, 2700
