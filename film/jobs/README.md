# film/jobs —— M13 任务编排与可靠性

> 队列/幂等/checkpoint/intent log/fencing/worker。契约层为纯函数、fail-closed（未知值一律拒绝），无外部依赖，可独立复测。

## 组成

- state_machine 合法状态转移（fail-closed）
- fingerprint 输入指纹与幂等键
- checkpoint 断点续跑
- intent 出站意图与对账
- fencing 租约纪元
- queue InMemoryQueue（同 PG SKIP LOCKED 语义）
- worker claim→handler→complete/fail
- db SQLAlchemy 模型 + SqlQueue
- sql PG SKIP LOCKED SQL
- enums 状态/阶段/失败分类

## 复测

```bash
. .venv/bin/activate && python3 tools/verify_jobs.py 2>/dev/null || echo '（见 tools/ 下对应 verify_*.py）'
```
