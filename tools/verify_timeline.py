#!/usr/bin/env python3
"""M9 剪辑契约层 · 独立复测（时间线/ASL/权重/命名/reel + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.timeline import exchange, rhythm, timeline

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 时间线合法性 ----------------
clips = [timeline.make_clip("v1", 0, 5), timeline.make_clip("v2", 5, 3), timeline.make_clip("v3", 8, 4)]
check("连续无重叠无空洞合规", timeline.validate_timeline(clips, {"v1", "v2", "v3"}) == [])
check("重叠违规", timeline.validate_timeline(
    [timeline.make_clip("v1", 0, 5), timeline.make_clip("v2", 4, 3)], {"v1", "v2"}) != [])
check("空洞违规", timeline.validate_timeline(
    [timeline.make_clip("v1", 0, 5), timeline.make_clip("v2", 7, 3)], {"v1", "v2"}) != [])
check("引用不存在违规", timeline.validate_timeline(
    [timeline.make_clip("v1", 0, 5), timeline.make_clip("vX", 5, 3)], {"v1"}) != [])
check("空时间线违规", timeline.validate_timeline([], set()) != [])

# ---------------- ASL 节奏 ----------------
check("ASL 计算", abs(rhythm.asl([2, 3, 4]) - 3.0) < 1e-9)
check("ASL 2.5s 在带内", rhythm.validate_asl_band(2.5) == [])
check("ASL 6s 超带", rhythm.validate_asl_band(6.0) != [])
check("ASL 递减合规", rhythm.validate_asl_decreasing([4.0, 3.0, 2.0]) == [])
check("ASL 未递减违规", rhythm.validate_asl_decreasing([2.0, 4.0, 3.0]) != [])

# ---------------- Murch 权重 ----------------
check("情绪权重 0.51", abs(rhythm.murch_weight("emotion") - 0.51) < 1e-9)
check("故事权重 0.23", abs(rhythm.murch_weight("story") - 0.23) < 1e-9)
check("未知权重 0", rhythm.murch_weight("bogus") == 0.0)

# ---------------- 版本命名 ----------------
check("版本命名合规", exchange.validate_version_name("回声_1_1_LC_20261011") == [])
check("版本命名违规", exchange.validate_version_name("回声_1_1_20261011") != [])

# ---------------- reel 名 ----------------
check("cmx3600 8 字符合规", exchange.validate_reel_name("ABCDEFGH", "cmx3600") == [])
check("cmx3600 9 字符违规", exchange.validate_reel_name("ABCDEFGHI", "cmx3600") != [])
check("avid 32 字符合规", exchange.validate_reel_name("A" * 32, "avid") == [])
check("avid 33 字符违规", exchange.validate_reel_name("A" * 33, "avid") != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M9-timeline-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
