# P1-A · 镜头契约与安全框预检闭环（实现方案）

> 本文是**实现方案**，不是需求。需求见 [PRD/90-评审与验收清单.md](../../PRD/90-评审与验收清单.md) 第五章 P0 缺口与各模块文件；本文归位见 [PRD/README.md](../../PRD/README.md)「不属于本目录」表。
> 切片范围由选举裁决，票型与异议见 [P1-A-选举记录.md](P1-A-选举记录.md)。实测发现的 PRD 内部冲突见 [P1-待裁决清单.md](P1-待裁决清单.md)。
> 验证证据：`out/p1a/verify_report.json` 与由脚本生成的 [docs/spec/P1-A-验证记录.md](../spec/P1-A-验证记录.md)（**禁止手抄数字**）。

## 一、切片定位与能力边界

| 项 | 内容 |
|----|------|
| 切片 ID | `P1-A`（P1 电影化主干第 1 片：**接口层先冻结，再生成资产**） |
| 覆盖 | M4 分镜契约 + M5 摄影契约的**结构化、确定性、可机检**部分 |
| 不覆盖 | 真实模型调用、音频/母版/TC、ACES、口型、门禁状态机与人工终审 |
| P1 退出标准进展 | **未达成**（`not_verified.json` 的 `p1_exit_criteria_advanced = false`） |
| 代理纪律 | 所有产物标注 `PROXY — NOT A DELIVERABLE MASTER`（EL-16） |
| 环境约束 | 纯 CPU：标准库 + numpy + Pillow；**无 ffmpeg / 无 GPU / 无付费凭据** |

**为什么先做接口层**：依据 A-30~A-34，主流视频平台**没有**焦距/光圈/景深/快门参数，摄影控制只能靠
「提示词契约 + 分镜层锁定 + 生成后漂移检测」三件事实现（PRD M5 §1 核心约束原文）。契约定错会被
全季继承（600 镜/集 × 三画幅），因此接口层是失败半径最大、也最该先冻结的一段。

## 二、功能点映射（切片实现的 PRD 功能点）

| 功能点 | 内容 | 本切片的机检落点 | 验收指标（PRD 原文） |
|--------|------|------------------|----------------------|
| M4.1-F01 | 分镜表字段完整化 | `R-CONTRACT-FIELDS` | 关键字段非空率 100% |
| M4.2-F01 | 单主运镜约束 | `R-ONE-MOVE` | 双主运镜镜数 = 0 |
| M4.2-F02 | dolly 与 zoom 区分 | `R-DOLLY-ZOOM` | 因混用导致的错配 = 0 |
| M4.2-F03 | 焦距档与景深意图 | `R-CONTRACT-FIELDS` + `R-DRIFT-lens` | 非空率 100%；同场戏漂移告警可复核 |
| M4.2-F04 | 光位方位角与色温契约 | `R-LIGHT-CONTRACT` + `R-DRIFT-clock` + `R-DRIFT-cct` | 漂移超限 100% 生成告警条目 |
| M4.4-F02 | 多画幅安全框预演 | `R-SAFEFRAME`（三窗水平可裁切） | 100% 镜头通过三画幅可裁切预演 |
| M4.7-F01 | 安全框标准与阈值 | `R-SAFETY-BASIS` | 安全区未通过镜头进入生成的数量 = 0 |
| M4.7-F02 | 三画幅可裁切预演 | `R-SAFEFRAME` | **9:16 关键信息出框镜数 = 0** |
| M5.1-F01 | 镜头语言枚举映射 | `prompts.json` + 字节级确定性 | 同分镜重复生成提示词**字节级一致** |
| M5.1-F02 | 一镜一运动铁律 | `R-ONE-MOVE` | 多主运动镜头数 = 0 |
| M5.1-F03 | 提示词与设置不得双重指挥 | 指令归属表 + `leaks` 泄漏检测 | 冲突告警可复现，误配镜次 = 0 |
| M5.1-F04 | dolly / zoom 分支语义 | `R-DOLLY-ZOOM` | 三类分支描述模板覆盖率 100% |
| M5.1-F05 | 运镜速度与 judder 联动 | `prompts.json` 的 `judder` 片段 | 快摇镜 100% 带 judder 标注 |
| M5.2-F01 | 焦距档契约 | `R-CONTRACT-FIELDS` | 焦距档字段完整率 100% |
| M5.2-F02 | 景深意图 | `R-CONTRACT-FIELDS` | 景深意图字段完整率 100% |
| M5.2-F03 | bokeh 描述规范 | 提示词 `bokeh` 片段（形态+来源+边缘） | shallow 镜描述模板覆盖率 100% |
| M5.2-F05 | 摄影参数快照 | `photo_snapshot.json` | 每镜可反查摄影参数快照 |
| M5.3-F01 | 三点光登记 | `R-LIGHT-CONTRACT` | 人物镜三点光登记率 100% |
| M5.3-F02 | fill ≤ key 50% | `R-FILL-KEY` | 违规镜次提交数 = 0 |
| M5.3-F03 | 人脸布光图案 | `R-FACE-PATTERN` | 人物镜图案字段完整率 100% |
| M5.3-F05 | 色温 CCT 与冷暖对比 | `R-CCT-CLOSED` | 色温字段完整率 100% |
| M5.3-F06 | 体积光介质声明 | `R-VOLUMETRIC-MEDIA` | 体积光镜 100% 带介质声明 |
| M5.6-F03 | 跨镜摄影漂移检测 | `drift.json` | 四项漂移检出并有报告 |
| M5.6-F05 | 生成前预检聚合 | `precheck.json` | 因输入问题导致的付费失败 < 1% |
| M10.3-F02/F03 | 署名责任 / 二元化清单 | `gate_receipt.json`（**仅字段契约**） | 门禁记录完整率 100%、清单覆盖率 100% |

