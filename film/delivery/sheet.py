"""交付单（M12.1-F08：字段齐备 + 可选交付显式标注 保证/可选/需确认）。"""
from . import enums

REQUIRED_FIELDS = ("spec", "version", "duration", "qc_conclusion", "rights_status",
                   "ai_label", "rating", "language", "color_tag")


def validate_delivery_sheet(sheet):
    v = []
    for field in REQUIRED_FIELDS:
        if not sheet.get(field):
            v.append("缺交付单字段 %s" % field)
    for item in sheet.get("optional_items", []):
        if item.get("status") not in enums.DELIVERY_STATUS:
            v.append("可选交付未标注保证/可选/需确认：%r" % (item,))
    return v
