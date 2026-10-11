"""单位可交付母版成本（M14.1-F01 / M14.7-F01：北极星口径）。"""


def unit_master_cost(total_cost, deliverable_minutes):
    """总成本 ÷ 可交付母版分钟数（未过门禁/QC 的分钟不计入分母）。"""
    if deliverable_minutes <= 0:
        return None
    return total_cost / deliverable_minutes


def master_minutes_per_cost(total_cost, deliverable_minutes):
    """北极星：可交付母版分钟数 / 总成本（每元产出多少分钟能过门禁的成片）。"""
    if total_cost <= 0:
        return None
    return deliverable_minutes / total_cost
