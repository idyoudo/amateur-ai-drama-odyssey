#!/usr/bin/env python3
"""端到端链路联调冒烟（纯 Python，无外部服务）：立项→剧本→选角→任务编排→交付→合规。

验证 19 模块契约层能串成一条可执行链路，跨模块数据流正确。退出码：0 通过；1 违规。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.projects import project as m1
from film.script import enums as m2e, outline as m2
from film.casting import anchors as m3a, character as m3c, gates as m3g
from film.jobs import model as m13m, queue as m13q, worker as m13w
from film.delivery import release as m12r, sheet as m12s, spec as m12p
from film.legal import compliance as m18c, label as m18l

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


# 1) M1 立项
p = m1.make_project("回声", "都市悬疑：失忆调音师卷入命案", "短剧平台", "全龄", "悬疑")
check("M1 立项单校验", m1.validate_project(p) == [])

# 2) M2 剧本结构（20 场覆盖 15 拍 + 四节点）
scenes = []
for i in range(20):
    scenes.append(m2.make_scene(i + 1, "SLUG", "事件", "目标", "冲突", "结果",
                                [m2e.BEATS_15[i % 15]]))
outline = m2.make_outline("half_hour", scenes, 0.24, 0.50, 0.80, list(m2e.TRUBY_NODES))
check("M2 Step Outline 结构校验", m2.validate_outline(outline) == [])

# 3) M3 选角 + 定妆门禁
anchors = [m3a.make_anchor(v, "key_%s" % v) for v in ("front", "side", "full_body")]
ch = m3c.make_character("主角", anchors, voice_key="v1")
check("M3 角色卡校验", m3c.validate_character(ch) == [])
gate = {"approver": "张三", "approver_position": "showrunner", "doer_position": "director",
        "reason_code": "pass_with_condition", "decision": "approve", "locked": True}
check("M3 定妆门禁校验", m3g.validate_casting_gate(gate) == [])

# 4) M13 任务编排：入队 → worker 完成 → checkpoint
q = m13q.InMemoryQueue()
job = q.enqueue(m13m.make_job("p1", 1, 1, "shot_video", "p1:1:1:shot_video:fp1"))
w = m13w.Worker(q)
w.run_once(lambda j: {"produced_keys": ["obj/shot1"]})
check("M13 worker 完成任务并写 checkpoint",
      q.get(job["id"])["status"] == "completed"
      and q.get(job["id"])["checkpoint"]["produced_keys"] == ["obj/shot1"])

# 5) M12 交付（母版规格 + 交付单 + 三重放行）
check("M12 母版规格", m12p.validate_master_spec("2.39:1", 24, -23.0, -1.5) == [])
sheet = {"spec": "2.39:1", "version": "v1", "duration": 1800, "qc_conclusion": "pass",
         "rights_status": "ok", "ai_label": "AI 生成", "rating": "全龄",
         "language": "zh", "color_tag": "Rec.709", "optional_items": []}
check("M12 交付单", m12s.validate_delivery_sheet(sheet) == [])
check("M12 分发三重放行", m12r.validate_release(True, True, True) == [])

# 6) M18 合规（AI 标识 + 交付前合规）
check("M18 AI 标识三类齐备", m18l.validate_ai_labels(["explicit", "implicit", "export_file"]) == [])
check("M18 交付前合规", m18c.validate_delivery_compliance(True, True, True, True, True) == [])

# 跨模块一致性：立项交付规格 → 交付母版规格同源
check("M1→M12 画幅同源", p["delivery_spec"]["master"] == sheet["spec"])

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "pipeline-e2e", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
