# film/legal —— M18 法律工会与行业准入

> 署名/source/同意/AI标识/合规。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- credit 署名（AI 不得 writer）+ source material
- consent 同意记录 + 数字替身
- label AI 标识三类
- compliance 交付前合规
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_legal.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
