"""音画同步验收（M7.5-F04 / B-26：工程目标 ≤±25ms；ITU 容差 +90/-185ms）。"""
from . import enums


def validate_av_offset(offset_ms):
    """AV 偏移验收（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if abs(offset_ms) > enums.SYNC_ENGINE_MS:
        v.append("偏移 %dms 超工程目标 ±%dms" % (offset_ms, enums.SYNC_ENGINE_MS))
    if offset_ms > enums.SYNC_ITU_PLUS_MS or offset_ms < enums.SYNC_ITU_MINUS_MS:
        v.append("偏移 %dms 超 ITU 容差 +%d/-%dms" % (offset_ms, enums.SYNC_ITU_PLUS_MS, -enums.SYNC_ITU_MINUS_MS))
    return v
