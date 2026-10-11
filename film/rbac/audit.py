"""操作审计（M16.3-F03：谁在何时触发了哪次操作，成本可归因到人，留痕不可篡改）。"""


def make_audit(who, action, target, when, why="", evidence=None):
    return {"who": who, "action": action, "target": target, "when": when,
            "why": why, "evidence": evidence or []}


def validate_audit(a):
    """审计记录不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not a.get("who"):
        v.append("缺 who")
    if not a.get("action"):
        v.append("缺 action")
    if not a.get("target"):
        v.append("缺 target")
    if not a.get("when"):
        v.append("缺 when")
    return v
