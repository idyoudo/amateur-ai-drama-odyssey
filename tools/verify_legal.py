#!/usr/bin/env python3
"""M18 法律契约层 · 独立复测（署名/素材来源/同意/标识/合规 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.legal import compliance, consent, credit, label

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 署名（AI 不得 writer） ----------------
check("人类署名合规", credit.validate_credit(
    {"name": "张三", "role": "writer", "subject_type": "human"}) == [])
check("AI 署名违规", credit.validate_credit(
    {"name": "AI", "role": "writer", "subject_type": "ai"}) != [])
check("非法角色违规", credit.validate_credit(
    {"name": "张三", "role": "bogus", "subject_type": "human"}) != [])

# ---------------- source material ----------------
check("人类材料合规", credit.validate_source_material({"name": "原著", "origin": "human"}) == [])
check("AI 材料计入违规", credit.validate_source_material({"name": "AI 稿", "origin": "ai"}) != [])

# ---------------- 同意记录 ----------------
check("同意记录合规", consent.validate_consent(
    {"who": "张三", "when": "2026-10-11", "scope": "AI 辅助剧本"}) == [])
check("缺同意字段违规", consent.validate_consent({"who": "张三"}) != [])
check("数字替身合规", consent.validate_digital_double(
    {"consent": "书面", "compensation": "约定", "scope": "首季"}) == [])
check("数字替身缺补偿违规", consent.validate_digital_double(
    {"consent": "书面", "scope": "首季"}) != [])

# ---------------- AI 标识 ----------------
check("三类标识齐备", label.validate_ai_labels(["explicit", "implicit", "export_file"]) == [])
check("缺导出文件标识违规", label.validate_ai_labels(["explicit", "implicit"]) != [])

# ---------------- 交付前合规 ----------------
check("全合规通过", compliance.validate_delivery_compliance(True, True, True, True, True) == [])
check("缺权利链违规", compliance.validate_delivery_compliance(False, True, True, True, True) != [])
check("缺 AI 标识违规", compliance.validate_delivery_compliance(True, True, False, True, True) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M18-legal-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
