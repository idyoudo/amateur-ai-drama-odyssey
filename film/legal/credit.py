"""署名与 source material（M18.2-F01/F02：AI 不得作 writer，AI 材料不计入 source material）。"""
from . import enums


def validate_credit(credit):
    """署名校验：主体类型限人类（AI 不得出现在 writer 或等效署名位）。"""
    v = []
    if credit.get("role") not in enums.CREDIT_ROLES:
        v.append("非法署名角色：%r" % (credit.get("role"),))
    if credit.get("subject_type") != "human":
        v.append("AI 不得署名：%r 主体类型为 %r" % (credit.get("name"), credit.get("subject_type")))
    return v


def validate_source_material(item):
    """AI 生成材料不得登记为 assigned/source material（WGA 口径 2）。"""
    if item.get("origin") == "ai":
        return ["AI 材料不得计入 source material：%r" % item.get("name")]
    return []
