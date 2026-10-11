"""输入指纹与幂等键（M13.4-F01：相同输入重复提交 0 次付费调用）。"""
import hashlib
import json


def input_fingerprint(prompt, model_version, params, seed, asset_hashes):
    """sha256(prompt + model_version + params + seed + 参考素材 hash)。

    模型升级必须换指纹：model_version 参与哈希，升级即换指纹，杜绝新旧产物混用。
    """
    params_key = json.dumps(params, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    asset_key = ",".join(sorted(asset_hashes))
    payload = "\x1f".join([str(prompt), str(model_version), params_key, str(seed), asset_key])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def idempotency_key(project, episode, shot, job_type, fingerprint):
    """幂等键（任务编排设计 §三：project:episode:shot:type:fingerprint）。"""
    return "%s:%s:%s:%s:%s" % (project, episode, shot, job_type, fingerprint)
