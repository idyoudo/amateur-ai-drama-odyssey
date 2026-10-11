"""分发三重放行（M12.4-F04：母版门禁通过 + AI 标识校验 + 权利要求校验）。"""


def validate_release(master_gate_passed, ai_label_ok, rights_ok):
    v = []
    if not master_gate_passed:
        v.append("母版门禁未通过")
    if not ai_label_ok:
        v.append("AI 标识校验未通过")
    if not rights_ok:
        v.append("权利要求校验未通过")
    return v
