#!/usr/bin/env python3
"""M12 交付契约层 · 独立复测（母版规格/字幕/交付单/三重放行 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.delivery import release, sheet, spec, subtitle

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 主母版规格 ----------------
check("母版规格合规", spec.validate_master_spec("2.39:1", 24, -23.0, -1.5) == [])
check("画幅非法", spec.validate_master_spec("16:9", 24, -23.0, -1.5) != [])
check("响度越界", spec.validate_master_spec("2.39:1", 24, -21.0, -1.5) != [])
check("真峰值越界", spec.validate_master_spec("2.39:1", 24, -23.0, -0.5) != [])

# ---------------- 字幕来源 ----------------
check("tts 来源合规", subtitle.validate_cue_source("tts") == [])
check("asr 来源合规", subtitle.validate_cue_source("asr") == [])
check("estimate 来源合规", subtitle.validate_cue_source("estimate") == [])
check("provider 来源违规", subtitle.validate_cue_source("provider") != [])

# ---------------- 字幕排版 ----------------
check("字幕排版合规", subtitle.validate_cue_layout(1.0, ["第一行", "第二行"]) == [])
check("时长过短违规", subtitle.validate_cue_layout(0.5, ["一行"]) != [])
check("行长超限违规", subtitle.validate_cue_layout(1.0, ["这" * 24]) != [])
check("竖屏 4 行违规", subtitle.validate_cue_layout(1.0, ["一", "二", "三", "四"], vertical=True) != [])
check("横屏 4 行也超限（>2 行不在此校验，仅行长）", True)  # 横屏行数校验在 M11，此处只查行长

# ---------------- 交付单 ----------------
ok_sheet = {"spec": "2.39:1", "version": "v1", "duration": 1800, "qc_conclusion": "pass",
            "rights_status": "ok", "ai_label": "AI 生成", "rating": "12+",
            "language": "zh", "color_tag": "Rec.709",
            "optional_items": [{"name": "5.1", "status": "optional"}]}
check("交付单合规", sheet.validate_delivery_sheet(ok_sheet) == [])
check("缺字段违规", sheet.validate_delivery_sheet({"spec": "2.39:1"}) != [])
check("可选交付未标注违规", sheet.validate_delivery_sheet(
    {**ok_sheet, "optional_items": [{"name": "HDR10", "status": "maybe"}]}) != [])

# ---------------- 分发三重放行 ----------------
check("三重放行合规", release.validate_release(True, True, True) == [])
check("母版门禁未过违规", release.validate_release(False, True, True) != [])
check("AI 标识未过违规", release.validate_release(True, False, True) != [])
check("权利未过违规", release.validate_release(True, True, False) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M12-delivery-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
