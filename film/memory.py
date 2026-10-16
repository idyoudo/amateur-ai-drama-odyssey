"""长篇连贯性：四层记忆（C1）+ 因果链变更记录（C2）。

来源：huohuo-drama 的四层连贯性记忆（全局快照 / 上一章结尾 / 更早章节摘要 / 关键词账本，各设硬上限）
与因果链 Change Record（每场记录 触发→过程→结果）。纯确定性实现，不依赖付费 LLM。

用途：跨集生成时把「当前状态」注入提示词，保证 6 集 × 30 分钟长篇的人物/设定/伏笔不跑偏。
"""
# 四层各自的硬上限（控制提示词长度，防止上下文膨胀）
LAYER_LIMITS = {
    "global_snapshot": 1,      # 全局状态快照：只保留最新一份
    "prev_tail": 1,            # 上一集结尾：只保留一份
    "earlier_digest": 5,       # 更早章节摘要：最多 5 条
    "keyword_ledger": 40,      # 关键词检索账本：最多 40 条
}

CHANGE_FIELDS = ("trigger", "process", "result")   # 因果链三段


class MemoryError(Exception):
    """记忆层非法（fail-closed）。"""


def make_memory():
    return {"global_snapshot": {}, "prev_tail": "", "earlier_digest": [], "keyword_ledger": []}


def update_memory(mem, episode, outline=None, change_records=None, keywords=None):
    """按一集内容更新四层记忆（就地，各自截断到硬上限）。返回新记忆。"""
    import copy as _copy
    m = _copy.deepcopy(mem)
    # 全局快照：最新一集的状态
    if outline is not None:
        m["global_snapshot"] = {"episode": episode,
                                "scenes": len(outline.get("scenes", [])),
                                "form": outline.get("form"),
                                "last_event": (outline["scenes"][-1]["event"] if outline.get("scenes") else "")}
    # 上一集结尾 ← 把原 prev_tail 挤入更早摘要
    if m.get("prev_tail") and m["global_snapshot"].get("episode", 0) > 1:
        m["earlier_digest"].append(m["prev_tail"])
        m["earlier_digest"] = m["earlier_digest"][-LAYER_LIMITS["earlier_digest"]:]
    if outline and outline.get("scenes"):
        m["prev_tail"] = "第%d集结尾：%s" % (episode, outline["scenes"][-1]["event"])
    # 关键词账本
    for kw in (keywords or []):
        if kw not in m["keyword_ledger"]:
            m["keyword_ledger"].append(kw)
    m["keyword_ledger"] = m["keyword_ledger"][-LAYER_LIMITS["keyword_ledger"]:]
    return m


def assemble_context(mem):
    """把四层记忆装配成可注入提示词的状态文本（受硬上限约束）。"""
    parts = []
    gs = mem.get("global_snapshot") or {}
    if gs:
        parts.append("【全局状态】第%s集约%s场，形态%s，最新事件：%s" % (
            gs.get("episode"), gs.get("scenes"), gs.get("form"), gs.get("last_event")))
    if mem.get("prev_tail"):
        parts.append("【上一集结尾】" + mem["prev_tail"])
    if mem.get("earlier_digest"):
        parts.append("【更早摘要】" + "；".join(mem["earlier_digest"]))
    if mem.get("keyword_ledger"):
        parts.append("【关键词账本】" + "、".join(mem["keyword_ledger"]))
    return "\n".join(parts)


def validate_memory(mem):
    """记忆层不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    for layer, limit in LAYER_LIMITS.items():
        val = mem.get(layer)
        if val is None:
            v.append("缺记忆层 %s" % layer)
            continue
        n = 1 if isinstance(val, (dict, str)) else len(val)
        if n > limit:
            v.append("记忆层 %s 超上限：%d > %d" % (layer, n, limit))
    return v


def make_change_record(scene_no, trigger, process, result):
    """C2 因果链变更记录：每场「触发→过程→结果」。"""
    return {"scene_no": scene_no, "trigger": trigger, "process": process, "result": result}


def validate_change_record(rec):
    """因果链三段齐备（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    for f in CHANGE_FIELDS:
        if not rec.get(f):
            v.append("因果链缺 %s（场 %s）" % (f, rec.get("scene_no")))
    return v


def audit_change_records(records):
    """跨章审计：返回未闭合（结果为空）与断链（场号不连续）清单。"""
    issues = []
    prev = None
    for r in records:
        if not r.get("result"):
            issues.append({"scene_no": r.get("scene_no"), "issue": "结果未闭合"})
        if prev is not None and r.get("scene_no") not in (None, prev + 1):
            issues.append({"scene_no": r.get("scene_no"), "issue": "场号断链（上一场 %s）" % prev})
        prev = r.get("scene_no", prev)
    return issues
