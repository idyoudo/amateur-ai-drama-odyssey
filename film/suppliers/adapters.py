"""真实供应商适配器（提交/查询/下载三段式）。

- 文本/图像/配音：多数供应商兼容 OpenAI 风格（`/chat/completions`、`/images/generations`、`/audio/speech`）。
- 视频：异步三段式（创建任务 → 轮询状态 → 下载产物）。
- 所有适配器用 httpx；无凭据时由 make_adapter 返回 MockProvider（见 adapter.py）。
依据：PRD/M17.5-F02（屏蔽各供应商差异）、C-13。
"""
import time


class ProviderError(Exception):
    """供应商调用失败（携带可重试性）。"""

    def __init__(self, message, retryable=True):
        super().__init__(message)
        self.retryable = retryable


def _join(base, path):
    return base.rstrip("/") + path


class OpenAICompatText:
    """OpenAI 兼容文本生成（chat/completions）。"""

    def __init__(self, api_key, api_url, model, timeout=60):
        self.api_key, self.api_url, self.model, self.timeout = api_key, api_url, model, timeout

    def submit(self, payload):
        import httpx
        url = _join(self.api_url, "/chat/completions")
        body = {"model": self.model, "messages": [{"role": "user", "content": payload.get("prompt", "")}]}
        try:
            r = httpx.post(url, json=body, timeout=self.timeout,
                           headers={"Authorization": "Bearer " + self.api_key})
        except Exception as e:  # noqa: BLE001
            raise ProviderError("文本请求失败：%s" % e, retryable=True)
        if r.status_code >= 500 or r.status_code == 429:
            raise ProviderError("文本供应商 %d" % r.status_code, retryable=True)
        if r.status_code >= 400:
            raise ProviderError("文本供应商 %d：%s" % (r.status_code, r.text[:200]), retryable=False)
        return {"task_id": "text-ok", "status": "done", "text": r.json()}

    def query(self, task_id):
        return {"task_id": task_id, "status": "done"}

    def download(self, result):
        return {"object_key": "text/response.json", "data": result.get("text")}


class OpenAICompatImage:
    """OpenAI 兼容图像生成（images/generations）。"""

    def __init__(self, api_key, api_url, model, size="1024x1024", timeout=120):
        self.api_key, self.api_url, self.model = api_key, api_url, model
        self.size, self.timeout = size, timeout

    def submit(self, payload):
        import httpx
        url = _join(self.api_url, "/images/generations")
        body = {"model": self.model, "prompt": payload.get("prompt", ""), "size": self.size, "n": 1}
        try:
            r = httpx.post(url, json=body, timeout=self.timeout,
                           headers={"Authorization": "Bearer " + self.api_key})
        except Exception as e:  # noqa: BLE001
            raise ProviderError("图像请求失败：%s" % e, retryable=True)
        if r.status_code >= 500 or r.status_code == 429:
            raise ProviderError("图像供应商 %d" % r.status_code, retryable=True)
        if r.status_code >= 400:
            raise ProviderError("图像供应商 %d：%s" % (r.status_code, r.text[:200]), retryable=False)
        items = r.json().get("data", [])
        return {"task_id": "image-ok", "status": "done", "url": items[0].get("url") if items else None}

    def query(self, task_id):
        return {"task_id": task_id, "status": "done"}

    def download(self, result):
        return {"object_key": "image/out.png", "url": result.get("url")}


class OpenAICompatTTS:
    """OpenAI 兼容语音合成（audio/speech）。"""

    def __init__(self, api_key, api_url, model, voice="alloy", timeout=60):
        self.api_key, self.api_url, self.model = api_key, api_url, model
        self.voice, self.timeout = voice, timeout

    def submit(self, payload):
        import httpx
        url = _join(self.api_url, "/audio/speech")
        body = {"model": self.model, "input": payload.get("prompt", ""), "voice": self.voice}
        try:
            r = httpx.post(url, json=body, timeout=self.timeout,
                           headers={"Authorization": "Bearer " + self.api_key})
        except Exception as e:  # noqa: BLE001
            raise ProviderError("TTS 请求失败：%s" % e, retryable=True)
        if r.status_code >= 500 or r.status_code == 429:
            raise ProviderError("TTS 供应商 %d" % r.status_code, retryable=True)
        if r.status_code >= 400:
            raise ProviderError("TTS 供应商 %d：%s" % (r.status_code, r.text[:200]), retryable=False)
        return {"task_id": "tts-ok", "status": "done", "bytes": len(r.content)}

    def query(self, task_id):
        return {"task_id": task_id, "status": "done"}

    def download(self, result):
        return {"object_key": "audio/voice.mp3"}


