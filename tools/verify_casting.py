#!/usr/bin/env python3
"""M3 选角契约层 · 独立复测（锚点/角色卡/定妆门禁 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.casting import anchors, character, gates

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 锚点图集 ----------------
ok_anchors = [anchors.make_anchor(v, "key_%s" % v) for v in ("front", "side", "full_body")]
check("3 张 3 视角合规", anchors.validate_anchors(ok_anchors) == [])
check("2 张违规", anchors.validate_anchors(ok_anchors[:2]) != [])
check("2 视角违规", anchors.validate_anchors(
    [anchors.make_anchor("front", "a"), anchors.make_anchor("front", "b"),
     anchors.make_anchor("front", "c")]) != [])
check("9 张超上限违规", anchors.validate_anchors(
    [anchors.make_anchor("front", str(i)) for i in range(9)]) != [])

# ---------------- 角色卡 ----------------
ch = character.make_character("主角", ok_anchors, voice_key="v1")
check("角色卡合规", character.validate_character(ch) == [])
ch2 = character.make_character("主角", ok_anchors, voice_key=None)
check("未绑定音色违规", character.validate_character(ch2) != [])
ch3 = character.make_character("主角", ok_anchors, voice_key="v1", uses_real_likeness=True, consent=None)
check("真人形象无授权违规", character.validate_character(ch3) != [])
ch4 = character.make_character("主角", ok_anchors, voice_key="v1", uses_real_likeness=True, consent={"scope": "drama"})
check("真人形象有授权合规", character.validate_character(ch4) == [])

# ---------------- 定妆门禁 ----------------
g = {"approver": "张三", "approver_position": "showrunner", "doer_position": "director",
     "reason_code": "pass_with_condition", "decision": "approve", "locked": True}
check("定妆门禁合规", gates.validate_casting_gate(g) == [])
check("未署名违规", gates.validate_casting_gate({**g, "approver": ""}) != [])
check("自审自批违规", gates.validate_casting_gate({**g, "approver_position": "director"}) != [])
check("理由码非法违规", gates.validate_casting_gate({**g, "reason_code": "随便"}) != [])
check("通过未锁定违规", gates.validate_casting_gate({**g, "locked": False}) != [])
check("writer 无权签定妆违规", gates.validate_casting_gate({**g, "approver_position": "writer"}) != [])

# ---------------- 生成（实现层，Mock） ----------------
from film.suppliers import adapter as sup_adapter
from film.casting import generate as casting_gen

ad = sup_adapter.make_adapter("image", {"model": "", "api_key": ""})
ch, cp = casting_gen.generate_casting("主角", ad)
check("生成角色卡合规", character.validate_character(ch) == [])
check("生成 checkpoint 有产出", len(cp["produced_keys"]) == 1)
# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M3-casting-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
