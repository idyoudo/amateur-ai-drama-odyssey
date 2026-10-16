"""生成前成本确认闸（C6，源自 Nomi 最佳实践 / DramaClaw review 环）。

预演确认：花额度前把「即将生成的付费镜头」逐条摊开、给单价与合计，
经人工/批量点头才执行；与 M14 超预算熔断（事后）形成事前+事中双层。
"""

# 单位成本锚点（元；用于预估，实际以供应商账单为准）
UNIT_COST = {"image": 0.5, "video": 8.0, "tts": 0.2, "music": 2.0, "lipsync": 20.0}


def preview_cost(items):
    """items: [{kind, count, seconds?}] → 逐项预估 + 合计。

    video/lipsync 按秒（seconds）计；image/tts/music 按次。
    """
    rows = []
    total = 0.0
    for it in items:
        kind = it.get("kind")
        unit = UNIT_COST.get(kind, 0)
        if kind in ("video", "lipsync"):
            cost = unit * float(it.get("seconds", 0))
        else:
            cost = unit * int(it.get("count", 0))
        rows.append({"kind": kind, "count": it.get("count"), "seconds": it.get("seconds"),
                     "unit_cost": unit, "cost_cny": round(cost, 2)})
        total += cost
    return {"items": rows, "total_cny": round(total, 2),
            "requires_confirmation": any(r["cost_cny"] > 0 for r in rows)}


def validate_confirmation(confirmed, threshold_cny=50.0, preview=None):
    """确认闸：合计超阈值须显式确认，否则拒绝执行（fail-closed）。"""
    v = []
    total = (preview or {}).get("total_cny", 0)
    if total > threshold_cny and not confirmed:
        v.append("预估 ¥%.2f 超阈值 ¥%.2f，须显式确认后才执行" % (total, threshold_cny))
    return v
