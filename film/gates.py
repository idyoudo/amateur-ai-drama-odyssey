"""分镜门禁收据（切片 A · M10.3-F01~F04 / M16.2-F03~F06 / NFR-14 的字段契约层）。

⚠️ 能力边界（必须显式声明，禁止冒充）：
本模块只落地**门禁记录的字段契约与不变量校验**，不含状态机、权限、SLA 与人工终审。
approver 一律写 `PENDING-HUMAN-SIGNATURE`，**绝不冒充真人署名**（D6：无署名即视为未通过）。
"""

GATE_NODES = {
    "script": "剧本门禁",
    "casting": "定妆门禁",
    "board": "分镜门禁",
    "picture": "成片门禁",
    "master": "母版门禁",
}

PLACEHOLDER_APPROVER = "PENDING-HUMAN-SIGNATURE"


def make_receipt(node, decision, reason_code, checklist, ai_recommendation,
                 ai_overridden=False, override_reason="", written_reason="",
                 approver=PLACEHOLDER_APPROVER, role="", timestamp="", evidence=None):
    """构造门禁收据（字段齐备性由 validate_receipt 校验）。"""
    return {
        "gate_node": node,
        "gate_label": GATE_NODES.get(node, node),
        "decision": decision,               # pass / pass_with_condition / reject / pending
        "approver": approver,
        "role": role,
        "timestamp": timestamp,
        "reason_code": reason_code,
        "binary_checklist": checklist,      # 二元化验收清单（M10.3-F03）
        "ai_recommendation": ai_recommendation,
        "ai_overridden": bool(ai_overridden),
        "override_reason": override_reason,
        "written_reason": written_reason,
        "evidence": evidence or [],
        "capability_note": "本切片仅实现门禁**记录字段契约**；状态机、权限、SLA 与人工终审不在范围内。"
                           "approver 为占位符时不构成 D6 意义上的通过。",
    }


def validate_receipt(receipt):
    """不变量校验（fail-closed）。返回违规列表，空列表 = 合规。"""
    v = []
    if not receipt.get("gate_node"):
        v.append("缺 gate_node")
    if not receipt.get("reason_code"):
        v.append("缺 reason_code（D6：通过/驳回必须带理由码）")
    signed = receipt.get("approver") not in (PLACEHOLDER_APPROVER, "", None)
    if signed:
        if not receipt.get("timestamp"):
            v.append("已署名但缺 timestamp")
    elif receipt.get("timestamp"):
        v.append("未署名却带 timestamp（时间戳只能由人工终审产生）")
    if not receipt.get("binary_checklist"):
        v.append("缺二元化验收清单（M10.3-F03）")
    if receipt.get("ai_overridden") and not receipt.get("override_reason"):
        v.append("AI 异议被覆盖但无覆盖理由（D6/EL-10：不得静默覆盖）")
    if receipt.get("decision") == "pass" and not receipt.get("written_reason"):
        v.append("『零缺陷通过』未附书面理由（D6 缓解措施 2）")
    if receipt.get("decision") in ("pass", "pass_with_condition") and \
            receipt.get("approver") == PLACEHOLDER_APPROVER:
        v.append("无人工署名却给出通过结论（D6：无署名即视为未通过）")
    return v


def checklist(items):
    """items: [(item, expected, measured), ...] → 二元清单（每项二值判定）。"""
    out = []
    for item, expected, measured in items:
        out.append({
            "item": item,
            "expected": expected,
            "measured": measured,
            "pass": bool(measured == expected) if not isinstance(expected, bool) else bool(measured is expected),
            "binary": True,
        })
    return out
