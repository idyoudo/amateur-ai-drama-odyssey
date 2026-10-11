"""镜头级不变量（同框角色上限 M6.2-F05）。"""
from . import enums


def validate_shot_characters(character_ids):
    """单镜同框角色硬上限 3（A-07）。返回违规列表，空 = 合规。"""
    n = len(character_ids)
    if n > enums.MAX_SAME_FRAME_CHARACTERS:
        return ["同框角色超上限：%d > %d" % (n, enums.MAX_SAME_FRAME_CHARACTERS)]
    return []
