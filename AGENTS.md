# AGENTS.md —— 所有 AI Agent 的统一入口（单一事实来源）

> **任何 Agent harness（Claude Code / DeepSeek Harness / Codex / Cursor / Gemini CLI …）接手本仓库，先读本文件。**
> Claude Code 另见 [CLAUDE.md](CLAUDE.md)（薄适配层，指向本文件，不复制内容）。
> 治理规则见 [GOVERNANCE.md](GOVERNANCE.md)；工作方法见 [docs/agent-prd-method.md](docs/agent-prd-method.md)；项目资产与进度见下方第 10 节。

---

## 0. 这是什么项目

**Amateur AI Drama Odyssey**（`amateur-ai-drama-odyssey`，缩写 **AADO**）：一套「好莱坞级 AI 短剧」产品——
从小说到成片母版的完整链路（剧本开发 → 选角定妆 → 分镜 previz → 电影摄影 → 一致性与连续性 →
表演配音口型 → 声音设计与配乐 → 剪辑 → 调色母版 QC → 交付 → VFX → 法律合规）。

- **首季包型**：6 集 × 30 分钟（D7），首集《回声》都市悬疑（D13）；**主母版规格** 2.39:1 / 24fps / Rec.709 SDR / −23.0 LUFS / ≤−1 dBTP / 24-bit 48 kHz（D1/D3/D4/D5）。
- 它**已从交易项目 `retail-trading-odyssey` 独立**，与交易业务无关。**绝对不要改动宿主仓库。**
- PRD 中的 **「RTO」＝宿主平台与既有实现基线**，不是本项目名；`apps/...:行号` 只是「现状基线」引用，
  本项目按 PRD 重新实现，**不继承其架构约束**。
- **PRD 回答「要什么、为什么、怎样算达标」；不写「怎么实现」。** 架构进 `docs/architecture.md`，
  技术设计进 `docs/designs/`，计划与决策进 `docs/plans/`，验证证据进 `docs/spec/`，部署运维进 `docs/guid/`。

## 1. 三条命令：每次开工与收工都必须全绿

```bash
# ① 治理门禁（强规则一/二 + Agent 文档一致性）
python3 tools/prd_guard.py --all

# ② Demo 独立复测（必须 24/24；依赖装在 .venv，系统 python3 没有 numpy/Pillow）
. .venv/bin/activate && cd demo && python3 verify.py && python3 report.py && cd ..

# ③ P1-A 切片（镜头契约与安全框预检）
python3 tools/build_p1_a.py --out out/p1a
python3 tools/verify_p1_a.py --out out/p1a --determinism
```

判定口径：任一门禁非 0 退出即**未完成**。收工前必须三条全绿；不允许「先提交、后修绿」。

首次接手（新克隆）先做两件事：

```bash
sh tools/install-hooks.sh                     # Git 钩子不随 clone 生效，必须本机启用一次
python3 -m venv .venv && . .venv/bin/activate && pip install -r demo/requirements.txt
```

## 2. 硬约束（违反会被机器拦住）

| # | 约束 | 触发点 | 后果 |
|---|------|--------|------|
| 1 | **PRD 变更必登记**：任何 `PRD/` 下改动必须**同时**登记 `PRD/CHANGELOG.md` + `PRD/changelog.jsonl` + 被改文件内 `## 变更记录`（追加型，行数不得减少），且**必须由本次新增条目覆盖**（旧条目不算） | `git commit` / `--staged` / `--range` | 拒绝 |
| 2 | 台账 `files` 必须写**具体文件路径**，禁止目录前缀与通配符 | 任意校验 | 拒绝 |
| 3 | 追溯登记（`"retroactive": true`）**不构成**对本次改动的登记 | `--staged` / `--range` | 拒绝 |
| 4 | **项目级文档唯一**：模块地图 / NFR / 路线图只由 `PRD/00-项目背景.md`（L1）定义，且 L1 模块地图 ↔ `PRD/M*.md` ↔ `PRD/README.md` 索引**三者集合完全一致** | `--all` | 拒绝 |
| 5 | **功能必归模块**：功能点只登记在 `M#` 模块内；编号 `M<模块>.<二级>-F<序号>` 全局唯一；表头固定 7 列；状态取值封闭集合；`已实现` 必须给 `path:行号` 证据；`规划中` 必须有依据 | `--all` | 拒绝 |
| 6 | **开发任务必登记模块文档**：任何触及 `M#` 模块的实现/改动/排查/文档/迁移，动手前必读 `docs/modules/M#-<中文名>.md` 总入口，开工在 `## 任务登记` 登记一行（编号 `M#-TNN`），完成在 `## 变更记录` 回写；每个模块必须有同名 `docs/modules/M#-<中文名>.md` | `--all` / `--staged` | 拒绝 |

