# film/audio —— M8 声音设计与配乐

> 四层 stem/响度/下混/授权。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- stems 四层总线 + Σ 校验
- loudness 响度真峰值多目标
- mix 下混 + 可懂度
- license AI 音乐授权档位
- generate 生成
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_audio.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
