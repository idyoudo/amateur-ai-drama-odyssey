"""按镜头重要性路由与降级（M17.3-F01/F02）。"""
from . import enums


def route_model(importance, premium, economy):
    """关键镜头（hero/对白正脸）用高质量模型；氛围/过场用经济模型（E-18）。"""
    if importance in ("hero", "dialogue_closeup"):
        return premium
    return economy


def degrade_tier(tier):
    """供应商故障/限流时沿降级链切换（premium→standard→economy→None）。"""
    chain = enums.MODEL_TIER_CHAIN
    if tier not in chain:
        return None
    i = chain.index(tier)
    return chain[i + 1] if i + 1 < len(chain) else None
