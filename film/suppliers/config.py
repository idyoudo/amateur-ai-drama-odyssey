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
        _preset("DeepSeek", "deepseek-v4-pro", "https://api.deepseek.com/v1",
                GROUP_CN, "deepseek.com"),
        _preset("月之暗面 Kimi", "kimi-k3", "https://api.moonshot.cn/v1",
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
        _preset("OpenAI", "gpt-6-astra", "https://api.openai.com/v1", GROUP_INTL, "openai.com",
                "以 OpenAI 文档为准"),
        _preset("Anthropic Claude", "claude-fable-5-1", "https://api.anthropic.com/v1",
                GROUP_INTL, "anthropic.com", "原生协议，需兼容网关"),
        _preset("Google Gemini", "gemini-3.1-pro",
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
        _preset("302.AI", "gpt-6-astra", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
        _preset("AiHubMix", "gpt-6-astra", "https://aihubmix.com/v1", GROUP_THIRD, "aihubmix.com"),
        _preset("OhMyGPT", "gpt-6-astra", "https://api.ohmygpt.com/v1", GROUP_THIRD, "ohmygpt.com"),
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
        _preset("千问 Qwen-Image 3.0 Pro", "qwen-image-3.0-pro",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "10px 中文小字 · 1K ¥0.25 / 2K ¥0.5"),
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
        _preset("通义万相 Wan 3.0", "wan3.0-video",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "30s · 1080p · 原生音频 · 20 个参考素材"),
        _preset("通义万相 Wan 3.0 Prime", "wan3.0-video-prime",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "同画质更快；成本约 +40%"),
        _preset("豆包 Seedance 2.5", "doubao-seedance-2-5-260628",
                "https://ark.cn-beijing.volces.com/api/v3", GROUP_CN, "volcengine.com",
                "30s · 50 个参考素材 · 身份一致性"),
        _preset("可灵 Kling 3", "kling-v3", "https://api.klingai.com/v1", GROUP_CN,
                "klingai.com", "多镜头/动作；4.0 API 待开放"),
        _preset("MiniMax H3", "MiniMax-H3", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat", "开放权重 · 2K · 原生音频"),
        _preset("Vidu", "vidu-1.5", "https://api.vidu.cn/v1", GROUP_CN, "vidu.cn"),
        _preset("智谱 CogVideoX", "cogvideox-3", "https://open.bigmodel.cn/api/paas/v4",
                GROUP_CN, "bigmodel.cn"),
        _preset("腾讯混元视频", "hunyuan-video",
                "https://api.hunyuan.cloud.tencent.com/v1", GROUP_CN, "cloud.tencent.com"),
        _preset("Google Veo 3.1", "veo-3.1-generate-001",
                "https://generativelanguage.googleapis.com/v1beta", GROUP_INTL,
                "ai.google.dev", "4K · 原生音频 · 4–8s"),
        _preset("Google Gemini Omni 1.1", "gemini-omni-1.1-flash",
                "https://generativelanguage.googleapis.com/v1beta", GROUP_INTL,
                "ai.google.dev", "40s · 4K · 可编辑"),
        _preset("Runway", "gen-4", "https://api.dev.runwayml.com/v1", GROUP_INTL, "runwayml.com"),
        _preset("Luma", "ray-2", "https://api.lumalabs.ai/dream-machine/v1",
                GROUP_INTL, "lumalabs.ai"),
        _preset("Stability AI", "stable-video", "https://api.stability.ai/v2beta",
                GROUP_INTL, "stability.ai"),
        _preset("Replicate", "bytedance/seedance-2.5", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com", "以网关模型名为准"),
        _preset("302.AI", "wan3.0-video", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "tts": [
        _preset("CosyVoice（DashScope）", "cosyvoice-v3",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "开源/自托管可选"),
        _preset("Qwen-Audio-3.1-TTS-Plus", "qwen-audio-3.1-tts-plus",
                "https://dashscope.aliyuncs.com/compatible-mode/v1", GROUP_CN,
                "dashscope.aliyuncs.com", "中文性价比 · 克隆榜第 2"),
        _preset("豆包语音", "seed-tts", "https://ark.cn-beijing.volces.com/api/v3",
                GROUP_CN, "volcengine.com"),
        _preset("讯飞语音", "spark-tts", "https://spark-api-open.xf-yun.com/v1",
                GROUP_CN, "xf-yun.com"),
        _preset("腾讯云语音", "tts", "https://tts.tencentcloudapi.com", GROUP_CN,
                "cloud.tencent.com", "非 OpenAI 协议，需适配器"),
        _preset("MiniMax Speech 2.8 HD", "speech-2.8-hd", "https://api.minimax.chat/v1",
                GROUP_CN, "minimax.chat", "角色克隆 · 32 语种"),
        _preset("OpenAI", "tts-1", "https://api.openai.com/v1", GROUP_INTL, "openai.com"),
        _preset("ElevenLabs", "eleven_v4_turbo", "https://api.elevenlabs.io/v1",
                GROUP_INTL, "elevenlabs.io", "多语言/情感"),
        _preset("HeyGen Voice", "heygen-voice", "https://api.heygen.com/v2",
                GROUP_INTL, "heygen.com", "克隆榜第 1；价格高"),
        _preset("Azure OpenAI", "tts", "https://<resource>.openai.azure.com/openai/v1",
                GROUP_INTL, "azure.microsoft.com", "替换 resource 子域"),
        _preset("Google Cloud TTS", "tts", "https://texttospeech.googleapis.com/v1",
                GROUP_INTL, "cloud.google.com", "非 OpenAI 协议，需适配器"),
        _preset("硅基流动", "FunAudioLLM/CosyVoice2-0.5B", "https://api.siliconflow.cn/v1",
                GROUP_THIRD, "siliconflow.cn"),
        _preset("302.AI", "tts-1", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "music": [
        _preset("ACE-Step 1.5", "ace-step-1.5", "http://localhost:8001/v1", GROUP_CN,
                "github.com/ace-step", "MIT · <4GB 显存 · 可带人声"),
        _preset("Suno", "suno-v6", "https://api.suno.ai/v1", GROUP_INTL, "suno.ai",
                "质量领先；无官方 API，第三方非官方"),
        _preset("Mureka", "mureka-v9", "https://api.mureka.ai/v1", GROUP_INTL, "mureka.ai",
                "官方 API 带商用授权"),
        _preset("ElevenLabs Music", "eleven-music-v2.5", "https://api.elevenlabs.io/v1",
                GROUP_INTL, "elevenlabs.io", "不含影视/广播；$0.15/分钟"),
        _preset("Google Lyria", "lyria-3.5", "https://generativelanguage.googleapis.com/v1beta",
                GROUP_INTL, "ai.google.dev", "最便宜官方 API；SynthID"),
        _preset("Stability Audio", "stable-audio-3", "https://api.stability.ai/v2beta",
                GROUP_INTL, "stability.ai", "无人声；收入门槛"),
        _preset("Replicate MusicGen", "meta/musicgen", "https://api.replicate.com/v1",
                GROUP_INTL, "replicate.com"),
        _preset("302.AI", "suno-v6", "https://api.302.ai/v1", GROUP_THIRD, "302.ai"),
    ],
    "lipsync": [
        _preset("可灵 Avatar 2.0", "kling-avatar-2.0", "https://api.klingai.com/v1",
                GROUP_CN, "klingai.com", "生成式数字人"),
        _preset("Sync.so", "sync-2.0", "https://api.sync.so/v2", GROUP_INTL, "sync.so",
                "实拍同步准确度标杆；约 $0.04/秒"),
        _preset("HeyGen Avatar IV", "avatar-iv", "https://api.heygen.com/v2", GROUP_INTL,
                "heygen.com", "单人口播/翻译"),
        _preset("D-ID", "talks", "https://api.d-id.com", GROUP_INTL, "d-id.com"),
        _preset("Runway Act-Two", "act-two", "https://api.dev.runwayml.com/v1",
                GROUP_INTL, "runwayml.com", "表演驱动/表情动作"),
        _preset("Hedra", "character-3", "https://api.hedra.com/v1", GROUP_INTL,
                "hedra.com", "一张图生成表演"),
        _preset("OmniHuman 2.0", "omnihuman-2.0", "https://ark.cn-beijing.volces.com/api/v3",
                GROUP_CN, "volcengine.com", "BytePlus · 单镜最长 5 分钟"),
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
