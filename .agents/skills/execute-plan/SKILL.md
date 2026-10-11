---
name: execute-plan
description: Use when the user asks to implement, 修, 改, 优化, 落地, run tests, or create a git commit. Fast/light changes to already machine-verified artifacts implement directly. Full-lane (new module, new feature point, data model/API/contract change, cross-module, or human decision) needs the P1 work order + design.
---

# Execute Plan（AADO）

用于实现、验证、按用户要求创建本地 commit。不得 push、创建 PR、改 git config 或做破坏性 git 操作，除非用户明确要求。

按 `AGENTS.md` 的「变更档位」判档（常驻规则，不必再 Read）。`docs/plans/P1-实施计划.md` 与 `docs/modules/M#-<中文名>.md` 仅完整档必读；快/轻只打开将改的文件。

## 强规则（先于档位，任何档位都不可跳过）

1. **强规则一（PRD 台账）**：改 `PRD/` 任何文件必须三处登记（`prd_guard.py --new-entry`），否则提交被钩子拒绝。
2. **强规则三（模块文档登记）**：触及 `M#` 模块的实现/改动/排查/文档/迁移，动手前 Read `docs/modules/M#-<中文名>.md` 的 §1/§2/§4；开工在 §2 登记一行（`M#-TNN`）、收尾在 §4 回写。没做完不算完成。
3. 用户本轮明确说「不登记」时可跳过第 2 步的登记/回写，回复里注明；「开发前必读」不可跳过。

## 档位（先判定；AADO 是绿地，默认完整）

- **快路径**：对**已机器验证**产物做局部修正（文档错字/断链、已复测覆盖的常量、已定位的 bug）。直接改，不写 `docs/plans`/`docs/spec`、不选举、不红灯。
- **轻量**：**已实现**模块内的局部行为（提示词模板、QC 阈值、局部 bugfix），不新增功能点、不改契约。简述决策后实现。
- **完整**：新模块、新增功能点、改数据模型/API/契约、跨模块、需人类拍板。

反向门禁：中途发现要新增功能点、改契约/数据模型、跨模块，或撞上 `P1-实施计划` 第七节的 12 项人类拍板 → 停下升到完整档，别在快/轻里顺手做掉。

## 快路径 / 轻量

1. `git status --short` 确认范围，不覆盖用户无关改动。
2. 改代码。
3. 跑**聚焦验证**：改动涉及的复测脚本（`demo/verify.py`、`verify_p1_a.py` 等）；不要无脑跑全部三条命令，除非改动可能影响全局。
4. 按强规则三回写模块文档 §2/§4。
5. 回复：改了什么、怎么验证、未提交项。不写 `docs/spec`、不勾 checkpoint。

## 完整

1. 认领/确认 `P1-实施计划` 工单（`W#-#`），缺失则本轮补。
2. 读 `docs/architecture.md` 对应章节 + 相关 `docs/designs/` + `docs/modules/M#-*.md` 总入口。
3. 有争议走 5 人选举（不直接问人）；需人类拍板项先列清再动手。
4. 领域逻辑 / API 行为 TDD 红灯先行；UI/文案/夹具不强制。
5. 实现 + 跑**全部门禁**（三条必绿命令）；生成与复测分离、复测器只读磁盘产物。
6. 状态流转：PRD 功能点「已实现」须带 `path:行号` 证据 + 强规则一登记；模块文档 §2/§4 回写。
7. 用户要求提交时才 commit。

## 验证

- 默认聚焦：改动涉及的复测脚本 + `python3 tools/prd_guard.py --all`。
- 禁止为证明会失败先跑整包；禁止跳过 `--determinism` 复测。
- 媒体/QC 结论必须能机器验证，禁止手抄数字；严格「先生成 → 后复测」。

## 提交

仅用户明确要求时。`git add` 用显式路径、**禁用 `git add -A`**（盲加产物）。只 stage 本次文件，排除 `out/tmp*/`、`__pycache__/`、`.env`、密钥、无关改动。提交信息 `<type>: <中文摘要>`。失败不 amend、不 `--no-verify`。

## 禁止

- 以「没有计划文件」为由拒绝快/轻实现，或写完文档才肯动代码。
- 快/轻写执行规格或 checkpoint；完整档以外强制 TDD 红灯。
- 因本次改动新开分支或 stash 搬运。
- 为「保险」整体裸跑 `git diff`、列出整个 `docs/plans`/`docs/spec`。
- 用「别过度流程化」当借口跳过机器门禁（三条命令 + 强规则一/三永远要绿）。
