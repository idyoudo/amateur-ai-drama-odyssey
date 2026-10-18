"""模型/供应商配置（env 为部署默认，API/页面可覆盖）。

每个模型 kind 三项：model / api_key / api_url；三项中 model+api_key 齐备才算「已配置」，
否则该 kind 走 MockProvider（无凭据自证链路）。依据：PRD/M17、docs/designs/数据模型.md §四 suppliers。
"""
import os

MODEL_KINDS = ("text", "video", "image", "tts", "music", "lipsync")

_ENV_PREFIX = {"text": "TEXT", "video": "VIDEO", "image": "IMAGE", "tts": "TTS",
               "music": "MUSIC", "lipsync": "LIPSYNC"}

# 能力矩阵字段（供页面展示与路由判断，对齐 M17.1-F04）
CAPABILITY_FIELDS = ("reference_image", "first_last_frame", "multi_shot",
                     "camera_control", "native_audio", "timestamp")


# 供应商预设（选厂商 → 自动填 api_url 与推荐 model，用户只需填 api_key）
# group 用于页面分组；note 提示协议/授权/端点限制；不在目录中的厂商走「自定义配置」
GROUP_CN = "国内厂商"
GROUP_INTL = "海外厂商"
GROUP_THIRD = "第三方平台"
PROVIDER_GROUPS = (GROUP_CN, GROUP_INTL, GROUP_THIRD)


def _preset(vendor, model, api_url, group, site, note=""):
    return {"vendor": vendor, "model": model, "api_url": api_url,
            "group": group, "site": site, "note": note}


