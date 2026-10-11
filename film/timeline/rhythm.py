"""节奏设计（M9.2：滑窗 ASL + 张力段递减 + Murch 权重）。"""
from . import enums


def asl(durations):
    """平均镜头长度。"""
    return sum(durations) / len(durations) if durations else 0.0


def validate_asl_band(asl_value):
    """ASL 落在 2–4 s 参考带（E-53）；超出需附人工理由。"""
    lo, hi = enums.ASL_REF_BAND
    if not (lo <= asl_value <= hi):
        return ["ASL %.2f s 超出 %.0f–%.0f s 参考带" % (asl_value, lo, hi)]
    return []


def validate_asl_decreasing(window_asls):
    """张力上升段 ASL 单调递减、切点密度上升（E-62）。"""
    v = []
    for i in range(1, len(window_asls)):
        if window_asls[i] > window_asls[i - 1]:
            v.append("ASL 未递减：窗口 %d(%.2f) -> %d(%.2f)" % (i - 1, window_asls[i - 1], i, window_asls[i]))
    return v


def murch_weight(reason):
    """剪点取舍权重（E-55）。未知理由返回 0。"""
    return enums.MURCH_WEIGHTS.get(reason, 0.0)
