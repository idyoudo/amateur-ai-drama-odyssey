# film/performance —— M7 表演配音与口型

> 对白解析/音色/情绪/同步。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- dialogue 对白解析 + 旁白独立 + 别名归一
- voice 音色四维+能力位+全局绑定
- quality 情绪回落 + 电平差
- sync 音画同步验收
- generate 生成
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_performance.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
