---
name: review-plan
description: Audits whether work matches the user request, git diff, and project constraints. Use when the user asks to review, audit, inspect, or evaluate implementation or plan execution. Fast/light work may have no docs/plans or docs/spec — do not treat that as a defect, but missing machine evidence or missing module-doc registration is.
---

# Review Plan（Cursor 入口）

权威流程以 `.agents/skills/review-plan/SKILL.md` 为准，不要在此复制正文。

## 必做

1. Read `.agents/skills/review-plan/SKILL.md` 并遵循。
2. 先按 `AGENTS.md` 变更档位分级；快/轻按请求和 diff 审计，完整档再读 architecture / designs / plans。
3. 对照强规则一/三：PRD 台账齐备、模块文档 §2/§4 登记回写；缺登记或缺机器验证证据记为违规。

## Cursor 环境适配

- 默认只读；用户明确要求修复才改代码。
- 输出简体中文；问题优先。
- 快/轻没有执行规格或 checkpoint，不视为缺陷。
