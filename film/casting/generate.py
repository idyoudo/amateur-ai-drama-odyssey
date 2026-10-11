"""M3 选角生成（实现层）：调图像适配器产出锚点图集并校验。"""
from . import anchors, character


def generate_casting(character_name, image_adapter, voice_key="v1"):
    sub = image_adapter.submit({"prompt": "为角色「%s」生成三视图锚点" % character_name})
    result = image_adapter.query(sub["task_id"])
    anchor_list = [anchors.make_anchor(v, "mock/%s_%s" % (character_name, v))
                   for v in ("front", "side", "full_body")]
    ch = character.make_character(character_name, anchor_list, voice_key=voice_key)
    violations = character.validate_character(ch)
    if violations:
        raise ValueError("生成角色卡不合规：%s" % ";".join(violations))
    checkpoint = {"produced_keys": [result.get("result", {}).get("object_key", "mock/casting")]}
    return ch, checkpoint
