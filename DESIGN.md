---
version: 1.0
name: AADO-design-system
description: "AADO 的视觉系统：Editorial Cinematic。近单色冷灰画布、Instrument Serif 衬线展示体、低饱和墨青紫强调色、细边框、轻阴影与大留白。格式参考 awesome-design-md 的 DESIGN.md 方法（Google Stitch 提出），Token 与 apps/api/static/app.css 的 :root 保持同步。"
colors:
  bg: "#FBFBFD"
  surface: "#FFFFFF"
  surface-2: "#F4F4F8"
  surface-3: "#ECECF2"
  line: "#E9E9EF"
  line-strong: "#DCDCE4"
  ink: "#17171C"
  ink-2: "#3F3F4A"
  dim: "#6E6E7A"
  dim-2: "#A0A0AC"
  accent: "#6B6F9E"
  accent-soft: "#F4F5F9"
  accent-line: "#E4E6EF"
  ok: "#0E9F6E"
  ok-soft: "#EDFDF6"
  ok-line: "#C7F3DF"
  warn: "#B45309"
  warn-soft: "#FFF8EB"
  warn-line: "#FBE3B6"
  bad: "#D92D20"
  bad-soft: "#FEF3F2"
  bad-line: "#FBCDCA"
  btn-bg: "#DCE0EE"
  btn-fg: "#33375C"
  btn-hover: "#D2D7E8"
  btn-line: "#C9CDE6"
  on-ink: "#FFFFFF"
dark_colors:
  bg: "#08080B"
  surface: "#101014"
  surface-2: "#17171D"
  surface-3: "#1E1E25"
  line: "#232329"
  line-strong: "#2F2F38"
  ink: "#F4F4F5"
  ink-2: "#C7C7CF"
  dim: "#8A8A93"
  dim-2: "#5C5C66"
  accent: "#A3A6D6"
  accent-soft: "#1E1F2C"
  accent-line: "#30324F"
  ok: "#34D399"
  ok-soft: "#0C2A1F"
  ok-line: "#14532D"
  warn: "#FBBF24"
  warn-soft: "#2A2210"
  warn-line: "#5C4310"
  bad: "#F87171"
  bad-soft: "#2A1414"
  bad-line: "#5C1A1A"
  btn-bg: "#2A2D44"
  btn-fg: "#D6D9F0"
  btn-hover: "#343855"
  btn-line: "#3A3D60"
  on-ink: "#101014"
typography:
  families:
    sans: "Inter, system-ui, -apple-system, PingFang SC, Microsoft YaHei, sans-serif"
    serif: "Instrument Serif, Songti SC, Georgia, Times New Roman, serif"
    mono: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
  scale:
    micro: 10px
    meta: 11px
    sm: 12px
    table: 13px
    body: 14px
    h3: 16px
    h2: 18px
    h1: 20px
    stat: 28px
rounded:
  sm: 6px
  md: 10px
  lg: 14px
  xl: 20px
  pill: 9999px
layout:
  sidebar: 224px
  view-max: 1180px
  page-padding: "16px 52px 72px"
  topbar-padding: "9px 52px"
spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 28px

---

# AADO DESIGN.md

