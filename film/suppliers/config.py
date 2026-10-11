"""模型/供应商配置（env 为部署默认，API/页面可覆盖）。

每个模型 kind 三项：model / api_key / api_url；三项中 model+api_key 齐备才算「已配置」，
否则该 kind 走 MockProvider（无凭据自证链路）。依据：PRD/M17、docs/designs/数据模型.md §四 suppliers。
"""
import os

MODEL_KINDS = ("video", "image", "tts", "music", "lipsync")

_ENV_PREFIX = {"video": "VIDEO", "image": "IMAGE", "tts": "TTS",
               "music": "MUSIC", "lipsync": "LIPSYNC"}

# 能力矩阵字段（供页面展示与路由判断，对齐 M17.1-F04）
CAPABILITY_FIELDS = ("reference_image", "first_last_frame", "multi_shot",
                     "camera_control", "native_audio", "timestamp")


def load_from_env():
    """从环境变量读取模型参数 → {kind: {model, api_key, api_url}}。"""
    cfg = {}
    for kind in MODEL_KINDS:
        p = _ENV_PREFIX[kind]
        cfg[kind] = {
            "model": os.environ.get("%s_MODEL" % p, ""),
            "api_key": os.environ.get("%s_API_KEY" % p, ""),
            "api_url": os.environ.get("%s_API_URL" % p, ""),
        }
    return cfg


def is_configured(kind_cfg):
    """model + api_key 齐备才算已配置。"""
    return bool(kind_cfg.get("model")) and bool(kind_cfg.get("api_key"))


def available_kinds(cfg):
    """返回已完整配置的 kind 列表（其余走 Mock）。"""
    return [k for k in MODEL_KINDS if is_configured(cfg.get(k, {}))]


def validate_config(cfg):
    """配置不变量：已配置的 kind 三项字段非空且无重复 model；未配置只提示不报错。"""
    v = []
    models = []
    for kind in MODEL_KINDS:
        c = cfg.get(kind, {})
        if is_configured(c):
            if c["model"] in models:
                v.append("模型 %s 在多个 kind 重复" % c["model"])
            models.append(c["model"])
        elif c.get("model") or c.get("api_key"):
            v.append("%s 配置不完整（model/api_key 需同时填）" % kind)
    return v
