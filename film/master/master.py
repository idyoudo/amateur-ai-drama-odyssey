"""母版规格校验（M11.3：编码/音频/TC/头尾黑场）。"""
from . import enums


def validate_master_spec(codec, audio_bit_depth, sample_rate, has_tc):
    """归档母版规格（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if codec not in enums.MASTER_CODECS:
        v.append("母版编码非法：%r（应 %s）" % (codec, "/".join(enums.MASTER_CODECS)))
    if audio_bit_depth != enums.MASTER_BIT_DEPTH:
        v.append("音频位深 %d 应为 24-bit" % audio_bit_depth)
    if sample_rate != enums.MASTER_SAMPLE_RATE:
        v.append("采样率 %d 应为 48kHz" % sample_rate)
    if not has_tc:
        v.append("缺时间码嵌入（TC 起点 %s）" % enums.TC_START)
    return v


def validate_black_frames(head_frames, tail_frames, fps=24):
    """头尾黑场 ≥1 帧且 ≤1 s（B-37）。"""
    v = []
    for name, frames in (("头", head_frames), ("尾", tail_frames)):
        if frames < 1:
            v.append("%s黑场 <1 帧" % name)
        elif frames > fps:
            v.append("%s黑场 %d 帧 >1s(%d 帧)" % (name, frames, fps))
    return v
