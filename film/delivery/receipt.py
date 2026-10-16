"""发布锁定 + 签名收据（C7，源自 Qingshan 的 release lock 与 signed receipt）。

交付放行时生成**哈希清单 + HMAC 签名**的可举证收据：谁、何时、以何规格、哪些产物、
按何顺序放行。纯 Python（hmac/hashlib），不依赖外部服务；平台实投另立拍板项。
"""
import hashlib
import hmac
import json


def manifest(artifacts):
    """产物哈希清单：artifacts: [{name, sha256}] → 稳定排序的清单。"""
    items = sorted(({"name": a["name"], "sha256": a["sha256"]} for a in artifacts),
                   key=lambda x: x["name"])
    digest = hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {"items": items, "count": len(items), "manifest_sha256": digest}


def sign_receipt(receipt, secret):
    """对收据体做 HMAC 签名（密钥不入库不入 Git）。"""
    body = json.dumps({k: v for k, v in receipt.items() if k != "signature"},
                      ensure_ascii=False, sort_keys=True)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def make_receipt(project, version, spec, artifacts, approver, reason_code, when, channel_order=None):
    """构造发布锁定收据（字段齐备，签名由 sign_receipt 补）。"""
    m = manifest(artifacts)
    receipt = {
        "receipt_version": "1.0",
        "project": project, "version": version, "spec": spec,
        "manifest": m,
        "approver": approver, "reason_code": reason_code, "when": when,
        "release_lock": True,
        "channel_order": channel_order or ["母版归档", "平台版", "竖屏衍生"],
    }
    return receipt


def validate_receipt(receipt, secret=None):
    """收据不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    for f in ("project", "version", "spec", "approver", "reason_code", "when"):
        if not receipt.get(f):
            v.append("收据缺字段 %s" % f)
    if not receipt.get("release_lock"):
        v.append("收据未标记 release_lock")
    m = receipt.get("manifest") or {}
    if not m.get("manifest_sha256"):
        v.append("收据缺 manifest 指纹")
    if secret is not None:
        sig = receipt.get("signature")
        if not sig:
            v.append("收据未签名")
        elif not hmac.compare_digest(sig, sign_receipt(receipt, secret)):
            v.append("收据签名校验失败（被篡改）")
    return v