合规改动姿势（唯一正确写法）：

```bash
# 1) 改 PRD 文件（模块内登记功能点；新增模块则同时改 L1 地图与 README 索引）
# 2) 生成台账条目（自动填 id/date/files）
python3 tools/prd_guard.py --new-entry --type 修订 --level L2 \
  --files PRD/M5-电影摄影与画面生成.md --refs D7 --summary "说明改了什么与为什么"
# 3) 提交（钩子自动校验；不要用 git add -A，用显式路径，见第 9 节）
git add PRD/M5-电影摄影与画面生成.md PRD/CHANGELOG.md PRD/changelog.jsonl \
  && git commit -m "docs(prd): …"
```

> 只改 `PRD/` 以外的文件（代码、docs/plans、docs/spec、README、AGENTS.md…）**不需要**台账登记。
>
> 但触及 `M#` 模块的实现（`film/`、`apps/`、`docs/designs`、迁移…）须按**强规则三**登记到 `docs/modules/M#-<中文名>.md` 的 `## 任务登记`，完成后回写 `## 变更记录`。规则全文见 [GOVERNANCE.md](GOVERNANCE.md) 强规则三与 `.agents/rules/module-dev-record.md`。

## 变更档位（先判档，不豁免机器门禁）

动手前先判档。**任何档位，三条必绿命令 + 强规则一/二/三的机器门禁都不可豁免**——档位只决定「可选仪式」（计划/规格/选举/红灯测试）做多少。

| 档位 | 判据 | 仪式 |
|------|------|------|
| **快路径** | 对**已机器验证**产物做局部修正：文档错字/断链、已复测覆盖的常量、已定位的 bug | 直接改；不写 `docs/plans`/`docs/spec`，不选举，不 TDD 红灯 |
| **轻量** | **已实现**模块内的局部行为（提示词模板、QC 阈值、局部 bugfix），不新增功能点、不改契约 | 简述决策后实现；按强规则三登记模块文档 §2/§4；跑聚焦验证 |
| **完整** | 新模块、新增功能点、改数据模型/API/契约、跨模块、需人类拍板 | 走 P1 工单 → `docs/designs`/`docs/plans` → 争议选举 → 领域逻辑红灯 → 全部门禁 |

**反向门禁**：任何档位中途发现要新增功能点、改契约/数据模型、跨模块，或撞上 `P1-实施计划` 第七节的 12 项人类拍板 → **停下，升到完整档**，别在快/轻里顺手做掉。

**默认值（与 audit-worker-platform 相反）**：AADO 是绿地项目，**新模块默认「完整」**；只有改动对象是「已机器验证的产物」时才降档。「别过度流程化」不等于「跳过机器门禁」。

执行/审计工作流见 `.agents/skills/execute-plan` 与 `.agents/skills/review-plan`（Codex 端 `.agents/skills/`，Cursor 端 `.cursor/skills/`）。

## 3. 工作方式（已在本项目验证有效，请沿用）

1. **争议不问人，走多智能体选举**：5 名独立评估员、背对背、多数决；平票加选。
   每位必须给：**胜出理由（带实读出处）/ 最大风险 / 强制缓解措施 / 落选方案核心诉求的低成本覆盖**。
   记录落在 `docs/plans/*选举记录.md`。**需要人类拍板 = 你没先跑选举。**
