"""契约校验规则引擎（切片 A）。

每条规则有稳定 rule_id，并配一个**变异样本**（film/fixtures/mutations/mut_*.json）：
复测脚本断言「规则的 rule_id 集合 == 变异样本集合」，杜绝「有规则无测试」（杜绝恒真断言）。
"""

from . import enums, geometry
from .enums import ContractError

# 规则注册表：rule_id → (规则名, PRD 依据, 验收口径原文/摘要)
RULES = {
    "R-CONTRACT-FIELDS": ("契约字段完整率", "M4.1-F01 / M4.2-F03 / M5.2-F01 / M5.2-F02",
                          "关键字段非空率 100%"),
    "R-ONE-MOVE": ("一镜一运动铁律", "M5.1-F02 / M4.2-F01", "多主运动镜头数 = 0"),
    "R-DOLLY-ZOOM": ("dolly / zoom 分支语义", "M5.1-F04 / M4.2-F02", "三类分支描述模板覆盖率 100%"),
    "R-FILL-KEY": ("fill ≤ key 50%", "M5.3-F02", "违规镜次提交数 = 0"),
    "R-FACE-PATTERN": ("人脸布光图案四选一", "M5.3-F03", "人物镜图案字段完整率 100%"),
    "R-CCT-CLOSED": ("色温档封闭集合", "M5.3-F05", "色温字段完整率 100%"),
    "R-VOLUMETRIC-MEDIA": ("体积光介质声明", "M5.3-F06", "体积光镜 100% 带介质声明"),
    "R-DRIFT-lens": ("同场戏焦距档漂移", "M4.2-F03 / M5.6-F03", "漂移告警条目 100% 带镜号"),
    "R-DRIFT-clock": ("同场戏光位方位漂移 >30°", "M4.2-F04 / M5.6-F03", "漂移告警条目 100% 带镜号"),
    "R-DRIFT-cct": ("同场戏色温漂移 >200K", "M4.2-F04 / M5.6-F03", "漂移告警条目 100% 带镜号"),
    "R-SAFEFRAME": ("三画幅可裁切预演（含 9:16 关键信息出框 = 0）", "M4.4-F02 / M4.7-F02 / NFR-09 / EL-02",
                    "100% 镜头通过三画幅可裁切预演；9:16 关键信息出框镜数 = 0"),
    "R-SAFETY-BASIS": ("安全区口径唯一（择一并全片统一）", "M4.7-F01 / B-14 / B-16", "口径全片一致"),
    "R-LIGHT-CONTRACT": ("三点光登记（人物镜）", "M5.3-F01", "人物镜三点光登记率 100%"),
    "R-DOMAIN-BOUNDS": ("契约域值合法（构图几何）", "M4.1-F01 / M5.6-F05 / E-17",
                        "生成前预检聚合：因输入问题导致的付费失败 < 1%"),
}

# 无变异样本的规则必须给出理由（复测脚本断言：每条规则要么有 mut_*.json，要么在此登记豁免）
MUTATION_EXEMPTIONS = {
    "R-CONTRACT-FIELDS": "字段完整率由解析器保证：PRD 表缺列即解析异常（属于解析层 fail-closed，"
                         "构造阶段已覆盖；故以 R-DOMAIN-BOUNDS 的域值变异代替）",
}

# 项目自定阈值（无官方统一值 → 必须写入 QC 报告，不得冒充官方硬阈值）
DECLARED_THRESHOLDS = {
    "clock_drift_deg": {
        "value": 30.0,
        "source": "项目自定（依据：M4.2-F04 要求告警但未给数值；B-88 类「无官方统一值」）",
    },
    "cct_drift_k": {
        "value": 200.0,
        "source": "项目自定（依据：M4.2-F04 要求告警但未给数值）",
    },
    "aspect_ratio_tolerance": {
        "value": geometry.ASPECT_TOLERANCE,
        "source": "项目自定（裁切窗比例容差）",
    },
    "subject_containment": {
        "value": 1.0,
        "source": "项目自定（M4.7-F02「9:16 关键信息出框镜数=0」的机械口径：主体包围盒越界像素必须为 0）",
    },
    "safety_action_frac_smpte": {
        "value": enums.SMPTE_ACTION_SAFE,
        "source": "B-14（SMPTE ST 2046-1）官档数值",
    },
    "safety_title_frac_smpte": {
        "value": enums.SMPTE_TITLE_SAFE,
        "source": "B-14（SMPTE ST 2046-1）官档数值",
    },
    "graphics_inset": {
        "value": enums.GRAPHICS_INSET,
        "source": "B-16（EBU R95）官档数值；90 号第九章将「安全区百分比」列为未取到原文项，"
                  "故本项按项目声明使用并写入 QC 报告",
    },
}


