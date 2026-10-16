# film/rbac —— M16 工作区与协作

> 角色/岗位/权限矩阵/门禁署名/审计。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- roles 六技术角色 + 八影视岗位
- permissions 岗位×操作矩阵
- gates 门禁署名（岗位绑定+自审自批禁令+理由码）
- audit 操作审计

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_rbac.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