2. **结论必须能机器验证**：能写成断言的就别写成形容词；每条规则配一个违例样本（变异测试）。
3. **生成与复测分离**：生成器写产物；复测器**只读磁盘产物、不 import 生成器**、fail-closed。
4. **实测数据驱动文档**：报告由脚本生成，**禁止手抄数字**（本仓库已有手抄漂移的真实事故，见 `docs/plans/P1-待裁决清单.md` C-07）。
5. **对抗式自评迭代**：问「这套东西会被怎么执行错 / 怎么钻空子 / 怎么自证假通过」，
   然后**主动破坏产物**验证门禁是否真的拦得住，直到全绿。
6. **不冒充、不承诺未验证**：代理产物标 `PROXY — NOT A DELIVERABLE MASTER`（EL-16）；
   未取到原文的标准标「待补原文」，**不得作为验收阈值**；未达成退出标准就写 `false`。

## 4. 目录地图与归位规则

```text
AGENTS.md            ← 本文件：所有 Agent 的统一入口（单一事实来源）
CLAUDE.md            ← Claude Code 适配层（指向本文件）
GOVERNANCE.md        ← 两条强规则 + 合规三步
README.md            ← 面向人的仓库总览
PRD/                 ← 产品需求（唯一归档位置）：L1 00-项目背景 + M1..M19 模块 + 90..99 附录 + 两份台账
demo/                ← 可运行「规范合规模拟母版」代理样片（build_demo.py / verify.py / report.py / demo.html）
film/                ← P1-A 切片实现包：契约枚举 / 提示词编译 / 安全框几何 / 漂移 / 门禁字段契约 / 锚点互核
  fixtures/          ← 先导集构图几何声明 + 13 个违例样本（变异测试）
tools/               ← prd_guard.py（治理门禁）、build_p1_a.py、verify_p1_a.py、install-hooks.sh
out/p1a/             ← P1-A 产物（契约 / 提示词 / 安全框 / 漂移 / 预检 / 门禁收据 / 代理帧）
docs/README.md       ← 文档地图 + 归位约定（权威索引，改动必须同步）
docs/architecture.md ← 系统架构（技术选型 / 进程拓扑 / 模块映射）
docs/designs/        ← 技术设计（数据模型 / API 契约 / 任务编排 / 宿主基线 / 测试策略）
docs/plans/          ← 计划与决策（实施计划 / 切片方案 / 选举记录 / 待裁决清单）
docs/modules/        ← 模块级开发总入口（M1–M19，每模块一份；任务登记 + 变更记录，强规则三）
docs/spec/           ← 执行记录与验证证据（由脚本生成，禁止手抄）
docs/guid/           ← 部署 / 运维 / 使用指南（remote-deploy.md 远端部署规范，与 retail 三方隔离）
docs/agent-prd-method.md ← 八步工作流、关键机制、七类真实踩坑
```

**归位铁律**：需求 → `PRD/`；架构 → `docs/architecture.md`；技术设计 → `docs/designs/`；
计划与决策 → `docs/plans/`；验证证据 → `docs/spec/`；部署运维 → `docs/guid/`。
完整约定见 `docs/README.md`（权威索引，改动必须同步，断链/索引不一致会被门禁拦）。

## 5. 环境事实（不要假设，本机就是这些）

| 项 | 事实 |
|----|------|
| Python | **3.9.6**（venv 与系统同版本）→ **禁用 3.10+ 语法**（`match`、运行时 `X \| Y`、`dict \| dict`） |
| 依赖 | 只有 `.venv` 里有 `numpy` / `Pillow`（见 `demo/requirements.txt`）；**系统 `python3` 没有** |
| 无 ffmpeg | 视频封装/编码/响度工具链一律不可用 → 只能用纯 Python / numpy / Pillow 自证 |
| 无 GPU | 不跑任何本地大模型 |
| 无付费凭据 | 不调用任何付费 API；**重复付费调用必须恒为 0** |
| Node / pnpm | 可用（v25 / 11），但本仓库当前无前端构建 |

## 6. 每次收工的自检清单（可直接复制）

