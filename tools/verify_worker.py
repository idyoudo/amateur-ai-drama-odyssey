#!/usr/bin/env python3
"""worker 集成复测：入队 → worker 领取 → 业务分发 → 模块生成(Mock) → 完成写 checkpoint。

证明队列 + 适配层 + 各模块实现层能串成一条可执行链路（无凭据走 Mock）。
退出码：0 通过；1 违规。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from apps.worker import handlers
from film.jobs import model as jobs_model, queue as jobs_queue, worker as jobs_worker
from film.suppliers import config as sup_config

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# 空配置 → 全 Mock
handler = handlers.make_handler(sup_config.load_from_env())

q = jobs_queue.InMemoryQueue()
job_types = ("adapt", "casting", "generate_voice", "music")
for jt in job_types:
    q.enqueue(jobs_model.make_job("p1", 1, 1, jt, "idem-%s" % jt))

w = jobs_worker.Worker(q)
done = w.run_until_empty(handler)
check("worker 处理全部 4 个任务", done == 4)

for job_id, j in q._jobs.items():
    check("%s 完成" % j["type"], j["status"] == "completed")
    check("%s 有 checkpoint 产出" % j["type"], len(j["checkpoint"].get("produced_keys", [])) == 1)

# 幂等：同 key 再入队不重复
dup = q.enqueue(jobs_model.make_job("p1", 1, 1, "adapt", "idem-adapt"))
check("幂等入队不新增", dup["status"] == "completed")

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "worker-integration", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
