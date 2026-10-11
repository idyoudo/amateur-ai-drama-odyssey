"""定妆门禁（M3.3-F02：署名审批人 + 理由码 + 通过即锁定）。复用 film.rbac.gates 的署名与理由码。"""
from film.rbac import gates as rbac_gates


def validate_casting_gate(gate):
    """定妆门禁不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not gate.get("approver"):
        v.append("未署名（M3.3-F02：无署名即视为未通过）")
    v += rbac_gates.validate_sign_off("casting", gate.get("approver_position"),
                                      gate.get("doer_position"))
    if gate.get("reason_code") not in rbac_gates.REASON_CODES:
        v.append("理由码非法：%r" % (gate.get("reason_code"),))
    if gate.get("decision") == "approve" and not gate.get("locked"):
        v.append("通过但未锁定角色形象（M3.3-F02）")
    return v
