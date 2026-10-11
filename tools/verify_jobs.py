#!/usr/bin/env python3
"""M13 任务编排契约层 · 独立复测（生成与复测分离）。

只 import film/jobs，跑正样本 + 变异（负样本）断言；fail-closed。
变异样本用于证明规则不是恒真（对抗式自评）。退出码：0 通过；1 违规。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.jobs import checkpoint, enums, fencing, fingerprint, intent, state_machine  # noqa: E402

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# ---------------- 1) 状态机 ----------------
sm = state_machine
check("claim queued->running", sm.can_transition("queued", "running"))
check("complete running->completed", sm.can_transition("running", "completed"))
check("fail running->failed", sm.can_transition("running", "failed"))
check("retry failed->queued", sm.can_transition("failed", "queued"))
check("exhaust failed->retry_exhausted", sm.can_transition("failed", "retry_exhausted"))
check("reconcile unknown->completed", sm.can_transition("unknown", "completed"))
check("reconcile unknown->queued", sm.can_transition("unknown", "queued"))
check("cancel queued->cancelled", sm.can_transition("queued", "cancelled"))
# 变异：乱序
check("乱序 completed->running 拒绝", not sm.can_transition("completed", "running"))
check("乱序 queued->completed 拒绝", not sm.can_transition("queued", "completed"))
check("乱序 cancelled->running 拒绝", not sm.can_transition("cancelled", "running"))
check("乱序 failed->completed 拒绝", not sm.can_transition("failed", "completed"))
check("乱序 running->queued 拒绝", not sm.can_transition("running", "queued"))
try:
    sm.require_transition("completed", "running")
    check("require 乱序应抛错", False)
except state_machine.StateError:
    check("require 乱序应抛错", True)

# ---------------- 2) 指纹与幂等键 ----------------
fp = fingerprint.input_fingerprint("a prompt", "v1", {"k": 1}, 42, ["h1", "h2"])
check("指纹是 64 位 hex", len(fp) == 64 and all(c in "0123456789abcdef" for c in fp))
check("同输入同指纹", fp == fingerprint.input_fingerprint("a prompt", "v1", {"k": 1}, 42, ["h1", "h2"]))
check("模型升级换指纹", fp != fingerprint.input_fingerprint("a prompt", "v2", {"k": 1}, 42, ["h1", "h2"]))
check("seed 变化换指纹", fp != fingerprint.input_fingerprint("a prompt", "v1", {"k": 1}, 43, ["h1", "h2"]))
check("参数变化换指纹", fp != fingerprint.input_fingerprint("a prompt", "v1", {"k": 2}, 42, ["h1", "h2"]))
key = fingerprint.idempotency_key("p1", 1, 2, "shot_video", fp)
check("幂等键结构", key == "p1:1:2:shot_video:%s" % fp)

# ---------------- 3) checkpoint ----------------
cp = checkpoint.make_checkpoint(["obj/k1", "obj/k2"], fp, 3)
check("checkpoint 合规", checkpoint.validate_checkpoint(cp) == [])
check("checkpoint epoch=0 违规", checkpoint.validate_checkpoint(
    checkpoint.make_checkpoint(["obj/k1"], fp, 0)) != [])
check("checkpoint 缺指纹违规", checkpoint.validate_checkpoint(
    checkpoint.make_checkpoint(["obj/k1"], "", 3)) != [])
check("checkpoint 非对象违规", checkpoint.validate_checkpoint("x") != [])

# ---------------- 4) intent ----------------
it = intent.make_intent("j1", "p", fp, "cop1", "req1", {"frozen": True})
check("intent 合规", intent.validate_intent(it) == [])
check("intent 初始 intended", it["status"] == "intended")
check("intent intended->submitted", intent.require_intent_transition("intended", "submitted") == "submitted")
check("intent intended->unknown", intent.require_intent_transition("intended", "unknown") == "unknown")
check("intent unknown->resolved", intent.require_intent_transition("unknown", "resolved") == "resolved")
try:
    intent.require_intent_transition("submitted", "unknown")
    check("submitted 禁止重投", False)
except state_machine.StateError:
    check("submitted 禁止重投", True)
check("intent 缺 request_id 违规", intent.validate_intent(
    intent.make_intent("j1", "p", fp, "cop1", "", {})) != [])

# ---------------- 5) fencing ----------------
def _raises(fn, *args):
    try:
        fn(*args)
        return False
    except (ValueError, state_machine.StateError):
        return True

check("epoch 单调递增", fencing.next_epoch(3) == 4)
check("fencing 旧 epoch 被拒", not fencing.lease_current(4, 3))
check("fencing 当前 epoch 放行", fencing.lease_current(4, 4))
check("validate_epoch 非法抛错", _raises(fencing.validate_epoch, 0))
check("validate_epoch 合法", fencing.validate_epoch(1) == 1)



# ---------------- 6) 队列语义（InMemoryQueue） ----------------
from film.jobs import model, queue as queue_mod, retry as retry_mod

q = queue_mod.InMemoryQueue()
j1 = q.enqueue(model.make_job("p", 1, 1, "shot_video", "p:1:1:shot_video:fp1", priority=5))
dup = q.enqueue(model.make_job("p", 1, 1, "shot_video", "p:1:1:shot_video:fp1", priority=5))
check("幂等入队同一 job", dup["id"] == j1["id"])
check("幂等不新增", len(q._jobs) == 1)

j2 = q.enqueue(model.make_job("p", 1, 2, "shot_video", "p:1:2:shot_video:fp2", priority=1))
j3 = q.enqueue(model.make_job("p", 1, 3, "shot_video", "p:1:3:shot_video:fp3", priority=5))
c = q.claim()
check("claim 高优先级+FIFO", c["id"] == j1["id"])
check("claim 置 running", c["status"] == "running")
check("claim attempts/epoch", c["attempts"] == 1 and c["lease_epoch"] == 1)
q.heartbeat(j1["id"], 1, now=50)
check("心跳续租 locked_until", q.get(j1["id"])["locked_until"] == 50 + 90 * 60)
try:
    q.heartbeat(j1["id"], 0, now=50)
    check("心跳旧 epoch 拒绝", False)
except queue_mod.QueueError:
    check("心跳旧 epoch 拒绝", True)

try:
    q.complete(j1["id"], 0)
    check("旧 epoch 写入被拒", False)
except queue_mod.QueueError:
    check("旧 epoch 写入被拒", True)

q.complete(j1["id"], 1, checkpoint={"produced_keys": ["obj/a"]})
check("complete->completed", q.get(j1["id"])["status"] == "completed")

c = q.claim()
check("FIFO 同优先级取 j3", c["id"] == j3["id"])
q.fail(j3["id"], c["lease_epoch"], "network")
check("fail->failed", q.get(j3["id"])["status"] == "failed")
check("network 可自动重试", retry_mod.should_auto_retry("network", 1))
check("content 不自动重试", not retry_mod.should_auto_retry("content_reject", 1))
check("未知类 terminate", retry_mod.retry_disposition("bogus") == "terminate")
check("retry failed->queued", q.retry(j3["id"]) is True)
check("retry 后 queued", q.get(j3["id"])["status"] == "queued")

q2 = queue_mod.InMemoryQueue(lease_sec=10)
ja = q2.enqueue(model.make_job("p", 2, 1, "shot_video", "p:2:1:shot_video:fpa"))
q2.claim(now=0)
q2.get(ja["id"])["checkpoint"] = {"produced_keys": ["obj/x"]}
q2.get(ja["id"])["locked_until"] = 5
r = q2.reclaim_stale(now=10)
check("reclaim 有产出->completed", ja["id"] in r and q2.get(ja["id"])["status"] == "completed")

jb = q2.enqueue(model.make_job("p", 2, 2, "shot_video", "p:2:2:shot_video:fpb"))
q2.claim(now=0)
q2.get(jb["id"])["locked_until"] = 5
r = q2.reclaim_stale(now=10)
check("reclaim 无产出->requeue", jb["id"] in r and q2.get(jb["id"])["status"] == "queued")

try:
    q.cancel(j1["id"], 1)
    check("cancel completed 拒绝", False)
except state_machine.StateError:
    check("cancel completed 拒绝", True)

# ---------------- 汇总 ----------------
total = _total[0]
passed = total - len(_failed)
report = {"module": "M13-jobs-contract", "total": total, "pass": passed, "fail": len(_failed)}
print(json.dumps(report, ensure_ascii=False))
if _failed:
    print("失败项：", file=sys.stderr)
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
