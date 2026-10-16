#!/usr/bin/env python3
"""C3 双管线降级 · 独立复测（帧幻灯片计划 + Ken Burns + 时长对齐 + 管线选择）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film import fallback

_t = [0]; _f = []
def check(n, c):
    _t[0] += 1
    if not c: _f.append(n)


shots = [{"shot_no": 1, "duration": 4, "size": "CU", "image_key": "k1"},
         {"shot_no": 2, "duration": 5, "size": "WS"},
         {"shot_no": 3, "duration": 3, "size": "MS"}]
plan = fallback.build_slideshow(shots, voice_durations={1: 4.2, 3: 2.8})
check("段数 = 镜数", plan["count"] == 3)
check("计划校验合规", fallback.validate_plan(plan) == [])
check("时长对齐配音（镜1=4.2）", plan["segments"][0]["duration"] == 4.2)
check("无配音镜用原时长（镜2=5）", plan["segments"][1]["duration"] == 5.0)
check("静音镜加 BGM（镜2）", plan["segments"][1]["bgm"] is True and plan["segments"][1]["audio"] == "bgm")
check("有配音镜标 voice（镜1）", plan["segments"][0]["audio"] == "voice")
check("Ken Burns 合法", all(s["motion"] in fallback.KEN_BURNS for s in plan["segments"]))
check("关键帧非空", all(s["keyframe"] for s in plan["segments"]))
check("含 fingerprint", bool(plan["fingerprint"]))
check("总时长 = 段时长之和", abs(plan["total"] - sum(s["duration"] for s in plan["segments"])) < 0.01)

# 确定性：同输入同指纹
p2 = fallback.build_slideshow(shots, voice_durations={1: 4.2, 3: 2.8})
check("同输入同指纹（确定性）", p2["fingerprint"] == plan["fingerprint"])

# 管线选择
check("无视频→slideshow", fallback.choose_pipeline(False) == "slideshow")
check("有视频→ai_video", fallback.choose_pipeline(True) == "ai_video")
check("强制幻灯片", fallback.choose_pipeline(True, force_slideshow=True) == "slideshow")

# 变异
bad = {"segments": [{"shot_no": 1, "duration": 0, "motion": "zoom_in", "keyframe": "k"}], "fingerprint": "f"}
check("零时长被拒", fallback.validate_plan(bad) != [])
bad2 = {"segments": [{"shot_no": 1, "duration": 3, "motion": "乱写", "keyframe": "k"}], "fingerprint": "f"}
check("非法运动被拒", fallback.validate_plan(bad2) != [])
check("空计划被拒", fallback.validate_plan({"segments": [], "fingerprint": "f"}) != [])

total = _t[0]; passed = total - len(_f)
print(json.dumps({"module": "C3-dual-pipeline", "total": total, "pass": passed, "fail": len(_f)}, ensure_ascii=False))
sys.exit(1 if _f else 0)
