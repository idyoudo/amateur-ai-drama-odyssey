"""变形宽银幕光学特征（M19.4-F05：三项齐备才可标注 anamorphic）。"""
from . import enums


def validate_anamorphic(features):
    """oval bokeh + 水平 flare + 2.39:1 三项齐备校验。"""
    v = []
    for f in enums.ANAMORPHIC_FEATURES:
        if f not in features:
            v.append("缺 anamorphic 特征 %s" % f)
    return v
