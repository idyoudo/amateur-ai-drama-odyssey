"""资产编号参考槽位（C8，源自 LocalMiniDrama `@图片N` / Seedance2 资产编号）。

参考图挂载标准化：提示词中用 `@图片N` 指代参考图，槽位顺序固定为
**场景 → 角色 → 道具**（与 M3 锚点 / M15 资产库严格对齐），避免手挂错配。
依据：M6.2-F01（含角色镜头参考图挂载率 100%）。
"""

SLOT_ORDER = ("scene", "character", "prop")


def build_slots(scene_ref=None, character_refs=None, prop_refs=None):
    """按固定顺序装配参考图槽位 → [{slot, kind, asset_id, token}]。

    token 形如 @图片1、@图片2…（编号从 1 起，顺序 = 场景 → 角色 → 道具）。
    """
    ordered = []
    if scene_ref:
        ordered.append(("scene", scene_ref))
    for c in (character_refs or []):
        ordered.append(("character", c))
    for p in (prop_refs or []):
        ordered.append(("prop", p))
    slots = []
    for i, (kind, asset_id) in enumerate(ordered, 1):
        slots.append({"slot": i, "kind": kind, "asset_id": asset_id, "token": "@图片%d" % i})
    return slots


def compile_slot_prompt(base_prompt, slots):
    """把槽位前缀编译进提示词：`[参考图] @图片1=场景… @图片2=角色…` 前置。"""
    if not slots:
        return base_prompt
    ref = " ".join("%s=%s:%s" % (s["token"], s["kind"], s["asset_id"]) for s in slots)
    return "[参考图] " + ref + " | " + base_prompt


def validate_slots(slots, max_slots=9):
    """槽位不变量（fail-closed）：编号连续从 1 起、顺序合规、不超过上限（r2v 1–9 张）。"""
    v = []
    if len(slots) > max_slots:
        v.append("参考图槽位 %d 超上限 %d（r2v 支持 1–9 张）" % (len(slots), max_slots))
    for i, s in enumerate(slots, 1):
        if s.get("slot") != i or s.get("token") != "@图片%d" % i:
            v.append("槽位编号不连续：%r" % s)
        if s.get("kind") not in SLOT_ORDER:
            v.append("非法槽位类型：%r" % s.get("kind"))
    kinds = [s["kind"] for s in slots]
    ordered = [k for k in SLOT_ORDER for k in kinds if k == k]
    # 顺序须为 场景→角色→道具
    if kinds != sorted(kinds, key=lambda k: SLOT_ORDER.index(k)):
        v.append("槽位顺序不合规（应为 场景→角色→道具）：%s" % kinds)
    return v
