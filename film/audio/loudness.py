"""响度与真峰值验收（M8.5：归档 −23 LUFS/≤−1 dBTP；广播 −24 LKFS/<−2 dBTP；流媒体/Netflix）。"""
from . import enums


def validate_loudness(lufs, dbtp, preset):
    """响度/真峰值校验（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if preset == "archive":
        if abs(lufs - enums.ARCHIVE_LUFS) > enums.ARCHIVE_LUFS_TOL:
            v.append("归档响度 %.2f LUFS 超 ±%.1f" % (lufs, enums.ARCHIVE_LUFS_TOL))
        if dbtp > enums.ARCHIVE_DBTP:
            v.append("归档真峰值 %.2f dBTP > %d" % (dbtp, enums.ARCHIVE_DBTP))
    elif preset == "broadcast":
        if abs(lufs - enums.BROADCAST_LKFS) > 2.0:
            v.append("广播响度 %.2f LKFS 超 ±2 dB" % lufs)
        if dbtp >= enums.BROADCAST_DBTP:
            v.append("广播真峰值 %.2f dBTP ≥ %d" % (dbtp, enums.BROADCAST_DBTP))
    elif preset == "stream":
        lo, hi = enums.STREAM_LKFS_RANGE
        if not (lo <= lufs <= hi):
            v.append("流媒体响度 %.2f 越界（应 %s~%s）" % (lufs, lo, hi))
    elif preset == "netflix":
        if abs(lufs - enums.NETFLIX_LKFS) > 2.0:
            v.append("Netflix 响度 %.2f 超 ±2 LU" % lufs)
    else:
        v.append("未知响度预设：%r" % preset)
    return v
