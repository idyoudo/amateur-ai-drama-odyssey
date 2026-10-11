# Amateur AI Drama Odyssey（`amateur-ai-drama-odyssey`）· 规范合规 Demo

> **PROXY 代理样片 — 非交付母版（EL-16）**：本 Demo 在**无 GPU、无 ffmpeg、无付费模型凭据**的环境下，用程序化方式生成
> 「可机检门禁」的产物并**独立复测**，用于验证 PRD 中可自动判定的部分；摄影/表演/口型/混音/调色的**质量维度**不在声称范围内。

## 一键复现

依赖：**Python ≥ 3.10 + numpy + Pillow**（无需 ffmpeg / GPU / 付费模型凭据）。

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r demo/requirements.txt

cd demo
python3 build_demo.py     # 生成全部产物（约 4–10 分钟，取决于机器）
python3 verify.py         # 独立复测（只读磁盘产物，退出码 0 = 全项通过）
python3 report.py         # 由实测数据生成本 README 与 PRD/97-Demo验证报告.md
open demo.html            # 打开仪表盘（也可直接用浏览器打开 demo/demo.html）
```

## 当前实测结果

- QC：**24/24 通过（100.0%）** —— 全部通过
- 音频母版：**-23.00 LUFS**，真峰值 **-4.61 dBTP**
- 画幅：2.39:1 / 16:9 / 9:16 同源派生（EL-01），代理时基见 QC「代理时基」项
- 字幕：2 条，时长 ['5.50', '5.50']s；中文 最大 23

## 产物清单

| 文件 | 大小 |
|------|------|
| `out/animatic_169.webp` | 1144 KB |
| `out/animatic_239.webp` | 992 KB |
| `out/animatic_916.webp` | 1060 KB |
| `out/audio/master_23LUFS.wav` | 3375 KB |
| `out/audio/stem_ambience.wav` | 3375 KB |
| `out/audio/stem_dialogue.wav` | 3375 KB |
| `out/audio/stem_music.wav` | 3375 KB |
| `out/audio/stem_sfx.wav` | 3375 KB |
| `out/delivery/delivery_sheet.json` | 1 KB |
| `out/delivery/delivery_sheet.md` | 0 KB |
| `out/delivery/master.metadata.json` | 0 KB |
| `out/frames/black_head_169.png` | 0 KB |
| `out/frames/black_head_239.png` | 0 KB |
| `out/frames/black_head_916.png` | 0 KB |
| `out/frames/black_tail_169.png` | 0 KB |
| `out/frames/black_tail_239.png` | 0 KB |
| `out/frames/black_tail_916.png` | 0 KB |
| `out/frames/hero_169_open_gate_s05.png` | 3244 KB |
| `out/frames/hero_239_s05.png` | 2444 KB |
| `out/manifest.json` | 4 KB |
| `out/qc/qc_report.json` | 5 KB |
| `out/qc/qc_report.md` | 3 KB |
| `out/review/review_169_s01.png` | 1218 KB |
| `out/review/review_169_s03.png` | 1225 KB |
| `out/review/review_169_s07.png` | 1229 KB |
| `out/review/review_239_s01.png` | 908 KB |
| `out/review/review_239_s03.png` | 914 KB |
| `out/review/review_239_s07.png` | 916 KB |
| `out/review/review_916_s01.png` | 1329 KB |
| `out/review/review_916_s03.png` | 1325 KB |
| `out/review/review_916_s07.png` | 1331 KB |
| `out/subs/pilot.zh.srt` | 0 KB |
| `out/timeline.json` | 2 KB |

## 这证明了什么 / 没证明什么

**已由机器验证**：响度与真峰值（EBU R128 / B-21，独立复测）、音频位深/采样率/声道（B-38）、四层 stem 等长（B-24）、
母版时间线（`out/timeline.json`，1/24 s 精确）、代理样片时基漂移（≤1%）、画幅比、头尾黑场（B-37）、
字幕时长/行长/行数（B-32/B-33）、字幕安全区几何（B-16）、AI 显式标识（B-71）、隐式元数据标识（B-71）、
有损编码后色卡 ΔE（阈值按 B-88 由项目声明）。

**未证明（需真实模型与人工终审）**：镜头语言与布光的艺术质量、表演与口型同步、混音艺术判断、
角色一致性阈值（0.45/0.30–0.45 待自有数据标定）、ACES IDT 实测、5.1 下混兼容。

> 合规声明：本 Demo 画面为程序化生成的**代理样片**，不代表成片母版；AI 标识、字幕与响度等规格均可被第三方独立复测。
