"""任务检查点（M13.6-F01：记录已完成产物对象键、指纹、lease_epoch）。"""


def make_checkpoint(produced_keys, fingerprint, lease_epoch, stage_segments=None):
    return {
        "produced_keys": produced_keys or [],   # 已完成产物对象键（content-addressed）
        "fingerprint": fingerprint,
        "lease_epoch": lease_epoch,
        "stage_segments": stage_segments or [],  # 长任务按阶段分段落盘（M13.6-F01）
    }


def validate_checkpoint(cp):
    """不变量校验（fail-closed）。返回违规列表，空列表 = 合规。"""
    v = []
    if not isinstance(cp, dict):
        return ["checkpoint 必须是对象"]
    if not isinstance(cp.get("produced_keys"), list):
        v.append("produced_keys 必须是列表")
    if not cp.get("fingerprint"):
        v.append("缺 fingerprint（续跑判定依据）")
    epoch = cp.get("lease_epoch")
    if not isinstance(epoch, int) or epoch < 1:
        v.append("lease_epoch 必须是 ≥1 的整数（fencing）")
    for k in cp.get("produced_keys", []):
        if not isinstance(k, str) or not k:
            v.append("produced_keys 含非法键：%r" % (k,))
    return v
