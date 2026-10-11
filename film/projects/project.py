"""立项单（M1.0-F01：logline 必填 ≤120 字，缺 logline 不可提交）。"""
from . import delivery, enums, package


def make_project(title, logline, platform, rating, genre, episodes=6, minutes=30,
                 style="写实", optional_delivery=None, pilot_mode=False):
    return {
        "title": title,
        "logline": logline,
        "platform": platform,
        "rating": rating,
        "genre": genre,
        "style": style,
        "package": package.make_package(episodes, minutes),
        "delivery_spec": delivery.make_delivery_spec(optional_delivery),
        "pilot_mode": bool(pilot_mode),
    }


def validate_project(p):
    """立项单不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    logline = p.get("logline") or ""
    if not logline.strip():
        v.append("缺 logline，不可提交（M1.0-F01）")
    elif len(logline) > 120:
        v.append("logline ≤120 字，当前 %d 字" % len(logline))
    if p.get("rating") not in enums.RATINGS:
        v.append("分级非法：%r（允许 %s）" % (p.get("rating"), enums.RATINGS))
    if p.get("style") not in enums.STYLES:
        v.append("风格非法：%r（允许 %s）" % (p.get("style"), enums.STYLES))
    pk = p.get("package") or {}
    v += package.validate_params(p.get("title"), pk.get("episodes", 0), pk.get("minutes", 0))
    v += delivery.validate_delivery_spec(p.get("delivery_spec") or {})
    return v
