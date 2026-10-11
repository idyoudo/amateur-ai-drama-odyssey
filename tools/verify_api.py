#!/usr/bin/env python3
"""AADO 控制面 API 冒烟测试（FastAPI TestClient + SQLite 临时库，不连真 PG）。"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# 在 import app 前设置临时 SQLite（引擎在 import 时创建）
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.main import app  # noqa: E402

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


client = TestClient(app)

# health
r = client.get("/health")
check("health 200", r.status_code == 200 and r.json()["status"] == "ok")

# 立项：合法
r = client.post("/api/dramas", json={"title": "回声", "logline": "一句话故事",
                                     "platform": "短剧平台", "rating": "全龄",
                                     "genre": "悬疑", "episodes": 6, "minutes": 30})
check("立项合法 200", r.status_code == 200 and r.json()["package"]["minutes"] == 30)

# 立项：缺 logline 应 422
r = client.post("/api/dramas", json={"title": "回声", "logline": "",
                                     "platform": "短剧平台", "rating": "全龄", "genre": "悬疑"})
check("立项缺 logline 422", r.status_code == 422)

# 入队 + 幂等
r1 = client.post("/api/drama-jobs", json={"project_id": "p1", "type": "shot_video",
                                          "idempotency_key": "p1:1:1:shot_video:fp1"})
r2 = client.post("/api/drama-jobs", json={"project_id": "p1", "type": "shot_video",
                                          "idempotency_key": "p1:1:1:shot_video:fp1"})
check("幂等入队同一 id", r1.status_code == 200 and r1.json()["id"] == r2.json()["id"])

# 列出任务
r = client.get("/api/dramas/p1/jobs")
check("列任务", r.status_code == 200 and len(r.json()) == 1)

# 模型配置
r = client.get("/api/models/config")
check("config 6 个 kind", r.status_code == 200 and len(r.json()["config"]) == 6)
r = client.put("/api/models/config", json={"config": {"video": {"model": "v1", "api_key": "k1", "api_url": ""}}})
check("PUT 配置 video", r.status_code == 200 and r.json()["config"]["video"]["model"] == "v1")
check("PUT 后 available 含 video", "video" in r.json()["available"])
r = client.get("/models")
check("模型配置页面 200", r.status_code == 200 and "模型参数配置" in r.text)

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "apps-api-smoke", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
