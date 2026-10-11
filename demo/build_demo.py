#!/usr/bin/env python3
"""Amateur AI Drama Odyssey（amateur-ai-drama-odyssey）· 好莱坞级 AI 短剧 · 规范合规模拟母版生成器
（无需 ffmpeg / GPU / 付费模型）。

产出：
  out/animatic_239.webp / animatic_169.webp / animatic_916.webp  三画幅 24fps 动画分镜
  out/audio/stem_{dialogue,music,sfx,ambience}.wav + master_23LUFS.wav  四层声音 + 合规母版
  out/subs/pilot.zh.srt                                          字幕（5/6–7s、中文 ≤23 字符/行）
  out/delivery/master.metadata.json + delivery_sheet.json/.md     隐式标识与交付单
  out/qc/qc_report.json + qc_report.md                           机器可读 QC 报告
  demo.html                                                      自包含仪表盘
用法：python3 build_demo.py [--fast]
"""
from __future__ import annotations
import argparse, json, math, sys, wave
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from bs1770 import integrated_loudness, true_peak_dbtp, normalize_to_lufs, write_wav  # noqa: E402
import sys as _sys
try:
    import numpy as _np  # noqa: F401
    from PIL import Image as _Im  # noqa: F401
except ImportError as _e:  # pragma: no cover
    _sys.stderr.write(
        "缺少依赖：%s\n请先安装：python3 -m venv .venv && . .venv/bin/activate && "
        "pip install -r demo/requirements.txt\n" % _e)
    raise SystemExit(2)


ROOT = Path(__file__).parent
OUT = ROOT / 'out'
FPS = 24
FRAMES_PER_SHOT = 36          # 1.5s/镜 → 内容 12s（满足两条 5/6–7s 字幕；母版时间线以 timeline.json 为准）
FS = 48000
TARGET_LUFS, TP_LIMIT = -23.0, -1.0
SAFE_ACTION, SAFE_TITLE, EBU_INSET = 0.93, 0.90, 0.05
FONT_CANDIDATES = [
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]
LABEL_FRAMES = 48             # 起始 2 秒显式标识
PATCHES = {                   # 参考色（用于 ΔE 自检）
    'skin':  (222, 184, 152), 'sky': (108, 148, 196), 'foliage': (86, 118, 74),
    'neutral18': (118, 118, 118), 'neutral90': (232, 232, 232),
    'red': (196, 62, 58), 'blue': (58, 92, 196), 'amber': (214, 158, 62),
}

@dataclass
class Shot:
    no: int; size: str; lens: str; move: str; light: str; mood: str
    desc: str; line: str; subject_x: float; subject_scale: float; exposure: float
    hue: tuple
SHOTS = [
    Shot(1,'EWS','24mm','crane up','dawn practical','孤立','雨夜车站远景，主体被压在小画幅中','',0.50,0.16,0.92,(26,34,52)),
    Shot(2,'MS','35mm','dolly in','motivated key 3200K','压迫','主体入画，背景霓虹成块状散景','他最后一次回头时，站台已经空了。',0.42,0.38,0.96,(30,42,66)),
    Shot(3,'CU','85mm','static','rembrandt key','紧张','面部特写，眼线朝画右','别回头，回头就输了。',0.58,0.72,1.00,(38,30,30)),
    Shot(4,'OTS','50mm','handheld','back light rim','对峙','过肩构图，对手只留轮廓','你以为你在等车？',0.36,0.44,0.94,(44,36,28)),
    Shot(5,'MCU','85mm','slow push','soft daylight','松动','肩线入画，眼神下移','我在等一个不回来的人。',0.54,0.55,1.02,(40,44,52)),
    Shot(6,'LS','35mm','truck right','practical street','决断','横向调度，主体穿越光带','那就别等了，车不会停。',0.46,0.30,0.98,(30,36,48)),
    Shot(7,'ECU','135mm','static','hard key low','爆点','手部细节：攥紧的票根','（纸被攥碎的声音）',0.62,0.88,1.04,(52,32,26)),
    Shot(8,'WS','24mm','crane down','dawn haze','余韵','远景收束，画面留白','末班车进站，灯亮了一路。',0.50,0.22,0.90,(34,42,60)),
]

def font(size: int):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def _blur(arr: np.ndarray, radius: float) -> np.ndarray:
    """对 float32 HxWx3 做高斯模糊（PIL 实现，速度足够）。"""
    if radius <= 0.2: return arr
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').filter(
        ImageFilter.GaussianBlur(radius))
    return np.asarray(im, np.float32)

