"""字幕轨：SRT 解析/生成与时间轴校验。"""
import re

TIME_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def _sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000.0


def parse_srt(text):
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    cues = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        idx = 1 if re.fullmatch(r"\d+", lines[0]) else 0
        if idx >= len(lines):
            continue
        m = TIME_RE.search(lines[idx])
        if not m:
            continue
        start = _sec(*m.group(1, 2, 3, 4))
        end = _sec(*m.group(5, 6, 7, 8))
        content = " ".join(lines[idx + 1:]).strip()
        if not content:
            continue
        if end <= start:
            end = start + 0.5
        cues.append({"start": round(start, 3), "end": round(end, 3),
                     "text": content[:500]})
        if len(cues) >= 2000:
            break
    return cues


def _fmt_time(sec):
    sec = max(0.0, float(sec))
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        s += 1
        ms = 0
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def to_srt(cues):
    out = []
    ordered = sorted(cues or [], key=lambda c: float(c.get("start") or 0))
    for i, c in enumerate(ordered, 1):
        out.append(str(i))
        out.append("%s --> %s" % (_fmt_time(c.get("start", 0)), _fmt_time(c.get("end", 0))))
        out.append(str(c.get("text") or ""))
        out.append("")
    return "\n".join(out)


def validate_cues(cues):
    if not isinstance(cues, list):
        raise ValueError("cues 需为数组")
    if len(cues) > 2000:
        raise ValueError("字幕条数上限 2000")
    out = []
    for c in cues:
        try:
            start = float(c.get("start"))
            end = float(c.get("end"))
        except (TypeError, ValueError):
            raise ValueError("时间轴需为秒数")
        if start < 0 or end <= start:
            raise ValueError("每条字幕需满足 0 ≤ start < end")
        text = str(c.get("text") or "").strip()
        if not text:
            raise ValueError("字幕文本不能为空")
        out.append({"start": round(start, 3), "end": round(end, 3), "text": text[:500]})
    return sorted(out, key=lambda x: x["start"])
