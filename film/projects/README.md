# film/projects —— M1 项目与创作入口

> 立项单/包型/交付规格。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- project 立项单（logline 必填）
- package 包型预设 + 参数校验
- delivery 交付规格
- enums 分级/风格/时长档

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_projects.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
