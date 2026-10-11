"""混音与可懂度（M8.1-F03 下混纪律 + M8.4-F01 对白高于掩蔽 ≥15 dB）。"""
from . import enums


def validate_downmix(channel_gains):
    """下混纪律：中置/环绕各 −3 dB；LFE 不得下混（关键内容不得只放 LFE）。"""
    v = []
    for ch, expected in enums.DOWMIX_DB.items():
        if channel_gains.get(ch) != expected:
            v.append("声道 %s 下混应 %s dB，实际 %s" % (ch, expected, channel_gains.get(ch)))
    if channel_gains.get("LFE") is not None:
        v.append("LFE 不得下混")
    return v


def validate_intelligibility(dialogue_lufs, mask_lufs):
    """对白高于稳态掩蔽 ≥15 dB（B-24：−15 dB 时可懂度为零，作硬下限）。"""
    v = []
    diff = dialogue_lufs - mask_lufs
    if diff < enums.INTELLIGIBILITY_MIN_DB:
        v.append("对白高于掩蔽 %.1f dB < %.1f dB" % (diff, enums.INTELLIGIBILITY_MIN_DB))
    return v
