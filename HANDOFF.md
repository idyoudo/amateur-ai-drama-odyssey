# 交接话术（切换到本项目的开场简报）

> 用法：在新会话里把「版本 A」整段粘给下一个 Agent 即可；信息量需要更大时用「版本 B」。
> 本文件是**给 Agent 看的**，不是产品文档；改动它不需要 PRD 台账登记。

---

## 版本 A · 最短开场（直接复制粘贴）

```text
你在 /Users/zhangtong/Tech/codex-ws/amateur-ai-drama-odyssey 工作。

这是 Amateur AI Drama Odyssey（amateur-ai-drama-odyssey，缩写 AADO）：一套「好莱坞级 AI 短剧」
产品——从小说到成片母版的完整链路（剧本开发→选角定妆→分镜previz→电影摄影→一致性与连续性→
表演配音口型→声音设计与配乐→剪辑→调色母版QC→交付→VFX→法律合规）。

它刚从交易项目 retail-trading-odyssey 独立出来，与交易业务无关；PRD 中出现的「RTO」指宿主平台
与既有实现基线，本项目按 PRD 重新实现，不继承其架构约束。

已有资产：
- PRD/：31 个文件、19 个模块、631 个功能点、7 个附录（含两轮选举决议 D1–D14 与硬性要求 EL-01~EL-16）
- demo/：可运行 Demo（三画幅代理分镜 + 真实 −23.0 LUFS 母版 + 独立复测 QC 24/24 通过）
- GOVERNANCE.md：两条强规则 + 机器门禁 tools/prd_guard.py

请先读（顺序）：AGENTS.md（所有 Agent 的统一入口，含硬约束/必跑命令/环境事实）→ GOVERNANCE.md → PRD/README.md → PRD/00-项目背景.md → PRD/93-决策选举记录.md →
PRD/96-先导集演练.md → PRD/90-评审与验收清单.md（评审重点）。

硬约束（违反会被门禁拦住）：
1) 强规则一：任何 PRD/ 下的改动，必须同时登记 PRD/CHANGELOG.md、PRD/changelog.jsonl 与被改文件内的
   ## 变更记录，且必须用本次新增条目覆盖（旧条目不算）；
   做法：python3 tools/prd_guard.py --new-entry --type 修订 --level L2 --files <文件> --refs <依据> --summary "说明"
2) 强规则二：项目级文档唯一（PRD/00-项目背景.md 独占定义模块地图/NFR/路线图，与模块文件、README 索引
   三者集合必须一致）；功能必归模块（编号 M#.#-F## 全局唯一、7 列固定、状态封闭集合、已实现须有 path:行号 证据）。

工作方式（沿用上一阶段，已验证有效）：争议不问我，走多智能体选举（5 名独立评估员、多数决、平票加选，
每位必须给理由/最大风险/缓解措施/落选方案诉求的低成本覆盖）；结论要能机器验证；本轮结束后自评并迭代，
直到门禁与复测全绿。若需要我拍板，说明你没先跑选举。

环境事实：无 ffmpeg、无 GPU、无付费模型凭据；系统 python3 缺 numpy/Pillow，
用 `python3 -m venv .venv && . .venv/bin/activate && pip install -r demo/requirements.txt`。
自检命令：`python3 tools/prd_guard.py --all`（含 Agent 文档一致性）；`. .venv/bin/activate` 后
`cd demo && python3 verify.py && python3 report.py`（须 24/24）；`python3 tools/verify_p1_a.py --out out/p1a`。

本轮目标：<在这里写你要做的事，例如「按 90 号 P0 缺口推进 P1 电影化主干」或「补齐 91/95 的待补原文」>。
```

---

## 版本 B · 完整交接简报（首次接手建议）

### 1. 项目是什么

- **名称**：Amateur AI Drama Odyssey（`amateur-ai-drama-odyssey`，AADO）
- **目标**：好莱坞级 AI 短剧——小说 → 剧本 → 定妆 → 分镜 → 生成 → 声音 → 剪辑 → 调色母版 → 交付，全部按影视工业标准与规范执行
- **首季包型**：6 集 × 30 分钟（决议 D7），首集《回声》为都市悬疑（D13）
- **主母版规格**：2.39:1 / 24fps / Rec.709 SDR / −23.0 LUFS / ≤−1 dBTP / 24-bit 48 kHz（决议 D1/D3/D4/D5）

### 2. 已有资产与验证状态

