/* AADO 控制台 SPA —— 路由 / 项目工作台 / 阶段步骤条 / 资产网格 */
const TK = "aado_token";
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hasToken = () => !!localStorage.getItem(TK);

/* 19 个模块阶段的展示元数据（与后端 pipeline 的 stage 名对应） */
/* AADO 五段流程（Development→Delivery） */
const SEGMENTS = [
  ["Development 开发", ["M1 立项", "M2 剧本"]],
  ["Pre-production 前期", ["M3 选角", "M4 分镜"]],
  ["Production 制作", ["M5 摄影", "M6 一致性", "M7 配音", "M8 配乐"]],
  ["Post 后期", ["M9 剪辑", "M11 母版", "M19 VFX"]],
  ["Delivery 交付", ["M10 门禁", "M12 交付", "M14 成本", "M15 存储", "M16 协作", "M17 供应商", "M18 合规", "M13 任务"]],
];
const STAGES = [
  ["M1 立项", "立项", "📋"], ["M2 剧本", "剧本", "✍️"], ["M3 选角", "选角", "🎭"],
  ["M4 分镜", "分镜", "🎬"], ["M5 摄影", "摄影", "🎥"], ["M6 一致性", "一致性", "👤"],
  ["M7 配音", "配音", "🎙️"], ["M8 配乐", "配乐", "🎵"], ["M9 剪辑", "剪辑", "✂️"],
  ["M10 门禁", "门禁", "🚦"], ["M11 母版", "母版", "🎞️"], ["M12 交付", "交付", "📦"],
  ["M14 成本", "成本", "💰"], ["M15 存储", "存储", "🗄️"], ["M16 协作", "协作", "👥"],
  ["M17 供应商", "供应商", "🔌"], ["M18 合规", "合规", "⚖️"], ["M19 VFX", "VFX", "✨"],
  ["M13 任务", "任务", "🔄"],
];

/* ---------- 请求 ---------- */
async function api(path, opt) {
  opt = opt || {};
  opt.headers = Object.assign({}, opt.headers || {}, hasToken() ? { Authorization: "Bearer " + localStorage.getItem(TK) } : {});
  const r = await fetch(path, opt);
  if (r.status === 401) { logout(); throw new Error("未授权"); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((d && d.detail) ? JSON.stringify(d.detail) : ("HTTP " + r.status));
  return d;
}
function toast(msg) {
  let t = $("#toast"); if (t) t.remove();
  t = document.createElement("div"); t.id = "toast"; t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t); setTimeout(() => t.remove(), 2200);
}

/* ---------- 鉴权 ---------- */
function logout() { localStorage.removeItem(TK); renderLogin(); }
function renderLogin() {
  document.body.innerHTML = `<div class="login-wrap"><form class="login-card" id="lf">
    <div class="brand"><div class="lg">🎬</div><div><div style="font-weight:700;font-size:16px">AADO</div>
      <div class="muted" style="font-size:11px;letter-spacing:1px">AI DRAMA ODYSSEY</div></div></div>
    <div style="display:flex;flex-direction:column;gap:12px">
      <input name="username" placeholder="用户名" value="admin">
      <input name="password" type="password" placeholder="密码" autofocus>
      <button class="btn" type="submit">登 录</button>
      <div id="lerr" class="muted hide" style="color:var(--bad);font-size:12px"></div>
    </div></form></div>`;
  $("#lf").onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target);
    const r = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: f.get("username"), password: f.get("password") }) });
    if (r.ok) { const d = await r.json(); localStorage.setItem(TK, d.token); boot(); }
    else { const x = $("#lerr"); x.classList.remove("hide"); x.textContent = "用户名或密码错误"; }
  };
}

/* ---------- 外壳 ---------- */
const RAIL = [
  ["overview", "概览", "🏠"], ["projects", "项目", "🎬"], ["assets", "资产库", "🎨"],
  ["playground", "生成台", "🧪"], ["jobs", "任务", "📋"], ["models", "模型", "🎛️"], ["settings", "设置", "⚙️"],
];
function shell(active) {
  document.body.innerHTML = `<aside class="rail" id="rail">
      <div class="logo" title="AADO">🎬</div>
      <div class="nav">${RAIL.map(([id, l, ic]) =>
        `<div class="item ${id === active ? "on" : ""}" data-go="${id}"><div>${ic}</div><span>${l}</span></div>`).join("")}</div>
    </aside>
    <div class="main" id="main"></div>`;
  $$("[data-go]").forEach(el => el.onclick = () => go(el.dataset.go));
}
function setMain(html, wide) {
  const m = $("#main");
  m.innerHTML = `<div class="topbar">${html.top}</div><div class="view ${wide ? "wide" : ""}">${html.body}</div>`;
}
function go(route) {
  const parts = String(route).split(":");
  const name = parts[0];
  const param = parts[1];
  shell(name === "project" ? "projects" : name);
  if (name === "overview") return viewOverview();
  if (name === "projects") return viewProjects();
  if (name === "project") return viewProject(param);
  if (name === "assets") return viewAssets();
  if (name === "playground") return viewPlayground();
  if (name === "jobs") return viewJobs();
  if (name === "models") return viewModels();
  if (name === "settings") return viewSettings();
}

