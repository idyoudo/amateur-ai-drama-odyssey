#!/usr/bin/env python3
"""C1 四层记忆 + C2 因果链 · 独立复测。"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from film import memory as mem
_t=[0];_f=[]
def check(n,c):
    _t[0]+=1
    if not c:_f.append(n)

m = mem.make_memory()
check("初始四层齐备", mem.validate_memory(m) == [])
ol1={"form":"half_hour","scenes":[{"event":"开场"},{"event":"命案"}]}
m=mem.update_memory(m,1,ol1,keywords=["回声","调音师"])
check("更新后仍合规", mem.validate_memory(m) == [])
check("全局快照含集号", m["global_snapshot"]["episode"] == 1)
check("上集结尾有内容", "命案" in m["prev_tail"])
ol2={"form":"half_hour","scenes":[{"event":"线索浮现"}]}
m=mem.update_memory(m,2,ol2,keywords=["失忆"])
check("上集结尾入更早摘要", any("命案" in x for x in m["earlier_digest"]))
check("关键词去重累积", "回声" in m["keyword_ledger"] and "失忆" in m["keyword_ledger"])
ctx = mem.assemble_context(m)
check("上下文含四层标题", all(k in ctx for k in ("全局状态","上一集结尾","更早摘要","关键词账本")))
# 硬上限
m2 = mem.make_memory()
for i in range(1, 20):
    m2 = mem.update_memory(m2, i, {"form":"half_hour","scenes":[{"event":"e%d"%i}]}, keywords=["k%d"%i])
check("更早摘要不超上限", len(m2["earlier_digest"]) <= mem.LAYER_LIMITS["earlier_digest"])
check("关键词不超上限", len(m2["keyword_ledger"]) <= mem.LAYER_LIMITS["keyword_ledger"])
check("超上限整体仍合规", mem.validate_memory(m2) == [])
# C2
r = mem.make_change_record(1,"触发","过程","结果")
check("因果链齐备合规", mem.validate_change_record(r) == [])
check("缺结果违规", mem.validate_change_record(mem.make_change_record(1,"a","b","")) != [])
iss = mem.audit_change_records([r, mem.make_change_record(5,"a","b","")])
check("断链被检出", any(i["issue"].startswith("场号断链") for i in iss))
check("未闭合被检出", any(i["issue"]=="结果未闭合" for i in iss))

total=_t[0];passed=total-len(_f)
print(json.dumps({"module":"C1C2-memory","total":total,"pass":passed,"fail":len(_f)},ensure_ascii=False))
sys.exit(1 if _f else 0)
