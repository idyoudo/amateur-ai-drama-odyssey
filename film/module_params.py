"""模块参数契约（每个模块的关键输入 + 推荐值）。

用途：让用户在前端为每个模块填写关键参数（不填则用推荐默认值）。
纯数据定义；校验在 validate_value。
"""

# field: key / label / type(number|select|text|bool) / default / rec(推荐说明) / options / min / max
MODULE_PARAMS = {
  "M1": {"title": "立项与包型", "fields": [
    {"key": "episodes", "label": "集数", "type": "number", "default": 6, "rec": "首季推荐 6", "min": 1, "max": 50},
    {"key": "minutes", "label": "单集时长(分)", "type": "select", "default": 30, "rec": "推荐 30", "options": [22, 30, 45]},
    {"key": "rating", "label": "分级", "type": "select", "default": "12+", "options": ["全龄", "12+", "16+"]},
    {"key": "style", "label": "风格", "type": "select", "default": "写实", "options": ["写实", "日漫", "3D", "国风"]},
    {"key": "pilot_mode", "label": "先导集模式", "type": "bool", "default": False},
  ]},
  "M2": {"title": "剧本", "fields": [
    {"key": "form", "label": "剧集形态", "type": "select", "default": "half_hour", "options": ["half_hour", "pilot_1h", "feature"]},
    {"key": "scenes", "label": "目标场次", "type": "number", "default": 20, "rec": "30 分钟剧推荐 12–25", "min": 5, "max": 100},
    {"key": "rewrite", "label": "两稿 + Rewrite", "type": "bool", "default": True},
    {"key": "reviewer", "label": "剧本审片人岗位", "type": "select", "default": "showrunner", "options": ["showrunner", "writer", "legal"]},
  ]},
  "M3": {"title": "选角定妆", "fields": [
    {"key": "characters", "label": "角色（逗号分隔）", "type": "text", "default": "主角,配角", "rec": "从剧本自动抽取"},
    {"key": "anchor_count", "label": "锚点数", "type": "number", "default": 3, "rec": "最少 3、最多 8", "min": 3, "max": 8},
    {"key": "voice", "label": "默认音色", "type": "text", "default": "v1"},
    {"key": "lock_threshold", "label": "一致性阈值", "type": "number", "default": 0.45, "rec": "待自有样本标定", "min": 0.3, "max": 0.9},
  ]},
  "M4": {"title": "分镜", "fields": [
    {"key": "shots_per_scene", "label": "每场镜头数", "type": "text", "default": "1-3"},
    {"key": "size_preset", "label": "景别循环", "type": "text", "default": "WS,MS,MCU,CU,MLS,LS"},
    {"key": "move_preset", "label": "运镜循环", "type": "text", "default": "固定,推,摇,跟,移"},
    {"key": "max_same_frame", "label": "同框上限", "type": "number", "default": 3, "min": 1, "max": 5},
  ]},
  "M5": {"title": "摄影生成", "fields": [
    {"key": "model", "label": "视频模型", "type": "text", "default": "kling-v2", "rec": "须支持参考图 r2v"},
    {"key": "seed", "label": "seed", "type": "number", "default": 42, "rec": "同场景复用稳色调"},
    {"key": "candidates", "label": "每镜候选数", "type": "number", "default": 4, "min": 1, "max": 9},
    {"key": "aspect", "label": "生成画幅", "type": "select", "default": "16:9", "options": ["16:9", "2.39:1", "9:16"]},
  ]},
  "M6": {"title": "一致性", "fields": [
    {"key": "face_threshold", "label": "人脸阈值", "type": "number", "default": 0.45, "rec": "待标定", "min": 0.3, "max": 0.9},
    {"key": "quantile", "label": "分位截断", "type": "text", "default": "P10", "rec": "低于本集 P10 进复核"},
    {"key": "continuity", "label": "连续性检查", "type": "bool", "default": True},
  ]},
  "M7": {"title": "表演配音", "fields": [
    {"key": "voice", "label": "TTS 音色", "type": "text", "default": "v1"},
    {"key": "emotion", "label": "默认情绪", "type": "select", "default": "neutral", "options": ["neutral", "happy", "sad", "angry", "fearful", "surprised", "disgusted"]},
    {"key": "speed", "label": "语速", "type": "number", "default": 1.0, "min": 0.5, "max": 2.0},
    {"key": "lipsync_scope", "label": "口型范围", "type": "select", "default": "closeup_only", "options": ["closeup_only", "all"]},
  ]},
  "M8": {"title": "声音配乐", "fields": [
    {"key": "platform", "label": "配乐平台", "type": "select", "default": "ace_step", "options": ["ace_step", "suno", "mureka"]},
    {"key": "cue_count", "label": "Cue 数/集", "type": "number", "default": 3, "min": 1, "max": 12},
    {"key": "loudness", "label": "目标响度", "type": "number", "default": -23.0, "rec": "归档母版 −23 LUFS"},
    {"key": "true_peak", "label": "真峰值上限", "type": "number", "default": -1.0},
  ]},
  "M9": {"title": "剪辑", "fields": [
    {"key": "asl_min", "label": "ASL 下限(s)", "type": "number", "default": 2.0},
    {"key": "asl_max", "label": "ASL 上限(s)", "type": "number", "default": 4.0},
    {"key": "act_breaks", "label": "幕间数", "type": "number", "default": 3, "min": 1, "max": 6},
    {"key": "fps", "label": "帧率", "type": "number", "default": 24, "rec": "唯一 24fps 时间线"},
  ]},
  "M10": {"title": "门禁", "fields": [
    {"key": "require_signature", "label": "必须署名", "type": "bool", "default": True},
    {"key": "default_approver_role", "label": "默认审批岗位", "type": "select", "default": "showrunner", "options": ["showrunner", "director", "writer", "qc", "colorist", "legal"]},
    {"key": "sample_rate", "label": "回溯抽检比例", "type": "number", "default": 0.1, "rec": "≥10%", "min": 0, "max": 1},
  ]},
  "M11": {"title": "母版", "fields": [
    {"key": "codec", "label": "编码", "type": "select", "default": "ProRes 422 HQ", "options": ["ProRes 422 HQ", "ProRes 4444"]},
    {"key": "resolution", "label": "分辨率", "type": "text", "default": "3840x2160"},
    {"key": "loudness", "label": "响度", "type": "number", "default": -23.0},
    {"key": "tc_start", "label": "TC 起点", "type": "text", "default": "01:00:00:00"},
  ]},
  "M12": {"title": "交付", "fields": [
    {"key": "master", "label": "主母版", "type": "select", "default": "2.39:1", "options": ["2.39:1", "16:9", "9:16"]},
    {"key": "platform", "label": "平台版", "type": "select", "default": "16:9", "options": ["2.39:1", "16:9", "9:16"]},
    {"key": "derived", "label": "衍生版", "type": "select", "default": "9:16", "options": ["2.39:1", "16:9", "9:16"]},
    {"key": "optional", "label": "可选交付", "type": "text", "default": "HDR10,5.1,48fps"},
  ]},
  "M13": {"title": "任务编排", "fields": [
    {"key": "concurrency", "label": "并发", "type": "number", "default": 1, "min": 1, "max": 16},
    {"key": "retry_limit", "label": "自动重试上限", "type": "number", "default": 2, "rec": "单镜 K≤2"},
    {"key": "lease_min", "label": "租约(分钟)", "type": "number", "default": 90},
  ]},
  "M14": {"title": "成本配额", "fields": [
    {"key": "budget_project", "label": "项目预算(元)", "type": "number", "default": 100000},
    {"key": "budget_episode", "label": "单集预算(元)", "type": "number", "default": 20000},
    {"key": "warn_threshold", "label": "预警阈值", "type": "number", "default": 0.8, "rec": "80% 预警"},
  ]},
  "M15": {"title": "存储", "fields": [
    {"key": "object_root", "label": "对象根", "type": "text", "default": "users/{uid}/dramas/{pid}"},
    {"key": "retention_days", "label": "中间产物保留(天)", "type": "number", "default": 30},
  ]},
  "M16": {"title": "协作", "fields": [
    {"key": "approver_pool", "label": "候选审片人", "type": "text", "default": "showrunner,director,qc"},
    {"key": "self_review", "label": "允许自审自批", "type": "bool", "default": False, "rec": "禁止"},
  ]},
  "M17": {"title": "供应商", "fields": [
    {"key": "text_model", "label": "文本模型", "type": "text", "default": "qwen3-max"},
    {"key": "image_model", "label": "图像模型", "type": "text", "default": "wanx-v1"},
    {"key": "video_model", "label": "视频模型", "type": "text", "default": "kling-v2"},
    {"key": "tts_model", "label": "TTS 模型", "type": "text", "default": "cosyvoice-v1"},
  ]},
  "M18": {"title": "合规", "fields": [
    {"key": "ai_labels", "label": "AI 标识", "type": "text", "default": "explicit,implicit,export_file", "rec": "三类齐备"},
    {"key": "rating_scheme", "label": "分级体系", "type": "text", "default": "境内平台口径"},
  ]},
  "M19": {"title": "VFX", "fields": [
    {"key": "vfx_types", "label": "VFX 类型", "type": "text", "default": "repair,sky,cleanup"},
    {"key": "skeleton_policy", "label": "物理骨架", "type": "select", "default": "required", "options": ["required", "optional"]},
  ]},
}


