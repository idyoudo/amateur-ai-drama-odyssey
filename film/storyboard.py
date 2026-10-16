"""M4 分镜表生成（实现层）：从 Step Outline 的场次派生镜头表（M5 契约字段）。

每个场次派生 1–3 个镜头，景别/角度/主运镜从封闭枚举循环取值（确定性）。
依据：PRD/M4（分镜表字段）、PRD/M5（镜头语言枚举）。
"""
from film import enums

_SIZE_CYCLE = ("WS", "MS", "MCU", "CU", "MLS", "LS")
_ANGLE_CYCLE = ("eye_level", "low", "high", "over_shoulder")
_MOVE_CYCLE = ("固定", "推", "摇", "跟", "移")
_DUR_CYCLE = (3, 4, 5, 2)


def make_shotlist(outline, characters=None):
    """由场次列表派生镜头表。返回 [shot dict, ...]（未落库）。"""
    characters = characters or ["主角"]
    shots = []
    no = 0
    for sc in outline["scenes"]:
        n = 1 + (sc["number"] % 3)  # 1–3 镜/场（确定性）
        for j in range(n):
            no += 1
            size = _SIZE_CYCLE[(sc["number"] + j) % len(_SIZE_CYCLE)]
            angle = _ANGLE_CYCLE[(sc["number"] * 2 + j) % len(_ANGLE_CYCLE)]
            move = _MOVE_CYCLE[(sc["number"] + j * 2) % len(_MOVE_CYCLE)]
            dur = _DUR_CYCLE[(sc["number"] + j) % len(_DUR_CYCLE)]
            char = characters[(sc["number"] + j) % len(characters)]
            prompt = "%s, %s, %s，%s镜头" % (size, angle, move, "人物" if char else "空镜")
            shots.append({
                "shot_no": no, "scene_no": sc["number"],
                "size": size, "angle": angle, "move": move,
                "duration": dur, "characters": [char] if char else [],
                "dialogue": "", "prompt": prompt, "status": "待生成",
            })
    return shots


def validate_shot(shot):
    """镜头契约校验（fail-closed）：景别/角度/主运镜必须在封闭枚举内。"""
    v = []
    if shot.get("size") not in enums.SHOT_SIZES:
        v.append("景别非法：%r" % shot.get("size"))
    if shot.get("angle") not in enums.ANGLES:
        v.append("角度非法：%r" % shot.get("angle"))
    if shot.get("move") not in enums.MOVES:
        v.append("主运镜非法：%r" % shot.get("move"))
    if not shot.get("duration") or shot["duration"] <= 0:
        v.append("时长非正")
    return v
