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
    """按配置返回真实/Mock 适配器。未配置（缺 model/api_key）则返回 Mock。"""
    from .config import is_configured
    if is_configured(kind_cfg):
        # 真实供应商适配在凭据到位后按 kind 实现（视频/图/TTS/音乐/口型各自三段式）
        return MockProvider(kind)  # 占位：当前无真实供应商实现
    return MockProvider(kind)
