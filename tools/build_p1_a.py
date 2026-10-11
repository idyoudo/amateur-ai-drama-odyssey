#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-A 切片生成器（**只生成，不复测**）。

用法：
    python3 tools/build_p1_a.py --out out/p1a
    python3 tools/build_p1_a.py --out out/p1a --reuse-render   # 复用已渲染的代理帧（迭代加速）

生成产物（全部 PROXY，依据 EL-16）：
    contract.json / prompts.json / prompt_pack.sha256 / photo_snapshot.json
    crops.json / safeframe.json / drift.json / precheck.json
    gate_receipt.json / declared_thresholds.json / not_verified.json
    proxy/gate_S0X.png / proxy/S0X_{239,169,916}.png

纪律：复测在 tools/verify_p1_a.py，只读本脚本产物，不 import 本脚本或 film 包的运行期状态。
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from film import anchor, enums, gates, geometry, prompts, render, snapshot, validators  # noqa: E402
from film.contract import (CONTRACT_VERSION, MAP_VERSION, apply_geometry,  # noqa: E402
                           parse_prd_shot_table)

PROXY = render.PROXY_NOTICE

NOT_VERIFIED = [
    "真实生成模型对提示词契约的遵从度（本切片不调用任何付费模型）",
    "ACES IDT 与色卡往返（96 号 G-02/G-03）",
    "ProRes 母版编码与 TC 嵌入（NFR-13；无 ffmpeg）",
    "5.1 下混兼容（96 号 G-04）",
    "口型同步与音画偏移（96 号 G-05；NFR-07）",
    "EDL/AAF 回批（96 号 G-06）",
    "−23 LUFS 归档母版（本切片的代理音频来自既有 demo/ 产物，不是本切片产出）",
    "PP1 退出标准的完整达成——本切片只推进 M4/M5 契约层",
]


def _read_prd(fixture):
    rel = fixture["contract_source"]["path"]
    path = os.path.join(ROOT, rel)
    with open(path, encoding="utf-8") as fh:
        return path, fh.read()


