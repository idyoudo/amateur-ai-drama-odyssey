"""多画幅安全框几何（切片 A · M4.4-F02 / M4.7-F01 / M4.7-F02 / NFR-09 / EL-01 / EL-02）。

规则来源：
- EL-01：唯一生成母版为 **16:9 open gate**；2.39:1 与 9:16 一律由同一素材派生，禁止单画幅重复生成。
- M4.7-F01：SMPTE 与 EBU **两种口径择一并全片统一**。
- M4.7-F02：100% 镜头通过三画幅可裁切预演；**9:16 关键信息出框镜数 = 0**。
- B-14（SMPTE ST 2046-1 Action Safe 93% / Title Safe 90%）、B-16（EBU R95 内缩 3.5% / 5%）。
- 90 号第九章：安全区百分比属「未取到原文」类，项目自定值必须写入 QC 报告、不得冒充官方硬阈值。
"""

from . import enums

# 画幅目标（D1：2.39:1 主母版 / 16:9 平台版 / 9:16 衍生版）
ASPECTS = {
    "239": {"ratio": 2.39, "label": "2.39:1 主母版", "role": "master"},
    "169": {"ratio": 16.0 / 9.0, "label": "16:9 平台版", "role": "platform"},
    "916": {"ratio": 9.0 / 16.0, "label": "9:16 竖屏衍生", "role": "derivative"},
}
# 容差（比例）——项目自定，写入 QC 报告
ASPECT_TOLERANCE = 0.01


class SafetyBasisError(Exception):
    """安全区口径非法或未声明（fail-closed）。"""


def resolve_basis(basis):
    """把口径名解析为具体百分比。

    - SMPTE-ST-2046-1（B-14）：Action 93% / Title 90%
    - EBU-R95（B-16）：Action 内缩 3.5% / Title 内缩 5%
    口径必须显式声明（M4.7-F01「择一并全片统一」），缺省即拒绝。
    """
    if basis not in enums.SAFETY_BASES:
        raise SafetyBasisError("安全区口径必须在 %s 中显式声明，当前为 %r" % (enums.SAFETY_BASES, basis))
    if basis == "SMPTE-ST-2046-1":
        return {
            "basis": basis,
            "source": "B-14（SMPTE ST 2046-1）",
            "action_frac": enums.SMPTE_ACTION_SAFE,
            "title_frac": enums.SMPTE_TITLE_SAFE,
            "graphics_inset": enums.GRAPHICS_INSET,
            "graphics_source": "B-16（EBU R95 5% 图形安全区）",
            "declared": False,
        }
    return {
        "basis": basis,
        "source": "B-16（EBU R95）",
        "action_frac": 1.0 - 2 * enums.EBU_ACTION_INSET,
        "title_frac": 1.0 - 2 * enums.EBU_TITLE_INSET,
        "graphics_inset": enums.EBU_TITLE_INSET,
        "graphics_source": "B-16（EBU R95）",
        "declared": False,
    }


