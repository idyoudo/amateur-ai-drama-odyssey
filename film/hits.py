"""爆款分析与配方：案例结构、三秒钩子、断章类型与项目体检。

说明：公开检索未能获得这三部剧可核验的播放量，案例中的数值一律留空/标注未核验；
结构拆解基于片名、题材与平台爆款公式，具体剧情以正片为准。
"""

FORMULAS = {
    "underdog": {"name": "极端反差 / 打脸", "desc": "开局最低点受辱，快速获得力量或身份，连续打脸；每 2–3 集一次明确爽点。"},
    "revenge": {"name": "复仇 / 因果", "desc": "家族/至亲被害，主角带着明确目标归来；仇恨驱动，阶段性复仇对象逐级升级。"},
    "identity": {"name": "身份错位 / 隐藏大佬", "desc": "主角被低估，真实身份逐步揭露；每集用一次身份反差制造期待。"},
    "system": {"name": "系统 / 进化", "desc": "数值化成长与吞噬/升级反馈；每集给一次可见的能力跃迁。"},
    "monster": {"name": "镇妖 / 单元怪", "desc": "妖祸单元 + 更强妖王升级；强视觉动作与封印/身世悬念。"},
    "forbidden": {"name": "禁忌情感 / 招惹", "desc": "危险关系与高频拉扯；每集一个暧昧/冲突点，断章在关系曝光。"},
}

HOOK_TYPES = [
    ("结果前置", "先给最刺激的结果，再倒叙原因"),
    ("冲突爆发", "第一秒就发生对抗/羞辱/追杀"),
    ("身份揭露", "一句话点出主角被隐藏的身份"),
    ("悬念提问", "用一个问题把观众钉在屏幕前"),
    ("倒计时/绝境", "给出明确时限或必死局面"),
]

CLIFFHANGERS = [
    ("绝境反转", "主角看似必败，最后一秒反杀/觉醒"),
    ("身份暴露", "真实身份被当场揭穿"),
    ("新敌登场", "更强敌人出现，旧冲突瞬间失效"),
    ("真相半揭", "只揭开一半秘密，留下更大疑问"),
    ("情感决裂", "关系在误会/背叛中破裂"),
]

GENRE_FORMULA = {
    "悬疑": "underdog", "逆袭": "underdog", "都市": "underdog",
    "玄幻": "system", "仙侠": "system", "奇幻": "system",
    "古装": "monster", "志怪": "monster", "镇妖": "monster",
    "言情": "forbidden", "甜宠": "forbidden", "爱情": "forbidden",
    "复仇": "revenge", "家族": "revenge",
}

SEED_CASES = [
    {
        "title": "穷骨荒神", "platform": "红果漫剧", "genre": "玄幻/逆袭",
        "heat_note": "用户反馈为平台头部爆款；公开检索未获得可核验播放量，数值待后台/用户补充。",
        "formula": "underdog", "hook_type": "冲突爆发", "cliffhanger_type": "绝境反转",
        "structure": {
            "opening": "被判定为『穷骨/废骨』，当众受辱、逐出/判死，最低点开局",
            "progression": "偶得荒神残魂/机缘 → 首次力量反杀 → 更强对手出现 → 身世与力量来源半揭",
            "cadence": "每 2–3 集一次打脸/突破；每集结尾留一个力量或身份悬念",
        },
        "visual": "强反差：破败底层场景 vs 荒神法相/金色力量；大招与俯拍大全景制造升级感",
        "why": "低起点强代入 + 成长确定性 + 连续打脸；观众不需要理解复杂设定，只需看主角一步步翻盘。",
        "source_note": "结构拆解基于片名/题材与平台爆款公式，剧情细节以正片为准。",
    },
    {
        "title": "招惹少年", "platform": "红果漫剧", "genre": "言情/禁忌",
        "heat_note": "用户反馈为平台头部爆款；公开检索未获得可核验播放量，数值待后台/用户补充。",
        "formula": "forbidden", "hook_type": "悬念提问", "cliffhanger_type": "身份暴露",
        "structure": {
            "opening": "主动招惹危险少年/身份差关系，第一秒抛出『你确定要招惹我？』式危险信号",
            "progression": "试探 → 占有/保护 → 身份秘密 → 误会/决裂 → 关系曝光",
            "cadence": "每集至少一个暧昧或对抗点；结尾卡在关系被撞破/身份被揭穿",
        },
        "visual": "近景与特写为主，冷暖对比；眼神、手指、距离感强化张力",
        "why": "禁忌关系带来持续张力，CP 拉扯提供高频情绪回报；每集一个可讨论的关系节点。",
        "source_note": "结构拆解基于片名/题材与平台爆款公式，剧情细节以正片为准。",
    },
    {
        "title": "横刀镇妖", "platform": "红果漫剧", "genre": "玄幻/镇妖",
        "heat_note": "用户反馈为平台头部爆款；公开检索未获得可核验播放量，数值待后台/用户补充。",
        "formula": "monster", "hook_type": "结果前置", "cliffhanger_type": "新敌登场",
        "structure": {
            "opening": "妖祸降临、百姓受难，主角一刀镇妖，先给结果再讲原因",
            "progression": "单元怪 → 更强妖王 → 封印/身世线索 → 更大妖祸",
            "cadence": "每集一只妖/一次出刀；结尾必有更强敌人或封印异动",
        },
        "visual": "强动作与强光效：刀光、妖形、广角压迫；动作镜头与大全景交替",
        "why": "单元怪提供稳定节奏，升级体系提供长期目标；动作奇观适合竖屏即时刺激。",
        "source_note": "结构拆解基于片名/题材与平台爆款公式，剧情细节以正片为准。",
    },
]


