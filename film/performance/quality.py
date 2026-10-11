"""配音质检（M7.6：情绪回落 + 角色电平差 ≤1 dB）。"""
from . import enums


def norm_emotion(raw):
    """情绪归一（M7.4-F03）：未知情绪整条回落 neutral，禁止静默忽略。"""
    v = (raw or "").lower()
    return v if v in enums.EMOTIONS else "neutral"


def validate_level_diff(levels):
    """角色间对白电平差 ≤1 dB（M7.6-F03）。"""
    if not levels:
        return []
    spread = max(levels) - min(levels)
    if spread > enums.LEVEL_MAX_DIFF_DB:
        return ["角色间电平差 %.2f dB > %.1f dB" % (spread, enums.LEVEL_MAX_DIFF_DB)]
    return []