> **强规则四：本文件是 AADO 界面设计的唯一事实来源。**
> 新增或修改任何界面之前先读本文件；不得引入未登记的颜色、字号、圆角、阴影与间距。
> Token 与 [`apps/api/static/app.css`](apps/api/static/app.css) 的 `:root` 必须同步；改一处必须同时改另一处。
> 方法参考 [awesome-design-md](https://github.com/VoltAgent/awesome-design-md)（DESIGN.md 由 Google Stitch 提出），
> 但**不照搬任何第三方品牌视觉**；AADO 只使用本文件定义的自己的设计语言。

## 0. Agent 使用方式（先读这一节）

1. **先查 Token**：颜色用 `--bg / --surface / --ink / --accent` 等语义变量，不写十六进制字面量。
2. **先查组件**：按钮、卡片、表格、表单、弹窗按第 6 节的规格生成，不新造一套。
3. **先查页面模板**：列表、详情、设置、长文、视频课按第 7 节的骨架组织。
4. **改 Token 要成对**：`app.css` 与 `DESIGN.md` 同一提交内更新；`prd_guard --all` 会比对关键色值。
5. **不懂取舍就问**：不要用「更现代」当理由引入渐变、玻璃拟态或第二种强调色。

给 Agent 的最小提示模板：

```text
先读 DESIGN.md。按第 7 节的「列表页/设置页」模板生成页面。
只使用 DESIGN.md 与 app.css 中已存在的 token 和组件；
不得新增颜色、字号、圆角或阴影；完成后对照第 8 节 Do/Don't 自检。
```

## 1. 视觉主题：Editorial Cinematic

AADO 是「影视工业工具」，不是消费级娱乐 App，也不是通用 SaaS 后台。视觉上要像一本**排印精良的制片手册**：

- **近单色冷灰画布**：`#FBFBFD` 背景、白色卡片、发丝级边框。信息密度高，但不拥挤。
- **衬线展示体**：大标题、统计数字、项目名、弹窗标题用 Instrument Serif，带编辑感与电影感。
- **单一低饱和墨青紫强调**：`#6B6F9E` 只用于链接、焦点、选中与进度；不做大面积渐变或高饱和色块。
- **大留白**：整页布局、有序分区、充分间距。宁可多一屏，不把内容塞进弹窗或手风琴。

三条不可协商的原则：

1. **大气优先**：新建/配置类流程用独立整页 + 有序分区 + 充足留白，不用挤牙膏式向导或弹窗逐屏隐藏内容。
2. **内容优先**：装饰让位于信息。背景永远近白，卡片永远白，边框永远细；不用重阴影制造层级。
3. **克制强调**：一屏之内，强调色只出现在真正需要点击或注视的地方。状态色只表达状态。

## 2. 色彩

### 2.1 基础色

| Token | 值 | 用途 |
|---|---|---|
| `--bg` | #FBFBFD | 页面画布 |
| `--surface` | #FFFFFF | 卡片、弹窗、侧栏 |
| `--surface-2` | #F4F4F8 | 次级表面、表头、悬停 |
| `--surface-3` | #ECECF2 | 选中态、分组底 |
| `--line` | #E9E9EF | 发丝边框、分隔线 |
| `--line-strong` | #DCDCE4 | 输入框、可交互边框 |
| `--ink` | #17171C | 主文字、主按钮底 |
| `--ink-2` | #3F3F4A | 正文、次级标题 |
| `--dim` | #6E6E7A | 说明文字 |
| `--dim-2` | #A0A0AC | 元信息、占位符 |

### 2.2 强调与状态

| Token | 值 | 用途 |
|---|---|---|
| `--accent` | #6B6F9E | 链接、焦点环、选中、进度 |
| `--accent-soft` | #F4F5F9 | 焦点环底色、强调区块底 |
| `--accent-line` | #E4E6EF | 强调区块边框 |
| `--btn-bg` / `--btn-fg` / `--btn-line` | #DCE0EE / #33375C / #C9CDE6 | 浅色柔和主按钮 |
| `--btn-hover` | #D2D7E8 | 主按钮悬停 |
| `--ok` / `--ok-soft` / `--ok-line` | #0E9F6E / #EDFDF6 / #C7F3DF | 通过、健康、已完成 |
| `--warn` / `--warn-soft` / `--warn-line` | #B45309 / #FFF8EB / #FBE3B6 | 警告、待标定、灰区 |
| `--bad` / `--bad-soft` / `--bad-line` | #D92D20 / #FEF3F2 / #FBCDCA | 失败、阻断、删除 |

### 2.3 深色模式

深色模式只覆盖 Token，不写组件补丁（`body.dark`）：

| Token | 深色值 |
|---|---|
| `--bg` | #08080B |
| `--surface` | #101014 |
| `--surface-2` | #17171D |
| `--surface-3` | #1E1E25 |
| `--line` | #232329 |
| `--line-strong` | #2F2F38 |
| `--ink` | #F4F4F5 |
| `--ink-2` | #C7C7CF |
| `--dim` | #8A8A93 |
| `--dim-2` | #5C5C66 |
| `--accent` | #A3A6D6 |
| `--accent-soft` | #1E1F2C |
| `--accent-line` | #30324F |
| `--ok` / `--ok-soft` / `--ok-line` | #34D399 / #0C2A1F / #14532D |
| `--warn` / `--warn-soft` / `--warn-line` | #FBBF24 / #2A2210 / #5C4310 |
| `--bad` / `--bad-soft` / `--bad-line` | #F87171 / #2A1414 / #5C1A1A |
| `--btn-bg` / `--btn-fg` / `--btn-line` | #2A2D44 / #D6D9F0 / #3A3D60 |
| `--btn-hover` | #343855 |
| `--on-ink` | #101014 |

### 2.4 禁止

- 禁止大面积紫蓝渐变、彩虹色卡片、霓虹光晕。
- 禁止用纯黑 `#000000` 做大面积背景（深色模式用 `#08080B`）。
- 禁止把状态色当装饰色；一屏内强调色不超过必要数量。
- 禁止低对比灰字（正文不得低于 `--dim`，元信息可用 `--dim-2`）。

## 3. 字体

### 3.1 三套字体

| 角色 | 字体 | 回退 |
|---|---|---|
| 展示/标题 | Instrument Serif 400 | Songti SC, Georgia, Times New Roman |
| 界面/正文 | Inter 400/500/600 | system-ui, PingFang SC, Microsoft YaHei |
| 数字/代码/时间码 | JetBrains Mono 400/500 | ui-monospace, SFMono-Regular, Menlo |

中文标题回退到宋体，正文回退到苹方/微软雅黑。拉丁字体自托管，均为 OFL；不得引入未授权商业字体。

### 3.2 字号阶梯（唯一来源）

| Token | 字号 | 用途 |
|---|---|---|
| `--fs-micro` | 10px | 全大写标签、表头、eyebrow |
| `--fs-meta` | 11px | 元信息、徽章、辅助说明 |
| `--fs-sm` | 12px | 小号正文、按钮小号、表格辅助 |
| `--fs-table` | 13px | 表格、按钮、正文小号 |
| `--fs-body` | 14px | 默认正文、输入框 |
| `--fs-h3` | 16px | 三级标题、卡片标题 |
| `--fs-h2` | 18px | 页面标题、区块标题 |
| `--fs-h1` | 20px | 长文标题、弹窗标题 |
| `--fs-stat` | 28px | 统计数字、页面主标题（衬线） |

**禁止引入中间字号**（如 15px、17px）。需要层级时用字重、颜色与留白解决。

### 3.3 规则

- 大标题、统计数字、项目名、弹窗标题用衬线；正文与控件用无衬线；数字用等宽并开启 `tabular-nums`。
- 同屏字重不超过三种（400/500/600）。
- 全大写 + 字距只用于 micro 标签（如 `letter-spacing: .14em`），不用于正文。
- 中文正文行高 1.6–1.9；长文段落可到 1.95。

## 4. 布局与间距

### 4.1 应用骨架

- 侧栏固定 `224px`；主区自适应，`--view-max: 1180px`。
- 顶栏 sticky，半透明底 + 16px 模糊，底部一条发丝线。
- 页面内边距：桌面 `16px 52px 72px`；移动端 `28px 20px 72px`。
- 主区必须 `min-width: 0`，避免表格/长文撑破布局。

### 4.2 间距

以 8px 为基准：4 / 8 / 12 / 16 / 24 / 32 / 48。区块之间 24–28px；卡片内 18px；表单分区 24px；表格单元 14×16px。

### 4.3 大气优先的具体做法

- **整页而非弹窗**：新建项目、模型配置、课程等流程用独立页面 + 编号分区 + 右侧摘要。
- **分区有序**：每个分区有编号、标题、一句说明；不要把所有字段堆成一张长表。
- **留白是结构**：长文内容最大宽度 820px；左右留白不小于 52px；不要用满屏宽度排正文。
- **列表分页**：无限增长的列表必须服务端分页，不做全量渲染，也不用下拉框塞满数据。
- **按钮自然宽度**：表单操作按钮保持内容宽度与输入框同高，不做整行拉伸或独占一行。

## 5. 形状与层次

| 元素 | 圆角 |
|---|---|
| 按钮 / 输入框 | 6px（小号按钮 5px） |
| 卡片 / 资产卡 | 14px |
| 弹窗 | 20px |
| 徽章 / 标签 | 5px |
| 分段控件 / 胶囊 | 9999px |

阴影只表达层级，不用于装饰：

- `--shadow-xs`：极轻描边辅助
- `--shadow-sm`：静态卡片可选
- `--shadow-md`：可点击卡片悬停
- `--shadow-lg`：弹窗、抽屉、Toast

默认卡片只有 1px 边框；悬停才上浮 2px + `--shadow-md`。禁止重投影与多层发光。

## 6. 组件

### 6.1 按钮

| 变体 | 规格 |
|---|---|
| 主按钮 `.btn` | `--btn-bg` 浅灰蓝底、`--btn-fg` 墨青紫字、`--btn-line` 细边框、6px 圆角、`9px 16px`、13px/600 |
| 次按钮 `.btn.ghost` | 白底、`--line-strong` 边框、`--ink-2` 文字 |
| 小号 `.btn.sm` | `6px 11px`、12px、5px 圆角 |
| 选中态 `.btn.acc` / 筛选 chip / 页码 | `--accent-soft` 底、`--accent-line` 边框、`--accent` 文字；不使用填充墨色 |
| 禁用 | 40% 透明度、不可点 |

主按钮采用浅色柔和按钮，不使用深色或高饱和填充；靠 `--btn-fg` 文字色、`--btn-line` 边框与 600 字重建立主次，而不是靠色块面积。一屏通常只出现一个主按钮。悬停加深底色；按下位移 1px；焦点用 4px `--accent-soft` 环。按钮内图标 15px。深色模式下 `--btn-bg/--btn-fg` 自动反转，禁止把「墨色底 + 白字」写死。

### 6.2 卡片

白底、1px `--line`、14px 圆角、20px 内边距。只有可点击卡片才允许悬停上浮与阴影；静态卡片保持安静。

### 6.3 徽章 `.pill`

11px、5px 圆角、`3px 9px`、1px 边框。状态变体：`.ok` 绿、`.gold` 琥珀、`.bad` 红。徽章不承担主要信息。

### 6.4 表格

表头 10px 全大写、透明底 + `--line-strong` 下边线、字距 `.14em`；单元格 13px、`14px 16px`；行悬停 `--surface-2`；数字列用等宽。表格过宽时横向滚动，不压缩字号。

### 6.5 表单

输入框 `9px 12px`、6px 圆角、`--line-strong` 边框；聚焦换 `--accent` + 4px `--accent-soft` 环。标签 11px 全大写，推荐值用强调色小字。错误提示 11px `--bad`。

### 6.6 导航

- 侧栏分组标签 10px 全大写、字距 `.16em`；分组间距 26px。
- 导航项 14px、`9px 10px`、7px 圆角；悬停 `--surface-2`；选中项**不铺底色**，左侧 2×16px 强调色竖条 + 600 字重。
- 顶栏标题 28px 衬线（`--fs-stat`）、400 字重、负字距；右侧圆形图标按钮 30px，悬停 `--surface-2`。

### 6.7 弹窗 / Toast / 空态

- 弹窗：遮罩 `rgba(23,23,28,.36)` + 6px 模糊；20px 圆角；最大 780px；头 24×28；体 28px。
- Toast：墨色底白字、8px 圆角、底部居中。
- 空态：56px 圆形软底图标 + 13px 说明，垂直留白 56px；只保留一个主按钮 + 一个次按钮，避免重复 CTA。
- 加载：骨架屏使用 `--surface-2`→`--surface-3` 的 1.5s 扫光。

### 6.8 长文 / 课程 / 视频课

- 课程页：左导航 220px、正文最大 820px、章节间距 38px；图注 11px。
- 视频课：卡片网格最小 300px；缩略图 132px，只用 `--thumb-grad` 的中性渐变占位，不放第三方图片，也不做彩色卡片。
- 图表：SVG 内联、可缩放；窄屏横向滚动并提示「左右滑动查看完整图」。

## 7. 页面模板

| 模板 | 骨架 |
|---|---|
| **列表页** | 顶栏 → 统计卡行 → 筛选/搜索（浅灰工具条，不叠白卡）→ 表格或卡片网格 → 分页条（仅在有数据时显示） |
| **详情页** | 标题 + 状态徽章 → 关键信息格 → 分区内容 → 右侧摘要（sticky） |
| **新建 / 设置页** | 左侧编号表单分区（24px 间隔）→ 右侧 sticky 摘要 → 底部自然宽度操作按钮 |
| **长文页** | 左侧章节导航 → 右侧最大 820px 正文 → 上下章按钮 |
| **模型配置页** | 顶部说明 → 六类模型卡片双列（≤1000px 单列）→ 能力矩阵表 |
| **视频课页** | Hero + 学习路径 → 分类筛选 → 课程卡网格 → 外部平台清单 |

详情页与设置页优先使用整页；只有确认、重命名、删除等短操作才用弹窗。

## 8. Do / Don't

**Do**

- 用留白、细线、字重建立层级。
- 一屏只保留一个视觉焦点；强调色服务于操作。
- 长内容先分区，再排版；每区一个编号与一句说明。
- 表格/代码/时间码用等宽数字。
- 空态、错误、加载都有明确文案与下一步。

**Don't**

- 不要紫蓝渐变、玻璃拟态、霓虹发光、彩色阴影。
- 不要第二种强调色；不要把状态色当装饰。
- 不要用 emoji 当图标；不要混用图标风格。
- 不要把多步配置塞进弹窗或手风琴。
- 不要整行拉伸按钮，不要 15/17px 等中间字号。
- 不要为了「高级感」降低正文对比度。

## 9. 响应式

| 断点 | 行为 |
|---|---|
| ≤ 1100px | 双栏详情/编辑页收为单栏；右侧摘要回到文档流 |
| ≤ 860px | 侧栏变为抽屉；页面内边距 28×20；表单双列收单列 |
| ≤ 720px | 学习路径/步骤条纵排；隐藏纯装饰箭头 |
| ≤ 640px | 卡片网格单列；视频缩略图降至 118px |
| ≤ 520px | 统计卡双列（奇数时最后一张跨两列）；卡片单列；顶栏图标间距收紧 |

触控目标不小于 40×40px（顶栏图标可视觉 30px，但点击区补足）。所有 hover 效果必须有对应的 focus/active 状态。

## 10. 无障碍与文案

- 正文对比度达到 WCAG AA；状态不能只靠颜色，必须同时有文字或图标。
- 键盘可达：焦点可见（4px 强调环），弹窗打开后焦点进入，Esc 关闭。
- 表单控件必须有 label；图标按钮必须有 `aria-label` 或 `title`。
- 尊重 `prefers-reduced-motion`：入场动画 0.22s，不做无限循环装饰动画。
- 文案用用户语言：写「未配置 / 示例数据 / 已接入」，不写内部术语「Mock」。
- 空态写「为什么空 + 下一步」，不写「暂无数据」了事。

## 11. Agent 生成指南

生成新界面前，按顺序执行：

1. 读本文件第 1–5 节，确认主题、Token、字体与布局。
2. 选第 7 节的页面模板；不要从零发明结构。
3. 用第 6 节组件拼装；缺组件时先在本文件登记规格，再实现。
4. 用第 8 节自检；用第 9 节检查窄屏；用第 10 节检查无障碍与文案。
5. 跑 `python3 tools/prd_guard.py --all`；Token 漂移会被拦。

常见失败模式：新增了未登记的颜色；用了 15px 字号；把设置流程做成弹窗；卡片加了两层阴影；强调色出现三次以上；表格在窄屏被压到 10px。

## 12. 与 awesome-design-md 的关系

- **借用方法，不借品牌**：本文件采用 [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 推荐的 `DESIGN.md` 结构（YAML Token + 设计理由 + Do/Don't + Agent 指南），该方法由 Google Stitch 提出。
- 该仓库中的品牌文件是**参考案例**，用于理解如何描述一个设计系统；AADO 不复制任何品牌的配色、字体或组件外观。
- 字体只用自托管 OFL 字体或系统字体；商业字体只可作为回退栈中的名字，不打包分发。

## 13. 维护与变更记录

- **唯一事实来源**：`app.css` 的 `:root` 与本文件。两者必须同一提交更新。
- **机器校验**：`python3 tools/prd_guard.py --all` 检查本文件存在、必需章节齐备、关键色值/圆角与 `app.css` 一致。
- **评审口径**：新增视觉值必须说明用途、使用位置与替代方案；不能只写「更好看」。

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-22 | Agent | 建立 AADO DESIGN.md：从现有 app.css 提取 Token 与组件规则，补齐布局、页面模板、响应式、无障碍、Agent 生成指南与禁止项；登记为强规则四 |
| 2026-10-22 | Agent | 视觉精修：页面标题改衬线 28px、统计数字放大、侧栏选中强调条、表格头去灰底、空态圆形图标、工具卡化、模型页双列、视频缩略图改中性渐变；补齐深色模式 `--btn-bg/--btn-fg/--on-ink` 反转 |
| 2026-10-22 | Agent | 按钮体系二次精修：主按钮由近黑改为强调色，列表/看板、筛选 chip、页码统一为浅色选中态，避免页面出现沉重黑块 |
| 2026-10-22 | Agent | 色系第三次精修：强调色从高饱和靛蓝 `#4F46E5` 降到低饱和墨青紫，链接/选中态/深色模式同步换色 |
| 2026-10-22 | Agent | 按钮去填充：主按钮改为浅灰蓝底 + 墨青紫字 + 细边框 + 600 字重，彻底移除深色块；深色模式同步为暗色柔和按钮 |
| 2026-10-22 | Agent | 空态与列表布局精修：侧栏选中项去底色只留竖条；工具条改浅灰条；0 条时隐藏顶栏主按钮与分页；空态只保留一个主按钮 + 一个次按钮，减少重复 CTA |
