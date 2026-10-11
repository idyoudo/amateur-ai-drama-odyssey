# CLAUDE.md —— Claude Code 开发启动指引

> 本文件在你打开仓库时**自动加载**，讲清**前因后果 + 从哪开工 + 别踩什么**，让你无需翻历史就能上手。
> 规则手册见 [AGENTS.md](AGENTS.md)（硬约束/命令/环境事实）；架构见 [docs/architecture.md](docs/architecture.md)；
> 工单见 [docs/plans/P1-实施计划.md](docs/plans/P1-实施计划.md)。

## 前因：这是什么项目、从哪来

**AADO（Amateur AI Drama Odyssey）**＝好莱坞级 AI 短剧产品，端到端链路：
小说 → 剧本 → 选角定妆 → 分镜 previz → 电影摄影 → 一致性与连续性 → 表演配音口型 → 声音设计与配乐 → 剪辑 → 调色母版 QC → 交付 → VFX → 法律合规。

- 它从交易项目 `retail-trading-odyssey` **独立**出来；PRD 里的 `RTO` / `apps/...:行号` 是**宿主基线的现状参考，本项目不继承其架构**（详情见 `docs/designs/宿主基线映射.md`）。
- **首季包型**：6 集 × 30 分钟（D7），首集《回声》都市悬疑（D13）；**主母版规格** 2.39:1 / 24fps / Rec.709 SDR / −23.0 LUFS / ≤−1 dBTP / 24-bit 48 kHz（D1/D3/D4/D5）。

## 后果：已经做到哪一步了

| 已完成 | 状态 |
|--------|------|
| PRD | 19 模块 / 631 功能点，两轮选举 D1–D14 + 硬性要求 EL-01~EL-16，结构 0 异常 |
| Demo | 「规范合规模拟母版」代理样片，独立复测 **24/24** |
| P1 切片 A | 镜头契约 + 安全框预检（`film/` + `tools/`），独立复测 **62/62** |
| 开发交接包 | 架构 + 数据模型 + API 契约 + 任务编排 + 实施计划 + 测试策略（`docs/`） |

**结论：需求与设计阶段全部完成，你的任务是 P1 主干的「实现」。** PRD 是"要什么"，实现方案在 `docs/`，别把实现细节写回 PRD。

## 关键决策（已定，别重新发明）

1. **技术栈：Python monorepo**（FastAPI + SQLAlchemy/Alembic + PostgreSQL + PG 自建队列 `SKIP LOCKED`），**不是 TypeScript**——理由见 `docs/architecture.md` 第一节。两个 TS 参考项目只借鉴其**模式**（队列/幂等/intent log/fencing），不用其语言。
2. **环境约束**：无 ffmpeg / 无 GPU / 无付费凭据。媒体/QC 用纯 Python 降级路径自证（demo 已示范 BS.1770 响度、Pillow 几何/ΔE）；生产可加 ffmpeg 走加速路径。
3. **争议不问人，走 5 人多智能体选举**（多数决、平票加选），记录落 `docs/plans/*选举记录.md`。需要人类拍板 = 你没先跑选举。
4. **改 `PRD/` 任何文件必登记三处台账**（CHANGELOG + changelog.jsonl + 文件内变更记录），否则提交被钩子拒绝。
5. **文档归位约定**（权威索引 `docs/README.md`）：架构→`docs/architecture.md`；技术设计→`docs/designs/`；计划决策→`docs/plans/`；验证证据→`docs/spec/`；部署运维→`docs/guid/`。**断链或索引不一致会被 `prd_guard --all` 拦。**
6. **变更档位（先判档）**：快路径/轻量/完整三档，只门控「可选仪式」（计划/规格/选举/红灯），**不豁免**三条必绿命令与强规则一/三；新模块默认完整。执行/审计工作流见 `.agents/skills/`（Codex）与 `.cursor/skills/`（Cursor）

## 从哪里开工

先读 [docs/plans/P1-实施计划.md](docs/plans/P1-实施计划.md)。要点：

