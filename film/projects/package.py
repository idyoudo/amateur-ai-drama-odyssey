"""包型预设与参数校验（M1.0-F02 / M1.1-F04）。"""
from . import enums


def make_package(episodes=6, minutes=30):
    """默认包型「首季 6 集 × 30 分钟」，含 cold open 与 act breaks 结构标记（D2/EL-03）。"""
    if minutes not in enums.EPISODE_MINUTES:
        raise ValueError("单集时长档非法：%r（允许 %s）" % (minutes, enums.EPISODE_MINUTES))
    act_breaks = {22: 2, 30: 3, 45: 4}[minutes]
    return {
        "episodes": episodes,
        "minutes": minutes,
        "seconds": minutes * 60,
        "cold_open": True,
        "act_breaks": act_breaks,
    }


def validate_params(title, episodes, minutes):
    """参数校验（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not title:
        v.append("标题必填")
    elif len(title) > enums.TITLE_MAX:
        v.append("标题 ≤%d 字" % enums.TITLE_MAX)
    if not (enums.EPISODES_MIN <= episodes <= enums.EPISODES_MAX):
        v.append("集数 %d–%d" % (enums.EPISODES_MIN, enums.EPISODES_MAX))
    sec = minutes * 60
    if not (enums.SECONDS_MIN <= sec <= enums.SECONDS_MAX):
        v.append("单集 %d–%d 秒" % (enums.SECONDS_MIN, enums.SECONDS_MAX))
    return v
