"""锚点图集（M3.2-F03：每角色 3–8 张、最少 3 张、覆盖 ≥3 视角，是与 M6 共享的一致性基准）。"""
from . import enums


def make_anchor(view, image_key):
    return {"view": view, "image_key": image_key}


def validate_anchors(anchors):
    """锚点图集不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if len(anchors) < 3:
        v.append("锚点 <3 张（当前 %d）" % len(anchors))
    if len(anchors) > 8:
        v.append("锚点 >8 张（当前 %d）" % len(anchors))
    views = {a.get("view") for a in anchors}
    if len(views) < 3:
        v.append("锚点覆盖视角 <3（当前 %d）" % len(views))
    for a in anchors:
        if a.get("view") not in enums.ANCHOR_VIEWS:
            v.append("非法视角：%r" % (a.get("view"),))
    return v
