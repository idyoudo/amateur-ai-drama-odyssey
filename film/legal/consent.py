"""同意记录与数字替身（M18.2-F03 / M18.3-F01：使用需同意，数字替身需书面同意+补偿+范围）。"""


def validate_consent(record):
    """AI 辅助需同意记录（谁、何时、范围）。"""
    v = []
    for field in ("who", "when", "scope"):
        if not record.get(field):
            v.append("缺同意字段 %s" % field)
    return v


def validate_digital_double(record):
    """数字替身需书面同意 + 补偿约定 + 使用范围（缺失即禁止生成）。"""
    v = []
    for field in ("consent", "compensation", "scope"):
        if not record.get(field):
            v.append("缺数字替身字段 %s" % field)
    return v
