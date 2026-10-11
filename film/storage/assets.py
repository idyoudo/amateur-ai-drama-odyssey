"""资产登记与内容寻址（M15.3-F01：任一资产可反查生成参数与成本；内容哈希去重复用）。"""
import hashlib

from . import enums, keys, lineage


def content_sha256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def make_asset(project_id, episode_id, shot_id, kind, object_key, data=None,
               parent_asset_id=None, spec=None, generation_param=None):
    """构造资产登记。kind/spec 必须在封闭集合内（fail-closed）。"""
    if kind not in enums.ASSET_KINDS:
        raise ValueError("资产类型非法：%r（允许 %s）" % (kind, enums.ASSET_KINDS))
    if spec is not None and spec not in enums.MASTER_SPECS + enums.DERIVED_SPECS:
        raise ValueError("spec 非法：%r" % (spec,))
    return {
        "id": None,
        "project_id": project_id,
        "episode_id": episode_id,
        "shot_id": shot_id,
        "kind": kind,
        "object_key": object_key,
        "bytes": len(data) if data is not None else None,
        "checksum_sha256": content_sha256(data) if data is not None else None,
        "provider_task_id": None,
        "parent_asset_id": parent_asset_id,
        "spec": spec,
        "generation_param": generation_param or {},
    }


def validate_asset(asset):
    """单资产不变量校验（fail-closed）。"""
    v = keys.validate_object_key(asset.get("object_key"))
    if asset.get("kind") not in enums.ASSET_KINDS:
        v.append("kind 非法：%r" % (asset.get("kind"),))
    if asset.get("kind") == "master" and asset.get("spec") not in enums.MASTER_SPECS:
        v.append("母版缺合法 spec：%r（允许 %s）" % (asset.get("spec"), enums.MASTER_SPECS))
    return v
