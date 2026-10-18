"""分集格式预设与推荐（2026-10 调研）。

平台口径（公开资料）：
- 抖音真人短剧：2026-06-05 起单集 ≤3 分钟，建议约 1 分 30 秒，竖屏。
- 红果漫剧：常见约 1 分钟/集、60–120 集/季；平台扶持偏好 60 分钟以上成片。
- 快手星芒：竖屏短剧，行业常见 1–3 分钟/集。
- YouTube Shorts：官方支持 ≤3 分钟，9:16。
- YouTube 长视频：8–15 分钟/集，16:9。

本模块只提供建议，不强制；创建项目时用户可手动覆盖。
"""
import math

PLATFORMS = {
    "hongguo": {
        "name": "红果漫剧", "aspect": "9:16", "episode_seconds": 60,
        "seconds_range": (45, 180), "episodes_range": (60, 120), "default_episodes": 60,
        "chapters_per_ep": 1.5, "words_per_ep": 1.5,
        "note": "常见约 1 分钟/集、60–120 集/季；扶持偏好 60 分钟以上成片",
    },
    "douyin": {
        "name": "抖音短剧", "aspect": "9:16", "episode_seconds": 90,
        "seconds_range": (60, 180), "episodes_range": (60, 100), "default_episodes": 60,
        "chapters_per_ep": 1.5, "words_per_ep": 1.5,
        "note": "单集上限 3 分钟、建议约 1 分 30 秒（2026-06-05 起）",
    },
    "kuaishou": {
        "name": "快手星芒", "aspect": "9:16", "episode_seconds": 90,
        "seconds_range": (60, 180), "episodes_range": (60, 100), "default_episodes": 60,
        "chapters_per_ep": 1.5, "words_per_ep": 1.5,
        "note": "竖屏短剧，行业常见 1–3 分钟/集",
    },
    "youtube_shorts": {
        "name": "YouTube Shorts", "aspect": "9:16", "episode_seconds": 150,
        "seconds_range": (60, 180), "episodes_range": (30, 60), "default_episodes": 30,
        "chapters_per_ep": 3.0, "words_per_ep": 3.0,
        "note": "官方支持 ≤3 分钟，9:16；适合连续追更的短单元",
    },
    "youtube": {
        "name": "YouTube 长视频", "aspect": "16:9", "episode_seconds": 600,
        "seconds_range": (480, 900), "episodes_range": (6, 12), "default_episodes": 8,
        "chapters_per_ep": 15.0, "words_per_ep": 10.0,
        "note": "8–15 分钟/集，16:9；适合合集与深度叙事",
    },
    "tv30": {
        "name": "传统 30 分钟", "aspect": "2.39:1", "episode_seconds": 1800,
        "seconds_range": (1320, 2700), "episodes_range": (6, 12), "default_episodes": 6,
        "chapters_per_ep": 20.0, "words_per_ep": 20.0,
        "note": "6–12 集 × 22–45 分钟；传统剧集规格",
    },
}

SOURCE_TYPES = ("original", "novel")

# 分发渠道（与投放平台对齐；tv30 是制作包型，不作为分发渠道）
DISTRIBUTION_CHANNELS = ("hongguo", "douyin", "kuaishou", "youtube_shorts", "youtube")


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def recommend(platform="hongguo", source_type="original", words_wan=0, chapters=0, genre=""):
    """返回一季的建议分集数、单集秒数与理由；内容超季长时给出季数。"""
    key = platform if platform in PLATFORMS else "hongguo"
    p = PLATFORMS[key]
    per = p["episode_seconds"]
    lo, hi = p["episodes_range"]
    raw = p["default_episodes"]
    reasons = []

    if source_type == "novel":
        if chapters and chapters > 0:
            raw = int(round(chapters / p["chapters_per_ep"]))
            reasons.append("按 %d 章、每集约 %.1f 章估算" % (chapters, p["chapters_per_ep"]))
        elif words_wan and words_wan > 0:
            raw = int(round(words_wan / p["words_per_ep"]))
            reasons.append("按 %.1f 万字、每集约 %.1f 万字估算" % (words_wan, p["words_per_ep"]))
        else:
            reasons.append("未填原著规模，按平台默认季长")
    else:
        reasons.append("原创项目按平台默认季长")

    episodes = _clamp(raw, lo, hi)
    seasons = max(1, int(math.ceil(raw / float(hi)))) if raw > hi else 1
    if seasons > 1:
        episodes = _clamp(int(round(raw / float(seasons))), lo, hi)
    if raw < lo:
        reasons.append("内容偏短，建议补充支线或做成 %d 集短季" % lo)
    elif seasons > 1:
        reasons.append("全书约 %d 集，建议分 %d 季，每季约 %d 集" % (raw, seasons, episodes))

    season_minutes = round(episodes * per / 60.0, 1)
    if genre:
        reasons.append("%s题材：首集前 3 秒给冲突，每集结尾留反转" % genre)
    reasons.append(p["note"])

    return {
        "platform_key": key,
        "platform": p["name"],
        "source_type": source_type,
        "aspect": p["aspect"],
        "episodes": episodes,
        "episode_seconds": per,
        "episode_minutes": round(per / 60.0, 2),
        "season_minutes": season_minutes,
        "total_episodes": raw,
        "seasons": seasons,
        "reason": "；".join(reasons),
        "manual_allowed": True,
    }


def public_presets():
    return {
        "platforms": {
            k: {"name": v["name"], "aspect": v["aspect"],
                "episode_seconds": v["episode_seconds"], "note": v["note"],
                "episodes_range": list(v["episodes_range"]),
                "seconds_range": list(v["seconds_range"])}
            for k, v in PLATFORMS.items()
        },
        "source_types": list(SOURCE_TYPES),
    }


def public_channels():
    return {"channels": [{"key": k, "name": PLATFORMS[k]["name"],
                          "aspect": PLATFORMS[k]["aspect"],
                          "note": PLATFORMS[k]["note"]}
                         for k in DISTRIBUTION_CHANNELS]}
