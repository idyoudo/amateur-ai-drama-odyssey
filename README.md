# Amateur AI Drama Odyssey（`amateur-ai-drama-odyssey`）

> 好莱坞级 AI 短剧产品：**从小说到成片母版**的全链路产品需求（PRD）＋ 先导集全链路演练 ＋ 可运行的规范合规 Demo。
> 本仓库由原 `retail-trading-odyssey` 内的 AI 短剧方向独立出来，**不再与交易业务混放**。

## 治理规则（强规则，机器强制）

> **克隆仓库后第一步**：`sh tools/install-hooks.sh`（Git 钩子不随 clone 生效，必须本机启用一次）。


本项目有两条**强规则**，由 `tools/prd_guard.py` 在提交时与 CI 中强制执行：

1. **PRD 变更必登记**：任何 `PRD/` 下的改动都必须同时更新三处台账——项目级 [PRD/CHANGELOG.md](PRD/CHANGELOG.md)、机器可读 `PRD/changelog.jsonl`、被改文件内的 `## 变更记录`。
2. **两个稳定**：**项目级文档唯一**（`PRD/00-项目背景.md` 独占定义模块地图/NFR/路线图）＋ **功能必归模块**（每个功能点只能登记在所属 `M#` 模块内，编号唯一、字段齐备）。

**Agent 入口**：任何 AI 工具（Claude Code / DeepSeek Harness / Codex / Cursor…）接手本仓库，先读
[AGENTS.md](AGENTS.md)（唯一事实来源）；Claude Code 另见 [CLAUDE.md](CLAUDE.md)。
两份文件不得各自维护规则，由 `python3 tools/prd_guard.py --agent-docs` 校验一致性（也包含在 `--all` 中）。

详见 [GOVERNANCE.md](GOVERNANCE.md)。日常改动姿势：

```bash
python3 tools/prd_guard.py --new-entry --type 修订 --level L2 \
  --files PRD/M5-电影摄影与画面生成.md --refs D7 --summary "说明"
git add -A && git commit -m "docs(prd): …"   # 钩子自动校验，违规直接拒绝
```

## 目录结构

```text
AGENTS.md                      ← **所有 AI Agent 的统一入口**（单一事实来源：硬约束/命令/环境事实）
CLAUDE.md                      ← Claude Code 适配层（指向 AGENTS.md，不复制规则）
README.md                      ← 本文件
PRD/                           ← 产品需求文档（唯一归档位置，31 个文件）
  README.md                    ← PRD 规则与索引（先读这个）
  00-项目背景.md               ← L1 总览：19 模块、16 条 NFR、五段工业流程、三期路线图
  M1..M19-*.md                 ← 19 个 L2 模块，631 个功能点
  90-评审与验收清单.md          ← 评审入口：进度 / 自查 / P0 缺口 / 待决问题
  91-影视技术规格与交付标准.md   ← 图像·声音·字幕·母版·QC 硬规格（B-14~B-88）
  92-好莱坞制作流程对标.md       ← 开发/结构/剪辑/连续性/平台可控性（E-36~E-63）
  93-决策选举记录.md            ← 两轮 14 项决议（D1–D14）与硬性要求（EL-01~EL-16）
  94-自评与修订记录.md          ← 六轮自评—修订循环（CR-01~CR-25）
  95-法律工会与行业准入标准.md   ← 工会/肖像/版权/分级/披露与 12 条产品红线
  96-先导集演练.md              ← EP01《回声》Development→Delivery 全链路演练
  97-Demo验证报告.md            ← Demo 机检门禁实测（由实测数据生成）
  99-业界对标与调研.md          ← 市场/开源/工程/成本依据库
demo/                          ← 可运行 Demo（规范合规模拟母版）
  build_demo.py                ← 生成三画幅代理分镜 + 四层声音母版 + 字幕 + 交付单 + 时间线 + 仪表盘
  verify.py                    ← 独立复测（只读磁盘产物，fail-closed，退出码 0 = 全通过）
  report.py                    ← 由实测数据生成 demo/README.md 与 PRD/97
  demo.html                    ← 仪表盘（浏览器直接打开）
  out/                         ← 全部产物（动画分镜 / WAV 母版 / QC 报告 / 交付单）
film/                          ← P1-A 切片实现包（镜头契约 / 提示词编译 / 安全框几何 / 漂移 / 门禁字段契约）
  fixtures/pilot_ep01.json     ← 先导集 EP01 的构图几何声明（契约字段从 PRD/96 解析，不手抄）
  fixtures/mutations/          ← 13 个违例样本（每条规则一个，复测断言「规则集 == 变异集」）
tools/
  prd_guard.py                 ← 治理门禁（强规则一/二）
  build_p1_a.py                ← P1-A 切片生成器（只生成）
  verify_p1_a.py               ← P1-A 切片独立复测（只读产物、fail-closed）
docs/
  README.md                     ← 文档地图 + 归位约定（权威索引，改动必须同步）
  architecture.md               ← 系统架构（技术选型 / 进程拓扑 / 模块映射）
  designs/                      ← 技术设计（数据模型 / API 契约 / 任务编排 / 宿主基线 / 测试策略）
  plans/                        ← 计划与决策（实施计划 / 切片方案 / 选举记录 / 待裁决清单）
  spec/                         ← 执行记录与验证证据（由脚本生成，禁止手抄）
  guid/                         ← 部署 / 运维 / 使用指南（预留）
  agent-prd-method.md           ← 本次工作方法总结（可复用的八步工作流与验收清单）
out/p1a/                       ← P1-A 切片产物（契约 / 提示词 / 安全框 / 漂移 / 预检 / 收据 / 代理帧）
```