def defaults(module):
    m = MODULE_PARAMS.get(module)
    if not m:
        return {}
    return {f["key"]: f["default"] for f in m["fields"]}


def validate_value(field, value):
    """校验单个字段值（fail-closed）。返回错误消息或 None。"""
    t = field.get("type")
    if t == "number":
        try:
            v = float(value)
        except (TypeError, ValueError):
            return "%s 必须是数字" % field["label"]
        if "min" in field and v < field["min"]:
            return "%s 不能小于 %s" % (field["label"], field["min"])
        if "max" in field and v > field["max"]:
            return "%s 不能大于 %s" % (field["label"], field["max"])
    elif t == "select":
        if value not in field.get("options", []):
            return "%s 取值非法：%r" % (field["label"], value)
    elif t == "bool":
        if not isinstance(value, bool):
            return "%s 必须是布尔值" % field["label"]
    return None


def validate_module(module, values):
    """校验一个模块的参数集。返回违规列表，空 = 合规。"""
    spec = MODULE_PARAMS.get(module)
    if not spec:
        return ["未知模块：%s" % module]
    v = []
    fields = {f["key"]: f for f in spec["fields"]}
    for k, val in (values or {}).items():
        if k not in fields:
            v.append("未知字段：%s" % k)
            continue
        msg = validate_value(fields[k], val)
        if msg:
            v.append(msg)
    return v