/* ---------- 概览 ---------- */
async function viewOverview() {
  const [cfg, projs] = await Promise.all([api("/api/models/config"), api("/api/dramas")]);
  const configured = cfg.available.length;
  setMain({
    top: `<h1>概览 <span class="crumbs">好莱坞级 AI 短剧流水线</span></h1>
      <div class="right"><span class="pill ok"><i class="dot ok"></i>服务运行中</span>
      <span class="pill ${configured ? "gold" : ""}">${configured ? configured + " 个模型已配置" : "Mock 模式"}</span></div>`,
    body: `
    <div class="stats">
      <div class="stat"><div class="k">19</div><div class="l">流程模块</div></div>
      <div class="stat"><div class="k">${configured}</div><div class="l">已配置模型</div></div>
      <div class="stat"><div class="k">${projs.length}</div><div class="l">项目</div></div>
      <div class="stat"><div class="k">端到端</div><div class="l">小说 → 成片母版</div></div>
    </div>
    <h2>制作流程 <span class="hint">19 模块 · Development → Delivery</span></h2>
    <div class="card">
      ${SEGMENTS.map(([seg, mods]) => `<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--line)">
        <div style="flex:0 0 150px;font-size:12px;color:var(--gold2)">${seg}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">${mods.map(m => {
          const meta = STAGES.find(x => x[0] === m) || ["", m, ""];
          return `<span class="pill" style="font-size:11px">${meta[2]} ${meta[1]}</span>`; }).join("")}</div></div>`).join("")}
    </div>
    <h2>最近项目 <span class="hint">进入工作台运行流水线</span></h2>
    ${projs.length ? `<div class="cards">${projs.slice(0, 6).map(projectCard).join("")}</div>`
      : `<div class="card empty">还没有项目。到「项目」页创建第一部剧。</div>`}`,
  });
}
function projectCard(p) {
  const badge = p.deliverable ? `<span class="pill ok"><i class="dot ok"></i>可交付</span>`
    : (p.stages_passed ? `<span class="pill gold">${p.stages_passed}/19 阶段</span>` : `<span class="pill">未制作</span>`);
  return `<div class="card click" onclick="go('project:${p.id}')">
    <div style="display:flex;justify-content:space-between;align-items:start;gap:8px">
      <h4 style="margin:0 0 6px;font-size:15px">${esc(p.title)}</h4>${badge}</div>
    <div class="muted" style="font-size:12px;min-height:32px">${esc(p.logline || "")}</div>
    <div class="muted" style="font-size:11px;margin-top:8px">${p.episodes || 6} 集 × ${p.minutes || 30} 分钟${p.shots ? " · " + p.shots + " 镜" : ""}</div></div>`;
}

