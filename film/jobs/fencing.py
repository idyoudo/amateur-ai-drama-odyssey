"""租约 fencing（M13.4-F04：lease_epoch 单调递增，所有产物写入校验 epoch）。"""


def next_epoch(prev):
    """领取任务时发放单调递增 lease_epoch。"""
    return prev + 1


def lease_current(required_epoch, actual_epoch):
    """写入方持有的 epoch 必须等于当前发放 epoch（脑裂/回收后的旧 worker 写入被拒）。"""
    return required_epoch == actual_epoch


def validate_epoch(epoch):
    if not isinstance(epoch, int) or epoch < 1:
        raise ValueError("lease_epoch 必须是 ≥1 的整数")
    return epoch
