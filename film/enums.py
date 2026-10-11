"""封闭枚举与归一化（切片 A · 契约层）。

设计原则（依据 M5 核心约束 A-30~A-34）：平台无焦距/光圈/景深/快门参数，
因此契约层是**唯一**的摄影事实来源；枚举必须封闭，未知值一律拒绝（禁止静默回落）。

依据编号见 PRD/91-影视技术规格与交付标准.md、PRD/92-好莱坞制作流程对标.md、PRD/99-业界对标与调研.md。
"""

# ---------------------------------------------------------------- 枚举封闭集合

# 景别（M4.1-F01 分镜表字段完整化 / M5.1-F01 镜头语言枚举映射）
SHOT_SIZES = ("EWS", "WS", "LS", "MLS", "MS", "MCU", "CU", "ECU", "OTS", "POV", "INSERT")

# 角度（M5.1-F01）
ANGLES = ("eye_level", "high", "low", "birds_eye", "worms_eye", "dutch", "over_shoulder")

# 主运镜（M4.2-F01 单主运镜约束 / M5.1-F02 一镜一运动铁律）
#  推=dolly in（机位物理前移，透视变化）；zoom_in=焦距变化（透视不变）——二者不得混指（M5.1-F04）
MOVES = ("固定", "推", "拉", "摇", "移", "跟", "升降", "环绕", "手持", "zoom_in", "zoom_out")

# 次级运动只允许主体自身动作（M5.1-F02）
SUBJECT_MOVES = ("none", "walk", "run", "turn", "reach", "sit", "stand", "gesture", "breathe")

# 运镜速度三档（M5.1-F05：快档摇摄必须标注并交 judder QC）
SPEEDS = ("slow", "normal", "fast")

# 焦距六档（M5.2-F01；M4.2-F03 要求与景深意图非空）
#  档名 6 个：18=超广角、24=广角、35=标准、50=中长、85=长焦、135=超长焦
#  （PRD M5.2-F01 原文只给 5 个中文档名而列了 6 个 mm 值，此处按 M4 的 6 档名补齐 → 见待裁决清单 C-04）
LENS_MM = (18, 24, 35, 50, 85, 135)
LENS_LABEL = {
    18: "超广角", 24: "广角", 35: "标准",
    50: "中长", 85: "长焦", 135: "超长焦",
}

# 景深意图（M5.2-F02）。PRD 两处口径不一（M4.2-F03 写三值「浅/中/深」、M5.2-F02 写二值 shallow/deep），
# 此处取**二值** canonical，并把三值写成别名映射（见待裁决清单 C-02）。
DOF = ("shallow", "deep")
DOF_ALIASES = {
    "浅": "shallow", "shallow": "shallow",
    "中": "shallow", "medium": "shallow",
    "深": "deep", "deep": "deep",
}

# 人脸布光图案（M5.3-F03：人物镜必须四选一）
FACE_PATTERNS = ("rembrandt", "loop", "butterfly", "split", "none")

# 色温 CCT 档（M5.3-F05）
#  含 3000K：96 号演练的 S07 声明 3000K，而 PRD 原列五档不含 3000K → 见待裁决清单 C-03。
CCT = (2700, 3000, 3200, 4300, 5600, 6500)

# 体积光介质（M5.3-F06：无介质不得写「体积光」）
VOLUMETRIC_MEDIA = ("尘", "雾", "雨", "烟", "蒸汽", "none")

# 三点光方位（以镜头为基准的钟点方位，M5.3-F01）
CLOCK_POSITIONS = tuple("%d o'clock" % h for h in range(1, 13))

# 覆盖类型（M4.3-F01 覆盖类型枚举）
COVERAGE_TYPES = ("master", "single", "two_shot", "ots", "insert", "cutaway", "establishing")

# 物理骨架通道（M5.5-F01 / M4.4-F03 / E-63）：高动态 / 负重 / 碰撞三类强制走骨架
PHYSICS_SKELETON_TRIGGERS = ("high_dynamic", "load_bearing", "collision", "none")

# 安全区口径（M4.7-F01：SMPTE 与 EBU **择一并全片统一**）
SAFETY_BASES = ("SMPTE-ST-2046-1", "EBU-R95")

# 判定口径来源分级（B-14 SMPTE / B-16 EBU 为官档数值；其余为项目自定）
SOURCES_OFFICIAL = ("B-14", "B-16", "B-19")
SOURCE_SELF_DECLARED = "项目自定（B-88：无官方统一阈值）"

# 图形安全区：字幕等图形元素的内缩比例（B-16 EBU R95 5%）
GRAPHICS_INSET = 0.05
# 取景安全区（B-14 SMPTE ST 2046-1）
SMPTE_ACTION_SAFE = 0.93
SMPTE_TITLE_SAFE = 0.90
# EBU R95 取景内缩（B-16）
EBU_ACTION_INSET = 0.035
EBU_TITLE_INSET = 0.05

# ---------------------------------------------------------------- 别名归一化

