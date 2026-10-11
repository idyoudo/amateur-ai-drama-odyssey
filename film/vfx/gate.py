"""VFX 门禁与工具许可（M19.6-F03/F04）。"""
from film.suppliers import license as supplier_license


def validate_vfx_gate(shot):
    """需 VFX 的镜头必须完成修复并通过检查才可进成片。"""
    if shot.get("requires_vfx") and not shot.get("vfx_done"):
        return ["未完成 VFX 的镜头进入成片（M19.6-F03）"]
    return []


def validate_tool_license(component):
    """合成/修复工具许可检查（GPL 传染风险不得内置分发，C-18/C-19）。"""
    return supplier_license.validate_bundle(component)
