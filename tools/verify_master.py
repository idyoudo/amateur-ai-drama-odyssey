#!/usr/bin/env python3
"""M11 母版 QC 契约层 · 独立复测（色偏/母版规格/字幕/拒收项/门禁 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.master import color, master, qc, subtitle

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 色偏阈值 ----------------
check("ΔE 合规", color.validate_color_delta(2.0, 1.5) == [])
check("镜头间 ΔE 超限", color.validate_color_delta(3.5, 1.5) != [])
check("肤色 ΔE 超限", color.validate_color_delta(2.0, 2.5) != [])

# ---------------- 母版规格 ----------------
check("母版规格合规", master.validate_master_spec("ProRes 422 HQ", 24, 48000, True) == [])
check("编码非法", master.validate_master_spec("H.264", 24, 48000, True) != [])
check("位深非法", master.validate_master_spec("ProRes 422 HQ", 16, 48000, True) != [])
check("缺 TC", master.validate_master_spec("ProRes 422 HQ", 24, 48000, False) != [])

# ---------------- 头尾黑场 ----------------
check("黑场合规", master.validate_black_frames(10, 10) == [])
check("黑场 0 帧违规", master.validate_black_frames(0, 10) != [])
check("黑场超 1s 违规", master.validate_black_frames(30, 10) != [])

# ---------------- 字幕合规 ----------------
check("字幕合规", subtitle.validate_subtitle(6.0, ["第一行", "第二行"]) == [])
check("字幕时长越界", subtitle.validate_subtitle(8.0, ["一行"]) != [])
check("字幕行数超限", subtitle.validate_subtitle(6.0, ["一", "二", "三"]) != [])
check("字幕行长超限", subtitle.validate_subtitle(6.0, ["这" * 24]) != [])

# ---------------- 平台拒收项 ----------------
check("无拒收项合规", qc.validate_platform_rejects() == [])
check("硬字幕拒收", qc.validate_platform_rejects(hardcoded_subtitle=True) != [])
check("上混拒收", qc.validate_platform_rejects(upmix_audio=True) != [])
check("letterbox 拒收", qc.validate_platform_rejects(letterbox=True) != [])

# ---------------- 母版门禁 ----------------
g = {"approver": "张三", "approver_position": "showrunner", "doer_position": "colorist",
     "reason_code": "pass_with_condition"}
check("母版门禁合规", qc.validate_master_gate(g) == [])
check("母版未署名违规", qc.validate_master_gate({**g, "approver": ""}) != [])
check("母版自审自批违规", qc.validate_master_gate({**g, "approver_position": "colorist"}) != [])
check("母版理由码非法", qc.validate_master_gate({**g, "reason_code": "随便"}) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M11-master-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
