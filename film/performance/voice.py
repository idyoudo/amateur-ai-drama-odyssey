"""音色库与角色绑定（M7.3：音色四维+能力位 + 角色↔音色全局绑定，未绑定阻断）。"""
from . import enums


def validate_voice_meta(voice):
    """音色元数据四维完整率（M7.3-F01）。返回违规列表，空 = 合规。"""
    v = []
    for d in enums.VOICE_DIMS:
        if not voice.get(d):
            v.append("音色缺维度 %s" % d)
    return v


def validate_voice_binding(voice_key):
    """角色↔音色全局绑定（M7.3-F02）：未绑定即阻断出片，禁止隐式分配。"""
    if not voice_key:
        return ["角色未绑定音色，阻断出片（M7.3-F02）"]
    return []
