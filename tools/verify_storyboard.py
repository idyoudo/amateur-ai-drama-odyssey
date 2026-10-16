#!/usr/bin/env python3
"""M4 分镜表生成复测：从 outline 派生镜头 + 契约校验 + 变异样本。"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from film.storyboard import make_shotlist, validate_shot
from film.script import generate as m2g
from film.suppliers import adapter as sa

_t = [0]; _f = []
def check(n, c):
    _t[0] += 1
    if not c: _f.append(n)

ol, _ = m2g.generate_outline("x", sa.make_adapter("text", {}))
shots = make_shotlist(ol, ["主角", "配角"])
check("派生镜头数 = 场次 1-3 倍之和", len(shots) == sum(1 + (sc["number"] % 3) for sc in ol["scenes"]))
check("镜头号连续", [s["shot_no"] for s in shots] == list(range(1, len(shots) + 1)))
check("全部镜头契约合法", all(validate_shot(s) == [] for s in shots))
check("景别在封闭枚举内", all(s["size"] in ("WS","MS","MCU","CU","MLS","LS") for s in shots))
# 变异
bad = dict(shots[0]); bad["size"] = "XXX"
check("非法景别被拒", validate_shot(bad) != [])
bad2 = dict(shots[0]); bad2["move"] = "乱写"
check("非法运镜被拒", validate_shot(bad2) != [])
bad3 = dict(shots[0]); bad3["duration"] = 0
check("零时长被拒", validate_shot(bad3) != [])

total = _t[0]; passed = total - len(_f)
print(json.dumps({"module": "M4-storyboard", "total": total, "pass": passed, "fail": len(_f)}, ensure_ascii=False))
sys.exit(1 if _f else 0)
