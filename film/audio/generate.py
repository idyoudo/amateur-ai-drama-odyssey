"""M8 配乐生成（实现层）：调音乐适配器产出 Cue 并校验授权。"""
from . import license as audio_license


def generate_music(cue, music_adapter, platform="ace_step", tier="any"):
    sub = music_adapter.submit({"prompt": cue})
    result = music_adapter.query(sub["task_id"])
    violations = audio_license.validate_music_license(platform, tier)
    if violations:
        raise ValueError("配乐授权不合规：%s" % ";".join(violations))
    checkpoint = {"produced_keys": [result.get("result", {}).get("object_key", "mock/music")]}
    return {"cue": cue, "platform": platform}, checkpoint