/* ---------- 项目列表 ---------- */
async function viewProjects() {
  const projs = await api("/api/dramas");
  setMain({
    top: `<h1>项目 <span class="crumbs">立项与工作台</span></h1><div class="right"><span class="pill">${projs.length} 个项目</span></div>`,
    body: `
    <h2>创建项目</h2>
    <form class="stack" id="pf">
      <div class="row2"><input name="title" placeholder="片名" required>
        <input name="logline" placeholder="一句话故事（logline，必填 ≤120 字）" required></div>
      <div class="row2"><input name="platform" placeholder="目标平台" required>
        <input name="genre" placeholder="题材" value="悬疑"></div>
      <div class="row2">
        <select name="rating"><option>全龄</option><option>12+</option><option>16+</option></select>
        <select name="minutes"><option value="30">30 分钟/集</option><option value="22">22 分钟/集</option><option value="45">45 分钟/集</option></select></div>
      <div><button class="btn" type="submit">创建立项</button></div>
    </form>
    <h2>全部项目 <span class="hint">${projs.length} 个</span></h2>
    <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">
      <input id="psearch" placeholder="搜索片名 / logline" style="max-width:280px" oninput="filterProjs()">
      <select id="psort" style="max-width:180px" onchange="filterProjs()">
        <option value="id">按创建时间</option><option value="title">按片名</option>
        <option value="deliverable">可交付优先</option></select>
    </div>
    <div class="cards" id="plist">${projs.length ? projs.map(projectCard).join("") : ""}</div>
    ${projs.length ? "" : `<div class="card empty">暂无项目</div>`}`,
  });
  window._PROJS = projs;
}
function filterProjs() {
  const q = (($("#psearch") || {}).value || "").toLowerCase();
  const sort = ($("#psort") || {}).value || "id";
  let list = (window._PROJS || []).filter(p =>
    !q || (p.title || "").toLowerCase().includes(q) || (p.logline || "").toLowerCase().includes(q));
  if (sort === "title") list = list.slice().sort((a, b) => (a.title || "").localeCompare(b.title || ""));
  else if (sort === "deliverable") list = list.slice().sort((a, b) => (b.deliverable ? 1 : 0) - (a.deliverable ? 1 : 0));
  $("#plist").innerHTML = list.length ? list.map(projectCard).join("") : `<div class="card empty">无匹配项目</div>`;
  $("#pf").onsubmit = async e => {
    e.preventDefault(); const b = Object.fromEntries(new FormData(e.target)); b.episodes = 6;
    try { const d = await api("/api/dramas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
      toast("✅ 立项成功"); go("project:" + d.id); } catch (err) { toast("❌ " + err.message); }
  };
}

/* ---------- 项目工作台 ---------- */
let CUR = { id: null, stage: null };
async function viewProject(id) {
  CUR.id = id;
  let p; try { p = await api("/api/dramas/" + id); } catch (e) { toast("项目不存在"); return go("projects"); }
  const run = p.last_run;
  const stages = (run && run.stages) || [];
  const byName = {}; stages.forEach(s => byName[s.stage] = s);
  if (!CUR.stage) CUR.stage = STAGES[0][0];

  const stepCard = (name) => {
    const meta = STAGES.find(x => x[0] === name) || ["", name, ""];
    const st = byName[name];
    const cls = st ? (st.status === "passed" ? "ok" : "bad") : "";
    const txt = st ? (st.status === "passed" ? "通过" : "失败") : (run ? "—" : "待运行");
    return `<div class="step ${CUR.stage === name ? "on" : ""}" onclick="pickStage('${name}')">
      <div class="n">${meta[2]} ${meta[1]}</div><div class="t">${name.replace(/^M\d+ /, "")}</div>
      <div class="s">${st ? `<i class="dot ${cls}"></i> ${txt}` : txt}</div></div>`;
  };
  const stepper = SEGMENTS.map(([seg, mods]) => `<div style="margin-bottom:12px">
      <div style="font-size:11px;color:var(--gold2);letter-spacing:.5px;margin-bottom:6px">${seg}</div>
      <div class="stepper">${mods.map(stepCard).join("")}</div></div>`).join("");

  const passed = run ? run.summary.passed : 0, total = 19;
  setMain({
    top: `<h1><span class="crumbs" style="cursor:pointer" onclick="go('projects')">项目 ›</span> <span class="t">${esc(p.title)}</span></h1>
      <div class="right">
        <span class="pill">${p.episodes} 集 × ${p.minutes} 分钟</span>
        <span class="pill gold">${esc(p.rating || "")} · ${esc(p.genre || "")}</span>
        <button class="btn ghost" id="runbtn">▶ 运行流水线</button>
        <button class="btn" id="prodbtn">🎬 一键全流程</button></div>`,
    body: `
    <div class="card">
      <div class="kv">
        <div class="k">Logline</div><div>${esc(p.logline)}</div>
        <div class="k">目标平台</div><div>${esc(p.platform || "—")}</div>
        <div class="k">交付规格</div><div>${(p.delivery_spec && p.delivery_spec.master) ? `主母版 ${p.delivery_spec.master} · 平台版 ${p.delivery_spec.platform} · 竖屏 ${p.delivery_spec.derived}` : "—"}</div>
        <div class="k">流水线</div><div>${run ? `<span class="pill ${run.summary.deliverable ? "ok" : "bad"}">${passed}/${total} 阶段通过 ${run.summary.deliverable ? "· 可交付" : ""}</span>` : `<span class="pill">尚未运行</span>`}</div>
      </div>
    </div>
    <h2>制作流程 <span class="hint">按 Development → Delivery 五段 · 点击阶段查看成果</span></h2>
    ${stepper}
    <div id="stagedetail"></div>`,
  }, true);
  $("#runbtn").onclick = () => runPipeline(id);
  $("#prodbtn").onclick = () => produceAll(id);
  renderStageDetail(byName[CUR.stage]);
  window.pickStage = (n) => { CUR.stage = n; viewProject(id); };
}
async function renderStageDetail(st) {
  const el = $("#stagedetail"); if (!el) return;
  if (!st) { el.innerHTML = `<div class="detail empty">该阶段尚无运行结果，点击「运行流水线」生成。</div>`; return; }
  const meta = STAGES.find(s => s[0] === st.stage) || ["", "", ""];
  const art = st.artifact || {};
  const head = `<div class="head"><h2 style="margin:0">${meta[2]} ${st.stage}</h2>
      <span class="pill ${st.status === "passed" ? "ok" : "bad"}">${st.status === "passed" ? "✓ 通过" : "✗ 失败"}</span></div>`;
  const viol = (st.violations && st.violations.length) ? `<div style="margin-top:12px;color:var(--bad)">违规：${st.violations.map(esc).join("；")}</div>` : "";
  // 剧本阶段 → 剧本编辑器（可编辑场次 + 结构健康度）
  if (/剧本/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="scriptview">加载剧本…</div></div>`;
    return renderScript();
  }
  // 门禁阶段 → 门禁工作台（AADO 好莱坞级：五门禁署名）
  if (/门禁/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="gateview">加载门禁…</div></div>`;
    return renderGates();
  }
  // 剪辑阶段 → 时间线视图
  if (/剪辑/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="tlview">加载时间线…</div></div>`;
    return renderTimeline();
  }
  // 分镜/摄影阶段 → 分镜工作台
  if (/分镜|摄影/.test(st.stage)) {
    if (SBCUR !== CUR.id) { SBSEL.clear(); SBCUR = CUR.id; }
    el.innerHTML = `<div class="detail">${head}<div id="sbwork">加载分镜…</div></div>`;
    return renderStoryboard();
  }
  el.innerHTML = `<div class="detail">${head}${stageBody(st.stage, art)}${viol}</div>`;
}

/* ---------- 分镜工作台（参考 LumenX Storyboard / Toonflow 批量网格） ---------- */
const SBSEL = new Set();
let SBCUR = null;
async function renderStoryboard() {
  const box = $("#sbwork"); if (!box) return;
  let shots = [];
  try { shots = await api("/api/dramas/" + CUR.id + "/shots"); } catch (e) {}
  if (!shots.length) {
    box.innerHTML = `<div class="muted" style="margin-bottom:12px">尚无分镜表。从剧本派生镜头（每场 1–3 镜）。</div>
      <button class="btn" onclick="genShots()">📋 生成分镜表</button>`;
    return;
  }
  box.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px">
      <div class="muted">共 <b>${shots.length}</b> 镜 · 已生成 ${shots.filter(x => x.status === "已生成").length}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn ghost sm" onclick="sbSelect('all')">全选</button>
        <button class="btn ghost sm" onclick="sbSelect('none')">取消</button>
        <button class="btn ghost sm" onclick="sbSelect('pending')">选未生成</button>
        <button class="btn sm" onclick="sbBatch()">⚡ 批量生成所选</button>
      </div>
    </div>
    <div class="cards" id="sbshots" style="grid-template-columns:repeat(auto-fill,minmax(210px,1fr))">
      ${shots.map(sbCard).join("")}</div>`;
  $$(".sbcard").forEach(c => c.onclick = e => { if (e.target.tagName !== "INPUT") sbOpen(c.dataset.id, c.dataset.no); });
}
function sbCard(s) {
  const sel = SBSEL.has(String(s.id));
  return `<div class="asset sbcard" data-id="${s.id}" data-no="${s.shot_no}" style="cursor:pointer;${sel ? "border-color:var(--gold)" : ""}">
    <div class="thumb" style="font-size:30px">${s.status === "已生成" ? "🖼️" : "🎞️"}
      <span class="tag">镜 ${s.shot_no}</span>
      <input type="checkbox" ${sel ? "checked" : ""} style="position:absolute;top:8px;right:8px;width:auto" onclick="event.stopPropagation();sbToggle('${s.id}')"></div>
    <div class="body"><h4 style="font-size:13px">场 ${s.scene_no} · ${esc(s.move)}</h4>
      <div class="meta"><span>${esc(s.size)}</span><span>${esc(s.angle)}</span><span>${s.duration}s</span>
        ${(s.characters || []).map(c => `<span>${esc(c)}</span>`).join("")}</div>
      <div style="margin-top:8px"><span class="pill ${s.status === "已生成" ? "ok" : ""}" style="font-size:10px">${esc(s.status)}</span></div></div></div>`;
}
function sbToggle(id) {
  id = String(id); if (SBSEL.has(id)) SBSEL.delete(id); else SBSEL.add(id);
  const c = $(`.sbcard[data-id="${id}"]`);
  if (c) { c.style.borderColor = SBSEL.has(id) ? "var(--gold)" : ""; const cb = c.querySelector("input"); if (cb) cb.checked = SBSEL.has(id); }
}
async function sbSelect(mode) {
  const shots = await api("/api/dramas/" + CUR.id + "/shots");
  SBSEL.clear();
  shots.forEach(s => { if (mode === "all" || (mode === "pending" && s.status !== "已生成")) SBSEL.add(String(s.id)); });
  renderStoryboard();
}
async function sbBatch() {
  if (!SBSEL.size) return toast("先选择镜头");
  try { const r = await api("/api/dramas/" + CUR.id + "/shots/batch", { method: "POST",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify({ shot_ids: Array.from(SBSEL).map(Number) }) });
    toast("✅ 生成 " + r.generated + " 镜"); renderStoryboard();
  } catch (e) { toast("❌ " + e.message); }
}
async function genShots() {
  try { const r = await api("/api/dramas/" + CUR.id + "/shots/generate", { method: "POST" });
    toast("✅ 派生 " + r.count + " 镜"); renderStoryboard();
  } catch (e) { toast("❌ " + e.message); }
}

/* 镜头详情弹窗：字段 + 抽卡候选（参考 LumenX R2V 批量抽卡） */
async function sbOpen(shotId, shotNo) {
  const shots = await api("/api/dramas/" + CUR.id + "/shots");
  const sh = shots.find(x => String(x.id) === String(shotId));
  if (!sh) return;
  const cands = await api("/api/shots/" + shotId + "/candidates");
  const modal = document.createElement("div");
  modal.className = "modal"; modal.id = "sbmodal";
  modal.innerHTML = `<div class="box">
    <div class="mhead"><h2>镜 ${sh.shot_no} · 场 ${sh.scene_no} · ${esc(sh.move)}</h2>
      <button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="mbody">
      <div class="kv" style="margin-bottom:16px">
        <div class="k">景别 / 角度</div><div>${esc(sh.size)} / ${esc(sh.angle)}</div>
        <div class="k">时长</div><div>${sh.duration}s</div>
        <div class="k">角色</div><div>${(sh.characters || []).map(esc).join("、") || "空镜"}</div>
        <div class="k">提示词</div><div>${esc(sh.prompt)}</div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <b style="font-size:13px">候选（抽卡）</b>
        <button class="btn sm" onclick="genCands('${shotId}')">🎲 生成 4 个候选</button></div>
      <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(140px,1fr))">
        ${cands.length ? cands.map(c => `<div class="cand ${c.selected ? "on" : ""}" onclick="pickCand('${c.id}','${shotId}')">
          <div class="thumb">🖼️${c.selected ? '<span class="pick">已选</span>' : ""}<span class="score">${c.score}</span></div></div>`).join("")
          : `<div class="muted" style="padding:20px">尚无候选，点击「生成 4 个候选」抽卡。</div>`}
      </div>
    </div></div>`;
  document.body.appendChild(modal);
}
function closeModal() { const m = $("#sbmodal"); if (m) m.remove(); }
async function genCands(shotId) {
  try { await api("/api/shots/" + shotId + "/candidates", { method: "POST" }); closeModal(); await sbOpen(shotId); }
  catch (e) { toast("❌ " + e.message); }
}
/* 剧本编辑器（M2：场次编辑 + 结构健康度） */
async function renderScript() {
  const box = $("#scriptview"); if (!box) return;
  const d = await api("/api/dramas/" + CUR.id + "/script");
  if (!d.scenes || !d.scenes.length) { box.innerHTML = `<div class="muted">尚无剧本，先运行流水线。</div>`; return; }
  const st = d.structure || {}, viol = st.violations || [];
  const beatWindow = (v) => (v >= 0.22 && v <= 0.25) || (v >= 0.48 && v <= 0.52) || (v >= 0.78 && v <= 0.82);
  box.innerHTML = `
    <div class="stats" style="margin-bottom:16px">
      <div class="stat"><div class="k">${d.scenes.length}</div><div class="l">场次</div></div>
      <div class="stat"><div class="k">${esc(d.form)}</div><div class="l">剧集形态</div></div>
      <div class="stat"><div class="k">15/15</div><div class="l">Save the Cat 拍</div></div>
      <div class="stat"><div class="k">${viol.length ? "⚠ " + viol.length : "✓ 0"}</div><div class="l">结构问题</div></div>
    </div>
    <div class="card" style="margin-bottom:16px"><b style="font-size:13px">结构健康度</b>
      <div class="kv" style="grid-template-columns:150px 1fr;font-size:12px;margin-top:8px">
        <div class="k">Plot Point I</div><div>${esc(st.ppi)}（应 0.22–0.25）</div>
        <div class="k">Midpoint</div><div>${esc(st.midpoint)}（应 0.48–0.52）</div>
        <div class="k">Plot Point II</div><div>${esc(st.ppii)}（应 0.78–0.82）</div>
        <div class="k">Truby 四节点</div><div>${(st.truby || []).map(esc).join(" · ")}</div>
      </div>
      ${viol.length ? `<div style="color:var(--bad);margin-top:8px;font-size:12px">${viol.map(esc).join("；")}</div>` : ""}
    </div>
    <div class="muted" style="margin-bottom:8px">场次（点击编辑目标/冲突/结果，M2.5 rewrite）</div>
    <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr))">
      ${d.scenes.map(sc => `<div class="card" style="cursor:pointer" onclick="editScene(${sc.number})">
        <div style="display:flex;justify-content:space-between"><b style="font-size:13px">场 ${sc.number}</b>
          <span class="pill" style="font-size:10px">${esc((sc.beats || [])[0] || "")}</span></div>
        <div class="muted" style="font-size:11px;margin-top:6px;line-height:1.7">目标：${esc(sc.goal)}<br>冲突：${esc(sc.conflict)}<br>结果：${esc(sc.result)}</div></div>`).join("")}
    </div>`;
}
async function editScene(no) {
  const d = await api("/api/dramas/" + CUR.id + "/script");
  const sc = d.scenes.find(x => x.number === no); if (!sc) return;
  const modal = document.createElement("div"); modal.className = "modal"; modal.id = "scmodal";
  modal.innerHTML = `<div class="box" style="max-width:560px">
    <div class="mhead"><h2>编辑 场 ${no}</h2><button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="mbody">
      <div class="muted" style="font-size:12px;margin-bottom:12px">单改纪律：一次只改需要改的字段，改后自动复校验结构。</div>
      <div class="stack">
        <label class="muted" style="font-size:11px">事件</label><input id="s_event" value="${esc(sc.event || "")}">
        <label class="muted" style="font-size:11px">目标</label><input id="s_goal" value="${esc(sc.goal || "")}">
        <label class="muted" style="font-size:11px">冲突</label><input id="s_conflict" value="${esc(sc.conflict || "")}">
        <label class="muted" style="font-size:11px">结果</label><input id="s_result" value="${esc(sc.result || "")}">
        <button class="btn" onclick="saveScene(${no})">保存并复校验</button>
      </div></div></div>`;
  document.body.appendChild(modal);
}
async function saveScene(no) {
  const body = { event: $("#s_event").value, goal: $("#s_goal").value,
                 conflict: $("#s_conflict").value, result: $("#s_result").value };
  try { const r = await api("/api/dramas/" + CUR.id + "/script/scene/" + no, { method: "PUT",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    closeModal();
    toast(r.violations.length ? "⚠ 保存成功，但结构有 " + r.violations.length + " 处问题" : "✅ 已保存，结构合规");
    renderScript();
  } catch (e) { toast("❌ " + e.message); }
}

/* 门禁工作台（AADO 好莱坞级：五门禁署名 + 理由码 + 二元清单） */
async function renderGates() {
  const box = $("#gateview"); if (!box) return;
  const gates = await api("/api/dramas/" + CUR.id + "/gates");
  box.innerHTML = `<div class="muted" style="margin-bottom:12px">五门禁 = 剧本 → 定妆 → 分镜 → 成片 → 母版，每关署名 + 理由码；无署名即视为未通过（D6/EL-10）。</div>
    <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(230px,1fr))">
    ${gates.map(g => `<div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b style="font-size:14px">🚦 ${esc(g.label)}</b>
        <span class="pill ${g.decision === "pending" ? "" : "ok"}">${g.decision === "pending" ? "待签" : "已通过"}</span></div>
      <div class="kv" style="grid-template-columns:88px 1fr;font-size:12px;margin-top:10px">
        <div class="k">署名</div><div>${esc(g.approver)}</div>
        <div class="k">岗位</div><div>${esc(g.role)}</div>
        <div class="k">理由码</div><div>${esc(g.reason_code || "—")}</div>
      </div>
      <div style="margin-top:10px;font-size:11px">${g.checklist.map(c => `<div style="padding:2px 0;color:${c.pass ? "var(--ok)" : "var(--dim)"}">${c.pass ? "✓" : "○"} ${esc(c.item)}</div>`).join("")}</div>
    </div>`).join("")}</div>`;
}

/* 时间线视图（参考 LumenX Timeline / VideoAssembly） */
const SIZE_COLOR = { EWS:"#3b4a63", WS:"#3b4a63", LS:"#41546f", MLS:"#4a5f7d", MS:"#54688a", MCU:"#5e7297", CU:"#6a7ea4", ECU:"#7888ad", OTS:"#5a6d90", POV:"#5a6d90", INSERT:"#4a5f7d" };
async function renderTimeline() {
  const box = $("#tlview"); if (!box) return;
  let d;
  try { d = await api("/api/dramas/" + CUR.id + "/assemble", { method: "POST" }); }
  catch (e) { box.innerHTML = `<div class="muted">${esc(e.message)} · 先在分镜阶段派生镜头表。</div>`; return; }
  const total = d.total_duration;
  const bar = d.timeline.map(sh => {
    const w = (sh.duration / total * 100);
    return `<div title="镜${sh.shot_no} ${sh.size} ${sh.move} ${sh.duration}s" style="flex:0 0 ${w}%;height:44px;background:${SIZE_COLOR[sh.size]||"#4a5f7d"};border-right:1px solid #0a0c10;display:flex;align-items:center;justify-content:center;font-size:9px;color:#cdd7e5;overflow:hidden">${sh.shot_no}</div>`;
  }).join("");
  const markers = d.acts.map(a => `<div style="position:absolute;left:${a.at / total * 100}%;top:-6px;bottom:-20px;border-left:1px dashed var(--gold);font-size:9px;color:var(--gold2);padding-left:3px;white-space:nowrap">${esc(a.name)}</div>`).join("");
  box.innerHTML = `
    <div class="stats" style="margin-bottom:16px">
      <div class="stat"><div class="k">${total}s</div><div class="l">成片时长</div></div>
      <div class="stat"><div class="k">${d.shot_count}</div><div class="l">镜头数</div></div>
      <div class="stat"><div class="k">${d.asl}s</div><div class="l">平均镜头长度 ASL</div></div>
      <div class="stat"><div class="k">${d.asl_in_band ? "✓" : "⚠"}</div><div class="l">ASL 在 2–4s 参考带</div></div>
    </div>
    <h2 style="font-size:13px">时间线 <span class="hint">按镜头时长比例 · 虚线为幕结构标记</span></h2>
    <div style="position:relative;margin-top:18px;margin-bottom:26px">
      <div style="display:flex;height:44px;border-radius:8px;overflow:hidden;border:1px solid var(--line)">${bar}</div>
      ${markers}</div>
    <div class="kv">
      <div class="k">幕结构</div><div>${d.acts.map(a => `${esc(a.name)} @ ${a.at}s`).join(" · ")}</div>
      <div class="k">时间线校验</div><div>${d.violations.length ? `<span style="color:var(--bad)">${d.violations.map(esc).join("；")}</span>` : '<span class="pill ok">无重叠/无空洞 · 通过</span>'}</div>
      <div class="k">交付规格</div><div>${d.deliverable_spec && d.deliverable_spec.master ? `主母版 ${esc(d.deliverable_spec.master)}` : "—"}</div>
    </div>`;
}

async function pickCand(cid, shotId) {
  try { await api("/api/candidates/" + cid + "/select", { method: "POST" }); toast("✅ 已选定"); closeModal(); await sbOpen(shotId); }
  catch (e) { toast("❌ " + e.message); }
}
/* 阶段专属富展示 */
function stageBody(stage, art) {
  // 剧本：场次列表（场次 / 拍 / 目标-冲突-结果）
  if (art.scene_list) {
    return `<div class="muted" style="margin-bottom:10px">形态 <b>${esc(art.form)}</b> · ${art.scenes} 场 · 15 拍覆盖 · Truby 四节点</div>
      <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(190px,1fr))">
      ${art.scene_list.map(sc => `<div class="card"><div style="display:flex;justify-content:space-between">
        <b style="font-size:13px">场 ${sc.no}</b><span class="pill" style="font-size:10px">${esc((sc.beats||[])[0]||"")}</span></div>
        <div class="muted" style="font-size:11px;margin-top:6px;line-height:1.7">
          目标：${esc(sc.goal)}<br>冲突：${esc(sc.conflict)}<br>结果：${esc(sc.result)}</div></div>`).join("")}</div>`;
  }
  // 选角：角色工作台（参考 LumenX CharacterWorkbench / Cast）
  if (art.character && art.anchors) {
    const VIEWNAME = { front: "正面", side: "侧面", back: "背面", "3_4": "3/4 侧", full_body: "全身", expression: "表情" };
    return `<div class="muted" style="margin-bottom:10px">角色定妆 = 后续所有画面的唯一视觉事实来源。锚点图集是与一致性检测（M6）共享的基准。</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px">
        ${art.anchors.map(a => `<div class="asset"><div class="thumb" style="aspect-ratio:3/4;font-size:30px">🎭
          <span class="tag">${esc(VIEWNAME[a] || a)}</span></div>
          <div class="body"><div class="muted" style="font-size:11px">锚点 · ${esc(a)}</div></div></div>`).join("")}
      </div>
      <div class="kv" style="margin-top:16px">
        <div class="k">角色</div><div>${esc(art.character)}</div>
        <div class="k">音色绑定</div><div><span class="pill gold">${esc(art.voice)}</span></div>
        <div class="k">锚点数量</div><div>${art.anchor_count} 张（≥3 达标）</div>
        <div class="k">定妆门禁</div><div><span class="pill ok">署名 + 理由码齐备</span></div>
      </div>`;
  }
  // 一致性：QC 指标卡
  if (art.face_verdict && art.face_threshold !== undefined) {
    return `<div class="stats">
        <div class="stat"><div class="k">${esc(art.face_verdict)}</div><div class="l">人脸一致性判定</div></div>
        <div class="stat"><div class="k">${art.face_threshold}</div><div class="l">通过阈值（余弦）</div></div>
        <div class="stat"><div class="k">${art.same_frame_limit}</div><div class="l">同框角色上限</div></div>
        <div class="stat"><div class="k">${esc(art.axis_check)}</div><div class="l">越轴检查（告警不否决）</div></div>
      </div>
      <div class="muted" style="margin-top:10px">检测方法论：按批次分位截断（低于本集 P10 进复核），绝对阈值仅兜底（D-37）。</div>`;
  }
  // 母版：规格 QC 清单
  if (art.codec && art.tc) {
    return `<div class="kv">
        <div class="k">母版编码</div><div><span class="pill gold">${esc(art.codec)}</span></div>
        <div class="k">音频</div><div>${esc(art.audio)}</div>
        <div class="k">时间码起点</div><div>${esc(art.tc)}</div>
        <div class="k">色彩一致性</div><div>ΔE ${esc(art.color_de)}</div>
        <div class="k">字幕合规</div><div>${esc(art.subtitle_rule)}</div>
        <div class="k">平台拒收项</div><div><span class="pill ok">无硬字幕/无上混/无 letterbox</span></div>
      </div>`;
  }
  // 成本：预算与北极星
  if (art.budget && art.warn_level) {
    return `<div class="stats">
        <div class="stat"><div class="k">¥${art.budget}</div><div class="l">项目预算上限</div></div>
        <div class="stat"><div class="k">¥${art.reserved}</div><div class="l">已预占</div></div>
        <div class="stat"><div class="k">${esc(art.warn_level)}</div><div class="l">预算预警级别</div></div>
        <div class="stat"><div class="k">${art.duplicate_paid}</div><div class="l">重复付费调用</div></div>
      </div>
      <div class="muted" style="margin-top:10px">北极星指标：可交付母版分钟数 ÷ 总成本；超预算硬阻断，不静默超支。</div>`;
  }
  // 交付：交付单视图
  if (art.spec && art.release) {
    return `<div style="margin-bottom:12px"><button class="btn" onclick="downloadSheet()">⬇ 下载交付单（JSON）</button></div>
      <div class="kv">
        <div class="k">交付画幅</div><div><span class="pill gold">${esc(art.spec)}</span></div>
        <div class="k">分发放行</div><div><span class="pill ok">${esc(art.release)}</span></div>
        <div class="k">可选交付标注</div><div>保证 / 可选 / 需确认（EL-11）</div>
        <div class="k">交付单字段</div><div>规格 · 版本 · 时长 · QC 结论 · 权利 · AI 标识 · 分级 · 语言 · 色彩标签（齐备）</div>
      </div>`;
  }
  // 通用 KV
  if (Object.keys(art).length) {
    return `<div class="kv">${Object.entries(art).map(([k, v]) =>
      `<div class="k">${esc(k)}</div><div>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</div>`).join("")}</div>`;
  }
  return `<div class="muted">无附加产物。</div>`;
}
async function produceAll(id) {
  const b = $("#prodbtn"); b.disabled = true; b.textContent = "制作中…（流水线→分镜→抽卡→组装）";
  try { const r = await api("/api/dramas/" + id + "/produce", { method: "POST" });
    toast("🎬 完成：" + r.stages_passed + "/" + r.stages_total + " 阶段 · " + r.shots + " 镜 · 成片 " + r.total_duration + "s");
    CUR.stage = null; viewProject(id);
  } catch (e) { toast("❌ " + e.message); }
  b.disabled = false; b.textContent = "🎬 一键全流程";
}
async function runPipeline(id) {
  const b = $("#runbtn"); b.disabled = true; b.textContent = "运行中…";
  try { const r = await api("/api/dramas/" + id + "/run", { method: "POST" });
    toast("✅ 流水线完成 " + r.summary.passed + "/" + r.summary.total); CUR.stage = null; viewProject(id);
  } catch (e) { toast("❌ " + e.message); b.disabled = false; b.textContent = "▶ 运行流水线"; }
}

/* ---------- 资产库 ---------- */
async function viewAssets() {
  const projs = await api("/api/dramas");
  const chars = [], shots = [];
  for (const p of projs.slice(0, 12)) {
    try { const d = await api("/api/dramas/" + p.id);
      if (d.last_run) {
        const c = d.last_run.stages.find(x => x.stage === "M3 选角");
        if (c && c.artifact && c.artifact.character)
          chars.push({ project: p.title, name: c.artifact.character, voice: c.artifact.voice, anchors: c.artifact.anchors });
      }
      const sh = await api("/api/dramas/" + p.id + "/shots");
      sh.forEach(x => shots.push({ project: p.title, ...x }));
    } catch (e) {}
  }
  const VIEWNAME = { front: "正面", side: "侧面", back: "背面", "3_4": "3/4", full_body: "全身", expression: "表情" };
  setMain({
    top: `<h1>资产库 <span class="crumbs">跨项目角色与镜头</span></h1>
      <div class="right"><span class="pill">${chars.length} 角色</span><span class="pill">${shots.length} 镜头</span></div>`,
    body: `${chars.length ? `<h2>角色 <span class="hint">定妆锚点 + 音色</span></h2>
      <div class="cards">${chars.map(c => `<div class="asset"><div class="thumb" style="font-size:34px">🎭<span class="tag">${esc(c.project)}</span></div>
        <div class="body"><h4>${esc(c.name)}</h4>
          <div class="meta"><span>音色 ${esc(c.voice)}</span>${(c.anchors||[]).map(a => `<span>${esc(VIEWNAME[a]||a)}</span>`).join("")}</div></div></div>`).join("")}</div>` : ""}
      ${shots.length ? `<h2>镜头 <span class="hint">按状态</span></h2>
      <div class="cards">${shots.slice(0, 60).map(s => `<div class="asset"><div class="thumb" style="font-size:28px">${s.status === "已生成" || s.status === "已选定" ? "🖼️" : "🎞️"}
        <span class="tag">${esc(s.project)} · 镜${s.shot_no}</span></div>
        <div class="body"><div class="meta"><span>${esc(s.size)}</span><span>${esc(s.move)}</span><span>${s.duration}s</span>
          <span class="pill ${s.status === "已生成" || s.status === "已选定" ? "ok" : ""}" style="font-size:10px">${esc(s.status)}</span></div></div></div>`).join("")}</div>` : ""}
      ${(!chars.length && !shots.length) ? `<div class="card empty">还没有资产。先在项目里运行流水线。</div>` : ""}`,
  }, true);
}

/* ---------- 任务队列（PG SKIP LOCKED 队列的运维视图） ---------- */
const JOB_STATUS_COLOR = { queued: "muted", running: "gold", completed: "ok", failed: "bad", waiting_human: "gold", retry_exhausted: "bad", cancelled: "muted" };
async function viewJobs() {
  const projs = await api("/api/dramas");
  let jobs = [];
  for (const p of projs.slice(0, 10)) {
    try { const js = await api("/api/dramas/" + p.id + "/jobs"); js.forEach(j => jobs.push({ project: p.title, ...j })); } catch (e) {}
  }
  jobs.sort((a, b) => b.id - a.id);
  setMain({
    top: `<h1>任务 <span class="crumbs">PG 队列 · 幂等 + 租约 + checkpoint</span></h1><div class="right"><span class="pill">${jobs.length} 个任务</span></div>`,
    body: `<div class="card">
      <div class="stack" style="max-width:520px">
        <div class="row2"><input id="job_pid" placeholder="项目 ID"><select id="job_type">
          <option value="adapt">剧本开发</option><option value="casting">选角定妆</option>
          <option value="shot_video">镜头生成</option><option value="generate_voice">配音</option><option value="music">配乐</option></select></div>
        <div><button class="btn" onclick="submitJob()">入队任务</button></div>
      </div></div>
    <h2>任务列表</h2>
    ${jobs.length ? `<div class="card"><table><thead><tr><th>#</th><th>项目</th><th>类型</th><th>状态</th><th>操作</th></tr></thead><tbody>
      ${jobs.map(j => `<tr><td>${j.id}</td><td>${esc(j.project)}</td><td>${esc(j.type)}</td>
        <td><span class="pill ${JOB_STATUS_COLOR[j.status] || "muted"}">${esc(j.status)}</span></td>
        <td>${j.status === "failed" ? `<button class="btn ghost sm" onclick="jobRetry(${j.id})">重试</button>` : "—"}</td></tr>`).join("")}
      </tbody></table></div>` : `<div class="card empty">还没有任务。先提交一个，或运行流水线。</div>`}`,
  }, true);
}
async function submitJob() {
  const pid = ($("#job_pid") || {}).value, type = ($("#job_type") || {}).value;
  if (!pid) return toast("填项目 ID");
  try { await api("/api/drama-jobs", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: pid, type: type, idempotency_key: pid + ":" + type + ":" + Date.now() }) });
    toast("✅ 已入队"); viewJobs();
  } catch (e) { toast("❌ " + e.message); }
}
async function jobRetry(id) {
  try { await api("/api/drama-jobs/" + id + "/retry", { method: "POST" }); toast("✅ 已重试"); viewJobs(); }
  catch (e) { toast("❌ " + e.message); }
}

async function downloadSheet() {
  try {
    const d = await api("/api/dramas/" + CUR.id + "/delivery-sheet");
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = (d.project.title || "project") + "_delivery_sheet.json"; a.click();
    URL.revokeObjectURL(url); toast("✅ 交付单已下载");
  } catch (e) { toast("❌ " + e.message); }
}

/* ---------- 生成台 Playground（参考 LumenX Playground） ---------- */
let PG_KIND = "图像生成";
async function viewPlayground() {
  const d = await api("/api/playground/kinds");
  const tasks = await api("/api/playground/tasks");
  setMain({
    top: `<h1>生成台 <span class="crumbs">独立生成工具台 · 即开即用</span></h1><div class="right"><span class="pill">${tasks.length} 次生成</span></div>`,
    body: `
    <div class="card">
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">
        ${d.kinds.map(k => `<span class="pill ${k === PG_KIND ? "gold" : ""}" style="cursor:pointer" onclick="PG_KIND='${k}';viewPlayground()">${k}</span>`).join("")}</div>
      <div class="stack">
        <textarea id="pg_prompt" rows="3" placeholder="输入提示词（无凭据时走 Mock，仍会记录任务）"></textarea>
        <div><button class="btn" onclick="pgGenerate()">生成「${PG_KIND}」</button></div>
      </div>
    </div>
    <h2>生成历史 <span class="hint">最近 50 次</span></h2>
    ${tasks.length ? `<div class="cards">${tasks.map(t => `
      <div class="asset"><div class="thumb" style="font-size:28px">${({ "图像生成":"🖼️","文生视频":"🎬","图生视频":"🎞️","参考生视频":"🎥","配音":"🎙️","配乐":"🎵" }[t.kind] || "🧪")}
        <span class="tag">${esc(t.kind)}</span></div>
        <div class="body"><div class="desc">${esc(t.prompt)}</div>
          <div class="meta"><span>${esc(t.model)}</span><span class="pill ok" style="font-size:10px">${esc(t.status)}</span></div></div></div>`).join("")}</div>`
      : `<div class="card empty">还没有生成记录。选一个模式，输入提示词试试。</div>`}`,
  }, true);
}
async function pgGenerate() {
  const prompt = ($("#pg_prompt") || {}).value || "";
  if (!prompt.trim()) return toast("请输入提示词");
  try { await api("/api/playground/generate", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: PG_KIND, prompt }) });
    toast("✅ 已生成"); viewPlayground();
  } catch (e) { toast("❌ " + e.message); }
}