def playbook():
    return {
        "formulas": [{"key": k, **v} for k, v in FORMULAS.items()],
        "hooks": [{"type": t, "desc": d} for t, d in HOOK_TYPES],
        "cliffhangers": [{"type": t, "desc": d} for t, d in CLIFFHANGERS],
        "note": "公式来自公开爆款拆解与平台节奏常识；不保证结果，需结合题材与投放验证。",
    }


def formula_for_genre(genre):
    g = str(genre or "")
    for key, formula in GENRE_FORMULA.items():
        if key in g:
            return {"key": formula, **FORMULAS[formula]}
    return {"key": "underdog", **FORMULAS["underdog"]}


FORMULA_SIGNALS = {
    "underdog": ("废柴", "穷骨", "受辱", "逐出", "打脸", "逆袭", "翻盘", "最低点", "看不起"),
    "revenge": ("灭门", "复仇", "归来", "血债", "仇人", "家族", "报仇"),
    "identity": ("身份", "隐藏", "大佬", "真实身份", "伪装", "马甲"),
    "system": ("系统", "升级", "进化", "吞噬", "签到", "面板", "属性"),
    "monster": ("妖", "镇妖", "封印", "鬼", "怪", "刀", "妖王"),
    "forbidden": ("招惹", "禁忌", "暧昧", "少年", "偏执", "危险关系", "拉扯", "占有"),
}

HOOK_SIGNALS = {
    "冲突爆发": ("辱", "逐出", "逼", "追杀", "冲突", "打", "杀", "威胁"),
    "悬念提问": ("？", "?", "为什么", "是谁", "你确定", "难道"),
    "身份揭露": ("身份", "真实", "竟是", "原来", "隐藏"),
    "结果前置": ("一刀", "当场", "开局", "结果", "已经", "瞬间"),
    "倒计时/绝境": ("三天", "倒计时", "最后", "绝境", "必死", "只剩"),
}

CLIFF_SIGNALS = {
    "绝境反转": ("反杀", "觉醒", "逆转", "翻盘", "重生"),
    "身份暴露": ("身份", "揭穿", "暴露", "认亲"),
    "新敌登场": ("妖王", "更强", "新敌", "出现", "降临"),
    "真相半揭": ("真相", "秘密", "半揭", "线索"),
    "情感决裂": ("决裂", "误会", "背叛", "分手", "退婚"),
}

CADENCE = {
    "underdog": "每 2–3 集一次打脸/突破；每集结尾留一个力量或身份悬念",
    "revenge": "每 3–5 集解决一个复仇对象；结尾抛更大的幕后黑手",
    "identity": "每集用一次身份反差；结尾卡在身份即将暴露",
    "system": "每集一次可见的能力跃迁；结尾抛下一阶段任务",
    "monster": "每集一只妖/一次出刀；结尾必有更强敌人或封印异动",
    "forbidden": "每集一个暧昧/对抗点；结尾卡在关系被撞破/身份被揭穿",
}

