#!/usr/bin/env python3
"""AADO 控制面 API 冒烟测试（含登录鉴权：未登录 401 / 错误密码 401 / 登录后放行）。"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.main import app  # noqa: E402

_total = [0]
_failed = []


def check(name, cond):
    _total[0] += 1
    if not cond:
        _failed.append(name)


client = TestClient(app)

# ---------------- 鉴权 ----------------
check("未登录 401", client.get("/api/dramas").status_code == 401)
check("错误密码 401", client.post("/api/auth/login",
      json={"username": "admin", "password": "wrong"}).status_code == 401)
r = client.post("/api/auth/login", json={"username": "admin", "password": "test-password"})
check("正确登录 200 且有 token", r.status_code == 200 and bool(r.json().get("token")))
H = {"Authorization": "Bearer " + r.json()["token"]}

# ---------------- 公开端点 ----------------
check("health 200", client.get("/health").status_code == 200 and client.get("/health").json()["status"] == "ok")
check("首页 200", client.get("/").status_code == 200 and "AADO" in client.get("/").text)

# ---------------- 立项 ----------------
r = client.post("/api/dramas", headers=H, json={"title": "回声", "logline": "一句话故事",
                                                "platform": "短剧平台", "rating": "全龄",
                                                "genre": "悬疑", "episodes": 6, "minutes": 30})
check("立项合法 200", r.status_code == 200 and r.json()["package"]["minutes"] == 30)
check("立项缺 logline 422", client.post("/api/dramas", headers=H,
      json={"title": "回声", "logline": "", "platform": "p", "rating": "全龄", "genre": "悬疑"}).status_code == 422)

# ---------------- 项目持久化 ----------------
r = client.get("/api/dramas", headers=H)
check("项目列表含回声", r.status_code == 200 and any(p["title"] == "回声" for p in r.json()))
pid = r.json()[0]["id"]

# ---------------- 入队 + 幂等 ----------------
r1 = client.post("/api/drama-jobs", headers=H, json={"project_id": "p1", "type": "shot_video",
                                                     "idempotency_key": "p1:1:1:shot_video:fp1"})
r2 = client.post("/api/drama-jobs", headers=H, json={"project_id": "p1", "type": "shot_video",
                                                     "idempotency_key": "p1:1:1:shot_video:fp1"})
check("幂等入队同一 id", r1.status_code == 200 and r1.json()["id"] == r2.json()["id"])
check("列任务", client.get("/api/dramas/p1/jobs", headers=H).status_code == 200)

# ---------------- 流水线 ----------------
r = client.post("/api/dramas/%d/run" % pid, headers=H)
check("run 返回 19 阶段", r.status_code == 200 and len(r.json()["stages"]) == 19)
check("run 全通过", r.json()["summary"]["deliverable"] is True)

# ---------------- 模型配置 ----------------
r = client.get("/api/models/config", headers=H)
check("config 6 个 kind", r.status_code == 200 and len(r.json()["config"]) == 6)
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"model": "v1", "api_key": "k1", "api_url": ""}}})
check("PUT 配置 video", r.status_code == 200 and r.json()["config"]["video"]["model"] == "v1")
check("PUT 后 available 含 video", "video" in r.json()["available"])

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "apps-api-smoke", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
