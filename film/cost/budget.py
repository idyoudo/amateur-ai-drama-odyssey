"""四级预算与硬阻断（M14.2：预占-结算、分级预警、超预算硬阻断）。"""
from . import enums


def make_budget(level, cap):
    return {"level": level, "cap": cap, "reserved": 0.0, "consumed": 0.0}


def reserve(budget, amount):
    """额度预占（调用前按估算预占，E-17）。超预算返回 False。"""
    if budget["reserved"] + budget["consumed"] + amount > budget["cap"]:
        return False
    budget["reserved"] += amount
    return True


def settle(budget, actual):
    """结算（完成后按实际结算差额并回滚剩余预占，E-17）。"""
    budget["reserved"] = 0.0
    budget["consumed"] += actual
    return budget["consumed"] > budget["cap"]


def warn_level(budget):
    """分级预警（M14.2-F01）：50%/80%/100%。"""
    if budget["cap"] <= 0:
        return "blocked"
    usage = (budget["reserved"] + budget["consumed"]) / budget["cap"]
    if usage >= enums.WARN_THRESHOLDS["blocked"]:
        return "blocked"
    if usage >= enums.WARN_THRESHOLDS["warn_80"]:
        return "warn_80"
    if usage >= enums.WARN_THRESHOLDS["warn_50"]:
        return "warn_50"
    return "ok"