## 三、设计要点（为什么这样做）

1. **契约只从 PRD 原文解析，不手抄**：`tools/build_p1_a.py` 直接解析 PRD/96 的「EP01 前 8 镜镜头契约」表；
   任何手抄 fixture 都会漂移（本仓库已有先例：PRD/96 §8 手抄的 Demo 数值与自动生成的 97 号报告不一致，见待裁决 C-07）。
2. **枚举封闭 + fail-closed**：景别/角度/运镜/速度/焦距六档/景深/布光图案/CCT/介质 全部封闭集合；
   未知值抛 `ContractError`，**禁止静默回落**。
3. **提示词是纯函数且版本化**：`mapping_version` 写入产物；同一契约两次编译 **sha256 必须逐字节一致**（M5.1-F01）。
4. **指令归属表**：运镜/光位 → 提示词；时长/分辨率/帧率 → 接口参数；提示词里出现接口侧词汇即告警（M5.1-F03，依据 A-31 双重指挥失败模式）。
5. **安全框判据分三层**（依据 NFR-09 + EL-02 + D1 缓解措施 1）：
   - 硬性①：**9:16 主体越界像素 = 0**（M4.7-F02 原文口径）；
   - 硬性②：**关键信息区（头顶至颈部）落在三画幅各自 action safe 内**（NFR-09「100% 镜头通过三画幅可裁切预演」的可执行化）；
   - 硬性③：主体水平范围在三窗内（竖向被裁属正常电影取景，**不作硬性判据**——2.39:1 下站立人物脚部被裁是常规取景，不是缺陷）。
6. **几何可解而非手调**：`geometry_solver` 以解析方式求可行区间，取最接近原构图意图的解（见 fixture 的 `geometry_note`）。
7. **生成与复测分离**：`tools/verify_p1_a.py` 只读磁盘产物、**不 import 生成器**、像素几何从 PNG 重新解码测量；
   变异样本必须**全部被检出**，否则视为验证器失效。
8. **规则必须有牙**：14 条规则 ↔ 13 个变异样本 + 1 条登记豁免，且复测断言「规则注册表 == 变异样本集合」。
9. **锚点互核**：用同一判据去量**参考实现（demo）**已声明的构图几何，检出 3 镜不合格（S03/S04/S07），
   证明规则不是恒真；同时显式声明「不否定 demo 的 24/24 结论」（判据集合不同）。

