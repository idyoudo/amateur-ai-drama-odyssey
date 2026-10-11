"""摄影参数快照与漂移报告（切片 A · M5.2-F05 / M5.6-F03 / M4.2-F03/F04）。

快照目的：每镜产物可反查**当次实际使用的摄影契约**（焦距档、景深意图、风格包、光位、色温、帧率），
供跨镜漂移比对与事后追溯（依据 E-04 指纹、D-39 留存）。
"""

import hashlib
import json

from . import enums
from .contract import CONTRACT_VERSION, MAP_VERSION

FPS_LOCKED = 24  # EL-09：全片时间线锁定 24fps
STYLE_PACKS = ("anamorphic_widescreen", "none")


def snapshot_shot(shot):
    """单镜摄影参数快照。"""
    pack = "anamorphic_widescreen" if shot.lens_mm >= 85 and shot.dof == "shallow" else "none"
    return {
        "shot": "S%02d" % shot.no,
        "contract_version": CONTRACT_VERSION,
        "mapping_version": MAP_VERSION,
        "fps": FPS_LOCKED,
        "scene": shot.scene,
        "size": shot.size,
        "angle": shot.angle,
        "move": shot.move,
        "move_secondary": shot.move_secondary,
        "speed": shot.speed,
        "subject_move": shot.subject_move,
        "lens_mm": shot.lens_mm,
        "lens_label": enums.LENS_LABEL[shot.lens_mm],
        "dof": shot.dof,
        "style_pack": pack,
        "style_pack_three_elements": {
            "oval_bokeh": pack == "anamorphic_widescreen",
            "horizontal_blue_flare": pack == "anamorphic_widescreen",
            "aspect_intent_239": pack == "anamorphic_widescreen",
            "note": "M5.2-F04：三要素必须同时具备，缺一即风格不成立",
        },
        "face_pattern": shot.face_pattern,
        "lighting": {
            "key_clock": shot.key_clock,
            "fill_clock": shot.fill_clock,
            "back_clock": shot.back_clock,
            "key_ratio": shot.key_ratio,
            "fill_ratio": shot.fill_ratio,
            "fill_key_limit": 0.5,
        },
        "cct": {
            "key_k": shot.key_cct,
            "fill_k": shot.fill_cct,
            "relation": shot.cct_relation,
        },
        "volumetric": {"active": shot.volumetric_active, "media": shot.volumetric_media},
        "coverage": shot.coverage,
        "physics_skeleton": {
            "required": shot.physics_skeleton,
            "triggers": list(shot.physics_triggers),
            "rule": "M5.5-F01：高动态/负重/碰撞镜必须走物理骨架通道，覆盖率 100%",
        },
        "geometry": {
            "subject_x": shot.subject_x,
            "subject_y": shot.subject_y,
            "subject_scale": shot.subject_scale,
            "source": shot.provenance.get("geometry", {}).get("source", ""),
        },
        "duration_sec": shot.duration_sec,
        "prompt_sha256": None,  # 由 build 填入
    }


def snapshot_all(shots, prompt_records):
    by_no = {p["no"]: p for p in prompt_records}
    snaps = []
    for s in sorted(shots, key=lambda x: x.no):
        snap = snapshot_shot(s)
        snap["prompt_sha256"] = by_no.get(s.no, {}).get("sha256", "")
        snaps.append(snap)
    return {
        "contract_version": CONTRACT_VERSION,
        "mapping_version": MAP_VERSION,
        "shot_count": len(snaps),
        "shots": snaps,
    }


def drift_report(shots, findings):
    """漂移报告：同时给出「按场景分组的实测值」与「告警条目」（M5.6-F03 要求可复核）。"""
    scenes = {}
    for s in sorted(shots, key=lambda x: x.no):
        scenes.setdefault(s.scene, []).append({
            "shot": "S%02d" % s.no,
            "lens_mm": s.lens_mm,
            "dof": s.dof,
            "key_cct": s.key_cct,
            "key_clock": s.key_clock,
        })
    return {
        "policy": "漂移检测为**告警**而非否决（M4.5-F02 同纪律）；每条告警必须带镜号与场次",
        "scene_groups": scenes,
        "thresholds": {
            "clock_drift_deg": 30.0,
            "cct_drift_k": 200.0,
            "source": "项目自定（PRD 未给数值）",
        },
        "findings": findings,
        "finding_count": len(findings),
    }


def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dumps_stable(obj):
    """稳定序列化：排序键、固定分隔符、ensure_ascii=False（保证字节级可复现）。"""
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
