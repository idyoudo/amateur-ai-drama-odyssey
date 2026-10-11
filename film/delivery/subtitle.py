"""字幕排版与来源（M12.2-F01/F02）。"""
from . import enums


def validate_cue_source(source):
    """字幕来源统一（E-31）：tts/asr/estimate，禁止把估算标成 provider。"""
    if source not in enums.CUE_SOURCES:
        return ["字幕来源非法：%r（应 tts/asr/estimate，禁止标 provider）" % source]
    return []


def validate_cue_layout(duration_sec, lines, vertical=False):
    """字幕排版（B-05/B-06）：中文 ≤23 字/行、最短 ≥0.833s、竖屏 ≤3 行。"""
    v = []
    if duration_sec < enums.SUBTITLE_MIN_SEC:
        v.append("字幕时长 %.3f s < %.3f s" % (duration_sec, enums.SUBTITLE_MIN_SEC))
    for line in lines:
        if len(line) > enums.SUBTITLE_MAX_CHARS:
            v.append("字幕行超 %d 字符（当前 %d）" % (enums.SUBTITLE_MAX_CHARS, len(line)))
    if vertical and len(lines) > enums.VERTICAL_MAX_LINES:
        v.append("竖屏字幕行数 %d > %d" % (len(lines), enums.VERTICAL_MAX_LINES))
    return v
