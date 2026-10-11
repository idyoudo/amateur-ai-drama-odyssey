"""AI 音乐/音效授权门禁（M8.6-F01 / A-21：按平台条款分档放行）。"""


def validate_music_license(platform, tier):
    """AI 音乐授权档位校验。返回违规列表，空 = 合规（可商用）。"""
    platform = (platform or "").lower()
    tier = (tier or "").lower()
    if platform == "suno":
        if tier not in ("pro", "premier"):
            return ["Suno 仅订阅档（Pro/Premier）才可商用，且不保证版权"]
    elif platform == "mureka":
        if tier == "free":
            return ["Mureka 免费层不可商用"]
    elif platform == "ace_step":
        return []  # Apache-2.0 可直接内置
    else:
        return ["未识别平台：%r" % platform]
    return []
