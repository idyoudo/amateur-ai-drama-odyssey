"""电影参数能力矩阵与校验（M17.1-F04/F07：提交前校验模型是否支持该任务）。"""


def make_model(name, kind, capabilities=None):
    return {"name": name, "kind": kind, "capabilities": capabilities or {}}


def supports(model, capability):
    """能力位读取：参数缺失不得默认「支持」。"""
    return bool(model.get("capabilities", {}).get(capability))


def validate_task(model, required_capabilities):
    """能力矩阵校验（fail-closed）：缺任一必需能力即失败并给出可读原因。"""
    v = []
    for cap in required_capabilities:
        if not supports(model, cap):
            v.append("模型 %s 不支持 %s" % (model["name"], cap))
    return v
