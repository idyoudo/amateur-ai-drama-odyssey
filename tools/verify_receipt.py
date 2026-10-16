#!/usr/bin/env python3
"""C7 发布锁定 + 签名收据 · 独立复测。"""
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(HERE);sys.path.insert(0,ROOT)
from film.delivery.receipt import make_receipt, sign_receipt, validate_receipt, manifest
_t=[0];_f=[]
def check(n,c):
    _t[0]+=1
    if not c:_f.append(n)
arts=[{"name":"master.mov","sha256":"a"*64},{"name":"poster.png","sha256":"b"*64}]
m=manifest(arts)
check("清单 2 项", m["count"]==2)
check("清单确定性（排序）", manifest(list(reversed(arts)))["manifest_sha256"]==m["manifest_sha256"])
r=make_receipt("回声","v1","2.39:1",arts,"admin","pass_with_condition","2026-10-16")
check("未签名时校验提示未签名", any("未签名" in v for v in validate_receipt(r, "sk")))
r["signature"]=sign_receipt(r,"sk")
check("签名后合规", validate_receipt(r,"sk")==[])
check("release_lock 标记", r["release_lock"] is True)
r2=dict(r); r2["version"]="v2"
check("篡改被检出", validate_receipt(r2,"sk") != [])
check("错误密钥被检出", any("篡改" in v for v in validate_receipt(r,"other")))
total=_t[0];passed=total-len(_f)
print(json.dumps({"module":"C7-receipt","total":total,"pass":passed,"fail":len(_f)},ensure_ascii=False))
sys.exit(1 if _f else 0)
