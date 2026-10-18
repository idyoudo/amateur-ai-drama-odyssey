#!/usr/bin/env python3
"""AADO 控制面 API 冒烟测试（含登录鉴权：未登录 401 / 错误密码 401 / 登录后放行）。"""
import base64
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

# ---------------- 分集格式与小说改编 ----------------
r = client.get("/api/formats", headers=H)
check("格式预设 6 平台", r.status_code == 200 and len(r.json()["platforms"]) == 6)
r = client.post("/api/formats/recommend", headers=H,
                json={"platform_key": "hongguo", "source_type": "novel",
                      "chapters": 300, "genre": "悬疑"})
d = r.json()
check("红果 300 章建议", r.status_code == 200 and d["aspect"] == "9:16"
      and d["episodes"] == 100 and d["seasons"] == 2)
check("红果单集 1 分钟", d["episode_seconds"] == 60)
r = client.post("/api/formats/recommend", headers=H,
                json={"platform_key": "youtube", "source_type": "novel", "chapters": 300})
d = r.json()
check("YouTube 长视频建议", d["aspect"] == "16:9" and d["episode_seconds"] == 600)
r = client.post("/api/dramas", headers=H,
                json={"title": "长夜回声", "logline": "小说改编测试故事", "platform": "红果漫剧",
                      "rating": "12+", "genre": "悬疑", "platform_key": "hongguo",
                      "source_type": "novel",
                      "source_meta": {"author": "作者", "words_wan": 300, "chapters": 300},
                      "episodes": 100, "episode_seconds": 60, "aspect": "9:16", "minutes": 1})
d = r.json()
check("小说改编立项 200", r.status_code == 200 and d["package"]["episodes"] == 100)
check("小说改编画幅 9:16", d["delivery_spec"]["master"] == "9:16")
check("小说改编来源入库", d["source_meta"].get("type") == "novel"
      and d["source_meta"].get("chapters") == 300)
check("小说改编单集秒数", d["episode_seconds"] == 60)
novel_id = d["id"]
r = client.post("/api/dramas/%d/run" % novel_id, headers=H)
check("小说项目流水线 19 阶段", r.status_code == 200 and len(r.json()["stages"]) == 19)
check("短剧包型进入 M1",
      any(s["artifact"].get("package") == "100 集×1 分" for s in r.json()["stages"]))

# ---------------- 小说 TXT 导入 ----------------
_sample = ("测试小说\n作者：测试作者\n\n第一章 雨夜\n" + ("雨夜里的旧剧院传来回声。" * 20)
           + "\n\n第二章 回声\n" + ("调音师在旧磁带里听见自己的声音。" * 20)
           + "\n\n第三章 真相\n" + ("真相藏在那盘从未播放过的磁带里。" * 20))
_b64 = base64.b64encode(_sample.encode("utf-8")).decode()
r = client.post("/api/novels/import", headers=H,
                json={"filename": "测试小说.txt", "content_b64": _b64})
d = r.json()
check("小说导入 200", r.status_code == 200 and d["chapters"] == 3)
check("小说标题识别", d["title"] == "测试小说")
check("小说作者识别", d["author"] == "测试作者")
check("小说字数统计", d["char_count"] > 100 and d["words_wan"] > 0)
check("小说编码识别", d["encoding"] == "utf-8")
novel_id = d["novel_id"]
_gbk = base64.b64encode(_sample.encode("gb18030")).decode()
r = client.post("/api/novels/import", headers=H,
                json={"filename": "测试小说-GBK.txt", "content_b64": _gbk})
check("GBK 编码识别", r.status_code == 200 and r.json()["encoding"] == "gb18030"
      and r.json()["title"] == "测试小说")
r = client.post("/api/dramas", headers=H,
                json={"title": "导入小说项目", "logline": "从 TXT 导入的小说改编项目",
                      "platform": "红果漫剧", "rating": "12+", "genre": "悬疑",
                      "platform_key": "hongguo", "source_type": "novel",
                      "source_meta": {"novel_id": novel_id},
                      "episodes": 3, "episode_seconds": 60, "aspect": "9:16", "minutes": 1})
