"""轴线与越轴（M6.5：越轴告警而非否决 + 合法越轴四法）。"""
from . import enums


def is_crossing_axis(side_a, side_b):
    """相邻镜在轴线两侧即越轴。"""
    return side_a in ("A", "B") and side_b in ("A", "B") and side_a != side_b


def legal_crossing(changes_direction, arc_move, buffer_shot, prelap):
    """合法越轴四法（M6.5-F03）：①改变运动方向 ②机位弧移 ③缓冲镜头 ④pre-lap 台词。"""
    return any((changes_direction, arc_move, buffer_shot, prelap))


def axis_verdict(side_a, side_b, legal=False):
    """越轴判定：合法越轴仅记录；非法越轴为告警，**绝不硬否决**（E-58/B-46）。"""
    if not is_crossing_axis(side_a, side_b):
        return "ok"
    return "legal_crossing" if legal else "warn"
