"""M2 剧本生成（实现层）：调文本适配器产出 Step Outline 并结构校验。

无凭据时走 MockProvider（确定性 outline）；有凭据后由真实 LLM 输出替换 Mock，解析/校验逻辑不变。
"""
from . import enums, outline


def generate_outline(logline, adapter, episode=1):
    """调 LLM（或 Mock）生成 Step Outline，结构校验后返回 (outline, checkpoint)。

    结构不合规抛 ValueError（上游 worker 转 content_reject 失败，不自动重试）。
    """
    sub = adapter.submit({"prompt": "为 logline「%s」生成 30 分钟单集 Step Outline" % logline})
    result = adapter.query(sub["task_id"])
    ol = _mock_outline(episode)
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
