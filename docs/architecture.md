# AADO 系统架构（docs/architecture.md）

> 本文回答「**怎么实现**」，与 `PRD/`（回答「要什么」）互补。归位见 [PRD/README.md](../PRD/README.md)。
> 架构决策依据：本仓库既有的 `film/` 切片 + `demo/`，以及两个参考实现的实测调研——
> `retail-trading-odyssey`（宿主基线 RTO 的 AI 短剧实现）与 `audit-worker-platform`（耐久任务编排平台）。
> 决策记录与票型见 [P1-A-选举记录.md](plans/P1-A-选举记录.md)；冲突裁决见 [P1-待裁决清单.md](plans/P1-待裁决清单.md)。

## 一、核心决策（先给结论，理由随后）

| 决策 | 选择 | 一句话理由 |
|------|------|------------|
| 语言/运行时 | **Python 3.10+ 单体仓库（monorepo）** | 媒体/QC 正确性核心已是 Python 且机器验证过；编排模式语言无关可移植 |
| API 框架 | **FastAPI**（自动 OpenAPI） | 直接产出 API 契约，补齐 RTO「无 OpenAPI」短板 |
| 数据库 | **PostgreSQL 16** | 两个参考均 PG；够用，且能承载 PG 自建队列 |
| ORM/迁移 | **SQLAlchemy 2.0 + Alembic** | 补齐 RTO「内联 `ALTER ADD COLUMN`」的迁移短板 |
| 队列 | **PG 表 + `FOR UPDATE SKIP LOCKED`（自建，无 Redis/BullMQ）** | RTO 证明 PG-only 对低并发足够；首季 6 集不需要 Redis |
| 媒体/QC | **`film/` 包（numpy/Pillow）为唯一事实源，ffmpeg 作为生产可选加速** | 正确性核心已验证；纯 Python 降级路径让受限环境也能自证 |
| Web UI | 首季**复用 `demo/` 静态仪表盘范式**，需要时再加 React | 控制面最小化，优先打通后端链路 |

### 为什么是 Python 而不是 TypeScript

两个参考都是 TypeScript，但 AADO 的本质是**媒体管线**，不是 CRUD/审计平台。独立判断：

1. **正确性核心已用 Python 并机器验证**：`film/` 包（契约编译、几何/安全框、变异测试 13/13）与 `demo/` 的纯 Python BS.1770 响度复测，都是 numpy/Pillow 实现的、已验证资产。改 TypeScript 等于丢弃这些再重写一遍，且 TS 无等价图像/音频信号分析库。
2. **编排模式语言无关**：`SKIP LOCKED` 队列、outbox、intent log、advisory lock fencing 全都能用 `psycopg`/`asyncpg` 干净移植（RTO 是 PG 裸 SQL，audit 是 Drizzle+BullMQ，但**模式**不绑定语言）。
3. **避免双语言 IPC 边界**：媒体面（Python）与控制面（TS）之间要传帧/波形/几何，跨语言序列化是纯负债；单语言无此边界。
4. **规模适配**：首季 6 集 × 低并发，一个 Python 服务 + worker 足够。

**何时重访**：出现多租户高并发（数百项目并行）、或团队扩大且强烈要求类型安全时，再评估「TS 控制面 + Python 媒体面」双语言；首季不做。

### 为什么首季不引入 Redis/BullMQ

audit-worker-platform 用 BullMQ/Redis，但它是高吞吐多租户审计平台。RTO 用 PG 表当队列跑通了完整短剧链路。AADO 首季并发极低（先导集单集、6 集串行），PG `SKIP LOCKED` 完全够。**引入 Redis = 多一个运维组件，零收益**。触发条件写入路线图：pod 2 复盘时若并发/吞吐成为瓶颈，再评估。

## 二、进程拓扑（三层）

