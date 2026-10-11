# Cursor / Codex Skills 共存说明

本仓库同时支持 Codex 与 Cursor，**正文只维护一份**。

| 用途 | 路径 |
|------|------|
| Codex 权威 skill（含 `agents/openai.yaml`） | `.agents/skills/<name>/` |
| Cursor 发现入口（薄包装，指向权威正文） | `.cursor/skills/<name>/SKILL.md` |

当前 skill：`execute-plan`、`review-plan`。

## 规则（rules）

强规则正文放 `.agents/rules/*.md`（权威）；Cursor 端在 `.cursor/rules/*.mdc` 放同义的 alwaysApply 短版，并在 `AGENTS.md` 与相关 skill 里引用。改规则时先改 `.agents/rules`，再同步 `.mdc` 与引用处。当前：`module-dev-record`（开发任务必登记模块文档，强规则三）。

## 维护规则

1. 改流程、门禁、模板时，只改 `.agents/skills/*/SKILL.md`（及 Codex 的 `agents/openai.yaml`）。
2. `.cursor/skills/*/SKILL.md` 只保留 frontmatter、Read 指向与 Cursor 工具名映射；不要把完整流程抄两份。
3. 新增 skill：先在 `.agents/skills` 落地，再补同名 Cursor 入口。

## 档位

实现默认先判档（见 `AGENTS.md`「变更档位」）。AADO 是绿地，新模块默认「完整」，只对已机器验证产物走快/轻。**任何档位不豁免三条必绿命令与强规则一/三**。