def _check(rule_id, subject, measured, ok, detail=""):
    name, refs, criterion = RULES[rule_id]
    return {
        "rule_id": rule_id,
        "rule": name,
        "subject": subject,
        "criterion": criterion,
        "prd_refs": refs,
        "measured": measured,
        "result": "PASS" if ok else "FAIL",
        "detail": detail,
    }


def check_contract_fields(shot):
    """M4.1-F01 / M4.2-F03 / M5.2-F01 / M5.2-F02：关键字段完整率 100%。"""
    missing = []
    if not shot.size:
        missing.append("size")
    if not shot.angle:
        missing.append("angle")
    if not shot.move:
        missing.append("move")
    if not shot.speed:
        missing.append("speed")
    if not shot.lens_mm:
        missing.append("lens_mm")
    if not shot.dof:
        missing.append("dof")
    if not shot.key_cct:
        missing.append("key_cct")
    if shot.duration_sec <= 0:
        missing.append("duration_sec")
    ok = not missing
    return _check("R-CONTRACT-FIELDS", "S%02d" % shot.no,
                  "缺失字段 %d 项%s" % (len(missing), ("：" + ",".join(missing)) if missing else ""),
                  ok, "关键字段：size/angle/move/speed/lens_mm/dof/key_cct/duration_sec")


def check_one_move(shot):
    """M5.1-F02：单镜只允许一个主运动（推/拉/摇/移/跟/升降/环绕/手持/固定 择一）。

    次级机位运动（move_secondary）必须为 none；次级运动仅限**主体自身动作**（subject_move）。
    """
    bad = []
    if shot.move_secondary != "none":
        bad.append("次级机位运动=%s" % shot.move_secondary)
    if shot.subject_move in set(enums.MOVES):
        bad.append("次级运动写了机位运动=%s" % shot.subject_move)
    ok = not bad
    return _check("R-ONE-MOVE", "S%02d" % shot.no,
                  "主运动=%s / 次级机位=%s / 次级主体=%s"
                  % (shot.move, shot.move_secondary, shot.subject_move),
                  ok, ("检出多主运动：" + "；".join(bad)) if bad else "单主运动")


def check_dolly_zoom(shot):
    """M5.1-F04 / M4.2-F02：dolly 与 zoom 不得混指。"""
    prompt_hint = {
        "推": "dolly_in", "拉": "dolly_out", "zoom_in": "zoom_in", "zoom_out": "zoom_out",
    }.get(shot.move, "other")
    # zoom 分支必须使用 zoom_* 词汇；dolly 分支必须使用 dolly 语义（不得写成 zoom）
    ok = True
    detail = "分支=%s" % prompt_hint
    if shot.move in ("推", "拉") and shot.light_note.lower().find("zoom") >= 0:
        ok = False
    if shot.move in ("zoom_in", "zoom_out") and shot.light_note.lower().find("dolly") >= 0:
        ok = False
    return _check("R-DOLLY-ZOOM", "S%02d" % shot.no, prompt_hint, ok, detail)


def check_fill_key(shot):
    """M5.3-F02：fill 强度 ≤ key 的 50%（生成前预检拦截）。"""
    ratio = shot.fill_ratio / shot.key_ratio if shot.key_ratio > 0 else 0.0
    ok = ratio <= 0.5 + 1e-9
    return _check("R-FILL-KEY", "S%02d" % shot.no,
                  "fill/key = %.2f（fill=%.2f, key=%.2f）" % (ratio, shot.fill_ratio, shot.key_ratio),
                  ok, "阈值：fill ≤ key × 0.5")