/* ---------- 模型 ---------- */
async function viewModels() {
  const d = await api("/api/models/config");
  setMain({
    top: `<h1>模型配置 <span class="crumbs">填 model + Key 走真实供应商，缺一走 Mock</span></h1>
      <div class="right"><a href="/models"><button class="btn ghost sm">编辑配置</button></a></div>`,
    body: `<div class="cards">${Object.entries(d.config).map(([k, c]) => {
      const on = c.model && c.api_key;
      return `<div class="asset"><div class="thumb" style="font-size:30px">${({ text: "📝", video: "🎥", image: "🖼️", tts: "🎙️", music: "🎵", lipsync: "👄" }[k]) || "🔌"}</div>
        <div class="body"><h4 style="display:flex;justify-content:space-between">${k}
          <span class="pill ${on ? "ok" : ""}">${on ? "已配置" : "Mock"}</span></h4>
          <div class="desc">${esc(c.model || "未填模型")}</div></div></div>`;
    }).join("")}</div>
    <h2>电影参数能力矩阵 <span class="hint">M17.1-F04：参数缺失不得默认「支持」</span></h2>
    <div class="card" style="padding:0"><table>
      <thead><tr><th>能力维度</th><th>说明</th></tr></thead><tbody>
      ${(d.capabilities || []).map(c => `<tr><td><code>${esc(c)}</code></td><td>${esc({
        reference_image: "参考图（r2v 多参考，角色一致性命门）",
        reference_video: "参考视频", first_last_frame: "首尾帧（衔接镜）",
        multi_shot: "多镜头一次调用", camera_control: "运镜枚举与相机控制",
        focal_dof: "焦距与景深模拟", resolution_aspect: "分辨率与画幅",
        native_audio: "原生音频", duration: "时长上限", cost: "单位成本", latency: "平均耗时",
      }[c] || c)}</td></tr>`).join("")}
      </tbody></table></div>
    <h2>路由与许可</h2>
    <div class="kv">
      <div class="k">关键镜路由</div><div>${esc((d.routing || {}).hero || "")}</div>
      <div class="k">氛围镜路由</div><div>${esc((d.routing || {}).ambient || "")}</div>
      <div class="k">不得内置分发</div><div>${((d.licenses || {}).bundle_forbidden || []).map(x => `<span class="pill bad">${esc(x)}</span>`).join(" ")}</div>
      <div class="k">非商用模型</div><div>${((d.licenses || {}).non_commercial || []).map(x => `<span class="pill bad">${esc(x)}</span>`).join(" ")}</div>
    </div>`,
  });
}

/* ---------- 设置 ---------- */
function viewSettings() {
  setMain({
    top: `<h1>设置 <span class="crumbs">账户与系统</span></h1>`,
    body: `<div class="card"><div class="kv">
        <div class="k">登录账户</div><div>admin</div>
        <div class="k">API 文档</div><div><a href="/docs" target="_blank">/docs</a></div>
        <div class="k">健康检查</div><div><a href="/health" target="_blank">/health</a></div>
      </div><div style="margin-top:18px"><button class="btn ghost" onclick="logout()">退出登录</button></div></div>`,
  });
}

/* ---------- 启动 ---------- */
function boot() { if (!hasToken()) return renderLogin(); go("overview"); }
boot();
