"""Step Outline 结构校验（三幕节拍/15 拍/四节点/场次区间）。"""
from . import enums


def validate_beat_positions(ppi, midpoint, ppii):
    """三幕节拍位置（M2.4-F03）：越界即违规。返回违规列表，空 = 合规。"""
    v = []
    lo, hi = enums.BEAT_WINDOWS["ppi"]
    if not (lo <= ppi <= hi):
        v.append("Plot Point I 位置 %s 越界（应 %s–%s）" % (ppi, lo, hi))
    lo, hi = enums.BEAT_WINDOWS["midpoint"]
    if not (lo <= midpoint <= hi):
        v.append("Midpoint 位置 %s 越界（应 %s–%s）" % (midpoint, lo, hi))
    lo, hi = enums.BEAT_WINDOWS["ppii"]
    if not (lo <= ppii <= hi):
        v.append("Plot Point II 位置 %s 越界（应 %s–%s）" % (ppii, lo, hi))
    return v


def validate_beats(covered_beats):
    """15 拍覆盖（M2.4-F04）：每拍须有 ≥1 场承载，缺失拍号输出清单。"""
    covered = set(covered_beats)
    missing = [b for b in enums.BEATS_15 if b not in covered]
    v = []
    if missing:
        v.append("缺失 Save the Cat 拍：%s" % "/".join(missing))
    return v


def validate_truby(truby_nodes):
    """Truby 四节点（M2.4-F05）：四节点各需 ≥1 处证据。"""
    v = []
    for node in enums.TRUBY_NODES:
        if node not in truby_nodes:
            v.append("缺 Truby 节点：%s" % node)
    return v


def validate_scene_count(form, scene_count):
    """场次数区间（M2.4-F01）。"""
    v = []
    lo, hi = enums.SCENE_RANGES[form]
    if not (lo <= scene_count <= hi):
        v.append("场次数 %d 越界（%s 应 %d–%d）" % (scene_count, form, lo, hi))
    return v