def check_face_pattern(shot):
    """M5.3-F03：人物镜必须声明四选一图案；非人物镜必须为 none。"""
    if shot.has_person:
        ok = shot.face_pattern in ("rembrandt", "loop", "butterfly", "split")
        measured = shot.face_pattern
    else:
        ok = True
        measured = "%s（非人物镜，免检）" % shot.face_pattern
    return _check("R-FACE-PATTERN", "S%02d" % shot.no, measured, ok,
                  "人物镜（%s）必须四选一" % shot.size)


def check_cct_closed(shot):
    """M5.3-F05：色温必须落在封闭档内。

    注意：契约构造时应已拦截；此处仍做**独立判定**，因为变异测试可能绕过构造层
    （直接 setattr 注入非法值），规则必须自己发现（不能依赖构造期校验）。
    """
    ok = shot.key_cct in enums.CCT and shot.fill_cct in enums.CCT
    return _check("R-CCT-CLOSED", "S%02d" % shot.no,
                  "key=%s / fill=%s" % (shot.key_cct, shot.fill_cct), ok,
                  "封闭集合：%s" % "/".join("%dK" % k for k in enums.CCT))


def check_volumetric_media(shot):
    """M5.3-F06：体积光必须声明介质。"""
    if not shot.volumetric_active:
        return _check("R-VOLUMETRIC-MEDIA", "S%02d" % shot.no, "未声明体积光（免检）", True, "")
    ok = shot.volumetric_media != "none"
    return _check("R-VOLUMETRIC-MEDIA", "S%02d" % shot.no, shot.volumetric_media, ok,
                  "允许介质：%s" % "/".join(enums.VOLUMETRIC_MEDIA))


def check_domain_bounds(shot, gate_w=1920, gate_h=1080):
    """构图几何域值合法（防止 fixture 写出不可能几何 → 生成前预检必须拦住）。"""
    problems = []
    if not (0.0 <= shot.subject_x <= 1.0):
        problems.append("subject_x=%.4f 越出 [0,1]" % shot.subject_x)
    if not (0.0 <= shot.subject_y <= 1.0):
        problems.append("subject_y=%.4f 越出 [0,1]" % shot.subject_y)
    if shot.subject_scale <= 0.0:
        problems.append("subject_scale=%.4f 必须 > 0" % shot.subject_scale)
    if shot.subject_scale > 1.0:
        problems.append("subject_scale=%.4f 越出 (0,1]" % shot.subject_scale)
    ok = not problems
    return _check("R-DOMAIN-BOUNDS", "S%02d" % shot.no,
                  "subject_x=%.4f / subject_y=%.4f / subject_scale=%.4f"
                  % (shot.subject_x, shot.subject_y, shot.subject_scale),
                  ok, "；".join(problems) if problems else "域值合法")


def check_light_contract(shot):
    """M5.3-F01：人物镜三点光（key/fill/back 方位）登记完整。"""
    if not shot.has_person:
        return _check("R-LIGHT-CONTRACT", "S%02d" % shot.no, "非人物镜（免检）", True, "")
    missing = [n for n, v in (("key", shot.key_clock), ("fill", shot.fill_clock),
                              ("back", shot.back_clock)) if v == "none"]
    ok = not missing
    return _check("R-LIGHT-CONTRACT", "S%02d" % shot.no,
                  "缺失 %d 项%s" % (len(missing), ("：" + ",".join(missing)) if missing else ""),
                  ok, "人物镜三点光登记率 100%")


def check_safety_basis(basis, crops=None):
    """M4.7-F01：口径必须显式声明且全片唯一。"""
    try:
        info = geometry.resolve_basis(basis)
        ok = True
        measured = "%s（action=%.4f, title=%.4f, graphics_inset=%.3f）" % (
            info["basis"], info["action_frac"], info["title_frac"], info["graphics_inset"])
        detail = "来源：%s；图形安全区来源：%s" % (info["source"], info["graphics_source"])
    except geometry.SafetyBasisError as exc:
        ok = False
        measured = str(exc)
        detail = "允许：%s" % "/".join(enums.SAFETY_BASES)
    return _check("R-SAFETY-BASIS", "全片", measured, ok, detail)


