#!/usr/bin/env python3
"""C8 资产编号参考槽位 · 独立复测。"""
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);sys.path.insert(0,ROOT)
from film.slots import build_slots, compile_slot_prompt, validate_slots, SLOT_ORDER
_t=[0];_f=[]
def check(n,c):
    _t[0]+=1
    if not c:_f.append(n)
sl=build_slots("scene_01",["char_A","char_B"],["prop_knife"])
check("4 槽位", len(sl)==4)
check("编号从 1 连续", [s["slot"] for s in sl]==[1,2,3,4])
check("token 正确", [s["token"] for s in sl]==["@图片1","@图片2","@图片3","@图片4"])
check("顺序 场景→角色→道具", [s["kind"] for s in sl]==["scene","character","character","prop"])
check("槽位校验合规", validate_slots(sl)==[])
p=compile_slot_prompt("主角推门", sl)
check("提示词含槽位前缀", p.startswith("[参考图]") and "@图片1" in p and "主角推门" in p)
check("无槽位不改提示词", compile_slot_prompt("x", []) == "x")
# 上限 9
many=build_slots("s",["c%d"%i for i in range(10)])
check("超 9 槽被拒", validate_slots(many) != [])
# 顺序违规
bad=[{"slot":1,"kind":"character","asset_id":"c","token":"@图片1"},{"slot":2,"kind":"scene","asset_id":"s","token":"@图片2"}]
check("顺序违规被拒", validate_slots(bad) != [])
total=_t[0];passed=total-len(_f)
print(json.dumps({"module":"C8-slots","total":total,"pass":passed,"fail":len(_f)},ensure_ascii=False))
sys.exit(1 if _f else 0)