```bash
python3 tools/prd_guard.py --all                       # 期望：✓ …均满足
. .venv/bin/activate
(cd demo && python3 verify.py && python3 report.py)     # 期望：24/24
python3 tools/build_p1_a.py --out out/p1a               # 期望：checks_failed=0
python3 tools/verify_p1_a.py --out out/p1a --determinism \
  --report docs/spec/P1-A-验证记录.md                    # 期望：PASS，退出码 0
git status --short                                      # 期望：改动的文件都在预期内
```

收工报告必须包含：**做了什么 / 哪些是机器验证过的（给命令与数字）/ 哪些没验证（显式列出）/ 遗留与待裁决项**。

## 7. 真实踩过的坑（照做，别重犯）

| 坑 | 正确做法 |
|----|----------|
| 用系统 `python3` 跑 `demo/verify.py` → `ModuleNotFoundError: numpy` | 一律先 `. .venv/bin/activate` |
| 子代理同改一个目录 → 互相覆盖 | 每个 Agent/子代理只写自己那份文件；删旧件前先确认新件非空 |
| 以为 WebP 存了几帧就是几帧（有损编码会量化合并极暗帧） | **不假设，实测**；时基用时长效验而非帧数硬比 |
| 从自己的渲染结果取样做质量对比 → 恒为 0，无检验价值 | 从**有损编码后的产物**取样；并用负样本证明规则不是恒真 |
| 复测早于被检对象生成 → 0 分误判 | 严格「先生成 → 后复测」，复测脚本先校验产物存在且非空 |
| 文档数字手抄 → 与产物漂移 | 报告由脚本生成；文档只引用产物或脚本输出 |
| 子代理虚引不存在的依据编号 | 派发时给「必读清单 + 依据编号范围 + 禁止修改文件清单」；宁可标缺口也不许编造 |

## 8. 机器可读事实块（供 `tools/prd_guard.py --agent-docs` 校验，请保持键名不变）

```aado-facts
python_version = 3.9.6
ci_python_version = 3.12
venv_python = .venv/bin/python
requirements = demo/requirements.txt
demo_verify = demo/verify.py
demo_qc_expected = 24/24
slice_build = tools/build_p1_a.py
slice_verify = tools/verify_p1_a.py
slice_out = out/p1a
guard = tools/prd_guard.py
module_docs = docs/modules
ffmpeg = false
gpu = false
paid_api = false
max_parallel_writers = 1
```

## 9. 产物目录 `out/` 的纪律（踩过坑，务必遵守）

`out/p1a/` 是 P1-A 切片的**交接证据**（`docs/spec/P1-A-验证记录.md`、`PRD/97` 引用它），**已入库、不要删除**。
但它同时是**可复现产物**——任何人可用下面两条命令逐字节重建：

```bash
python3 tools/build_p1_a.py --out out/p1a
python3 tools/verify_p1_a.py --out out/p1a --determinism   # 必须带 --determinism，否则报告少一项
```

三条硬纪律：

1. **写临时产物一律用系统临时目录**（Python 用 `tempfile.mkdtemp()` 默认值，或显式 `dir='/tmp'`），
   **绝对不要** `tempfile.mkdtemp(dir='out')` / `dir=ROOT`——历史上这么做导致 12 个 `out/tmp*/` 目录、
   1630 个文件被 `git add -A` 误提交进仓库（2026-10-11，已清理）。`out/tmp*/` 现已进 `.gitignore`。
2. **不要用 `git add -A` / `git add .` 提交**。本仓库有多个生成目录（`out/`、`demo/out/`、`__pycache__/`），
   盲加会把产物与临时垃圾一起提交。用显式路径：`git add <具体文件或目录>`。
3. **`demo/out/` 与 `out/p1a/` 都是证据链**，清理前先确认它不是 `PRD/96`/`97`/`docs/spec/` 的引用来源。

## 10. 项目资产与进度（快照，接手先看这里）

### 已有资产（全部机器验证）

