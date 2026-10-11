---
name: execute-plan
description: Use when the user asks to implement, 修, 改, 优化, 落地, run tests, or create a git commit. Fast/light changes to already machine-verified artifacts implement directly; full-lane needs the P1 work order + design.
---

# Execute Plan（Cursor 入口）

权威流程以 `.agents/skills/execute-plan/SKILL.md` 为准，不要在此复制正文。

## 必做

1. Read `.agents/skills/execute-plan/SKILL.md` 并遵循。先按 `AGENTS.md` 变更档位判档；快/轻不要写 `docs/plans`/`docs/spec`，但**不豁免**三条必绿命令与强规则一/三。
2. 强规则三：触及 `M#` 模块先 Read 对应 `docs/modules/M#-*.md`，开工登记 §2、收尾回写 §4。
3. `git add` 用显式路径、禁用 `git add -A`；不因本次改动 stash 搬运。
