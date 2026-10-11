"""picture lock 与交换格式（M9.5：版本命名 + reel 名上限）。"""
import re

from . import enums

VERSION_RE = re.compile(r'^.+_.+_.+_LC_\d{8}$')


def validate_version_name(name):
    """版本命名（B-41：项目_季_集_LC_YYYYMMDD）。"""
    if not VERSION_RE.match(name):
        return ["版本命名不合规（应为 项目_季_集_LC_YYYYMMDD）：%r" % name]
    return []


def validate_reel_name(reel, format_="cmx3600"):
    """reel 名上限（B-42：CMX3600 仅 8 字符；Avid 32）。"""
    if format_ not in enums.REEL_MAX:
        return ["未知交换格式：%r" % format_]
    limit = enums.REEL_MAX[format_]
    if len(reel) > limit:
        return ["reel 名超长：%d > %d（%s）" % (len(reel), limit, format_)]
    return []
