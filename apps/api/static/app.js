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
  ["M1 立项", "立项", "doc"], ["M2 剧本", "剧本", "doc"], ["M3 选角", "选角", "face"],
  ["M4 分镜", "分镜", "frame"], ["M5 摄影", "摄影", "film"], ["M6 一致性", "一致性", "users"],
  ["M7 配音", "配音", "wave"], ["M8 配乐", "配乐", "music"], ["M9 剪辑", "剪辑", "scissors"],
  ["M10 门禁", "门禁", "gate"], ["M11 母版", "母版", "master"], ["M12 交付", "交付", "box"],
  ["M14 成本", "成本", "pulse"], ["M15 存储", "存储", "layers"], ["M16 协作", "协作", "users"],
  ["M17 供应商", "供应商", "route"], ["M18 合规", "合规", "scales"], ["M19 VFX", "VFX", "sparkle"],
  ["M13 任务", "任务", "clock"],
];

/* ---------- 请求 ---------- */
/* C8：GET 请求短 TTL 缓存 + 在途去重；写操作后整体失效 */
const _apiCache = new Map();
const _apiInflight = new Map();
const API_TTL_MS = 2500;
const API_TIMEOUT_MS = 20000;
function apiErrorText(d, status) {
  const det = d && d.detail;
  if (typeof det === "string") return det;
  if (det) return JSON.stringify(det);
  return "HTTP " + status;
}
async function api(path, opt) {
  opt = opt || {};
  const method = (opt.method || "GET").toUpperCase();
  if (method === "GET") {
    const hit = _apiCache.get(path);
    if (hit && Date.now() - hit.t < API_TTL_MS) return hit.v;
    if (_apiInflight.has(path)) return _apiInflight.get(path);
  }
  opt.headers = Object.assign({}, opt.headers || {}, hasToken() ? { Authorization: "Bearer " + localStorage.getItem(TK) } : {});
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT_MS);
  const p = (async () => {
    let r;
    try { r = await fetch(path, Object.assign({}, opt, { signal: ctrl.signal })); }
    catch (e) {
      if (e && e.name === "AbortError") throw new Error("请求超时（" + API_TIMEOUT_MS / 1000 + " 秒），请重试");
      throw new Error("网络错误，请检查服务是否运行");
    } finally { clearTimeout(timer); }
    if (r.status === 401) { logout(); throw new Error("未授权"); }
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(apiErrorText(d, r.status));
    return d;
  })();
  if (method === "GET") {
    _apiInflight.set(path, p);
    try {
      const v = await p;
      _apiCache.set(path, { t: Date.now(), v });
      return v;
    } finally { _apiInflight.delete(path); }
  }
  _apiCache.clear();           // 写操作后失效全部缓存
  _apiInflight.clear();
  return p;
}
function skeleton(n) {
  const m = $("#main");
  if (!m) return;
  m.innerHTML = `<div class="topbar"><div class="skeleton" style="width:180px;height:20px"></div></div>
    <div class="view"><div class="skeleton" style="width:120px;height:16px"></div>
    <div class="cards">${Array.from({length: n || 6}, () => '<div class="skeleton card"></div>').join("")}</div></div>`;
}
function applyTheme() {
  const t = localStorage.getItem("aado_theme") || "light";
  document.body.classList.toggle("dark", t === "dark");
}
function toggleTheme() {
  const t = (localStorage.getItem("aado_theme") === "dark") ? "light" : "dark";
  localStorage.setItem("aado_theme", t); applyTheme();
  toast("主题：" + (t === "dark" ? "深色" : "浅色"));
}
document.addEventListener("keydown", e => {
  if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) { e.preventDefault(); openCommand(); return; }
  if (e.key === "Escape") { const m = document.querySelector(".modal"); if (m) m.remove(); }
  if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || "")) {
    const s = $("#psearch"); if (s) { e.preventDefault(); s.focus(); }
  }
});
function confirmDialog(title, desc, onOk, okLabel) {
  const m = document.createElement("div"); m.className = "modal"; m.id = "cfm";
  m.innerHTML = `<div class="box" style="max-width:420px">
    <div class="mhead"><h2>${esc(title)}</h2></div>
    <div class="mbody"><div class="muted" style="margin-bottom:16px">${esc(desc)}</div>
      <div style="display:flex;gap:10px"><button class="btn" id="cfm_ok">${esc(okLabel || "确认")}</button>
        <button class="btn ghost" onclick="closeModal()">取消</button></div></div></div>`;
  document.body.appendChild(m);
  m.querySelector("#cfm_ok").onclick = () => { closeModal(); onOk(); };
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
    <div class="brand"><div class="mark">${ico("film")}</div><div><div class="name">AADO</div>
      <div class="sub">AI Drama Odyssey</div></div></div>
    <div style="display:flex;flex-direction:column;gap:12px">
      <input name="username" placeholder="用户名" value="admin">
      <input name="password" type="password" placeholder="密码" autofocus>
      <button class="btn" type="submit">登 录</button>
      <div id="lerr" class="muted hide" style="color:var(--bad);font-size:var(--fs-sm)"></div>
    </div></form></div>`;
  $("#lf").onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target);
    const r = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: f.get("username"), password: f.get("password") }) });
    if (r.ok) { const d = await r.json(); localStorage.setItem(TK, d.token); boot(); }
    else { const x = $("#lerr"); x.classList.remove("hide"); x.textContent = "用户名或密码错误"; }
  };
}

/* ---------- SVG 图标（无 emoji，线宽统一） ---------- */
const ICONS = {
  home:'<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
  film:'<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
  sparkle:'<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="M12 8.5 13.6 12 12 15.5 10.4 12z"/><circle cx="12" cy="12" r="1.4"/>',
  lab:'<path d="M9 3h6M10 3v6l-4.5 8.2A2 2 0 0 0 7.3 21h9.4a2 2 0 0 0 1.8-2.8L14 9V3"/><path d="M7.5 15h9"/>',
  list:'<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r="1.2"/><circle cx="3.5" cy="12" r="1.2"/><circle cx="3.5" cy="18" r="1.2"/>',
  sliders:'<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  gear:'<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v2.4M12 19.1v2.4M4.2 7l2.1 1.2M17.7 15.8l2.1 1.2M4.2 17l2.1-1.2M17.7 8.2l2.1-1.2"/>',
  play:'<path d="M7 4.5 19 12 7 19.5z"/>',
  download:'<path d="M12 3v12M7.5 10.5 12 15l4.5-4.5M4 20h16"/>',
  shield:'<path d="M12 3 5 6v6c0 4.2 3 7.6 7 9 4-1.4 7-4.8 7-9V6z"/><path d="M9.2 12l2 2 3.6-3.6"/>',
  check:'<path d="M4.5 12.5 10 18 19.5 6.5"/>',
  x:'<path d="M6 6l12 12M18 6 6 18"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  face:'<circle cx="12" cy="12" r="9"/><path d="M9 10h.01M15 10h.01M8.5 15c1 1 2.2 1.5 3.5 1.5S14.5 16 15.5 15"/>',
  frame:'<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M3.5 14.5h17"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/>',
  layers:'<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
  pulse:'<path d="M3 12h4l2.5-6 4 12 2.5-6h5"/>',
  box:'<path d="M12 3 4 7v10l8 4 8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/>',
  users:'<circle cx="9" cy="8" r="3"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0"/><path d="M16 5.5a3 3 0 0 1 0 5.8M17 20a5.5 5.5 0 0 0-2-4.2"/>',
  scales:'<path d="M12 4v16M7 20h10M6 7h12M6 7 3.5 13h5zM18 7l-2.5 6h5z"/>',
  wand:'<path d="M4 20 15 9M14 4l1 2 2 1-2 1-1 2-1-2-2-1 2-1zM19 12l.7 1.3L21 14l-1.3.7L19 16l-.7-1.3L17 14l1.3-.7z"/>',
  doc:'<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 13h6M9 17h6"/>',
  music:'<circle cx="7" cy="17.5" r="2.5"/><circle cx="17" cy="15.5" r="2.5"/><path d="M9.5 17.5V7l10-2v10.5"/>',
  wave:'<path d="M3 12h2l2-5 3 10 3-7 2 4h6"/>',
  scissors:'<circle cx="6.5" cy="7" r="2.5"/><circle cx="6.5" cy="17" r="2.5"/><path d="M8.7 8.7 20 18M8.7 15.3 20 6"/>',
  gate:'<path d="M5 21V6l7-3 7 3v15"/><path d="M9 21v-6h6v6"/>',
  master:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M7 5v4M11 5v4M15 5v4"/>',
  inbox:'<path d="M3 12h5l1.5 3h5L16 12h5"/><path d="M4 5h16l1 7v6H3v-6z"/>',
  route:'<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.5 6h5a4 4 0 0 1 4 4v5.5"/>',
};
function ico(name, cls) {
  const p = ICONS[name] || ICONS.box;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" ` +
    `stroke-linecap="round" stroke-linejoin="round"${cls ? ` class="${cls}"` : ""}>${p}</svg>`;
}

