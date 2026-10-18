"""营销素材：多平台文案、海报 SVG、预告片分镜与 HTML 动态预览。

不依赖外部生成服务；文案/海报/分镜由项目数据确定性生成，视频由浏览器录制 WebM。
"""
import html
import json

CHANNELS = [
    ("hongguo", "红果漫剧"), ("douyin", "抖音短剧"), ("kuaishou", "快手星芒"),
    ("youtube_shorts", "YouTube Shorts"), ("youtube", "YouTube 长视频"),
]

HOOK_WORDS = ("真相", "命案", "失忆", "复仇", "秘密", "背叛", "逆袭", "阴谋",
              "追杀", "失踪", "重生", "离婚", "豪门", "悬案")


def _clauses(logline):
    out = []
    for part in str(logline or "").replace("；", "，").replace(";", "，").split("，"):
        p = part.strip("。 ")
        if p:
            out.append(p)
    return out


def _has_hook(text):
    return any(w in text for w in HOOK_WORDS)


def _fmt_line(project):
    eps = project.get("episodes") or 6
    mins = project.get("minutes") or 30
    spec = project.get("delivery_spec") or {}
    aspect = spec.get("master") or "2.39:1"
    return "%d 集 × %d 分钟 · %s" % (eps, mins, aspect)


def _titles(project, clauses):
    title = project.get("title") or "未命名短剧"
    genre = project.get("genre") or "短剧"
    hook = clauses[0] if clauses else title
    return [title, "《%s》｜%s短剧" % (title, genre),
            "%s：%s" % (title, hook[:24]), "《%s》第 1 集" % title]


def _hooks(clauses):
    if not clauses:
        return ["前 3 秒，故事已经开始。"]
    c1 = clauses[0]
    c2 = clauses[1] if len(clauses) > 1 else c1
    hooks = []
    hooks.append(c1[:40])
    if _has_hook(c1) or _has_hook(c2):
        hooks.append("如果%s，你还会相信%s吗？" % (c1[:18], c2[:18]))
    hooks.append("前 3 秒：%s。下一秒，%s。" % (c1[:20], c2[:20]))
    hooks.append("所有人都以为结束了，直到%s。" % c2[:28])
    return hooks[:3]


def _hashtags(genre):
    g = str(genre or "短剧")
    tags = ["#短剧", "#AI短剧", "#%s" % g]
    if any(w in g for w in ("悬疑", "犯罪", "惊悚")):
        tags += ["#反转", "#烧脑"]
    elif any(w in g for w in ("甜", "恋", "爱情")):
        tags += ["#甜宠", "#上头"]
    elif any(w in g for w in ("古装", "国风")):
        tags += ["#古装", "#国风"]
    return " ".join(dict.fromkeys(tags))


def _captions(project, titles, hooks):
    title = project.get("title") or "未命名短剧"
    genre = project.get("genre") or "短剧"
    rating = project.get("rating") or "全龄"
    fmt = _fmt_line(project)
    hook = hooks[0] if hooks else ""
    tags = _hashtags(genre)
    out = {}
    for key, name in CHANNELS:
        if key in ("hongguo", "douyin", "kuaishou"):
            out[key] = {"channel": name,
                        "title": "%s｜%s" % (title, genre),
                        "body": "%s\n%s\n%s · %s" % (hook, fmt, rating, tags)}
        elif key == "youtube_shorts":
            out[key] = {"channel": name,
                        "title": "%s #Shorts" % title,
                        "body": "%s\n%s\n%s" % (hook, fmt, tags)}
        else:
            out[key] = {"channel": name,
                        "title": "%s｜%s短剧" % (title, genre),
                        "body": "%s\n%s\n%s · %s\n%s" % (hook, fmt, rating, tags, "全集连载")}
    return out


