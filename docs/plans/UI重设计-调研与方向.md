# AADO UI 重设计 · 调研与候选方向

> 用户诉求：**现代化、高级感、偏浅色**。当前为深色暖金主题，用户不满意。
> 方法：调研 2026 浅色/现代 UI 设计参考 → 提炼 4 个候选方向 → 5 人选举定稿 → 改造。

## 一、调研要点（浅色现代设计）

- **基底不要纯白**：2026 趋势用 `#F0F2F0`（Cloud Dancer）类微灰绿非纯白作背景，比 `#FFFFFF` 护眼且更高级。
- **层级用背景色差而非重边框**：页面底色 / 卡片白 / 弹层更白 三层；1px 极浅边框（`#E4E4E7` 级）。
- **单一强调色**：交互色收敛为一个（靛蓝 `#6366F1` 或品牌色），语义色（成功/警告/错误）固定不混用。
- **字体**：Inter（正文/标题）+ JetBrains Mono（数字/代码），数字用 `tabular-nums`。
- **间距 4px 网格**；卡片圆角 8–12px；悬停用边框微光/背景微亮，不用缩放。
- **避免**：暖琥珀作主色（语义=警告）、发光/蜂窝装饰、纯黑或冷硬纯白、顶部标签导航堆砌。

## 二、候选方向（4 选 1，选举裁决）

### D1 · Editorial Neutral（编辑风中性）
- 背景 `#F7F8F7`(微灰绿) · 卡片 `#FFFFFF` · 正文 `#18181B` · 次文 `#71717A`
- 强调色 **靛蓝 `#6366F1`**（交互）；语义色固定
- 边框 `#E4E4E7` · 圆角 9px · Inter + JetBrains Mono
- 气质：克制、精确、专业工具（Linear-light / Notion 家族）

### D2 · Warm Studio（暖调影棚）
- 背景 `#FAF8F5`(暖米白) · 卡片 `#FFFFFF` · 正文 `#1C1917`
- 强调色 **陶土红 `#C4563C`** + 金 `#B8860B` 点缀（**保留 AADO 电影身份，浅色化**）
- 边框 `#E8E2D8` · 圆角 10px
- 气质：温暖、编辑感、"影棚/制片厂"

### D3 · Monochrome Precision（单色精密）
- 背景 `#FFFFFF` · 卡片 `#FAFAFA` · 正文 `#0A0A0A`
- 主按钮**纯黑** `#0A0A0A` + 单一强调蓝 `#0070F3`
- 边框 `#EAEAEA`（极弱）· 圆角 6px（偏方正）
- 气质：极简、开发者级、Vercel/Geist 家族

### D4 · Soft Depth（柔和纵深）
- 背景 `#F5F5F7`(Apple 灰) · 卡片 `#FFFFFF` + **柔和阴影**
- 强调色 **苹果蓝 `#0071E3`**
- 圆角 14px（更大）· 更宽松间距
- 气质：通透、消费级高级感（Apple HIG light）

## 三、评估维度（供选举）

是否满足「现代化 / 高级感 / 浅色」；是否契合**电影制作工具**定位；是否适配现有 vanilla JS + CSS 变量（改动成本）；可读性/对比度（WCAG AA）；是否经得起长时间使用（密集数据）。

## 来源

- [2026 浅色极简趋势 Cloud Dancer](https://colorui.io/how-to/cloud-dancer-2026-minimalist-trend)
- [现代仪表盘设计最佳实践 2025-2026](https://github.com/desplega-ai/agent-swarm/blob/main/thoughts/taras/research/2026-02-25-dashboard-ui-design-best-practices.md)
- [shadcn/ui 主题变量与 OKLCH](https://21st.dev/blog/shadcn-theming-css-variables)
- [Design references: cutting edge yet simple (2026)](https://github.com/mcorbett51090/RavenClaude/blob/main/plugins/web-design/knowledge/design-references.md)

## 变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-17 | Agent | 建立 UI 重设计调研与 4 个候选方向 |
