# film/timeline —— M9 剪辑节奏与时间线

> 时间线合法性/ASL/Murch/交换格式。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- timeline 时间线合法性
- rhythm 滑窗 ASL + 张力递减 + Murch 权重
- exchange 版本命名 + reel 名上限
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_timeline.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
