"""一致性检测阈值判定（人脸阈值 + 分位截断）。"""
from . import enums


def face_verdict(similarity):
    """人脸相似度判定（M6.3-F02）：≥0.45 通过 / 0.30–0.45 灰区（待标定）/ <0.30 失败。"""
    if similarity >= enums.FACE_PASS:
        return "pass"
    if similarity >= enums.FACE_FAIL:
        return "gray"
    return "fail"


def quantile_trim(score, p10, mean, sigma):
    """分位截断（M6.3-F03）：低于本集 P10 或 均值−2σ → 进复核队列（绝对阈值仅兜底）。"""
    return score < p10 or score < mean - 2 * sigma
