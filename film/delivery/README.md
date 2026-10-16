# film/delivery —— M12 交付版本与分发

> 母版规格/字幕来源/交付单/三重放行。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- spec 主母版规格
- subtitle 字幕排版 + 来源
- sheet 交付单
- release 分发三重放行
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_delivery.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
