#!/usr/bin/env python3
"""真实供应商适配器复测（mock HTTP，不联网）：三段式协议 + 错误分类。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film.suppliers import adapters

_t = [0]; _f = []
def check(n, c):
    _t[0] += 1
    if not c: _f.append(n)


class FakeResp:
    def __init__(self, status, payload=None, content=b"", text=""):
        self.status_code = status
        self._p = payload or {}
        self.content = content
        self.text = text or json.dumps(self._p)
    def json(self):
        return self._p


class FakeHttpx:
    """可编程的假 httpx：按 URL 返回预设响应，记录调用。"""
    def __init__(self, post_map=None, get_map=None):
        self.post_map = post_map or {}
        self.get_map = get_map or {}
        self.calls = []
    def post(self, url, json=None, timeout=None, headers=None):
        self.calls.append(("POST", url, json, headers))
        for k, v in self.post_map.items():
            if k in url:
                return v
        return FakeResp(500, text="no mock")
    def get(self, url, timeout=None, headers=None):
        self.calls.append(("GET", url, None, headers))
        for k, v in self.get_map.items():
            if k in url:
                return v
        return FakeResp(500, text="no mock")


def with_httpx(fake):
    sys.modules["httpx"] = fake


# 文本
with_httpx(FakeHttpx(post_map={"chat/completions": FakeResp(200, {"choices": [{"message": {"content": "ok"}}]})}))
tp = adapters.OpenAICompatText("k", "https://api.x/v1", "m")
r = tp.submit({"prompt": "hi"})
check("文本 submit 成功", r["status"] == "done" and r["text"]["choices"])
check("文本带 Bearer 头", any(c[3] and "Bearer k" in c[3].get("Authorization", "") for c in sys.modules["httpx"].calls))

# 文本 4xx → 不可重试
with_httpx(FakeHttpx(post_map={"chat/completions": FakeResp(400, text="bad param")}))
try:
    adapters.OpenAICompatText("k", "https://api.x/v1", "m").submit({"prompt": "x"})
    check("文本 4xx 抛错", False)
except adapters.ProviderError as e:
    check("文本 4xx 不可重试", e.retryable is False)

# 文本 5xx → 可重试
with_httpx(FakeHttpx(post_map={"chat/completions": FakeResp(503)}))
try:
    adapters.OpenAICompatText("k", "https://api.x/v1", "m").submit({"prompt": "x"})
    check("文本 5xx 抛错", False)
except adapters.ProviderError as e:
    check("文本 5xx 可重试", e.retryable is True)

# 图像
with_httpx(FakeHttpx(post_map={"images/generations": FakeResp(200, {"data": [{"url": "https://img/1.png"}]})}))
ip = adapters.OpenAICompatImage("k", "https://api.x/v1", "m")
r = ip.submit({"prompt": "a cat"})
check("图像 submit 返回 url", r["url"] == "https://img/1.png")
check("图像 download 有 object_key", "object_key" in ip.download(r))

# TTS
with_httpx(FakeHttpx(post_map={"audio/speech": FakeResp(200, content=b"\x00" * 100)}))
tt = adapters.OpenAICompatTTS("k", "https://api.x/v1", "m")
r = tt.submit({"prompt": "你好"})
check("TTS submit 字节数", r["bytes"] == 100)

# 视频异步三段式
with_httpx(FakeHttpx(
    post_map={"videos/generations": FakeResp(200, {"id": "task-1"})},
    get_map={"videos/generations/task-1": FakeResp(200, {"status": "succeeded", "output": {"url": "https://v/1.mp4"}})}))
vp = adapters.AsyncVideoProvider("k", "https://api.x/v1", "m")
sub = vp.submit({"prompt": "shot"})
check("视频 submit 返回 task_id", sub["task_id"] == "task-1" and sub["status"] == "submitted")
q = vp.query("task-1")
check("视频 query done", q["status"] == "done" and q["url"] == "https://v/1.mp4")
check("视频 download 有 object_key", "object_key" in vp.download(q))

total = _t[0]; passed = total - len(_f)
print(json.dumps({"module": "M17-real-adapters", "total": total, "pass": passed, "fail": len(_f)}, ensure_ascii=False))
sys.exit(1 if _f else 0)
