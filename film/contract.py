"""镜头契约数据结构与 PRD 解析（切片 A · 契约层）。

契约是 M4 分镜表与 M5 摄影契约的**唯一**结构化事实来源：
- M4.1-F01 分镜表字段完整化（关键字段非空率 100%）
- M4.2-F01~F04 单主运镜 / dolly 与 zoom 区分 / 焦距档与景深意图 / 光位与色温
- M5.2-F05 摄影参数快照、M5.3-F01~F06 布光契约、M5.5-F01 物理骨架通道
"""

import re

from . import enums
from .enums import ContractError

# 契约 schema 版本：任何字段语义变化必须递增，并让旧快照走显式迁移
CONTRACT_VERSION = "p1a-contract-v1"
# 枚举 → 提示词映射表版本（M5.1-F01 要求记录所用映射表版本）
MAP_VERSION = "p1a-map-v1"


class ShotContract(object):
    """单镜契约。所有字段在构造时即被封闭枚举校验（fail-closed）。"""

    __slots__ = (
        "no", "scene", "size", "angle", "move", "move_secondary", "speed", "subject_move",
        "lens_mm", "dof", "face_pattern", "key_clock", "fill_clock", "back_clock",
        "key_ratio", "fill_ratio", "key_cct", "fill_cct", "cct_relation",
        "volumetric_active", "volumetric_media", "coverage", "physics_skeleton",
        "physics_triggers", "duration_sec", "dialogue", "reference",
        "light_note", "subject_x", "subject_y", "subject_scale", "provenance",
    )

    def __init__(self, **kw):
        self.no = int(kw["no"])
        self.scene = kw.get("scene", "")
        self.size = enums.norm_size(kw.get("size", ""))
        self.angle = kw.get("angle", "eye_level")
        if self.angle not in enums.ANGLES:
            raise ContractError("角度不在封闭集合内：%r（允许：%s）" % (self.angle, enums.ANGLES))
        self.move = enums.norm_move(kw.get("move", ""))
        self.move_secondary = kw.get("move_secondary", "none")
        if self.move_secondary not in ("none",) + enums.MOVES:
            raise ContractError("次级**机位**运动不在封闭集合内：%r（一镜一运动铁律：只允许 none）"
                                % (self.move_secondary,))
        self.speed = kw.get("speed", "normal")
        if self.speed not in enums.SPEEDS:
            raise ContractError("速度档不在封闭集合内：%r（允许：%s）" % (self.speed, enums.SPEEDS))
        self.subject_move = kw.get("subject_move", "none")
        if self.subject_move not in enums.SUBJECT_MOVES:
            raise ContractError("次级运动不在封闭集合内：%r（允许：%s）"
                                % (self.subject_move, enums.SUBJECT_MOVES))
        self.lens_mm = enums.norm_lens(kw.get("lens_mm", kw.get("lens", "")))
        self.dof = enums.norm_dof(kw.get("dof", "shallow"))
        self.face_pattern = enums.norm_face_pattern(kw.get("face_pattern", "none"))
        self.key_clock = kw.get("key_clock", "none")
        self.fill_clock = kw.get("fill_clock", "none")
        self.back_clock = kw.get("back_clock", "none")
        for name, val in (("key_clock", self.key_clock), ("fill_clock", self.fill_clock),
                          ("back_clock", self.back_clock)):
            if val != "none":
                enums.norm_clock(val)
        self.key_ratio = float(kw.get("key_ratio", 1.0))
        self.fill_ratio = float(kw.get("fill_ratio", 0.0))
        self.key_cct = enums.norm_cct(kw.get("key_cct", "3200"))
        self.fill_cct = enums.norm_cct(kw.get("fill_cct", str(self.key_cct)))
        self.cct_relation = kw.get("cct_relation", "same")
        if self.cct_relation not in ("same", "cool_bg_warm_subject", "warm_bg_cool_subject"):
            raise ContractError("冷暖关系不在封闭集合内：%r" % (self.cct_relation,))
        self.volumetric_active = bool(kw.get("volumetric_active", False))
        self.volumetric_media = enums.norm_volumetric_media(kw.get("volumetric_media", "none"))
        self.coverage = kw.get("coverage", "single")
        if self.coverage not in enums.COVERAGE_TYPES:
            raise ContractError("覆盖类型不在封闭集合内：%r（允许：%s）"
                                % (self.coverage, enums.COVERAGE_TYPES))
        self.physics_skeleton = bool(kw.get("physics_skeleton", False))
        self.physics_triggers = tuple(kw.get("physics_triggers", ("none",)))
        for t in self.physics_triggers:
            if t not in enums.PHYSICS_SKELETON_TRIGGERS:
                raise ContractError("物理骨架触发类型不在封闭集合内：%r" % (t,))
        self.duration_sec = float(kw.get("duration_sec", 0.0))
        self.dialogue = kw.get("dialogue", "")
        self.reference = kw.get("reference", "")
        self.light_note = kw.get("light_note", "")
        # 构图参数（PRD 96 的镜头契约表未提供 → 由 fixture 显式声明，并登记 provenance；
        # 仅供三画幅安全框预演使用，不参与提示词编译）
        self.subject_x = float(kw.get("subject_x", 0.5))
        self.subject_y = float(kw.get("subject_y", 0.66))
        self.subject_scale = float(kw.get("subject_scale", 0.0))
        self.provenance = kw.get("provenance", {})

    # ------------------------------------------------------------ 派生判定

    @property
    def has_person(self):
        """是否人物镜（决定三点光/人脸图案/参考图是否强制）。

        人物镜 = 景别落在人物镜集合内，且不是纯道具插入镜。
        """
        return self.size in ("CU", "MCU", "MS", "MLS", "OTS", "ECU", "POV")

    @property
    def needs_judder_note(self):
        """快档摇/移/跟必须带 judder 标注（M5.1-F05、EL-09）。"""
        return self.speed == "fast" and self.move in ("摇", "移", "跟", "环绕", "手持")

    def as_dict(self):
        d = {k: getattr(self, k) for k in self.__slots__}
        d["lens_label"] = enums.LENS_LABEL[self.lens_mm]
        d["physics_triggers"] = list(self.physics_triggers)
        return d


