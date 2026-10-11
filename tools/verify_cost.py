#!/usr/bin/env python3
"""M14 成本契约层 · 独立复测（预算/预警/重生成/指标/去重 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.cost import budget, dedup, metrics, regen

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 预算硬阻断 ----------------
b = budget.make_budget("episode", 100)
check("预占 60 成功", budget.reserve(b, 60) is True)
check("预占超预算拒绝", budget.reserve(b, 50) is False)
check("结算在预算内", budget.settle(b, 80) is False)
check("消耗 80", b["consumed"] == 80)
b3 = budget.make_budget("episode", 100)
check("结算超预算", budget.settle(b3, 120) is True)

# ---------------- 分级预警 ----------------
b2 = budget.make_budget("episode", 100)
check("初始 ok", budget.warn_level(b2) == "ok")
budget.reserve(b2, 55)
check("55% warn_50", budget.warn_level(b2) == "warn_50")
budget.reserve(b2, 30)
check("85% warn_80", budget.warn_level(b2) == "warn_80")
check("超预算预占拒绝", budget.reserve(b2, 30) is False)
budget.settle(b2, 150)
check("结算后 blocked", budget.warn_level(b2) == "blocked")

# ---------------- 重生成预算 R ----------------
check("R 公式", regen.regen_budget(600, 20, 5) == 6)
check("R 零成本为 0", regen.regen_budget(600, 20, 0) == 0)

# ---------------- 单位母版成本 ----------------
check("单位母版成本", abs(metrics.unit_master_cost(400, 10) - 40.0) < 1e-9)
check("无交付分钟返回 None", metrics.unit_master_cost(400, 0) is None)
check("北极星", abs(metrics.master_minutes_per_cost(400, 10) - 0.025) < 1e-9)

# ---------------- 重复付费守护 ----------------
seen = set()
check("首次登记成功", dedup.register_fingerprint(seen, "fp1") is True)
check("重复登记拒绝", dedup.register_fingerprint(seen, "fp1") is False)
check("重复检测", dedup.is_duplicate(seen, "fp1") is True)
check("新指纹非重复", dedup.is_duplicate(seen, "fp2") is False)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M14-cost-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
