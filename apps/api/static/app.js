/* AADO 控制台 SPA —— 路由 / 项目工作台 / 阶段步骤条 / 资产网格 */
const TK = "aado_token";
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hasToken = () => !!localStorage.getItem(TK);

/* 19 个模块阶段的展示元数据（与后端 pipeline 的 stage 名对应） */
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
  ["models", "模型", "🎛️"], ["settings", "设置", "⚙️"],
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
    <h2>流程覆盖 <span class="hint">19 个模块 · 端到端</span></h2>
    <div class="card" style="line-height:2">${STAGES.map(s => `<span class="pill" style="margin:3px">${s[2]} ${s[1]}</span>`).join("")}</div>
    <h2>最近项目 <span class="hint">进入工作台运行流水线</span></h2>
    ${projs.length ? `<div class="cards">${projs.slice(0, 6).map(projectCard).join("")}</div>`
      : `<div class="card empty">还没有项目。到「项目」页创建第一部剧。</div>`}`,
  });
}
function projectCard(p) {
  return `<div class="card click" onclick="go('project:${p.id}')">
    <div style="display:flex;justify-content:space-between;align-items:start">
      <h4 style="margin:0 0 6px;font-size:15px">${esc(p.title)}</h4>
      <span class="pill ${p.status === "draft" ? "" : "gold"}">${esc(p.status || "draft")}</span></div>
    <div class="muted" style="font-size:12px;min-height:32px">${esc(p.logline || "")}</div>
    <div class="muted" style="font-size:11px;margin-top:8px">${p.episodes || 6} 集 × ${p.minutes || 30} 分钟</div></div>`;
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
    <h2>全部项目</h2>
    ${projs.length ? `<div class="cards">${projs.map(projectCard).join("")}</div>` : `<div class="card empty">暂无项目</div>`}`,
  });
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

  const stepper = STAGES.map(([name, label, ic]) => {
    const st = byName[name];
    const cls = st ? (st.status === "passed" ? "ok" : "bad") : "";
    const txt = st ? (st.status === "passed" ? "通过" : "失败") : (run ? "—" : "待运行");
    return `<div class="step ${CUR.stage === name ? "on" : ""}" onclick="pickStage('${name}')">
      <div class="n">${ic} ${label}</div><div class="t">${name.replace(/^M\d+ /, "")}</div>
      <div class="s">${st ? `<i class="dot ${cls}"></i> ${txt}` : txt}</div></div>`;
  }).join("");

  const passed = run ? run.summary.passed : 0, total = 19;
  setMain({
    top: `<h1><span class="crumbs" style="cursor:pointer" onclick="go('projects')">项目 ›</span> <span class="t">${esc(p.title)}</span></h1>
      <div class="right">
        <span class="pill">${p.episodes} 集 × ${p.minutes} 分钟</span>
        <span class="pill gold">${esc(p.rating || "")} · ${esc(p.genre || "")}</span>
        <button class="btn" id="runbtn">▶ 运行流水线</button></div>`,
    body: `
    <div class="card">
      <div class="kv">
        <div class="k">Logline</div><div>${esc(p.logline)}</div>
        <div class="k">目标平台</div><div>${esc(p.platform || "—")}</div>
        <div class="k">交付规格</div><div>${(p.delivery_spec && p.delivery_spec.master) ? `主母版 ${p.delivery_spec.master} · 平台版 ${p.delivery_spec.platform} · 竖屏 ${p.delivery_spec.derived}` : "—"}</div>
        <div class="k">流水线</div><div>${run ? `<span class="pill ${run.summary.deliverable ? "ok" : "bad"}">${passed}/${total} 阶段通过 ${run.summary.deliverable ? "· 可交付" : ""}</span>` : `<span class="pill">尚未运行</span>`}</div>
      </div>
    </div>
    <h2>制作流程 <span class="hint">点击阶段查看成果</span></h2>
    <div class="stepper">${stepper}</div>
    <div id="stagedetail"></div>`,
  }, true);
  $("#runbtn").onclick = () => runPipeline(id);
  renderStageDetail(byName[CUR.stage]);
  window.pickStage = (n) => { CUR.stage = n; viewProject(id); };
}
function renderStageDetail(st) {
  const el = $("#stagedetail"); if (!el) return;
  if (!st) { el.innerHTML = `<div class="detail empty">该阶段尚无运行结果，点击「运行流水线」生成。</div>`; return; }
  const meta = STAGES.find(s => s[0] === st.stage) || ["", "", ""];
  const art = st.artifact || {};
  const head = `<div class="head"><h2 style="margin:0">${meta[2]} ${st.stage}</h2>
      <span class="pill ${st.status === "passed" ? "ok" : "bad"}">${st.status === "passed" ? "✓ 通过" : "✗ 失败"}</span></div>`;
  const viol = (st.violations && st.violations.length) ? `<div style="margin-top:12px;color:var(--bad)">违规：${st.violations.map(esc).join("；")}</div>` : "";
  el.innerHTML = `<div class="detail">${head}${stageBody(st.stage, art)}${viol}</div>`;
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
  // 选角：角色卡 + 锚点视角 chip
  if (art.character && art.anchors) {
    return `<div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">
      <div class="asset"><div class="thumb" style="font-size:40px">🎭<span class="tag">角色</span></div>
        <div class="body"><h4>${esc(art.character)}</h4>
          <div class="meta"><span>音色 ${esc(art.voice)}</span><span>${art.anchor_count} 张锚点</span>
          ${art.anchors.map(a => `<span>${esc(a)}</span>`).join("")}</div></div></div></div>`;
  }
  // 通用 KV
  if (Object.keys(art).length) {
    return `<div class="kv">${Object.entries(art).map(([k, v]) =>
      `<div class="k">${esc(k)}</div><div>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</div>`).join("")}</div>`;
  }
  return `<div class="muted">无附加产物。</div>`;
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
  let cards = [];
  for (const p of projs.slice(0, 12)) {
    try { const d = await api("/api/dramas/" + p.id); if (d.last_run) {
      // 从阶段产物里提取「资产类」信息（有 artifact 的阶段）
      d.last_run.stages.forEach(s => {
        if (Object.keys(s.artifact || {}).length && /选角|摄影|配音|配乐|剧本|母版/.test(s.stage))
          cards.push({ project: p.title, stage: s.stage, art: s.artifact });
      });
    } } catch (e) {}
  }
  setMain({
    top: `<h1>资产库 <span class="crumbs">各项目阶段产物</span></h1><div class="right"><span class="pill">${cards.length} 项</span></div>`,
    body: cards.length ? `<div class="cards">${cards.map(c => `
      <div class="asset"><div class="thumb">🎞️<span class="tag">${esc(c.stage)}</span></div>
        <div class="body"><h4>${esc(c.project)}</h4>
          <div class="meta">${Object.entries(c.art).map(([k, v]) => `<span>${esc(k)}: ${esc(v)}</span>`).join("")}</div></div></div>`).join("")}</div>`
      : `<div class="card empty">还没有资产。先在项目里运行流水线。</div>`,
  }, true);
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
    }).join("")}</div>`,
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