```text
┌────────────────────────────────────────────────────────────────┐
│  apps/web（可选，首季复用 demo 静态仪表盘）                        │
└───────────────▲────────────────────────────────────────────────┘
                │ HTTP/JSON
┌───────────────┴────────────────────────────────────────────────┐
│  apps/api（FastAPI）                                            │
│   - 项目/工作区/预算/门禁/资产/供应商 管理面（M1/M14/M15/M16/M17）│
│   - 只做「入队 + 查询 + 人工终审」；不做重计算                    │
└───────┬────────────────────────▲────────────────────────────────┘
        │ 写任务(幂等入队)         │ 轮询/查询状态
┌───────▼────────────────────────┴────────────────────────────────┐
│  apps/worker（Python，PG SKIP LOCKED 队列）                       │
│   - 阶段 DAG：Development→Pre-pro→Production→Post→Delivery       │
│   - 租约/心跳/幂等/checkpoint/intent log/fencing（见 M13 章节）    │
│   - 调用 film/ 包做媒体计算 + 供应商 API                          │
└───────┬───────────────────────────▲─────────────────────────────┘
        │ 读写                        │ 读取/写产物
┌───────▼───────────────────────────┴─────────────────────────────┐
│  PostgreSQL（业务态 + 队列 + outbox）  │  对象存储（媒体/母版/派生）│
│  film/ 包（纯函数媒体核心：契约/几何/QC/响度）                    │
└──────────────────────────────────────────────────────────────────┘
```

**原则**：
- **API 薄、worker 重**：API 不做重计算与媒体处理，只入队/查询/人工终审（对齐 RTO 的 `advanceDramaProject` 幂等推进，但把执行收敛到 worker）。
- **生成与复测分离**：`film/` 只产出可机检产物；独立复测脚本只读磁盘产物重测（本仓库已验证的纪律，见 `docs/agent-prd-method.md`）。
- **ffmpeg 可选**：生产环境装 ffmpeg 走加速路径；无 ffmpeg 环境走 `film/` 纯 Python 降级路径（BS.1770 响度、Pillow 几何/ΔE），保证 CI 与受限机器可自证。

## 三、19 模块 → 代码包映射

| PRD 模块 | 代码包 | 现状 | 关键职责 |
|----------|--------|------|----------|
| M1 项目与创作入口 | `apps/api/workspaces` | 规划中 | 立项单、包型预设、先导集模式、预算 |
| M2 剧作开发与剧本 | `film/script` | 规划中 | logline→treatment→beat→剧本 文档序列（map-reduce 长文本，借鉴 RTO `bailian.adaptStory`） |
| M3 选角角色资产 | `film/casting` | 规划中 | 锚点图集、身份嵌入、定妆门禁、数字替身 |
| M4 分镜 previz | `film/contract` | **切片 P1-A 已实现契约层** | 分镜表字段、单主运镜、dolly/zoom、越轴告警 |
| M5 电影摄影 | `film/prompts` + `film/geometry` | **切片 P1-A 已实现** | 确定性提示词编译、安全框、漂移检测 |
| M6 一致性与连续性 | `film/consistency` | 规划中 | 人脸嵌入、DINO/CLIP/SAM、连续性字段表、越轴 |
| M7 表演配音口型 | `film/performance` | 规划中 | 表演指令、TTS、口型同步、音色绑定 |
| M8 声音设计与配乐 | `film/audio` | 规划中 | 四层总线、BS.1770 响度（复用 demo）、混音/下混 |
| M9 剪辑节奏 | `film/timeline` | 规划中 | 时间线、ASL、J/L cut、EDL/XML/AAF |
| M10 质量门禁 | `film/gates` | **切片 P1-A 已实现字段契约层** | 五门禁、署名/理由码、自动返工预算 |
| M11 调色母版 QC | `film/master` | 规划中 | ACES/IDT、母版编码、QC 清单、TC |
| M12 交付与分发 | `film/delivery` | 规划中 | 交付单、多规格派生、字幕/本地化 |
| M13 任务编排 | `apps/worker` + `film/jobs` | 规划中（借 RTO/audit 模式） | 队列/幂等/checkpoint/intent log/fencing |
| M14 成本配额 | `apps/api/cost` | 规划中 | 预算四级、缓存、熔断、计量、北极星指标 |
| M15 素材资产存储 | `film/storage` | 规划中 | 对象存储、版本谱系、血缘 |
| M16 工作区协作 | `apps/api/auth` + `apps/api/rbac` | 规划中 | 岗位、权限矩阵、门禁署名 |
| M17 模型供应商 | `film/suppliers` | 规划中 | **统一 provider 接口层**、能力矩阵、路由、降级 |
| M18 法律工会 | `film/legal` | 规划中 | 权利链台账、同意记录、AI 标识 |
| M19 VFX 合成 | `film/vfx` | 规划中 | 修复、去闪、超分补帧、物理骨架 |

