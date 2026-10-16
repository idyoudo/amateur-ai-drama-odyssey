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

# 项目详情 + 静态资源
r = client.get("/api/dramas/%d" % pid, headers=H)
check("项目详情 200", r.status_code == 200 and r.json()["title"] == "回声")
check("详情含 last_run", r.json().get("last_run") is not None)
check("静态 app.css 200", client.get("/static/app.css").status_code == 200)
check("静态 app.js 200", client.get("/static/app.js").status_code == 200)
check("首页 shell 含 app.js", "app.js" in client.get("/").text)

# 分镜工作台
r = client.post("/api/dramas/%d/shots/generate" % pid, headers=H)
check("生成分镜表 200", r.status_code == 200 and r.json()["count"] > 0)
r = client.get("/api/dramas/%d/shots" % pid, headers=H)
shots = r.json()
check("分镜列表非空", r.status_code == 200 and len(shots) > 0)
check("镜头字段齐备", all(k in shots[0] for k in ("shot_no","size","angle","move","duration","status")))
ids = [sh["id"] for sh in shots[:3]]
r = client.post("/api/dramas/%d/shots/batch" % pid, headers=H, json={"shot_ids": ids})
check("批量生成 3 镜", r.status_code == 200 and r.json()["generated"] == 3)
r = client.get("/api/dramas/%d/shots" % pid, headers=H)
check("批量后状态已更新", sum(1 for x in r.json() if x["status"] == "已生成") >= 3)

# 抽卡候选
sh_id = shots[0]["id"]
r = client.post("/api/shots/%d/candidates" % sh_id, headers=H)
check("生成 4 候选", r.status_code == 200 and r.json()["count"] == 4)
r = client.get("/api/shots/%d/candidates" % sh_id, headers=H)
cands = r.json()
check("候选列表 4 个", len(cands) == 4)
check("候选含分数", all("score" in c for c in cands))
r = client.post("/api/candidates/%d/select" % cands[0]["id"], headers=H)
check("选定候选 200", r.status_code == 200)
r = client.get("/api/shots/%d/candidates" % sh_id, headers=H)
check("选择位唯一", sum(1 for c in r.json() if c["selected"]) == 1)

# 成片组装（M9 时间线）
r = client.post("/api/dramas/%d/assemble" % pid, headers=H)
d = r.json()
check("组装 200", r.status_code == 200)
check("组装含时间线", len(d["timeline"]) > 0)
check("时长 = 镜头时长之和", abs(d["total_duration"] - sum(x["duration"] for x in d["timeline"])) < 0.01)
check("ASL 在 2-4s 带内", d["asl_in_band"] is True)
check("幕结构 4 段", len(d["acts"]) == 4)
check("时间线无违规", d["violations"] == [])

# 五门禁
r = client.get("/api/dramas/%d/gates" % pid, headers=H)
gates = r.json()
check("门禁 5 个", r.status_code == 200 and len(gates) == 5)
check("门禁节点齐备", [g["node"] for g in gates] == ["script","casting","board","picture","master"])
check("门禁含署名+理由码", all("approver" in g and "reason_code" in g for g in gates))
check("门禁含二元清单", all(len(g["checklist"]) > 0 for g in gates))

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "apps-api-smoke", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
