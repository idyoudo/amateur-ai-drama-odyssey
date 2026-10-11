"""时间线合法性校验（M9.1-F04：无重叠/无空洞、时长非零、引用素材存在）。"""


def make_clip(video_key, start, duration):
    return {"video_key": video_key, "start": start, "duration": duration}


def validate_timeline(clips, available_keys):
    """时间线不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not clips:
        v.append("时间线为空")
        return v
    sorted_clips = sorted(clips, key=lambda c: c["start"])
    for c in sorted_clips:
        if c["duration"] <= 0:
            v.append("时长非正：%s" % c)
        if c["video_key"] not in available_keys:
            v.append("引用素材不存在：%s" % c["video_key"])
    prev_end = 0
    for c in sorted_clips:
        if c["start"] < prev_end:
            v.append("重叠：start=%s 早于上一段结束 %s" % (c["start"], prev_end))
        elif c["start"] > prev_end:
            v.append("空洞：@%s 与上一段结束 %s 之间有缝隙" % (c["start"], prev_end))
        prev_end = max(prev_end, c["start"] + c["duration"])
    return v
