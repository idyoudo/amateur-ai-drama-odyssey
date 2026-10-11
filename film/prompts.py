"""确定性提示词编译（切片 A · M5.1/M5.2/M5.3）。

硬性要求：
- **纯函数**：同输入 → 同输出（字节级一致，M5.1-F01 验收原文）。
- **版本化**：映射表版本写入产物（M5.1-F01「记录所用映射表版本」）。
- **指令归属表**：运镜/光位 → 提示词；时长/分辨率/帧率 → 接口参数；
  同一动作不得既写提示词又设参数，冲突即告警（M5.1-F03，依据 A-31 双重指挥失败模式）。
- 平台无焦距/光圈/景深参数（A-30~A-34），故全部落为**可见结果描述**而非参数名（A-33）。
"""

import hashlib

from .contract import MAP_VERSION
from .enums import LENS_LABEL

# 指令归属表（M5.1-F03）：每条指令只能有一个归属通道
OWNERSHIP = {
    "move": "prompt",
    "speed": "prompt",
    "size": "prompt",
    "angle": "prompt",
    "lens_mm": "prompt",
    "dof": "prompt",
    "lighting": "prompt",
    "cct": "prompt",
    "volumetric_media": "prompt",
    "duration_sec": "interface",
    "resolution": "interface",
    "fps": "interface",
    "frame_rate": "interface",
    "aspect": "interface",
}

# 不得出现在提示词里的接口侧词汇（出现即视为双重指挥 → 冲突告警）
_INTERFACE_LEAK_TOKENS = (
    "1080p", "720p", "2K", "4K", "resolution", "分辨率", "duration", "时长参数",
    "24fps", "30fps", "60fps", "帧率参数", "aspect_ratio",
)

_ANGLE_LABEL = {
    "eye_level": "平视机位，视线与主体眼高齐平",
    "high": "高机位俯视，主体显得被压制",
    "low": "低机位仰视，主体显得有压迫力",
    "birds_eye": "顶视鸟瞰，空间关系一览",
    "worms_eye": "极低机位，地面成为背景",
    "dutch": "倾斜机位，画面水平线倾斜",
    "over_shoulder": "过肩机位，前景肩线入画",
}

_SIZE_LABEL = {
    "EWS": "极远景，人物在环境中很小",
    "WS": "远景，人物全身且环境占主导",
    "LS": "全景，人物全身入画",
    "MLS": "中全景，人物膝上入画",
    "MS": "中景，人物腰部以上入画",
    "MCU": "中近景，人物胸部以上入画",
    "CU": "特写，面部充满画面",
    "ECU": "大特写，局部细节充满画面",
    "OTS": "过肩镜，前景肩部与后脑入画",
    "POV": "主观镜，等同角色视角",
    "INSERT": "插入镜，只拍道具或细节",
}

_MOVE_LABEL = {
    "固定": "机位固定不动，画面稳定",
    "推": "机位沿光轴向前移动（dolly in），透视随距离改变、背景相对主体放大",
    "拉": "机位沿光轴向后移动（dolly out），透视随距离改变、环境逐步纳入",
    "摇": "机位不移动，镜头在水平或垂直方向转动（pan / tilt）",
    "移": "机位整体横向平移（track / truck），背景产生视差",
    "跟": "机位跟随主体运动，主体在画面中位置基本不变",
    "升降": "机位垂直升降（crane），高度改变带来空间展开",
    "环绕": "机位绕主体做弧线运动（orbit），背景连续滚动",
    "手持": "手持机位，画面有轻微不规则晃动与呼吸感",
    "zoom_in": "焦距变长（zoom in），透视不变，画面整体放大、景别收窄",
    "zoom_out": "焦距变短（zoom out），透视不变，画面整体缩小、景别放宽",
}

_SPEED_LABEL = {"slow": "运动速度缓慢", "normal": "运动速度常速", "fast": "运动速度快，需标注 judder 检查"}

_DOF_LABEL = {
    ("shallow", False): "景深浅：主体清晰、背景明显分离",
    ("deep", False): "景深深：主体与背景同时可辨",
    ("shallow", True): "景深浅：主体清晰、背景明显分离，焦外为椭圆光斑（变形宽银幕风格包）",
    ("deep", True): "景深深：主体与背景同时可辨，画面横向光晕（变形宽银幕风格包）",
}

_MEDIA_LABEL = {
    "尘": "空气中悬浮尘埃形成可见光柱",
    "雾": "雾介质让光柱边界柔和、产生丁达尔现象",
    "雨": "雨介质中光柱被雨丝切碎、出现闪烁颗粒",
    "烟": "烟雾介质让光柱有翻滚形体",
    "蒸汽": "蒸汽介质让光柱随气流摆动",
    "none": "",
}


def _lens_visible_result(mm):
    """焦距档 → 可见结果描述（A-33：真正起作用的是用文字描述的可见结果）。"""
    return {
        18: "画面视野极开阔，近大远小夸张，边缘有可见透视拉伸",
        24: "画面视野开阔，环境交代完整，纵深层次分明",
        35: "接近人眼观感的自然透视，空间关系写实",
        50: "透视平缓，人物与环境比例接近真实观感",
        85: "空间被压缩，背景与主体贴近，人物从环境中被剥离",
        135: "空间强烈压缩，背景成片状色块，细节被抽取放大",
    }[mm]