def check_safeframe(shot, crops, bounds, critical, basis_info, min_containment=1.0):
    """M4.4-F02 / M4.7-F02 / EL-02：三画幅可裁切预演 + 9:16 关键信息不出框 + 关键信息落在 action safe。

    口径（项目自定，写入 QC 报告）：
    1. **9:16 硬性项**：主体包围盒在 9:16 窗内越界像素必须为 0，且包含率达到 min_containment
       （M4.7-F02「9:16 关键信息出框镜数 = 0」）；
    2. **三窗可裁切预演**：主体水平范围必须在 239/169/916 三窗内（竖向被裁属正常取景）；
    3. **action safe 硬性项**：关键信息区（面部/手部）必须落在三窗各自的 action safe 内
       （NFR-09 + D1 缓解措施 1：所有关键表演与叙事信息收在安全区内）。
    """
    per = {}
    safe_bad = []
    for key, crop in sorted(crops.items()):
        ov = geometry.overflow(crop, bounds)
        total = sum(ov.values())
        a = geometry.safe_rect(crop, basis_info["action_frac"])
        h_ov = geometry.overflow({"x0": crop["x0"], "x1": crop["x0"] + crop["w"],
                                  "y0": crop["y0"], "y1": crop["y0"] + crop["h"]}, bounds)
        critical_ov = geometry.overflow(a, critical)
        if sum(critical_ov.values()) > 0:
            safe_bad.append(key)
        per[key] = {
            "window": {"x0": crop["x0"], "y0": crop["y0"], "w": crop["w"], "h": crop["h"]},
            "action_safe": a,
            "overflow_px": ov,
            "overflow_total": total,
            "horizontal_overflow": h_ov["left"] + h_ov["right"],
            "critical_overflow_px": critical_ov,
            "critical_in_action_safe": sum(critical_ov.values()) == 0,
            "containment": round(geometry.intersection_ratio(crop, bounds), 6),
            "fit_916": (key != "916") or total == 0,
        }
    c916 = per["916"]["containment"]
    o916 = per["916"]["overflow_total"]
    h_worst = max(v["horizontal_overflow"] for v in per.values())
    ok = (o916 == 0 and c916 >= min_containment - 1e-9 and h_worst == 0 and not safe_bad)
    detail = ("9:16 越界=%d、水平越界 max=%d、关键信息越出 action safe 的画幅=%s"
              % (o916, h_worst, safe_bad or "无"))
    return _check("R-SAFEFRAME", "S%02d" % shot.no,
                  "9:16 越界像素=%d；9:16 包含率=%.4f；%s" % (o916, c916, detail), ok,
                  "判据：9:16 出框=0（M4.7-F02）+ 三窗水平可裁切 + 关键信息落 action safe（NFR-09）"), per