class AsyncVideoProvider:
    """异步视频生成（创建任务 → 轮询 → 下载），适配可灵/Seedance/Vidu 等的通用协议。"""

    def __init__(self, api_key, api_url, model, poll_sec=10, max_polls=60, timeout=60):
        self.api_key, self.api_url, self.model = api_key, api_url, model
        self.poll_sec, self.max_polls, self.timeout = poll_sec, max_polls, timeout

    def submit(self, payload):
        import httpx
        url = _join(self.api_url, "/videos/generations")
        body = {"model": self.model, "prompt": payload.get("prompt", ""),
                "reference_images": payload.get("reference_images", [])}
        try:
            r = httpx.post(url, json=body, timeout=self.timeout,
                           headers={"Authorization": "Bearer " + self.api_key})
        except Exception as e:  # noqa: BLE001
            raise ProviderError("视频提交失败：%s" % e, retryable=True)
        if r.status_code >= 500 or r.status_code == 429:
            raise ProviderError("视频供应商 %d" % r.status_code, retryable=True)
        if r.status_code >= 400:
            raise ProviderError("视频供应商 %d：%s" % (r.status_code, r.text[:200]), retryable=False)
        data = r.json()
        return {"task_id": data.get("id") or data.get("task_id"), "status": "submitted"}

    def query(self, task_id):
        import httpx
        url = _join(self.api_url, "/videos/generations/%s" % task_id)
        r = httpx.get(url, timeout=self.timeout, headers={"Authorization": "Bearer " + self.api_key})
        d = r.json()
        status = d.get("status", "running")
        return {"task_id": task_id, "status": "done" if status in ("succeeded", "done") else status,
                "url": (d.get("output") or {}).get("url") if isinstance(d.get("output"), dict) else d.get("url")}

    def download(self, result):
        return {"object_key": "video/out.mp4", "url": result.get("url")}

    def wait(self, task_id):
        """轮询至完成或超时（供联调使用）。"""
        for _ in range(self.max_polls):
            q = self.query(task_id)
            if q["status"] == "done":
                return q
            time.sleep(self.poll_sec)
        raise ProviderError("视频任务 %s 轮询超时" % task_id, retryable=True)


class AsyncTaskProvider:
    """通用异步任务供应商（音乐 Suno/Mureka、口型 Sync.so 等：创建 → 轮询 → 下载）。

    create_path / query_path 可按供应商调整；默认 `/generations` 与 `/generations/{id}`。
    """

    def __init__(self, api_key, api_url, model, kind="async",
                 create_path="/generations", timeout=60, poll_sec=10, max_polls=60):
        self.api_key, self.api_url, self.model = api_key, api_url, model
        self.kind, self.create_path = kind, create_path
        self.timeout, self.poll_sec, self.max_polls = timeout, poll_sec, max_polls

    def submit(self, payload):
        import httpx
        url = _join(self.api_url, self.create_path)
        body = {"model": self.model, "prompt": payload.get("prompt", "")}
        if payload.get("fingerprint"):
            body["idempotency_key"] = payload["fingerprint"]
        try:
            r = httpx.post(url, json=body, timeout=self.timeout,
                           headers={"Authorization": "Bearer " + self.api_key})
        except Exception as e:  # noqa: BLE001
            raise ProviderError("%s 提交失败：%s" % (self.kind, e), retryable=True)
        if r.status_code >= 500 or r.status_code == 429:
            raise ProviderError("%s 供应商 %d" % (self.kind, r.status_code), retryable=True)
        if r.status_code >= 400:
            raise ProviderError("%s 供应商 %d：%s" % (self.kind, r.status_code, r.text[:200]), retryable=False)
        d = r.json()
        return {"task_id": d.get("id") or d.get("task_id"), "status": "submitted"}

    def query(self, task_id):
        import httpx
        url = _join(self.api_url, self.create_path + "/%s" % task_id)
        r = httpx.get(url, timeout=self.timeout, headers={"Authorization": "Bearer " + self.api_key})
        d = r.json()
        status = d.get("status", "running")
        done = status in ("succeeded", "done", "complete", "completed")
        out = d.get("output") or d.get("result") or {}
        url_out = out.get("url") if isinstance(out, dict) else d.get("url")
        return {"task_id": task_id, "status": "done" if done else status, "url": url_out}

    def download(self, result):
        return {"object_key": "%s/out.bin" % self.kind, "url": result.get("url")}

    def wait(self, task_id):
        for _ in range(self.max_polls):
            q = self.query(task_id)
            if q["status"] == "done":
                return q
            time.sleep(self.poll_sec)
        raise ProviderError("%s 任务 %s 轮询超时" % (self.kind, task_id), retryable=True)