d = r.json()
check("导入小说立项 200", r.status_code == 200 and d["source_meta"].get("novel_id") == novel_id)
check("导入小说来源字段", d["source_meta"].get("filename") == "测试小说.txt"
      and d["source_meta"].get("chapters") == 3)

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
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"model": "v1", "api_key": "sk-test-video-0001", "api_url": ""}}})
check("PUT 配置 video", r.status_code == 200 and r.json()["config"]["video"]["model"] == "v1")
check("PUT 后 available 含 video", "video" in r.json()["available"])
# G1/G2：密钥绝不回传 + 空值保留 + 显式清除 + 落库
r = client.get("/api/models/config", headers=H)
check("配置不回传明文 Key", "sk-test-video-0001" not in r.text
      and r.json()["config"]["video"]["api_key"] == "")
check("配置返回 api_key_set", r.json()["config"]["video"]["api_key_set"] is True)
check("配置持久化后端", r.json()["persistence"]["backend"] == "database")
from film.jobs.db import ModelConfig  # noqa: E402
from apps.api.main import Session  # noqa: E402
with Session() as s:
    check("配置已落库", s.get(ModelConfig, "video") is not None)
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"api_key": ""}}})
check("空值保留原 Key", r.json()["config"]["video"]["api_key_set"] is True)
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"api_key": "…0001"}}})
check("掩码哨兵不覆盖原 Key", r.json()["config"]["video"]["api_key_set"] is True)
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"api_key_clear": True}}})
check("显式清除 Key", r.json()["config"]["video"]["api_key_set"] is False)
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"model": "v2", "api_key": "sk-secret-abcdef1234", "api_url": "https://example.com/v1"}}})
check("保存新 Key 不泄露", "sk-secret-abcdef1234" not in r.text
      and r.json()["config"]["video"]["api_key_hint"].endswith("1234"))
r = client.put("/api/models/config", headers=H, json={"config": {"video": {"api_url": "ftp://bad"}}})
check("非法 URL 422", r.status_code == 422)
client.put("/api/models/config", headers=H, json={"config": {"video": {"api_key_clear": True}}})

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

# 剧本编辑
r = client.get("/api/dramas/%d/script" % pid, headers=H)
check("剧本含场次", r.status_code == 200 and len(r.json()["scenes"]) > 0)
check("剧本含结构", "violations" in r.json()["structure"])
r = client.put("/api/dramas/%d/script/scene/1" % pid, headers=H, json={"goal": "新目标", "conflict": "新冲突", "result": "新结果"})
check("编辑场次 200", r.status_code == 200)
check("编辑后结构合规", r.json()["violations"] == [])
r = client.get("/api/dramas/%d/script" % pid, headers=H)
check("编辑已持久化", r.json()["scenes"][0]["goal"] == "新目标")

# 一键全流程
r = client.post("/api/dramas", headers=H, json={"title":"全流程","logline":"测试","platform":"p","rating":"全龄","genre":"悬疑"})
p2 = r.json()["id"]
r = client.post("/api/dramas/%d/produce" % p2, headers=H)
d = r.json()
check("全流程 200", r.status_code == 200)
check("全流程阶段全通过", d["stages_passed"] == d["stages_total"])
check("全流程含分镜数", d["shots"] > 0)
check("全流程可交付", d["deliverable"] is True)
check("全流程含成片时长", d["total_duration"] > 0)

# 资产库（筛选 / 详情 / 复用 / 导出）
r = client.get("/api/assets?limit=5", headers=H)
d = r.json()
check("资产库 200", r.status_code == 200 and d["character_total"] > 0 and d["shot_total"] > 0)
check("资产库统计", d["stats"]["generated"] > 0)
check("资产库分页", len(d["shots"]) <= 5)
_base_stats = d["stats"]
r = client.get("/api/assets?status=__generated&limit=5", headers=H)
d = r.json()
check("资产已生成筛选", d["shot_total"] > 0
      and all(s["status"] in ("已生成", "已选定") for s in d["shots"]))
