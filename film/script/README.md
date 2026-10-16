# film/script —— M2 剧作开发与剧本

> Step Outline 结构校验 + 生成。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- structure 三幕节拍/15拍/Truby/场次区间
- outline 场景三元 + 整体校验
- generate 生成（调文本适配器，无凭据 Mock）
- enums 15拍/四节点/形态

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_script.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
