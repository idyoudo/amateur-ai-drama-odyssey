#!/usr/bin/env python3
"""M6 一致性契约层 · 独立复测（阈值/连续性/越轴/同框上限 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.consistency import axis, continuity, shots, thresholds

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 人脸阈值 ----------------
check("0.6 通过", thresholds.face_verdict(0.6) == "pass")
check("0.40 灰区", thresholds.face_verdict(0.40) == "gray")
check("0.20 失败", thresholds.face_verdict(0.20) == "fail")
check("0.45 边界通过", thresholds.face_verdict(0.45) == "pass")

# ---------------- 分位截断 ----------------
check("低于 P10 进复核", thresholds.quantile_trim(0.90, 0.92, 0.95, 0.02) is True)
check("高于阈值不进复核", thresholds.quantile_trim(0.96, 0.92, 0.95, 0.02) is False)
check("均值-2σ 进复核", thresholds.quantile_trim(0.30, 0.60, 0.90, 0.10) is True)

# ---------------- 同框上限 ----------------
check("3 人合规", shots.validate_shot_characters(["a", "b", "c"]) == [])
check("4 人违规", shots.validate_shot_characters(["a", "b", "c", "d"]) != [])

# ---------------- 连续性字段表 ----------------
t = continuity.make_take(5, "门口", "left", "right", "开门", "50mm")
check("字段齐备合规", continuity.validate_take(t) == [])
check("缺字段违规", continuity.validate_take(
    continuity.make_take(5, "", "left", "right", "开门", "50mm")) != [])

# ---------------- 屏幕方向（左出右入） ----------------
a = continuity.make_take(5, "门口", "right", "left", "走", "35mm")  # entry right, exit left
b = continuity.make_take(5, "门口", "left", "right", "走", "35mm")   # entry left == a.exit left → 穿帮
check("方向穿帮检出", continuity.validate_screen_direction(a, b) != [])
c = continuity.make_take(5, "门口", "right", "left", "走", "35mm")   # entry right != a.exit left → 合规
check("方向一致合规", continuity.validate_screen_direction(a, c) == [])

# ---------------- eyeline ----------------
check("正反打互补合规", continuity.validate_eyeline("right", "left") == [])
check("正反打同侧违规", continuity.validate_eyeline("right", "right") != [])

# ---------------- 时间天气 ----------------
check("时间跳变未声明违规", continuity.validate_time_weather("day", "night", "晴", "晴") != [])
check("天气跳变违规", continuity.validate_time_weather("day", "day", "晴", "雨") != [])
check("一致合规", continuity.validate_time_weather("day", "day", "晴", "晴") == [])

# ---------------- 越轴 ----------------
check("同侧不越轴", axis.axis_verdict("A", "A") == "ok")
check("越轴告警", axis.axis_verdict("A", "B") == "warn")
check("合法越轴仅记录", axis.axis_verdict("A", "B", legal=True) == "legal_crossing")
check("合法越轴四法之一", axis.legal_crossing(True, False, False, False) is True)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M6-consistency-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
