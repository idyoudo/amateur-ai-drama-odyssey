"""代理画面渲染与三画幅裁切预演（切片 A · M4.4-F02 / M4.7-F02）。

⚠️ 纪律：
- 产物是**构图预演代理图（PROXY）**，不是成片画面，也不是母版（EL-16）。
- 渲染只用于**逐像素验证安全框几何**：主体以高对比暗部渲染，背景保持高亮，使「主体包围盒」
  可由亮度假掩膜独立复算——复测脚本据此判定主体是否出框（M4.7-F02「出框镜数 = 0」）。
- 渲染是 16:9 open gate 唯一母版；239 / 169 / 916 全部由它**中心裁切派生**（EL-01）。
"""

import numpy as np
from PIL import Image

from . import geometry

PROXY_NOTICE = "PROXY — NOT A DELIVERABLE MASTER"

# 亮度假掩膜阈值：主体（暗）< 阈值 < 背景（亮）
LUMA_SUBJECT_MAX = 70.0
LUMA_BG_MIN = 100.0


def _luma(arr):
    return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]


def subject_mask(cx, cy, sw, sh, xx, yy):
    """主体掩膜：头部椭圆 + 躯干矩形（与参考实现对同一构图语义同一公式）。

    head: 半轴 (sw*0.40, sh*0.40)，圆心 (cx, cy - sh*0.36)
    body: 半宽 sw*0.36，纵向 [cy - sh*0.14, cy + sh*0.60]
    """
    head = (((xx - cx) / max(sw * 0.40, 1.0)) ** 2
            + ((yy - (cy - sh * 0.36)) / max(sh * 0.40, 1.0)) ** 2) <= 1.0
    body = (np.abs(xx - cx) < sw * 0.36) & (yy > cy - sh * 0.14) & (yy < cy + sh * 0.60)
    return (head | body)


def render_gate(shot, gate_w=1920, gate_h=1080):
    """渲染 16:9 open gate 代理构图帧（确定性：无随机数）。"""
    yy, xx = np.mgrid[0:gate_h, 0:gate_w].astype(np.float32)
    horizon = gate_h * 0.62

    # 背景：天花板亮 → 地面中等（保证远高于主体亮度，便于覆盖掩膜反推）
    sky = 250.0 - 70.0 * (yy / max(horizon, 1.0))
    ground = 150.0 - 30.0 * ((yy - horizon) / max(gate_h - horizon, 1.0))
    bg = np.where(yy < horizon, sky, ground)
    arr = np.stack([bg * 0.98, bg * 0.97, bg * 0.94], axis=2)

    cx = shot.subject_x * gate_w
    cy = getattr(shot, "subject_y", 0.66) * gate_h
    full_w = 0.10 * gate_w * shot.subject_scale * 3.0
    full_h = 0.40 * gate_h * shot.subject_scale * 3.0
    mask = subject_mask(cx, cy, full_w, full_h, xx, yy)

    # 主体：近黑；轮廓勾一圈中间调（使包围盒边缘明确、可被掩膜稳定反推）
    body_val = 26.0
    arr[mask] = np.array([body_val, body_val * 0.96, body_val * 0.9], np.float32)
    edge = mask & ~_erode(mask)
    arr[edge] = np.array([58.0, 56.0, 54.0], np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def _erode(mask):
    out = mask.copy()
    out[1:, :] &= mask[:-1, :]
    out[:-1, :] &= mask[1:, :]
    out[:, 1:] &= mask[:, :-1]
    out[:, :-1] &= mask[:, 1:]
    return out


def crop_by_window(img, crop):
    """按裁切窗裁切（纯裁切，禁止拉伸/重采样）。"""
    return img.crop((crop["x0"], crop["y0"], crop["x0"] + crop["w"], crop["y0"] + crop["h"]))


# 三画幅预演输出尺寸（保持比例，用于人眼复核；几何判定一律用原始裁切窗）
PREVIEW_SIZES = {"239": (960, 402), "169": (960, 540), "916": (405, 720)}


def make_previews(img, crops):
    out = {}
    for key in sorted(crops):
        crop = crop_by_window(img, crops[key])
        size = PREVIEW_SIZES[key]
        out[key] = crop.resize(size, Image.LANCZOS)
    return out


def draw_guides(img, shot, crop, basis_info):
    """在裁切后的代理图上画安全框与主体包围盒（仅供人工复核）。"""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img, "RGBA")
    local = {"x0": 0, "y0": 0, "w": img.size[0], "h": img.size[1]}
    for frac, col in ((basis_info["action_frac"], (60, 220, 120, 200)),
                      (basis_info["title_frac"], (240, 200, 80, 200))):
        r = geometry.safe_rect(local, frac)
        d.rectangle([r["x0"], r["y0"], r["x1"] - 1, r["y1"] - 1], outline=col, width=1)
    g = geometry.graphics_rect(local, basis_info["graphics_inset"])
    d.rectangle([g["x0"], g["y0"], g["x1"] - 1, g["y1"] - 1], outline=(120, 190, 255, 170), width=1)
    cx = int((shot.subject_x * 1920 - crop["x0"]) * img.size[0] / float(crop["w"]))
    d.line([cx, 0, cx, img.size[1]], fill=(255, 80, 80, 160), width=1)
    return img