check("资产统计不随状态变", d["stats"]["shots"] == _base_stats["shots"])
r = client.get("/api/assets?limit=2&offset=2", headers=H)
check("资产 offset 分页", len(r.json()["shots"]) == 2)
cid, sid = d["characters"][0]["id"], d["shots"][0]["id"]
_p2chars = client.get("/api/dramas/%d/characters" % p2, headers=H).json()
if _p2chars:
    cid = _p2chars[0]["id"]
r = client.get("/api/assets?q=主角", headers=H)
check("资产搜索", r.status_code == 200 and all("主角" in c["name"] for c in r.json()["characters"]))
r = client.get("/api/assets/characters/%d" % cid, headers=H)
check("角色详情", r.status_code == 200 and "shots" in r.json() and "shot_count" in r.json())
r = client.get("/api/assets/shots/%d" % sid, headers=H)
check("镜头详情", r.status_code == 200 and "candidates" in r.json())
_target = client.post("/api/dramas", headers=H,
                      json={"title": "复用目标", "logline": "资产复用测试项目",
                            "platform": "p", "rating": "全龄", "genre": "悬疑"}).json()["id"]
r = client.post("/api/assets/characters/%d/copy" % cid, headers=H,
                json={"target_project_id": _target})
check("角色复用", r.status_code == 200 and r.json()["created"] is True)
r = client.post("/api/assets/characters/%d/copy" % cid, headers=H,
                json={"target_project_id": _target})
check("角色复用幂等", r.status_code == 200 and r.json()["created"] is False)
r = client.get("/api/assets/export?project_id=%d" % p2, headers=H)
d = r.json()
check("资产导出", r.status_code == 200 and d["exported_at"] and len(d["characters"]) > 0)

# 分发中心
r = client.get("/api/distributions/channels", headers=H)
check("分发渠道 5 个", r.status_code == 200 and len(r.json()["channels"]) == 5)
r = client.post("/api/distributions", headers=H,
                json={"project_id": p2, "channel_key": "douyin",
                      "scheduled_at": "2026-11-01T10:00", "note": "测试排期"})
d = r.json()
did = d["id"]
check("创建分发", r.status_code == 200 and d["status"] == "已排期")
r = client.patch("/api/distributions/%d" % did, headers=H,
                 json={"status": "已发布",
                       "metrics": {"views": 1000, "likes": 80,
                                   "completion_rate": 62.5, "revenue": 123.45}})
d = r.json()
check("更新分发", r.status_code == 200 and d["status"] == "已发布"
      and d["metrics"]["views"] == 1000)
r = client.get("/api/distributions", headers=H)
d = r.json()
check("分发汇总", d["summary"]["published"] >= 1 and d["summary"]["views"] >= 1000)
r = client.delete("/api/distributions/%d" % did, headers=H)
check("删除分发", r.status_code == 200 and r.json()["deleted"] is True)

# 审核中心
r = client.post("/api/reviews", headers=H,
                json={"project_id": p2, "target_type": "delivery",
                      "title": "第 1 集成片审核", "comment": "请复核"})
d = r.json()
rid = d["id"]
check("创建审核", r.status_code == 200 and d["status"] == "待审")
r = client.patch("/api/reviews/%d" % rid, headers=H,
                 json={"status": "通过", "comment": "通过"})
d = r.json()
check("通过审核", r.status_code == 200 and d["status"] == "通过"
      and d["reviewer"] == "admin")
r = client.get("/api/reviews", headers=H)
check("审核汇总", r.json()["summary"]["approved"] >= 1)
r = client.delete("/api/reviews/%d" % rid, headers=H)
check("删除审核", r.status_code == 200 and r.json()["deleted"] is True)

# Playground
r = client.post("/api/playground/generate", headers=H, json={"kind": "图像生成", "prompt": "一只猫"})
check("Playground 生成 200", r.status_code == 200)
check("非法类型 422", client.post("/api/playground/generate", headers=H, json={"kind": "乱写", "prompt": "x"}).status_code == 422)
check("空提示词 422", client.post("/api/playground/generate", headers=H, json={"kind": "图像生成", "prompt": ""}).status_code == 422)
r = client.get("/api/playground/tasks", headers=H)
check("生成历史非空", r.status_code == 200 and len(r.json()) >= 1)
check("kinds 6 种", len(client.get("/api/playground/kinds", headers=H).json()["kinds"]) == 6)

