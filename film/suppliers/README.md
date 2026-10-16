# film/suppliers —— M17 模型与供应商接入

> 能力矩阵/路由/降级/许可/适配。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- matrix 电影参数能力矩阵
- route 按镜头重要性路由 + 降级链
- license GPL/非商用风险清单
- config 模型配置（env + 页面可覆盖）
- adapter 提交/查询/下载三段式 + Mock
- enums

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_suppliers.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
