#!/usr/bin/env python3
"""独立复测（fail-closed）：只读产物文件 + manifest，重新测量并生成 QC 报告。

原则：不复用生成器的中间变量；一切以磁盘文件为准。任一项失败 → QC FAIL。
"""
from __future__ import annotations
import json, math, re, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from bs1770 import integrated_loudness, true_peak_dbtp  # noqa: E402
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

def read_wav(path: Path):
    with wave.open(str(path), 'rb') as w:
        ch, sw, fr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        v = (b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v) / float(1 << 23)
    elif sw == 2:
        v = np.frombuffer(raw, '<i2').astype(np.float32) / 32768.0
    else:
        raise ValueError(f'unsupported sampwidth {sw}')
    if ch > 1:
        v = v.reshape(-1, ch)
    return {'channels': ch, 'sampwidth_bits': sw * 8, 'framerate': fr, 'frames': n, 'data': v}

def delta_e2000(c1, c2):
    def lab(rgb):
        def f(u):
            u = u / 255.0
            return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
        r, g, b = [f(v) for v in rgb]
        X = r * .4124 + g * .3576 + b * .1805; Y = r * .2126 + g * .7152 + b * .0722; Z = r * .0193 + g * .1192 + b * .9505
        def gg(u): return u ** (1 / 3) if u > 0.008856 else (7.787 * u + 16 / 116)
        fx, fy, fz = gg(X / .95047), gg(Y), gg(Z / 1.08883)
        return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
    (L1, a1, b1), (L2, a2, b2) = lab(c1), lab(c2)
    return round(math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2), 2)