| 资产 | 位置 | 状态 |
|------|------|------|
| PRD 正文 | `PRD/00-项目背景.md` + `M1`~`M19` | 19 模块 / 631 功能点；状态、证据、编号、链接、依据 **0 异常** |
| 技术规格 | `PRD/91-…` | B-14~B-88（安全区、EBU R128、ITU-R BT.1359-1、Netflix/Amazon/YouTube、ACES/HDR/DCP） |
| 流程对标 | `PRD/92-…` | E-36~E-63、D-16~D-40、B-89 |
| 选举决议 | `PRD/93-…` | 两轮 14 项决议、77 次独立评估、EL-01~EL-16（**约束性**） |
| 自评记录 | `PRD/94-…` | 六轮自评、CR-01~CR-25 闭环 |
| 法律合规 | `PRD/95-…` | 工会/肖像/版权/分级披露 + RL-01~RL-12 红线 |
| 先导集演练 | `PRD/96-…` | 五门禁决策、驳回回退路径、9 条缺口 |
| Demo 报告 | `PRD/97-…` | 由实测数据生成 |
| 依据库 | `PRD/99-…` | 273 条编号依据（A/B/C/D/E/F） |
| 可运行 Demo | `demo/`（入口 `demo/demo.html`） | 独立复测 **24/24 通过** |
| 治理 | `GOVERNANCE.md` + `tools/prd_guard.py` + `.githooks/pre-commit` + CI | 提交与 CI 双重强制 |
| Agent 入口 | `AGENTS.md`（唯一事实来源）+ `CLAUDE.md`（Claude Code 适配层） | 由 `prd_guard.py --agent-docs` 校验一致性 |
| P1 主干切片 A | `film/` + `tools/build_p1_a.py` + `tools/verify_p1_a.py` + `out/p1a/` | 预检 84/84、独立复测 62/62（含确定性双跑） |

### 3. 十分钟上手路径

```bash
sh tools/install-hooks.sh                 # 0) 克隆后启用提交钩子（必须一次）
python3 tools/prd_guard.py --all          # 1) 确认治理门禁全绿
cd demo && python3 verify.py              # 2) 确认 Demo 24/24（依赖见 demo/requirements.txt）
open demo.html                            # 3) 看 Demo 仪表盘
# 4) 读 PRD/90-评审与验收清单.md 第五章（404 条 P0 缺口）与第七章（101 条待决）
```

### 4. 硬约束速查

| 约束 | 触发 | 后果 |
|------|------|------|
| PRD 改动未登记 | `git commit` | 钩子拒绝并给出 `--new-entry` 命令 |
| 台账写目录前缀/通配 | 任意校验 | 拒绝（防止一条台账永久豁免整目录） |
| 追溯登记（`retroactive`）当豁免用 | `--staged/--range` | 拒绝（追溯条目只管历史） |
| 模块地图/索引/文件三处不一致 | `--all` | 拒绝 |
| 功能点编号重复、状态非法、`已实现` 无证据、`规划中` 无依据 | `--all` | 拒绝 |
| 文件内 `## 变更记录` 未新增行 | `--staged` | 拒绝 |

### 5. 现在处在哪一步

- **已完成**：PRD 全量好莱坞级重构 + 两轮选举 + 六轮自评；先导集演练；规范合规 Demo（机检门禁全通过）
- **未开始**：P1 电影化主干的**实现**（PRD 是需求，不是开发计划；实现方案应放 `docs/plans/`）
- **真机才能证的三项**：ACES IDT hero shot 往返、5.1 下混兼容、口型引擎接入（对应 96 的 G-02/G-03 与 EL-14）
- **待补原文（不得作为验收阈值）**：SAG-AFTRA 2026 MOA / WGA 2026 MBA 逐条文本、AB 1836 签署版、标识强制国标编号、ΔE 与闪白 PSE 阈值、Apple TV+/Disney+/TikTok 标注政策

### 6. 边界（别踩）

1. **不要动宿主仓库** `retail-trading-odyssey`：本项目已独立，PRD 里的 `apps/...:行号` 只是"现状基线"引用；
2. **不要把 PRD 当开发计划**：PRD 只回答"做什么、做到什么程度算完成"；技术方案进 `docs/plans/`，调研资料进 `docs/spec/`；
3. **不要绕过治理**：即使只改一行 PRD 说明，也要登记（门禁会拦）；
4. **不要声称未验证的东西**：Demo 是代理样片（PROXY），艺术质量维度不在其声称范围内。

### 7. 建议的第一批任务（任选其一）

| 选项 | 内容 | 交付物 |
|------|------|--------|
| A | 按 `PRD/90` 第五章 P0 缺口推进 **P1 电影化主干**实现方案 | `docs/plans/` 计划 + 可运行的最小链路 |
| B | 补齐 **待补原文**（91/95 第九章清单）并升级为门禁项 | 附录回填 + 台账登记 + 门禁阈值 |
| C | 攻**真机三项**：ACES IDT / 5.1 下混 / 口型引擎 | 实测报告 + QC 门禁扩展 |
| D | 把 Demo 从"规范合规"升级为**接入真实模型的样片**（先导集 1 镜端到端） | 真实产物 + 成本与时长实测 |

---

## 变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立交接话术：短版开场（可直接粘贴）与完整交接简报（项目/资产/上手路径/硬约束/现状/边界/首批任务） |
| 2026-10-11 | Agent | 补 Agent 入口：短版开场与资产表补 `AGENTS.md`/`CLAUDE.md`、P1-A 切片与 Agent 文档门禁；自检命令补 `.venv` 与切片复测 |