| 资产 | 位置 | 状态 |
|------|------|------|
| PRD 正文 | `PRD/00-项目背景.md` + `M1`~`M19` | 19 模块 / 631 功能点；状态、证据、编号、链接、依据 0 异常 |
| 选举决议 | `PRD/93-…` | D1–D14 + EL-01~EL-16（**约束性**） |
| 先导集演练 | `PRD/96-…` | 《回声》EP01 全链路走查 + 五门禁决策 |
| 可运行 Demo | `demo/`（入口 `demo/demo.html`） | 独立复测 **24/24** |
| 治理 | `GOVERNANCE.md` + `tools/prd_guard.py` + `.githooks/pre-commit` + CI | 提交与 CI 双重强制 |
| P1 主干切片 A | `film/` + `tools/build_p1_a.py` + `verify_p1_a.py` + `out/p1a/` | 预检 84/84、独立复测 62/62 |
| 开发交接包 | `docs/architecture.md` + `docs/designs/` + `docs/plans/` | 架构 / 设计 / 计划齐备 |

### 现在处在哪一步

- **已完成**：PRD 好莱坞级重构 + 两轮选举 + 先导集演练 + 规范合规 Demo + P1 切片 A + 开发交接包（架构/数据模型/API 契约/实施计划/测试策略）。
- **待启动**：P1 主干的**实现**（开发范式见 `docs/plans/P1-开发范式与自主决策协议.md`；工单见 `docs/plans/P1-实施计划.md`；第 0 批 M13/M15/M16 可直接开工）。
- **真机才能证的三项**：ACES IDT hero shot 往返、5.1 下混、口型引擎（`PRD/96` 的 G-02/G-03、EL-14）。
- **待补原文（不得作验收阈值）**：SAG-AFTRA 2026 MOA / WGA 2026 MBA / AB 1836 签署版 / 标识强制国标编号 / ΔE 与闪白 PSE 阈值。

### 边界（别踩）

1. **不要动宿主仓库** `retail-trading-odyssey`：本项目已独立，`apps/...:行号` 只是现状基线引用。
2. **不要把 PRD 当开发计划**：技术方案进 `docs/designs/`，计划进 `docs/plans/`，验证证据进 `docs/spec/`。
3. **不要绕过治理**：即使只改一行 PRD 说明也要登记（门禁会拦）。
4. **不要声称未验证的东西**：Demo 是 PROXY 代理样片，艺术质量维度不在其声称范围内。

## 11. 变更记录

> 本文件不是 PRD 文件，**不受**强规则一台账约束（该规则只管 `PRD/` 下的文件）；但仍保留追加型变更记录便于追溯。

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立：跨 harness 统一入口（三条必绿命令、5 条硬约束、6 条工作方式、目录归位铁律、环境事实、收工自检清单、7 条真实踩坑、机器可读事实块） |
| 2026-10-11 | Agent | 新增第 9 节「产物目录 `out/` 的纪律」：登记 12 个 `out/tmp*/`（1630 文件）被 `git add -A` 误提交的真实事故，明确「临时产物写系统临时目录」「禁用 `git add -A`」「`out/p1a` 与 `demo/out` 是证据链不可清理」三条硬纪律 |
| 2026-10-11 | Agent | 合并 HANDOFF.md：新增第 10 节「项目资产与进度」（资产表/进度快照/边界），目录地图更新 docs 结构（designs/plans/spec/guid），删除 HANDOFF.md 消除与 AGENTS 的重叠 |
| 2026-10-11 | Agent | 新增强规则三（开发任务必登记模块文档）：硬约束第 6 条、`docs/modules/` 目录、aado-facts 新增 `module_docs` 键 |
| 2026-10-11 | Agent | 新增「变更档位」（快/轻/完整 + 反向门禁，默认完整、不豁免机器门禁）与 `execute-plan`/`review-plan` 两个 skill（Codex `.agents/skills/` + Cursor `.cursor/skills/`） |
| 2026-10-11 | Agent | 新增远端部署规范与脚手架：`docs/guid/remote-deploy.md`、`docker-compose.prod.yml`（独立 postgres）、`.env.example`、`scripts/deploy-remote.sh`；与 retail 目录/数据卷/数据库三方隔离 |
| 2026-10-11 | Agent | 新增 P1 开发范式与自主决策协议：六步流水线、模块级范围、文档不漂移、开源参考政策；选举替代人类拍板（12 项拍板分类处置） |