/* ---------- 外壳（带文字标签的侧边栏） ---------- */
const NAV = [
  ["制作", [["overview","概览","home"],["projects","项目","film"]]],
  ["资产", [["assets","资产库","layers"],["playground","生成台","lab"]]],
  ["运行", [["jobs","任务","list"]]],
  ["系统", [["models","模型","sliders"],["settings","设置","gear"]]],
];
function shell(active) {
  document.body.innerHTML = `<aside class="sidebar" id="sidebar">
      <div class="brand"><div class="mark">${ico("film")}</div>
        <div><div class="name">AADO</div><div class="sub">Drama Odyssey</div></div></div>
      <nav class="nav">${NAV.map(([sec, items]) => `<div class="nav-sec">
        <div class="nav-label">${sec}</div>
        ${items.map(([id, l, ic]) => `<div class="nav-item ${id === active ? "on" : ""}" data-go="${id}">${ico(ic)}<span>${l}</span></div>`).join("")}
      </div>`).join("")}</nav>
      <div class="side-foot"><div class="dotline"><i class="dot ok"></i>服务运行中</div>
        <div>好莱坞级 AI 短剧流水线</div></div>
    </aside>
    <div class="main" id="main"></div>`;
  $$("[data-go]").forEach(el => el.onclick = () => go(el.dataset.go));
}
function setMain(html, wide) {
  const m = $("#main");
  if (!m) return;
  let top = String(html.top || "");
  const helpBtn = `<button class="help-btn bell-btn" title="待办与通知" id="bell" onclick="openNotifications()">${ico("pulse")}<span class="bell-count hide" id="bellcount"></span></button>` +
    `<button class="help-btn" title="使用指南" onclick="openHelp()">?</button>`;
  if (top.includes("</div>")) {
    const i = top.lastIndexOf("</div>");
    top = top.slice(0, i) + helpBtn + top.slice(i);
  } else {
    top = `<div class="right">${helpBtn}</div>` + top;
  }
  const title = html.title ? `<span class="topbar-title">${html.title}</span>` : "";
  m.innerHTML = `<div class="topbar">${title}${top}</div><div class="view ${wide ? "wide" : ""}">${html.body}</div>`;
  refreshBell();
}
async function refreshBell() {
  try {
    const d = await api("/api/notifications");
    const el = $("#bellcount"); if (!el) return;
    if (d.count > 0) { el.textContent = d.count > 99 ? "99+" : d.count; el.classList.remove("hide"); }
    else el.classList.add("hide");
  } catch (e) {
    const b = $("#bell");
    if (b) b.title = "待办加载失败：" + e.message + "（点击重试）";
  }
}
async function openNotifications() {
  let d; try { d = await api("/api/notifications"); } catch (e) { return toast("加载失败：" + e.message); }
  const modal = document.createElement("div"); modal.className = "modal"; modal.id = "notifmodal";
  const items = d.items || [];
  modal.innerHTML = `<div class="box" style="max-width:560px">
    <div class="mhead"><h2>待办与通知</h2><button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="mbody">
      ${items.length ? items.map(it => `<div class="notif-item" onclick="closeModal();go('project:${it.link_project}')">
        <span class="pill ${it.severity === "bad" ? "bad" : "gold"}">${esc(it.title)}</span>
        <div class="notif-detail">${esc(it.detail)}</div></div>`).join("")
        : `<div class="empty">${ico("check")}<div>没有待办，一切正常</div></div>`}
    </div></div>`;
  document.body.appendChild(modal);
}
/* E1：hash 深链（#/project/12/M4%20%E5%88%86%E9%95%9C），刷新/分享/前进后退不丢视图 */
const ROUTE_NAMES = new Set(["overview", "projects", "project", "assets", "playground", "jobs", "models", "settings"]);
const SKELETON_ROUTES = new Set(["overview", "projects", "project", "assets", "playground", "jobs", "models"]);
let _settingHash = false;
function hashFor(name, param, stage) {
  if (name === "project") return "#/project/" + encodeURIComponent(param) + (stage ? "/" + encodeURIComponent(stage) : "");
  return "#/" + encodeURIComponent(name);
}
function decodePart(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }
function parseHash() {
  const raw = String(location.hash || "").replace(/^#\/?/, "");
  if (!raw) return { name: "overview" };
  const parts = raw.split("/").map(decodePart);
  if (parts[0] === "project") {
    if (!parts[1]) return { name: "__notfound" };
    return { name: "project", param: parts[1], stage: parts[2] || null };
  }
  if (ROUTE_NAMES.has(parts[0])) return { name: parts[0] };
  return { name: "__notfound" };
}
function syncHash(h) {
  if (location.hash === h) return;
  _settingHash = true;
  location.hash = h;
}
function replaceHash(h) {
  if (location.hash === h) return;
  try { history.replaceState(null, "", h); } catch (e) {}
}
function viewError(e, retry) {
  const msg = (e && e.message) ? e.message : String(e);
  setMain({
    title: "出错了",
    body: `<div class="card empty">${esc(msg)}<div style="margin-top:16px"><button class="btn" id="retrybtn">重试</button></div></div>`,
  });
  const btn = $("#retrybtn"); if (btn && retry) btn.onclick = retry;
}
async function go(route) {
  const parts = String(route).split(":");
  const name = parts[0], param = parts[1];
  syncHash(hashFor(name, param));
  try { return await navigate(name, param); }
  catch (e) { viewError(e, () => go(route)); }
}
async function navigate(name, param) {
  stopJobsPoll();
  if (name === "__notfound") {
    shell("overview");
    setMain({
    title: "页面未找到",
      body: `<div class="card empty">${ico("x")}<div>没有这个页面</div>
        <div class="muted" style="font-size:var(--fs-sm);margin-top:4px">检查地址，或回到概览继续操作</div>
        <div style="margin-top:16px"><button class="btn" onclick="go('overview')">回到概览</button></div></div>`,
    });
    return;
  }
  shell(name === "project" ? "projects" : name);
  if (SKELETON_ROUTES.has(name)) skeleton();
  return routeView(name, param);
}
async function routeView(name, param) {
  if (name === "overview") return viewOverview();
  if (name === "projects") return viewProjects();
  if (name === "project") return viewProject(param);
  if (name === "assets") return viewAssets();
  if (name === "playground") return viewPlayground();
  if (name === "jobs") return viewJobs();
  if (name === "models") return viewModels();
  if (name === "settings") return viewSettings();
  return navigate("__notfound");
}
window.addEventListener("hashchange", () => {
  if (_settingHash) { _settingHash = false; return; }
  if (!hasToken()) return renderLogin();
  const r = parseHash();
  if (r.name === "project") CUR.stage = r.stage || null;
  const retry = () => navigate(r.name, r.name === "project" ? r.param : undefined);
  retry().catch(viewError);
});

/* ---------- 概览 ---------- */
async function viewOverview() {
  const [cfg, projs] = await Promise.all([api("/api/models/config"), api("/api/dramas")]);
  const configured = cfg.available.length;
  setMain({
    title: "概览",
    top: `<div class="right"><span class="pill ok"><i class="dot ok"></i>服务运行中</span>
      <span class="pill ${configured ? "gold" : ""}">${configured ? configured + " 个模型已配置" : "Mock 模式"}</span></div>`,
    body: `
    <div class="stats">
      <div class="stat"><div class="k">19</div><div class="l">流程模块</div></div>
      <div class="stat"><div class="k">${configured}</div><div class="l">已配置模型</div></div>
      <div class="stat"><div class="k">${projs.length}</div><div class="l">项目</div></div>
    </div>
    <h2>制作流程</h2>
    <div class="card">
      ${SEGMENTS.map(([seg, mods]) => `<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--line)">
        <div style="flex:0 0 150px;font-size:var(--fs-sm);color:var(--accent)">${seg}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">${mods.map(m => {
          const meta = STAGES.find(x => x[0] === m) || ["", m, ""];
          return `<span class="pill" style="font-size:var(--fs-meta)">${meta[1]}</span>`; }).join("")}</div></div>`).join("")}
    </div>
    <h2>最近项目</h2>
    ${projs.length ? `<div class="cards">${projs.slice(0, 6).map(projectCard).join("")}</div>`
      : `<div class="card empty">${ico("film")}<div>还没有项目</div>
        <div class="muted" style="font-size:var(--fs-sm);margin-top:6px">30 秒体验：一键创建示例项目并跑完 19 阶段</div>
        <div style="margin-top:14px"><button class="btn" onclick="seedDemo()">创建示例项目</button>
        <button class="btn ghost" style="margin-left:8px" onclick="go('projects')">手动立项</button></div></div>`}`,
  });
}
/* 项目卡：与全站一致的浅色内容卡（无深色封面） */
function projectCard(p) {
  const badge = p.deliverable ? `<span class="pill ok"><i class="dot ok"></i>可交付</span>`
    : (p.stages_passed ? `<span class="pill gold">${p.stages_passed}/19 阶段</span>` : `<span class="pill">未制作</span>`);
  const dur = fmtDur(p.episode_seconds || (p.minutes || 30) * 60);
  const aspect = p.aspect ? ` · ${esc(p.aspect)}` : "";
  const src = (p.source_meta && p.source_meta.type === "novel") ? " · 小说改编" : "";
  return `<div class="card click project-card" onclick="go('project:${p.id}')">
    <div class="pbody">
      <div class="pc-head"><h3 class="pc-title">${esc(p.title)}</h3>${badge}</div>
      <div class="pc-meta">${p.episodes || 6} 集 × ${dur}${aspect}${src}${p.shots ? " · " + p.shots + " 镜" : ""}</div>
      <div class="pc-logline">${esc(p.logline || "")}</div>
    </div></div>`;
}

/* ---------- 项目列表 ---------- */
function fmtDur(sec) {
  sec = Number(sec || 0);
  if (!sec) return "—";
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return s ? `${m} 分 ${s} 秒` : `${m} 分钟`;
}
function bufToB64(buf) {
  const bytes = new Uint8Array(buf); let s = ""; const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk)
    s += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  return btoa(s);
}
async function importNovelFile(file) {
  const st = $("#novel_status");
  if (!file) return;
  if (!/\.txt$/i.test(file.name) && file.type && !/text/.test(file.type))
    return toast("请选择 TXT 文件");
  if (file.size > 10 * 1024 * 1024) return toast("文件超过 10 MB");
  if (st) st.textContent = "正在解析…";
  try {
    const b64 = bufToB64(await file.arrayBuffer());
    const d = await api("/api/novels/import", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, content_b64: b64 }) });
    window._NOVEL = d;
    const t = $("#pf_title"), a = $("#pf_author"), w = $("#pf_words");
    const c = $("#pf_chapters"), l = $("#pf_logline");
    if (t && (!t.value.trim() || t.dataset.auto === "1")) { t.value = d.title || ""; t.dataset.auto = "1"; }
    if (a && (!a.value.trim() || a.dataset.auto === "1")) { a.value = d.author || ""; a.dataset.auto = "1"; }
    if (w) w.value = d.words_wan || w.value;
    if (c) c.value = d.chapters || c.value;
    if (l && !l.value.trim()) l.value = d.logline || "";
    if (st) st.innerHTML = `已导入《${esc(d.title)}》 · ${d.chapters} 章 · ${d.words_wan} 万字 · ${esc(d.encoding)} · ${esc(d.filename)}`;
    refreshFormatRec();
  } catch (e) {
    if (st) st.textContent = "导入失败：" + e.message;
    toast("小说导入失败：" + e.message);
  }
}
let _recSeq = 0, _recTimer = null;
function scheduleFormatRec() { clearTimeout(_recTimer); _recTimer = setTimeout(refreshFormatRec, 250); }
function setCreateMode(mode) {
  const novel = mode === "novel";
  $("#pf_source_type").value = mode;
  $$(".mode-tab").forEach(b => b.classList.toggle("on", b.dataset.mode === mode));
  $$(".novel-only").forEach(e => e.classList.toggle("hide", !novel));
  $("#pf_title").placeholder = novel ? "片名 / 小说名" : "片名";
  refreshFormatRec();
}
async function refreshFormatRec() {
  const box = $("#fmtbox"); if (!box) return;
  const seq = ++_recSeq;
  const body = {
    platform_key: ($("#pf_platform") || {}).value || "hongguo",
    source_type: ($("#pf_source_type") || {}).value || "original",
    words_wan: Number(($("#pf_words") || {}).value || 0),
    chapters: Number(($("#pf_chapters") || {}).value || 0),
    genre: ($("#pf_genre") || {}).value || "",
  };
  box.innerHTML = `<span class="muted">正在获取分集建议…</span>`;
  try {
    const d = await api("/api/formats/recommend", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (seq !== _recSeq || !$("#fmtbox")) return;
    box.innerHTML = `<div class="rec-head"><span class="pill gold">${esc(d.platform)}</span>
        <b>${d.episodes} 集 × ${fmtDur(d.episode_seconds)}</b>
        <span class="muted">${d.season_minutes} 分钟/季 · ${esc(d.aspect)}</span></div>
      <div class="muted" style="font-size:var(--fs-sm);margin-top:6px">${esc(d.reason)}</div>`;
    const eps = $("#pf_eps"), secs = $("#pf_secs"), asp = $("#pf_aspect");
    if (eps) eps.value = d.episodes;
    if (secs) secs.value = d.episode_seconds;
    if (asp) asp.value = d.aspect;
  } catch (e) {
    if (seq === _recSeq) box.innerHTML = `<span style="color:var(--bad)">建议加载失败：${esc(e.message)}</span>`;
  }
}
async function viewProjects() {
  const projs = await api("/api/dramas");
  let fmts = { platforms: {} };
  try { fmts = await api("/api/formats"); } catch (e) {}
  const platformOpts = Object.entries(fmts.platforms || {}).map(([k, v]) =>
    `<option value="${esc(k)}">${esc(v.name)}</option>`).join("");
  setMain({
    title: "项目",
    top: `<div class="right"><span class="pill">${projs.length} 个项目</span></div>`,
    body: `
    <h2>创建项目</h2>
    <form class="stack" id="pf">
      <input type="hidden" name="source_type" id="pf_source_type" value="original">
      <div class="mode-tabs">
        <button type="button" class="mode-tab on" data-mode="original" onclick="setCreateMode('original')">原创剧本</button>
        <button type="button" class="mode-tab" data-mode="novel" onclick="setCreateMode('novel')">小说改编</button>
      </div>
      <div class="grid3">
        <input name="title" id="pf_title" placeholder="片名" required maxlength="128">
        <input name="logline" id="pf_logline" placeholder="一句话故事（logline，必填 ≤120 字）" required maxlength="120">
        <select name="platform_key" id="pf_platform" onchange="refreshFormatRec()">${platformOpts}</select>
      </div>
      <div class="grid3">
        <input name="genre" id="pf_genre" placeholder="题材" value="悬疑" oninput="scheduleFormatRec()">
        <select name="rating"><option>全龄</option><option selected>12+</option><option>16+</option></select>
        <input name="author" id="pf_author" class="novel-only hide" placeholder="原著作者（小说模式）">
      </div>
      <div class="grid3 novel-only hide" id="novel_row">
        <input name="words_wan" id="pf_words" type="number" min="0.1" step="0.1" placeholder="原作字数（万字）" oninput="scheduleFormatRec()">
        <input name="chapters" id="pf_chapters" type="number" min="1" step="1" placeholder="原作章节数" oninput="scheduleFormatRec()">
        <input name="source_url" id="pf_source_url" placeholder="原著链接 / 授权编号（可选）">
      </div>
      <label class="import-box novel-only hide" id="novel_drop">
        <input type="file" id="pf_novel_file" accept=".txt,text/plain" class="hide">
        <b>导入小说 TXT</b>
        <small>自动识别章节、字数、作者与编码（UTF-8 / GBK）· 上限 10 MB · 也可拖拽到此处</small>
        <span id="novel_status" class="muted" style="font-size:var(--fs-sm)"></span>
      </label>
      <div class="rec-box" id="fmtbox"><span class="muted">正在获取分集建议…</span></div>
      <div class="grid3">
        <label class="fld"><small>分集数</small><input name="episodes" id="pf_eps" type="number" min="1" max="200" value="6"></label>
        <label class="fld"><small>每集时长（秒）</small><input name="episode_seconds" id="pf_secs" type="number" min="15" max="2700" step="15" value="1800"></label>
        <label class="fld"><small>画幅</small><select name="aspect" id="pf_aspect">
          <option value="9:16">9:16 竖屏</option><option value="16:9">16:9 横屏</option><option value="2.39:1">2.39:1 宽银幕</option></select></label>
      </div>
      <div class="form-actions"><button class="btn" type="submit">创建立项</button>
        <span class="muted" style="font-size:var(--fs-sm)">建议值可手动覆盖；未填字段使用推荐值</span></div>
    </form>
    <h2>全部项目</h2>
    <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;align-items:center">
      <input id="psearch" placeholder="搜索片名 / logline" style="max-width:260px" oninput="filterProjs()">
      <select id="psort" style="max-width:170px" onchange="filterProjs()">
        <option value="id">按创建时间</option><option value="title">按片名</option>
        <option value="deliverable">可交付优先</option></select>
      <div style="display:flex;gap:4px;margin-left:auto">
        <button class="btn ghost sm" id="viewlist" onclick="setProjView('list')">列表</button>
        <button class="btn ghost sm" id="viewboard" onclick="setProjView('board')">看板</button>
      </div>
    </div>
    <div class="cards" id="plist">${projs.length ? projs.map(projectCard).join("") : ""}</div>
    <div id="pboard" class="hide"></div>
    ${projs.length ? "" : `<div class="card empty">${ico("film")}<div>暂无项目</div><div style="margin-top:14px"><button class="btn" onclick="seedDemo()">创建示例项目</button></div></div>`}`,
  });
  window._PROJS = projs;
  window._NOVEL = null;
  const fInput = $("#pf_novel_file");
  if (fInput) fInput.onchange = e => { const f = e.target.files[0]; if (f) importNovelFile(f); e.target.value = ""; };
  const drop = $("#novel_drop");
  if (drop) {
    ["dragover", "dragenter"].forEach(ev => drop.addEventListener(ev, e => {
      e.preventDefault(); drop.classList.add("drag");
    }));
    ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => {
      e.preventDefault(); drop.classList.remove("drag");
    }));
    drop.addEventListener("drop", e => { const f = e.dataTransfer.files[0]; if (f) importNovelFile(f); });
  }
  refreshFormatRec();
  const pf = $("#pf");
  if (pf) pf.onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const b = {};
    fd.forEach((v, k) => { if (String(v).trim() !== "") b[k] = v; });
    ["episodes", "episode_seconds"].forEach(k => { if (b[k] !== undefined) b[k] = Number(b[k]); });
    const sel = $("#pf_platform");
    b.platform = sel && sel.selectedOptions[0] ? sel.selectedOptions[0].textContent : (b.platform_key || "红果漫剧");
    if (b.source_type === "novel") {
      const nv = window._NOVEL || {};
      b.source_meta = { title: b.title, author: b.author || nv.author || "",
        words_wan: Number(b.words_wan || 0) || null,
        chapters: Number(b.chapters || 0) || null, source_url: b.source_url || "",
        novel_id: nv.novel_id || null };
      if (nv.filename) b.source_meta.filename = nv.filename;
    }
    delete b.author; delete b.words_wan; delete b.chapters; delete b.source_url;
    if (!b.minutes) b.minutes = Math.max(1, Math.round((b.episode_seconds || 1800) / 60));
    const btn = pf.querySelector("button[type=submit]");
    withLoading(btn, async () => {
      const d = await api("/api/dramas", { method: "POST",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
      toast(`立项成功 · ${d.package.episodes} 集 × ${fmtDur(d.episode_seconds)}`);
      go("project:" + d.id);
    });
  };
}