def check_cross_shot_drift(shots, thresholds=None):
    """M4.2-F03/F04 / M5.6-F03：同场戏四项漂移（焦距档 / 光位方位 / 色温 / 景深意图）。"""
    th = thresholds or {}
    clock_max = float(th.get("clock_drift_deg", DECLARED_THRESHOLDS["clock_drift_deg"]["value"]))
    cct_max = float(th.get("cct_drift_k", DECLARED_THRESHOLDS["cct_drift_k"]["value"]))
    scenes = {}
    for s in sorted(shots, key=lambda x: x.no):
        scenes.setdefault(s.scene, []).append(s)

    findings = []
    for scene, group in sorted(scenes.items()):
        if len(group) < 2:
            continue
        lenses = sorted({s.lens_mm for s in group})
        dofs = sorted({s.dof for s in group})
        ccts = sorted({s.key_cct for s in group if isinstance(s.key_cct, int)})
        if len(lenses) > 1:
            findings.append({"kind": "lens", "scene": scene, "rule_id": "R-DRIFT-lens",
                             "shots": [s.no for s in group], "values": lenses,
                             "message": "同场戏焦距档漂移：%s mm" % "/".join(str(v) for v in lenses)})
        if len(dofs) > 1:
            findings.append({"kind": "dof", "scene": scene, "rule_id": "R-DRIFT-lens",
                             "shots": [s.no for s in group], "values": dofs,
                             "message": "同场戏景深意图漂移：%s" % "/".join(dofs)})
        if ccts and (max(ccts) - min(ccts)) > cct_max:
            findings.append({"kind": "cct", "scene": scene, "rule_id": "R-DRIFT-cct",
                             "shots": [s.no for s in group], "values": ccts,
                             "message": "同场戏色温漂移 %dK > 阈值 %.0fK" % (max(ccts) - min(ccts), cct_max)})
        clocks = [s.key_clock for s in group if s.key_clock != "none"]
        if len(clocks) > 1:
            worst = 0.0
            pair = None
            for i in range(len(clocks)):
                for j in range(i + 1, len(clocks)):
                    d = enums.clock_angular_delta(clocks[i], clocks[j])
                    if d > worst:
                        worst, pair = d, (clocks[i], clocks[j])
            if worst > clock_max:
                findings.append({"kind": "clock", "scene": scene, "rule_id": "R-DRIFT-clock",
                                 "shots": [s.no for s in group],
                                 "values": [pair[0], pair[1]],
                                 "message": "同场戏光位方位漂移 %.0f° > 阈值 %.0f°（%s vs %s）"
                                            % (worst, clock_max, pair[0], pair[1])})

    seen = sorted({f["rule_id"] for f in findings})
    checks = []
    for rule_id in ("R-DRIFT-lens", "R-DRIFT-clock", "R-DRIFT-cct"):
        hits = [f for f in findings if f["rule_id"] == rule_id]
        # 漂移类规则：命中即告警（告警本身是**预期行为**，不判 FAIL）；
        # FAIL 只发生在「命中却无法定位镜号/场次」时（M4.2-F04：每条告警带镜号）。
        locatable = all(f.get("shots") and f.get("scene") for f in hits)
        checks.append(_check(rule_id, "全片",
                             "命中 %d 条%s" % (len(hits), "（均可定位）" if locatable else "（存在不可定位条目）"),
                             locatable, "漂移检测为**告警**而非否决（M4.5-F02 同纪律）"))
    return checks, findings, seen


def evaluate(shots, basis, crops=None, bounds_by_shot=None, critical_by_shot=None,
             thresholds=None, gate=None):
    """对全部镜头跑规则引擎，返回 (checks, findings, safeframe_detail)。

    bounds_by_shot / critical_by_shot：{镜号: 矩形}；缺省时按门尺寸与契约几何自行推导。
    """
    bounds_by_shot = bounds_by_shot or {}
    critical_by_shot = critical_by_shot or {}
    gate_w, gate_h = (gate or (1920, 1080))
    if crops is None:
        crops = geometry.derive_crops(gate_w, gate_h)
    checks = []
    for s in sorted(shots, key=lambda x: x.no):
        checks.append(check_contract_fields(s))
        checks.append(check_one_move(s))
        checks.append(check_dolly_zoom(s))
        checks.append(check_fill_key(s))
        checks.append(check_face_pattern(s))
        checks.append(check_cct_closed(s))
        checks.append(check_volumetric_media(s))
        checks.append(check_light_contract(s))
        checks.append(check_domain_bounds(s))
    checks.append(check_safety_basis(basis, crops))
    drift_checks, findings, _ = check_cross_shot_drift(shots, thresholds=thresholds)
    checks.extend(drift_checks)

    try:
        basis_info = geometry.resolve_basis(basis)
    except geometry.SafetyBasisError:
        basis_info = None
    safeframe_detail = {}
    for s in sorted(shots, key=lambda x: x.no):
        if s.no not in bounds_by_shot:
            full, crit, _meta = geometry.critical_from_params(
                s.subject_x, s.subject_scale, getattr(s, "subject_y", 0.66),
                gate_w=gate_w, gate_h=gate_h)
        else:
            full = bounds_by_shot[s.no]
            crit = critical_by_shot.get(s.no)
            if crit is None:
                _f, crit, _m = geometry.critical_from_params(
                    s.subject_x, s.subject_scale, getattr(s, "subject_y", 0.66),
                    gate_w=gate_w, gate_h=gate_h)
        if basis_info is None:
            continue
        chk, per = check_safeframe(s, crops, full, crit, basis_info)
        checks.append(chk)
        safeframe_detail[s.no] = {"bounds": full, "critical_region": crit, "per_aspect": per}
    return checks, findings, safeframe_detail


def failed(checks):
    return [c for c in checks if c["result"] != "PASS"]
