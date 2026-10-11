"""对白解析与说话人归属（M7.2：角色：台词 解析 + 旁白独立 + 角色名归一）。"""
import re

from . import enums

_LINE_RE = re.compile(r'^(?:【([^】]+)】|(.+?)[：:])\s*(.+)$')


def parse_line(line):
    """解析对白行 → (speaker, text)；非对白行返回 None。"""
    line = (line or "").strip()
    if not line:
        return None
    m = _LINE_RE.match(line)
    if not m:
        return None
    speaker = (m.group(1) or m.group(2)).strip()
    text = m.group(3).strip()
    return speaker, text


def is_narration(speaker):
    return any(h.lower() in (speaker or "").lower() for h in enums.NARRATION_HINTS)


def classify_line(line):
    """对白行分类：('dialogue'|'narration', speaker, text) 或 None。"""
    p = parse_line(line)
    if p is None:
        return None
    speaker, text = p
    return ("narration" if is_narration(speaker) else "dialogue", speaker, text)


def normalize_speaker(speaker, aliases):
    """角色别名归一（M7.2-F05）：别名表归一到角色 ID。"""
    return aliases.get(speaker, speaker)