- **第 0 批无阻塞，可直接开工**：M13 任务编排（队列/幂等/checkpoint）、M15 存储与血缘、M16 权限矩阵。
- 第 1 批（P1 上游串行）：M1 立项 → M2 剧本 → M3 定妆 → M4/M5 契约（切片 A 已打底）。
- **开工前有 12 项必须人类拍板**（P1-实施计划第七节）：M6 标定样本、NFR-04 成本目标、工具链采买、供应商选型、法务原文、M19 自建/外包、盲评人力、ACES IDT 形态、InsightFace 替代、门禁署名岗位等。**先把对应模块的拍板项问清楚再动手，别空写代码。**

## 必读文档（按顺序）

1. [AGENTS.md](AGENTS.md) —— 硬约束、三条必绿命令、环境事实、产物纪律
2. [docs/architecture.md](docs/architecture.md) —— 技术选型 + 19 模块→代码包映射 + 宿主基线边界
3. [docs/plans/P1-实施计划.md](docs/plans/P1-实施计划.md) —— 工单拆分 + 依赖 + 验收命令 + 12 项拍板
4. [docs/designs/](docs/designs/) —— 数据模型 / API 契约 / 任务编排 / 测试策略（动手前按需）
5. [docs/modules/](docs/modules/) —— 模块级开发总入口（强规则三：开发前必读、开工登记、完成回写）

## 收工前必跑（全绿才算完成）

```bash
python3 tools/prd_guard.py --all                     # 期望 ✓（强规则 + 断链 + 索引 + agent-docs）
. .venv/bin/activate
(cd demo && python3 verify.py && python3 report.py)   # 期望 24/24
python3 tools/build_p1_a.py --out out/p1a             # 期望 checks_failed=0
python3 tools/verify_p1_a.py --out out/p1a --determinism
```

## Claude Code 专属注意事项

1. **Python 一律用 `.venv`**：系统 `python3` 没有 numpy/Pillow；只有 `python3 tools/prd_guard.py` 这类纯标准库脚本可直接跑。
2. **语言版本 3.9.6**：禁 3.10+ 语法（`match`、运行时 `X | Y`、`dict | dict`）。
3. **不要交互式提问**：争议走选举（见「关键决策」第 3 条）。
4. **改了 `PRD/` 就登记三处台账**（见「关键决策」第 4 条），模板见 AGENTS.md 第 2 节。
5. **长命令放后台**：`demo/build_demo.py`、`verify_p1_a.py --determinism` 是分钟级任务。
6. **`.claude/worktrees/`**：Claude Code 的 worktree 会整份复制仓库，在那里改动**主线看不到**，收工前确认动的是主线。
7. **删文件前先确认替代件非空**；**不要清理 `demo/out/` 和 `out/p1a/`**（是 PRD/96、97、docs/spec 的证据链）。
8. **单写者约定**（`max_parallel_writers = 1`）：多 Agent 并行时子代理只写各自文件，不并发改同一目录。
9. **提交纪律**：`git add` 用显式路径、**禁用 `git add -A`**（会盲加生成产物）；临时产物写系统临时目录 `/tmp`。

## 变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立 Claude Code 适配层：指向 AGENTS.md 作为唯一事实来源，只保留 Claude Code 专属注意事项 |
| 2026-10-11 | Agent | 升级为「开发启动指引」：新增前因（项目从哪来）、后果（已完成到什么程度）、关键决策（技术栈/环境/选举/台账/归位）、从哪开工（第 0 批 + 12 项拍板）、必读文档；保留收工命令与 9 条专属注意 |
| 2026-10-11 | Agent | 新增强规则三指引：必读文档增补 `docs/modules/`（模块开发总入口，开发前必读、开工登记、完成回写），与 `.agents/rules/module-dev-record.md` 对齐 |
| 2026-10-11 | Agent | 新增「变更档位」关键决策（快/轻/完整 + 反向门禁，默认完整、不豁免机器门禁），并指向 `execute-plan`/`review-plan` 两个 skill |
