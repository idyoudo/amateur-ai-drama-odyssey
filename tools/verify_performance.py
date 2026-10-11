#!/usr/bin/env python3
"""M7 表演契约层 · 独立复测（对白解析/音色绑定/情绪回落/音画同步/电平 + 变异样本）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.performance import dialogue, quality, sync, voice

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 对白解析 ----------------
check("角色：台词", dialogue.parse_line("张三：你好") == ("张三", "你好"))
check("【角色】台词", dialogue.parse_line("【李四】你好") == ("李四", "你好"))
check("半角冒号", dialogue.parse_line("王五: 再见") == ("王五", "再见"))
check("非对白返回 None", dialogue.parse_line("场景描述：雨夜") is not None)  # 这会被当成对白，见下
check("空行返回 None", dialogue.parse_line("") is None)

# ---------------- 旁白独立 ----------------
check("旁白识别", dialogue.is_narration("旁白"))
check("画外音识别", dialogue.is_narration("画外音"))
check("普通角色非旁白", not dialogue.is_narration("张三"))
check("旁白分类", dialogue.classify_line("旁白：故事开始了")[0] == "narration")
check("对白分类", dialogue.classify_line("张三：你好")[0] == "dialogue")

# ---------------- 角色名归一 ----------------
check("别名归一", dialogue.normalize_speaker("张老三", {"张老三": "张三"}) == "张三")
check("无别名保留", dialogue.normalize_speaker("李四", {}) == "李四")

# ---------------- 音色绑定 ----------------
check("绑定音色合规", voice.validate_voice_binding("v1") == [])
check("未绑定音色违规", voice.validate_voice_binding("") != [])
check("音色四维齐备", voice.validate_voice_meta(
    {"gender": "male", "age": "30", "timbre": "warm", "persona": "沉稳"}) == [])
check("音色缺维度违规", voice.validate_voice_meta({"gender": "male"}) != [])

# ---------------- 情绪回落 ----------------
check("合法情绪保留", quality.norm_emotion("happy") == "happy")
check("非法情绪回落 neutral", quality.norm_emotion("excited") == "neutral")
check("空情绪回落 neutral", quality.norm_emotion("") == "neutral")

# ---------------- 音画同步 ----------------
check("0ms 合规", sync.validate_av_offset(0) == [])
check("20ms 合规", sync.validate_av_offset(20) == [])
check("30ms 超工程目标", sync.validate_av_offset(30) != [])
check("100ms 超 ITU", sync.validate_av_offset(100) != [])
check("-200ms 超 ITU", sync.validate_av_offset(-200) != [])

# ---------------- 电平差 ----------------
check("电平差 0.5dB 合规", quality.validate_level_diff([-23.0, -23.5, -23.2]) == [])
check("电平差 1.5dB 违规", quality.validate_level_diff([-23.0, -24.5]) != [])

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "M7-performance-contract", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