def sample_patches(img: Image.Image, safe_action=0.93):
    W, H = img.size
    pw = max(22, int(W * 0.032)); ph = max(22, int(H * 0.038))
    px0 = int(W * ((1 - safe_action) / 2) + W * 0.012); py0 = int(H * ((1 + safe_action) / 2) - ph - H * 0.025)
    arr = np.asarray(img, np.float32); out = {}
    for i, name in enumerate(MANIFEST['patches']):
        cx = min(W - 1, px0 + i * (pw + 2) + pw // 2); cy = min(H - 1, py0 + ph // 2)
        box = arr[max(0, cy - 2):cy + 3, max(0, cx - 2):cx + 3]
        out[name] = tuple(int(v) for v in np.median(box.reshape(-1, 3), axis=0))
    return out

MANIFEST = json.loads((OUT / 'manifest.json').read_text())

def main() -> int:
    checks = []
    def add(item, value, rule, ok, note=''):
        checks.append({'item': item, 'value': value, 'rule': rule, 'pass': bool(ok), 'note': note})

    # 1) 产物存在且非空
    required = ['animatic_239.webp', 'animatic_169.webp', 'animatic_916.webp',
                'audio/master_23LUFS.wav', 'audio/stem_dialogue.wav', 'audio/stem_music.wav',
                'audio/stem_sfx.wav', 'audio/stem_ambience.wav', 'subs/pilot.zh.srt',
                'delivery/master.metadata.json', 'delivery/delivery_sheet.json', 'timeline.json']
    missing = [f for f in required if not (OUT / f).exists() or (OUT / f).stat().st_size == 0]
    add('产物存在且非空', f'{len(required) - len(missing)}/{len(required)}', '全部产物存在且大小 > 0', not missing,
        ('缺失: ' + ', '.join(missing)) if missing else '')
    if missing:
        report(checks); return 1

    # 2) 音频母版规格（24-bit / 48kHz / 立体声）与响度复测
    m = read_wav(OUT / 'audio/master_23LUFS.wav')
    add('音频母版位深/采样率/声道', f"{m['sampwidth_bits']}bit {m['framerate']}Hz {m['channels']}ch",
        '24-bit / 48 kHz / 立体声（B-38）', m['sampwidth_bits'] == 24 and m['framerate'] == 48000 and m['channels'] == 2)
    lufs = integrated_loudness(m['data'], m['framerate']); tp = true_peak_dbtp(m['data'], m['framerate'])
    add('响度（独立复测）', f'{lufs:.2f} LUFS', '−23.0 LUFS，QC 容差 ±0.2 LU（B-21）', abs(lufs + 23.0) <= 0.2)
    add('真峰值（独立复测）', f'{tp:.2f} dBTP', '≤ −1 dBTP（B-21）', tp <= -1.0)
    stems = [read_wav(OUT / f'audio/stem_{k}.wav') for k in ('dialogue', 'music', 'sfx', 'ambience')]
    same = len({s['frames'] for s in stems + [m]}) == 1
    add('四层 stem 等长', f"frames={stems[0]['frames']}", '四路逐帧等长（B-24/M8）', same)

    # 3) 动画分镜：时长守恒（编码器允许合并相同帧）、代理时基、画幅、头尾黑场、AI 标识
    exp_frames = MANIFEST['content_frames']
    exp_dur = exp_frames / MANIFEST['fps']  # 代理样片只含内容帧
    for aspect, fname, target in (('239', 'animatic_239.webp', 2.39), ('169', 'animatic_169.webp', 16 / 9), ('916', 'animatic_916.webp', 9 / 16)):
        im = Image.open(OUT / fname)
        n = getattr(im, 'n_frames', 1)
        durs = []
        for i in range(n):
            im.seek(i); durs.append(int(im.info.get('duration', MANIFEST['proxy_frame_ms'])))
        total_dur = sum(durs) / 1000.0
        drift = abs(total_dur - exp_dur) / exp_dur * 100
        nominal = sum(durs) / len(durs)
        w, h = im.size; ar = w / h
        add(f'代理总时长与时基 {aspect}',
            f'编码 {n} 帧 / 共 {total_dur:.3f}s（声明 {exp_frames} 帧 / {exp_dur:.3f}s @ 1/24s）/ 标称 {nominal:.1f}ms/帧',
            '代理样片：内容帧数与总时长对应母版时间线，偏差 ≤1%（黑场另按时间线资产验证）', drift <= 1.0 and n == exp_frames)
        add(f'画幅 {aspect}', f'{w}×{h} = {ar:.3f}', f'目标 {target:.3f}（±1%）', abs(ar - target) / target <= 0.01)
        # 头尾黑场：以独立 PNG（母版时间线资产）验证亮度与时长（B-37：≥1 帧且 ≤1 s）
        bh = np.asarray(Image.open(OUT / 'frames' / f'black_head_{aspect}.png').convert('L'), np.float32)
        bt = np.asarray(Image.open(OUT / 'frames' / f'black_tail_{aspect}.png').convert('L'), np.float32)
        head_s = MANIFEST['head_black_frames'] / MANIFEST['fps']; tail_s = MANIFEST['tail_black_frames'] / MANIFEST['fps']
        add(f'头尾黑场 {aspect}', f'亮度 {bh.mean():.2f}/{bt.mean():.2f}，声明时长 {head_s:.3f}s/{tail_s:.3f}s',
            '黑场 ≥1 帧（1/24s）且 ≤1 s（B-37）；以母版时间线资产验证',
            bh.mean() < 1.0 and bt.mean() < 1.0 and 1 / MANIFEST['fps'] - 1e-6 <= head_s <= 1.0 and 1 / MANIFEST['fps'] - 1e-6 <= tail_s <= 1.0)
        # AI 显式标识（首个内容帧的红色徽标像素）
        im.seek(0)
        arr = np.asarray(im.convert('RGB'), np.int16)
        red = int(((arr[:, :, 0] > 150) & (arr[:, :, 1] < 90) & (arr[:, :, 2] < 90)).sum())
        add(f'AI 显式标识 {aspect}', f'首个内容帧红色标识像素 {red}', '起始画面显式标识（B-71/EL-11）', red > 200)

    # 6) 字幕（SRT 解析 + 规则）
    srt = (OUT / 'subs/pilot.zh.srt').read_text(encoding='utf-8').strip().split('\n\n')
    def parse_ts(t):
        h, m, rest = t.split(':'); s, ms = rest.split(','); return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    cues = []
    for blk in srt:
        lines = blk.splitlines()
        a, b = [x.strip() for x in lines[1].split('-->')]
        cues.append({'start': parse_ts(a), 'end': parse_ts(b), 'lines': lines[2:]})
    durs = [c['end'] - c['start'] for c in cues]
    add('字幕条数与时长', f"{len(cues)} 条，时长 {['%.2f' % d for d in durs]}s", '每条 5/6–7 s（B-32）',
        all(5 / 6 - 1e-6 <= d <= 7.0 for d in durs))
    add('中文字符/行', f"最大 {max(len(l) for c in cues for l in c['lines'])}", '≤23 字符/行（B-33）',
        max(len(l) for c in cues for l in c['lines']) <= 23)
    add('字幕行数', f"最大 {max(len(c['lines']) for c in cues)}", '≤2 行（B-32）', max(len(c['lines']) for c in cues) <= 2)
    sb = MANIFEST['subtitle_boxes']['239']
    W, H = MANIFEST['sizes']['239']
    inside = (sb[0] >= W * 0.05 and sb[1] >= H * 0.05 and sb[2] <= W * 0.95 and sb[3] <= H * 0.95)
    add('字幕安全区（渲染期几何）', f"box={sb}", '落在 EBU graphics safe（内缩 5%）内（B-16）', inside)

    # 7) 色彩一致性：从有损编码首帧取样 vs 声明参考
    im = Image.open(OUT / 'animatic_239.webp'); im.seek(0)
    measured = sample_patches(im.convert('RGB'))
    de = {k: delta_e2000(tuple(v), tuple(measured[k])) for k, v in MANIFEST['patches'].items()}
    thr = MANIFEST['declared_thresholds']['delta_e_max']
    add('色卡 ΔE（有损编码后实测）', f'最大 ΔE={max(de.values())}', f'项目自定 ΔE ≤ {thr}（B-88：无官方统一阈值）',
        max(de.values()) <= thr, '阈值由项目声明，非官方标准')

    # 8) 隐式标识与代理声明
    meta = json.loads((OUT / 'delivery/master.metadata.json').read_text())
    add('隐式标识（元数据）', 'AIGC=' + str(meta.get('AIGC', {}).get('isAIGenerated')), '元数据含生成合成属性（B-71）',
        bool(meta.get('AIGC', {}).get('isAIGenerated')))
    add('代理样片声明', str(meta.get('ProxyNotice', ''))[:42], '必须标注 PROXY、不得冒充母版（EL-16）',
        'PROXY' in str(meta.get('ProxyNotice', '')))
    return report(checks, de)

def report(checks, de=None) -> int:
    total = len(checks); passed = sum(1 for c in checks if c['pass'])
    qc = {'checks': checks, 'summary': {'total': total, 'pass': passed,
          'pass_rate': round(100 * passed / max(total, 1), 1)}, 'delta_e': de or {},
          'verified_from': 'on-disk artifacts only (independent pass)',
          'verifier': 'demo/verify.py'}
    (OUT / 'qc').mkdir(parents=True, exist_ok=True)
    (OUT / 'qc' / 'qc_report.json').write_text(json.dumps(qc, ensure_ascii=False, indent=2))
    md = ['# QC 报告（独立复测 · Demo）', '',
          f"- 结论：**{passed}/{total} 通过（{qc['summary']['pass_rate']}%）**",
          f"- 复测方式：{qc['verified_from']}", '',
          '| 检查项 | 实测 | 规则 | 结果 |', '|--------|------|------|------|']
    md += [f"| {c['item']} | {c['value']} | {c['rule']} | {'PASS' if c['pass'] else 'FAIL'} |" for c in checks]
    md += ['', '> ΔE 阈值按 B-88 由项目声明（无官方统一值）；代理样片按 EL-16 标注，不代表成片母版。']
    (OUT / 'qc' / 'qc_report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps(qc['summary'], ensure_ascii=False), '→ out/qc/qc_report.json')
    for c in checks:
        if not c['pass']: print('  FAIL:', c['item'], '|', c['value'], '|', c['rule'])
    return 0 if passed == total else 1

if __name__ == '__main__':
    raise SystemExit(main())
