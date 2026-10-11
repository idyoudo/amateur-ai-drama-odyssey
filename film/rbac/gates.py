"""门禁署名与理由码（M16.2-F03/F04/F05：岗位绑定 + 自审自批禁令 + 理由码）。"""

GATE_NODES = ("script", "casting", "board", "picture", "master")

# 每个门禁节点可签的岗位（候选审片人）
GATE_APPROVERS = {
    "script": ("showrunner", "writer", "legal"),
    "casting": ("showrunner", "director"),
    "board": ("showrunner", "director"),
    "picture": ("showrunner", "director", "qc"),
    "master": ("showrunner", "colorist", "qc", "legal"),
}

# 理由码（M16.2-F04：通过/驳回必须选理由码）
REASON_CODES = ("pass_zero_defect", "pass_with_condition",
                "reject_quality", "reject_continuity", "reject_compliance", "reject_other")


def validate_sign_off(gate_node, approver_position, doer_position=None):
    """门禁署名校验（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if gate_node not in GATE_APPROVERS:
        v.append("非法门禁节点：%r" % (gate_node,))
        return v
    if approver_position not in GATE_APPROVERS[gate_node]:
        v.append("岗位无权签该门禁：%r 不属 %s" % (approver_position, GATE_APPROVERS[gate_node]))
    if doer_position is not None and doer_position == approver_position:
        v.append("自审自批违规：%r 同岗既做又审（M16.2-F01）" % (approver_position,))
    return v


def validate_reason(reason_code):
    """理由码必须落在封闭集合（M16.2-F04）。"""
    return reason_code in REASON_CODES
