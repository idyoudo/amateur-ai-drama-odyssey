"""字幕合规（M11.5-F04 / B-32/B-33/B-16：5–7s、≤2 行、中文 ≤23 字/行）。"""
from . import enums


def validate_subtitle(duration_sec, lines):
    v = []
    if not (enums.SUBTITLE_MIN_SEC <= duration_sec <= enums.SUBTITLE_MAX_SEC):
        v.append("字幕时长 %.1f s 不在 %.0f–%.0f s" % (duration_sec, enums.SUBTITLE_MIN_SEC, enums.SUBTITLE_MAX_SEC))
    if len(lines) > enums.SUBTITLE_MAX_LINES:
        v.append("字幕行数 %d > %d" % (len(lines), enums.SUBTITLE_MAX_LINES))
    for line in lines:
        if len(line) > enums.SUBTITLE_MAX_CHARS_PER_LINE:
            v.append("字幕行超 %d 字符（当前 %d）" % (enums.SUBTITLE_MAX_CHARS_PER_LINE, len(line)))
    return v
