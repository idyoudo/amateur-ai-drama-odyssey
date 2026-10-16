# film/consistency —— M6 一致性与连续性

> 人脸阈值/分位截断/连续性/越轴。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- thresholds 人脸阈值 + 分位截断
- continuity 连续性字段/屏幕方向/eyeline/时间天气
- axis 越轴告警而非否决 + 合法四法
- shots 同框上限
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_consistency.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
