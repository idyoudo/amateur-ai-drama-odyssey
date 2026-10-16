#!/usr/bin/env python3
"""C6 成本确认闸 · 独立复测。"""
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);sys.path.insert(0,ROOT)
from film.cost.confirm import preview_cost, validate_confirmation, UNIT_COST
_t=[0];_f=[]
def check(n,c):
    _t[0]+=1
    if not c:_f.append(n)
pv = preview_cost([{"kind":"video","seconds":40},{"kind":"image","count":10},{"kind":"tts","count":20}])
check("三项预估", len(pv["items"])==3)
check("视频按秒计费", abs(pv["items"][0]["cost_cny"] - UNIT_COST["video"]*40) < 0.01)
check("合计 = 各项和", abs(pv["total_cny"] - sum(r["cost_cny"] for r in pv["items"])) < 0.01)
check("需确认", pv["requires_confirmation"] is True)
check("超阈值未确认被拒", validate_confirmation(False, 50, pv) != [])
check("超阈值已确认放行", validate_confirmation(True, 50, pv) == [])
small = preview_cost([{"kind":"image","count":1}])
check("低于阈值免确认", validate_confirmation(False, 50, small) == [])
total=_t[0];passed=total-len(_f)
print(json.dumps({"module":"C6-confirm","total":total,"pass":passed,"fail":len(_f)},ensure_ascii=False))
sys.exit(1 if _f else 0)