def _shot_beats(shots):
    if not shots:
        return []
    picks = [s for s in shots if s.get("dialogue") or s.get("characters")]
    if len(picks) < 6:
        picks = shots
    step = max(1, len(picks) // 6)
    picked = picks[::step][:6]
    beats = []
    for s in picked:
        cap = s.get("dialogue") or "、".join(s.get("characters") or []) or s.get("prompt") or "关键镜头"
        beats.append({"caption": str(cap)[:40],
                      "duration": min(3, max(1, int(s.get("duration") or 2))),
                      "shot_no": s.get("shot_no"), "episode_id": s.get("episode_id") or 1,
                      "transition": "硬切"})
    return beats


def build_kit(project, scenes=None, shots=None):
    clauses = _clauses(project.get("logline"))
    titles = _titles(project, clauses)
    hooks = _hooks(clauses)
    captions = _captions(project, titles, hooks)
    shot_beats = _shot_beats(shots or [])
    beats = [{"caption": hooks[0] if hooks else "故事开始", "duration": 3,
              "transition": "冷开场", "shot_no": None, "episode_id": 1}]
    if shot_beats:
        beats += shot_beats
    else:
        for c in clauses[:5]:
            beats.append({"caption": c[:40], "duration": 3, "transition": "硬切",
                          "shot_no": None, "episode_id": 1})
    beats.append({"caption": "真相即将揭晓，全集上线", "duration": 3,
                  "transition": "悬念收尾", "shot_no": None, "episode_id": 1})
    total = sum(b["duration"] for b in beats)
    fmt = _fmt_line(project)
    kit = {
        "project": {"id": project.get("id"), "title": project.get("title"),
                    "logline": project.get("logline"), "genre": project.get("genre"),
                    "rating": project.get("rating"), "platform": project.get("platform"),
                    "format": fmt},
        "titles": titles,
        "hooks": hooks,
        "captions": captions,
        "hashtags": _hashtags(project.get("genre")),
        "trailer": {"beats": beats, "total_seconds": total},
        "posters": {
            "portrait": _poster_svg(project, fmt, 1080, 1920, hooks[0] if hooks else ""),
            "landscape": _poster_svg(project, fmt, 1200, 675, hooks[0] if hooks else ""),
        },
        "disclaimer": "文案与海报为模板生成；HTML 为动态预览；WebM 由浏览器录制，平台如需 MP4 请转码。",
    }
    return kit


def _wrap(text, width):
    lines, cur = [], ""
    for ch in str(text or ""):
        cur += ch
        if len(cur) >= width:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return lines[:4]


def _poster_svg(project, fmt, w, h, hook):
    title = str(project.get("title") or "未命名短剧")
    genre = str(project.get("genre") or "短剧")
    rating = str(project.get("rating") or "全龄")
    title_lines = _wrap(title, 10 if w < h else 16)
    hook_lines = _wrap(hook, 18 if w < h else 36)
    title_size = 92 if w < h else 64
    y = h * 0.52
    tspans = "".join(
        '<tspan x="8%%" dy="%d">%s</tspan>' % (0 if i == 0 else title_size + 12, html.escape(ln))
        for i, ln in enumerate(title_lines))
    hspans = "".join(
        '<tspan x="8%%" dy="%d">%s</tspan>' % (0 if i == 0 else 34, html.escape(ln))
        for i, ln in enumerate(hook_lines))
    return """<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#101018"/><stop offset="1" stop-color="#26263f"/></linearGradient></defs>
<rect width="%d" height="%d" fill="url(#bg)"/>
<rect x="8%%" y="%d" width="12%%" height="4" fill="#8b8bf0"/>
<text x="8%%" y="%d" fill="#ffffff" font-family="'PingFang SC','Songti SC',serif" font-size="%d" font-weight="600">%s</text>
<text x="8%%" y="%d" fill="#c9c9d6" font-family="'PingFang SC',sans-serif" font-size="30">%s</text>
<text x="8%%" y="88%%" fill="#a0a0ac" font-family="'PingFang SC',sans-serif" font-size="26">%s · %s</text>
<text x="8%%" y="94%%" fill="#8b8bf0" font-family="'PingFang SC',sans-serif" font-size="24">AADO · AI 生成内容</text>
</svg>""" % (w, h, w, h, w, h, int(h * 0.30), int(y),
             title_size, tspans, int(y + title_size * len(title_lines) + 60),
             hspans, html.escape(fmt), html.escape(rating))


def build_promo_html(kit):
    beats = kit["trailer"]["beats"]
    data = json.dumps({"title": kit["project"]["title"], "hook": kit["hooks"][0] if kit["hooks"] else "",
                       "beats": beats, "format": kit["project"]["format"]}, ensure_ascii=False)
    return """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · 动态预览</title>
<style>
html,body{margin:0;height:100%%;background:#09090d;color:#fff;font-family:"PingFang SC","Microsoft YaHei",sans-serif;overflow:hidden}
.stage{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}
.card{width:min(92vw,420px);aspect-ratio:9/16;background:linear-gradient(150deg,#12121b,#272742);border-radius:18px;padding:34px 30px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:flex-end;position:relative;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6)}
.card:before{content:"";position:absolute;inset:0;background:radial-gradient(600px 300px at 80%% -10%%,rgba(139,139,240,.35),transparent 60%%)}
.kicker{position:absolute;top:30px;left:30px;font-size:12px;letter-spacing:.18em;color:#8b8bf0}
h1{font-size:34px;line-height:1.15;margin:0 0 10px;position:relative}
p{font-size:16px;line-height:1.6;color:#d0d0dc;margin:0;position:relative}
.bar{position:absolute;left:0;right:0;bottom:0;height:4px;background:rgba(255,255,255,.12)}
.bar i{display:block;height:100%%;width:0;background:#8b8bf0}
.foot{position:absolute;left:30px;right:30px;bottom:22px;display:flex;justify-content:space-between;font-size:11px;color:#8a8a96}
.replay{position:fixed;bottom:18px;left:50%%;transform:translateX(-50%%);background:#fff;color:#111;border:0;border-radius:8px;padding:8px 14px;font-size:12px;cursor:pointer}
</style></head><body>
<div class="stage"><div class="card">
  <div class="kicker">AADO · AI 短剧预告</div>
  <h1 id="t"></h1><p id="p"></p>
  <div class="bar"><i id="bar"></i></div>
  <div class="foot"><span id="fmt"></span><span>AI 生成内容</span></div>
</div></div>
<button class="replay" onclick="start()">重播</button>
<script>
const D=%s; let timer;
function start(){
  const seq=[{t:D.title,p:D.hook}].concat(D.beats.map(b=>({t:b.caption,p:b.transition})));
  const per=2600; let i=0; document.getElementById("fmt").textContent=D.format;
  clearInterval(timer);
  function show(){
    const s=seq[i%%seq.length]; document.getElementById("t").textContent=s.t||"";
    document.getElementById("p").textContent=s.p||""; i++;
    const bar=document.getElementById("bar"); bar.style.transition="none"; bar.style.width="0%%";
    requestAnimationFrame(()=>{bar.style.transition="width "+per+"ms linear"; bar.style.width="100%%";});
  }
  show(); timer=setInterval(show,per);
}
start();
</script></body></html>""" % (html.escape(kit["project"]["title"]), data)
