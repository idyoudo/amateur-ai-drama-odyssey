# P1-A 切片独立复测记录（由 tools/verify_p1_a.py 生成，禁止手抄）

> 被检对象：`out/p1a`｜复测脚本：`tools/verify_p1_a.py`（只读磁盘产物）
> 代理声明：PROXY — NOT A DELIVERABLE MASTER
> P1 退出标准进展：**未达成**（本切片只推进 M4/M5 契约层）

## 一、汇总

| 项 | 值 |
|----|----|
| 检查项总数 | 62 |
| 通过 | 62 |
| 失败 | 0 |
| 通过率 | 100.00% |
| 结论 | **PASS** |

## 二、逐项结果

| # | 检查项 | 实测 | 判据 | 结论 |
|---|--------|------|------|------|
| 1 | 产物存在且非空 | 13/13 | 全部必需产物存在且 size>0 | PASS |
| 2 | 预检自洽 | total=84 pass=84 fail=0 | fail 计数与 failed_checks 长度一致 | PASS |
| 3 | 提示词 sha256 ↔ 快照一致 | 8 条 | prompt_pack.sha256 与 prompts.json 逐条一致 | PASS |
| 4 | 确定性双跑（PYTHONHASHSEED/TZ/LANG 不同） | 两跑产物字节一致 | 同输入必须字节级一致 | PASS |
| 5 | 契约镜数 ↔ 产物镜数 | 8 / 8 | PRD 解析结果与 contract.json 一致 | PASS |
| 6 | 契约字段 ↔ 产物字段 | 逐字段比对 8 镜 | contract.json 与 PRD 解析结果逐字段一致 | PASS |
| 7 | 契约字段可反查 PRD 原文 | 自报 all_match=True；实测 8/8 镜逐字段一致 | table_source.json 必须证明每个表内字段都来自 PRD 原文（禁手抄） | PASS |
| 8 | PRD 表未提供字段已显式登记为默认值 | 21 类 | 表未提供的字段（角度/速度/景深/布光/几何等）必须显式声明为默认值并带来源 | PASS |
| 9 | 像素测量 S01 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 10 | 像素级 9:16 安全框 S01 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 11 | 像素级水平可裁切 S01 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 12 | 像素测量 S02 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 13 | 像素级 9:16 安全框 S02 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 14 | 像素级水平可裁切 S02 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 15 | 像素测量 S03 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 16 | 像素级 9:16 安全框 S03 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 17 | 像素级水平可裁切 S03 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 18 | 像素测量 S04 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 19 | 像素级 9:16 安全框 S04 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 20 | 像素级水平可裁切 S04 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 21 | 像素测量 S05 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 22 | 像素级 9:16 安全框 S05 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 23 | 像素级水平可裁切 S05 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 24 | 像素测量 S06 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 25 | 像素级 9:16 安全框 S06 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 26 | 像素级水平可裁切 S06 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 27 | 像素测量 S07 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 28 | 像素级 9:16 安全框 S07 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 29 | 像素级水平可裁切 S07 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 30 | 像素测量 S08 与声明包围盒一致 | max_dev=1px（tol=3） | 由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致 | PASS |
| 31 | 像素级 9:16 安全框 S08 | 越界像素=0 | M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0 | PASS |
| 32 | 像素级水平可裁切 S08 | 水平越界 max=0 | M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景） | PASS |
| 33 | 9:16 关键信息出框镜数 | 0 镜 | M4.7-F02：9:16 关键信息出框镜数 = 0 | PASS |
| 34 | 关键信息区落在三画幅 action safe 内 | 越界 0 处 | NFR-09 + EL-02：关键信息区（头顶至颈部）必须落在三窗 action safe 内 | PASS |
| 35 | 锚点互核：返修后参考实现 8/8 合规（C-08 已落地） | 0/8 镜不合格 | S03/S04/S07 返修后（C-08 选举决议）必须 0 不合格 | PASS |
| 36 | 锚点互核：返修前 S03(x=0.58) 必须被判不合格（规则有牙） | 命中画幅=['239-action-safe', '916', '916-action-safe'] | 同一判据必须能检出返修前的真实缺陷（证伪「恒真断言」） | PASS |
| 37 | 锚点互核不越权否定 demo 结论 | 参考实现（demo/）的 24/24 机检结论**不受本互核否定**：其判据集合… | 必须声明「不否定 demo 24/24 机检结论」并说明判据差异 | PASS |
| 38 | 漂移告警可定位 | 4 条告警 | M4.2-F04：每条漂移告警必须带镜号与场次 | PASS |
| 39 | P1-A-05 场景内色温漂移被发现 | kinds=['cct', 'lens'] | SC-EP01-02 内 3000K 与 3200K 并存必须产出 cct 告警（96 表 S07 与 M5.3-F05 封闭档的冲突） | PASS |
| 40 | 变异 mut_cct_closed 被拒 | 构造期 ContractError | R-CCT-CLOSED 必须 FAIL | PASS |
| 41 | 变异 mut_cct_drift 命中 R-DRIFT-cct | failed=['R-CCT-CLOSED'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-DRIFT-cct 必须被检出（FAIL 或漂移告警） | PASS |
| 42 | 变异 mut_clock_drift 命中 R-DRIFT-clock | failed=[] drift=['R-DRIFT-cct', 'R-DRIFT-clock', 'R-DRIFT-lens'] | R-DRIFT-clock 必须被检出（FAIL 或漂移告警） | PASS |
| 43 | 变异 mut_critical_actionsafe 命中 R-SAFEFRAME | failed=['R-SAFEFRAME'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-SAFEFRAME 必须被检出（FAIL 或漂移告警） | PASS |
| 44 | 变异 mut_dolly_zoom 命中 R-DOLLY-ZOOM | failed=['R-DOLLY-ZOOM'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-DOLLY-ZOOM 必须被检出（FAIL 或漂移告警） | PASS |
| 45 | 变异 mut_domain_bounds 命中 R-DOMAIN-BOUNDS | failed=['R-DOMAIN-BOUNDS', 'R-SAFEFRAME'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-DOMAIN-BOUNDS 必须被检出（FAIL 或漂移告警） | PASS |
| 46 | 变异 mut_face_pattern 命中 R-FACE-PATTERN | failed=['R-FACE-PATTERN'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-FACE-PATTERN 必须被检出（FAIL 或漂移告警） | PASS |
| 47 | 变异 mut_fill_key 命中 R-FILL-KEY | failed=['R-FILL-KEY'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-FILL-KEY 必须被检出（FAIL 或漂移告警） | PASS |
| 48 | 变异 mut_lens_drift 命中 R-DRIFT-lens | failed=[] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-DRIFT-lens 必须被检出（FAIL 或漂移告警） | PASS |
| 49 | 变异 mut_light_contract 命中 R-LIGHT-CONTRACT | failed=['R-LIGHT-CONTRACT'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-LIGHT-CONTRACT 必须被检出（FAIL 或漂移告警） | PASS |
| 50 | 变异 mut_one_move 命中 R-ONE-MOVE | failed=['R-ONE-MOVE'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-ONE-MOVE 必须被检出（FAIL 或漂移告警） | PASS |
| 51 | 变异 mut_safeframe 命中 R-SAFEFRAME | failed=['R-SAFEFRAME'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-SAFEFRAME 必须被检出（FAIL 或漂移告警） | PASS |
| 52 | 变异 mut_safety_basis 命中 R-SAFETY-BASIS | failed=['R-SAFETY-BASIS'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-SAFETY-BASIS 必须被检出（FAIL 或漂移告警） | PASS |
| 53 | 变异 mut_volumetric_media 命中 R-VOLUMETRIC-MEDIA | failed=['R-VOLUMETRIC-MEDIA'] drift=['R-DRIFT-cct', 'R-DRIFT-lens'] | R-VOLUMETRIC-MEDIA 必须被检出（FAIL 或漂移告警） | PASS |
| 54 | 规则注册表 ↔ 变异样本配平 | 规则 14 条 / 变异 13 条 / 豁免 1 条 | 每条规则要么有变异样本、要么登记豁免；变异不得指向未注册规则 | PASS |
| 55 | 门禁收据字段齐备 | 违规 0 项 | M10.3-F02/F03 + D6：署名/理由码/时间戳/二元清单齐备；AI 覆盖须留痕；无署名不得给出通过结论 | PASS |
| 56 | 门禁收据不冒充人工署名 | PENDING-HUMAN-SIGNATURE | 占位署名 + 无时间戳时必须为 pending/reject，不得为 pass | PASS |
| 57 | 代理声明（EL-16） | PROXY — NOT A DELIVERABLE MASTER | 产物必须标注 PROXY — NOT A DELIVERABLE MASTER | PASS |
| 58 | P1 退出标准进展诚实字段 | False | p1_exit_criteria_advanced 必须为 false（本切片不覆盖 −23 LUFS / TC） | PASS |
| 59 | 未验证清单非空 | 8 项 | 必须显式列出未验证项（D12 缓解措施 3） | PASS |
| 60 | 项目自定阈值均带来源 | 7 条 | B-88 / 90 号第九章：项目自定阈值必须写明来源 | PASS |
| 61 | 负样本：参考实现原构图 S03(x=0.58)：9:16 右溢 | 命中 1 镜 | 必须触发 9:16 出框 的 R-SAFEFRAME FAIL | PASS |
| 62 | 负样本：参考实现原构图 S07(y=0.66)：关键信息越出 action safe | 命中 1 镜 | 必须触发 action safe 越界 的 R-SAFEFRAME FAIL | PASS |

## 三、未验证项（不得作为验收结论引用）

- 真实生成模型对提示词契约的遵从度（本切片不调用任何付费模型）
- ACES IDT 与色卡往返（96 号 G-02/G-03）
- ProRes 母版编码与 TC 嵌入（NFR-13；无 ffmpeg）
- 5.1 下混兼容（96 号 G-04）
- 口型同步与音画偏移（96 号 G-05；NFR-07）
- EDL/AAF 回批（96 号 G-06）
- −23 LUFS 归档母版（本切片的代理音频来自既有 demo/ 产物，不是本切片产出）
- PP1 退出标准的完整达成——本切片只推进 M4/M5 契约层

## 四、复现命令

```bash
python3 tools/build_p1_a.py --out out/p1a
python3 tools/verify_p1_a.py --out out/p1a --report docs/spec/P1-A-验证记录.md
cd demo && python3 verify.py && python3 report.py
python3 tools/prd_guard.py --all
```

