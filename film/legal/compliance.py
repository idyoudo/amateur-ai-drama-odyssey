"""交付前合规校验（M18.7-F01：权利链+工会+标识+分级+平台标签，任一项失败即拒绝）。"""


def validate_delivery_compliance(rights_ok, union_ok, label_ok, rating_ok, tag_ok):
    v = []
    if not rights_ok:
        v.append("权利链不齐备")
    if not union_ok:
        v.append("工会同意/披露不齐备")
    if not label_ok:
        v.append("AI 标识缺失")
    if not rating_ok:
        v.append("分级/披露字段缺失")
    if not tag_ok:
        v.append("平台标签缺失")
    return v
