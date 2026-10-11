"""M15 存储契约层 · 封闭枚举。"""

# 资产类型（数据模型 §三 assets.kind）
ASSET_KINDS = ("image", "video", "audio", "stem", "subtitle", "master", "derived")

# 生成母版（M15.2-F01：16:9 open gate 最高可用分辨率，唯一）
GENERATION_MASTER_SPEC = "16:9-open-gate"
# 归档主母版（M15.3-F04：2.39:1 Rec.709，唯一）
ARCHIVE_MASTER_SPEC = "2.39:1"
# 派生版本（M15.2-F02 / M15.3-F05：均从生成母版派生，不新增生成调用）
DERIVED_SPECS = ("16:9", "9:16", "HDR10", "5.1", "48fps")

# 母版类 spec（生成母版 + 归档母版）
MASTER_SPECS = (GENERATION_MASTER_SPEC, ARCHIVE_MASTER_SPEC)
