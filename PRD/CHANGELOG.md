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
| CR-20261011-007 | 2026-10-11 | 修订 | L1 | `PRD/00-项目背景.md`<br>`PRD/90-评审与验收清单.md`<br>`PRD/M4-分镜previz与导演台.md`<br>`PRD/M5-电影摄影与画面生成.md` | 依 5 人选举裁决冻结实现冲突 C-01~C-04/C-06/C-09：90 号 NFR-09/10 对齐 L1 口径（画幅安全框/帧率运动）；景深二值 canonical（M4 保留浅/中/深别名）；CCT 扩六档含 3000K；焦距六档名与 mm 一一对齐；P1 退出标准的响度/TC 明确由 M11 母版 QC 承担（M8/M9 留 P2）；90 自查项扩到 EL-16 | D1、D4、D5、EL-01、EL-02、EL-07、EL-09、NFR-09、NFR-10、NFR-13、A-11、A-30、A-33 | Agent |
| CR-20261011-008 | 2026-10-11 | 修订 | 附录 | `PRD/96-先导集演练.md` | 依 C-07 修复 96 §8 手抄漂移：Demo 实测值对齐 qc_report.json（真峰值 -4.61 dBTP / 288 内容帧 / 字幕 5.5s×2 / ΔE 1.61），杜绝与自动生成的 97 号报告双事实源 | B-21、B-32、B-33、B-88、EL-09 | Agent |
| CR-20261011-009 | 2026-10-11 | 修订 | 附录 | `PRD/97-Demo验证报告.md` | C-08 返修 demo（S03/S04/S07 构图参数修正，多画幅安全框合规）后由 report.py 重生成 97 号：字幕安全区实测 box 随 re-render 更新；同时 report.py 改为追加型+幂等，避免覆盖变更记录历史 | D1、EL-02、NFR-09、B-16 | Agent |
| CR-20261011-010 | 2026-10-11 | 治理 | 治理 | `PRD/CHANGELOG.md`<br>`PRD/changelog.jsonl` | 本轮「可开发交接包」的台账追加登记：CR-20261011-007（冲突冻结 C-01~C-04/C-06/C-09）、CR-008（C-07 手抄漂移修复）、CR-009（C-08 demo 返修重生成 97 号）；CHANGELOG.md 与 changelog.jsonl 随之追加 | D1、D4、D5、EL-01、EL-02、EL-07、EL-09、NFR-09、NFR-10、NFR-13、A-11、A-30、A-33、B-16、B-21、B-32、B-33、B-88 | Agent |
