#!/usr/bin/env python3
"""M17 供应商契约层 · 独立复测（能力矩阵/路由/降级/许可 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.suppliers import license, matrix, route

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 能力矩阵 ----------------
m = matrix.make_model("m1", "video", {"reference_image": True, "first_last_frame": True,
                                       "multi_shot": False, "native_audio": False})
check("支持参考图", matrix.supports(m, "reference_image") is True)
check("不支持多镜头", matrix.supports(m, "multi_shot") is False)
check("能力校验通过", matrix.validate_task(m, ["reference_image", "first_last_frame"]) == [])
check("能力校验失败", matrix.validate_task(m, ["multi_shot"]) != [])
check("能力缺失不得默认支持", matrix.supports(m, "camera_control") is False)

# ---------------- 路由 ----------------
check("hero 用高质量", route.route_model("hero", "premium", "economy") == "premium")
check("对白正脸用高质量", route.route_model("dialogue_closeup", "premium", "economy") == "premium")
check("氛围镜用经济", route.route_model("ambient", "premium", "economy") == "economy")
check("过场镜用经济", route.route_model("transition", "premium", "economy") == "economy")

# ---------------- 降级链 ----------------
check("premium→standard", route.degrade_tier("premium") == "standard")
check("standard→economy", route.degrade_tier("standard") == "economy")
check("economy→None", route.degrade_tier("economy") is None)

# ---------------- 许可风险 ----------------
check("ComfyUI 不得内置", license.validate_bundle("ComfyUI") != [])
check("HunyuanVideo 不得内置", license.validate_bundle("HunyuanVideo") != [])
check("普通组件可内置", license.validate_bundle("Wan") == [])
check("InsightFace 商用违规", license.validate_insightface("InsightFace", True) != [])
check("InsightFace 非商用合规", license.validate_insightface("InsightFace", False) == [])
check("普通模型商用合规", license.validate_insightface("Wan", True) == [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M17-suppliers-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
