# film/casting —— M3 选角角色资产

> 锚点图集/角色卡/定妆门禁。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- anchors 锚点图集（3-8张/≥3视角）
- character 角色卡（音色绑定/授权先于生成）
- gates 定妆门禁
- generate 生成
- enums 视角/音色能力位

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_casting.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
