"""AI 生成内容标识（M18.5-F02：显式/隐式/导出文件三类 100% 存在）。"""
from . import enums


def validate_ai_labels(labels):
    """三类 AI 标识齐备校验。"""
    v = []
    for t in enums.LABEL_TYPES:
        if t not in labels:
            v.append("缺 AI 标识：%s" % t)
    return v
