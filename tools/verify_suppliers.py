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

# ---------------- 模型配置 + 适配层 ----------------
from film.suppliers import adapter, config as sup_config

cfg = sup_config.load_from_env()
check("6 个模型 kind", set(cfg.keys()) == set(sup_config.MODEL_KINDS))
check("无凭据时无可用 kind", sup_config.available_kinds(cfg) == [])

full_cfg = {k: {"model": "%s_model" % k, "api_key": "key", "api_url": ""} for k in sup_config.MODEL_KINDS}
check("完整配置校验通过", sup_config.validate_config(full_cfg) == [])
check("完整配置 6 个可用", len(sup_config.available_kinds(full_cfg)) == 6)

partial = dict(full_cfg)
partial["video"] = {"model": "m", "api_key": "", "api_url": ""}
check("配置不完整违规", sup_config.validate_config(partial) != [])

p = adapter.make_adapter("video", {"model": "", "api_key": ""})
check("未配置走 Mock", isinstance(p, adapter.MockProvider))
sub = p.submit({"fingerprint": "fp", "prompt": "hello"})
check("Mock submit 返回 task_id", sub["task_id"].startswith("mock:"))
q = p.query(sub["task_id"])
check("Mock query done", q["status"] == "done")
d = p.download(q)
check("Mock download 标 EL-16", "MOCK" in d["source"])

# 供应商预设
check("预设含 6 类", set(sup_config.PRESETS.keys()) == set(sup_config.MODEL_KINDS))
check("文本预设含 dashscope", any("dashscope" in p["api_url"] for p in sup_config.PRESETS["text"]))
check("视频预设含可灵", any("kling" in p["api_url"] for p in sup_config.PRESETS["video"]))
check("每个预设含 vendor/model/api_url", all(
    all(k in p for k in ("vendor", "model", "api_url"))
    for ps in sup_config.PRESETS.values() for p in ps))

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
