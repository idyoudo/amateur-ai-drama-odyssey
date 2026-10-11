#!/usr/bin/env python3
"""M8 声音契约层 · 独立复测（stem/响度/下混/可懂度/授权 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.audio import license, loudness, mix, stems

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 四层 stem ----------------
ok = [stems.make_stem("D", 300, -30), stems.make_stem("M", 300, -33),
      stems.make_stem("E", 300, -35), stems.make_stem("Amb", 300, -36)]
check("四层 stem 齐备等长", stems.validate_stems(ok) == [])
check("缺层违规", stems.validate_stems(ok[:3]) != [])
check("时长不等违规", stems.validate_stems(
    [stems.make_stem("D", 300), stems.make_stem("M", 299),
     stems.make_stem("E", 300), stems.make_stem("Amb", 300)]) != [])
check("Σ 与母版差 ≤0.1", stems.validate_stems(ok, master_lufs=stems.power_sum_lufs([-30, -33, -35, -36])) == [])
check("Σ 与母版差 >0.1 违规", stems.validate_stems(ok, master_lufs=stems.power_sum_lufs([-30, -33, -35, -36]) + 0.5) != [])

# ---------------- 响度真峰值 ----------------
check("归档合规", loudness.validate_loudness(-23.0, -1.5, "archive") == [])
check("归档响度越界", loudness.validate_loudness(-21.0, -1.5, "archive") != [])
check("归档真峰值越界", loudness.validate_loudness(-23.0, -0.5, "archive") != [])
check("广播合规", loudness.validate_loudness(-24.0, -3.0, "broadcast") == [])
check("广播真峰值违规", loudness.validate_loudness(-24.0, -1.5, "broadcast") != [])
check("流媒体合规", loudness.validate_loudness(-25.0, -3.0, "stream") == [])
check("流媒体越界", loudness.validate_loudness(-28.0, -3.0, "stream") != [])

# ---------------- 下混 ----------------
check("下混合规", mix.validate_downmix({"C": -3.0, "Ls": -3.0, "Rs": -3.0}) == [])
check("下混中置错违规", mix.validate_downmix({"C": 0.0, "Ls": -3.0, "Rs": -3.0}) != [])
check("LFE 下混违规", mix.validate_downmix({"C": -3.0, "Ls": -3.0, "Rs": -3.0, "LFE": -3.0}) != [])

# ---------------- 可懂度 ----------------
check("对白高于掩蔽 20dB 合规", mix.validate_intelligibility(-20, -40) == [])
check("对白高于掩蔽 10dB 违规", mix.validate_intelligibility(-30, -40) != [])

# ---------------- AI 音乐授权 ----------------
check("Suno pro 可商用", license.validate_music_license("suno", "pro") == [])
check("Suno free 不可商用", license.validate_music_license("suno", "free") != [])
check("Mureka free 不可商用", license.validate_music_license("mureka", "free") != [])
check("ACE-Step 可商用", license.validate_music_license("ace_step", "any") == [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M8-audio-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