## 快速开始（Demo，约 4–10 分钟）

依赖：**Python ≥ 3.10 + numpy + Pillow**（无需 ffmpeg / GPU / 付费模型凭据）。

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r demo/requirements.txt

cd demo
python3 build_demo.py     # 生成全部产物
python3 verify.py         # 独立复测：24/24 通过，退出码 0
python3 report.py         # 由实测数据刷新 demo/README.md 与 PRD/97
open demo.html            # 仪表盘（也可用浏览器直接打开 demo/demo.html）
```

无需 GPU、无需 ffmpeg、无需付费模型凭据：画面为程序化生成的**代理样片**，音频为**真实可复测的 24-bit/48 kHz 母版**（−23.0 LUFS，EBU R128 口径）。

## P1 电影化主干 · 第一个切片（P1-A：镜头契约与安全框预检）

依据 [PRD/90](PRD/90-评审与验收清单.md) 的 P0 缺口推进。范围由多智能体选举裁决（5 名独立评估员，A 4:1 B）：
方案见 [docs/plans/P1-A-镜头契约与安全框预检-方案.md](docs/plans/P1-A-镜头契约与安全框预检-方案.md)，
票型与缓解措施见 [docs/plans/P1-A-选举记录.md](docs/plans/P1-A-选举记录.md)，
实测发现的 PRD 内部冲突见 [docs/plans/P1-待裁决清单.md](docs/plans/P1-待裁决清单.md)。

```bash
. .venv/bin/activate
python3 tools/build_p1_a.py --out out/p1a            # 生成：8 镜契约 / 确定性提示词 / 三画幅裁切预演
python3 tools/verify_p1_a.py --out out/p1a \
        --report docs/spec/P1-A-验证记录.md           # 独立复测：fail-closed，退出码 0 = 全通过
