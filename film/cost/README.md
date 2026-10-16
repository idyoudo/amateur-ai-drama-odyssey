# film/cost —— M14 成本配额与度量

> 四级预算/重生成/指标/去重。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- budget 四级预算 + 分级预警
- regen 重生成预算 R
- metrics 单位母版成本
- dedup 重复付费守护
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_cost.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
