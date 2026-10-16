"""供应商适配层三段式（M17.5-F02：提交/查询/下载）+ Mock（无凭据自证）。"""
import hashlib


class ProviderAdapter:
    """统一供应商接口：提交 → 轮询 → 下载，屏蔽各供应商差异。"""

    def submit(self, payload):
        raise NotImplementedError

    def query(self, task_id):
        raise NotImplementedError

    def download(self, result):
        raise NotImplementedError


class MockProvider(ProviderAdapter):
    """确定性 Mock：无凭据时让整条链路可自证（不调用真实供应商）。"""

    def __init__(self, kind):
        self.kind = kind

    def submit(self, payload):
        key = "%s|%s|%s" % (self.kind, payload.get("fingerprint", ""), payload.get("prompt", "")[:32])
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return {"task_id": "mock:" + h[:16], "status": "submitted"}

    def query(self, task_id):
        return {"task_id": task_id, "status": "done",
                "result": {"object_key": "mock/%s/%s.bin" % (self.kind, task_id)}}

    def download(self, result):
        return {"object_key": result.get("result", {}).get("object_key", "mock/obj"),
                "source": "MOCK — 非真实产物（EL-16）"}


def make_adapter(kind, kind_cfg):
    """按配置返回真实/Mock 适配器。未配置（缺 model/api_key）则返回 Mock。

    已配置时按 kind 返回对应真实适配器（OpenAI 兼容 / 异步视频三类协议）；
    未覆盖的 kind（music/lipsync）暂回 Mock，待供应商确定后补。
    """
    from .config import is_configured
    from . import adapters
    if not is_configured(kind_cfg):
        return MockProvider(kind)
    key, url, model = kind_cfg.get("api_key"), kind_cfg.get("api_url"), kind_cfg.get("model")
    if kind == "text":
        return adapters.OpenAICompatText(key, url, model)
    if kind == "image":
        return adapters.OpenAICompatImage(key, url, model)
    if kind == "tts":
        return adapters.OpenAICompatTTS(key, url, model)
    if kind == "video":
        return adapters.AsyncVideoProvider(key, url, model)
    if kind == "music":
        return adapters.AsyncTaskProvider(key, url, model, kind="music", create_path="/music/generations")
    if kind == "lipsync":
        return adapters.AsyncTaskProvider(key, url, model, kind="lipsync", create_path="/lipsync/jobs")
    # 未覆盖 kind：Mock
    return MockProvider(kind)
