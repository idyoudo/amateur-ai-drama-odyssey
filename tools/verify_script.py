#!/usr/bin/env python3
"""M2 结构校验契约层 · 独立复测（三幕节拍/15拍/四节点/场次区间/场景三元 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.script import enums, outline, structure

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


def mk_scenes(n, beat_fn=None):
    out = []
    for i in range(n):
        beats = [beat_fn(i)] if beat_fn else []
        out.append(outline.make_scene(i + 1, "SLUG", "事件", "目标", "冲突", "结果", beats))
    return out


# ---------------- 合法 outline ----------------
scenes = mk_scenes(20, lambda i: enums.BEATS_15[i % 15])
o = outline.make_outline("half_hour", scenes, 0.24, 0.50, 0.80, list(enums.TRUBY_NODES))
check("合法 outline 合规", outline.validate_outline(o) == [])

# ---------------- 三幕节拍位置 ----------------
check("节拍位置合规", structure.validate_beat_positions(0.24, 0.50, 0.80) == [])
check("PPI 越界违规", structure.validate_beat_positions(0.10, 0.50, 0.80) != [])
check("PPII 越界违规", structure.validate_beat_positions(0.24, 0.50, 0.90) != [])

# ---------------- 15 拍覆盖 ----------------
check("15 拍全覆盖合规", structure.validate_beats(list(enums.BEATS_15)) == [])
check("缺拍违规", structure.validate_beats(enums.BEATS_15[:-1]) != [])

# ---------------- 场次区间 ----------------
check("20 场 half_hour 合规", structure.validate_scene_count("half_hour", 20) == [])
check("2 场 half_hour 越界", structure.validate_scene_count("half_hour", 2) != [])
check("120 场 feature 越界", structure.validate_scene_count("feature", 120) != [])

# ---------------- Truby 四节点 ----------------
check("四节点齐备合规", structure.validate_truby(list(enums.TRUBY_NODES)) == [])
check("缺节点违规", structure.validate_truby(["Ghost", "Weakness"]) != [])

# ---------------- 场景三元 ----------------
check("场景三元齐备合规", outline.validate_scene(outline.make_scene(1, "S", "E", "G", "C", "R")) == [])
check("缺冲突违规", outline.validate_scene(outline.make_scene(1, "S", "E", "G", "", "R")) != [])

# ---------------- 整体变异 ----------------
bad_scenes = mk_scenes(20, lambda i: enums.BEATS_15[i % 14])  # 缺第 15 拍
o2 = outline.make_outline("half_hour", bad_scenes, 0.24, 0.50, 0.80, list(enums.TRUBY_NODES))
check("整体缺拍违规", outline.validate_outline(o2) != [])
o3 = outline.make_outline("bogus", scenes, 0.24, 0.50, 0.80, [])
check("非法形态违规", outline.validate_outline(o3) != [])

# ---------------- 生成（实现层，Mock） ----------------
from film.suppliers import adapter as sup_adapter
from film.script import generate as script_gen

ad = sup_adapter.make_adapter("text", {"model": "", "api_key": ""})
ol, cp = script_gen.generate_outline("一句话", ad)
check("生成 outline 结构合规", outline.validate_outline(ol) == [])
check("生成 checkpoint 有产出", len(cp["produced_keys"]) == 1)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M2-script-structure", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