def derive_crops(gate_w, gate_h):
    """由 16:9 open gate 派生三画幅**中心裁切窗**（一律裁切，禁止拉伸/重采样）。

    返回 {aspect: {x0, y0, w, h, ratio, tol_ok}}。
    宽画幅（2.39 < 16:9）上下裁；窄画幅（9:16 > 16:9 的倒数）左右裁。
    """
    out = {}
    gate_ratio = float(gate_w) / float(gate_h)
    for key, spec in ASPECTS.items():
        target = spec["ratio"]
        if target >= gate_ratio:
            # 比 open gate 更宽的画幅（2.39:1）→ 上下裁
            w = gate_w
            h = int(round(gate_w / target))
            x0 = 0
            y0 = int((gate_h - h) // 2)
            mode = "vertical_crop"  # 上下裁
        else:
            # 比 open gate 更窄的画幅（9:16）→ 左右裁
            h = gate_h
            w = int(round(gate_h * target))
            x0 = int((gate_w - w) // 2)
            y0 = 0
            mode = "horizontal_crop"  # 左右裁
        if x0 < 0 or y0 < 0 or x0 + w > gate_w or y0 + h > gate_h:
            raise SafetyBasisError("裁切窗越出 open gate：%s → (%d,%d,%d,%d) in %dx%d"
                                   % (key, x0, y0, w, h, gate_w, gate_h))
        out[key] = {
            "x0": x0, "y0": y0, "w": w, "h": h,
            "ratio": round(float(w) / float(h), 6),
            "target_ratio": target,
            "ratio_ok": abs((float(w) / float(h)) - target) / target <= ASPECT_TOLERANCE,
            "mode": mode,
            "derived_from": "16:9 open gate（EL-01）",
        }
    return out


def safe_rect(crop, frac):
    """在给定裁切窗内居中的安全矩形（frac 为边长比例）。"""
    w = int(round(crop["w"] * frac))
    h = int(round(crop["h"] * frac))
    x0 = crop["x0"] + int((crop["w"] - w) // 2)
    y0 = crop["y0"] + int((crop["h"] - h) // 2)
    return {"x0": x0, "y0": y0, "w": w, "h": h, "x1": x0 + w, "y1": y0 + h,
            "frac": frac, "width": w, "height": h}


def graphics_rect(crop, inset):
    """图形安全区（字幕等）：四边各内缩 inset。"""
    x0 = crop["x0"] + int(round(crop["w"] * inset))
    y0 = crop["y0"] + int(round(crop["h"] * inset))
    x1 = crop["x0"] + crop["w"] - int(round(crop["w"] * inset))
    y1 = crop["y0"] + crop["h"] - int(round(crop["h"] * inset))
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "w": x1 - x0, "h": y1 - y0}


def subject_bounds(center_x_frac, width_frac, base_y_frac=0.66,
                   gate_w=1920, gate_h=1080, width_scale=3.0, head_radius_frac=0.40,
                   height_frac=0.40, body_dy=(0.36, 0.14, 0.60)):
    """由构图参数推导主体包围盒（**与生成器同一公式**，用于口径对账）。

    语义（与 demo 参考实现一致）：
      全宽 = 0.10 × gate_w × subject_scale × 3；主体水平中心 = subject_x × gate_w；
      最宽部件为头部椭圆（半径 = 全宽 × 0.40），故包围盒 = 中心 ± 全宽 × 0.40。
    """
    hd, b0, b1 = body_dy
    full_w = 0.10 * gate_w * width_frac * width_scale
    full_h = height_frac * gate_h * width_frac * width_scale
    cx = center_x_frac * gate_w
    cy = base_y_frac * gate_h
    half = full_w * head_radius_frac
    top = cy - full_h * hd - full_h * head_radius_frac
    bottom = cy + full_h * b1
    return {
        "x0": int(round(cx - half)), "x1": int(round(cx + half)),
        "y0": int(round(max(0, top))), "y1": int(round(min(gate_h, bottom))),
        "cx": int(round(cx)), "cy": int(round(cy)),
        "widest_part": "head_ellipse",
        "formula": "cx=subject_x*gate_w; half=0.10*gate_w*subject_scale*3*0.40; "
                   "cy=subject_y*gate_h",
    }


# 关键信息（面部/手部）竖向范围：以包围盒顶为 0 计的偏移比例。
# 头部椭圆几何：圆心 = cy - 0.36×full_h，竖向半轴 = 0.40×full_h
#   → 头顶（包围盒顶）= cy - 0.76×full_h；下巴 = cy + 0.04×full_h
# 取「头顶 − 0.10×full_h（含发型/留白）」到「下巴 + 0.05×full_h（含颈部）」
CRITICAL_TOP_FRAC = 0.10
CRITICAL_BOTTOM_FRAC = 0.05


def critical_region(subject, full_h, head_bottom):
    """关键信息区（面部/手部）——多画幅安全框的**硬性**判据对象。

    依据 D1 缓解措施 1（EL-02）：「所有关键表演与叙事信息收在中心 9:16 安全区内，
    两侧仅承载氛围」。因此**关键信息区**必须落在三画幅各自的 action safe 内；
    而躯体（含脚部）在 2.39:1 画幅被裁切属正常电影取景，不作硬性判据。
    """
    return {
        "x0": subject["x0"], "x1": subject["x1"],
        "y0": int(round(subject["y0"] + full_h * CRITICAL_TOP_FRAC)),
        "y1": int(round(head_bottom + full_h * CRITICAL_BOTTOM_FRAC)),
    }


def critical_from_params(center_x_frac, width_frac, base_y_frac=0.66,
                         gate_w=1920, gate_h=1080, width_scale=3.0, height_frac=0.40,
                         head_radius_frac=0.40, body_dy=(0.36, 0.14, 0.60)):
    """由构图参数直接推导关键信息区与整体包围盒（供契约层与复测层独立复算）。"""
    hd, b0, b1 = body_dy
    full_w = 0.10 * gate_w * width_frac * width_scale
    full_h = height_frac * gate_h * width_frac * width_scale
    cx = center_x_frac * gate_w
    cy = base_y_frac * gate_h
    half = full_w * head_radius_frac
    head_bottom = cy - full_h * hd + full_h * head_radius_frac
    full = {"x0": int(round(cx - half)), "x1": int(round(cx + half)),
            "y0": int(round(max(0, cy - full_h * hd - full_h * head_radius_frac))),
            "y1": int(round(min(gate_h, cy + full_h * b1)))}
    top = cy - full_h * hd - full_h * head_radius_frac
    crit = {"x0": full["x0"], "x1": full["x1"],
            "y0": int(round(max(0, top + full_h * CRITICAL_TOP_FRAC))),
            "y1": int(round(head_bottom + full_h * CRITICAL_BOTTOM_FRAC))}
    return full, crit, {"full_w": full_w, "full_h": full_h, "cx": cx, "cy": cy}


def _edges(rect):
    """统一取矩形的四边：同时兼容 {x0,y0,w,h} 与 {x0,y0,x1,y1} 两种写法。"""
    x0 = rect["x0"]
    y0 = rect["y0"]
    x1 = rect["x1"] if "x1" in rect else x0 + rect["w"]
    y1 = rect["y1"] if "y1" in rect else y0 + rect["h"]
    return x0, y0, x1, y1


def contains(rect, box):
    """box 是否完全落在 rect 内。"""
    rx0, ry0, rx1, ry1 = _edges(rect)
    bx0, by0, bx1, by1 = _edges(box)
    return bx0 >= rx0 and bx1 <= rx1 and by0 >= ry0 and by1 <= ry1


def overflow(rect, box):
    """越界像素数（左右上下分别计），全 0 表示未出框。"""
    rx0, ry0, rx1, ry1 = _edges(rect)
    bx0, by0, bx1, by1 = _edges(box)
    return {
        "left": max(0, rx0 - bx0),
        "right": max(0, bx1 - rx1),
        "top": max(0, ry0 - by0),
        "bottom": max(0, by1 - ry1),
    }


def intersection_ratio(rect, box):
    """box 落在 rect 内的面积占比（用于「关键信息主体应基本落在 9:16 内」的量化）。"""
    rx0, ry0, rx1, ry1 = _edges(rect)
    bx0, by0, bx1, by1 = _edges(box)
    ix0, iy0 = max(rx0, bx0), max(ry0, by0)
    ix1, iy1 = min(rx1, bx1), min(ry1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = float((ix1 - ix0) * (iy1 - iy0))
    area = float((bx1 - bx0) * (by1 - by0))
    return 0.0 if area <= 0 else inter / area