## 四、产物清单

| 产物 | 生成者 | 内容 |
|------|--------|------|
| `out/p1a/contract.json` | build | 8 镜契约（含来源与 provenance） |
| `out/p1a/prompts.json` + `prompt_pack.sha256` | build | 确定性提示词与逐镜 sha256 |
| `out/p1a/photo_snapshot.json` | build | 摄影参数快照（M5.2-F05） |
| `out/p1a/crops.json` | build | 三画幅中心裁切窗与安全区口径 |
| `out/p1a/safeframe.json` | build | 逐镜三窗越界/关键信息 containment |
| `out/p1a/drift.json` | build | 同场戏四项漂移告警（带镜号与场次） |
| `out/p1a/precheck.json` | build | 生成前预检聚合（84 项判定） |
| `out/p1a/gate_receipt.json` | build | 分镜门禁收据（占位署名，不作通过结论） |
| `out/p1a/declared_thresholds.json` | build | 项目自定阈值 + 来源 |
| `out/p1a/not_verified.json` | build | 未验证清单 + P1 进展诚实字段 |
| `out/p1a/anchor_crosscheck.json` | build | 参考实现构图互核（只读） |
| `out/p1a/proxy/*.png` | build | 8 镜 open gate 代理帧 + 三画幅裁切预演 |
| `out/p1a/verify_report.json` | verify | 独立复测报告（59 项） |

## 五、验收命令与顺序纪律

顺序：**先生成 → 再复测 → 最后回归**（复测必须晚于被检对象产生，`docs/agent-prd-method.md`）。

```bash
. .venv/bin/activate
python3 tools/build_p1_a.py --out out/p1a                       # 1) 生成
python3 tools/verify_p1_a.py --out out/p1a \
        --report docs/spec/P1-A-验证记录.md                      # 2) 独立复测（fail-closed）
python3 tools/verify_p1_a.py --out out/p1a --determinism         # 2b) 确定性双跑（PYTHONHASHSEED/TZ/LANG 不同）
cd demo && python3 verify.py && python3 report.py                # 3) 既有交付基线回归（须 24/24）
python3 tools/prd_guard.py --all                                 # 4) 治理门禁（本轮 PRD 零改动）
```

判定：任一 FAIL → 退出码非 0 并打印失败清单；`verify_p1_a.py` 退出码 `0=全通过 / 1=存在 FAIL / 2=产物缺失`。

## 六、本轮结论与遗留

**已完成**：8 镜契约全量结构化；84 项生成前预检 0 失败；59 项独立复测 100% 通过；
提示词字节级确定性（双跑跨 hash seed/时区/语言一致）；13 个变异样本 100% 被检出。

**决定性发现（本轮最有价值的产出）**：用「主体**关键信息区**必须落在三画幅 action safe 内」这一判据去量
参考实现 `demo/build_demo.py` 的既有构图，**S03/S04/S07 三镜不合格**（S04 在 9:16 窗左溢 66px、
S07 右溢 128px）。这直接关系到 D1 决议自陈的**最大风险**（「9:16 衍生版质量塌陷」，PRD/93 第 37 行）
与其缓解措施 1（「生成阶段即执行多画幅安全框」，PRD/93 第 39 行）。
处理方式见 [P1-待裁决清单.md](P1-待裁决清单.md) **C-08**：本轮**不改** demo（不污染既有 24/24 证据链），
返修由显式决议驱动。

**遗留（不在本切片范围）**：`−23 LUFS`、TC/母版、ACES IDT、5.1 下混、口型、门禁状态机与人工终审，
逐条登记在 `not_verified.json`。

## 七、变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立 P1-A 切片方案：范围与能力边界、24 条 PRD 功能点映射、9 条设计要点、产物清单、验收命令与顺序纪律；登记决定性发现（参考实现 3 镜构图不合格）与遗留项 |
