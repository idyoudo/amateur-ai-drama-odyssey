"""ITU-R BS.1770-4 集成响度与真峰值测量（纯 numpy 实现，用于自证交付母版合规）。

实现要点：
- K 加权：两级 RBJ 双二阶（高架 +3.999 dB @1681.97Hz Q=0.7071；高通 38.135Hz Q=0.5）
- 门限：400ms 块、75% 重叠；绝对门限 −70 LUFS；相对门限 −10 LU
- 真峰值：4 倍过采样（多相 FIR）后取绝对值峰值
参考：EBU R128 / ITU-R BS.1770-4（本项目验收阈值见 PRD/91 B-21、B-22）
"""
from __future__ import annotations
import numpy as np

def _biquad_coeffs(kind: str, f0: float, Q: float, gain_db: float, fs: float):
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / fs
    cw, sw = np.cos(w0), np.sin(w0)
    if kind == 'highshelf':
        alpha = sw / 2 * np.sqrt((A + 1 / A) * (1 / 0.7071 - 1) + 2)
        b0 = A * ((A + 1) + (A - 1) * cw + 2 * np.sqrt(A) * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * cw)
        b2 = A * ((A + 1) + (A - 1) * cw - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) - (A - 1) * cw + 2 * np.sqrt(A) * alpha
        a1 = 2 * ((A - 1) - (A + 1) * cw)
        a2 = (A + 1) - (A - 1) * cw - 2 * np.sqrt(A) * alpha
    elif kind == 'highpass':
        alpha = sw / (2 * Q)
        b0, b1, b2 = (1 + cw) / 2, -(1 + cw), (1 + cw) / 2
        a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
    else:
        raise ValueError(kind)
    return np.array([b0 / a0, b1 / a0, b2 / a0]), np.array([1.0, a1 / a0, a2 / a0])

def _apply(b: np.ndarray, a: np.ndarray, x: np.ndarray) -> np.ndarray:
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(x.shape[0]):
        v = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1 = x1, x[i]
        y2, y1 = y1, v
        y[i] = v
    return y

def k_weight(x: np.ndarray, fs: float) -> np.ndarray:
    b, a = _biquad_coeffs('highshelf', 1681.974450955533, 0.7071752369554196, 3.999843853973347, fs)
    y = _apply(b, a, x)
    b2, a2 = _biquad_coeffs('highpass', 38.13547087602444, 0.5003270373238773, 0.0, fs)
    return _apply(b2, a2, y)

def integrated_loudness(x: np.ndarray, fs: float) -> float:
    """x: (n,) 单声道 或 (n, ch) 多声道；返回 LUFS。"""
    if x.ndim == 1:
        x = x[:, None]
    y = np.stack([k_weight(x[:, c], fs) for c in range(x.shape[1])], axis=1)
    # 声道权重：L/R/C = 1.0，环绕 = 1.41（本 Demo 只用立体声）
    G = np.ones(x.shape[1])
    block = int(round(0.400 * fs)); step = block // 4
    if y.shape[0] < block:
        return -np.inf
    idx = range(0, y.shape[0] - block + 1, step)
    z = np.array([np.mean((y[i:i + block] ** 2) * G) for i in idx])
    l = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    abs_gated = z[l > -70.0]
    if abs_gated.size == 0:
        return -np.inf
    rel = -0.691 + 10 * np.log10(np.mean(abs_gated)) - 10.0
    keep = z[(l > -70.0) & (l > rel)]
    if keep.size == 0:
        return -np.inf
    return float(-0.691 + 10 * np.log10(np.mean(keep)))

def true_peak_dbtp(x: np.ndarray, fs: float, oversample: int = 4) -> float:
    """4 倍过采样真峰值估计（多相 FIR 低通）。x: (n,) 或 (n, ch)。"""
    if x.ndim == 1:
        x = x[:, None]
    peak = 0.0
    n_taps = 48
    t = np.arange(n_taps) - (n_taps - 1) / 2
    h = np.sinc(t / oversample) * np.hamming(n_taps)
    h /= h.sum()
    for c in range(x.shape[1]):
        up = np.zeros(x.shape[0] * oversample)
        up[::oversample] = x[:, c]
        y = np.convolve(up, h, mode='same') * oversample  # 补偿零插值带来的幅度损失
        peak = max(peak, float(np.max(np.abs(y))))
    return 20 * np.log10(max(peak, 1e-12))

def normalize_to_lufs(x: np.ndarray, fs: float, target_lufs: float = -23.0,
                      max_true_peak_dbtp: float = -1.0, iterations: int = 4) -> tuple[np.ndarray, dict]:
    """按目标响度缩放，并在真峰值超限时回退增益，返回 (y, 报告)。"""
    y = x.copy()
    gain_db = 0.0
    for _ in range(iterations):
        lufs = integrated_loudness(y, fs)
        tp = true_peak_dbtp(y, fs)
        delta = target_lufs - lufs
        # 真峰值余量约束：若达标后 tp 会超限，则限制增益
        allow = max_true_peak_dbtp - tp
        apply_db = min(delta, allow) if abs(delta) > 0.01 else 0.0
        if abs(apply_db) < 0.01:
            break
        y = y * (10 ** (apply_db / 20.0))
        gain_db += apply_db
    return y, {
        'integrated_lufs': round(integrated_loudness(y, fs), 2),
        'true_peak_dbtp': round(true_peak_dbtp(y, fs), 2),
        'applied_gain_db': round(gain_db, 2),
        'target_lufs': target_lufs,
        'true_peak_limit_dbtp': max_true_peak_dbtp,
    }

def write_wav(path: str, x: np.ndarray, fs: int, bitdepth: int = 24, force_stereo: bool = True) -> None:
    """写 WAV；默认 24-bit 立体声（交付母版规格 B-38）。"""
    import wave
    data = np.clip(x, -1.0, 1.0)
    if data.ndim == 1:
        data = data[:, None]
    if force_stereo and data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    ch = data.shape[1]
    if bitdepth == 24:
        ints = np.round(data * (2 ** 23 - 1)).astype('<i4')
        b = ints.astype('<i4').view(np.uint8).reshape(-1, 4)[:, :3].copy()
        payload = b.tobytes(); sampwidth = 3
    else:
        payload = np.round(data * 32767.0).astype('<i2').tobytes(); sampwidth = 2
    with wave.open(path, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(sampwidth); w.setframerate(fs)
        w.writeframes(payload)
