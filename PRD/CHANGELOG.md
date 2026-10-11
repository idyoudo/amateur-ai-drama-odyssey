# PRD 变更台账（强规则一）

> **任何 PRD 文件的新增、修订、删除、状态流转都必须在此登记**，并在 `PRD/changelog.jsonl` 写入同一 id 的机器可读条目，同时在被改文件内追加 `## 变更记录` 行。
> 台账是**追加型**：禁止删除既有行、禁止复用 id。校验：`python3 tools/prd_guard.py --all`；提交时由 `.githooks/pre-commit` 自动阻断违规。

| 条目 | 日期 | 类型 | 级别 | 文件 | 摘要 | 依据 | 修订人 |
|------|------|------|------|------|------|------|--------|
| CR-20261011-001 | $ISO | 治理 | 治理 | `PRD/*.md`（31 个随迁文件，README.md 见 CR-20261011-006） | AI 短剧 PRD 与 Demo 由 retail-trading-odyssey 迁出，建立独立项目 amateur-ai-drama-odyssey；PRD 全量随迁（31 文件） | AADO 独立立项 | Agent |
| CR-20261011-002 | $ISO | 修订 | L1 | `PRD/README.md`<br>`PRD/00-项目背景.md`<br>`PRD/93-决策选举记录.md` | 项目定名 Amateur AI Drama Odyssey（amateur-ai-drama-odyssey，AADO）；明确「RTO」为宿主平台；补充证据口径与跨目录引用约定 | AADO 命名 | Agent |
| CR-20261011-003 | $ISO | 修订 | L2 | `PRD/M2-剧作开发与剧本.md`<br>`PRD/M4-分镜previz与导演台.md` | 把 55 处链接式代码引用规范化为 `path:行号` 代码引用（修断链并满足证据格式规则） | E-04 | Agent |
| CR-20261011-004 | $ISO | 治理 | 治理 | `GOVERNANCE.md`<br>`tools/prd_guard.py`<br>`.githooks/pre-commit`<br>`.github/workflows/prd-guard.yml`<br>`PRD/CHANGELOG.md`<br>`PRD/changelog.jsonl` | 建立两条强规则：强规则一（PRD 变更必登记：三处台账）、强规则二（两个稳定：项目级文档唯一 / 功能必归模块）；配套门禁脚本、预提交钩子与 CI | D6、EL-10 | Agent |
| CR-20261011-005 | $ISO | 修订 | 附录 | `PRD/M16-工作区与协作.md`<br>`PRD/99-业界对标与调研.md`<br>`PRD/94-自评与修订记录.md` | 修复治理门禁首跑发现的真实缺陷：M16.4-F07 补代码证据；99 的三处悬空/过期编号（A-23、D-13、D-15）与重编号表述；94 的编号范围表述 | EL-10 | Agent |
| CR-20261011-006 | 2026-10-11 | 修订 | L1 | `PRD/README.md` | PRD/README 新增「十、治理（强规则）」与变更记录章节，登记两条强规则的入口与自检命令 | D6、EL-10 | Agent |