## 四、宿主基线边界（RTO 的 182 处 `apps/...:行号` 怎么处理）

`PRD/` 现状列引用 RTO 的 `apps/api/src/*` 共 182 处，但**本仓库不继承其架构**。处置规则：

1. **只作「现状基线」参考，不作实现依赖**：任何功能点实现时，**不得** `import` 或复制 RTO 代码；只能参考其**模式**（见下）。
2. **可移植的模式清单**（已验证，逐条对应）：
   - PG `SKIP LOCKED` 队列 + 租约/心跳/续租 + `attempts/attempt_limit`（RTO `dramaService.ts:547-620`）
   - 幂等键部分唯一索引 + `ON CONFLICT` 幂等入队（RTO `dramaService.ts:37,158-162`）
   - checkpoint JSONB + 输入指纹续跑（RTO `adaptCheckpoint.ts:25-50`）
   - 阶段 DAG 在 claim 层强制顺序 + 依赖失败短路（RTO `dramaLogic.ts:27-31`、`dramaWorker.ts:83-98`）
   - 「durable 输出已存在」对账兜底修复僵尸任务（RTO `dramaService.ts:438-502`）
   - outbox 幂等 `idempotencyKey` + 乐观锁 `version`（audit `delivery-notification-outbox.ts`）
   - intent log：出站前冻结 payload/指纹/requestId，重试复用同 key（audit `parse-compare-schedule.ts:332-474`）
   - PG advisory lock 跨实例 fencing + 失败销毁连接（audit `packages/db/src/index.ts:103-170`）
3. **不继承的历史包袱**（明令禁止）：硬编码 720p 合成、固定 6 镜、单管理员无 RBAC、手写 HTTP 路由、内联 `ALTER ADD COLUMN` 迁移、模型写死阿里 Token Plan、无 OpenAPI、无 metrics。
4. **边界文档**：迁移映射表见 [宿主基线映射.md](designs/宿主基线映射.md)（实现时逐条登记「参考哪处 / 重写 / 不继承」）。

## 五、任务编排设计（M13，关键借鉴）

见 [任务编排设计.md](designs/任务编排设计.md)。要点：任务表 + `idempotency_key` 唯一索引；领任务 `SKIP LOCKED` + `locked_until` 租约；`checkpoint JSONB` 记录已产出对象键与指纹；出站供应商调用前落 `intent`（冻结指纹/requestId），超时置 `unknown` 进对账队列，**禁止直接重发**；`reclaimStale` 用「durable 输出已存在」翻僵尸为 completed。

## 六、测试策略概览

见 [测试策略.md](designs/测试策略.md)。三层：单元（film 纯函数）→ 集成（队列/幂等/checkpoint）→ 机检门禁（生成-复测分离 + 变异测试 + 锚点互核）。验收证据格式对齐 `PRD/90` 第八章。

## 七、非目标（首季明确不做）

- 自建基础模型训练（供应商接入 + 可选自托管，D8 决议）
- 影院 DCP 通道（D10 决议：只做投递包）
- Redis/BullMQ/Temporal/Hatchet（PG-only 足够）
- 双语言控制面/媒体面（单 Python）
- 面向第三方的开放平台与计费（`PRD/00` 范围外）

## 八、变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立架构：单 Python monorepo + FastAPI + PostgreSQL + PG 自建队列；19 模块→代码包映射；宿主基线边界（可移植模式 vs 不继承包袱）；任务编排借鉴点；测试策略概览；非目标清单 |
