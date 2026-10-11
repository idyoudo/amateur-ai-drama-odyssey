#!/usr/bin/env python3
"""M19 VFX 契约层 · 独立复测（物理骨架/修复优先级/变形宽银幕/门禁/许可 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.vfx import anamorphic, gate, repair, shotlist

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- VFX 类型 ----------------
check("repair 合法", shotlist.validate_vfx_type("repair") == [])
check("非法类型违规", shotlist.validate_vfx_type("bogus") != [])

# ---------------- 物理骨架通道 ----------------
check("高动态有骨架合规", shotlist.require_skeleton(
    {"physics_trigger": "high_dynamic", "has_skeleton": True}) == [])
check("碰撞无骨架违规", shotlist.require_skeleton(
    {"physics_trigger": "collision", "has_skeleton": False}) != [])
check("普通镜头无骨架合规", shotlist.require_skeleton(
    {"physics_trigger": "none", "has_skeleton": False}) == [])

# ---------------- 修复优先级 ----------------
check("轻微缺陷局部修复", repair.repair_priority("minor") == "local_repair")
check("中度局部重生成", repair.repair_priority("moderate") == "local_regen")
check("重度整镜重抽", repair.repair_priority("severe") == "full_resample")

# ---------------- 变形宽银幕 ----------------
check("三项齐备合规", anamorphic.validate_anamorphic(
    ["oval_bokeh", "horizontal_flare", "2.39:1"]) == [])
check("缺 flare 违规", anamorphic.validate_anamorphic(["oval_bokeh", "2.39:1"]) != [])

# ---------------- VFX 门禁 ----------------
check("完成 VFX 合规", gate.validate_vfx_gate(
    {"requires_vfx": True, "vfx_done": True}) == [])
check("未完成 VFX 违规", gate.validate_vfx_gate(
    {"requires_vfx": True, "vfx_done": False}) != [])
check("无需 VFX 合规", gate.validate_vfx_gate(
    {"requires_vfx": False, "vfx_done": False}) == [])

# ---------------- 工具许可 ----------------
check("ComfyUI 不得内置", gate.validate_tool_license("ComfyUI") != [])
check("普通工具可内置", gate.validate_tool_license("Natron") == [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M19-vfx-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