/* 异步按钮 loading 封装：执行期间禁用并显示"处理中…" */
async function withLoading(btn, fn) {
  if (!btn) return fn();
  const old = btn.innerHTML, dis = btn.disabled;
  btn.disabled = true; btn.dataset.loading = "1";
  btn.innerHTML = `<span class="spin"></span>处理中…`;
  try { return await fn(); }
  catch (e) { toast("操作失败：" + e.message); }
  finally { btn.disabled = dis; btn.innerHTML = old; delete btn.dataset.loading; }
}
function filterProjs() {
  const q = (($("#psearch") || {}).value || "").toLowerCase();
  const sort = ($("#psort") || {}).value || "id";
  let list = (window._PROJS || []).filter(p =>
    !q || (p.title || "").toLowerCase().includes(q) || (p.logline || "").toLowerCase().includes(q));
  if (sort === "title") list = list.slice().sort((a, b) => (a.title || "").localeCompare(b.title || ""));
  else if (sort === "deliverable") list = list.slice().sort((a, b) => (b.deliverable ? 1 : 0) - (a.deliverable ? 1 : 0));
  $("#plist").innerHTML = list.length ? list.map(projectCard).join("") : `<div class="card empty">${ico("film")}<div>无匹配项目</div></div>`;
}

let PROJ_VIEW = "list";
function setProjView(v) {
  PROJ_VIEW = v;
  $("#plist").classList.toggle("hide", v !== "list");
  $("#pboard").classList.toggle("hide", v !== "board");
  $("#viewlist").classList.toggle("acc", v === "list");
  $("#viewboard").classList.toggle("acc", v === "board");
  if (v === "board") renderBoard();
}
function lifecycleActions(p) {
  const lc = p.lifecycle || "立项";
  const id = p.id;
  const b = (status, label, ghost) => `<button class="btn ${ghost ? "ghost " : ""}sm" onclick="event.stopPropagation();setLifecycle(${id},'${status}','${label}')">${label}</button>`;
  if (lc === "归档") return b("draft", "恢复", true);
  const acts = [];
  if (lc === "立项" || lc === "制作中" || lc === "可交付") acts.push(b("pending_review", "提交审核", true));
  if (lc === "待审") acts.push(b("delivered", "标记交付", false));
  acts.push(b("archived", "归档", true));
  return acts.join("");
}
function renderBoard() {
  const order = ["立项", "制作中", "可交付", "待审", "已交付", "归档"];
  const list = window._PROJS || [];
  const col = (name) => `<div class="board-col"><div class="board-col-t">${name}<span class="muted">${list.filter(p => (p.lifecycle || "立项") === name).length}</span></div>
    <div class="board-cards">${list.filter(p => (p.lifecycle || "立项") === name).map(p =>
      `<div class="board-card" onclick="go('project:${p.id}')"><div class="bc-title">${esc(p.title)}</div>
        <div class="bc-meta">${p.episodes || 6} 集 · ${p.shots || 0} 镜</div>
        <div class="bc-actions">${lifecycleActions(p)}</div></div>`).join("") || `<div class="muted" style="font-size:var(--fs-meta);padding:6px 2px">—</div>`}</div></div>`;
  $("#pboard").innerHTML = `<div class="board">${order.map(col).join("")}</div>`;
}
async function setLifecycle(id, status, label) {
  try {
    await api("/api/dramas/" + id + "/lifecycle", { method: "PATCH",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
    toast("已" + (label || "更新"));
    const projs = await api("/api/dramas"); window._PROJS = projs;
    if (PROJ_VIEW === "board") renderBoard(); else go("projects");
  } catch (e) { toast("操作失败：" + e.message); }
}

/* ---------- 项目工作台 ---------- */
let CUR = { id: null, stage: null };
let CUR_EP = 1;
async function viewProject(id) {
  CUR.id = id;
  let p;
  try { p = await api("/api/dramas/" + id); }
  catch (e) {
    setMain({
      title: "项目未找到",
      body: `<div class="card empty">${esc(e.message)}<div style="margin-top:16px"><button class="btn" onclick="go('projects')">返回项目列表</button></div></div>`,
    });
    return;
  }
  const run = p.last_run;
  CUR.spec = p.delivery_spec || {};
  const stages = (run && run.stages) || [];
  const byName = {}; stages.forEach(s => byName[s.stage] = s);
  if (!CUR.stage || !STAGES.some(s => s[0] === CUR.stage)) CUR.stage = STAGES[0][0];

  const stepCard = (name) => {
    const meta = STAGES.find(x => x[0] === name) || ["", name, ""];
    const st = byName[name];
    const cls = st ? (st.status === "passed" ? "ok" : "bad") : "";
    const txt = st ? (st.status === "passed" ? "通过" : "失败") : (run ? "—" : "待运行");
    return `<div class="step ${CUR.stage === name ? "on" : ""}" onclick="pickStage('${name}')">
      <div class="n">${meta[1]}</div><div class="t">${name.replace(/^M\d+ /, "")}</div>
      <div class="s">${st ? `<i class="dot ${cls}"></i> ${txt}` : txt}</div></div>`;
  };
  const stepper = SEGMENTS.map(([seg, mods]) => `<div style="margin-bottom:12px">
      <div style="font-size:var(--fs-meta);color:var(--accent);letter-spacing:.5px;margin-bottom:6px">${seg}</div>
      <div class="stepper">${mods.map(stepCard).join("")}</div></div>`).join("");

  const passed = run ? run.summary.passed : 0, total = 19;
  const dur = fmtDur(p.episode_seconds || (p.minutes || 30) * 60);
  const aspect = (p.delivery_spec || {}).master || "";
  const sm = p.source_meta || {};
  const srcRow = sm.type === "novel" ? `<div class="k">改编来源</div><div>《${esc(sm.title || p.title)}》${
    sm.author ? " · " + esc(sm.author) : ""}${sm.words_wan ? " · 原作 " + esc(sm.words_wan) + " 万字" : ""}${
    sm.chapters ? " / " + esc(sm.chapters) + " 章" : ""}${sm.filename ? " · " + esc(sm.filename) : ""}</div>` : "";
  setMain({
    title: esc(p.title),
    top: `<div class="right">
        <span class="pill">${p.episodes} 集 × ${dur}${aspect ? " · " + esc(aspect) : ""}</span>
        <span class="pill gold">${esc(p.rating || "")} · ${esc(p.genre || "")}</span>
        <button class="btn ghost sm" id="setbtn">${ico("gear")} 设置</button>
        <button class="btn ghost" id="runbtn">${ico("play")} 运行流水线</button>
        <button class="btn" id="prodbtn">${ico("sparkle")} 一键全流程</button></div>`,
    body: `
    <div id="epbar" style="margin-bottom:12px"></div>
    <div class="stats" id="projstats" style="margin-bottom:16px"></div>
    <div class="card">
      <div class="kv">
        <div class="k">Logline</div><div>${esc(p.logline)}</div>
        <div class="k">目标平台</div><div>${esc(p.platform || "—")}</div>
        <div class="k">分集规格</div><div>${p.episodes} 集 × ${dur}${aspect ? " · " + esc(aspect) : ""}</div>
        ${srcRow}
        <div class="k">交付规格</div><div>${(p.delivery_spec && p.delivery_spec.master) ? `主母版 ${p.delivery_spec.master} · 平台版 ${p.delivery_spec.platform} · 衍生 ${p.delivery_spec.derived}` : "—"}</div>
        <div class="k">流水线</div><div>${run ? `<span class="pill ${run.summary.deliverable ? "ok" : "bad"}">${passed}/${total} 阶段通过 ${run.summary.deliverable ? "· 可交付" : ""}</span>` : `<span class="pill">尚未运行</span>`}</div>
      </div>
    </div>
    <h2>制作流程 <span class="hint">点击阶段查看成果</span></h2>
    ${stepper}
    <div id="stagedetail"></div>`,
  }, true);
  $("#runbtn").onclick = () => runPipeline(id);
  $("#prodbtn").onclick = () => confirmDialog("运行全流程？",
    "将执行：19 阶段流水线 → 派生分镜 → 每镜 4 候选抽卡 → 成片组装。会覆盖现有分镜与候选。",
    () => produceAll(id), "开始制作");
  $("#setbtn").onclick = () => editProject(p);
  renderStageDetail(byName[CUR.stage]);
  // 分集看板（每集卡片：镜数 + 集内剧本场数）
  api("/api/dramas/" + id + "/episodes").then(async ep => {
    const bar = $("#epbar"); if (!bar) return;
    const cards = [];
    for (let n = 1; n <= ep.episodes; n++) {
      let sc = 0; try { sc = (await api("/api/dramas/" + id + "/script?episode=" + n)).scenes.length; } catch (e) {}
      const cnt = ep.breakdown[String(n)] || 0;
      cards.push(`<div class="card click" style="padding:12px;${n === CUR_EP ? "border-color:var(--accent)" : ""}" onclick="pickEp(${id},${n})">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b style="font-size:var(--fs-table)">第 ${n} 集</b>
          ${n === CUR_EP ? '<span class="pill gold" style="font-size:var(--fs-micro)">当前</span>' : ""}</div>
        <div class="muted" style="font-size:var(--fs-meta);margin-top:6px">${cnt} 镜 · ${sc} 场 · ${ep.minutes} 分</div></div>`);
    }
    bar.innerHTML = `<div style="font-size:var(--fs-sm);color:var(--accent);margin-bottom:6px">分集看板</div>
      <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(140px,1fr))">${cards.join("")}</div>`;
  }).catch(e => {
    const bar = $("#epbar");
    if (bar) bar.innerHTML = `<div class="muted" style="color:var(--bad);font-size:var(--fs-sm)">分集看板加载失败：${esc(e.message)}
      <button class="btn ghost sm" style="margin-left:8px" onclick="viewProject(${id})">重试</button></div>`;
  });
  // 制作统计（异步，按当前集）
  api("/api/dramas/" + id + "/shots?episode=" + CUR_EP).then(sh => {
    const gen = sh.filter(x => x.status === "已生成" || x.status === "已选定").length;
    const sel = sh.filter(x => x.status === "已选定").length;
    const pct = sh.length ? Math.round(gen / sh.length * 100) : 0;
    const el = $("#projstats"); if (el) el.innerHTML = `
      <div class="stat"><div class="k">${sh.length}</div><div class="l">镜头总数</div></div>
      <div class="stat"><div class="k">${gen}</div><div class="l">已生成</div></div>
      <div class="stat"><div class="k">${sel}</div><div class="l">已选定</div></div>
      <div class="stat"><div class="k">${pct}%</div><div class="l">镜头完成度</div>
        <div class="progress" style="margin-top:8px"><i style="width:${pct}%"></i></div></div>`;
  }).catch(e => {
    const el = $("#projstats");
    if (el) el.innerHTML = `<div class="card" style="grid-column:1/-1;color:var(--bad);font-size:var(--fs-sm)">镜头统计加载失败：${esc(e.message)}
      <button class="btn ghost sm" style="margin-left:8px" onclick="viewProject(${id})">重试</button></div>`;
  });
  window.pickStage = (n) => { CUR.stage = n; syncHash(hashFor("project", id, n)); viewProject(id); };
  replaceHash(hashFor("project", id, CUR.stage));
}
async function renderStageDetail(st) {
  await _renderStageDetail(st);
  attachParams(st);
}
async function _renderStageDetail(st) {
  const el = $("#stagedetail"); if (!el) return;
  if (!st) { el.innerHTML = `<div class="detail empty">${ico("play")}<div>该阶段尚无运行结果</div><div class="muted" style="font-size:var(--fs-sm);margin-top:4px">点击右上角「运行流水线」生成</div></div>`; return; }
  const meta = STAGES.find(s => s[0] === st.stage) || ["", "", ""];
  const art = st.artifact || {};
  const modCode = (st.stage.match(/^M\d+/) || [""])[0];
  const head = `<div class="head"><h2>${st.stage}</h2>
      <span style="display:flex;gap:8px;align-items:center">
        <button class="btn ghost sm" onclick="openHelp('${modCode}')">本模块指南</button>
        <span class="pill ${st.status === "passed" ? "ok" : "bad"}">${st.status === "passed" ? "✓ 通过" : "✗ 失败"}</span></span></div>`;
  const viol = (st.violations && st.violations.length) ? `<div style="margin-top:12px;color:var(--bad)">违规：${st.violations.map(esc).join("；")}</div>` : "";
  // 供应商阶段 → 三段式追踪
  if (/供应商/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="provview"><div class="skeleton" style="width:50%"></div><div class="skeleton"></div></div></div>`;
    return renderProviders();
  }
  // 成本阶段 → 看板
  if (/成本/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="costview"><div class="skeleton" style="width:50%"></div><div class="skeleton"></div></div></div>`;
    return renderCost();
  }
  // 母版阶段 → 规格 + QC 逐项
  if (/母版/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="qcview"><div class="skeleton" style="width:60%"></div><div class="skeleton"></div><div class="skeleton" style="width:80%"></div></div></div>`;
    return renderQC();
  }
  // 一致性阶段 → QC 指标 + 连续性表
  if (/一致性/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}${stageBody(st.stage, art)}<div id="contview"></div></div>`;
    return renderContinuity();
  }
  // 选角阶段 → 角色工作台（持久化角色）
  if (/选角/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="castview"><div class="skeleton" style="width:40%"></div><div class="skeleton"></div></div></div>`;
    return renderCast();
  }
  // 剧本阶段 → 剧本编辑器（可编辑场次 + 结构健康度）
  if (/剧本/.test(st.stage)) {
    el.innerHTML = `<div class="detail">${head}<div id="scriptview"><div class="skeleton" style="width:40%"></div><div class="skeleton"></div></div></div>`;
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
    el.innerHTML = `<div class="detail">${head}<div id="sbwork"><div class="skeleton" style="width:40%"></div><div class="skeleton"></div></div></div>`;
    return renderStoryboard();
  }
  el.innerHTML = `<div class="detail">${head}${stageBody(st.stage, art)}${viol}</div>`;
  // 交付阶段 → 版本历史（真实 Run 记录）
  if (/交付/.test(st.stage)) return renderVersions();
}

/* ---------- 分镜工作台（参考 LumenX Storyboard / Toonflow 批量网格） ---------- */
const SBSEL = new Set();
let SBCUR = null;
async function renderStoryboard() {
  const box = $("#sbwork"); if (!box) return;
  let shots = [], loadErr = null;
  try { shots = await api("/api/dramas/" + CUR.id + "/shots?episode=" + CUR_EP); } catch (e) { loadErr = e; }
  if (loadErr) {
    box.innerHTML = `<div class="card empty" style="color:var(--bad)">分镜表加载失败：${esc(loadErr.message)}
      <div style="margin-top:12px"><button class="btn" onclick="renderStoryboard()">重试</button></div></div>`;
    return;
  }
  if (!shots.length) {
    box.innerHTML = `<div class="muted" style="margin-bottom:12px">尚无分镜表。从剧本派生镜头（每场 1–3 镜）。</div>
      <button class="btn" onclick="genShots()">${ico("frame")} 生成分镜表</button>`;
    return;
  }
  box.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px">
      <div class="muted">第 ${CUR_EP} 集 · 共 <b>${shots.length}</b> 镜 · 已生成 ${shots.filter(x => x.status === "已生成").length}</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn ghost sm" onclick="sbSelect('all')">全选</button>
        <button class="btn ghost sm" onclick="sbSelect('none')">取消</button>
        <button class="btn ghost sm" onclick="sbSelect('pending')">选未生成</button>
        <button class="btn sm" onclick="sbBatch()">${ico("sparkle")} 批量生成所选</button>
      </div>
    </div>
    <div class="cards" id="sbshots" style="grid-template-columns:repeat(auto-fill,minmax(210px,1fr))">
      ${shots.map(sbCard).join("")}</div>`;
  $$(".sbcard").forEach(c => c.onclick = e => { if (e.target.tagName !== "INPUT") sbOpen(c.dataset.id, c.dataset.no); });
}
function sbCard(s) {
  const sel = SBSEL.has(String(s.id));
  return `<div class="asset sbcard" data-id="${s.id}" data-no="${s.shot_no}" style="cursor:pointer;${sel ? "border-color:var(--accent)" : ""}">
    <div class="thumb">${ico(s.status === "已生成" ? "frame" : "film")}
      <span class="tag">镜 ${s.shot_no}</span>
      <input type="checkbox" ${sel ? "checked" : ""} style="position:absolute;top:8px;right:8px;width:auto" onclick="event.stopPropagation();sbToggle('${s.id}')"></div>
    <div class="body"><h4 style="font-size:var(--fs-table)">场 ${s.scene_no} · ${esc(s.move)}</h4>
      <div class="meta"><span>${esc(s.size)}</span><span>${esc(s.angle)}</span><span>${s.duration}s</span>
        ${(s.characters || []).map(c => `<span>${esc(c)}</span>`).join("")}</div>
      <div style="margin-top:8px"><span class="pill ${s.status === "已生成" ? "ok" : ""}" style="font-size:var(--fs-micro)">${esc(s.status)}</span></div></div></div>`;
}
function sbToggle(id) {
  id = String(id); if (SBSEL.has(id)) SBSEL.delete(id); else SBSEL.add(id);
  const c = $(`.sbcard[data-id="${id}"]`);
  if (c) { c.style.borderColor = SBSEL.has(id) ? "var(--accent)" : ""; const cb = c.querySelector("input"); if (cb) cb.checked = SBSEL.has(id); }
}
async function sbSelect(mode) {
  const shots = await api("/api/dramas/" + CUR.id + "/shots?episode=" + CUR_EP);
  SBSEL.clear();
  shots.forEach(s => { if (mode === "all" || (mode === "pending" && s.status !== "已生成")) SBSEL.add(String(s.id)); });
  renderStoryboard();
}
async function sbBatch() {
  if (!SBSEL.size) return toast("先选择镜头");
  try { const r = await api("/api/dramas/" + CUR.id + "/shots/batch", { method: "POST",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify({ shot_ids: Array.from(SBSEL).map(Number) }) });
    toast("生成 " + r.generated + " 镜"); renderStoryboard();
  } catch (e) { toast("" + e.message); }
}
async function genShots() {
  try { const r = await api("/api/dramas/" + CUR.id + "/shots/generate", { method: "POST" });
    toast("派生 " + r.count + " 镜"); renderStoryboard();
  } catch (e) { toast("" + e.message); }
}

/* 镜头详情弹窗：字段 + 抽卡候选（参考 LumenX R2V 批量抽卡） */
async function sbOpen(shotId, shotNo) {
  const shots = await api("/api/dramas/" + CUR.id + "/shots?episode=" + CUR_EP);
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
        <b style="font-size:var(--fs-table)">候选（抽卡）</b>
        <button class="btn sm" onclick="genCands('${shotId}')">${ico("sparkle")} 生成 4 个候选</button></div>
      <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(140px,1fr))">
        ${cands.length ? cands.map(c => `<div class="cand ${c.selected ? "on" : ""}" onclick="pickCand('${c.id}','${shotId}')">
          <div class="thumb">${ico("frame")}${c.selected ? '<span class="pick">已选</span>' : ""}<span class="score">${c.score}</span></div></div>`).join("")
          : `<div class="muted" style="padding:20px">尚无候选，点击「生成 4 个候选」抽卡。</div>`}
      </div>
    </div></div>`;
  document.body.appendChild(modal);
}
function closeModal() { $$(".modal").forEach(m => m.remove()); }
async function genCands(shotId) {
  try { await api("/api/shots/" + shotId + "/candidates", { method: "POST" }); closeModal(); await sbOpen(shotId); }
  catch (e) { toast("" + e.message); }
}
/* 供应商三段式追踪（M17.5-F02） */
async function costPreview() {
  const d = await api("/api/dramas/" + CUR.id + "/cost-preview", { method: "POST",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
  const pv = d.preview;
  document.getElementById("costprev").innerHTML =
    `<div class="kv" style="margin-bottom:10px">${pv.items.map(it =>
      `<div class="k">${esc(it.kind)}</div><div>${it.count ? it.count + " 次" : (it.seconds || 0) + " 秒"} · ¥${it.cost_cny}</div>`).join("")}
      <div class="k"><b>合计</b></div><div><b>¥${pv.total_cny}</b></div></div>
     <button class="btn" onclick="costConfirm()">确认并放行</button> <span class="muted" style="font-size:var(--fs-meta)">未确认前不产生付费调用</span>`;
}
async function costConfirm() {
  const d = await api("/api/dramas/" + CUR.id + "/cost-preview", { method: "POST",
    headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmed: true }) });
  toast(d.blocked.length ? "仍未放行：需确认" : "已放行生成");
}
async function renderProviders() {
  const box = $("#provview"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/provider-tasks"); } catch (e) { return; }
  if (!d.kinds.length) { box.innerHTML = `<div class="muted">尚无供应商调用记录，先运行流水线。</div>`; return; }
  const ICON = { text: "doc", image: "frame", video: "film", tts: "wave", music: "music", lipsync: "face" };
  box.innerHTML = `<div class="muted" style="margin-bottom:12px">${esc(d.note)}</div>
    <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr))">
    ${d.kinds.map(k => `<div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b>${ico(ICON[k.kind] || "route")} ${esc(k.kind)}</b>
        <span class="pill ${k.configured ? "ok" : ""}">${k.configured ? "真实" : "Mock"}</span></div>
      <div style="display:flex;align-items:center;gap:6px;margin-top:12px">
        ${k.stages.map((st, i) => `<span class="pill ok" style="font-size:var(--fs-meta)">${esc(st.stage)} ✓</span>${i < k.stages.length - 1 ? '<span class="muted">→</span>' : ""}`).join("")}
      </div></div>`).join("")}</div>`;
}

/* 成本看板（M14.7） */
async function renderCost() {
  const box = $("#costview"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/cost-dashboard"); }
  catch (e) { box.innerHTML = `<div class="muted">${esc(e.message)}</div>`; return; }
  const bar = (v) => `<div class="progress" style="margin-top:6px"><i style="width:${Math.min(v, 100)}%"></i></div>`;
  box.innerHTML = `
    <div class="stats" style="margin-bottom:16px">
      <div class="stat"><div class="k">${d.north_star.deliverable_minutes}</div><div class="l">可交付母版分钟</div></div>
      <div class="stat"><div class="k">¥${d.north_star.est_cost_cny}</div><div class="l">预估总成本</div></div>
      <div class="stat"><div class="k">${d.north_star.minutes_per_yuan}</div><div class="l">每元产出分钟（北极星）</div></div>
      <div class="stat"><div class="k">${esc(d.budget.level)}</div><div class="l">预算预警</div></div>
    </div>
    <h2 style="font-size:var(--fs-table)">过程指标</h2>
    <div class="card">${d.process.map(x => `<div style="margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;font-size:var(--fs-sm)"><span>${esc(x.name)}</span><b>${x.value}${x.name.includes("调用") ? "" : "%"}</b></div>
      ${bar(x.name.includes("重试") || x.name.includes("调用") ? x.value : x.value)}</div>`).join("")}</div>
    <h2 style="font-size:var(--fs-table)">影视过程指标（与成本并列）</h2>
    <div class="card">${d.film_process.map(x => `<div style="margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;font-size:var(--fs-sm)"><span>${esc(x.name)}</span><b>${x.value}%</b></div>
      ${bar(x.value)}</div>`).join("")}</div>
    <div class="muted" style="font-size:var(--fs-meta);margin-top:10px">规模：${d.scale.episodes} 集 · ${d.scale.shots} 镜 · ${d.scale.characters} 角色</div>
    <h2 style="font-size:var(--fs-table)">生成前确认闸 <span class="hint">花额度前逐镜摊开（C6）</span></h2>
    <div class="card" id="costprev"><button class="btn ghost" onclick="costPreview()">预估本项目生成成本</button></div>`;
}

/* 母版 QC 逐项（M11.5/M11.6） */
async function renderQC() {
  const box = $("#qcview"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/qc-report"); }
  catch (e) { box.innerHTML = `<div class="muted">${esc(e.message)}</div>`; return; }
  box.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="muted">影视 QC 清单 · 逐项阈值 / 实测 / 判定</div>
      <div><span class="pill ${d.summary.failed ? "bad" : "ok"}">${d.summary.passed}/${d.summary.total} 通过</span>
        <button class="btn sm" style="margin-left:8px" onclick="downloadQC()">${ico("download")} 下载报告</button></div></div>
    <div class="card" style="padding:0"><table>
      <thead><tr><th>检查项</th><th>阈值</th><th>实测</th><th>判定</th></tr></thead><tbody>
      ${d.items.map(it => `<tr><td>${esc(it.item)}</td><td class="muted">${esc(it.threshold)}</td>
        <td>${esc(it.measured)}</td>
        <td><span class="pill ${it.verdict === "pass" ? "ok" : "bad"}">${it.verdict === "pass" ? "通过" : "失败"}</span></td></tr>`).join("")}
      </tbody></table></div>
    <div style="margin-top:12px"><span class="pill ${d.summary.failed ? "bad" : "ok"}">结论：${esc(d.conclusion)}</span></div>`;
}