# 交付单
r = client.get("/api/dramas/%d/delivery-sheet" % pid, headers=H)
d = r.json()
check("交付单 200", r.status_code == 200)
check("交付单含规格", d["spec"]["master"] == "2.39:1")
check("交付单含内容统计", d["content"]["shots"] > 0)
check("交付单含 AI 标识", "AI" in d["ai_label"])
check("交付单含可选交付标注", set(d["optional_delivery"].keys()) == {"HDR10", "5.1", "48fps"})

# QC 报告
r = client.get("/api/dramas/%d/qc-report" % pid, headers=H)
d = r.json()
check("QC 报告 200", r.status_code == 200)
check("QC 报告含逐项", len(d["items"]) >= 8)
check("QC 报告结论通过", d["conclusion"] == "通过")
check("QC 汇总正确", d["summary"]["passed"] == d["summary"]["total"])

# 项目设置
r = client.put("/api/dramas/%d" % pid, headers=H, json={"platform": "新平台", "minutes": 22})
check("更新项目 200", r.status_code == 200)
d = client.get("/api/dramas/%d" % pid, headers=H).json()
check("项目已更新", d["platform"] == "新平台" and d["minutes"] == 22)

# 角色
r = client.get("/api/dramas/%d/characters" % pid, headers=H)
chars = r.json()
check("角色列表非空", r.status_code == 200 and len(chars) >= 1)
check("角色含锚点", len(chars[0]["anchors"]) >= 3)
check("角色含音色", bool(chars[0]["voice_key"]))

# 连续性表
r = client.get("/api/dramas/%d/continuity" % pid, headers=H)
d = r.json()
check("连续性表 200", r.status_code == 200)
check("连续性表含行", len(d["rows"]) > 0)
check("连续性行含方向/视线", all("entry_side" in x and "eyeline" in x for x in d["rows"]))

# 剧本原文
r = client.get("/api/dramas/%d/screenplay" % pid, headers=H)
check("剧本原文 200", r.status_code == 200)
check("剧本原文含场景", "INT." in r.json()["text"] or "EXT." in r.json()["text"])
check("剧本原文含场次数", r.json()["scene_count"] > 0)

# 分集
r = client.get("/api/dramas/%d/episodes" % pid, headers=H)
d = r.json()
check("集列表 200", r.status_code == 200 and d["episodes"] >= 1)
check("集分镜明细", len(d["breakdown"]) >= 1)
ep1 = client.get("/api/dramas/%d/shots?episode=1" % pid, headers=H).json()
allsh = client.get("/api/dramas/%d/shots" % pid, headers=H).json()
check("按集过滤生效", len(ep1) <= len(allsh))
check("镜头带集号", all("episode_id" in x for x in allsh))

# 每集独立剧本
e1 = client.get("/api/dramas/%d/script?episode=1" % pid, headers=H).json()
e2 = client.get("/api/dramas/%d/script?episode=2" % pid, headers=H).json()
check("每集剧本不同", e1["scenes"][0]["event"] != e2["scenes"][0]["event"])

# 成本看板
r = client.get("/api/dramas/%d/cost-dashboard" % pid, headers=H)
d = r.json()
check("成本看板 200", r.status_code == 200)
check("看板含北极星", "minutes_per_yuan" in d["north_star"])
check("看板含过程指标", len(d["process"]) >= 4)
check("看板含影视指标", len(d["film_process"]) >= 4)

# 供应商三段式
r = client.get("/api/dramas/%d/provider-tasks" % pid, headers=H)
d = r.json()
check("供应商追踪 200", r.status_code == 200)
check("三段式含提交/查询/下载", all(
    [st["stage"] for st in k["stages"]] == ["提交", "查询", "下载"] for k in d["kinds"]))
check("供应商含多个类型", len(d["kinds"]) >= 3)