python3 tools/verify_p1_a.py --out out/p1a --determinism   # 确定性双跑（跨 hash seed / 时区 / 语言）
```

它做到：24 条 PRD 功能点的**可机检化**（M4.1-F01、M4.2-F01~F04、M4.4-F02、M4.7-F01/F02、
M5.1-F01~F05、M5.2-F01/F02/F03/F05、M5.3-F01/F02/F03/F05/F06、M5.6-F03/F05、M10.3-F02/F03）；
13 个变异样本 100% 被检出；提示词字节级确定性；**决定性发现**——用同一判据量参考实现 `demo/` 的既有构图，
S03/S04/S07 三镜不满足多画幅安全框（详见 P1-待裁决清单 C-08）。

它**没有**做到（`out/p1a/not_verified.json` 逐条登记）：真实模型调用、−23 LUFS 母版、TC 嵌入、ACES IDT、
5.1 下混、口型、EDL/AAF 回批。**P1 退出标准未达成**（`p1_exit_criteria_advanced = false`）。

## PRD 阅读顺序（建议）

1. [PRD/README.md](PRD/README.md)：规则、编号体系、文档索引
2. [PRD/00-项目背景.md](PRD/00-项目背景.md)：愿景、模块地图、NFR、路线图
3. [PRD/93-决策选举记录.md](PRD/93-决策选举记录.md)：**约束性决议**（含票型、异议、风险与缓解措施）
4. 附录 [91](PRD/91-影视技术规格与交付标准.md) / [92](PRD/92-好莱坞制作流程对标.md) / [95](PRD/95-法律工会与行业准入标准.md) / [99](PRD/99-业界对标与调研.md)：证据与硬规格
5. [PRD/96-先导集演练.md](PRD/96-先导集演练.md)：一条真实链路怎么走、门禁怎么判、缺口在哪
6. [PRD/90-评审与验收清单.md](PRD/90-评审与验收清单.md)：评审重点（404 条 P0 缺口、101 条待决问题）
7. 模块 `M1`~`M19`：按需深入

## 证据口径（重要）

- 功能点「现状」列中的 `apps/...:行号` 引用**宿主实现基线**——原 `retail-trading-odyssey` 仓库内的既有 AI 短剧链路。本项目按 PRD 重新实现，**不继承该实现的架构约束**。
- 结论的依据编号（`A` 对标/产业、`B` 标准法规、`C` 开源、`D` 论文指标、`E` 工程实践、`F` 成本基准）见附录 91/92/95/99；**未取到原文者标「待补原文」，不得作为验收阈值**。
- Demo 标注 **PROXY 代理样片**（EL-16），不冒充成片母版。

## Agent 文档一致性门禁

```bash
python3 tools/prd_guard.py --agent-docs   # 单跑；--all 也会带上
```

它校验：`AGENTS.md` 的 `aado-facts` 机器可读事实块是否齐备且键值合法；声明的路径与命令**是否真实存在**；
声明的 Python 版本与**实际解释器**是否主次版本一致（本机 3.9.6 / CI 3.12 双环境已在事实块登记）；
`CLAUDE.md` 是否指向 `AGENTS.md`（防止两套规则漂移）；`README` 里的通过率是否与事实块一致（**逐处校验**）。

## 当前状态

| 项 | 状态 |
|----|------|
| PRD | 31 个文件 / 4998 行 / 19 模块 / 631 功能点；状态取值、证据完整、编号唯一、内部链接、依据可解析**全部 0 异常** |
| 先导集演练 | EP01《回声》全链路走查；五门禁决策与驳回回退；暴露 9 条缺口（G-01 已闭环） |
| Demo | 独立复测 **24/24 通过（100%）**；母版 −23.00 LUFS / 真峰值 −4.61 dBTP |
| P1 主干切片 A | 镜头契约与安全框预检闭环：**预检 84/84、独立复测 62/62、变异 13/13 检出、确定性双跑一致**；参考实现 3 镜安全框已返修（C-08） |
| 决策 | 两轮选举共 14 项决议、77 次独立评估；派生 EL-01~EL-16 并回填到全部模块 |
| **开发交接包** | 架构 + 数据模型 + API 契约 + 任务编排 + 实施计划 + 测试策略已产出；5 条冲突经选举冻结并落地 PRD（`CR-20261011-007/008`） |
| **P1 契约层实现** | 19 模块纯 Python 契约层落地（`film/` 16 子包，337 断言全绿）+ FastAPI 控制面 + worker + Alembic 迁移 + 部署脚手架；6 项拍板经 5 人选举裁决 |

## 开发交接（给接手团队）

**先读**：[docs/architecture.md](docs/architecture.md)（技术选型 + 模块边界）→ [docs/plans/P1-实施计划.md](docs/plans/P1-实施计划.md)（572 条拆 5 批 17 工单 + 验收命令）→ [docs/README.md](docs/README.md)（文档地图 + 归位约定）。

**必须人类先拍板**的 12 项（非写文档可解决）见 [P1-实施计划.md 第七节](docs/plans/P1-实施计划.md)：M6 标定样本、NFR-04 成本目标、工具链采买、供应商选型、法务原文、M19 自建/外包、盲评人力、ACES IDT 形态、InsightFace 替代、门禁署名岗位等。

**接手后的开发纪律**（已写进 [AGENTS.md](AGENTS.md)）：改 PRD 必须三处台账登记；临时产物写系统临时目录；`git add` 用显式路径禁用 `-A`；`demo/out`、`out/p1a` 是证据链不可清理；收工跑三条必绿命令。

## 下一步

1. 部署 api/worker 到远端（`./scripts/deploy-remote.sh`）并跑 `tools/verify_pg.py`（`DATABASE_URL` 注入）做 PG SKIP LOCKED 并发联调。
2. 接入供应商（视频/口型/音乐，待付费凭据）与「待补原文」标准（SAG-AFTRA/WGA 原文、标识国标编号等）。
3. 按批次把契约层接到真实后端，做模块间联调打通端到端链路。
