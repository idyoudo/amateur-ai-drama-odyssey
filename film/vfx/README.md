# film/vfx —— M19 VFX 与合成

> 物理骨架/修复优先级/门禁/许可。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- shotlist VFX 类型 + 物理骨架通道
- repair 修复优先级
- anamorphic 变形宽银幕三项
- gate VFX 门禁 + 工具许可
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_vfx.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
