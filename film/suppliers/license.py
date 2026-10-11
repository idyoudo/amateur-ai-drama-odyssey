"""自托管与许可合规（M17.4-F02/F03：GPL/非商用风险清单）。"""
from . import enums


def validate_bundle(component):
    """不得内置分发清单（GPL-3.0 / 非 OSI 许可）。"""
    if component in enums.FORBIDDEN_BUNDLE:
        return ["%s 不得内置分发，仅允许自建外部服务或云 API 接入" % component]
    return []


def validate_insightface(component, commercial_use):
    """InsightFace 系仅限非商业研究（D-34）；商用链路禁止直接依赖。"""
    c = (component or "").lower()
    if "insightface" in c or "arcface" in c or "inswapper" in c:
        if commercial_use:
            return ["%s 仅限非商业研究，商用须另行授权或替换" % component]
    return []
