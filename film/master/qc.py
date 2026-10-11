"""平台拒收项（M11.5-F06 / B-40）与母版门禁（M11.6-F01，复用 film.rbac.gates）。"""
from film.rbac import gates as rbac_gates


def validate_platform_rejects(hardcoded_subtitle=False, upmix_audio=False,
                              letterbox=False, has_promotion=False):
    """平台拒收项硬规则检查（命中即拒收）。"""
    v = []
    if hardcoded_subtitle:
        v.append("硬字幕属平台拒收项")
    if upmix_audio:
        v.append("上混音频属平台拒收项")
    if letterbox:
        v.append("16:9 letterbox 属拒收项（须原始画幅）")
    if has_promotion:
        v.append("含广告/宣传/网址呼出属拒收项")
    return v


def validate_master_gate(gate):
    """母版门禁（五门禁最后一关）：署名 + 理由码 + 岗位权限。"""
    v = []
    if not gate.get("approver"):
        v.append("未署名（M11.6-F01）")
    v += rbac_gates.validate_sign_off("master", gate.get("approver_position"),
                                      gate.get("doer_position"))
    if gate.get("reason_code") not in rbac_gates.REASON_CODES:
        v.append("理由码非法：%r" % (gate.get("reason_code"),))
    return v
