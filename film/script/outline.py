"""Step Outline 模型与不变量（场景三元 + 结构校验）。"""
from . import enums, structure


def make_scene(number, slug_line, event, goal, conflict, result, beats=None):
    return {
        "number": number,
        "slug_line": slug_line,
        "event": event,
        "goal": goal,
        "conflict": conflict,
        "result": result,
        "beats": beats or [],
    }


def validate_scene(scene):
    """目标-冲突-结果三元（M2.4-F02）：缺任一段标记为不完整场景。"""
    v = []
    if not scene.get("goal"):
        v.append("场 %s 缺目标" % scene.get("number"))
    if not scene.get("conflict"):
        v.append("场 %s 缺冲突" % scene.get("number"))
    if not scene.get("result"):
        v.append("场 %s 缺结果" % scene.get("number"))
    return v


def make_outline(form, scenes, ppi, midpoint, ppii, truby_nodes):
    return {"form": form, "scenes": scenes, "ppi": ppi, "midpoint": midpoint,
            "ppii": ppii, "truby_nodes": truby_nodes}


def validate_outline(outline):
    """Step Outline 整体结构校验（fail-closed）。"""
    v = []
    if outline.get("form") not in enums.FORMS:
        v.append("形态非法：%r" % outline.get("form"))
        return v
    scenes = outline.get("scenes", [])
    v += structure.validate_scene_count(outline["form"], len(scenes))
    for sc in scenes:
        v += validate_scene(sc)
    covered = set()
    for sc in scenes:
        covered.update(sc.get("beats", []))
    v += structure.validate_beats(covered)
    v += structure.validate_beat_positions(
        outline.get("ppi", 0), outline.get("midpoint", 0), outline.get("ppii", 0))
    v += structure.validate_truby(outline.get("truby_nodes", []))
    return v