VISUAL = {
    "underdog": "破败底层 vs 金色力量/法相；俯拍大全景与大招特写对比",
    "revenge": "冷色压抑与血色回闪；归来时装/场景反差",
    "identity": "低调日常与高光身份的服装/构图反差",
    "system": "面板/数值可视化与技能特效；升级瞬间强光",
    "monster": "刀光、妖形、广角压迫；动作镜头与大全景交替",
    "forbidden": "近景/特写为主，冷暖对比；眼神、手指、距离感",
}


def _pick(text, signals, default):
    best, best_hits = default, 0
    for name, words in signals.items():
        hits = sum(text.count(w) for w in words)
        if hits > best_hits:
            best, best_hits = name, hits
    return best, best_hits


def analyze_submission(title, platform="红果漫剧", genre="", summary="",
                       script_text="", filename=""):
    text = " ".join([str(title or ""), str(genre or ""), str(summary or ""),
                     str(script_text or "")])
    formula_key, formula_hits = _pick(text, FORMULA_SIGNALS, "")
    if not formula_key:
        formula_key = formula_for_genre(genre)["key"]
    formula = {"key": formula_key, **FORMULAS[formula_key]}
    hook, hook_hits = _pick(text, HOOK_SIGNALS, "冲突爆发")
    cliff, cliff_hits = _pick(text, CLIFF_SIGNALS, "绝境反转")
    clauses = _clauses(summary or script_text or title)
    opening = clauses[0] if clauses else "—"
    progression = " → ".join(clauses[1:4]) if len(clauses) > 1 else formula["desc"]
    structure = {"opening": opening, "progression": progression,
                 "cadence": CADENCE.get(formula_key, "每集一个冲突点，结尾留钩子")}
    visual = VISUAL.get(formula_key, "强反差构图与近景/大全景对比")
    scene_rows = [{"event": c, "conflict": c, "result": c} for c in clauses[:8]]
    project = {"id": None, "title": title, "genre": genre,
               "logline": summary or " ".join(clauses[:2])}
    analysis = analyze_project(project, scene_rows, [])
    confidence = min(95, 40 + 10 * (formula_hits + hook_hits + cliff_hits))
    if not summary and not script_text:
        confidence = max(35, confidence - 25)
    why = ("采用「%s」配方；以「%s」开场，用「%s」断章；%s"
           % (formula["name"], hook, cliff, structure["cadence"]))
    suggested = {
        "title": title or "未命名案例", "platform": platform, "genre": genre,
        "summary": (summary or script_text)[:4000],
        "formula": formula_key, "hook_type": hook, "cliffhanger_type": cliff,
        "structure": structure, "visual": visual, "why": why,
        "score": analysis["overall"], "grade": analysis["grade"],
        "heat_note": "本地规则分析生成；播放量待平台后台/用户补充。",
        "verified": False,
        "source_note": "由输入文本按爆款公式规则分析；结论需以真实数据复核。",
        "analysis_meta": {"confidence": confidence,
                          "signals": {"formula_hits": formula_hits,
                                      "hook_hits": hook_hits,
                                      "cliffhanger_hits": cliff_hits},
                          "dimensions": analysis["dimensions"],
                          "suggestions": analysis["suggestions"]},
    }
    return {"formula": formula, "hook_type": hook, "cliffhanger_type": cliff,
            "structure": structure, "visual": visual, "why": why,
            "confidence": confidence, "analysis": analysis,
            "signals": suggested["analysis_meta"]["signals"],
            "suggested_case": suggested,
            "note": "规则分析，不代表真实播放量；保存后可继续人工修订。"}


HOOK_WORDS = ("真相", "命案", "失忆", "复仇", "追杀", "背叛", "秘密", "失踪",
              "重生", "退婚", "逐出", "死", "妖", "系统", "觉醒", "招惹")
CONFLICT_WORDS = ("冲突", "对抗", "拒绝", "威胁", "追杀", "命案", "背叛", "决裂",
                  "争夺", "羞辱", "打脸", "反杀", "围攻", "封印", "逼")
PAYOFF_WORDS = ("逆袭", "复仇", "觉醒", "打脸", "升级", "真相", "身份", "反转",
                "守护", "救赎", "翻盘", "镇妖")
CLIFF_WORDS = ("真相", "身份", "出现", "死", "逃", "封印", "觉醒", "背叛", "决裂", "妖王")


def _clauses(text):
    return [p.strip("。 ") for p in str(text or "").replace("；", "，").split("，") if p.strip("。 ")]


