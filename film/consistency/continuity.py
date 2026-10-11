"""连续性与剧本监督（M6.4：连续性字段表 / 屏幕方向 / eyeline / 时间天气）。"""
from . import enums


def make_take(duration, actor_position, entry_side, exit_side, key_action, lens,
              notes="", eyeline=None, day_night=None, weather=None):
    return {"duration": duration, "actor_position": actor_position,
            "entry_side": entry_side, "exit_side": exit_side,
            "key_action": key_action, "lens": lens, "notes": notes,
            "eyeline": eyeline, "day_night": day_night, "weather": weather}


def validate_take(take):
    """连续性字段完整率（M6.4-F01）。返回违规列表，空 = 合规。"""
    v = []
    for field in ("duration", "actor_position", "key_action", "lens"):
        if not take.get(field):
            v.append("缺连续性字段 %s" % field)
    for side_field in ("entry_side", "exit_side"):
        if take.get(side_field) not in enums.SCREEN_DIRECTIONS:
            v.append("屏幕方向非法：%s=%r" % (side_field, take.get(side_field)))
    if take.get("eyeline") is not None and take.get("eyeline") not in enums.EYELINES:
        v.append("eyeline 非法：%r" % (take.get("eyeline"),))
    return v


def validate_screen_direction(prev_take, cur_take):
    """屏幕方向「左出右入」（M6.4-F03）：前一镜 exit_side 与本镜 entry_side 应相反。"""
    v = []
    if prev_take and cur_take:
        if prev_take.get("exit_side") == cur_take.get("entry_side"):
            v.append("屏幕方向穿帮：前镜出 %s 侧，本镜应从另一侧入" % prev_take["exit_side"])
    return v


def validate_eyeline(shot_a_eyeline, shot_b_eyeline):
    """正反打视线互补（M6.4-F04）：A 看右则 B 看左。"""
    v = []
    if shot_a_eyeline in ("left", "right") and shot_a_eyeline == shot_b_eyeline:
        v.append("eyeline 不匹配：双方看向同侧 %s" % shot_a_eyeline)
    return v


def validate_time_weather(prev_day_night, cur_day_night, prev_weather, cur_weather):
    """时间/天气连续（M6.4-F05）：跨场跳变须显式声明，未声明即告警。"""
    v = []
    if prev_day_night and cur_day_night and prev_day_night != cur_day_night:
        v.append("时间跳变未声明：%s → %s" % (prev_day_night, cur_day_night))
    if prev_weather and cur_weather and prev_weather != cur_weather:
        v.append("天气跳变未声明：%s → %s" % (prev_weather, cur_weather))
    return v
