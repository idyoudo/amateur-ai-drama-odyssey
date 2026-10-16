"""M2 剧本生成（实现层）：调文本适配器产出 Step Outline 并结构校验。

无凭据时走 MockProvider（确定性 outline）；有凭据后由真实 LLM 输出替换 Mock，解析/校验逻辑不变。
"""
from . import enums, outline


PROMPT_TEMPLATE = (
    "你是职业编剧。为 logline「%s」生成 30 分钟单集 Step Outline，"
    "输出严格 JSON：{\"scenes\":[{\"number\":1,\"event\":\"\",\"goal\":\"\",\"conflict\":\"\",\"result\":\"\","
    "\"beats\":[\"Opening Image\"]}]}，覆盖 Save the Cat 15 拍，场次三元齐备。只输出 JSON。")


def _parse_llm_outline(text, episode=1):
    """尝试解析 LLM 返回的 JSON outline；失败返回 None（回退 Mock）。"""
    import json as _json
    import re as _re
    if not text:
        return None
    if isinstance(text, dict):
        data = text
    else:
        m = _re.search(r"\{.*\}", text, _re.S)
        if not m:
            return None
        try:
            data = _json.loads(m.group(0))
        except Exception:
            return None
    scenes_raw = (data or {}).get("scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        return None
    scenes = []
    for i, sc in enumerate(scenes_raw[:30], 1):
        scenes.append(outline.make_scene(
            sc.get("number", i), "SLUG", sc.get("event", "") or "事件 %d" % i,
            sc.get("goal", "") or "目标", sc.get("conflict", "") or "冲突",
            sc.get("result", "") or "结果", sc.get("beats") or ["Opening Image"]))
    return outline.make_outline("half_hour", scenes, 0.24, 0.50, 0.80, list(enums.TRUBY_NODES))


def generate_outline(logline, adapter, episode=1):
    """调 LLM（或 Mock）生成 Step Outline，结构校验后返回 (outline, checkpoint)。

    真实 LLM：解析其 JSON 输出为 outline；解析失败或 Mock：回退确定性 outline。
    结构不合规抛 ValueError（上游 worker 转 content_reject 失败，不自动重试）。
    """
    sub = adapter.submit({"prompt": PROMPT_TEMPLATE % logline})
    result = adapter.query(sub["task_id"])
    text = None
    if isinstance(result, dict):
        text = result.get("text") or result.get("data")
        if isinstance(text, dict):
            ch = text.get("choices")
            if isinstance(ch, list) and ch:
                text = (ch[0].get("message") or {}).get("content")
    ol = _parse_llm_outline(text, episode) or _mock_outline(episode)
    violations = outline.validate_outline(ol)
    if violations:
        raise ValueError("生成的 outline 结构不合规：%s" % ";".join(violations))
    checkpoint = {"produced_keys": [result.get("result", {}).get("object_key", "mock/outline")]}
    return ol, checkpoint


def _mock_outline(episode=1):
    """确定性 Mock：每集场次数与节拍起点按集号变化（集间内容不同）；覆盖 15 拍 + 四节点。"""
    n = 18 + (episode % 4)          # 18–21 场
    start = (episode - 1) % 15      # 节拍起点按集偏移
    scenes = []
    for i in range(n):
        scenes.append(outline.make_scene(
            i + 1, "SLUG",
            "第 %d 集·事件 %d" % (episode, i + 1), "目标 %d" % (i + 1),
            "冲突 %d" % (i + 1), "结果 %d" % (i + 1),
            [enums.BEATS_15[(i + start) % 15]]))
    return outline.make_outline("half_hour", scenes, 0.24, 0.50, 0.80, list(enums.TRUBY_NODES))