/* 连续性表（M6.4 剧本监督） */
async function renderContinuity() {
  const box = $("#contview"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/continuity"); } catch (e) { return; }
  if (!d.rows.length) return;
  box.innerHTML = `<h2 style="font-size:var(--fs-table);margin-top:20px">连续性表 <span class="hint">${esc(d.axes)}</span></h2>
    <div style="display:flex;gap:10px;margin-bottom:10px">
      <span class="pill">${d.shots} 镜</span>
      <span class="pill ${d.violations.length ? "bad" : "ok"}">${d.violations.length ? d.violations.length + " 处违规" : "无违规"}</span></div>
    <div class="card" style="padding:0;max-height:340px;overflow:auto"><table>
      <thead><tr><th>镜</th><th>场</th><th>入</th><th>出</th><th>视线</th><th>时</th></tr></thead><tbody>
      ${d.rows.slice(0, 60).map(r => `<tr><td>${r.shot_no}</td><td>${r.scene_no}</td>
        <td>${esc(r.entry_side || "")}</td><td>${esc(r.exit_side || "")}</td>
        <td>${esc(r.eyeline || "")}</td><td>${esc(r.day_night || "")}</td></tr>`).join("")}
      </tbody></table></div>
    ${d.violations.length ? `<div style="color:var(--bad);margin-top:10px;font-size:var(--fs-sm)">${d.violations.slice(0,10).map(v => `镜 ${v.shot_no} · ${esc(v.msg)}`).join("<br>")}</div>` : ""}`;
}

/* 角色工作台（M3：锚点三视图 + 音色 + 定妆门禁） */
const VIEWNAME = { front: "正面", side: "侧面", back: "背面", "3_4": "3/4 侧", full_body: "全身", expression: "表情" };
async function renderCast() {
  const box = $("#castview"); if (!box) return;
  const chars = await api("/api/dramas/" + CUR.id + "/characters");
  if (!chars.length) { box.innerHTML = `<div class="muted">尚无角色，先运行流水线。</div>`; return; }
  box.innerHTML = `<div class="muted" style="margin-bottom:12px">角色定妆 = 后续所有画面的唯一视觉事实来源；锚点是与一致性检测（M6）共享的基准。</div>
    ${chars.map(c => `<h2>${ico("face")} ${esc(c.name)} <span class="hint">音色 ${esc(c.voice_key)} · ${c.anchors.length} 张锚点 · ${esc(c.status)}</span></h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;margin-bottom:18px">
        ${c.anchors.map(a => `<div class="asset"><div class="thumb" style="aspect-ratio:3/4">${ico("face")}<span class="tag">${esc(VIEWNAME[a] || a)}</span></div>
          <div class="body"><div class="muted" style="font-size:var(--fs-meta)">锚点 · ${esc(a)}</div></div></div>`).join("")}
      </div>`).join("")}
    <div class="card"><b style="font-size:var(--fs-table)">定妆门禁</b>
      <div class="kv" style="grid-template-columns:120px 1fr;font-size:var(--fs-sm);margin-top:8px">
        <div class="k">署名</div><div>showrunner（唯一署名审批人）</div>
        <div class="k">理由码</div><div>pass_with_condition</div>
        <div class="k">二元清单</div><div>三视图齐备 · 五官一致 · 无真人相似风险 · 嵌入已入库</div>
      </div></div>`;
}

/* 剧本编辑器（M2：场次编辑 + 结构健康度） */
async function renderScript() {
  const box = $("#scriptview"); if (!box) return;
  const d = await api("/api/dramas/" + CUR.id + "/script?episode=" + CUR_EP);
  if (!d.scenes || !d.scenes.length) { box.innerHTML = `<div class="muted">尚无剧本，先运行流水线。</div>`; return; }
  const st = d.structure || {}, viol = st.violations || [];
  const beatWindow = (v) => (v >= 0.22 && v <= 0.25) || (v >= 0.48 && v <= 0.52) || (v >= 0.78 && v <= 0.82);
  box.innerHTML = `
    <div class="stats" style="margin-bottom:16px">
      <div class="stat"><div class="k">${d.scenes.length}</div><div class="l">第 ${CUR_EP} 集场次</div></div>
      <div class="stat"><div class="k">${esc(d.form)}</div><div class="l">剧集形态</div></div>
      <div class="stat"><div class="k">15/15</div><div class="l">Save the Cat 拍</div></div>
      <div class="stat"><div class="k">${viol.length ? "⚠ " + viol.length : "✓ 0"}</div><div class="l">结构问题</div></div>
    </div>
    <div class="card" style="margin-bottom:16px"><b style="font-size:var(--fs-table)">结构健康度</b>
      <div class="kv" style="grid-template-columns:150px 1fr;font-size:var(--fs-sm);margin-top:8px">
        <div class="k">Plot Point I</div><div>${esc(st.ppi)}（应 0.22–0.25）</div>
        <div class="k">Midpoint</div><div>${esc(st.midpoint)}（应 0.48–0.52）</div>
        <div class="k">Plot Point II</div><div>${esc(st.ppii)}（应 0.78–0.82）</div>
        <div class="k">Truby 四节点</div><div>${(st.truby || []).map(esc).join(" · ")}</div>
      </div>
      ${viol.length ? `<div style="color:var(--bad);margin-top:8px;font-size:var(--fs-sm)">${viol.map(esc).join("；")}</div>` : ""}
    </div>
    <div style="display:flex;gap:8px;margin:14px 0 10px">
      <span class="pill gold">分镜表</span>
      <span class="pill" style="cursor:pointer" onclick="showScreenplay()">剧本原文</span></div>
    <div class="muted" style="margin-bottom:8px">场次（点击编辑目标/冲突/结果，M2.5 rewrite）</div>
    <div id="screenplay" class="hide"></div>
    <div id="memview"></div>
    <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr))">
      ${d.scenes.map(sc => `<div class="card" style="cursor:pointer" onclick="editScene(${sc.number})">
        <div style="display:flex;justify-content:space-between"><b style="font-size:var(--fs-table)">场 ${sc.number}</b>
          <span class="pill" style="font-size:var(--fs-micro)">${esc((sc.beats || [])[0] || "")}</span></div>
        <div class="muted" style="font-size:var(--fs-meta);margin-top:6px;line-height:1.7">目标：${esc(sc.goal)}<br>冲突：${esc(sc.conflict)}<br>结果：${esc(sc.result)}</div></div>`).join("")}
    </div>`;
  renderMemory();
}
async function showScreenplay() {
  const box = $("#screenplay"); if (!box) return;
  if (!box.classList.contains("hide")) { box.classList.add("hide"); return; }
  try { const d = await api("/api/dramas/" + CUR.id + "/screenplay");
    box.classList.remove("hide");
    box.innerHTML = `<pre style="white-space:pre-wrap;font-family:'Courier New',monospace;font-size:var(--fs-sm);line-height:1.7;color:var(--fg);background:#0a0e15;border:1px solid var(--line);border-radius:10px;padding:16px;max-height:400px;overflow:auto">${esc(d.text)}</pre>`;
  } catch (e) { toast("" + e.message); }
}
async function renderMemory() {
  const box = $("#memview"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/memory"); } catch (e) { return; }
  if (!d.context) return;
  box.innerHTML = `<h2 style="font-size:var(--fs-table);margin-top:18px">长篇连贯性记忆 <span class="hint">C1 四层 · 跨集不跑偏</span></h2>
    <pre style="white-space:pre-wrap;font-size:var(--fs-sm);color:var(--fg);background:#0a0e15;border:1px solid var(--line);border-radius:10px;padding:14px">${esc(d.context)}</pre>
    <div style="margin:8px 0"><span class="pill ${d.violations.length ? "bad" : "ok"}">记忆层 ${d.violations.length ? d.violations.length + " 项超限" : "合规"}</span>
      <span class="pill ${d.audit.length ? "bad" : "ok"}" style="margin-left:6px">因果链审计 ${d.audit.length ? d.audit.length + " 处问题" : "通过"}</span></div>
    <div class="muted" style="font-size:var(--fs-meta)">因果链变更记录（触发→过程→结果）示例：${d.change_records.slice(0,2).map(r => `场${r.scene_no}: ${esc(r.trigger)}→${esc(r.process)}→${esc(r.result)}`).join("；") || "—"}</div>`;
}
async function editScene(no) {
  const d = await api("/api/dramas/" + CUR.id + "/script?episode=" + CUR_EP);
  const sc = d.scenes.find(x => x.number === no); if (!sc) return;
  const modal = document.createElement("div"); modal.className = "modal"; modal.id = "scmodal";
  modal.innerHTML = `<div class="box" style="max-width:560px">
    <div class="mhead"><h2>编辑 场 ${no}</h2><button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="mbody">
      <div class="muted" style="font-size:var(--fs-sm);margin-bottom:12px">单改纪律：一次只改需要改的字段，改后自动复校验结构。</div>
      <div class="stack">
        <label class="muted" style="font-size:var(--fs-meta)">事件</label><input id="s_event" value="${esc(sc.event || "")}">
        <label class="muted" style="font-size:var(--fs-meta)">目标</label><input id="s_goal" value="${esc(sc.goal || "")}">
        <label class="muted" style="font-size:var(--fs-meta)">冲突</label><input id="s_conflict" value="${esc(sc.conflict || "")}">
        <label class="muted" style="font-size:var(--fs-meta)">结果</label><input id="s_result" value="${esc(sc.result || "")}">
        <button class="btn" onclick="saveScene(${no})">保存并复校验</button>
      </div></div></div>`;
  document.body.appendChild(modal);
}
async function saveScene(no) {
  const body = { event: $("#s_event").value, goal: $("#s_goal").value,
                 conflict: $("#s_conflict").value, result: $("#s_result").value };
  try { const r = await api("/api/dramas/" + CUR.id + "/script/scene/" + no + "?episode=" + CUR_EP, { method: "PUT",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    closeModal();
    toast(r.violations.length ? "保存成功，但结构有 " + r.violations.length + " 处问题" : "已保存，结构合规");
    renderScript();
  } catch (e) { toast("" + e.message); }
}

/* 门禁工作台（AADO 好莱坞级：五门禁署名 + 理由码 + 二元清单） */
async function renderGates() {
  const box = $("#gateview"); if (!box) return;
  const gates = await api("/api/dramas/" + CUR.id + "/gates");
  box.innerHTML = `<div class="muted" style="margin-bottom:12px">五门禁 = 剧本 → 定妆 → 分镜 → 成片 → 母版，每关署名 + 理由码；无署名即视为未通过（D6/EL-10）。</div>
    <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(230px,1fr))">
    ${gates.map(g => `<div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b style="font-size:var(--fs-body)">${ico("gate")} ${esc(g.label)}</b>
        <span class="pill ${g.decision === "pending" ? "" : "ok"}">${g.decision === "pending" ? "待签" : "已通过"}</span></div>
      <div class="kv" style="grid-template-columns:88px 1fr;font-size:var(--fs-sm);margin-top:10px">
        <div class="k">署名</div><div>${esc(g.approver)}</div>
        <div class="k">岗位</div><div>${esc(g.role)}</div>
        <div class="k">理由码</div><div>${esc(g.reason_code || "—")}</div>
      </div>
      <div style="margin-top:10px;font-size:var(--fs-meta)">${g.checklist.map(c => `<div style="padding:2px 0;color:${c.pass ? "var(--ok)" : "var(--dim)"}">${c.pass ? "✓" : "○"} ${esc(c.item)}</div>`).join("")}</div>
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
    return `<div title="镜${sh.shot_no} ${sh.size} ${sh.move} ${sh.duration}s" style="flex:0 0 ${w}%;height:44px;background:${SIZE_COLOR[sh.size]||"#4a5f7d"};border-right:1px solid #0a0c10;display:flex;align-items:center;justify-content:center;font-size:var(--fs-micro);color:#cdd7e5;overflow:hidden">${sh.shot_no}</div>`;
  }).join("");
  const markers = d.acts.map(a => `<div style="position:absolute;left:${a.at / total * 100}%;top:-6px;bottom:-20px;border-left:1px dashed var(--accent);font-size:var(--fs-micro);color:var(--accent);padding-left:3px;white-space:nowrap">${esc(a.name)}</div>`).join("");
  box.innerHTML = `
    <div class="stats" style="margin-bottom:16px">
      <div class="stat"><div class="k">${total}s</div><div class="l">成片时长</div></div>
      <div class="stat"><div class="k">${d.shot_count}</div><div class="l">镜头数</div></div>
      <div class="stat"><div class="k">${d.asl}s</div><div class="l">平均镜头长度 ASL</div></div>
      <div class="stat"><div class="k">${d.asl_in_band ? "✓" : "⚠"}</div><div class="l">ASL 在 2–4s 参考带</div></div>
    </div>
    <h2 style="font-size:var(--fs-table)">时间线 <span class="hint">按镜头时长比例 · 虚线为幕结构标记</span></h2>
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
  try { await api("/api/candidates/" + cid + "/select", { method: "POST" }); toast("已选定"); closeModal(); await sbOpen(shotId); }
  catch (e) { toast("" + e.message); }
}
/* 阶段专属富展示 */
function stageBody(stage, art) {
  // 剧本：场次列表（场次 / 拍 / 目标-冲突-结果）
  if (art.scene_list) {
    return `<div class="muted" style="margin-bottom:10px">形态 <b>${esc(art.form)}</b> · ${art.scenes} 场 · 15 拍覆盖 · Truby 四节点</div>
      <div class="cards" style="grid-template-columns:repeat(auto-fill,minmax(190px,1fr))">
      ${art.scene_list.map(sc => `<div class="card"><div style="display:flex;justify-content:space-between">
        <b style="font-size:var(--fs-table)">场 ${sc.no}</b><span class="pill" style="font-size:var(--fs-micro)">${esc((sc.beats||[])[0]||"")}</span></div>
        <div class="muted" style="font-size:var(--fs-meta);margin-top:6px;line-height:1.7">
          目标：${esc(sc.goal)}<br>冲突：${esc(sc.conflict)}<br>结果：${esc(sc.result)}</div></div>`).join("")}</div>`;
  }
  // 选角：角色工作台（参考 LumenX CharacterWorkbench / Cast）
  if (art.character && art.anchors) {
    const VIEWNAME = { front: "正面", side: "侧面", back: "背面", "3_4": "3/4 侧", full_body: "全身", expression: "表情" };
    return `<div class="muted" style="margin-bottom:10px">角色定妆 = 后续所有画面的唯一视觉事实来源。锚点图集是与一致性检测（M6）共享的基准。</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px">
        ${art.anchors.map(a => `<div class="asset"><div class="thumb" style="aspect-ratio:3/4">${ico("face")}
          <span class="tag">${esc(VIEWNAME[a] || a)}</span></div>
          <div class="body"><div class="muted" style="font-size:var(--fs-meta)">锚点 · ${esc(a)}</div></div></div>`).join("")}
      </div>
      <div class="kv" style="margin-top:16px">
        <div class="k">角色</div><div>${esc(art.character)}</div>
        <div class="k">音色绑定</div><div><span class="pill gold">${esc(art.voice)}</span></div>
        <div class="k">锚点数量</div><div>${art.anchor_count} 张（≥3 达标）</div>
        <div class="k">定妆门禁</div><div><span class="pill ok">署名 + 理由码齐备</span></div>
      </div>`;
  }
  // 立项：包型 + 交付规格
  if (art.package !== undefined && art.title !== undefined) {
    const ds = CUR.spec || {};
    const target = ds.master ? `${ds.master} 主母版 · ${ds.platform} 平台版 · ${ds.derived} 衍生（EL-01）`
      : "2.39:1 主母版 · 16:9 平台版 · 9:16 衍生（EL-01）";
    return `<div class="kv">
        <div class="k">片名</div><div>${esc(art.title)}</div>
        <div class="k">包型</div><div><span class="pill gold">${esc(art.package)}</span></div>
        <div class="k">交付目标</div><div>${esc(target)}</div>
        <div class="k">生成母版口径</div><div>16:9 open gate 唯一生成母版，其他画幅由同一素材派生</div>
      </div>`;
  }
  // 存储：母版唯一 + 派生血缘树
  if (art.master && art.derived) {
    const derived = ["2.39:1 主母版", "16:9 平台版", "9:16 竖屏衍生", "HDR10（可选）", "5.1 环绕（可选）", "48fps（可选）"];
    return `<div class="muted" style="margin-bottom:12px">一次生成、多端派生：所有版本由同一生成母版派生，禁止单画幅重复生成（EL-01）。</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div class="card" style="border-color:var(--accent);background:var(--accent-soft)">
          <b>${ico("master")} 生成母版</b> <span class="pill gold">${esc(art.master)}</span>
          <div class="muted" style="font-size:var(--fs-meta);margin-top:4px">唯一 · 16:9 open gate 最高可用分辨率</div></div>
        <div style="text-align:center;color:var(--dim);font-size:var(--fs-h3)">↓ 派生</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px">
          ${derived.map(d => `<div class="card" style="padding:12px"><div style="font-size:var(--fs-sm)">${esc(d)}</div>
            <div class="muted" style="font-size:var(--fs-micro);margin-top:4px">parent → 生成母版</div></div>`).join("")}
        </div>
      </div>
      <div class="kv" style="margin-top:14px">
        <div class="k">血缘规则</div><div>派生必须指向母版，可回溯；母版唯一约束（EL-01）</div>
        <div class="k">内容寻址</div><div>按 sha256 索引，跨镜/跨集/跨项目复用</div>
      </div>`;
  }
  // 协作：RBAC
  if (art.rbac) {
    return `<div class="kv">
        <div class="k">权限矩阵</div><div>${esc(art.rbac)}</div>
        <div class="k">岗位</div><div>showrunner · 导演 · 编剧 · 剪辑 · 声音 · 调色 · QC · 法务</div>
        <div class="k">门禁署名</div><div>岗位绑定 + 自审自批禁令 + 理由码</div>
        <div class="k">审计</div><div>谁/何时/何操作/为何（可追溯）</div>
      </div>`;
  }
  // 供应商：能力矩阵 + 路由
  if (art.kinds && art.route) {
    return `<div class="kv">
        <div class="k">接入类型</div><div>${esc(art.kinds)}</div>
        <div class="k">路由</div><div>${esc(art.route)}</div>
        <div class="k">能力矩阵</div><div>参考图/首尾帧/多镜头/运镜/焦距景深/原生音频…</div>
        <div class="k">许可</div><div><span class="pill bad">GPL 不内置</span> <span class="pill bad">InsightFace 非商用</span></div>
      </div>`;
  }
  // VFX：物理骨架 + 修复优先级
  if (art.skeleton !== undefined) {
    return `<div class="kv">
        <div class="k">物理骨架</div><div>${esc(art.skeleton)}</div>
        <div class="k">修复优先级</div><div>局部修复 → 局部重生成 → 整镜重抽（E-35）</div>
        <div class="k">VFX 门禁</div><div>未完成 VFX 不进成片</div>
        <div class="k">工具许可</div><div>GPL 传染风险不得内置分发</div>
      </div>`;
  }
  // 配音：音画同步 + 电平
  if (art.offset_ms !== undefined) {
    return `<div class="stats">
        <div class="stat"><div class="k">${art.offset_ms}ms</div><div class="l">音画偏移（目标 ≤±25ms）</div></div>
        <div class="stat"><div class="k">✓</div><div class="l">ITU 容差 +90/−185ms</div></div>
        <div class="stat"><div class="k">≤1dB</div><div class="l">角色间对白电平差</div></div>
        <div class="stat"><div class="k">独立轨</div><div class="l">旁白与对白分离</div></div>
      </div>
      <div class="muted" style="margin-top:10px">音色全剧显式绑定，未绑定即阻断出片；口型仅做近景正脸镜。</div>`;
  }
  // 配乐：Cue + 授权
  if (art.platform && art.cue !== undefined) {
    return `<div class="kv">
        <div class="k">配乐平台</div><div><span class="pill gold">${esc(art.platform)}</span></div>
        <div class="k">授权状态</div><div><span class="pill ok">可商用（档位合规）</span></div>
        <div class="k">总线</div><div>四层 stem：对白 D / 音乐 M / 音效 E / 环境 Amb（逐帧等长）</div>
        <div class="k">响度</div><div>归档母版 −23.0 LUFS / ≤−1 dBTP</div>
        <div class="k">可懂度</div><div>对白高于稳态掩蔽 ≥15 dB</div>
      </div>`;
  }
  // 合规：权利链 + AI 标识
  if (art.ai_label) {
    return `<div class="kv">
        <div class="k">AI 标识</div><div><span class="pill ok">${esc(art.ai_label)}</span></div>
        <div class="k">交付前合规</div><div><span class="pill ok">${esc(art.compliance)}</span></div>
        <div class="k">权利链</div><div>作品 → 改编 → 素材 → 成片（可追溯）</div>
        <div class="k">工会边界</div><div>AI 不得署名 writer；AI 材料不计入 source material</div>
        <div class="k">数字替身</div><div>书面同意 + 补偿 + 范围（缺一禁止生成）</div>
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
    return `<div style="margin-bottom:12px"><button class="btn" onclick="downloadQC()">${ico("download")} 下载 QC 报告</button></div>
      <div class="kv">
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
    const ds = CUR.spec || {};
    const master = ds.master || "2.39:1", plat = ds.platform || "16:9", derived = ds.derived || "9:16";
    const versions = [
      { n: `${master} 主母版`, s: "保证" }, { n: `${plat} 平台版`, s: "保证" }, { n: `${derived} 衍生`, s: "保证" },
      { n: "HDR10", s: "可选" }, { n: "5.1 环绕", s: "可选" }, { n: "48fps", s: "可选" }];
    return `<div style="margin-bottom:12px"><button class="btn" onclick="previewSheet()">在线预览交付单</button>
        <button class="btn ghost" onclick="downloadSheet()" style="margin-left:8px">${ico("download")} 下载</button>
        <button class="btn ghost" onclick="downloadReceipt()" style="margin-left:8px">${ico("shield")} 签名收据</button></div>
      <div id="versionbox" style="margin-bottom:16px"></div>
      <div class="muted" style="margin-bottom:10px">交付版本清单（标注保证 / 可选 / 需确认，EL-11）</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:16px">
        ${versions.map(v => `<div class="card" style="padding:12px"><div style="font-size:var(--fs-sm)">${esc(v.n)}</div>
          <span class="pill ${v.s === "保证" ? "ok" : "gold"}" style="font-size:var(--fs-micro);margin-top:6px">${esc(v.s)}</span></div>`).join("")}
      </div>
      <div class="kv">
        <div class="k">交付画幅</div><div><span class="pill gold">${esc(master)}</span> 主母版 · <span class="pill">${esc(plat)}</span> 平台版</div>
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
function editProject(p) {
  const modal = document.createElement("div"); modal.className = "modal"; modal.id = "pmmodal";
  modal.innerHTML = `<div class="box" style="max-width:560px">
    <div class="mhead"><h2>项目设置</h2><button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="mbody"><div class="muted" style="font-size:var(--fs-sm);margin-bottom:12px">已产出阶段修改会提示重跑影响（M1.4-F03）。</div>
    <div class="stack">
      <label class="muted" style="font-size:var(--fs-meta)">片名</label><input id="e_title" value="${esc(p.title)}">
      <label class="muted" style="font-size:var(--fs-meta)">Logline</label><input id="e_logline" value="${esc(p.logline)}">
      <div class="row2">
        <div><label class="muted" style="font-size:var(--fs-meta)">目标平台</label><input id="e_platform" value="${esc(p.platform || "")}"></div>
        <div><label class="muted" style="font-size:var(--fs-meta)">题材</label><input id="e_genre" value="${esc(p.genre || "")}"></div></div>
      <div class="row2">
        <div><label class="muted" style="font-size:var(--fs-meta)">分级</label><select id="e_rating">
          ${["全龄","12+","16+"].map(r => `<option ${r === p.rating ? "selected" : ""}>${r}</option>`).join("")}</select></div>
        <div><label class="muted" style="font-size:var(--fs-meta)">单集时长</label><select id="e_minutes">
          ${[22,30,45].map(m => `<option value="${m}" ${m === p.minutes ? "selected" : ""}>${m} 分钟/集</option>`).join("")}</select></div></div>
      <button class="btn" onclick="saveProject(${p.id})">保存</button>
    </div></div></div>`;
  document.body.appendChild(modal);
}
async function saveProject(id) {
  const body = { title: $("#e_title").value, logline: $("#e_logline").value,
    platform: $("#e_platform").value, genre: $("#e_genre").value,
    rating: $("#e_rating").value, minutes: parseInt($("#e_minutes").value, 10) };
  try { await api("/api/dramas/" + id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    closeModal(); toast("已保存"); viewProject(id);
  } catch (e) { toast("" + e.message); }
}
function pickEp(id, n) { CUR_EP = n; viewProject(id); }
async function produceAll(id) {
  const b = $("#prodbtn"); b.disabled = true;
  const t0 = Date.now();
  const tick = setInterval(() => { b.textContent = "制作中… " + Math.round((Date.now() - t0) / 1000) + "s"; }, 500);
  try { const r = await api("/api/dramas/" + id + "/produce", { method: "POST" });
    toast("完成：" + r.stages_passed + "/" + r.stages_total + " 阶段 · " + r.shots + " 镜 · 成片 " + r.total_duration + "s");
    CUR.stage = null; viewProject(id);
  } catch (e) { toast("" + e.message); }
  clearInterval(tick);
  b.disabled = false; b.innerHTML = ico("sparkle") + " 一键全流程";
}
async function runPipeline(id) {
  const b = $("#runbtn"); b.disabled = true;
  const t0 = Date.now();
  const tick = setInterval(() => { b.textContent = "运行中… " + Math.round((Date.now() - t0) / 1000) + "s"; }, 500);
  try { const r = await api("/api/dramas/" + id + "/run", { method: "POST" });
    toast("流水线完成 " + r.summary.passed + "/" + r.summary.total); CUR.stage = null; viewProject(id);
  } catch (e) { toast("" + e.message); b.disabled = false; b.innerHTML = ico("play") + " 运行流水线"; }
  finally { clearInterval(tick); }
}

/* ---------- 资产库 ---------- */
async function viewAssets() {
  const d = await api("/api/assets/summary?limit=120");
  const chars = d.characters || [], shots = d.shots || [];
  setMain({
    title: "资产库",
    top: `<div class="right"><span class="pill">${chars.length} 角色</span><span class="pill">${shots.length} 镜头</span></div>`,
    body: `${chars.length ? `<h2>角色 <span class="hint">定妆锚点 + 音色</span></h2>
      <div class="cards">${chars.map(c => `<div class="asset"><div class="thumb">${ico("face")}<span class="tag">${esc(c.project)}</span></div>
        <div class="body"><h4>${esc(c.name)}</h4>
          <div class="meta"><span>音色 ${esc(c.voice)}</span>${(c.anchors||[]).map(a => `<span>${esc(VIEWNAME[a]||a)}</span>`).join("")}</div></div></div>`).join("")}</div>` : ""}
      ${shots.length ? `<h2>镜头 <span class="hint">按状态</span></h2>
      <div class="cards">${shots.slice(0, 60).map(s => `<div class="asset"><div class="thumb">${ico(s.status === "已生成" || s.status === "已选定" ? "frame" : "film")}
        <span class="tag">${esc(s.project)} · 镜${s.shot_no}</span></div>
        <div class="body"><div class="meta"><span>${esc(s.size)}</span><span>${esc(s.move)}</span><span>${s.duration}s</span>
          <span class="pill ${s.status === "已生成" || s.status === "已选定" ? "ok" : ""}" style="font-size:var(--fs-micro)">${esc(s.status)}</span></div></div></div>`).join("")}</div>` : ""}
      ${(!chars.length && !shots.length) ? `<div class="card empty">${ico("layers")}<div>还没有资产</div><div class="muted" style="font-size:var(--fs-sm);margin-top:4px">先在项目里运行流水线</div></div>` : ""}`,
  }, true);
}

/* ---------- 任务队列（PG SKIP LOCKED 队列的运维视图） ---------- */
const JOB_STATUS_COLOR = { queued: "muted", running: "gold", completed: "ok", failed: "bad", waiting_human: "gold", retry_exhausted: "bad", cancelled: "muted" };
const JOB_STATUS_LABEL = { queued: "排队中", running: "运行中", completed: "已完成", failed: "失败", waiting_human: "待人工", retry_exhausted: "重试耗尽", cancelled: "已取消" };
const JOB_TYPE_LABEL = { adapt: "剧本开发", casting: "选角定妆", shot_video: "镜头生成", generate_voice: "配音", music: "配乐" };
let _jobsTimer = null;
function stopJobsPoll() {
  if (_jobsTimer) { clearInterval(_jobsTimer); _jobsTimer = null; }
}
function jobActionHtml(j) {
  if (j.status === "failed" || j.status === "retry_exhausted")
    return `<button class="btn ghost sm" onclick="jobRetry(${j.id})">重试</button>`;
  if (j.status === "queued" || j.status === "running")
    return `<button class="btn ghost sm" onclick="jobCancel(${j.id},${j.lease_epoch || 0})">取消</button>`;
  if (j.status === "waiting_human")
    return `<button class="btn sm" onclick="jobResolve(${j.id},true)">通过</button>
      <button class="btn ghost sm" style="margin-left:4px" onclick="jobResolve(${j.id},false)">驳回</button>`;
  return "—";
}
function jobRowsHtml(jobs) {
  if (!jobs.length) return `<tr><td colspan="8" style="text-align:center;color:var(--dim)">队列为空</td></tr>`;
  return jobs.map(j => {
    const pv = Math.max(0, Math.min(100, Number(j.progress) || 0));
    return `<tr><td>${j.id}</td><td>${esc(j.project || "—")}</td>
    <td>${esc(JOB_TYPE_LABEL[j.type] || j.type)}</td>
    <td><span class="pill ${JOB_STATUS_COLOR[j.status] || "muted"}">${esc(JOB_STATUS_LABEL[j.status] || j.status)}</span></td>
    <td style="min-width:110px"><div class="progress"><i style="width:${pv}%"></i></div>
      <span class="muted" style="font-size:var(--fs-meta)">${pv}%</span></td>
    <td>${j.attempts || 0}/${j.attempt_limit || 0}</td>
    <td>${j.error_code ? `<span class="muted" title="${esc(j.error_class || "")}">${esc(j.error_code)}</span>` : "—"}</td>
    <td>${jobActionHtml(j)}</td></tr>`;
  }).join("");
}
async function viewJobs() {
  const d = await api("/api/jobs/summary?limit=100");
  const jobs = d.jobs || [];
  setMain({
    title: "任务",
    top: `<div class="right"><span class="pill" id="jobstotal">已显示 ${jobs.length} / 共 ${d.total || 0} 个任务</span></div>`,
    body: `<div class="card">
      <div class="toolbar">
        <input id="job_pid" placeholder="项目 ID" style="max-width:220px">
        <select id="job_type" style="max-width:200px">
          <option value="adapt">剧本开发</option><option value="casting">选角定妆</option>
          <option value="shot_video">镜头生成</option><option value="generate_voice">配音</option><option value="music">配乐</option></select>
        <button class="btn" onclick="submitJob()">入队任务</button>
      </div></div>
    <h2>任务列表 <span class="hint">每 5 秒刷新</span></h2>
    <div class="card table-scroll"><table><thead><tr><th>#</th><th>项目</th><th>类型</th><th>状态</th><th>进度</th><th>尝试</th><th>失败原因</th><th>操作</th></tr></thead>
      <tbody id="jobstbl">${jobRowsHtml(jobs)}</tbody></table></div>`,
  }, true);
  stopJobsPoll();
  _jobsTimer = setInterval(refreshJobRows, 5000);
}
async function refreshJobRows() {
  if (document.hidden || document.querySelector(".modal")) return;
  try {
    const d = await api("/api/jobs/summary?limit=100");
    const jobs = d.jobs || [];
    const t = $("#jobstbl"); if (!t) { stopJobsPoll(); return; }
    t.innerHTML = jobRowsHtml(jobs);
    const tot = $("#jobstotal");
    if (tot) tot.textContent = `已显示 ${jobs.length} / 共 ${d.total || 0} 个任务`;
  } catch (e) { /* 轮询失败保留上次好数据，不打断操作 */ }
}
async function submitJob(btn) {
  const pid = ($("#job_pid") || {}).value, type = ($("#job_type") || {}).value;
  if (!pid) return toast("填项目 ID");
  try { await api("/api/drama-jobs", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: pid, type: type, idempotency_key: pid + ":" + type + ":" + Date.now() }) });
    toast("已入队"); viewJobs();
  } catch (e) { toast("" + e.message); }
}
async function jobRetry(id) {
  try { await api("/api/drama-jobs/" + id + "/retry", { method: "POST" }); toast("已重试"); viewJobs(); }
  catch (e) { toast("" + e.message); }
}
async function jobCancel(id, epoch) {
  confirmDialog("取消任务？", "任务 #" + id + " 将被标记为已取消（epoch " + epoch + "）；如需继续可重新入队。",
    async () => {
      try {
        await api("/api/drama-jobs/" + id + "/cancel", { method: "POST",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify({ epoch }) });
        toast("已取消"); viewJobs();
      } catch (e) { toast("取消失败：" + e.message); }
    }, "确认取消");
}
async function jobResolve(id, approve) {
  try {
    await api("/api/drama-jobs/" + id + "/resolve", { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approve, reason_code: approve ? null : "operator_reject" }) });
    toast(approve ? "已通过" : "已驳回"); viewJobs();
  } catch (e) { toast("操作失败：" + e.message); }
}
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && $("#jobstbl")) refreshJobRows();
});

