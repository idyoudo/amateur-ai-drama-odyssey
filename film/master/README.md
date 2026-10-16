# film/master —— M11 调色母版与影视 QC

> 色偏/母版规格/字幕/拒收项/门禁。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- color 色偏阈值
- master 母版规格 + 头尾黑场
- subtitle 字幕合规
- qc 平台拒收项 + 母版门禁
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_master.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