PRESETS = {
    "text": [
        _preset("通义千问（DashScope）", "qwen3-max",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com"),
        _preset("DeepSeek", "deepseek-chat", "https://api.deepseek.com/v1",
                GROUP_CN, "deepseek.com"),
        _preset("月之暗面 Kimi", "kimi-k2", "https://api.moonshot.cn/v1",
                GROUP_CN, "moonshot.cn"),
        _preset("智谱 GLM", "glm-4-plus", "https://open.bigmodel.cn/api/paas/v4",
                GROUP_CN, "bigmodel.cn"),
        _preset("百度千帆", "ernie-4.5-turbo", "https://qianfan.baidubce.com/v2",
                GROUP_CN, "qianfan.baidubce.com"),
        _preset("火山方舟（豆包）", "doubao-seed-1-6",
                "https://ark.cn-beijing.volces.com/api/v3", GROUP_CN, "volcengine.com"),
        _preset("腾讯混元", "hunyuan-turbos-latest",
                "https://api.hunyuan.cloud.tencent.com/v1", GROUP_CN, "cloud.tencent.com"),
        _preset("MiniMax", "abab6.5s-chat", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat"),
        _preset("讯飞星火", "4.0Ultra", "https://spark-api-open.xf-yun.com/v1",
                GROUP_CN, "xf-yun.com"),
        _preset("商汤日日新", "SenseChat-5", "https://api.sensenova.cn/compatible-mode/v1",
                GROUP_CN, "sensenova.cn"),
        _preset("OpenAI", "gpt-4o", "https://api.openai.com/v1", GROUP_INTL, "openai.com"),
        _preset("Anthropic Claude", "claude-sonnet-4-5", "https://api.anthropic.com/v1",
                GROUP_INTL, "anthropic.com", "原生协议，需兼容网关"),
        _preset("Google Gemini", "gemini-2.5-pro",
                "https://generativelanguage.googleapis.com/v1beta/openai",
                GROUP_INTL, "ai.google.dev"),
        _preset("xAI Grok", "grok-4", "https://api.x.ai/v1", GROUP_INTL, "x.ai"),
        _preset("Mistral", "mistral-large-latest", "https://api.mistral.ai/v1",
                GROUP_INTL, "mistral.ai"),
        _preset("Cohere", "command-r-plus", "https://api.cohere.ai/compatibility/v1",
                GROUP_INTL, "cohere.com"),
        _preset("OpenRouter", "openrouter/auto", "https://openrouter.ai/api/v1",
                GROUP_THIRD, "openrouter.ai"),
        _preset("硅基流动", "Qwen/Qwen3-235B-A22B", "https://api.siliconflow.cn/v1",
                GROUP_THIRD, "siliconflow.cn"),
        _preset("302.AI", "gpt-4o", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
        _preset("AiHubMix", "gpt-4o", "https://aihubmix.com/v1", GROUP_THIRD, "aihubmix.com"),
        _preset("OhMyGPT", "gpt-4o", "https://api.ohmygpt.com/v1", GROUP_THIRD, "ohmygpt.com"),
    ],
    "image": [
        _preset("豆包 Seedream 5.0 Pro", "doubao-seedream-5-0-pro-260628",
                "https://ark.cn-beijing.volces.com/api/v3", GROUP_CN, "volcengine.com",
                "最多 10 张参考图 · 2K · 质量优先"),
        _preset("豆包 Seedream 5.0 Flash", "doubao-seedream-5-0-flash-260915",
                "https://ark.cn-beijing.volces.com/api/v3", GROUP_CN, "volcengine.com",
                "速度快、成本低"),
        _preset("通义万相 Wan 2.5", "wan2.5-t2i-preview",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "低成本中文排版；纯文生图"),
        _preset("智谱 CogView", "cogview-3-plus",
                "https://open.bigmodel.cn/api/paas/v4", GROUP_CN, "bigmodel.cn"),
        _preset("腾讯混元生图", "hunyuan-image",
                "https://api.hunyuan.cloud.tencent.com/v1", GROUP_CN, "cloud.tencent.com"),
        _preset("可灵图片", "kling-image", "https://api.klingai.com/v1", GROUP_CN,
                "klingai.com"),
        _preset("MiniMax 图像", "image-01", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat"),
        _preset("OpenAI GPT Image 2.5", "gpt-image-2.5-sunburst",
                "https://api.openai.com/v1", GROUP_INTL, "openai.com",
                "盲测质量第一梯队；需账号权限"),
        _preset("Google Nano Banana 2.1", "gemini-nano-banana-2.1",
                "https://generativelanguage.googleapis.com/v1beta/openai", GROUP_INTL,
                "ai.google.dev", "14 张参考图 · 4 角色一致性；需专用适配器"),
        _preset("Black Forest Labs FLUX 3", "flux-3", "https://api.bfl.ai/v1",
                GROUP_INTL, "bfl.ai", "需确认端点"),
        _preset("Stability AI", "sd3.5-large", "https://api.stability.ai/v2beta",
                GROUP_INTL, "stability.ai"),
        _preset("Replicate", "flux-schnell", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com"),
        _preset("硅基流动", "Kwai-Kolors/Kolors", "https://api.siliconflow.cn/v1",
                GROUP_THIRD, "siliconflow.cn"),
        _preset("OpenRouter", "gemini-2.5-flash-image", "https://openrouter.ai/api/v1",
                GROUP_THIRD, "openrouter.ai", "以网关模型名为准"),
        _preset("302.AI", "gpt-image-2.5-sunburst", "https://api.302.ai/v1",
                GROUP_THIRD, "302.ai"),
    ],
    "video": [
        _preset("可灵 Kling", "kling-v2", "https://api.klingai.com/v1", GROUP_CN, "klingai.com"),
        _preset("豆包 Seedance", "seedance-1-0-pro",
                "https://ark.cn-beijing.volces.com/api/v3", GROUP_CN, "volcengine.com"),
        _preset("MiniMax 海螺", "video-01", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat"),
        _preset("Vidu", "vidu-1.5", "https://api.vidu.cn/v1", GROUP_CN, "vidu.cn"),
        _preset("智谱 CogVideoX", "cogvideox-3", "https://open.bigmodel.cn/api/paas/v4",
                GROUP_CN, "bigmodel.cn"),
        _preset("通义万相视频", "wanx2.1-t2v-turbo",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com"),
        _preset("腾讯混元视频", "hunyuan-video",
                "https://api.hunyuan.cloud.tencent.com/v1", GROUP_CN, "cloud.tencent.com"),
        _preset("Runway", "gen-4", "https://api.dev.runwayml.com/v1", GROUP_INTL, "runwayml.com"),
        _preset("Luma", "ray-2", "https://api.lumalabs.ai/dream-machine/v1",
                GROUP_INTL, "lumalabs.ai"),
        _preset("OpenAI Sora", "sora-2", "https://api.openai.com/v1", GROUP_INTL, "openai.com",
                "需账号权限"),
        _preset("Stability AI", "stable-video", "https://api.stability.ai/v2beta",
                GROUP_INTL, "stability.ai"),
        _preset("Replicate", "minimax/video-01", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com"),
        _preset("302.AI", "kling-v2", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "tts": [
        _preset("CosyVoice（DashScope）", "cosyvoice-v1",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com"),
        _preset("豆包语音", "seed-tts", "https://ark.cn-beijing.volces.com/api/v3",
                GROUP_CN, "volcengine.com"),
        _preset("讯飞语音", "spark-tts", "https://spark-api-open.xf-yun.com/v1",
                GROUP_CN, "xf-yun.com"),
        _preset("腾讯云语音", "tts", "https://tts.tencentcloudapi.com", GROUP_CN,
                "cloud.tencent.com", "非 OpenAI 协议，需适配器"),
        _preset("MiniMax 语音", "speech-01", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat"),
        _preset("OpenAI", "tts-1", "https://api.openai.com/v1", GROUP_INTL, "openai.com"),
        _preset("ElevenLabs", "eleven_multilingual_v2", "https://api.elevenlabs.io/v1",
                GROUP_INTL, "elevenlabs.io"),
        _preset("Azure OpenAI", "tts", "https://<resource>.openai.azure.com/openai/v1",
                GROUP_INTL, "azure.microsoft.com", "替换 resource 子域"),
        _preset("Google Cloud TTS", "tts", "https://texttospeech.googleapis.com/v1",
                GROUP_INTL, "cloud.google.com", "非 OpenAI 协议，需适配器"),
        _preset("硅基流动", "FunAudioLLM/CosyVoice2-0.5B", "https://api.siliconflow.cn/v1",
                GROUP_THIRD, "siliconflow.cn"),
        _preset("302.AI", "tts-1", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "music": [
        _preset("ACE-Step", "ace-step", "http://localhost:8001/v1", GROUP_CN,
                "github.com/ace-step", "自托管，Apache-2.0"),
        _preset("Suno", "suno-v4", "https://api.suno.ai/v1", GROUP_INTL, "suno.ai",
                "仅 Pro/Premier 可商用"),
        _preset("Mureka", "mureka-v1", "https://api.mureka.ai/v1", GROUP_INTL, "mureka.ai",
                "付费档才可商用"),
        _preset("Stability Audio", "stable-audio-2", "https://api.stability.ai/v2beta",
                GROUP_INTL, "stability.ai"),
        _preset("Replicate MusicGen", "meta/musicgen", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com"),
        _preset("302.AI", "suno-v4", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "lipsync": [
        _preset("可灵 Lip Sync", "kling-lipsync", "https://api.klingai.com/v1",
                GROUP_CN, "klingai.com"),
        _preset("Sync.so", "sync-1.9", "https://api.sync.so/v2", GROUP_INTL, "sync.so"),
        _preset("HeyGen", "lip-sync", "https://api.heygen.com/v2", GROUP_INTL, "heygen.com"),
        _preset("D-ID", "talks", "https://api.d-id.com", GROUP_INTL, "d-id.com"),
        _preset("Runway Act-One", "act-one", "https://api.dev.runwayml.com/v1",
                GROUP_INTL, "runwayml.com", "需确认账号权限"),
        _preset("Replicate", "sync/lipsync", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com"),
        _preset("302.AI", "kling-lipsync", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
}


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