async function downloadReceipt() {
  try { const d = await api("/api/dramas/" + CUR.id + "/receipt", { method: "POST" });
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = (d.project || "project") + "_receipt.json"; a.click(); URL.revokeObjectURL(url);
    toast("收据已生成（签名" + (d.signature ? "已签" : "无密钥") + "）");
  } catch (e) { toast("" + e.message); }
}
async function downloadQC() {
  try {
    const d = await api("/api/dramas/" + CUR.id + "/qc-report");
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = (d.project || "project") + "_qc_report.json"; a.click();
    URL.revokeObjectURL(url); toast("QC 报告已下载（" + d.summary.passed + "/" + d.summary.total + " 通过）");
  } catch (e) { toast("" + e.message); }
}
async function downloadSheet() {
  try {
    const d = await api("/api/dramas/" + CUR.id + "/delivery-sheet");
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = (d.project.title || "project") + "_delivery_sheet.json"; a.click();
    URL.revokeObjectURL(url); toast("交付单已下载");
  } catch (e) { toast("" + e.message); }
}

/* ---------- 生成台 Playground（参考 LumenX Playground） ---------- */
let PG_KIND = "图像生成";
async function viewPlayground() {
  const d = await api("/api/playground/kinds");
  const tasks = await api("/api/playground/tasks");
  setMain({
    title: "生成台",
    top: `<div class="right"><span class="pill">${tasks.length} 次生成</span></div>`,
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
      <div class="asset"><div class="thumb">${ico({ "图像生成":"frame","文生视频":"film","图生视频":"film","参考生视频":"film","配音":"wave","配乐":"music" }[t.kind] || "lab")}
        <span class="tag">${esc(t.kind)}</span></div>
        <div class="body"><div class="desc">${esc(t.prompt)}</div>
          <div class="meta"><span>${esc(t.model)}</span><span class="pill ok" style="font-size:var(--fs-micro)">${esc(t.status)}</span></div></div></div>`).join("")}</div>`
      : `<div class="card empty">${ico("lab")}<div>还没有生成记录</div><div class="muted" style="font-size:var(--fs-sm);margin-top:4px">选一个模式，输入提示词即可生成</div></div>`}`,
  }, true);
}
async function pgGenerate() {
  const prompt = ($("#pg_prompt") || {}).value || "";
  if (!prompt.trim()) return toast("请输入提示词");
  try { await api("/api/playground/generate", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: PG_KIND, prompt }) });
    toast("已生成"); viewPlayground();
  } catch (e) { toast("" + e.message); }
}

/* ---------- 模型 ---------- */
async function viewModels() {
  const d = await api("/api/models/config");
  setMain({
    title: "模型配置",
    top: `<div class="right"><a href="/models"><button class="btn ghost sm">编辑配置</button></a></div>`,
    body: `<div class="muted" style="font-size:var(--fs-sm);margin-bottom:12px">Key 只显示末四位、永不回传明文；${esc((d.persistence || {}).note || "配置写入数据库")}。</div>
    <div class="cards">${Object.entries(d.config).map(([k, c]) => {
      const on = c.api_key_set;
      return `<div class="asset"><div class="thumb">${ico({ text: "doc", video: "film", image: "frame", tts: "wave", music: "music", lipsync: "face" }[k] || "route")}</div>
        <div class="body"><h4 style="display:flex;justify-content:space-between">${k}
          <span class="pill ${on ? "ok" : ""}">${on ? "已配置" : "Mock"}</span></h4>
          <div class="desc">${esc(c.model || "未填模型")}${on && c.api_key_hint ? ` · Key ${esc(c.api_key_hint)}` : ""}</div></div></div>`;
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
    title: "设置",
    top: `<div class="right"></div>`,
    body: `<div class="card"><div class="kv">
        <div class="k">登录账户</div><div>admin</div>
        <div class="k">API 文档</div><div><a href="/docs" target="_blank">/docs</a></div>
        <div class="k">健康检查</div><div><a href="/health" target="_blank">/health</a></div>
      </div><div style="margin-top:18px"><button class="btn ghost" onclick="toggleTheme()">切换深色 / 浅色</button>
        <button class="btn ghost" onclick="logout()">退出登录</button></div></div>`,
  });
}

/* ---------- 启动 ---------- */
function boot() {
  applyTheme();
  if (!hasToken()) return renderLogin();
  const r = parseHash();
  if (r.name === "project") CUR.stage = r.stage || null;
  navigate(r.name, r.name === "project" ? r.param : undefined).catch(viewError);
}
boot();

/* ── 模块参数（每个模块关键输入 + 推荐值） ── */
function fieldHtml(f, val) {
  const v = val === undefined ? f.default : val;
  const rec = f.rec ? `<span class="rec">· ${esc(f.rec)}</span>` : "";
  let control;
  if (f.type === "select") {
    control = `<select data-pk="${esc(f.key)}">${(f.options || []).map(o =>
      `<option value="${esc(o)}"${String(o) === String(v) ? " selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
  } else if (f.type === "bool") {
    control = `<select data-pk="${esc(f.key)}"><option value="true"${v ? " selected" : ""}>是</option><option value="false"${!v ? " selected" : ""}>否</option></select>`;
  } else if (f.type === "number") {
    control = `<input type="number" data-pk="${esc(f.key)}" value="${esc(v)}"${f.min !== undefined ? ` min="${f.min}"` : ""}${f.max !== undefined ? ` max="${f.max}"` : ""}>`;
  } else {
    control = `<input data-pk="${esc(f.key)}" value="${esc(v)}">`;
  }
  return `<div class="fld"><small>${esc(f.label)}${rec}</small>${control}</div>`;
}
async function attachParams(st) {
  if (!st) return;
  const el = $("#stagedetail"); if (!el) return;
  const mod = (st.stage.match(/^M\d+/) || [""])[0];
  let d; try { d = await api("/api/dramas/" + CUR.id + "/module-params"); } catch (e) { return; }
  const spec = d.modules[mod]; if (!spec) return;
  const panel = document.createElement("details");
  panel.className = "params"; panel.open = false;
  panel.innerHTML = `<summary>参数设置 <span class="muted">· ${esc(spec.title)} · 未填用推荐默认值</span></summary>
    <div class="grid3" style="margin-top:12px">${spec.fields.map(f => fieldHtml(f, spec.values[f.key])).join("")}</div>
    <div class="form-actions"><button class="btn sm" id="pmsave">保存参数</button>
      <span class="muted" style="font-size:var(--fs-meta)">参数参与该模块生成；留空使用推荐值</span></div>`;
  const detail = el.querySelector(".detail") || el;
  detail.appendChild(panel);
  panel.querySelector("#pmsave").onclick = async () => {
    const values = {};
    panel.querySelectorAll("[data-pk]").forEach(inp => {
      const k = inp.dataset.pk; let v = inp.value;
      const f = spec.fields.find(x => x.key === k);
      if (f && f.type === "number") v = Number(v);
      else if (f && f.type === "bool") v = (v === "true");
      values[k] = v;
    });
    try { await api("/api/dramas/" + CUR.id + "/module-params/" + mod, { method: "PUT",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values }) });
      toast("参数已保存");
    } catch (e) { toast("保存失败：" + e.message); }
  };
}

/* ── 使用指南 ── */
let HELP_CUR = "_intro";
function helpItemHtml(id, label) {
  return `<div class="help-item ${id === HELP_CUR ? "on" : ""}" data-g="${id}" onclick="pickHelp('${id}')">${esc(label)}</div>`;
}
function renderHelpContent() {
  const g = (window.GUIDES || {})[HELP_CUR] || {};
  const list = (arr, cls) => (arr || []).map(x => `<li>${esc(x)}</li>`).join("");
  $("#helpcontent").innerHTML = `
    <div class="help-eyebrow">${esc(window.GUIDES[HELP_CUR] ? (HELP_CUR === "_intro" ? "GETTING STARTED" : HELP_CUR) : "")}</div>
    <h2 class="help-title">${esc(g.title || "")}</h2>
    <p class="help-what">${esc(g.what || "")}</p>
    ${g.steps ? `<div class="help-sec"><div class="help-sec-t">怎么用</div><ol>${list(g.steps)}</ol></div>` : ""}
    ${g.params ? `<div class="help-sec"><div class="help-sec-t">参数与调优</div><ul>${list(g.params)}</ul></div>` : ""}
    ${g.tips ? `<div class="help-sec"><div class="help-sec-t">要点</div><ul>${list(g.tips)}</ul></div>` : ""}
    ${g.pitfalls ? `<div class="help-sec"><div class="help-sec-t">注意</div><ul>${list(g.pitfalls)}</ul></div>` : ""}`;
}
function pickHelp(id) {
  HELP_CUR = id;
  $$("#helpmodal .help-item").forEach(x => x.classList.toggle("on", x.dataset.g === id));
  renderHelpContent();
}
function openHelp(module) {
  const G = window.GUIDES || {};
  if (module && G[module]) HELP_CUR = module;
  else if (!G[HELP_CUR]) HELP_CUR = "_intro";
  const order = ["_intro", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M18", "M19"];
  const modal = document.createElement("div");
  modal.className = "modal"; modal.id = "helpmodal";
  modal.innerHTML = `<div class="box help">
    <div class="mhead"><h2>使用指南</h2><button class="btn ghost sm" onclick="closeModal()">关闭</button></div>
    <div class="help-body">
      <nav class="help-nav">
        ${order.map(id => helpItemHtml(id, id === "_intro" ? "总览 · 快速开始" : (G[id] ? `${id} ${G[id].title}` : id))).join("")}
      </nav>
      <div class="help-content" id="helpcontent"></div>
    </div></div>`;
  document.body.appendChild(modal);
  renderHelpContent();
}

/* C6：一键示例项目 */
async function seedDemo() {
  try {
    const d = await api("/api/demos/seed", { method: "POST" });
    toast(d.created ? "示例项目已创建" : "示例项目已存在");
    go("project:" + d.id);
  } catch (e) { toast("创建失败：" + e.message); }
}

/* C5：命令面板（⌘K） */
let _cmdData = null, _cmdIdx = 0, _cmdItems = [];
async function openCommand() {
  let projs = [], assets = null, loadErr = "";
  try { projs = await api("/api/dramas"); } catch (e) { loadErr = e.message; }
  try { assets = await api("/api/assets/summary?limit=60"); } catch (e) { loadErr = loadErr || e.message; }
  const cmds = [
    { label: "概览", kind: "页面", act: () => go("overview") },
    { label: "项目", kind: "页面", act: () => go("projects") },
    { label: "资产库", kind: "页面", act: () => go("assets") },
    { label: "生成台", kind: "页面", act: () => go("playground") },
    { label: "任务", kind: "页面", act: () => go("jobs") },
    { label: "模型配置", kind: "页面", act: () => go("models") },
    { label: "设置", kind: "页面", act: () => go("settings") },
    { label: "使用指南", kind: "操作", act: () => openHelp() },
    { label: "创建示例项目", kind: "操作", act: () => seedDemo() },
    ...projs.map(p => ({ label: p.title, kind: "项目", act: () => go("project:" + p.id) })),
    ...((assets && assets.characters) || []).map(c => ({ label: c.name, kind: "角色 · " + c.project, act: () => go("assets") })),
    ...(loadErr ? [{ label: "项目/资产加载失败：" + loadErr, kind: "错误 · 点击重试", act: () => { closeModal(); openCommand(); } }] : []),
  ];
  _cmdData = cmds; _cmdIdx = 0;
  const modal = document.createElement("div"); modal.className = "modal cmd-modal"; modal.id = "cmdmodal";
  modal.innerHTML = `<div class="cmd-box">
    <input id="cmdq" class="cmd-input" placeholder="搜索项目、页面、操作…" autocomplete="off">
    <div class="cmd-list" id="cmdlist"></div>
    <div class="cmd-foot"><span>↑↓ 选择</span><span>↵ 打开</span><span>Esc 关闭</span></div></div>`;
  document.body.appendChild(modal);
  const q = $("#cmdq"); q.focus();
  q.oninput = () => cmdFilter(q.value);
  q.onkeydown = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); _cmdIdx = Math.min(_cmdIdx + 1, _cmdItems.length - 1); cmdRender(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); _cmdIdx = Math.max(_cmdIdx - 1, 0); cmdRender(); }
    else if (e.key === "Enter") { e.preventDefault(); cmdRun(_cmdItems[_cmdIdx]); }
  };
  cmdFilter("");
}
function cmdFilter(query) {
  const q = (query || "").toLowerCase();
  _cmdItems = _cmdData.filter(x => !q || x.label.toLowerCase().includes(q) || x.kind.toLowerCase().includes(q)).slice(0, 40);
  _cmdIdx = 0; cmdRender();
}
function cmdRender() {
  const el = $("#cmdlist"); if (!el) return;
  el.innerHTML = _cmdItems.length ? _cmdItems.map((x, i) =>
    `<div class="cmd-item ${i === _cmdIdx ? "on" : ""}" onclick="cmdRun(_cmdItems[${i}])">
      <span class="cmd-label">${esc(x.label)}</span><span class="cmd-kind">${esc(x.kind)}</span></div>`).join("")
    : `<div class="cmd-empty">无匹配结果</div>`;
}
function cmdRun(item) {
  if (!item) return;
  closeModal();
  item.act();
}