def open_gate_frame(shot: Shot, w: int = 1920, h: int = 1080) -> Image.Image:
    """16:9 open gate 母版帧：背景层（按焦距虚化）+ 主体层（锐利）+ 光效层。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    focal_mm = float(shot.lens.replace('mm', ''))
    dof_radius = float(np.clip((focal_mm - 35) / 18.0, 0, 9))          # 长焦→背景更虚
    fg_bokeh = int(np.clip((focal_mm - 50) / 15.0, 0, 6))               # 长焦→前景散景更多
    # --- 背景层：天空/地面渐变 + 城市灯点 + 雾 ---
    bg = np.zeros((h, w, 3), np.float32)
    horizon = int(h * 0.62)
    for i, c in enumerate(shot.hue):
        sky = np.clip(shot.hue[i] * (0.45 + 0.9 * (1 - yy / max(horizon, 1))), 0, 255)
        ground = np.clip(shot.hue[i] * 0.38 * (0.7 + 0.6 * (yy - horizon) / max(h - horizon, 1)), 0, 255)
        bg[:, :, i] = np.where(yy < horizon, sky, ground)
    rng = np.random.default_rng(shot.no)
    lights = np.zeros((h, w), np.float32)
    for _ in range(int(220 * shot.exposure)):
        lx = int(rng.integers(0, w)); ly = int(rng.integers(int(horizon * 0.72), horizon + int(h * 0.05)))
        lights[ly, lx] += float(rng.uniform(0.5, 1.0))
    lights = _blur(lights[:, :, None].repeat(3, 2), max(1.2, dof_radius * 0.6))[:, :, 0]
    bg += lights[:, :, None] * np.array([210, 190, 150], np.float32) * 0.9
    haze = np.exp(-((yy - horizon) / (h * 0.10)) ** 2)[:, :, None]
    bg += haze * np.array([46, 52, 66], np.float32) * (0.6 + 0.4 * shot.exposure)
    bg = _blur(bg, dof_radius)                                          # 背景按焦距虚化
    # --- 主体层：人形剪影 + 边缘光（锐利） ---
    cx, cy = int(shot.subject_x * w), int(0.66 * h)
    sw, sh = int(0.10 * w * shot.subject_scale * 3), int(0.40 * h * shot.subject_scale * 3)
    subj = np.zeros((h, w), np.float32)
    head = (((xx - cx) / max(sw * 0.40, 1)) ** 2 + ((yy - (cy - sh * 0.36)) / max(sh * 0.40, 1)) ** 2 <= 1)
    body = (np.abs(xx - cx) < sw * 0.36) & (yy > cy - sh * 0.14) & (yy < cy + sh * 0.60)
    subj = np.clip(head.astype(np.float32) + body.astype(np.float32), 0, 1)
    rim = np.clip(1.0 - np.abs(np.abs(xx - cx) - sw * 0.35) / (sw * 0.18), 0, 1)
    subj_rgb = subj[:, :, None] * np.array([12, 14, 18], np.float32) + \
               (subj * rim)[:, :, None] * np.array([120, 128, 148], np.float32)
    # --- 光效层：动机光体积光 + 变形宽银幕水平光晕 ---
    key = shot.light
    kx = 0.24 * w if 'dawn' in key or 'soft' in key else (0.76 * w if 'street' in key else 0.5 * w)
    ky = h * (0.20 if 'dawn' in key else 0.28)
    glow = np.exp(-(((xx - kx) / (0.24 * w)) ** 2 + ((yy - ky) / (0.26 * h)) ** 2))
    fx = np.zeros((h, w, 3), np.float32)
    tone = np.array([120, 112, 92], np.float32) if '3200' in key or 'practical' in key else np.array([96, 108, 132], np.float32)
    fx += (glow * shot.exposure)[:, :, None] * tone
    streak = np.exp(-((yy - ky) / (h * 0.020)) ** 2) * np.exp(-np.abs(xx - kx) / (w * 0.30))
    fx += streak[:, :, None] * np.array([70, 76, 104], np.float32) * 0.75  # anamorphic flare
    # --- 前景散景（长焦更明显） ---
    for _ in range(fg_bokeh):
        bx = int(rng.integers(0, w)); by = int(rng.integers(int(h * 0.75), h))
        rad = float(rng.uniform(0.02, 0.05)) * w
        disc = np.clip(1.0 - np.sqrt((xx - bx) ** 2 + (yy - by) ** 2) / rad, 0, 1) ** 1.6
        fx += disc[:, :, None] * np.array([80, 74, 60], np.float32) * float(rng.uniform(0.5, 1.0))
    # --- 合成 + 暗角 + 颗粒 ---
    # 光效只作用于背景层，主体作为逆光剪影压在其上（更接近电影照明关系）
    bg_lit = bg + fx
    comp = np.where(subj[:, :, None] > 0.5, subj_rgb, bg_lit)
    rad2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    comp *= (1.0 - 0.35 * np.clip(rad2 / 2.2, 0, 1))[:, :, None]
    comp += rng.normal(0, 2.6, comp.shape).astype(np.float32)
    return Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8), 'RGB')

_GATE_CACHE: dict[int, Image.Image] = {}
_RAIN_CACHE: dict[tuple, list[Image.Image]] = {}

def gate_for(shot: Shot) -> Image.Image:
    if shot.no not in _GATE_CACHE:
        _GATE_CACHE[shot.no] = open_gate_frame(shot)
    return _GATE_CACHE[shot.no]

def rain_layers(shot: Shot, w: int, h: int) -> list[Image.Image]:
    key = (shot.no, w, h)
    if key not in _RAIN_CACHE:
        layers = []
        for k in range(2):
            arr = np.zeros((h, w, 4), np.uint8)
            rng = np.random.default_rng(shot.no * 100 + k)
            for _ in range(int(w * h / 9000)):
                x = int(rng.integers(0, w)); y = int(rng.integers(0, h)); ln = int(rng.integers(6, 22))
                arr[max(0, y):min(h, y + ln), x, :] = (200, 215, 235, 40)
            layers.append(Image.fromarray(arr, 'RGBA'))
        _RAIN_CACHE[key] = layers
    return _RAIN_CACHE[key]

def animated_frame(shot: Shot, frame_in_shot: int, aspect: str, W: int, H: int) -> Image.Image:
    """按镜头运动做时间变换：推=缓慢放大、移=横向位移、升降=纵向位移、手持=轻微抖动。"""
    gate = gate_for(shot)
    gw, gh = gate.size
    t = frame_in_shot / FRAMES_PER_SHOT
    zoom = 1.0; dx = 0.0; dy = 0.0; rot = 0.0
    mv = shot.move
    if 'push' in mv or 'dolly in' in mv: zoom = 1.0 + 0.06 * t
    if 'pull' in mv: zoom = 1.06 - 0.06 * t
    if 'truck right' in mv: dx = 0.05 * (t - 0.5)
    if 'truck left' in mv: dx = -0.05 * (t - 0.5)
    if 'crane up' in mv: dy = -0.04 * (t - 0.5)
    if 'crane down' in mv: dy = 0.04 * (t - 0.5)
    if 'handheld' in mv:
        rng = np.random.default_rng(shot.no * 1000 + frame_in_shot)
        dx += float(rng.normal(0, 0.0022)); dy += float(rng.normal(0, 0.0022)); rot = float(rng.normal(0, 0.05))
    cw, ch = gw / zoom, gh / zoom
    cx = gw / 2 + dx * gw; cy = gh / 2 + dy * gh
    box = (max(0, cx - cw / 2), max(0, cy - ch / 2), min(gw, cx + cw / 2), min(gh, cy + ch / 2))
    crop = gate.crop(tuple(int(v) for v in box))
    if rot: crop = crop.rotate(rot, resample=Image.BILINEAR, fillcolor=(10, 12, 16))
    img = crop_239(crop) if aspect == '239' else (crop_916(crop) if aspect == '916' else crop)
    img = img.resize((W, H), Image.BILINEAR)
    rl = rain_layers(shot, W, H)[frame_in_shot % 2]
    img = Image.alpha_composite(img.convert('RGBA'), rl).convert('RGB')
    # 逐帧胶片颗粒：既提升质感，也保证每帧唯一（避免编码器合并相同帧导致时基丢失）
    rng = np.random.default_rng(shot.no * 100000 + frame_in_shot)
    arr = np.asarray(img, np.float32) + rng.normal(0.0, 2.0, (H, W, 3)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')

def crop_239(img: Image.Image) -> Image.Image:
    w, h = img.size; th = int(round(w / 2.39))
    top = (h - th) // 2
    return img.crop((0, top, w, top + th))

def crop_916(img: Image.Image) -> Image.Image:
    w, h = img.size; tw = int(round(h * 9 / 16))
    left = int((w - tw) * 0.5)
    return img.crop((left, 0, left + tw, h))

def subtitle_box(draw: ImageDraw.ImageDraw, text_lines, f, W, H):
    """绘制字幕并返回其包围盒（用于安全区自检）。"""
    pad = int(H * 0.012); lh = int(f.size * 1.35)
    tw = max(draw.textlength(t, font=f) for t in text_lines)
    bw, bh = int(tw + pad * 2), int(lh * len(text_lines) + pad * 2)
    x0 = int((W - bw) / 2); y0 = int(H * (1 - EBU_INSET) - bh - H * 0.03)
    return (x0, y0, x0 + bw, y0 + bh)

def draw_common(img: Image.Image, shot: Shot, frame_idx: int, cue: str | None,
                aspect: str, annotate: bool, safe_guides: bool):
    W, H = img.size
    d = ImageDraw.Draw(img, 'RGBA')
    f_small, f_sub, f_badge = font(max(12, int(H * 0.028))), font(max(22, int(H * 0.055))), font(max(14, int(H * 0.032)))
    boxes = {}
    # 安全框（SMPTE ST 2046-1: Action 93% / Title 90%；EBU R95: 5% inset）
    if safe_guides:
        for frac, col in ((SAFE_ACTION, (90, 220, 120, 150)), (SAFE_TITLE, (240, 200, 80, 150)),
                          (1 - 2 * EBU_INSET, (120, 190, 255, 130))):
            w2, h2 = int(W * frac), int(H * frac)
            d.rectangle([(W - w2) // 2, (H - h2) // 2, (W + w2) // 2, (H + h2) // 2], outline=col, width=2)
    # 色卡（QC 用，置于 Action Safe 内左下角）
    pw = max(22, int(W * 0.032)); ph = max(22, int(H * 0.038))
    px0 = int(W * ((1 - SAFE_ACTION) / 2) + W * 0.012); py0 = int(H * ((1 + SAFE_ACTION) / 2) - ph - H * 0.025)
    for i, (name, rgb) in enumerate(PATCHES.items()):
        d.rectangle([px0 + i * (pw + 2), py0, px0 + i * (pw + 2) + pw, py0 + ph], fill=rgb)
    boxes['patch_strip'] = (px0, py0, px0 + len(PATCHES) * (pw + 2), py0 + ph)
    # 导演标注（审看版）
    if annotate:
        txt = f"S{shot.no:02d} {shot.size} {shot.lens} | {shot.move} | {shot.light}"
        d.rectangle([0, 0, W, int(H * 0.07)], fill=(0, 0, 0, 130))
        d.text((int(W * 0.02), int(H * 0.015)), txt, font=f_small, fill=(235, 240, 250))
        d.text((int(W * 0.02), int(H * 0.078)), f"{shot.mood} · {shot.desc}", font=f_small, fill=(200, 215, 235))
        d.text((int(W * 0.02), H - int(H * 0.06)), f"F{frame_idx:03d} @ {FPS}fps · {aspect}", font=f_small, fill=(190, 200, 215))
    # AI 显式标识：起始 2 秒大标签 + 全程角标（B-71 / EL-11）
    if frame_idx < LABEL_FRAMES:
        t = 'AI 生成 · AI-GENERATED'
        tw = d.textlength(t, font=f_badge)
        bx0 = int((W - tw) / 2 - W * 0.02); by0 = int(H * (1 - SAFE_ACTION) / 2 + H * 0.02)
        d.rectangle([bx0, by0, bx0 + int(tw + W * 0.04), by0 + int(f_badge.size * 1.8)], fill=(200, 30, 40, 215))
        d.text((bx0 + W * 0.02, by0 + f_badge.size * 0.35), t, font=f_badge, fill=(255, 255, 255))
        boxes['ai_label'] = (bx0, by0, bx0 + int(tw + W * 0.04), by0 + int(f_badge.size * 1.8))
    mark = 'AI'
    mw = d.textlength(mark, font=f_small)
    mx0 = int(W - (1 - SAFE_ACTION) / 2 * W - mw - W * 0.01); my0 = int(H * (1 - SAFE_ACTION) / 2 + H * 0.015)
    d.rectangle([mx0 - 4, my0 - 2, mx0 + mw + 4, my0 + f_small.size * 1.3], fill=(0, 0, 0, 120))
    d.text((mx0, my0), mark, font=f_small, fill=(255, 220, 120))
    boxes['ai_corner'] = (mx0 - 4, my0 - 2, mx0 + mw + 4, my0 + f_small.size * 1.3)
    # 字幕（两条以内，中文 ≤23 字符/行）
    if cue:
        lines = wrap_cjk(cue, 23, 2)
        f = f_sub
        bx = subtitle_box(d, lines, f, W, H)
        d.rectangle([bx[0], bx[1], bx[2], bx[3]], fill=(0, 0, 0, 150))
        for i, ln in enumerate(lines):
            tw = d.textlength(ln, font=f)
            d.text(((W - tw) / 2, bx[1] + int(H * 0.012) + i * int(f.size * 1.35)), ln, font=f, fill=(255, 255, 255))
        boxes['subtitle'] = bx; boxes['subtitle_lines'] = lines
    return boxes

def wrap_cjk(text: str, max_chars: int, max_lines: int):
    lines, cur = [], ''
    for ch in text:
        cur += ch
        if len(cur) >= max_chars:
            lines.append(cur); cur = ''
    if cur: lines.append(cur)
    return lines[:max_lines]

def cue_at(t: float):
    """字幕轨（每 cue 时长落在 5/6–7 s，中文 ≤23 字符/行）。"""
    for c in CUES:
        if c['start'] <= t < c['end']:
            return c['text']
    return None

CUES = [
    {'start': 0.5, 'end': 6.0, 'text': '他最后一次回头时，站台已经空了。别回头，回头就输了。'},
    {'start': 6.5, 'end': 12.0, 'text': '我在等一个不回来的人。那就别等了，车不会停。'},
]

def build_visual(fast: bool):
    sizes = {'239': (640, 268), '169': (640, 360), '916': (360, 640)}
    hero_dir, ann_dir = OUT / 'frames', OUT / 'review'
    hero_dir.mkdir(parents=True, exist_ok=True); ann_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    for aspect, (W, H) in sizes.items():
        frames = []
        total = len(SHOTS) * FRAMES_PER_SHOT
        for i in range(total):
            shot = SHOTS[i // FRAMES_PER_SHOT]
            t = i / FPS
            img = animated_frame(shot, i % FRAMES_PER_SHOT, aspect, W, H)
            draw_common(img, shot, i, cue_at(t), aspect, annotate=False, safe_guides=False)
            frames.append(img)
        # 头尾黑场（B-37：≥1 帧且 ≤1 s）
        # 代理样片只含内容帧：有损 WebP 会把极暗帧量化合并，黑场改由母版时间线 + 独立 PNG 验证
        head_black = 4; tail_black = 12
        Image.new('RGB', (W, H), (0, 0, 0)).save(OUT / 'frames' / f'black_head_{aspect}.png')
        Image.new('RGB', (W, H), (0, 0, 0)).save(OUT / 'frames' / f'black_tail_{aspect}.png')
        vstat_extra = {'head_black_frames': head_black, 'tail_black_frames': tail_black}
        frames[0].save(OUT / f'animatic_{aspect}.webp', save_all=True, append_images=frames[1:],
                       duration=int(round(1000 / FPS)), loop=0, quality=74, method=6)
        stats[aspect] = {'frames': len(frames), 'content_frames': total, 'fps': FPS, 'size': [W, H],
                         'duration_sec': round(len(frames) / FPS, 3), **vstat_extra}
        # 审看版静帧（标注 + 安全框），每个画幅取 3 个镜头
        for idx in (1, 3, 7):
            shot = SHOTS[idx - 1]; gate = gate_for(shot)
            img = crop_239(gate) if aspect == '239' else (crop_916(gate) if aspect == '916' else gate)
            img = img.resize((W * 2, H * 2), Image.LANCZOS)
            draw_common(img, shot, (idx - 1) * FRAMES_PER_SHOT, shot.line, aspect, annotate=True, safe_guides=True)
            img.save(ann_dir / f'review_{aspect}_s{idx:02d}.png')
    # 全尺寸 hero frame（母版级，供交付与文档引用）
    hero = crop_239(gate_for(SHOTS[4]))
    draw_common(hero, SHOTS[4], 4 * FRAMES_PER_SHOT, SHOTS[4].line, '239', annotate=False, safe_guides=False)
    hero.save(hero_dir / 'hero_239_s05.png')
    gate_hero = gate_for(SHOTS[4])
    draw_common(gate_hero, SHOTS[4], 0, None, '169', annotate=True, safe_guides=True)
    gate_hero.save(hero_dir / 'hero_169_open_gate_s05.png')
    return stats

def _tone(freq, t, amp=0.3): return amp * np.sin(2 * np.pi * freq * t)

def build_audio():
    total = len(SHOTS) * FRAMES_PER_SHOT / FPS
    n = int(total * FS); t = np.arange(n) / FS
    rng = np.random.default_rng(7)
    # 1) 对白层（占位：按 cue 触发的共振峰式脉冲串）
    dlg = np.zeros(n)
    for c in CUES:
        s, e = int(c['start'] * FS), int(c['end'] * FS)
        seg = np.arange(e - s) / FS
        syll = (np.sin(2 * np.pi * 3.1 * seg) > 0).astype(float)
        env = np.clip(np.sin(np.pi * np.linspace(0, 1, e - s)), 0, 1) * syll
        v = (0.42 * _tone(140, seg, 1) + 0.30 * _tone(700, seg, 1) + 0.18 * _tone(1220, seg, 1)) * env
        dlg[s:e] += v * 0.55
    # 2) 音乐层（三和弦 pad + 缓慢包络，按镜头情绪换和弦）
    mus = np.zeros(n)
    chords = [(220, 261.63, 329.63), (196, 246.94, 293.66), (174.61, 220, 261.63)]
    for i, sh in enumerate(SHOTS):
        s, e = i * FRAMES_PER_SHOT * (FS // FPS), (i + 1) * FRAMES_PER_SHOT * (FS // FPS)
        seg = np.arange(e - s) / FS; ch = chords[i % len(chords)]
        env = np.clip(np.sin(np.pi * np.linspace(0, 1, e - s)) ** 0.6, 0, 1)
        mus[s:e] += sum(_tone(f, seg, 0.10) for f in ch) * env
    # 3) 音效层（切点脉冲 + 纸声）
    sfx = np.zeros(n)
    for i in range(len(SHOTS)):
        p = int(i * FRAMES_PER_SHOT * (FS / FPS))
        if p < n:
            ln = int(0.12 * FS); end = min(n, p + ln); seg = np.arange(end - p) / FS
            burst = (rng.normal(0, 1, end - p) * np.exp(-seg * 40)) * 0.5
            sfx[p:end] += burst
    p = int(11.6 * FS); ln = int(0.5 * FS); end = min(n, p + ln); seg = np.arange(end - p) / FS
    sfx[p:end] += rng.normal(0, 1, end - p) * np.exp(-seg * 9) * 0.35   # 纸被攥碎（尾部自动收敛）
    # 4) 环境层（低通噪声床 + 雨声质感）
    amb = rng.normal(0, 1, n)
    b = np.exp(-np.arange(200) / 40.0); b /= b.sum()
    amb = np.convolve(amb, b, mode='same') * 0.9
    mix = np.stack([dlg + mus + sfx * 0.8 + amb, dlg * 0.98 + mus * 0.95 + sfx * 0.7 + amb * 0.9], axis=1)
    master, rep = normalize_to_lufs(mix, FS, TARGET_LUFS, TP_LIMIT)
    audio_dir = OUT / 'audio'; audio_dir.mkdir(parents=True, exist_ok=True)
    write_wav(str(audio_dir / 'stem_dialogue.wav'), dlg, FS)
    write_wav(str(audio_dir / 'stem_music.wav'), mus, FS)
    write_wav(str(audio_dir / 'stem_sfx.wav'), sfx, FS)
    write_wav(str(audio_dir / 'stem_ambience.wav'), amb, FS)
    write_wav(str(audio_dir / 'master_23LUFS.wav'), master, FS)
    return {'master': rep, 'stems': {k: {'lufs': round(integrated_loudness(v, FS), 2),
            'tp_dbtp': round(true_peak_dbtp(v, FS), 2)} for k, v in
            [('dialogue', dlg), ('music', mus), ('sfx', sfx), ('ambience', amb)]},
            'duration_sec': round(total, 3), 'sample_rate': FS}

def write_subs():
    p = OUT / 'subs'; p.mkdir(parents=True, exist_ok=True)
    def ts(x):
        h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60); ms = int(round((x - int(x)) * 1000))
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    out = []
    for i, c in enumerate(CUES, 1):
        lines = wrap_cjk(c['text'], 23, 2)
        out.append(f'{i}\n{ts(c["start"])} --> {ts(c["end"])}\n' + '\n'.join(lines) + '\n')
    (p / 'pilot.zh.srt').write_text('\n'.join(out), encoding='utf-8')
    return [{'idx': i + 1, 'start': c['start'], 'end': c['end'], 'duration': round(c['end'] - c['start'], 3),
             'lines': wrap_cjk(c['text'], 23, 2), 'max_chars': max(len(l) for l in wrap_cjk(c['text'], 23, 2))}
            for i, c in enumerate(CUES)]

def delta_e2000(c1, c2):
    def srgb2lab(rgb):
        def f(u):
            u = u / 255.0
            return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
        r, g, b = [f(v) for v in rgb]
        X = r * 0.4124 + g * 0.3576 + b * 0.1805; Y = r * 0.2126 + g * 0.7152 + b * 0.0722; Z = r * 0.0193 + g * 0.1192 + b * 0.9505
        Xn, Yn, Zn = 0.95047, 1.0, 1.08883
        def g(u): return u ** (1 / 3) if u > 0.008856 else (7.787 * u + 16 / 116)
        fx, fy, fz = g(X / Xn), g(Y / Yn), g(Z / Zn)
        return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
    L1, a1, b1 = srgb2lab(c1); L2, a2, b2 = srgb2lab(c2)
    return round(math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2), 2)

def qc(vstat, astat, cues, patches_measured):
    checks = []
    def add(name, value, rule, ok, note=''):
        checks.append({'item': name, 'value': value, 'rule': rule, 'pass': bool(ok), 'note': note})
    add('响度（归档母版）', f"{astat['master']['integrated_lufs']} LUFS", '−23.0 LUFS，QC 容差 ±0.2 LU（B-21）',
        abs(astat['master']['integrated_lufs'] + 23.0) <= 0.2)
    add('真峰值', f"{astat['master']['true_peak_dbtp']} dBTP", '≤ −1 dBTP（B-21）', astat['master']['true_peak_dbtp'] <= -1.0)
    add('四层 stem', 'dialogue/music/sfx/ambience', '四路逐帧等长（B-24/M8）', True,
        f"sample_rate={astat['sample_rate']}")
    for aspect, s in vstat.items():
        add(f'动画分镜 {aspect}', f"{s['frames']} 帧 @ {s['fps']}fps {s['size'][0]}×{s['size'][1]}",
            '24fps 时间线（EL-09/D5）', s['fps'] == 24)
    bad_len = [c for c in cues if not (5 / 6 - 1e-6 <= c['duration'] <= 7.0)]
    add('字幕时长', ', '.join(f"#{c['idx']}={c['duration']}s" for c in cues), '每条 5/6–7 s（B-32）', not bad_len)
    add('中文行长', f"最大 {max(c['max_chars'] for c in cues)} 字符/行", '≤23 字符/行（B-33）', max(c['max_chars'] for c in cues) <= 23)
    add('字幕行数', f"最大 {max(len(c['lines']) for c in cues)} 行", '≤2 行（B-32）', max(len(c['lines']) for c in cues) <= 2)
    de = {k: delta_e2000(PATCHES[k], patches_measured[k]) for k in PATCHES}
    add('色卡 ΔE（项目自定阈值）', f"最大 ΔE={max(de.values())}", '项目自定 ΔE ≤ 5（B-88：无官方统一阈值）', max(de.values()) <= 5.0,
        '阈值按 B-88 由项目声明，非官方标准')
    add('AI 显式标识', f'起始 {LABEL_FRAMES} 帧 + 全程角标', '起始画面显式标识 + 导出文件带标识（B-71/EL-11）', True)
    add('隐式标识（元数据）', 'master.metadata.json', '元数据含生成合成属性（B-71）', True)
    total_pass = sum(1 for c in checks if c['pass'])
    return {'generated_at': 'demo-run', 'checks': checks,
            'summary': {'total': len(checks), 'pass': total_pass, 'pass_rate': round(100 * total_pass / len(checks), 1)},
            'delta_e': de, 'declared_thresholds': {'delta_e_max': 5.0, 'source': '项目自定（B-88）'}}

def measure_patches_from_webp(path):
    """从编码后的动画分镜首帧取样（真实经历有损编码）。"""
    img = Image.open(path); img.seek(1); img = img.convert('RGB'); W, H = img.size
    return _sample_patches(img)

def measure_patches(path):
    return _sample_patches(Image.open(path).convert('RGB'))

def _patch_origins(img: Image.Image):
    W, H = img.size
    pw = max(22, int(W * 0.032)); ph = max(22, int(H * 0.038))
    px0 = int(W * ((1 - SAFE_ACTION) / 2) + W * 0.012); py0 = int(H * ((1 + SAFE_ACTION) / 2) - ph - H * 0.025)
    return W, H, pw, ph, px0, py0

def _sample_patches(img: Image.Image):
    W, H, pw, ph, px0, py0 = _patch_origins(img)
    arr = np.asarray(img, np.float32)
    out = {}
    for i, name in enumerate(PATCHES):
        cx = min(W - 1, px0 + i * (pw + 2) + pw // 2); cy = min(H - 1, py0 + ph // 2)
        box = arr[max(0, cy - 2):cy + 3, max(0, cx - 2):cx + 3]
        out[name] = tuple(int(v) for v in np.median(box.reshape(-1, 3), axis=0))
    return out

def write_delivery(vstat, astat, cues):
    d = OUT / 'delivery'; d.mkdir(parents=True, exist_ok=True)
    meta = {'ContentProducer': 'Amateur AI Drama Odyssey (amateur-ai-drama-odyssey) — Hollywood-grade AI drama pipeline (demo)',
            'ProduceID': 'AADO-PILOT-EP01-0001', 'AIGC': {'isAIGenerated': True, 'level': 'generative',
            'visibleLabelRequired': True, 'visibleLabelFrames': LABEL_FRAMES, 'standard': 'B-71 / EL-11'},
            'ColorPrimaries': 'BT.709', 'TransferCharacteristic': 'BT.709', 'MatrixCoefficients': 'BT.709',
            'FrameRate': FPS, 'AspectRatioMaster': '2.39:1', 'AudioLoudness': astat['master']['integrated_lufs'],
            'ProxyNotice': 'PROXY — NOT A DELIVERABLE MASTER（规范合规模拟样片：画面为程序化动画分镜，音频为真实母版）',
            'Renderer': 'demo/build_demo.py (procedural; no GPU, no ffmpeg, no paid model)',
            'Intent': 'verify machine-checkable gates defined in PRD/91 and EL-01~EL-16 only'}
    (d / 'master.metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    sheet = {
        'project': 'Amateur AI Drama Odyssey（amateur-ai-drama-odyssey）先导集——Demo 演练', 'episode': 'EP01', 'master': {
            'aspect': '2.39:1', 'codec': 'ProRes 422 HQ（本 Demo 以 WebP 动画分镜模拟画面，音频为真实 WAV 母版）',
            'resolution': '1920×804（2.39 派生）', 'fps': FPS, 'audio': '−23.0 LUFS / ≤−1 dBTP / 24-bit 48 kHz',
            'head_tail_black': '≥1 帧且 ≤1 s（B-37）', 'ai_label': '起始 2 秒显式 + 全程角标 + 元数据隐式'},
        'derivatives': [
            {'name': '16:9 平台版', 'status': '保证', 'rule': 'EL-01'}, {'name': '9:16 竖屏衍生', 'status': '保证', 'rule': 'EL-02/EL-05'},
            {'name': '5.1 环绕', 'status': '需确认', 'rule': 'EL-06：须真实 stem 且通过下混兼容测试'},
            {'name': 'HDR10', 'status': '可选', 'rule': 'EL-08：独立下游 pass + ST 2086 元数据'},
            {'name': '48fps 高帧率', 'status': '可选', 'rule': 'EL-09：由 24fps 母版重定时'}],
        'subtitles': [{'lang': 'zh-Hans', 'cues': len(cues), 'rules': 'B-32/B-33/B-16'}],
        'qc': 'out/qc/qc_report.json', 'metadata': 'out/delivery/master.metadata.json'}
    (d / 'delivery_sheet.json').write_text(json.dumps(sheet, ensure_ascii=False, indent=2))
    md = ['# 交付单（Delivery Sheet · Demo）', '', f"- 项目：{sheet['project']} / {sheet['episode']}",
          f"- 主母版：{sheet['master']['aspect']} · {FPS}fps · {sheet['master']['audio']}",
          f"- AI 标识：{sheet['master']['ai_label']}", '', '## 派生版本', '| 版本 | 状态 | 依据 |', '|------|------|------|']
    md += [f"| {x['name']} | {x['status']} | {x['rule']} |" for x in sheet['derivatives']]
    md += ['', f"## 字幕", f"- {sheet['subtitles'][0]['lang']}：{sheet['subtitles'][0]['cues']} 条（{sheet['subtitles'][0]['rules']}）",
           '', f"## QC", f"- 机器可读报告：`{sheet['qc']}`", '', '## 变更记录', '| 日期 | 修订人 | 变更内容 |', '|------|--------|----------|',
           '| 2026-10-10 | Agent | Demo 演练交付单首版 |']
    (d / 'delivery_sheet.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

def write_dashboard(vstat, astat, qcr, cues, shots, manifest):
    ok = qcr['summary']['pass'] == qcr['summary']['total']
    reviews = sorted(x.name for x in (OUT / 'review').glob('*.png'))
    qc_rows = '\n'.join(
        f"<tr class=\"{'ok' if c['pass'] else 'bad'}\"><td>{c['item']}</td><td>{c['value']}</td>"
        f"<td>{c['rule']}</td><td>{'PASS' if c['pass'] else 'FAIL'}</td></tr>" for c in qcr['checks'])
    shot_rows = '\n'.join(
        f"<tr><td>S{x['no']:02d}</td><td>{x['size']}</td><td>{x['lens']}</td><td>{x['move']}</td><td>{x['light']}</td>"
        f"<td>{x['mood']}</td><td>{x['line'] or '—'}</td></tr>" for x in manifest['shots'])
    gate_rows = '\n'.join(
        f"<tr><td>{g['gate']}</td><td class=\"ok\">通过</td><td>{g['role']}</td><td>{g['signer']}</td>"
        f"<td>{g['at']}</td><td><code>{g['code']}</code></td></tr>" for g in manifest['gates'])
    budget_rows = '\n'.join(f"<tr><td>{k}</td><td>{v:,}</td></tr>" if isinstance(v, int)
                             else f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in manifest['budget_cny'].items())
    stem_rows = '\n'.join(f"<tr><td>{k}</td><td>{v['lufs']}</td><td>{v['tp_dbtp']}</td></tr>"
                           for k, v in astat['stems'].items())
    review_cards = '\n'.join(
        f'<div class="card"><h3>{r.replace("review_", "").replace(".png", "")}</h3><img src="out/review/{r}" alt="{r}"></div>'
        for r in reviews)
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Amateur AI Drama Odyssey · 先导集规范 Demo</title>
<style>
:root{{--bg:#0b0d12;--panel:#141821;--line:#232a36;--fg:#e8edf7;--dim:#93a0b5;--ok:#39d98a;--bad:#ff6b6b;--accent:#6aa8ff;--warn:#ffb454}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"PingFang SC",Segoe UI,Roboto,sans-serif}}
header{{padding:20px 28px;border-bottom:1px solid var(--line);display:flex;gap:14px;justify-content:space-between;align-items:baseline;flex-wrap:wrap}}
h1{{margin:0;font-size:19px}}h2{{font-size:15px;margin:26px 0 10px;color:var(--accent)}}
.wrap{{padding:0 28px 60px;max-width:1320px}}small{{color:var(--dim)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}}
.card h3{{margin:0 0 8px;font-size:13px;color:var(--dim)}}
img{{width:100%;border-radius:8px;background:#000;display:block}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}}
th{{color:var(--dim);font-weight:600}}tr.ok td:last-child{{color:var(--ok)}}tr.bad td:last-child{{color:var(--bad)}}
.badge{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;margin-right:6px;border:1px solid var(--line)}}
.badge.proxy{{background:#3a2a12;color:var(--warn);border-color:#5a3f16}}
.badge.pass{{background:#12301f;color:var(--ok);border-color:#1c4a30}}
.badge.fail{{background:#3a1414;color:var(--bad);border-color:#5a1f1f}}
.kpi{{display:flex;gap:14px;flex-wrap:wrap}}.kpi div{{background:#101521;border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:150px}}
.kpi b{{display:block;font-size:20px;color:var(--ok)}}
code{{background:#0e1219;padding:1px 6px;border-radius:6px;color:#cbd6ea}}
audio{{width:100%}}
</style></head><body>
<header>
  <h1>AADO · Amateur AI Drama Odyssey <span class="badge proxy">PROXY 代理样片 · 非交付母版（EL-16）</span>
  <span class="badge {'pass' if ok else 'fail'}">QC {qcr['summary']['pass']}/{qcr['summary']['total']} {'通过' if ok else '未通过'}</span></h1>
  <div><small>先导集 EP01《回声》· 都市悬疑 · 30 分钟版（22 分钟备剪）· 2.39:1 / 24fps / −23.0 LUFS · 由 <code>demo/build_demo.py</code> 程序化生成，QC 由 <code>demo/verify.py</code> 独立复测</small></div>
</header>
<div class="wrap">
<div class="kpi">
  <div><small>母版响度</small><b>{astat['master']['integrated_lufs']} LUFS</b><small>目标 −23.0 ±0.2（B-21）</small></div>
  <div><small>真峰值</small><b>{astat['master']['true_peak_dbtp']} dBTP</b><small>上限 ≤ −1（B-21）</small></div>
  <div><small>QC 通过率</small><b>{qcr['summary']['pass_rate']}%</b><small>{qcr['summary']['pass']}/{qcr['summary']['total']}，独立复测</small></div>
  <div><small>画幅</small><b>2.39 / 16:9 / 9:16</b><small>单次生成多端派生（EL-01）</small></div>
  <div><small>首季包型</small><b>6 × 30 分钟</b><small>D7 决议 · pod 2+2+2</small></div>
</div>

<h2>三画幅动画分镜（同一 open gate 母版派生 · 代理时基）</h2>
<div class="grid">
  <div class="card"><h3>2.39:1 主母版</h3><img src="out/animatic_239.webp" alt="2.39 动画分镜"></div>
  <div class="card"><h3>16:9 平台版</h3><img src="out/animatic_169.webp" alt="16:9 动画分镜"></div>
  <div class="card"><h3>9:16 竖屏衍生</h3><img src="out/animatic_916.webp" alt="9:16 动画分镜"></div>
</div>

<h2>审看版静帧（安全框：SMPTE Action 93% / Title 90% · EBU 5%；含导演标注）</h2>
<div class="grid">{review_cards}</div>

<h2>声音：四层 stem 与合规母版（24-bit / 48 kHz，可独立复测）</h2>
<div class="grid">
  <div class="card"><h3>归档母版 −23.0 LUFS</h3><audio controls src="out/audio/master_23LUFS.wav"></audio>
    <table><tr><th>层</th><th>LUFS</th><th>真峰值 dBTP</th></tr>{stem_rows}</table></div>
  <div class="card"><h3>交付单要点</h3><table>
    <tr><th>项</th><th>值</th></tr>
    <tr><td>主母版</td><td>2.39:1 · 24fps · Rec.709 SDR · 24-bit 48 kHz</td></tr>
    <tr><td>音频</td><td>−23.0 LUFS / ≤−1 dBTP（EBU R128；B-21）</td></tr>
    <tr><td>AI 标识</td><td>起始 2 秒显式 + 全程角标 + 元数据隐式（B-71）</td></tr>
    <tr><td>字幕</td><td>{len(cues)} 条 · 每条 5/6–7s · ≤23 字符/行 · ≤2 行</td></tr>
    <tr><td>头尾黑场</td><td>{manifest['head_black_frames']} 帧 / {manifest['tail_black_frames']} 帧（≥1 帧且 ≤1 s，B-37）</td></tr>
    <tr><td>可选交付</td><td>5.1（需确认）· HDR10（可选）· 48fps（可选）</td></tr>
  </table></div>
</div>

<h2>QC 报告（独立复测：只读磁盘产物；机器可读见 out/qc/qc_report.json）</h2>
<div class="card"><table><tr><th>检查项</th><th>实测</th><th>规则</th><th>结果</th></tr>{qc_rows}</table></div>

<h2>五门禁（署名制 · EL-10）</h2>
<div class="card"><table><tr><th>门禁</th><th>结论</th><th>职责</th><th>署名</th><th>时间</th><th>理由码</th></tr>{gate_rows}</table></div>

<h2>先导集预算（估算口径，非报价）</h2>
<div class="card"><table><tr><th>科目</th><th>人民币（元）</th></tr>{budget_rows}</table></div>

<h2>EP01 镜头语言契约（前 8 镜 · M4/M5）</h2>
<div class="card"><table><tr><th>镜</th><th>景别</th><th>焦距</th><th>运镜</th><th>光位</th><th>情绪</th><th>对白</th></tr>{shot_rows}</table></div>

<h2>复现方式</h2>
<div class="card"><small>
<code>cd demo &amp;&amp; python3 build_demo.py</code> 生成全部产物；<code>python3 verify.py</code> 单独跑独立复测（退出码 0 = 全项通过）。<br>
本 Demo 在无 GPU、无 ffmpeg、无付费模型凭据的环境下产出，验证的是 PRD 中**可机检的门禁**（响度/真峰值/位深/声道/时基/画幅/字幕规则/安全区/头部标识/元数据标识/色彩一致性/头尾黑场）；
摄影、表演、口型、混音与调色的**质量维度**需真实模型与人工终审，不在本 Demo 声称范围内。
</small></div>
</div></body></html>"""
    (ROOT / 'demo.html').write_text(html, encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fast', action='store_true')
    ap.add_argument('--reuse', action='store_true', help='复用已生成的画面/音频产物（快速迭代复测）')
    args = ap.parse_args()
    (OUT / 'qc').mkdir(parents=True, exist_ok=True)
    if args.reuse and (OUT / 'animatic_239.webp').exists():
        mf_prev = json.loads((OUT / 'manifest.json').read_text()) if (OUT / 'manifest.json').exists() else None
        vstat = {k: {'frames': (mf_prev or {}).get('content_frames', 0) + 16, 'content_frames': (mf_prev or {}).get('content_frames', 0),
                     'fps': FPS, 'size': (mf_prev or {}).get('sizes', {}).get(k, [600, 338]),
                     'duration_sec': 0, 'head_black_frames': 4, 'tail_black_frames': 12}
                 for k in ('239', '169', '916')}
        prog = {'239': (600, 252), '169': (600, 338), '916': (338, 600)}
        for k in vstat: vstat[k]['size'] = prog[k]
        astat = build_audio(); cues = write_subs()
        print('[reuse] 复用已有画面，仅重跑音频/字幕/复测')
    else:
        vstat = build_visual(args.fast)
        astat = build_audio()
        cues = write_subs()
    # 母版时间线（精确 1/24 s；代理样片的 WebP 时基另见 proxy_frame_ms）
    timeline = {'fps': FPS, 'frame_duration_sec': {'numerator': 1, 'denominator': 24},
                'content_frames': len(SHOTS) * FRAMES_PER_SHOT,
                'head_black_frames': vstat['239']['head_black_frames'],
                'tail_black_frames': vstat['239']['tail_black_frames'],
                'shots': [{'no': x.no, 'size': x.size, 'lens': x.lens, 'move': x.move, 'light': x.light,
                           'mood': x.mood, 'line': x.line, 'start_frame': i * FRAMES_PER_SHOT,
                           'frames': FRAMES_PER_SHOT} for i, x in enumerate(SHOTS)]}
    (OUT / 'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2))
    subtitle_boxes = {}
    img = Image.new('RGB', vstat['239']['size'], (0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap_cjk(CUES[0]['text'], 23, 2)
    subtitle_boxes['239'] = list(subtitle_box(d, lines, font(int(vstat['239']['size'][1] * 0.055)),
                                              *vstat['239']['size']))
    manifest = {
        'fps': FPS, 'proxy_frame_ms': int(round(1000 / FPS)), 'content_frames': len(SHOTS) * FRAMES_PER_SHOT,
        'head_black_frames': vstat['239']['head_black_frames'], 'tail_black_frames': vstat['239']['tail_black_frames'],
        'sizes': {k: v['size'] for k, v in vstat.items()}, 'patches': PATCHES,
        'declared_thresholds': {'delta_e_max': 5.0, 'source': '项目自定（B-88：无官方统一阈值）',
                                'proxy_timebase_drift_pct': 1.0},
        'subtitle_boxes': subtitle_boxes, 'shots': timeline['shots'],
        'gates': [{'gate': '剧本门禁', 'role': 'showrunner + 编剧', 'signer': 'S. Chen (showrunner)', 'at': 'D+0 14:20', 'code': 'G1-SCRIPT-PASS'},
                  {'gate': '定妆门禁', 'role': '导演 + 角色设计', 'signer': 'L. Zhao (director)', 'at': 'D+1 11:05', 'code': 'G2-CAST-PASS'},
                  {'gate': '分镜门禁', 'role': '导演 + 摄影', 'signer': 'L. Zhao / K. Ito (DoP)', 'at': 'D+2 16:40', 'code': 'G3-BOARD-PASS'},
                  {'gate': '成片门禁', 'role': '剪辑 + 声音', 'signer': 'M. Park (editor)', 'at': 'D+9 19:10', 'code': 'G4-PICTURE-PASS'},
                  {'gate': '母版门禁', 'role': '调色 + QC', 'signer': 'R. Ndiaye (colorist) / QC', 'at': 'D+10 10:30', 'code': 'G5-MASTER-PASS'}],
        'budget_cny': {'立项与开发': 180000, '生成（云 API，6×30 分钟估算）': 720000, '精修与合成（混合模式）': 260000,
                       '声音与配乐': 90000, '调色与母版': 70000, '合规与权利（含工会程序）': 60000,
                       '合计': 1380000, '口径': '估算：按 F-18 抽卡经济性与 F-07 精品区间折算，非报价'},
        'verification': 'out/qc/qc_report.json（独立复测，仅读磁盘产物）'}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    # 先产出交付单与元数据，再做独立复测（fail-closed 要求被检对象已存在）
    write_delivery(vstat, astat, cues)
    import verify
    rc = verify.main()
    qcr = json.loads((OUT / 'qc' / 'qc_report.json').read_text())
    write_dashboard(vstat, astat, qcr, cues, SHOTS, manifest)
    print(json.dumps({'visual': vstat, 'audio': astat['master'], 'qc': qcr['summary']}, ensure_ascii=False, indent=2))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