def _score_hook(logline):
    clauses = _clauses(logline)
    first = clauses[0] if clauses else ""
    score = 35
    if first:
        score += 15
    if any(w in first for w in HOOK_WORDS):
        score += 25
    if len(first) <= 24:
        score += 15
    if "？" in str(logline) or "！" in str(logline):
        score += 10
    return min(100, score)


def _score_conflict(logline, scenes):
    text = str(logline or "") + " " + " ".join(
        str(sc.get("conflict") or "") + str(sc.get("event") or "") for sc in (scenes or []))
    hits = sum(text.count(w) for w in CONFLICT_WORDS)
    score = 35 + min(45, hits * 8)
    if len(scenes or []) >= 3:
        score += 10
    if len(scenes or []) >= 6:
        score += 10
    return min(100, score)


def _score_cliffhanger(scenes):
    if not scenes:
        return 45
    last = scenes[-1]
    tail = str(last.get("result") or "") + str(last.get("conflict") or "")
    score = 50
    if any(w in tail for w in CLIFF_WORDS):
        score += 25
    if len(scenes) >= 2:
        score += 10
    return min(100, score)


def _score_payoff(genre, logline):
    text = str(genre or "") + " " + str(logline or "")
    hits = sum(text.count(w) for w in PAYOFF_WORDS)
    score = 40 + min(40, hits * 8)
    if formula_for_genre(genre)["key"] in ("underdog", "system", "revenge"):
        score += 10
    return min(100, score)


def _score_title(title, genre):
    t = str(title or "")
    score = 40
    if 2 <= len(t) <= 10:
        score += 20
    if any(w in t for w in ("神", "妖", "骨", "少年", "镇", "横刀", "荒")):
        score += 15
    if any(w in str(genre or "") for w in ("玄幻", "逆袭", "悬疑", "言情")):
        score += 10
    if any(c in t for c in ("：", "·", "！", "？")):
        score += 5
    return min(100, score)


def _score_spectacle(shots):
    if not shots:
        return 50
    score = 50
    if len(shots) >= 30:
        score += 15
    if len(shots) >= 100:
        score += 15
    sizes = {sh.get("size") for sh in shots}
    if len(sizes) >= 3:
        score += 10
    if any(sh.get("move") for sh in shots):
        score += 5
    return min(100, score)


def analyze_project(project, scenes=None, shots=None):
    title = project.get("title")
    genre = project.get("genre")
    logline = project.get("logline")
    dims = [
        {"key": "hook", "label": "前 3 秒钩子", "score": _score_hook(logline),
         "suggestion": "第一句直接给冲突、结果或身份反差；删掉背景铺垫。"},
        {"key": "conflict", "label": "冲突密度", "score": _score_conflict(logline, scenes),
         "suggestion": "每集至少 2 次对抗升级，避免连续解释设定。"},
        {"key": "cliffhanger", "label": "断章强度", "score": _score_cliffhanger(scenes),
         "suggestion": "结尾用身份暴露/新敌登场/真相半揭，不要平收。"},
        {"key": "payoff", "label": "情绪回报", "score": _score_payoff(genre, logline),
         "suggestion": "每 2–3 集给一次明确爽点或情绪释放，让观众有追更理由。"},
        {"key": "title", "label": "标题/封面", "score": _score_title(title, genre),
         "suggestion": "标题控制在 2–10 字，含题材关键词与冲突意象。"},
        {"key": "spectacle", "label": "视觉奇观", "score": _score_spectacle(shots),
         "suggestion": "增加大全景/特写对比、动作镜头与力量/妖形奇观。"},
    ]
    weights = {"hook": .25, "conflict": .2, "cliffhanger": .2,
               "payoff": .15, "title": .1, "spectacle": .1}
    overall = round(sum(d["score"] * weights[d["key"]] for d in dims))
    grade = "S" if overall >= 85 else "A" if overall >= 75 else "B" if overall >= 60 else "C"
    formula = formula_for_genre(genre)
    gaps = [d for d in dims if d["score"] < 70]
    return {
        "project": {"id": project.get("id"), "title": title, "genre": genre},
        "overall": overall, "grade": grade, "dimensions": dims,
        "formula": formula,
        "hook_suggestion": "前 3 秒：%s" % ((_clauses(logline) or ["故事冲突"])[0][:28]),
        "suggestions": [d["suggestion"] for d in gaps] or ["保持当前结构，继续强化每集结尾钩子。"],
        "note": "评分为结构启发式，不代表真实播放量；上线后需用平台数据复核。",
    }