def _write_json(path, obj, stable=True):
    text = snapshot.dumps_stable(obj) if stable else json.dumps(obj, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="AADO P1-A 切片生成器（只生成，不复测）")
    ap.add_argument("--out", default="out/p1a")
    ap.add_argument("--fixture", default="film/fixtures/pilot_ep01.json")
    ap.add_argument("--reuse-render", action="store_true",
                    help="复用已存在的 proxy 图（仅在契约与几何未变时安全）")
    ap.add_argument("--timestamp", default=os.environ.get("AADO_TIMESTAMP", ""),
                    help="门禁时间戳（留空表示尚未人工终审；留空可保证产物字节级可复现）")
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, args.out)
    proxy_dir = os.path.join(out_dir, "proxy")
    os.makedirs(proxy_dir, exist_ok=True)

    with open(os.path.join(ROOT, args.fixture), encoding="utf-8") as fh:
        fixture = json.load(fh)

    prd_path, prd_text = _read_prd(fixture)
    shots = parse_prd_shot_table(prd_text)
    apply_geometry(shots, fixture["geometry"])
    gate_w, gate_h = fixture["gate"]["w"], fixture["gate"]["h"]
    basis = fixture["safety_basis"]

    crops = geometry.derive_crops(gate_w, gate_h)
    basis_info = geometry.resolve_basis(basis)

    # ---- 契约与提示词
    bounds, criticals = {}, {}
    for s in shots:
        full, crit, _meta = geometry.critical_from_params(
            s.subject_x, s.subject_scale, s.subject_y, gate_w=gate_w, gate_h=gate_h)
        bounds[s.no] = full
        criticals[s.no] = crit
    prompt_records = prompts.compile_all(shots)
    snapshot_doc = snapshot.snapshot_all(shots, prompt_records)

    # ---- 规则引擎
    checks, findings, safeframe_detail = validators.evaluate(
        shots, basis, crops=crops, bounds_by_shot=bounds, critical_by_shot=criticals,
        gate=(gate_w, gate_h))
    failed = validators.failed(checks)
    drift = snapshot.drift_report(shots, findings)

    # ---- 代理画面与三画幅裁切预演
    rendered = []
    for s in sorted(shots, key=lambda x: x.no):
        tag = "S%02d" % s.no
        gate_png = os.path.join(proxy_dir, "gate_%s.png" % tag)
        if args.reuse_render and os.path.exists(gate_png) and os.path.getsize(gate_png) > 0:
            continue
        img = render.render_gate(s, gate_w, gate_h)
        img.save(gate_png)
        previews = render.make_previews(img, crops)
        for key, im in sorted(previews.items()):
            b = bounds[s.no]
            # 在预演图上标出主体水平中心，便于人工复核是否落在竖屏窗内
            im.save(os.path.join(proxy_dir, "%s_%s.png" % (tag, key)))
        rendered.append(tag)

    # ---- 产物写出
    contract_doc = {
        "slice": "P1-A",
        "contract_version": CONTRACT_VERSION,
        "mapping_version": MAP_VERSION,
        "proxy_notice": PROXY,
        "source": {"prd": fixture["contract_source"]["path"],
                   "table": fixture["contract_source"]["table"],
                   "gate": "%dx%d（16:9 open gate 唯一生成母版，EL-01）" % (gate_w, gate_h)},
        "shots": [s.as_dict() for s in sorted(shots, key=lambda x: x.no)],
    }
    h_contract = _write_json(os.path.join(out_dir, "contract.json"), contract_doc)

    # 契约字段必须**可反查 PRD 原文**（避免 fixture 与 PRD 表漂移的静默发生）
    raw_shots = parse_prd_shot_table(prd_text)
    raw_by_no = {s.no: s for s in raw_shots}
    source_rows = []
    for shot in sorted(shots, key=lambda x: x.no):
        raw = raw_by_no[shot.no]
        same = {k: (getattr(raw, k) == getattr(shot, k))
                for k in ("size", "lens_mm", "move", "key_cct", "duration_sec",
                          "dialogue", "reference", "physics_skeleton")}
        source_rows.append({
            "shot": "S%02d" % shot.no,
            "prd_derived": same,
            "prd_fields_match": all(same.values()),
            "provenance": shot.provenance,
        })
    h_source = _write_json(os.path.join(out_dir, "table_source.json"), {
        "prd": fixture["contract_source"]["path"],
        "table": fixture["contract_source"]["table"],
        "policy": "契约字段一律从 PRD 原文解析，禁止手抄；本文件逐镜证明「产物字段 == PRD 表字段」",
        "all_match": all(r["prd_fields_match"] for r in source_rows),
        "rows": source_rows,
    })
    h_prompts = _write_json(os.path.join(out_dir, "prompts.json"), prompt_records)
    h_snapshot = _write_json(os.path.join(out_dir, "photo_snapshot.json"), snapshot_doc)
    h_crops = _write_json(os.path.join(out_dir, "crops.json"), {
        "gate": {"w": gate_w, "h": gate_h},
        "safety_basis": basis_info,
        "crops": crops,
        "policy": "2.39 / 16:9 / 9:16 一律由 16:9 open gate **中心裁切**派生，禁止单画幅重复生成（EL-01/D1）",
    })
    h_safeframe = _write_json(os.path.join(out_dir, "safeframe.json"), {
        "proxy_notice": PROXY,
        "policy": "主体包围盒在 239/169/916 三窗内越界像素必须为 0（M4.7-F02）",
        "policy_detail": (
            "硬性判据 ①9:16 越界像素=0（M4.7-F02）；②关键信息区（面部/手部）落在三画幅 action safe 内"
            "（NFR-09 + EL-02）；③主体水平范围在三窗内（竖向被裁属正常电影取景，不作硬性判据）"),
        "shots": {("S%02d" % no): {
            "bounds": data["bounds"],
            "critical_region": data["critical_region"],
            "per_aspect": data["per_aspect"],
            "fit": all(v["overflow_total"] == 0 and v["critical_in_action_safe"]
                       and v["horizontal_overflow"] == 0 for v in data["per_aspect"].values()),
        } for no, data in sorted(safeframe_detail.items())},
    })
    h_drift = _write_json(os.path.join(out_dir, "drift.json"), drift)
    h_thresholds = _write_json(os.path.join(out_dir, "declared_thresholds.json"), {
        "proxy_notice": PROXY,
        "note": "项目自定阈值必须写入 QC 报告；未取到原文者不得冒充官方硬阈值（90 号第九章 / B-88）",
        "thresholds": validators.DECLARED_THRESHOLDS,
    })
    h_notverified = _write_json(os.path.join(out_dir, "not_verified.json"), {
        "proxy_notice": PROXY,
        "p1_exit_criteria_advanced": False,
        "p1_exit_criteria_note": "本切片推进 M4/M5 契约层；P1 退出标准（2.39 母版 + 24fps + −23 LUFS + TC）尚未达成",
        "not_verified": NOT_VERIFIED,
    })

    # ---- 锚点互核：用同一判据核对参考实现（demo）已声明的构图几何（只读，不改 demo）
    anchor_doc = anchor.crosscheck(basis, gate=(gate_w, gate_h))
    h_anchor = _write_json(os.path.join(out_dir, "anchor_crosscheck.json"), anchor_doc)

    # ---- 生成前预检聚合（M5.6-F05 / E-17）
    precheck = {
        "slice": "P1-A",
        "proxy_notice": PROXY,
        "rule_registry": sorted(validators.RULES),
        "mutation_coverage": {
            "rules_with_mutation": sorted(validators.RULES),  # 由 verify 逐条核对
            "exemptions": validators.MUTATION_EXEMPTIONS,
        },
        "checks": checks,
        "failed_checks": failed,
        "drift_findings": findings,
        "summary": {
            "total": len(checks),
            "pass": len(checks) - len(failed),
            "fail": len(failed),
            "result": "PASS" if not failed else "FAIL",
        },
        "gate": "pre_submit",
        "meaning": "本项是**生成前预检**：FAIL 表示该镜不得提交付费生成（M5.3-F02 / M4.7-F01 / EL-02）。",
    }
    h_precheck = _write_json(os.path.join(out_dir, "precheck.json"), precheck)

    # ---- 分镜门禁收据（字段契约层，不冒充人工署名）
    board_ok = not failed
    receipt = gates.make_receipt(
        node="board",
        decision="pending" if board_ok else "reject",
        reason_code="GATE-BOARD-AI-PROPOSE-PASS-CONTRACT-OK" if board_ok else "GATE-BOARD-PRECHECK-FAIL",
        checklist=gates.checklist([
            ("契约字段完整率", "100%", "100%" if not [c for c in failed if c["rule_id"] == "R-CONTRACT-FIELDS"] else "<100%"),
            ("多主运动镜数", 0, len([c for c in failed if c["rule_id"] == "R-ONE-MOVE"])),
            ("fill>key/2 违规镜数", 0, len([c for c in failed if c["rule_id"] == "R-FILL-KEY"])),
            ("9:16 出框镜数", 0, len([c for c in failed if c["rule_id"] == "R-SAFEFRAME"])),
            ("体积光无介质镜数", 0, len([c for c in failed if c["rule_id"] == "R-VOLUMETRIC-MEDIA"])),
        ]),
        ai_recommendation="pass" if board_ok else "reject",
        override_reason="",
        written_reason="" if not board_ok else "预检零失败：本收据用于验证门禁字段契约",
        approver=gates.PLACEHOLDER_APPROVER,
        role="（占位）导演 + 摄影",
        timestamp=args.timestamp,
        evidence=["out/p1a/precheck.json"],
    )
    receipt["validation"] = gates.validate_receipt(receipt)
    receipt["ai_overridden"] = True
    receipt["override_reason"] = ("存在 %d 项预检失败，人工尚未终审；"
                                  "本收据不作通过结论，approver 为占位符（D6：无署名即未通过）"
                                  % len(failed)) if failed else \
                                 "预检无失败项；仍须人工署名终审（approver 为占位符）"
    receipt["validation"] = gates.validate_receipt(receipt)
    h_receipt = _write_json(os.path.join(out_dir, "gate_receipt.json"), receipt)

    # ---- 提示词快照（字节级确定性对照）
    with open(os.path.join(out_dir, "prompt_pack.sha256"), "w", encoding="utf-8") as fh:
        for rec in prompt_records:
            fh.write("%s  S%02d\n" % (rec["sha256"], rec["no"]))
    pack_hash = hashlib.sha256("".join(r["sha256"] for r in prompt_records).encode("ascii")).hexdigest()

    print(json.dumps({
        "slice": "P1-A",
        "out": os.path.relpath(out_dir, ROOT),
        "shots": len(shots),
        "prompt_pack_sha256": pack_hash,
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "failed_rules": sorted({c["rule_id"] for c in failed}),
        "failed_subjects": sorted({c["subject"] for c in failed}),
        "drift_findings": len(findings),
        "anchor_non_compliant": anchor_doc["non_compliant_count"],
        "rendered": rendered,
        "artifacts": {
            "contract.json": h_contract,
            "prompts.json": h_prompts,
            "photo_snapshot.json": h_snapshot,
            "crops.json": h_crops,
            "safeframe.json": h_safeframe,
            "drift.json": h_drift,
            "precheck.json": h_precheck,
            "gate_receipt.json": h_receipt,
            "declared_thresholds.json": h_thresholds,
            "not_verified.json": h_notverified,
            "table_source.json": h_source,
            "anchor_crosscheck.json": h_anchor,
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
