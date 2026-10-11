"""失败分类 → 重试处置（M13.7 / 任务编排设计 §七：网络类可重试，内容类不自动重试）。"""
from . import enums


def retry_disposition(error_class):
    """错误类 → 重试处置；未知类 fail-closed 为 terminate。"""
    return enums.ERROR_RETRY.get(error_class, "terminate")


def should_auto_retry(error_class, attempts):
    """是否自动重试：网络类可重试，且未超过单镜硬上限 K≤2（含首次共 3 次机会）。"""
    return (retry_disposition(error_class) == "retry"
            and attempts < enums.AUTO_RETRY_LIMIT + 1)