# ---------------------------------------------------------------- PRD 解析

# PRD/96 的镜头契约表行：| S01 | EWS | 24mm | crane up | dawn practical / 4300K | 2.0 s | 对白 | 参考 | 否 |
_ROW = re.compile(r"^\|\s*(S\d{2})\s*\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.+?)\|\s*$")
_CCT = re.compile(r"(\d{4})\s*K")
_DUR = re.compile(r"([0-9.]+)\s*s")
# 分镜表未给出的字段在此显式声明默认值（并在产物里登记 provenance，禁止假装表里有）
_TABLE_DEFAULTS = {
    "angle": "eye_level",
    "move_secondary": "none",
    "speed": "normal",
    "subject_move": "none",
    "scene": "SC-EP01-01",
    "dof": "shallow",
    "face_pattern": "none",
    "key_clock": "11 o'clock",
    "fill_clock": "3 o'clock",
    "back_clock": "7 o'clock",
    "key_ratio": 1.0,
    "fill_ratio": 0.5,
    "cct_relation": "same",
    "volumetric_active": False,
    "volumetric_media": "none",
    "coverage": "single",
    "physics_skeleton": False,
    "physics_triggers": ("none",),
    "subject_x": 0.5,
    "subject_y": 0.66,
    "subject_scale": 0.0,
    "provenance": {},
}

# 光位关键词 → 人脸布光图案（M5.3-F03）：表里写的是光位设计意图，这里做**显式**映射
_LIGHT_PATTERN = (
    ("rembrandt", "rembrandt"),
    ("loop", "loop"),
    ("butterfly", "butterfly"),
    ("split", "split"),
    ("back light", "split"),   # 轮廓主光 → 面部呈分割光（明暗分界沿中线）
    ("hard key low", "split"),
    ("soft daylight", "loop"),
    ("dawn", "none"),
    ("practical", "none"),
    ("motivated key", "rembrandt"),
)


