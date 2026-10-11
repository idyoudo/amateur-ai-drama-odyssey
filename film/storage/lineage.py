"""资产族与血缘（M15.3：母版唯一约束 + 派生可回溯 + 版本谱系）。"""
from . import enums


def family_key(project_id, episode_id, shot_id):
    """资产族键：同一镜头（母版/派生版本）归为一族。"""
    return "%s:%s:%s" % (project_id, episode_id, shot_id)


def validate_family(assets):
    """不变量校验（fail-closed）。

    规则（EL-01/EL-11）：
    - 同族生成母版/归档母版各至多一个（M15.3-F04）；
    - 派生资产必须有 parent_asset_id 且指向族内已有资产（M15.2-F02 派生可回溯）。
    """
    v = []
    gen = [a for a in assets if a.get("spec") == enums.GENERATION_MASTER_SPEC]
    arc = [a for a in assets if a.get("spec") == enums.ARCHIVE_MASTER_SPEC]
    if len(gen) > 1:
        v.append("生成母版唯一约束被破坏：%d 个" % len(gen))
    if len(arc) > 1:
        v.append("归档母版唯一约束被破坏：%d 个" % len(arc))
    by_id = {a["id"]: a for a in assets if a.get("id") is not None}
    for a in assets:
        if a.get("kind") != "derived":
            continue
        parent = a.get("parent_asset_id")
        if parent is None:
            v.append("派生资产缺 parent_asset_id：%r" % (a.get("object_key"),))
        elif parent not in by_id:
            v.append("派生资产父级不在族内：%r" % (a.get("object_key"),))
        if a.get("spec") not in enums.DERIVED_SPECS:
            v.append("派生资产 spec 非法：%r（允许 %s）" % (a.get("spec"), enums.DERIVED_SPECS))
    return v
