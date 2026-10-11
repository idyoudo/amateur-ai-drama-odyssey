#!/usr/bin/env python3
"""M5 摄影生成（实现层）复测：调视频适配器（Mock）产出 checkpoint。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.photography import generate_shot
from film.suppliers import adapter as sup_adapter

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


ad = sup_adapter.make_adapter("video", {"model": "", "api_key": ""})
p, cp = generate_shot("测试提示词", ad, "fp123")
check("生成镜头返回 prompt", p["prompt"] == "测试提示词")
check("生成 checkpoint 有产出", len(cp["produced_keys"]) == 1)
# 确定性：同 fingerprint 同 task_id
p2, cp2 = generate_shot("测试提示词", ad, "fp123")
check("同输入同 checkpoint（确定性）", cp["produced_keys"] == cp2["produced_keys"])

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M5-photo-generate", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
sys.exit(1 if _failed else 0)
