"""主母版规格校验（M12.1-F01）。"""
from . import enums


def validate_master_spec(aspect, fps, lufs, dbtp):
    v = []
    if aspect != enums.MASTER_ASPECT:
        v.append("画幅 %r != %s" % (aspect, enums.MASTER_ASPECT))
    if fps != enums.MASTER_FPS:
        v.append("帧率 %d != %d" % (fps, enums.MASTER_FPS))
    if abs(lufs - enums.MASTER_LUFS) > enums.MASTER_LUFS_TOL:
        v.append("响度 %.2f LUFS 超 ±%.1f" % (lufs, enums.MASTER_LUFS_TOL))
    if dbtp > enums.MASTER_DBTP:
        v.append("真峰值 %.2f dBTP > %d" % (dbtp, enums.MASTER_DBTP))
    return v
