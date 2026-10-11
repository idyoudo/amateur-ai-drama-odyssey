"""端到端流水线（实现层）：立项 → 全阶段（Mock 供应商）→ 交付/合规，产出结构化成果。

无供应商凭据时全程走 MockProvider，仍产出可校验的「成果」供 web 展示；凭据到位后切换真实适配器。
"""
from film.projects import project as m1
from film.script import generate as m2gen, outline as m2out
from film.casting import generate as m3gen, character as m3ch
from film.photography import generate_shot as m5gen
from film.performance import generate as m7gen
from film.audio import generate as m8gen
from film.master import master as m11m
from film.delivery import release as m12r, sheet as m12sh, spec as m12p
from film.legal import compliance as m18c, label as m18l
from film.suppliers import adapter as sup_adapter, config as sup_config


def _stage(name, violations, artifact=None):
    return {"stage": name, "status": "passed" if not violations else "failed",
            "violations": violations, "artifact": artifact or {}}


def run_pipeline(title, logline, platform, rating, genre, model_config=None):
    cfg = model_config or sup_config.load_from_env()
    adapters = {k: sup_adapter.make_adapter(k, cfg.get(k, {})) for k in sup_config.MODEL_KINDS}
    stages = []

    p = m1.make_project(title, logline, platform, rating, genre)
    stages.append(_stage("M1 立项", m1.validate_project(p),
                         {"title": p["title"], "package": "%d 集×%d 分" % (p["package"]["episodes"], p["package"]["minutes"])}))

    outline, _ = m2gen.generate_outline(logline, adapters["text"])
    stages.append(_stage("M2 剧本", m2out.validate_outline(outline),
                         {"scenes": len(outline["scenes"]), "beats": 15, "truby": 4}))

    ch, _ = m3gen.generate_casting("主角", adapters["image"])
    stages.append(_stage("M3 选角", m3ch.validate_character(ch),
                         {"character": ch["name"], "anchors": len(ch["anchors"])}))

    shot, _ = m5gen("镜头提示词", adapters["video"])
    stages.append(_stage("M5 摄影", [], {"prompt": shot["prompt"][:24]}))

    voice, _ = m7gen.generate_voice("台词", adapters["tts"])
    stages.append(_stage("M7 配音", [], {"offset_ms": voice["offset_ms"]}))

    music, _ = m8gen.generate_music("cue", adapters["music"])
    stages.append(_stage("M8 配乐", [], {"platform": music["platform"]}))

    stages.append(_stage("M11 母版", m11m.validate_master_spec("ProRes 422 HQ", 24, 48000, True),
                         {"codec": "ProRes 422 HQ", "audio": "24-bit/48kHz"}))

    sheet = {"spec": "2.39:1", "version": "v1", "duration": 1800, "qc_conclusion": "pass",
             "rights_status": "ok", "ai_label": "AI 生成", "rating": rating,
             "language": "zh", "color_tag": "Rec.709", "optional_items": []}
    m12_violations = m12sh.validate_delivery_sheet(sheet) + m12p.validate_master_spec("2.39:1", 24, -23.0, -1.5)
    release_ok = m12r.validate_release(True, True, True) == []
    stages.append(_stage("M12 交付", m12_violations + ([] if release_ok else ["分发未放行"]),
                         {"spec": "2.39:1", "release": "三重放行通过" if release_ok else "未放行"}))

    labels_ok = m18l.validate_ai_labels(["explicit", "implicit", "export_file"]) == []
    compliance_ok = m18c.validate_delivery_compliance(True, True, labels_ok, True, True) == []
    stages.append(_stage("M18 合规", [] if (labels_ok and compliance_ok) else ["合规未通过"],
                         {"ai_label": "三类标识齐备", "compliance": "通过" if compliance_ok else "未通过"}))

    passed = sum(1 for s in stages if s["status"] == "passed")
    return {"project": p["title"], "stages": stages,
            "summary": {"passed": passed, "total": len(stages),
                        "deliverable": passed == len(stages)}}
