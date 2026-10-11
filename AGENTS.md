# AGENTS.md —— 所有 AI Agent 的统一入口（单一事实来源）

> **任何 Agent harness（Claude Code / DeepSeek Harness / Codex / Cursor / Gemini CLI …）接手本仓库，先读本文件。**
> Claude Code 另见 [CLAUDE.md](CLAUDE.md)（薄适配层，指向本文件，不复制内容）。
> 人类交接简报见 [HANDOFF.md](HANDOFF.md)；治理规则见 [GOVERNANCE.md](GOVERNANCE.md)；工作方法见 [docs/agent-prd-method.md](docs/agent-prd-method.md)。

---

## 0. 这是什么项目

**Amateur AI Drama Odyssey**（`amateur-ai-drama-odyssey`，缩写 **AADO**）：一套「好莱坞级 AI 短剧」产品——
从小说到成片母版的完整链路（剧本开发 → 选角定妆 → 分镜 previz → 电影摄影 → 一致性与连续性 →
表演配音口型 → 声音设计与配乐 → 剪辑 → 调色母版 QC → 交付 → VFX → 法律合规）。

- 它**已从交易项目 `retail-trading-odyssey` 独立**，与交易业务无关。**绝对不要改动宿主仓库。**
- PRD 中的 **「RTO」＝宿主平台与既有实现基线**，不是本项目名；`apps/...:行号` 只是「现状基线」引用，
  本项目按 PRD 重新实现，**不继承其架构约束**。
- **PRD 回答「要什么、为什么、怎样算达标」；不写「怎么实现」。** 实现方案进 `docs/plans/`，
  执行记录与验证证据进 `docs/spec/`，架构说明进 `docs/architecture.md`。

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

合规改动姿势（唯一正确写法）：

```bash
# 1) 改 PRD 文件（模块内登记功能点；新增模块则同时改 L1 地图与 README 索引）
# 2) 生成台账条目（自动填 id/date/files）
python3 tools/prd_guard.py --new-entry --type 修订 --level L2 \
  --files PRD/M5-电影摄影与画面生成.md --refs D7 --summary "说明改了什么与为什么"
# 3) 提交（钩子自动校验）
git add -A && git commit -m "docs(prd): …"
```

> 只改 `PRD/` 以外的文件（代码、docs/plans、docs/spec、README、AGENTS.md…）**不需要**台账登记。

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
HANDOFF.md           ← 人类交接简报（短版开场 + 完整简报）
GOVERNANCE.md        ← 两条强规则 + 合规三步
README.md            ← 面向人的仓库总览
PRD/                 ← 产品需求（唯一归档位置）：L1 00-项目背景 + M1..M19 模块 + 90..99 附录 + 两份台账
demo/                ← 可运行「规范合规模拟母版」代理样片（build_demo.py / verify.py / report.py / demo.html）
film/                ← P1-A 切片实现包：契约枚举 / 提示词编译 / 安全框几何 / 漂移 / 门禁字段契约 / 锚点互核
  fixtures/          ← 先导集构图几何声明 + 13 个违例样本（变异测试）
tools/               ← prd_guard.py（治理门禁）、build_p1_a.py、verify_p1_a.py、install-hooks.sh
out/p1a/             ← P1-A 产物（契约 / 提示词 / 安全框 / 漂移 / 预检 / 门禁收据 / 代理帧）
docs/plans/          ← 开发计划与实现方案（怎么实现）＋ 选举记录 ＋ 待裁决清单
docs/spec/           ← 执行记录与验证证据（由脚本生成，禁止手抄）
docs/agent-prd-method.md ← 八步工作流、关键机制、七类真实踩坑
```

**归位铁律**：需求 → `PRD/`；怎么实现 → `docs/plans/`；验证证据 → `docs/spec/`。
把实现细节写进 PRD 会被评审打回；把需求写进 `docs/plans/` 会与 PRD 漂移。

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
ffmpeg = false
gpu = false
paid_api = false
max_parallel_writers = 1
```

## 9. 变更记录

> 本文件不是 PRD 文件，**不受**强规则一台账约束（该规则只管 `PRD/` 下的文件）；但仍保留追加型变更记录便于追溯。

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立：跨 harness 统一入口（三条必绿命令、5 条硬约束、6 条工作方式、目录归位铁律、环境事实、收工自检清单、7 条真实踩坑、机器可读事实块） |
