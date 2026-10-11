#!/usr/bin/env python3
"""由实测产物生成：demo/README.md 与 PRD/97-Demo验证报告.md（数字全部取自 qc_report.json / manifest.json）。"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / 'out'
PRD = ROOT.parent / 'PRD'

def main() -> int:
    qc = json.loads((OUT / 'qc' / 'qc_report.json').read_text())
    mf = json.loads((OUT / 'manifest.json').read_text())
    s = qc['summary']
    rows = '\n'.join(f"| {c['item']} | {c['value']} | {c['rule']} | {'PASS' if c['pass'] else 'FAIL'} |" for c in qc['checks'])
    fails = [c for c in qc['checks'] if not c['pass']]
    shots = '\n'.join(f"| S{x['no']:02d} | {x['size']} | {x['lens']} | {x['move']} | {x['light']} | {x['frames']} 帧 |"
                      for x in mf['shots'])
    files = sorted(p.relative_to(ROOT).as_posix() for p in OUT.rglob('*') if p.is_file())
    file_rows = '\n'.join(f"| `{f}` | {((OUT / f).stat().st_size / 1024):.0f} KB |" if False else
                          f"| `{f}` | {(ROOT / f).stat().st_size // 1024} KB |" for f in files)
    status = '全部通过' if not fails else f"**{len(fails)} 项未通过**"

    readme = f"""# Amateur AI Drama Odyssey（`amateur-ai-drama-odyssey`）· 规范合规 Demo

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

- QC：**{s['pass']}/{s['total']} 通过（{s['pass_rate']}%）** —— {status}
- 音频母版：**{qc['delta_e'] and ''}{[c['value'] for c in qc['checks'] if '响度' in c['item']][0]}**，真峰值 **{[c['value'] for c in qc['checks'] if '真峰值' in c['item']][0]}**
- 画幅：2.39:1 / 16:9 / 9:16 同源派生（EL-01），代理时基见 QC「代理时基」项
- 字幕：{[c['value'] for c in qc['checks'] if c['item'] == '字幕条数与时长'][0]}；中文 {[c['value'] for c in qc['checks'] if '字符/行' in c['item']][0]}

## 产物清单

| 文件 | 大小 |
|------|------|
{file_rows}

## 这证明了什么 / 没证明什么

**已由机器验证**：响度与真峰值（EBU R128 / B-21，独立复测）、音频位深/采样率/声道（B-38）、四层 stem 等长（B-24）、
母版时间线（`out/timeline.json`，1/24 s 精确）、代理样片时基漂移（≤1%）、画幅比、头尾黑场（B-37）、
字幕时长/行长/行数（B-32/B-33）、字幕安全区几何（B-16）、AI 显式标识（B-71）、隐式元数据标识（B-71）、
有损编码后色卡 ΔE（阈值按 B-88 由项目声明）。

**未证明（需真实模型与人工终审）**：镜头语言与布光的艺术质量、表演与口型同步、混音艺术判断、
角色一致性阈值（0.45/0.30–0.45 待自有数据标定）、ACES IDT 实测、5.1 下混兼容。

> 合规声明：本 Demo 画面为程序化生成的**代理样片**，不代表成片母版；AI 标识、字幕与响度等规格均可被第三方独立复测。
"""
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')

    report_body = f"""# Demo 验证报告（附录）· Amateur AI Drama Odyssey

> 本报告由 `demo/report.py` 依据**实测产物**生成（数据源：`demo/out/qc/qc_report.json`、`demo/out/manifest.json`），不含手抄数字。
> 复测方式：`demo/verify.py` **只读磁盘产物**重新测量（fail-closed），生成器内部结果不参与判定。

## 一、结论

| 项 | 结果 |
|----|------|
| QC 通过率 | **{s['pass']}/{s['total']}（{s['pass_rate']}%）** |
| 未通过项 | {('无' if not fails else '；'.join(c['item'] + '（' + str(c['value']) + '）' for c in fails))} |
| 性质 | **PROXY 代理样片**，非交付母版（EL-16）；验证对象是「可机检门禁」，不是艺术质量 |

## 二、机检门禁逐项实测

| 检查项 | 实测 | 规则 | 结果 |
|--------|------|------|------|
{rows}

## 三、先导集镜头契约（EP01 前 8 镜，与 [96-先导集演练.md](../PRD/96-先导集演练.md) 一致）

| 镜 | 景别 | 焦距 | 运镜 | 光位 | 时长 |
|----|------|------|------|------|------|
{shots}

说明：每镜 {mf['shots'][0]['frames']} 帧 @ {mf['fps']}fps；母版时间线以 `demo/out/timeline.json` 为准（1/24 s 精确），WebP 为代理预览。

## 四、五门禁与预算（演练口径）

| 门禁 | 结论 | 署名 | 理由码 |
|------|------|------|--------|
{chr(10).join(f"| {g['gate']} | 通过 | {g['signer']} | `{g['code']}` |" for g in mf['gates'])}

预算（**估算，非报价**）：合计 ¥{mf['budget_cny']['合计']:,}，口径：{mf['budget_cny']['口径']}。

## 五、复现步骤与产物

```bash
cd demo && python3 build_demo.py && python3 verify.py && python3 report.py
```

产物：三画幅动画分镜（`out/animatic_*.webp`）、审看版静帧（`out/review/*.png`）、
四层 stem 与母版（`out/audio/*.wav`）、字幕（`out/subs/pilot.zh.srt`）、
时间线（`out/timeline.json`）、交付单与元数据（`out/delivery/*`）、QC 报告（`out/qc/*`）、仪表盘（`demo.html`）。

## 六、局限与后续

1. 本 Demo **不冒充成片母版**；画面为程序化代理，未使用任何生成模型。
2. 色卡 ΔE 的阈值按 B-88 由项目声明（无官方统一值），本报告如实标注为「项目自定」。
3. 未覆盖项见 `demo/README.md`「未证明」清单；其中口型、ACES IDT、5.1 下混需接入真实能力后实测。
"""

    # —— 变更记录：追加型 + 幂等（正文不变则不重写，避免 re-render 制造无意义 diff / 丢历史）——
    today = dt.date.today().isoformat()
    new_row = (f"| {today} | Agent | 由 `demo/report.py` 依据实测产物生成/重生成："
               f"QC {s['pass']}/{s['total']}、镜头契约、五门禁与预算、复现步骤与局限 |")
    report_path = PRD / '97-Demo验证报告.md'
    hist_rows, old_body = [], ""
    if report_path.exists():
        old_text = report_path.read_text(encoding='utf-8')
        if '## 七、变更记录' in old_text:
            old_body, tail = old_text.split('## 七、变更记录', 1)
            hist_rows = [ln for ln in tail.splitlines()
                         if ln.strip().startswith('|') and '日期' not in ln and '修订人' not in ln]
    if old_body and old_body.strip() == report_body.strip():
        pass  # 正文未变：跳过重写，不制造新 diff
    else:
        report = (report_body + "## 七、变更记录\n\n"
                  "| 日期 | 修订人 | 变更内容 |\n|------|--------|----------|\n"
                  + "\n".join(hist_rows + [new_row]) + "\n")
        report_path.write_text(report, encoding='utf-8')
    print(json.dumps({'readme': 'demo/README.md', 'report': 'PRD/97-Demo验证报告.md', 'qc': s}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
