"""M8 声音契约层 · 封闭枚举与阈值。"""

# 四层声音总线（M8.1-F01）
STEM_LAYERS = ("D", "M", "E", "Amb")

# 归档母版响度/真峰值（M8.5-F01/F02 / B-21）
ARCHIVE_LUFS = -23.0
ARCHIVE_LUFS_TOL = 0.2
ARCHIVE_DBTP = -1.0
# 广播（B-22）
BROADCAST_LKFS = -24.0
BROADCAST_DBTP = -2.0
# 流媒体（B-22）
STREAM_LKFS_RANGE = (-27.0, -23.0)
# Netflix（B-23）
NETFLIX_LKFS = -27.0

# 下混纪律（M8.1-F03 / B-25）：中置/环绕各 -3 dB，LFE 不下混
DOWMIX_DB = {"C": -3.0, "Ls": -3.0, "Rs": -3.0}

# 可懂度（M8.4-F01 / B-24）：对白高于稳态掩蔽 ≥15 dB
INTELLIGIBILITY_MIN_DB = 15.0
