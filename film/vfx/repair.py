"""修复优先级决策（M19.1-F04 / E-35：局部修复优先于整镜重抽）。"""
from . import enums


def repair_priority(defect_severity):
    """轻微→局部修复；中度→局部重生成；重度→整镜重抽。"""
    if defect_severity == "minor":
        return "local_repair"
    if defect_severity == "moderate":
        return "local_regen"
    return "full_resample"
