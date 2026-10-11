#!/usr/bin/env python3
"""M16 RBAC 契约层 · 独立复测（角色/权限矩阵/门禁署名/审计 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.rbac import audit, gates, permissions, roles

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 权限矩阵 ----------------
check("showrunner 可 generate", permissions.can("showrunner", "generate"))
check("writer 可 script_edit", permissions.can("writer", "script_edit"))
check("writer 不可 generate", not permissions.can("writer", "generate"))
check("editor 可 edit", permissions.can("editor", "edit"))
check("editor 不可 script_edit", not permissions.can("editor", "script_edit"))
check("colorist 可 grade", permissions.can("colorist", "grade"))
check("unknown 岗位拒绝", not permissions.can("bogus", "generate"))
check("unknown 操作拒绝", not permissions.can("writer", "bogus"))

# ---------------- 门禁署名 ----------------
check("director 可签 board", gates.validate_sign_off("board", "director") == [])
check("writer 不可签 picture", gates.validate_sign_off("picture", "writer") != [])
check("qc 可签 master", gates.validate_sign_off("master", "qc") == [])
check("自审自批违规", gates.validate_sign_off("board", "director", "director") != [])
check("非自审自批合规", gates.validate_sign_off("board", "showrunner", "director") == [])
check("非法门禁节点违规", gates.validate_sign_off("bogus", "director") != [])

# ---------------- 理由码 ----------------
check("合法理由码", gates.validate_reason("pass_zero_defect"))
check("合法理由码 reject", gates.validate_reason("reject_quality"))
check("非法理由码拒绝", not gates.validate_reason("随便"))

# ---------------- 审计 ----------------
a = audit.make_audit("u1", "generate", "shot:1", "2026-10-11T10:00:00", why="budget ok")
check("审计合规", audit.validate_audit(a) == [])
check("审计缺 who 违规", audit.validate_audit(audit.make_audit("", "x", "y", "z")) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M16-rbac-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
