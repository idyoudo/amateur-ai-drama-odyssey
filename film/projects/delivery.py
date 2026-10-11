"""目标态交付规格清单（M1.0-F03：三画幅必交 + 可选 HDR10/5.1/48fps）。"""
from . import enums


def make_delivery_spec(optional=None):
    return {
        "master": "2.39:1",     # 主母版
        "platform": "16:9",     # 平台版
        "derived": "9:16",      # 竖屏衍生
        "optional": optional or [],   # HDR10 / 5.1 / 48fps
    }


def validate_delivery_spec(spec):
    v = []
    for field in ("master", "platform", "derived"):
        val = spec.get(field)
        if val not in enums.DELIVERY_ASPECTS:
            v.append("交付画幅 %s 非法：%r（允许 %s）" % (field, val, enums.DELIVERY_ASPECTS))
    for o in spec.get("optional", []):
        if o not in enums.OPTIONAL_DELIVERY:
            v.append("可选交付非法：%r（允许 %s）" % (o, enums.OPTIONAL_DELIVERY))
    return v
