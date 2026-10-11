"""四层总线与 stem（M8.1-F01：逐帧等长 + Σ(四路) 与母版差 ≤0.1 LU）。"""
import math

from . import enums


def power_sum_lufs(lufs_list):
    """LUFS 功率域求和：10*log10(Σ 10^(l/10))。"""
    return 10.0 * math.log10(sum(10 ** (l / 10.0) for l in lufs_list))


def make_stem(layer, duration, lufs=None):
    return {"layer": layer, "duration": duration, "lufs": lufs}


def validate_stems(stems, master_lufs=None):
    """四路 stem 不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    by_layer = {s.get("layer"): s for s in stems}
    for layer in enums.STEM_LAYERS:
        if layer not in by_layer:
            v.append("缺 stem 层 %s" % layer)
    durations = [s["duration"] for s in stems if s.get("duration") is not None]
    if durations and len(set(durations)) != 1:
        v.append("stem 时长不等：%s" % durations)
    if master_lufs is not None:
        lufs_list = [s["lufs"] for s in stems if s.get("lufs") is not None]
        if len(lufs_list) == 4:
            combined = power_sum_lufs(lufs_list)
            if abs(combined - master_lufs) > 0.1:
                v.append("Σ(stem)=%.2f LU 与母版 %.2f LU 差 >0.1" % (combined, master_lufs))
    return v
