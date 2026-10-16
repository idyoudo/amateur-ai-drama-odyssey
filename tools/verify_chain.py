#!/usr/bin/env python3
"""C4 首尾帧锚定链 · 独立复测。"""
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);sys.path.insert(0,ROOT)
from film.continuity_chain import build_chain, validate_chain
_t=[0];_f=[]
def check(n,c):
    _t[0]+=1
    if not c:_f.append(n)
c = build_chain([{"shot_no":1,"scene_no":1},{"shot_no":2,"scene_no":1},{"shot_no":3,"scene_no":2},{"shot_no":4,"scene_no":2}])
check("4 段链", len(c)==4)
check("首镜重挂参考图", c[0]["must_rerig_ref"] and c[0]["head_from"] is None)
check("同场镜用上镜尾帧", c[1]["head_from"] is not None and not c[1]["must_rerig_ref"])
check("换场重挂参考图", c[2]["must_rerig_ref"] and c[2]["head_from"] is None)
check("链校验合规", validate_chain(c) == [])
bad=[{"shot_no":1,"head_from":None,"must_rerig_ref":False}]
check("无来源且未重挂被拒", validate_chain(bad) != [])
total=_t[0];passed=total-len(_f)
print(json.dumps({"module":"C4-chain","total":total,"pass":passed,"fail":len(_f)},ensure_ascii=False))
sys.exit(1 if _f else 0)
