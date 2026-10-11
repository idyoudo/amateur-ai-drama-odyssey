"""VFX 需求标注与物理骨架通道判定（M19.1-F01/F03）。"""
from . import enums


def validate_vfx_type(vfx_type):
    if vfx_type not in enums.VFX_TYPES:
        return ["非法 VFX 类型：%r（允许 %s）" % (vfx_type, enums.VFX_TYPES)]
    return []


def require_skeleton(shot):
    """高动态/负重/碰撞镜头必须走「物理骨架 + AI 渲染」通道（覆盖率 100%）。"""
    trigger = shot.get("physics_trigger")
    if trigger in enums.PHYSICS_TRIGGERS and not shot.get("has_skeleton"):
        return ["%s 镜头必须走物理骨架通道" % trigger]
    return []