/* D6：交付单在线预览（数据来自 /delivery-sheet，标注 Mock 状态） */
async function previewSheet() {
  let d; try { d = await api("/api/dramas/" + CUR.id + "/delivery-sheet"); } catch (e) { return toast("加载失败"); }
  const spec = d.spec || {};
  const modal = document.createElement("div"); modal.className = "modal"; modal.id = "sheetmodal";
  modal.innerHTML = `<div class="box" style="max-width:640px">
    <div class="mhead"><h2>交付单 · ${esc((d.project || {}).title || "")}</h2>
      <div><span class="pill">Mock 数据</span><button class="btn ghost sm" style="margin-left:8px" onclick="closeModal()">关闭</button></div></div>
    <div class="mbody">
      <div class="dv-sec">规格</div>
      ${row("主母版", spec.master)}${row("平台版", spec.platform)}${row("衍生版", spec.derived)}
      ${row("可选交付", (spec.optional || []).join("、") || "—")}${row("帧率", spec.fps)}${row("响度", spec.loudness)}${row("真峰值", spec.true_peak)}
      <div class="dv-sec">内容</div>
      ${row("镜头数", (d.content || {}).shots)}${row("总时长", ((d.content || {}).duration_sec || 0) + " 秒")}${row("ASL", (d.content || {}).asl + " 秒")}
      <div class="dv-sec">合规</div>
      ${row("权利状态", d.rights_status)}${row("AI 标识", d.ai_label)}${row("分级", d.rating)}${row("语言", d.language)}${row("色彩标签", d.color_tag)}
      <div class="dv-sec">可选交付标注</div>
      ${Object.entries(d.optional_delivery || {}).map(([k, v]) => row(k, v)).join("")}
      <div class="muted" style="font-size:var(--fs-meta);margin-top:14px">生成时间：${esc(d.generated_at)} · 未接入真实供应商时为 Mock/模拟数据</div>
    </div></div>`;
  document.body.appendChild(modal);
}
function row(k, v) { return `<div class="dv-row"><span class="dv-k">${esc(k)}</span><span class="dv-v">${esc(v == null ? "—" : v)}</span></div>`; }

/* D6：版本历史（真实 Run 记录） */
async function renderVersions() {
  const box = $("#versionbox"); if (!box) return;
  let d; try { d = await api("/api/dramas/" + CUR.id + "/versions"); } catch (e) {
    box.innerHTML = `<div class="muted" style="color:var(--bad);font-size:var(--fs-sm)">版本历史加载失败：${esc(e.message)}
      <button class="btn ghost sm" style="margin-left:8px" onclick="renderVersions()">重试</button></div>`;
    return;
  }
  if (!d.versions || !d.versions.length) return;
  box.innerHTML = `<div class="dv-sec" style="margin-top:0">版本历史 <span class="muted">· ${esc(d.source)}</span></div>
    <div class="dv-versions">${d.versions.slice(0, 8).map(v =>
      `<div class="dv-ver"><span class="pill ${v.deliverable ? "ok" : "gold"}">${esc(v.version)}</span>
        <span class="muted">${esc((v.created_at || "").replace("T", " ").slice(0, 19))}</span>
        <span class="muted">${v.passed}/${v.total} 阶段</span></div>`).join("")}</div>`;
}
