#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1-A 切片**独立复测**（fail-closed，只读磁盘产物）。

用法：
    python3 tools/verify_p1_a.py --out out/p1a
    python3 tools/verify_p1_a.py --out out/p1a --report docs/spec/P1-A-验证记录.md
    python3 tools/verify_p1_a.py --out out/p1a --determinism    # 追加确定性双跑（较慢）

纪律（依据 docs/agent-prd-method.md）：
- 复测**晚于**被检对象产生；先校验产物存在且非空，缺件即 FAIL；
- 独立测量：像素几何从 PNG **重新解码**测量，不复用生成器的中间变量；
- 不 import tools/build_p1_a.py；变异样本必须**全部被判违规**（漏放一条即 FAIL）；
- 退出码：0 = 全通过；1 = 存在 FAIL；2 = 环境或产物缺失。
"""

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from film import enums, gates, geometry, render, validators  # noqa: E402
from film.contract import (ContractError, ShotContract, apply_geometry,  # noqa: E402
                           parse_prd_shot_table)

REQUIRED_ARTIFACTS = [
    "contract.json", "prompts.json", "photo_snapshot.json", "crops.json",
    "safeframe.json", "drift.json", "precheck.json", "gate_receipt.json",
    "declared_thresholds.json", "not_verified.json", "anchor_crosscheck.json",
    "table_source.json", "prompt_pack.sha256",
]

# 与生成器一致的几何公式（**独立实现**：用于交叉核对，不 import 生成器状态）
SUBJECT_WIDTH_SCALE = 3.0
HEAD_RADIUS_FRAC = 0.40
HEAD_DY = -0.36
BODY_DY0, BODY_DY1 = -0.14, 0.60
BODY_HALF_FRAC = 0.36
# 关键信息区（头顶至颈部）偏移比例——与 film/geometry.py 同一口径，此处独立复写
CRIT_TOP_FRAC = 0.10
CRIT_BOTTOM_FRAC = 0.05
ASPECTS = {"239": 2.39, "169": 16.0 / 9.0, "916": 9.0 / 16.0}


class Report(object):
    def __init__(self):
        self.items = []

    def add(self, item, value, rule, ok, note=""):
        self.items.append({"item": item, "value": value, "rule": rule,
                           "pass": bool(ok), "note": note})
        return ok

    @property
    def failed(self):
        return [i for i in self.items if not i["pass"]]

    def summary(self):
        total = len(self.items)
        passed = total - len(self.failed)
        return {
            "total": total, "pass": passed, "fail": len(self.failed),
            "pass_rate": round(100.0 * passed / total, 2) if total else 0.0,
            "result": "PASS" if not self.failed else "FAIL",
        }


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def measure_subject_from_png(png_path, gate_w=1920, gate_h=1080):
    """从代理 PNG **独立测量**主体暗部包围盒（亮度假掩膜）。

    坐标系：代理图可能被缩放 → 归一到 gate 像素坐标。
    """
    img = Image.open(png_path).convert("RGB")
    arr = np.asarray(img, np.float32)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    dark = luma < render.LUMA_SUBJECT_MAX
    bright = luma > render.LUMA_BG_MIN
    if not dark.any():
        return None
    ys, xs = np.nonzero(dark)
    h, w = luma.shape
    sx = float(gate_w) / w
    sy = float(gate_h) / h
    return {
        "x0": int(round(xs.min() * sx)), "x1": int(round((xs.max() + 1) * sx)),
        "y0": int(round(ys.min() * sy)), "y1": int(round((ys.max() + 1) * sy)),
        "dark_px": int(dark.sum()), "bright_px": int(bright.sum()),
        "img_size": [w, h],
    }


def compute_bounds(shot, gate_w, gate_h):
    """**复测侧独立实现**的构图几何（不 import 生成器）：返回 (整体包围盒, 关键信息区)。"""
    full_w = 0.10 * gate_w * shot.subject_scale * SUBJECT_WIDTH_SCALE
    full_h = 0.40 * gate_h * shot.subject_scale * SUBJECT_WIDTH_SCALE
    cx = shot.subject_x * gate_w
    cy = getattr(shot, "subject_y", 0.66) * gate_h
    half = full_w * HEAD_RADIUS_FRAC
    top = cy + full_h * HEAD_DY - full_h * HEAD_RADIUS_FRAC
    bottom = cy + full_h * BODY_DY1
    head_bottom = cy + full_h * HEAD_DY + full_h * HEAD_RADIUS_FRAC
    full = {"x0": int(round(cx - half)), "x1": int(round(cx + half)),
            "y0": int(round(max(0, top))), "y1": int(round(min(gate_h, bottom)))}
    crit = {"x0": full["x0"], "x1": full["x1"],
            "y0": int(round(max(0, top + full_h * CRIT_TOP_FRAC))),
            "y1": int(round(head_bottom + full_h * CRIT_BOTTOM_FRAC))}
    return full, crit


def rebuild_shots(fixture_path):
    """从 PRD 原文 + fixture 重新构建契约（复测侧独立路径）。"""
    with open(fixture_path, encoding="utf-8") as fh:
        fixture = json.load(fh)
    with open(os.path.join(ROOT, fixture["contract_source"]["path"]), encoding="utf-8") as fh:
        prd_text = fh.read()
    shots = parse_prd_shot_table(prd_text)
    apply_geometry(shots, fixture["geometry"])
    return fixture, shots


def run_mutations(mut_dir, base_shots, fixture, rep, crops):
    """变异测试：每条规则至少一个违例样本必须被判 FAIL。"""
    mut_files = sorted(f for f in os.listdir(mut_dir) if f.startswith("mut_") and f.endswith(".json"))
    if not mut_files:
        rep.add("变异样本存在", "0 个", "≥1 个 mut_*.json", False, "缺少变异样本目录内容")
        return
    rule_ids = set()
    for name in mut_files:
        mut = load_json(os.path.join(mut_dir, name))
        rule_id = mut["rule_id"]
        rule_ids.add(rule_id)
        shots = copy.deepcopy(base_shots)
        by_no = {s.no: s for s in shots}
        basis = fixture["safety_basis"]
        geometry_map = {g["no"]: dict(g) for g in fixture["geometry"]}

        construct_failed = False
        try:
            if mut["op"] == "contract":
                target = by_no[int(mut["base_shot"])]
                for key, val in mut["overrides"].items():
                    setattr(target, key, val)
            elif mut["op"] == "spec":
                target = by_no[int(mut["base_shot"])]
                kw = dict(target.provenance["constructor_kwargs"])
                kw.update(mut["overrides"])
                if "provenance" in kw:
                    kw.pop("provenance")
                ShotContract(**kw)
            elif mut["op"] == "geometry":
                for no_str, patch in mut["overrides"].items():
                    geometry_map[int(no_str)].update(patch)
                apply_geometry(shots, [geometry_map[k] for k in sorted(geometry_map)])
            elif mut["op"] == "meta":
                for key, val in mut["overrides"].items():
                    if key == "safety_basis":
                        basis = val
                    elif key == "geometry":
                        for no_key, patch in val.items():
                            geometry_map[int(no_key)].update(patch)
                        apply_geometry(shots, [geometry_map[k] for k in sorted(geometry_map)])
                    else:
                        raise ContractError("未知 meta 覆盖键：%s" % key)
            else:
                raise ContractError("未知变异 op：%s" % mut["op"])
        except ContractError as exc:
            construct_failed = True
            note = "构造期拒绝：%s" % exc

        if construct_failed:
            rep.add("变异 %s 被拒" % mut["mut_id"], "构造期 ContractError", "%s 必须 FAIL" % rule_id,
                    True, note)
            continue

        geo = {s.no: compute_bounds(s, fixture["gate"]["w"], fixture["gate"]["h"]) for s in shots}
        bounds = {k: v[0] for k, v in geo.items()}
        criticals = {k: v[1] for k, v in geo.items()}
        checks, findings, _ = validators.evaluate(shots, basis, crops=crops, bounds_by_shot=bounds,
                                                  critical_by_shot=criticals,
                                                  gate=(fixture["gate"]["w"], fixture["gate"]["h"]))
        failed_rules = {c["rule_id"] for c in validators.failed(checks)}
        # 漂移类规则以**告警条目**形式命中（M4.2-F04 明确要求告警而非否决）
        drift_rules = {f["rule_id"] for f in findings}
        hit = rule_id in failed_rules or rule_id in drift_rules
        detail = mut.get("note", "")
        if not hit:
            detail = "未命中目标规则；实际失败规则=%s，漂移告警=%s" % (sorted(failed_rules), sorted(drift_rules))
        rep.add("变异 %s 命中 %s" % (mut["mut_id"], rule_id),
                "failed=%s drift=%s" % (sorted(failed_rules), sorted(drift_rules)),
                "%s 必须被检出（FAIL 或漂移告警）" % rule_id, hit, detail)

    # 规则注册表 ↔ 变异样本覆盖配平
    registered = set(validators.RULES)
    exempt = set(validators.MUTATION_EXEMPTIONS)
    covered = rule_ids | exempt
    missing = sorted(registered - covered)
    extra = sorted(rule_ids - registered)
    rep.add("规则注册表 ↔ 变异样本配平",
            "规则 %d 条 / 变异 %d 条 / 豁免 %d 条" % (len(registered), len(rule_ids), len(exempt)),
            "每条规则要么有变异样本、要么登记豁免；变异不得指向未注册规则",
            not missing and not extra,
            ("缺样本：%s；越界样本：%s" % (missing, extra)) if (missing or extra) else "配平")


def main():
    ap = argparse.ArgumentParser(description="AADO P1-A 切片独立复测")
    ap.add_argument("--out", default="out/p1a")
    ap.add_argument("--fixture", default="film/fixtures/pilot_ep01.json")
    ap.add_argument("--mutations", default="film/fixtures/mutations")
    ap.add_argument("--report", default="")
    ap.add_argument("--determinism", action="store_true")
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, args.out)
    if not os.path.isdir(out_dir):
        print("产物目录不存在：%s（先跑 tools/build_p1_a.py）" % out_dir, file=sys.stderr)
        return 2

    rep = Report()

    # ---------- A1 存在性与非空（fail-closed 第一关）
    missing = []
    zero = []
    for name in REQUIRED_ARTIFACTS:
        p = os.path.join(out_dir, name)
        if not os.path.exists(p):
            missing.append(name)
        elif os.path.getsize(p) == 0:
            zero.append(name)
    rep.add("产物存在且非空", "%d/%d" % (len(REQUIRED_ARTIFACTS) - len(missing), len(REQUIRED_ARTIFACTS)),
            "全部必需产物存在且 size>0", not missing and not zero,
            ("缺：%s；空：%s" % (missing, zero)) if (missing or zero) else "")

    # fail-closed 第一关：缺件即停（不做任何测量、不写报告），避免「读不到 → 异常 → 看似通过」
    if missing or zero:
        print("产物缺失或为空，复测终止：缺=%s 空=%s" % (missing, zero), file=sys.stderr)
        print(json.dumps({"total": len(rep.items), "pass": 0, "fail": 1,
                          "pass_rate": 0.0, "result": "FAIL"}, ensure_ascii=False))
        return 1

    precheck = load_json(os.path.join(out_dir, "precheck.json"))
    contract_doc = load_json(os.path.join(out_dir, "contract.json"))
    crops_doc = load_json(os.path.join(out_dir, "crops.json"))
    safeframe = load_json(os.path.join(out_dir, "safeframe.json"))
    drift = load_json(os.path.join(out_dir, "drift.json"))
    prompts_doc = load_json(os.path.join(out_dir, "prompts.json"))
    receipt = load_json(os.path.join(out_dir, "gate_receipt.json"))
    thresholds = load_json(os.path.join(out_dir, "declared_thresholds.json"))
    not_verified = load_json(os.path.join(out_dir, "not_verified.json"))
    gate_w = crops_doc["gate"]["w"]
    gate_h = crops_doc["gate"]["h"]
    crops = crops_doc["crops"]
    basis_frac = crops_doc["safety_basis"]["action_frac"]

    # ---------- A2 预备性检查：预检本身必须自洽
    summary = precheck["summary"]
    rep.add("预检自洽", "total=%d pass=%d fail=%d" % (summary["total"], summary["pass"], summary["fail"]),
            "fail 计数与 failed_checks 长度一致",
            summary["fail"] == len(precheck["failed_checks"])
            and summary["total"] == summary["pass"] + summary["fail"],
            "FAIL 项：%s" % sorted({c["rule_id"] for c in precheck["failed_checks"]}))

    # ---------- A3 确定性：提示词 sha256 与快照文件一致
    pack_lines = [ln for ln in open(os.path.join(out_dir, "prompt_pack.sha256"), encoding="utf-8") if ln.strip()]
    pack_ok = len(pack_lines) == len(prompts_doc)
    mismatch = []
    for rec, ln in zip(prompts_doc, pack_lines):
        digest, tag = ln.split()
        if digest != rec["sha256"] or tag != "S%02d" % rec["no"]:
            pack_ok = False
            mismatch.append(tag)
    rep.add("提示词 sha256 ↔ 快照一致", "%d 条" % len(pack_lines),
            "prompt_pack.sha256 与 prompts.json 逐条一致", pack_ok, "不一致：%s" % mismatch)

    if args.determinism:
        tmp_a = os.path.join(out_dir, "_det_a")
        tmp_b = os.path.join(out_dir, "_det_b")
        cmd = [sys.executable, os.path.join(HERE, "build_p1_a.py"), "--out"]
        env_a = dict(os.environ, PYTHONHASHSEED="0", TZ="UTC", LANG="C")
        env_b = dict(os.environ, PYTHONHASHSEED="1", TZ="Asia/Shanghai", LANG="zh_CN.UTF-8")
        rc_a = subprocess.call(cmd + [os.path.relpath(tmp_a, ROOT), "--reuse-render"], cwd=ROOT, env=env_a,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rc_b = subprocess.call(cmd + [os.path.relpath(tmp_b, ROOT), "--reuse-render"], cwd=ROOT, env=env_b,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        same = rc_a == 0 and rc_b == 0
        diff_files = []
        if same:
            for name in REQUIRED_ARTIFACTS:
                if name == "prompt_pack.sha256":
                    continue
                pa, pb = os.path.join(tmp_a, name), os.path.join(tmp_b, name)
                if not (os.path.exists(pa) and os.path.exists(pb)):
                    same = False
                    diff_files.append(name)
                    continue
                ha = hashlib.sha256(open(pa, "rb").read()).hexdigest()
                hb = hashlib.sha256(open(pb, "rb").read()).hexdigest()
                if ha != hb:
                    same = False
                    diff_files.append(name)
        rep.add("确定性双跑（PYTHONHASHSEED/TZ/LANG 不同）", "两跑产物字节一致" if same else "存在差异",
                "同输入必须字节级一致", same, "差异文件：%s" % diff_files)
        # 清理临时双跑产物（避免残留污染 out/ 目录与后续审计）
        for tmp in (tmp_a, tmp_b):
            shutil.rmtree(tmp, ignore_errors=True)

    # ---------- A4 复测侧独立重建契约（交叉核对，非复用生成器产物）
    fixture, shots = rebuild_shots(os.path.join(ROOT, args.fixture))
    contract_shots = contract_doc["shots"]
    rep.add("契约镜数 ↔ 产物镜数", "%d / %d" % (len(shots), len(contract_shots)),
            "PRD 解析结果与 contract.json 一致", len(shots) == len(contract_shots))
    field_mismatch = []
    for s, doc in zip(sorted(shots, key=lambda x: x.no), contract_shots):
        for key in ("size", "move", "lens_mm", "key_cct", "dof", "face_pattern",
                    "duration_sec", "physics_skeleton"):
            if s.as_dict()[key] != doc[key]:
                field_mismatch.append("S%02d.%s(%r≠%r)" % (s.no, key, s.as_dict()[key], doc[key]))
    rep.add("契约字段 ↔ 产物字段", "逐字段比对 %d 镜" % len(shots),
            "contract.json 与 PRD 解析结果逐字段一致", not field_mismatch,
            "不一致：%s" % field_mismatch)

    # ---------- A4b 契约字段必须可反查 PRD 原文（逐镜）
    table_src = load_json(os.path.join(out_dir, "table_source.json"))
    src_bad = [r["shot"] for r in table_src["rows"] if not r["prd_fields_match"]]
    rep.add("契约字段可反查 PRD 原文", "自报 all_match=%s；实测 %d/%d 镜逐字段一致"
            % (table_src["all_match"], len(table_src["rows"]) - len(src_bad), len(table_src["rows"])),
            "table_source.json 必须证明每个表内字段都来自 PRD 原文（禁手抄）",
            bool(table_src["all_match"]) and not src_bad, "不一致：%s" % src_bad)
    defaulted = sorted({k for r in table_src["rows"]
                        for k in r["provenance"].get("defaulted", [])})
    rep.add("PRD 表未提供字段已显式登记为默认值", "%d 类" % len(defaulted),
            "表未提供的字段（角度/速度/景深/布光/几何等）必须显式声明为默认值并带来源",
            len(defaulted) >= 8, "默认字段：%s" % defaulted)

    # ---------- A5 像素真值：PNG 独立测量 vs 声明包围盒
    pixel_rows = []
    for s in sorted(shots, key=lambda x: x.no):
        tag = "S%02d" % s.no
        png = os.path.join(out_dir, "proxy", "gate_%s.png" % tag)
        if not os.path.exists(png) or os.path.getsize(png) == 0:
            rep.add("像素测量 %s" % tag, "缺图", "gate_%s.png 存在且非空" % tag, False)
            continue
        measured = measure_subject_from_png(png, gate_w, gate_h)
        declared = safeframe["shots"][tag]["bounds"]
        if measured is None:
            rep.add("像素测量 %s" % tag, "未检出暗部主体", "必须检出主体掩膜", False)
            continue
        tol = 3
        dev = {k: abs(measured[k] - declared[k]) for k in ("x0", "x1", "y0", "y1")}
        ok = all(v <= tol for v in dev.values())
        pixel_rows.append({"shot": tag, "measured": measured, "declared": declared,
                           "max_dev_px": max(dev.values())})
        rep.add("像素测量 %s 与声明包围盒一致" % tag,
                "max_dev=%dpx（tol=%d）" % (max(dev.values()), tol),
                "由 PNG 独立解码测得的主体包围盒必须与声明的构图几何一致", ok,
                "measured=%s" % {k: measured[k] for k in ("x0", "x1", "y0", "y1")})
        # 像素级安全框判定（只用像素实测值，不引用生成器声明）
        ov916 = geometry.overflow(crops["916"], measured)
        t916 = sum(ov916.values())
        rep.add("像素级 9:16 安全框 %s" % tag, "越界像素=%d" % t916,
                "M4.7-F02：像素实测主体在 9:16 窗内越界像素必须为 0",
                t916 == 0, "overflow=%s（measured=%s）" % (ov916, measured))
        h_worst = 0
        for key in ("239", "169"):
            ov = geometry.overflow(crops[key], measured)
            h_worst = max(h_worst, ov["left"] + ov["right"])
        rep.add("像素级水平可裁切 %s" % tag, "水平越界 max=%d" % h_worst,
                "M4.4-F02：主体水平范围必须落在三窗内（竖向被裁属正常取景）",
                h_worst == 0, "")

    # ---------- A6 safeframe.json 内部一致 + 汇总
    sf_bad = []
    clip_916 = []
    crit_bad = []
    for tag, data in safeframe["shots"].items():
        for k in ("239", "169", "916"):
            v = data["per_aspect"][k]
            ov_full = geometry.overflow(crops[k], data["bounds"])
            a = geometry.safe_rect(crops[k], basis_frac)
            ov_crit = geometry.overflow(a, data["critical_region"])
            if (sum(ov_full.values()) != v["overflow_total"]
                    or sum(ov_crit.values()) != sum(v["critical_overflow_px"].values())):
                sf_bad.append("%s/%s" % (tag, k))
            if k == "916" and v["overflow_total"] != 0:
                clip_916.append(tag)
            if sum(ov_crit.values()) != 0:
                crit_bad.append("%s/%s" % (tag, k))
        declared = all(data["per_aspect"][k]["overflow_total"] == 0
                       and data["per_aspect"][k]["critical_in_action_safe"]
                       and data["per_aspect"][k]["horizontal_overflow"] == 0
                       for k in ("239", "169", "916"))
        recomputed = all(data["per_aspect"][k]["overflow_total"] == 0
                         and sum(geometry.overflow(data["per_aspect"][k]["action_safe"],
                                                   data["critical_region"]).values()) == 0
                         and data["per_aspect"][k]["horizontal_overflow"] == 0
                         for k in ("239", "169", "916"))
        if data["fit"] != declared or declared != recomputed:
            sf_bad.append("%s/fit标记" % tag)
    rep.add("9:16 关键信息出框镜数", "%d 镜%s" % (len(clip_916), ("：" + ",".join(sorted(clip_916))) if clip_916 else ""),
            "M4.7-F02：9:16 关键信息出框镜数 = 0", not clip_916 and not sf_bad,
            "几何复算与声明不一致：%s" % sf_bad)
    rep.add("关键信息区落在三画幅 action safe 内", "越界 %d 处%s" % (len(crit_bad), ("：" + ",".join(crit_bad)) if crit_bad else ""),
            "NFR-09 + EL-02：关键信息区（头顶至颈部）必须落在三窗 action safe 内",
            not crit_bad, "判据矩形取各窗 action 93%")

    # ---------- A6b 锚点互核：返修后的参考实现必须全合规；规则之「牙」由变异/负样本证明
    anchor_doc = load_json(os.path.join(out_dir, "anchor_crosscheck.json"))
    anchor_defects = anchor_doc["defects"]
    declared_defect_shots = sorted(d["shot"] for d in anchor_defects)
    rep.add("锚点互核：返修后参考实现 8/8 合规（C-08 已落地）",
            "%d/%d 镜不合格" % (anchor_doc["non_compliant_count"], anchor_doc["shot_count"]),
            "S03/S04/S07 返修后（C-08 选举决议）必须 0 不合格",
            anchor_doc["non_compliant_count"] == 0, "缺陷：%s" % declared_defect_shots)
    # 规则有牙的独立证明：把 S03 灌回返修前的构图参数，必须被 R-SAFEFRAME 判 FAIL
    ref_full, ref_crit, _m = geometry.critical_from_params(0.58, 0.72, 0.66,
                                                           gate_w=gate_w, gate_h=gate_h)
    ref_reasons = []
    for k in ("239", "169", "916"):
        if k == "916" and sum(geometry.overflow(crops[k], ref_full).values()) > 0:
            ref_reasons.append(k)
        if sum(geometry.overflow(geometry.safe_rect(crops[k], basis_frac), ref_crit).values()) > 0:
            ref_reasons.append("%s-action-safe" % k)
    rep.add("锚点互核：返修前 S03(x=0.58) 必须被判不合格（规则有牙）",
            "命中画幅=%s" % sorted(set(ref_reasons)),
            "同一判据必须能检出返修前的真实缺陷（证伪「恒真断言」）",
            bool(ref_reasons), "独立复算（不复用 anchor 模块产物）")
    rep.add("锚点互核不越权否定 demo 结论", anchor_doc["disclaimer"][:40] + "…",
            "必须声明「不否定 demo 24/24 机检结论」并说明判据差异",
            "不受本互核否定" in anchor_doc["disclaimer"])

    # ---------- A7 漂移告警可定位 + 确有条目（S07 3000K 与同场戏 3200K 必须被发现）
    bad_findings = [f for f in drift["findings"] if not f.get("shots") or not f.get("scene")]
    rep.add("漂移告警可定位", "%d 条告警" % len(drift["findings"]),
            "M4.2-F04：每条漂移告警必须带镜号与场次", not bad_findings,
            "不可定位：%s" % bad_findings)
    kinds = sorted({f["kind"] for f in drift["findings"]})
    cct_pairs = [f for f in drift["findings"] if f["kind"] == "cct"]
    rep.add("P1-A-05 场景内色温漂移被发现", "kinds=%s" % kinds,
            "SC-EP01-02 内 3000K 与 3200K 并存必须产出 cct 告警（96 表 S07 与 M5.3-F05 封闭档的冲突）",
            bool(cct_pairs), "cct 告警：%s" % cct_pairs)

    # ---------- A8 变异测试（规则必须有牙）
    run_mutations(os.path.join(ROOT, args.mutations), shots, fixture, rep, crops)

    # ---------- A9 门禁收据字段契约
    v = gates.validate_receipt(receipt)
    rep.add("门禁收据字段齐备", "违规 %d 项" % len(v),
            "M10.3-F02/F03 + D6：署名/理由码/时间戳/二元清单齐备；AI 覆盖须留痕；"
            "无署名不得给出通过结论", not v, "；".join(v))
    rep.add("门禁收据不冒充人工署名", receipt["approver"],
            "占位署名 + 无时间戳时必须为 pending/reject，不得为 pass",
            receipt["approver"] == gates.PLACEHOLDER_APPROVER and receipt["decision"] != "pass",
            "decision=%s" % receipt["decision"])

    # ---------- A10 诚实性字段
    rep.add("代理声明（EL-16）", contract_doc.get("proxy_notice", ""),
            "产物必须标注 PROXY — NOT A DELIVERABLE MASTER", "PROXY" in contract_doc.get("proxy_notice", ""))
    rep.add("P1 退出标准进展诚实字段", str(not_verified.get("p1_exit_criteria_advanced")),
            "p1_exit_criteria_advanced 必须为 false（本切片不覆盖 −23 LUFS / TC）",
            not_verified.get("p1_exit_criteria_advanced") is False)
    rep.add("未验证清单非空", "%d 项" % len(not_verified.get("not_verified", [])),
            "必须显式列出未验证项（D12 缓解措施 3）", len(not_verified.get("not_verified", [])) >= 5)
    src_missing = [k for k, t in thresholds["thresholds"].items() if not t.get("source")]
    rep.add("项目自定阈值均带来源", "%d 条" % len(thresholds["thresholds"]),
            "B-88 / 90 号第九章：项目自定阈值必须写明来源", not src_missing,
            "缺来源：%s" % src_missing)

    # ---------- A11 负样本：注入已知违规构图，必须判 FAIL（证明规则不是恒真）
    neg_cases = [
        ("参考实现原构图 S03(x=0.58)：9:16 右溢", {3: {"subject_x": 0.58}},
         "9:16 出框"),
        ("参考实现原构图 S07(y=0.66)：关键信息越出 action safe", {7: {"subject_y": 0.66}},
         "action safe 越界"),
    ]
    for label, patch, expect in neg_cases:
        neg = copy.deepcopy(shots)
        for s in neg:
            if s.no in patch:
                for k, v in patch[s.no].items():
                    setattr(s, k, v)
        neg_geo = {s.no: compute_bounds(s, gate_w, gate_h) for s in neg}
        neg_checks, _, _ = validators.evaluate(
            neg, fixture["safety_basis"], crops=crops,
            bounds_by_shot={k: v[0] for k, v in neg_geo.items()},
            critical_by_shot={k: v[1] for k, v in neg_geo.items()},
            gate=(gate_w, gate_h))
        neg_failed = [c for c in validators.failed(neg_checks) if c["rule_id"] == "R-SAFEFRAME"]
        rep.add("负样本：%s" % label, "命中 %d 镜" % len(neg_failed),
                "必须触发 %s 的 R-SAFEFRAME FAIL" % expect,
                bool(neg_failed), "；".join(c["measured"] for c in neg_failed))

    # ---------- 报告
    result = rep.summary()
    doc = {
        "verifier": "tools/verify_p1_a.py",
        "verified_from": os.path.relpath(out_dir, ROOT),
        "proxy_notice": render.PROXY_NOTICE,
        "p1_exit_criteria_advanced": False,
        "checks": rep.items,
        "summary": result,
        "not_verified": not_verified.get("not_verified", []),
        "declared_thresholds": thresholds["thresholds"],
        "pixel_vs_declared": pixel_rows,
    }
    out_json = os.path.join(out_dir, "verify_report.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    if args.report:
        lines = ["# P1-A 切片独立复测记录（由 tools/verify_p1_a.py 生成，禁止手抄）", "",
                 "> 被检对象：`%s`｜复测脚本：`tools/verify_p1_a.py`（只读磁盘产物）" % os.path.relpath(out_dir, ROOT),
                 "> 代理声明：%s" % render.PROXY_NOTICE,
                 "> P1 退出标准进展：**未达成**（本切片只推进 M4/M5 契约层）", "",
                 "## 一、汇总", "",
                 "| 项 | 值 |", "|----|----|",
                 "| 检查项总数 | %d |" % result["total"],
                 "| 通过 | %d |" % result["pass"],
                 "| 失败 | %d |" % result["fail"],
                 "| 通过率 | %.2f%% |" % result["pass_rate"],
                 "| 结论 | **%s** |" % result["result"], "",
                 "## 二、逐项结果", "",
                 "| # | 检查项 | 实测 | 判据 | 结论 |", "|---|--------|------|------|------|"]
        for i, it in enumerate(rep.items, 1):
            lines.append("| %d | %s | %s | %s | %s |"
                         % (i, it["item"], str(it["value"]).replace("|", "\\|"),
                            it["rule"].replace("|", "\\|"), "PASS" if it["pass"] else "**FAIL**"))
        lines += ["", "## 三、未验证项（不得作为验收结论引用）", ""]
        for item in not_verified.get("not_verified", []):
            lines.append("- %s" % item)
        lines += ["", "## 四、复现命令", "", "```bash",
                  "python3 tools/build_p1_a.py --out out/p1a",
                  "python3 tools/verify_p1_a.py --out out/p1a --report docs/spec/P1-A-验证记录.md",
                  "cd demo && python3 verify.py && python3 report.py",
                  "python3 tools/prd_guard.py --all", "```", ""]
        os.makedirs(os.path.dirname(os.path.join(ROOT, args.report)), exist_ok=True)
        with open(os.path.join(ROOT, args.report), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    print(json.dumps(result, ensure_ascii=False))
    if rep.failed:
        for it in rep.failed:
            print("FAIL: %s | %s | %s" % (it["item"], it["value"], it["note"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