_SIZE_ALIASES = {
    "EWS": "EWS", "超远景": "EWS", "大远景": "EWS",
    "WS": "WS", "远景": "WS",
    "LS": "LS", "全景": "LS",
    "MLS": "MLS", "中全景": "MLS",
    "MS": "MS", "中景": "MS",
    "MCU": "MCU", "中近景": "MCU",
    "CU": "CU", "特写": "CU",
    "ECU": "ECU", "大特写": "ECU",
    "OTS": "OTS", "过肩": "OTS", "过肩镜": "OTS",
    "POV": "POV", "主观": "POV",
    "INSERT": "INSERT", "插入": "INSERT",
}

_MOVE_ALIASES = {
    "static": "固定", "固定": "固定", "固定镜": "固定", "lock": "固定",
    "crane up": "升降", "crane down": "升降", "升降": "升降", "crane": "升降",
    "dolly in": "推", "push": "推", "push in": "推", "slow push": "推", "推": "推", "推镜": "推",
    "dolly out": "拉", "pull": "拉", "pull out": "拉", "拉": "拉", "拉镜": "拉",
    "pan": "摇", "pan left": "摇", "pan right": "摇", "tilt": "摇", "摇": "摇", "摇镜": "摇",
    "truck": "移", "truck left": "移", "truck right": "移", "track": "移", "移": "移", "横移": "移",
    "follow": "跟", "tracking": "跟", "跟": "跟", "跟拍": "跟",
    "orbit": "环绕", "arc": "环绕", "环绕": "环绕",
    "handheld": "手持", "手持": "手持",
    "zoom in": "zoom_in", "zoom_in": "zoom_in", "变焦推": "zoom_in",
    "zoom out": "zoom_out", "zoom_out": "zoom_out", "变焦拉": "zoom_out",
}


class ContractError(Exception):
    """契约非法（fail-closed：由调用方转成非零退出）。"""


def _norm_key(raw):
    return (raw or "").strip()


def norm_size(raw):
    v = _norm_key(raw)
    if v not in _SIZE_ALIASES:
        raise ContractError("景别不在封闭集合内：%r（允许：%s）" % (raw, "/".join(SHOT_SIZES)))
    return _SIZE_ALIASES[v]


def norm_move(raw):
    v = _norm_key(raw)
    if v not in _MOVE_ALIASES:
        raise ContractError("运镜不在封闭集合内：%r（允许：%s）" % (raw, "/".join(MOVES)))
    return _MOVE_ALIASES[v]


def norm_lens(raw):
    v = _norm_key(raw).replace("mm", "").replace("MM", "").strip()
    try:
        mm = int(float(v))
    except ValueError:
        raise ContractError("焦距档无法解析：%r（允许：%s）" % (raw, LENS_MM))
    if mm not in LENS_MM:
        raise ContractError("焦距档不在封闭集合内：%r mm（允许：%s）" % (raw, LENS_MM))
    return mm


def norm_dof(raw):
    v = _norm_key(raw).lower()
    if v not in DOF_ALIASES:
        raise ContractError("景深意图不在封闭集合内：%r（允许：%s 及其别名 %s）"
                            % (raw, DOF, sorted(DOF_ALIASES)))
    return DOF_ALIASES[v]


def norm_cct(raw):
    v = _norm_key(raw).upper().replace("K", "").strip()
    try:
        k = int(float(v))
    except ValueError:
        raise ContractError("色温档无法解析：%r（允许：%s）" % (raw, CCT))
    if k not in CCT:
        raise ContractError("色温档不在封闭集合内：%r K（允许：%s）" % (raw, CCT))
    return k


def norm_face_pattern(raw):
    v = _norm_key(raw).lower()
    aliases = {"伦勃朗": "rembrandt", "环型光": "loop", "蝴蝶光": "butterfly", "分割光": "split", "": "none"}
    v = aliases.get(v, v)
    if v not in FACE_PATTERNS:
        raise ContractError("人脸布光图案不在封闭集合内：%r（允许：%s）" % (raw, FACE_PATTERNS))
    return v


def norm_clock(raw):
    v = _norm_key(raw)
    if v not in CLOCK_POSITIONS:
        raise ContractError("光位方位不在封闭集合内：%r（允许：%s）" % (raw, CLOCK_POSITIONS))
    return v


def clock_to_degrees(clock):
    """钟点方位 → 以镜头光轴为 0°、顺时针的角度（用于跨镜方位漂移比对）。"""
    h = int(clock.split()[0])
    return (h % 12) * 30.0


def clock_angular_delta(a, b):
    """两个钟点方位的夹角（0–180）。"""
    d = abs(clock_to_degrees(a) - clock_to_degrees(b)) % 360.0
    return d if d <= 180.0 else 360.0 - d


def norm_volumetric_media(raw):
    v = _norm_key(raw)
    if not v:
        return "none"
    if v not in VOLUMETRIC_MEDIA:
        raise ContractError("体积光介质不在封闭集合内：%r（允许：%s）" % (raw, VOLUMETRIC_MEDIA))
    return v
