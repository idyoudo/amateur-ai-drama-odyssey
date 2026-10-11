#!/usr/bin/env python3
"""M15 存储契约层 · 独立复测（对象键/母版唯一/派生谱系/内容寻址 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.storage import assets, enums, keys, lineage

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 对象键 ----------------
k = keys.make_object_key("u1", "p1", 1, 2, "shot_video", 3, "mp4")
check("对象键合规", keys.validate_object_key(k) == [])
check("对象键含版本 v3", "/v3." in k)
check("绝对路径拒绝", keys.validate_object_key("/users/x") != [])
check("越界 .. 拒绝", keys.validate_object_key("users/../x") != [])
check("空键拒绝", keys.validate_object_key("") != [])
check("非法模式拒绝", keys.validate_object_key("foo/bar.mp4") != [])

# ---------------- 内容寻址 ----------------
a = assets.make_asset("p1", 1, 1, "video", "users/u/dramas/p/ep1/shot1/shot_video/v1.mp4", data=b"abc")
b = assets.make_asset("p1", 1, 1, "video", "users/u/dramas/p/ep1/shot1/shot_video/v2.mp4", data=b"abc")
check("内容哈希确定（同数据同哈希）", a["checksum_sha256"] == b["checksum_sha256"])
check("内容哈希 64 hex", len(a["checksum_sha256"]) == 64)

# ---------------- 母版唯一 ----------------
gen = assets.make_asset("p1", 1, 1, "master", "users/u/dramas/p/ep1/shot1/master/v1.mov", data=b"x", spec=enums.GENERATION_MASTER_SPEC)
gen["id"] = 1
arc = assets.make_asset("p1", 1, 1, "master", "users/u/dramas/p/ep1/shot1/master/v2.mov", data=b"y", spec=enums.ARCHIVE_MASTER_SPEC)
arc["id"] = 2
check("单母版族合规", lineage.validate_family([gen, arc]) == [])
gen2 = dict(gen)
gen2["id"] = 3
check("双生成母版违规", lineage.validate_family([gen, gen2, arc]) != [])

# ---------------- 派生谱系 ----------------
d = assets.make_asset("p1", 1, 1, "derived", "users/u/dramas/p/ep1/shot1/derive/v1.mp4", data=b"z", parent_asset_id=1, spec="9:16")
check("派生指向母版合规", lineage.validate_family([gen, arc, d]) == [])
d2 = assets.make_asset("p1", 1, 1, "derived", "users/u/dramas/p/ep1/shot1/derive/v2.mp4", data=b"z", parent_asset_id=999, spec="9:16")
check("派生父级不存在违规", lineage.validate_family([gen, arc, d2]) != [])
d3 = assets.make_asset("p1", 1, 1, "derived", "users/u/dramas/p/ep1/shot1/derive/v3.mp4", data=b"z", parent_asset_id=1, spec="9:16")
d3["spec"] = "bogus"
check("派生 spec 非法违规", lineage.validate_family([gen, arc, d3]) != [])

# ---------------- spec 封闭 ----------------
try:
    assets.make_asset("p1", 1, 1, "derived", "users/u/dramas/p/ep1/shot1/derive/v4.mp4", data=b"z", spec="bogus")
    check("make_asset 非法 spec 抛错", False)
except ValueError:
    check("make_asset 非法 spec 抛错", True)
try:
    assets.make_asset("p1", 1, 1, "bogus_kind", "users/u/dramas/p/ep1/shot1/x/v1.bin", data=b"z")
    check("make_asset 非法 kind 抛错", False)
except ValueError:
    check("make_asset 非法 kind 抛错", True)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M15-storage-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
