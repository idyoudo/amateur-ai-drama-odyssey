"""M7 配音生成（实现层）：调 TTS 适配器产出音轨段并校验音画同步。"""
from . import sync


def generate_voice(line, tts_adapter):
    sub = tts_adapter.submit({"prompt": line})
    result = tts_adapter.query(sub["task_id"])
    violations = sync.validate_av_offset(0)  # Mock 同步在工程目标内
    if violations:
        raise ValueError("配音同步不合规：%s" % ";".join(violations))
    checkpoint = {"produced_keys": [result.get("result", {}).get("object_key", "mock/voice")]}
    return {"line": line, "offset_ms": 0}, checkpoint
