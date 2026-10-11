"""锚点互核：用本切片的判据去核对**参考实现（demo）**已渲染/已声明的构图几何。

目的（为什么需要它）：
1. 证明规则**不是恒真** —— 用同一套判据去量一份**独立来源**的构图参数（demo/build_demo.py
   的 SHOTS 及其渲染产物），必须检出真实缺陷；
2. 证明修复方向正确 —— 本切片 fixture 声明的几何在同判据下全部通过。

⚠️ 纪律：
- 本模块**只读**，不修改 demo 任何文件、不重渲染 demo 产物（避免污染既有 24/24 证据链）；
- 参考实现是否符合本切片判据**不构成**对 demo/verify.py 结论的否定：两者判据不同
  （demo 的 24 项不含多画幅安全框，见 PRD/96 §8「覆盖不到」清单）；
- 本互核只用于**登记缺陷**，是否返修参考实现由显式决议决定（见 docs/plans/P1-待裁决清单.md）。
"""

from . import geometry

REFERENCE_GEOMETRY = [
    # demo/build_demo.py:57-66 的 SHOTS（subject_x / subject_scale），逐字对齐原值
    {"no": 1, "label": "EWS 24mm crane up", "subject_x": 0.50, "subject_scale": 0.16},
    {"no": 2, "label": "MS 35mm dolly in", "subject_x": 0.42, "subject_scale": 0.38},
    {"no": 3, "label": "CU 85mm static", "subject_x": 0.58, "subject_scale": 0.72},
    {"no": 4, "label": "OTS 50mm handheld", "subject_x": 0.36, "subject_scale": 0.44},
    {"no": 5, "label": "MCU 85mm slow push", "subject_x": 0.54, "subject_scale": 0.55},
    {"no": 6, "label": "LS 35mm truck right", "subject_x": 0.46, "subject_scale": 0.30},
    {"no": 7, "label": "ECU 135mm static", "subject_x": 0.62, "subject_scale": 0.88},
    {"no": 8, "label": "WS 24mm crane down", "subject_x": 0.50, "subject_scale": 0.22},
]

REFERENCE_SOURCE = {
    "path": "demo/build_demo.py",
    "lines": "57-66（SHOTS 定义）；82-108（open_gate_frame 构图语义）",
    "rendered_artifacts": "demo/out/animatic_{239,169,916}.webp",
    "note": "参考实现是「规范合规模拟母版」代理样片；其 verify.py 的 24 项机检不含多画幅安全框判据。",
}


def crosscheck(basis, gate=(1920, 1080), reference=None):
    """对参考实现的构图几何跑本切片判据，返回逐镜结论与缺陷清单。"""
    gate_w, gate_h = gate
    basis_info = geometry.resolve_basis(basis)
    crops = geometry.derive_crops(gate_w, gate_h)
    rows = []
    defects = []
    for item in (reference or REFERENCE_GEOMETRY):
        full, crit, _meta = geometry.critical_from_params(
            item["subject_x"], item["subject_scale"], item.get("subject_y", 0.66),
            gate_w=gate_w, gate_h=gate_h)
        per = {}
        reasons = []
        for key, crop in sorted(crops.items()):
            a = geometry.safe_rect(crop, basis_info["action_frac"])
            ov_full = geometry.overflow(crop, full)
            ov_crit = geometry.overflow(a, crit)
            h_ov = geometry.overflow(
                {"x0": crop["x0"], "x1": crop["x0"] + crop["w"],
                 "y0": crop["y0"], "y1": crop["y0"] + crop["h"]}, full)
            per[key] = {
                "overflow_total": sum(ov_full.values()),
                "overflow_px": ov_full,
                "horizontal_overflow": h_ov["left"] + h_ov["right"],
                "critical_overflow_px": ov_crit,
                "critical_in_action_safe": sum(ov_crit.values()) == 0,
            }
            if key == "916" and sum(ov_full.values()) > 0:
                reasons.append("9:16 主体出框 %d px" % sum(ov_full.values()))
            if h_ov["left"] + h_ov["right"] > 0:
                reasons.append("%s 主体水平出框 %d px" % (key, h_ov["left"] + h_ov["right"]))
            if sum(ov_crit.values()) > 0:
                reasons.append("%s 关键信息越出 action safe %d px" % (key, sum(ov_crit.values())))
        row = {
            "shot": "S%02d" % item["no"],
            "label": item.get("label", ""),
            "subject_x": item["subject_x"],
            "subject_y": item.get("subject_y", 0.66),
            "subject_scale": item["subject_scale"],
            "bounds": full,
            "critical_region": crit,
            "per_aspect": per,
            "compliant": not reasons,
            "reasons": reasons,
        }
        rows.append(row)
        if reasons:
            defects.append({"shot": row["shot"], "reasons": reasons,
                            "bounds": full, "critical_region": crit})
    return {
        "source": REFERENCE_SOURCE,
        "basis": basis_info,
        "judgement": "本互核使用与 P1-A 切片同一套判据（9:16 出框=0 + 三窗水平可裁切 + 关键信息落 action safe）",
        "disclaimer": (
            "参考实现（demo/）的 24/24 机检结论**不受本互核否定**：其判据集合不含多画幅安全框。"
            "本互核只证明「该缺陷类真实存在」以及「本切片判据有牙」，不构成对 demo 的返修要求。"),
        "shot_count": len(rows),
        "non_compliant_count": len(defects),
        "rows": rows,
        "defects": defects,
    }
