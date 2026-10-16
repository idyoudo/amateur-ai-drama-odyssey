"""首尾帧锚定链（C4，源自 LocalMiniDrama 尾帧链接 / huohuo 分段接缝）。

同一场景内的连续镜：上一镜**尾帧**作为下一镜**首帧**，消除分段生成接缝；
**换场/换景必须重挂参考图**（否则误差累积）。依据：M6.2-F04、E-57。
"""


def make_frame_anchor(shot_no, scene_no, head_frame, tail_frame, carries_ref=False):
    return {"shot_no": shot_no, "scene_no": scene_no,
            "head_frame": head_frame, "tail_frame": tail_frame,
            "carries_ref": carries_ref}


def build_chain(shots):
    """构建锚定链：同场景连续镜用上一镜尾帧作下一镜首帧；换场重挂参考图。

    shots: [{shot_no, scene_no, frame_key?}, ...]（按序）
    返回 [{shot_no, head_from, must_rerig_ref}, ...]
    """
    chain = []
    prev = None
    for sh in shots:
        same_scene = prev is not None and sh.get("scene_no") == prev.get("scene_no")
        if same_scene:
            chain.append({"shot_no": sh["shot_no"], "head_from": prev.get("tail_key") or ("尾帧@镜%s" % prev["shot_no"]),
                          "must_rerig_ref": False})
        else:
            chain.append({"shot_no": sh["shot_no"], "head_from": None, "must_rerig_ref": True})
        prev = {"shot_no": sh["shot_no"], "scene_no": sh.get("scene_no"),
                "tail_key": sh.get("frame_key") or ("尾帧@镜%s" % sh["shot_no"])}
    return chain


def validate_chain(chain):
    """锚定链不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    for i, link in enumerate(chain):
        if link.get("head_from") is None and not link.get("must_rerig_ref"):
            v.append("镜 %s 无首帧来源却未重挂参考图" % link.get("shot_no"))
        if i == 0 and link.get("head_from") is not None:
            v.append("首镜不应有首帧来源")
    return v