# 开源吸纳功能
r = client.get("/api/dramas/%d/memory" % pid, headers=H)
d = r.json()
check("记忆 200", r.status_code == 200)
check("记忆四层合规", d["violations"] == [])
check("上下文非空", len(d["context"]) > 0)
check("含因果链记录", len(d["change_records"]) > 0)
r = client.post("/api/dramas/%d/cost-preview" % pid, headers=H, json={"items": [{"kind": "video", "seconds": 60}]})
check("成本预估 200", r.status_code == 200 and r.json()["preview"]["total_cny"] > 0)
check("超阈值未确认被拦", len(r.json()["blocked"]) > 0)
r = client.post("/api/dramas/%d/cost-preview" % pid, headers=H, json={"items": [{"kind": "video", "seconds": 60}], "confirmed": True})
check("确认后放行", r.json()["blocked"] == [])
r = client.post("/api/dramas/%d/receipt" % pid, headers=H)
check("收据 200", r.status_code == 200 and r.json()["release_lock"] is True)
check("收据含签名", "signature" in r.json())

# 模块参数
r = client.get("/api/dramas/%d/module-params" % pid, headers=H)
d = r.json()
check("模块参数 19 个", r.status_code == 200 and len(d["modules"]) == 19)
check("M1 有推荐默认值", d["modules"]["M1"]["values"]["episodes"] == 6)
check("M1 有字段定义", len(d["modules"]["M1"]["fields"]) >= 5)
r = client.put("/api/dramas/%d/module-params/M1" % pid, headers=H, json={"episodes": 12, "minutes": 22})
check("保存 M1 参数 200", r.status_code == 200)
r = client.get("/api/dramas/%d/module-params" % pid, headers=H)
check("参数已持久化", r.json()["modules"]["M1"]["values"]["episodes"] == 12)
r = client.put("/api/dramas/%d/module-params/M1" % pid, headers=H, json={"episodes": 999})
check("非法参数 422", r.status_code == 422)
check("未知模块 404", client.put("/api/dramas/%d/module-params/M99" % pid, headers=H, json={}).status_code == 404)

# 聚合接口（C7）
r = client.get("/api/assets/summary?limit=10", headers=H)
check("资产聚合 200", r.status_code == 200 and "characters" in r.json())
check("资产聚合有镜头上限", len(r.json()["shots"]) <= 10)
r = client.get("/api/jobs/summary?limit=10", headers=H)
check("任务聚合 200", r.status_code == 200 and "jobs" in r.json())
d = r.json()
check("任务聚合含可观测字段",
      bool(d["jobs"]) and all(k in d["jobs"][0] for k in
                              ("progress", "attempts", "attempt_limit", "error_code", "lease_epoch")))
check("任务聚合 limit 夹紧", client.get("/api/jobs/summary?limit=9999", headers=H).json()["limit"] == 200)
check("任务聚合 offset 下限", client.get("/api/jobs/summary?offset=-5", headers=H).json()["offset"] == 0)
_jid = r1.json()["id"]
r = client.post("/api/drama-jobs/%d/cancel" % _jid, headers=H, json={"epoch": 0})
check("取消任务（epoch 0）", r.status_code == 200 and r.json()["status"] == "cancelled")
r = client.post("/api/drama-jobs/%d/cancel" % _jid, headers=H, json={"epoch": 7})
check("旧 epoch 取消被拒", r.status_code == 409)
r = client.get("/api/dramas/%d/overview" % pid, headers=H)
d = r.json()
check("项目概览 200", r.status_code == 200)
check("概览含镜头统计", "shots_total" in d and "completion" in d)
check("概览含分集", len(d["breakdown"]) >= 1)

# 通知待办（C4）
r = client.get("/api/notifications", headers=H)
d = r.json()
check("通知 200", r.status_code == 200)
check("通知含 items/count", "items" in d and "count" in d)

total = _total[0]
passed = total - len(_failed)
print(json.dumps({"module": "apps-api-smoke", "total": total, "pass": passed, "fail": len(_failed)}, ensure_ascii=False))
if _failed:
    for f in _failed:
        print("  - %s" % f, file=sys.stderr)
    sys.exit(1)
print("PASS", total)
sys.exit(0)
