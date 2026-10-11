"""角色卡与不变量（音色绑定 M3.7-F01 / 授权先于生成 M3.5-F02）。"""
from . import anchors


def make_character(name, anchor_list, voice_key=None, uses_real_likeness=False,
                   consent=None, voice_capabilities=None):
    return {
        "name": name,
        "anchors": anchor_list,
        "voice_key": voice_key,
        "uses_real_likeness": uses_real_likeness,
        "consent": consent,          # 数字替身/肖像授权记录（M3.5-F01）
        "voice_capabilities": voice_capabilities or [],
    }


def validate_character(ch):
    """角色卡不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not ch.get("name"):
        v.append("缺角色名")
    v += anchors.validate_anchors(ch.get("anchors", []))
    if not ch.get("voice_key"):
        v.append("角色未绑定音色（M3.7-F01：未绑定即阻断出片）")
    if ch.get("uses_real_likeness") and not ch.get("consent"):
        v.append("使用真人形象但无授权记录（M3.5-F02：未授权不得生成）")
    return v
