#!/usr/bin/env python3
"""M1 立项契约层 · 独立复测（立项单/包型/交付规格/参数校验 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.projects import delivery, enums, package, project

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 包型预设 ----------------
pkg = package.make_package()
check("默认 6 集×30 分", pkg["episodes"] == 6 and pkg["minutes"] == 30 and pkg["seconds"] == 1800)
check("act breaks 30 分=3", pkg["act_breaks"] == 3)
check("cold open 默认开", pkg["cold_open"] is True)
check("45 分 act=4", package.make_package(6, 45)["act_breaks"] == 4)
try:
    package.make_package(6, 60)
    check("非法时长档抛错", False)
except ValueError:
    check("非法时长档抛错", True)

# ---------------- 参数校验 ----------------
check("合法参数", package.validate_params("标题", 6, 30) == [])
check("缺标题违规", package.validate_params("", 6, 30) != [])
check("集数越界违规", package.validate_params("标题", 51, 30) != [])
check("时长越界违规", package.validate_params("标题", 6, 46) != [])

# ---------------- 交付规格 ----------------
spec = delivery.make_delivery_spec(["HDR10", "5.1"])
check("交付规格合规", delivery.validate_delivery_spec(spec) == [])
check("可选交付非法违规", delivery.validate_delivery_spec(
    delivery.make_delivery_spec(["4K"])) != [])

# ---------------- 立项单 ----------------
p = project.make_project("标题", "一句话故事", "短剧平台", "全龄", "悬疑")
check("立项单合规", project.validate_project(p) == [])
p2 = project.make_project("标题", "", "短剧平台", "全龄", "悬疑")
check("缺 logline 违规", project.validate_project(p2) != [])
p3 = project.make_project("标题", "长" * 121, "短剧平台", "全龄", "悬疑")
check("logline 超长违规", project.validate_project(p3) != [])
p4 = project.make_project("标题", "一句话", "短剧平台", "R级", "悬疑")
check("分级非法违规", project.validate_project(p4) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M1-onboarding-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
