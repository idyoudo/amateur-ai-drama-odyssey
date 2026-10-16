# film/storage —— M15 素材资产与存储

> 对象键规范/母版唯一/派生谱系/内容寻址。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- keys 对象键 users/{uid}/dramas/{pid}/ep{n}/shot{m}/{stage}/v{k}.ext
- lineage 母版唯一约束 + 派生可回溯
- assets 资产登记 + sha256 内容寻址
- enums 资产类型/母版/派生规格

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_storage.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