def parse_prd_shot_table(text):
    """解析 PRD/96 的「EP01 前 8 镜镜头契约」表 → ShotContract 列表。

    只读 PRD 原文，避免手抄 fixture 带来的数字漂移（docs/agent-prd-method.md 的踩坑教训）。
    """
    rows = []
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        no, size, lens, move, light, dur, line_, ref, phys = (g.strip() for g in m.groups())
        if not no.startswith("S") or not re.match(r"^S\d{2}$", no):
            continue
        cct_m = _CCT.search(light)
        if not cct_m:
            raise ContractError("%s 的光位列缺少色温档：%r" % (no, light))
        key_cct = cct_m.group(1)
        light_note = _CCT.sub("", light).strip().rstrip("/").strip()
        dur_m = _DUR.search(dur)
        if not dur_m:
            raise ContractError("%s 的时长列无法解析：%r" % (no, dur))
        pattern = "none"
        low = light_note.lower()
        for kw, pat in _LIGHT_PATTERN:
            if kw in low:
                pattern = pat
                break
        kw = dict(_TABLE_DEFAULTS)
        kw.update({
            "no": int(no[1:]),
            "size": size,
            "lens_mm": lens,
            "move": move,
            "light_note": light_note,
            "key_cct": key_cct,
            "fill_cct": key_cct,
            "duration_sec": float(dur_m.group(1)),
            "dialogue": "" if line_ in ("—", "-", "") else line_,
            "reference": "" if ref in ("—", "-") else ref,
            "physics_skeleton": phys.replace("*", "").strip() == "是",
            "face_pattern": pattern,
            "provenance": {
                "source": "PRD/96-先导集演练.md（EP01 前 8 镜镜头契约表）",
                "table_supplied": ["no", "size", "lens_mm", "move", "light_note", "key_cct",
                                   "duration_sec", "dialogue", "reference", "physics_skeleton"],
                "defaulted": sorted(k for k in _TABLE_DEFAULTS
                                    if k not in ("provenance",)),
                "derived": {"face_pattern": "由光位描述映射（M5.3-F03）"},
            },
        })
        provenance = dict(kw.get("provenance", {}))
        provenance["constructor_kwargs"] = {k: v for k, v in kw.items() if k != "provenance"}
        kw["provenance"] = provenance
        rows.append(ShotContract(**kw))
    if not rows:
        raise ContractError("未从 PRD 文本解析到任何镜头契约行（表格格式可能已变）")
    return rows


# 构图几何的允许来源：只接受具名来源，禁止无出处的裸数字
GEOMETRY_SOURCES = (
    "anchor:demo-render",       # 由参考实现的渲染几何反推（本仓库 demo/out）
    "declared:director",        # 导演/分镜层显式声明
    "declared:fixture",         # fixture 显式声明
)


def apply_geometry(shots, geometry):
    """把 fixture 的构图几何（subject_x / subject_scale / scene）叠加到契约上。

    PRD 96 的镜头契约表**不含**构图几何字段 → 这里必须带来源（GEOMETRY_SOURCES），
    否则拒绝（禁止无出处的裸数字，见 90 号第九章与 B-88 的诚实口径纪律）。
    """
    by_no = {int(item["no"]): item for item in geometry}
    for s in shots:
        item = by_no.get(s.no)
        if not item:
            raise ContractError("S%02d 缺少构图几何声明（fixture.geometry）" % s.no)
        src = item.get("geometry_source")
        if src not in GEOMETRY_SOURCES:
            raise ContractError("S%02d 的构图几何来源非法或缺失：%r（允许：%s）"
                                % (s.no, src, GEOMETRY_SOURCES))
        s.subject_x = float(item["subject_x"])
        s.subject_y = float(item.get("subject_y", 0.66))
        s.subject_scale = float(item["subject_scale"])
        s.scene = item.get("scene", s.scene)
        if "light_note" in item:
            s.light_note = item["light_note"]
        s.provenance = dict(s.provenance)
        s.provenance["geometry"] = {
            "source": src,
            "subject_x": s.subject_x,
            "subject_y": s.subject_y,
            "subject_scale": s.subject_scale,
            "note": item.get("geometry_note", ""),
        }
    return shots
