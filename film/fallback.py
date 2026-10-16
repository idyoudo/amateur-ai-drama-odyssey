"""双管线降级（C3，源自 huohuo/LocalMiniDrama）。

主路径：AI 视频（图生视频）。降级路径：**帧幻灯片**——关键帧序列 + Ken Burns 运镜，
镜头时长对齐配音（TTS），静音镜头加 BGM。用途：**无视频额度/供应商不可用时仍能出片**。

纯函数契约，输出可机检的 slideshow 计划（供渲染器或剪辑使用）。
"""
import hashlib

# Ken Burns 运动类型（对关键帧施加的推/拉/平移）
KEN_BURNS = ("zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "static")


def _pick_ken_burns(shot_no, size):
    """按镜号与景别确定性选 Ken Burns 运动（景别越大越倾向缓慢推拉）。"""
    wide = {"EWS", "WS", "LS", "MLS"}
    pool = ("zoom_in", "zoom_out") if size in wide else ("pan_left", "pan_right", "zoom_in")
    return pool[shot_no % len(pool)]


def build_slideshow(shots, voice_durations=None, bgm_for_silent=True):
    """由镜头表构建帧幻灯片计划。

    shots: [{shot_no, duration, status, size, image_key?}, ...]
    voice_durations: {shot_no: 配音秒数}；给定则镜头时长对齐配音（帧跟随配音时长）。
    返回 {segments: [...], total, source}。
    """
    voice_durations = voice_durations or {}
    segments = []
    total = 0.0
    for sh in shots:
        no = sh.get("shot_no")
        dur = float(voice_durations.get(no, sh.get("duration") or 3))
        if dur <= 0:
            dur = 3.0
        has_voice = no in voice_durations
        segments.append({
            "shot_no": no,
            "duration": dur,
            "motion": _pick_ken_burns(no, sh.get("size") or ""),
            "keyframe": sh.get("image_key") or "mock/shot_%s.png" % no,
            "bgm": (not has_voice) and bgm_for_silent,   # 静音镜头加 BGM
            "audio": "voice" if has_voice else ("bgm" if bgm_for_silent else "silent"),
        })
        total += dur
    plan = {"segments": segments, "total": round(total, 2), "count": len(segments), "source": "slideshow"}
    plan["fingerprint"] = hashlib.sha256(
        ("|".join("%s:%.2f:%s" % (s["shot_no"], s["duration"], s["motion"]) for s in segments)).encode()
    ).hexdigest()
    return plan


def validate_plan(plan):
    """计划不变量（fail-closed）。返回违规列表，空 = 合规。"""
    v = []
    if not plan.get("segments"):
        v.append("slideshow 计划为空")
    for s in plan.get("segments", []):
        if s.get("motion") not in KEN_BURNS:
            v.append("非法 Ken Burns 运动：%r" % s.get("motion"))
        if not s.get("duration") or s["duration"] <= 0:
            v.append("镜 %s 时长非正" % s.get("shot_no"))
        if not s.get("keyframe"):
            v.append("镜 %s 缺关键帧" % s.get("shot_no"))
    if not plan.get("fingerprint"):
        v.append("缺 fingerprint（幂等/去重依据）")
    return v


def choose_pipeline(video_available, force_slideshow=False):
    """双管线选择：视频可用走 AI 视频；否则降级帧幻灯片。"""
    if force_slideshow or not video_available:
        return "slideshow"
    return "ai_video"