def _bokeh_clause(shot):
    """bokeh 描述规范（M5.2-F03）：焦外光斑形态 + 光斑来源 + 边缘软硬；禁止只写 bokeh。"""
    if shot.dof != "shallow":
        return ""
    src = {
        "dawn": "远景天光与街灯光点",
        "practical": "站台实用灯与广告牌光点",
        "street": "街道车灯与招牌光点",
        "soft": "窗内散射光斑",
        "hard": "低角度硬光在金属道具上的高光点",
        "back": "轮廓光在空气中的光点",
        "motivated": "场景动机灯的光点",
        "rembrandt": "侧后位主光在暗部的光点",
    }
    key = None
    low = (shot.light_note or "").lower()
    for k in src:
        if k in low:
            key = k
            break
    source = src.get(key, "场景内动机光源的光点")
    return "焦外光斑为边缘柔和的圆形光斑，来源为%s，光斑边缘由内向外渐隐" % source


def _lighting_clause(shot):
    parts = []
    if shot.has_person and shot.key_clock != "none":
        ratio_txt = "主辅光比约 %.1f:1" % (shot.key_ratio / max(shot.fill_ratio, 1e-6))
        parts.append("主光位于%s、辅光位于%s、轮廓光位于%s，%s"
                     % (shot.key_clock, shot.fill_clock, shot.back_clock, ratio_txt))
    if shot.face_pattern == "rembrandt":
        parts.append("面部呈现伦勃朗光：暗侧颊部有一枚倒三角光斑，鼻影与颊影连成一体")
    elif shot.face_pattern == "loop":
        parts.append("面部呈现环形光：鼻影呈小弧形但未触及颊影，面部明暗分界柔和")
    elif shot.face_pattern == "butterfly":
        parts.append("面部呈现蝴蝶光：鼻下对称蝶形阴影，颧骨下方有阴影带")
    elif shot.face_pattern == "split":
        parts.append("面部呈现分割光：面部沿中线一明一暗，明暗边界清晰")
    if shot.cct_relation == "cool_bg_warm_subject":
        parts.append("主体受暖光（%dK）、背景为冷色（%dK），冷暖分离" % (shot.key_cct, shot.fill_cct))
    elif shot.cct_relation == "warm_bg_cool_subject":
        parts.append("主体受冷光（%dK）、背景为暖色（%dK），冷暖分离" % (shot.key_cct, shot.fill_cct))
    else:
        parts.append("全场色温统一约 %dK" % shot.key_cct)
    if shot.volumetric_active and shot.volumetric_media != "none":
        parts.append(_MEDIA_LABEL[shot.volumetric_media])
    return "；".join(parts)


def compile_prompt(shot, identity_lock=None):
    """把契约编译为确定性提示词片段。

    返回 dict：{prompt, sha256, fragments, mapping_version, ownership, leaks}
    - fragments：逐条片段及来源字段，便于复测逐项核对（不黑箱）。
    - leaks：提示词里出现的接口侧词汇（M5.1-F03 冲突告警）。
    """
    frags = []
    if identity_lock:
        frags.append(("identity_lock", identity_lock))
    frags.append(("size", _SIZE_LABEL[shot.size]))
    frags.append(("angle", _ANGLE_LABEL[shot.angle]))
    frags.append(("lens", "%dmm（%s）：%s" % (shot.lens_mm, LENS_LABEL[shot.lens_mm],
                                             _lens_visible_result(shot.lens_mm))))
    frags.append(("dof", _DOF_LABEL[(shot.dof, shot.lens_mm >= 85 and shot.dof == "shallow")]))
    bokeh = _bokeh_clause(shot)
    if bokeh:
        frags.append(("bokeh", bokeh))
    frags.append(("move", _MOVE_LABEL[shot.move]))
    frags.append(("speed", _SPEED_LABEL[shot.speed]))
    if shot.needs_judder_note:
        frags.append(("judder", "快摇/快速运动镜：标注为 judder 抽检项（EL-09）"))
    if shot.has_person:
        frags.append(("lighting", _lighting_clause(shot)))
    if shot.reference:
        frags.append(("reference", "参考图：%s" % shot.reference))
    if shot.subject_move not in ("none",):
        frags.append(("subject_move", "主体自身动作：%s" % shot.subject_move))

    prompt = "，".join(text for _, text in frags)
    leaks = [t for t in _INTERFACE_LEAK_TOKENS if t in prompt]
    return {
        "no": shot.no,
        "prompt": prompt,
        "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "fragments": [{"field": f, "text": t} for f, t in frags],
        "mapping_version": MAP_VERSION,
        "ownership": OWNERSHIP,
        "leaks": leaks,
    }


def compile_all(shots, identity_lock=None):
    """全镜编译（顺序稳定；不使用 set/dict 迭代顺序）。"""
    return [compile_prompt(s, identity_lock=identity_lock) for s in sorted(shots, key=lambda x: x.no)]
