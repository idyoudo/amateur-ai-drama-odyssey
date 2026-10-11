"""M17 供应商契约层 · 封闭枚举。"""

# 电影参数能力矩阵维度（M17.1-F04）
CAPABILITIES = ("reference_image", "reference_video", "first_last_frame", "multi_shot",
                "camera_control", "focal_dof", "resolution_aspect", "native_audio",
                "duration", "cost", "latency")

# 镜头重要性（M17.3-F01）
SHOT_IMPORTANCE = ("hero", "dialogue_closeup", "ambient", "transition")

# 模型档位降级链（M17.3-F02 / E-18）
MODEL_TIER_CHAIN = ("premium", "standard", "economy")

# 不得内置分发组件（M17.4-F02：GPL-3.0 / 非 OSI 许可）
FORBIDDEN_BUNDLE = ("ComfyUI", "ComfyUI-KJNodes", "HunyuanVideo")
