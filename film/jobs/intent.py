"""intent log（M13.4-F05：调用供应商前先落盘，超时置 unknown 进对账，已提交绝不重投）。"""
from .state_machine import StateError

INTENT_STATUS = ("intended", "submitted", "unknown", "resolved")

# intended → submitted(成功) / unknown(超时/异常)；unknown → resolved(对账)；submitted 终态
INTENT_TRANSITIONS = {
    "intended": ("submitted", "unknown"),
    "submitted": (),
    "unknown": ("resolved",),
    "resolved": (),
}


def make_intent(job_id, provider, fingerprint, client_op_id, request_id, payload_frozen):
    return {
        "job_id": job_id,
        "provider": provider,
        "fingerprint": fingerprint,
        "client_op_id": client_op_id,
        "request_id": request_id,
        "payload_frozen": payload_frozen,
        "status": "intended",
    }


def validate_intent(it):
    v = []
    if not it.get("job_id"):
        v.append("缺 job_id")
    if not it.get("provider"):
        v.append("缺 provider")
    if not it.get("fingerprint"):
        v.append("缺 fingerprint")
    if not it.get("request_id"):
        v.append("缺 request_id（对账查询入口）")
    if it.get("status") not in INTENT_STATUS:
        v.append("status 非法：%r" % (it.get("status"),))
    return v


def require_intent_transition(src, dst):
    if dst not in INTENT_TRANSITIONS.get(src, ()):
        raise StateError("非法 intent 转移：%r -> %r（已提交后禁止重投）" % (src, dst))
    return dst
