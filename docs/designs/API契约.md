# AADO API 契约（docs/plans/API契约.md）

> FastAPI 自动生成 OpenAPI 即本契约的机器可读版本；本文件是**语义契约**（方法/路径/请求响应/幂等键/错误码），
> 供实现与评审对齐。命名沿用 RTO 的 `/api/dramas/...` 前缀但**不继承其手写路由与单管理员模型**。
> 通用约定：Bearer 鉴权（M16 权限矩阵）；错误码统一 `code` + `message`；幂等写操作带 `Idempotency-Key`。

## 一、通用错误码（封闭集合）

| code | 含义 |
|------|------|
| `VALIDATION_ERROR` | 契约枚举非法（film 封闭校验拒绝） |
| `GATE_BLOCKED` | 上游门禁未过，下游阶段禁止启动 |
| `BUDGET_EXCEEDED` | 预算硬阻断（M14） |
| `FINGERPRINT_DUP` | 输入指纹命中，拒绝重复付费调用（NFR-01） |
| `SUPPLIER_LIMITED` | 供应商限流/熔断，降级或转人工 |
| `RESULT_UNKNOWN` | 提交结果不确定，进入对账队列 |
| `UNAUTHORIZED` / `FORBIDDEN` | 鉴权/越权（M16） |
| `NOT_FOUND` | 资源不存在 |

## 二、项目与创作入口（M1）

| 方法 路径 | 说明 | 幂等键 | 关键错误 |
|---|---|---|---|
| `POST /api/projects` | 立项（校验 logline/包型/交付规格） | 客户端 UUID | `VALIDATION_ERROR`（缺 logline） |
| `GET /api/projects/{id}` | 项目详情 + 预算/门禁状态 | — | — |
| `POST /api/projects/{id}/gate` | 门禁终审（五节点，署名+理由码） | `{node}` | `GATE_BLOCKED`（未署名视为未通过） |
| `POST /api/projects/{id}/pod/go-kill` | pod 分块 go/kill 决策记录 | `{pod_no}` | — |

## 三、剧本开发（M2）

| 方法 路径 | 说明 |
|---|---|
| `POST /api/projects/{id}/script/story-package` | 入队 logline→synopsis→treatment→bible 序列（map-reduce） |
| `POST /api/projects/{id}/script/outline` | 入队分集大纲（三幕节拍校验） |
| `POST /api/projects/{id}/script/draft` | 入队剧本稿（beat 驱动分层） |
| `GET  /api/projects/{id}/script/{doc}` | 拉取开发文档序列产物 + provenance |

## 四、分镜与摄影（M4/M5 —— P1-A 契约已实现）

| 方法 路径 | 说明 |
|---|---|
| `POST /api/episodes/{eid}/shots` | 写入镜头契约（film/contract 封闭枚举校验） |
| `GET  /api/episodes/{eid}/shots/contract` | 分镜表 + 每镜摄影参数快照（M5.2-F05） |
| `POST /api/episodes/{eid}/precheck` | 生成前预检聚合（安全框/漂移/预算/模型能力） |
| `POST /api/shots/{sid}/generate` | 入队出图/出视频（先预检，FAIL 则拒绝付费调用） |
| `GET  /api/shots/{sid}/snapshot` | 摄影参数快照反查 |

## 五、媒体/资产/母版（M7/M8/M11/M12/M15）

| 方法 路径 | 说明 |
|---|---|
| `POST /api/shots/{sid}/voice` | 入队 TTS（角色音色全局绑定校验） |
| `POST /api/episodes/{eid}/compose` | 入队母版合成（QC 前置） |
| `POST /api/episodes/{eid}/derive` | 入队多规格派生（2.39/16:9/9:16/5.1/HDR10，失败只重跑该派生） |
| `GET  /api/assets/{id}` | 资产元数据 + 血缘（parent 指向 open gate） |
| `GET  /api/assets/{id}/content` | 流式/下载（鉴权 + AI 标识保持） |
| `GET  /api/episodes/{eid}/delivery-sheet` | 交付单（保证/可选/需确认 标注） |

## 六、任务与门禁（M10/M13）

| 方法 路径 | 说明 |
|---|---|
| `GET  /api/jobs` | 任务列表 + 状态/进度/成本/阶段耗时 |
| `POST /api/jobs/{id}/retry` | 人工重试（记录归因标签） |
| `POST /api/jobs/{id}/cancel` | 取消（回收供应商任务或标记待核销） |
| `POST /api/reviews` | 质检结论 + 返工指令（签名+理由码） |
| `GET  /api/projects/{id}/qc-report` | 机读 QC 报告（响度/安全框/一致性/连续性） |

## 七、成本与供应商（M14/M17）

| 方法 路径 | 说明 |
|---|---|
| `GET  /api/projects/{id}/cost` | 单位成本/单集单镜成本/北极星指标 |
| `POST /api/projects/{id}/budget` | 预算四级设定 + 额度预占 |
| `GET  /api/suppliers` | 能力矩阵（电影参数支持度/授权/限流/熔断态） |
| `POST /api/suppliers/{name}/admission` | 准入评测记录（可复现，未达线拒绝上线） |

## 八、法律合规（M18）

| 方法 路径 | 说明 |
|---|---|
| `POST /api/projects/{id}/rights-chain` | 权利链台账（原作授权/音乐/字体/素材/肖像/数字替身） |
| `POST /api/projects/{id}/consent` | 同意记录（授权先于生成） |
| `GET  /api/projects/{id}/compliance-report` | 交付前合规校验（AI 标识/权利链/分级） |

## 九、实现纪律

1. FastAPI 路由用 `pydantic` 模型 + `film/` 封闭枚举校验；契约非法一律 422 `VALIDATION_ERROR`。
2. 所有「入队」端点返回 202 + `job_id`；执行在 worker；API 不做重计算。
3. 幂等键：写操作强制 `Idempotency-Key`，与 `jobs.idempotency_key` 对齐，重复提交返回已存在任务（不重复付费）。
4. 门禁端点（gate/review）强制 `approver` 非空；占位署名只用于测试，生产拒绝。

## 十、变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立 API 契约：通用错误码封闭集 + 8 组资源端点（项目/剧本/分镜/媒体/任务/成本/合规）+ 实现纪律 |
