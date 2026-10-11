#!/usr/bin/env python3
"""PRD 治理门禁（强规则一 + 强规则二 + 强规则三）——见 GOVERNANCE.md。

用法：
  python3 tools/prd_guard.py --all                          # 全量结构体检
  python3 tools/prd_guard.py --staged                       # 预提交：暂存区内容 vs HEAD
  python3 tools/prd_guard.py --range origin/main..HEAD      # CI
  python3 tools/prd_guard.py --new-entry --type 修订 --level L2 \
      --files PRD/M5-电影摄影与画面生成.md --refs D7 --summary "说明"   # 生成台账条目
退出码：0 通过；1 违规；2 用法/环境错误。
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRD = ROOT / 'PRD'
VALID_STATUS = {'规划中', '待评审', '已确认', '开发中', '已实现', '已上线', '已废弃'}
VALID_TYPE = {'新增', '修订', '删除', '状态流转', '治理'}
VALID_LEVEL = {'L1', 'L2', '附录', '治理'}
FP_RE = re.compile(r'^M(\d+)\.(\d+)-F(\d{1,3})$')
LEDGER_JSONL = PRD / 'changelog.jsonl'
LEDGER_MD = PRD / 'CHANGELOG.md'
MODULE_DOCS_DIR = ROOT / 'docs' / 'modules'
VALID_TASK_STATUS = {'待开发', '进行中', '已完成', '阻塞', '已废弃'}
TASK_RE = re.compile(r'^M(\d+)-T(\d{2})$')
errors: list[str] = []
warns: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def read(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except FileNotFoundError:
        return ''


def module_files() -> dict[str, Path]:
    out = {}
    for p in sorted(PRD.glob('M*.md')):
        m = re.match(r'^(M\d+)-.+\.md$', p.name)
        if m:
            out[m.group(1)] = p
        else:
            err(f'[B] 模块文件名不合规：{p.name}（应为 M<编号>-<中文名>.md）')
    return out


def git(*args: str) -> str:
    r = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'git {" ".join(args)} 失败：{r.stderr.strip()}')
    return r.stdout


# ---------------- 强规则二 · 稳定 A：项目级文档唯一 ----------------
def check_file_level_log() -> None:
    """强规则一 · 文件级登记：每个 PRD 文件必须有 `## …变更记录` 章节。"""
    for f in sorted(PRD.glob('*.md')):
        if f.name == 'CHANGELOG.md':
            continue
        if not re.search(r'^##.*变更记录', read(f), re.M):
            err(f'[1] {f.name} 缺少 `## 变更记录` 章节（强规则一：变更必须可追溯）')


def check_stability_a() -> None:
    l1 = read(PRD / '00-项目背景.md')
    if not l1:
        err('[A] 缺少 PRD/00-项目背景.md（项目级唯一事实来源）')
        return
    mapped = set(re.findall(r'\|\s*\[(M\d+)\]\(', l1))
    files = set(module_files())
    if mapped != files:
        err(f'[A] L1 模块地图与实际模块文件不一致：仅地图 {sorted(mapped - files)}；仅文件 {sorted(files - mapped)}')
    readme = read(PRD / 'README.md')
    idx = set(re.findall(r'\((M\d+-[^)]+\.md)\)', readme))
    idx_ids = {re.match(r'(M\d+)-', x).group(1) for x in idx}
    if idx_ids != files:
        err(f'[A] README 文档索引与模块文件不一致：仅索引 {sorted(idx_ids - files)}；仅文件 {sorted(files - idx_ids)}')
    nfrs = sorted(int(x) for x in re.findall(r'\bNFR-(\d+)\b', l1))
    if nfrs:
        missing = [n for n in range(1, max(nfrs) + 1) if n not in nfrs]
        if missing:
            err(f'[A] L1 的 NFR 编号不连续，缺：{missing}')
    for key in ('Amateur AI Drama Odyssey', 'amateur-ai-drama-odyssey', 'AADO'):
        if key not in l1:
            err(f'[A] L1 未登记项目名要素：{key}')


# ---------------- 强规则二 · 稳定 B：功能必归模块 ----------------
def check_stability_b() -> None:
    seen: dict[str, str] = {}
    for mid, path in sorted(module_files().items()):
        text = read(path)
        if not re.search(r'^##\s*(\d+\.\s*)?变更记录', text, re.M):
            err(f'[B] {path.name} 缺少 `## 变更记录` 章节')
        has_dep = bool(re.search(r'##[^\n]*目标态依据', text))
        count = 0
        for line in text.splitlines():
            if not re.match(r'^\|\s*M\d+\.\d+-F\d+\s*\|', line):
                continue
            cells = [c.strip() for c in re.split(r'(?<!\\)\|', line)][1:-1]
            if len(cells) != 7:
                err(f'[B] {path.name} 单元格数 {len(cells)}≠7（禁止裸 `|`）：{line[:60]}…')
                continue
            code, name, cur, goal, prio, metric, status = cells
            count += 1
            if not FP_RE.match(code):
                err(f'[B] {path.name} 功能点编号不合规：{code}')
            if code in seen:
                err(f'[B] 功能点编号重复：{code}（{seen[code]} 与 {path.name}）')
            seen[code] = path.name
            if status not in VALID_STATUS:
                err(f'[B] {path.name} {code} 状态非法：{status}')
            if prio not in ('P0', 'P1', 'P2'):
                warn(f'[B] {path.name} {code} 优先级非常规值：{prio}')
            if not metric:
                err(f'[B] {path.name} {code} 缺验收指标')
            if status == '已实现' and not re.search(r'`[\w./-]+\.(ts|tsx|md|json|mjs|py):\d', cur):
                err(f'[B] {path.name} {code} 状态为已实现但「现状」列无 `path:行号` 证据')
            if status == '规划中' and '依据' not in goal and not has_dep:
                err(f'[B] {path.name} {code} 规划中但无依据（内联或模块级）')
        if count == 0:
            err(f'[B] {path.name} 没有任何功能点（M#.#-F##）')


# ---------------- 强规则三：开发任务必登记模块文档 ----------------
def module_doc_files() -> dict[str, Path]:
    out = {}
    if not MODULE_DOCS_DIR.exists():
        return out
    for p in sorted(MODULE_DOCS_DIR.glob('M*.md')):
        m = re.match(r'^(M\d+)-.+\.md$', p.name)
        if m:
            out[m.group(1)] = p
        else:
            err(f'[3] 模块文档文件名不合规：{p.name}（应为 M<编号>-<中文名>.md，与 PRD 模块同名）')
    return out


def check_module_docs() -> None:
    """强规则三：每个 PRD 模块必须有一份 docs/modules/ 模块文档（总入口），
    且 PRD 模块文件 ↔ 模块文档 ↔ docs/modules/README.md 索引三方一致、任务行格式合法。"""
    if not MODULE_DOCS_DIR.exists():
        err('[3] 缺少 docs/modules/ 目录（强规则三：每个模块必须维护模块级文档）')
        return
    prd_mods = module_files()
    doc_mods = module_doc_files()
    if set(doc_mods) != set(prd_mods):
        only_doc = sorted(set(doc_mods) - set(prd_mods))
        only_prd = sorted(set(prd_mods) - set(doc_mods))
        if only_prd:
            err(f'[3] 以下模块缺少 docs/modules/ 模块文档：{only_prd}')
        if only_doc:
            err(f'[3] docs/modules/ 存在 PRD 没有的模块文档：{only_doc}')
    for mid in sorted(set(prd_mods) & set(doc_mods)):
        if prd_mods[mid].name != doc_mods[mid].name:
            err(f'[3] {mid} 模块文档文件名与 PRD 不一致：PRD={prd_mods[mid].name} '
                f'vs docs/modules={doc_mods[mid].name}（须同名）')
    idx = read(MODULE_DOCS_DIR / 'README.md')
    if not idx:
        err('[3] 缺少 docs/modules/README.md（模块文档索引）')
    else:
        listed = set(re.findall(r'\((M\d+-[^)]+\.md)\)', idx))
        actual_names = {p.name for p in doc_mods.values()}
        if listed != actual_names:
            err(f'[3] docs/modules/README.md 索引与模块文档不一致：'
                f'仅索引 {sorted(listed - actual_names)}；仅文件 {sorted(actual_names - listed)}')
    for mid, path in sorted(doc_mods.items()):
        text = read(path)
        if '更新日期' not in text:
            err(f'[3] {path.name} 缺少「更新日期」')
        if not re.search(r'^##\s*(?:\d+\.\s*)?任务登记', text, re.M):
            err(f'[3] {path.name} 缺少 `## 任务登记` 章节')
        if not re.search(r'^##\s*(?:\d+\.\s*)?变更记录', text, re.M):
            err(f'[3] {path.name} 缺少 `## 变更记录` 章节')
        seen = set()
        for line in text.splitlines():
            if not re.match(r'^\|\s*M\d+-T\d+\s*\|', line):
                continue
            cells = [c.strip() for c in re.split(r'(?<!\\)\|', line)][1:-1]
            if len(cells) != 6:
                err(f'[3] {path.name} 任务登记行单元格数 {len(cells)}≠6：{line[:60]}…')
                continue
            code, task, status, date, doc, note = cells
            if not TASK_RE.match(code):
                err(f'[3] {path.name} 任务编号不合规：{code}（应为 M#-TNN）')
            elif not code.startswith(mid + '-T'):
                err(f'[3] {path.name} {code} 归属不符：应属于 {mid}')
            if code in seen:
                err(f'[3] {path.name} 任务编号重复：{code}')
            seen.add(code)
            if status not in VALID_TASK_STATUS:
                err(f'[3] {path.name} {code} 状态非法：{status}')
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                err(f'[3] {path.name} {code} 日期不合规：{date}（应为 YYYY-MM-DD）')


# ---------------- 强规则一：变更登记 ----------------
def load_ledger() -> list[dict]:
    if not LEDGER_JSONL.exists():
        err('[1] 缺少 PRD/changelog.jsonl（机器可读台账）')
        return []
    entries = []
    for i, line in enumerate(read(LEDGER_JSONL).splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError as ex:
            err(f'[1] changelog.jsonl 第 {i} 行不是合法 JSON：{ex}')
            continue
        for field in ('id', 'date', 'type', 'level', 'files', 'summary', 'author'):
            if field not in e:
                err(f'[1] 台账 {e.get("id", f"第{i}行")} 缺字段 {field}')
        if e.get('type') not in VALID_TYPE:
            err(f'[1] 台账 {e.get("id")} type 非法：{e.get("type")}')
        if e.get('retroactive') and not e.get('commit'):
            err(f'[1] 台账 {e.get("id")} 标为追溯登记但缺 commit 字段')
        if e.get('level') not in VALID_LEVEL:
            err(f'[1] 台账 {e.get("id")} level 非法：{e.get("level")}')
        if not re.match(r'^CR-\d{8}-\d{3}$', str(e.get('id', ''))):
            err(f'[1] 台账 id 格式不合规（应为 CR-YYYYMMDD-NNN）：{e.get("id")}')
        if not isinstance(e.get('files'), list) or not e.get('files'):
            err(f'[1] 台账 {e.get("id")} files 必须是非空数组')
        else:
            for fpath in e['files']:
                fp = str(fpath)
                if fp.endswith('/') or '*' in fp or '?' in fp or fp.startswith('PRD/') and fp.count('/') == 1 and fp == 'PRD/':
                    err(f'[1] 台账 {e.get("id")} 的 files 必须写明具体文件路径（禁止目录前缀/通配）：{fp}')
        entries.append(e)
    ids = [e.get('id') for e in entries]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        err(f'[1] 台账 id 重复：{sorted(dup)}')
    if ids != sorted(ids):
        err('[1] 台账必须按 id 递增排列（追加型，禁止重排）')
    # MD 与 JSONL 对齐
    md = read(LEDGER_MD)
    if not md:
        err('[1] 缺少 PRD/CHANGELOG.md（人类可读台账）')
    for e in entries:
        if e.get('id') and e['id'] not in md:
            err(f'[1] CHANGELOG.md 缺少条目 {e["id"]}')
    return entries


def matches(path: str, patterns: list[str]) -> bool:
    """覆盖判定：**只接受精确文件路径**（禁止目录前缀/glob，避免一条台账永久豁免整目录）。"""
    p = path.replace('\\', '/')
    return any(p == str(pat).replace('\\', '/') for pat in patterns)


def base_ledger_ids(base: str) -> set[str] | None:
    """基线版本已有的台账 id 集合；基线无台账则返回 None（视为全部为新增）。"""
    try:
        raw = git('show', f'{base}:PRD/changelog.jsonl')
    except SystemExit:
        return None
    ids = set()
    for line in raw.splitlines():
        line = line.strip()
        if line:
            try:
                ids.add(json.loads(line)['id'])
            except Exception:
                pass
    return ids


def changed_prd_files(base: str, staged: bool) -> list[str]:
    # -z：NUL 分隔，避免中文路径被 git 加引号转义而漏检
    args = ['diff', '--name-only', '-z', '--diff-filter=ACMR']
    if staged:
        args.insert(1, '--cached')
    args.append(base)
    out = git(*args)
    return [f for f in out.split('\0') if f.startswith('PRD/') and f.endswith('.md')]


def check_registration(base: str | None, staged: bool) -> None:
    entries = load_ledger()
    if not base:
        return
    changed = changed_prd_files(base, staged)
    if not changed:
        return
    base_ids = base_ledger_ids(base)
    # 追溯登记（retroactive=true）只记录历史提交，不构成对本次改动的登记
    fresh = [e for e in entries if not e.get('retroactive') and (base_ids is None or e.get('id') not in base_ids)]
    covered = {f for f in changed if any(matches(f, e.get('files', [])) for e in fresh)}
    missing = [f for f in changed if f not in covered]
    if missing:
        err('[1] 以下 PRD 文件已改动但未登记台账（强规则一）：\n    - ' + '\n    - '.join(missing)
            + '\n  修复：python3 tools/prd_guard.py --new-entry --type 修订 --level L2 \\\n'
              + '\n'.join(f'        --files {f} \\' for f in missing)
              + '\n        --summary "说明改动内容与原因"')
    # 文件级变更记录：追加型，行数不得减少
    for f in changed:
        try:
            old = git('show', f'{base}:{f}')
        except SystemExit:
            continue  # 新文件
        new = read(ROOT / f)
        def rows(t: str) -> int:
            m = re.search(r'##\s*(?:\d+\.\s*)?变更记录(.*)$', t, re.S)
            return len([l for l in (m.group(1).splitlines() if m else []) if l.strip().startswith('|')])
        if re.search(r'^##\s*(\d+\.\s*)?变更记录', old, re.M) and rows(new) <= rows(old):
            err(f'[1] {f} 的 `## 变更记录` 未新增行（台账是追加型）')


# ---------------- 引用完整性 ----------------
def strip_history(text: str) -> str:
    """去掉「历史叙述」，只保留活引用：① 变更记录章节（任意标题形式）；② 含「重编号」的说明句。"""
    out, skip = [], False
    for line in text.splitlines():
        if not skip and re.match(r'^##.*变更记录', line):
            skip = True
            continue
        if skip and line.startswith('## '):
            skip = False
        if skip:
            continue
        if '重编号' in line or '已废弃编号' in line:
            continue
        out.append(line)
    return '\n'.join(out)


def check_refs() -> None:
    defs = set()
    for f in list(PRD.glob('9*.md')) + list(PRD.glob('M*.md')):
        for line in read(f).splitlines():
            m = re.match(r'^\|\s*([A-F]-\d+)\s*\|', line)
            if m:
                defs.add(m.group(1))
    used = set()
    for f in PRD.glob('*.md'):
        if f.name == 'CHANGELOG.md':
            continue  # 台账为历史叙述，不参与活引用校验
        body = strip_history(read(f))
        used |= set(re.findall(r'(?<![\w-])([A-F]-\d+)(?![\w-])', body))
    dangling = sorted(used - defs)
    if dangling:
        err(f'[2] 依据编号悬空（附录未定义）：{dangling[:10]}')
    for f in PRD.glob('*.md'):
        for link in re.findall(r'\]\(([^)#\s]+\.md)\)', read(f)):
            if not (PRD / link).exists():
                err(f'[2] {f.name} 内部链接不可达：{link}')


def check_governance_self() -> None:
    if 'GOVERNANCE.md' not in read(ROOT / 'README.md'):
        warn('[3] 根 README 未引用 GOVERNANCE.md（建议登记强规则入口）')
    if not (ROOT / '.githooks' / 'pre-commit').exists():
        err('[3] 缺少 .githooks/pre-commit（强规则一无法在提交时阻断）')


def new_entry(args: argparse.Namespace) -> int:
    today = dt.date.today().strftime('%Y%m%d')
    entries = load_ledger()
    seq = 1 + max([int(e['id'].split('-')[-1]) for e in entries if str(e.get('id', '')).startswith(f'CR-{today}')] or [0])
    eid = f'CR-{today}-{seq:03d}'
    entry = {'id': eid, 'date': dt.date.today().isoformat(), 'type': args.type, 'level': args.level,
             'files': args.files, 'summary': args.summary or '（待填写：说明改了什么与为什么）',
             'author': args.author, 'refs': args.refs or []}
    with LEDGER_JSONL.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + '\n')
    refs = '、'.join(entry['refs']) or '—'
    files = '<br>'.join(f'`{x}`' for x in entry['files'])
    with LEDGER_MD.open('a', encoding='utf-8') as fh:
        fh.write(f"| {eid} | {entry['date']} | {entry['type']} | {entry['level']} | {files} | {entry['summary']} | {refs} | {entry['author']} |\n")
    print(f'已登记 {eid}：{entry["summary"]}')
    print('提示：请同步在被改文件内追加 `## 变更记录` 行，然后提交。')
    return 0


AGENTS_FACTS_START = '```aado-facts'
REQUIRED_FACT_KEYS = ['python_version', 'venv_python', 'requirements', 'demo_verify',
                      'demo_qc_expected', 'slice_build', 'slice_verify', 'slice_out',
                      'guard', 'module_docs', 'ffmpeg', 'gpu', 'paid_api', 'max_parallel_writers']
FACT_PATH_KEYS = ['venv_python', 'requirements', 'demo_verify', 'slice_build', 'slice_verify',
                  'slice_out', 'guard', 'module_docs']
# 允许「尚未生成」的路径（新克隆/CI 场景）：提示而非 FAIL
OPTIONAL_PATH_KEYS = {'slice_out', 'venv_python'}


def parse_facts(text: str) -> dict[str, str]:
    """解析 AGENTS.md 的 ```aado-facts 机器可读块（key = value，裸值）。"""
    if AGENTS_FACTS_START not in text:
        err('[AG] AGENTS.md 缺少 ```aado-facts 机器可读事实块')
        return {}
    block = text.split(AGENTS_FACTS_START, 1)[1]
    if '```' not in block:
        err('[AG] AGENTS.md 的 aado-facts 代码块未闭合')
        return {}
    body = block.split('```', 1)[0]
    facts = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            err(f'[AG] aado-facts 行不合规（应为 `key = value`）：{line!r}')
            continue
        k, v = line.split('=', 1)
        facts[k.strip()] = v.strip()
    return facts


def check_agent_docs() -> None:
    """Agent 指令文件一致性：单一事实来源 + 事实块可验证 + 命令/路径真实可达。

    覆盖：AGENTS.md（跨 harness 唯一事实来源）、CLAUDE.md（Claude Code 薄适配层）。
    **这些文件不是 PRD，不受强规则一台账约束**，但必须与仓库真实状态一致。
    """
    agents_p, claude_p = ROOT / 'AGENTS.md', ROOT / 'CLAUDE.md'
    agents, claude = read(agents_p), read(claude_p)
    if not agents:
        err('[AG] 缺少 AGENTS.md（所有 Agent 的统一入口）')
        return
    if not claude:
        err('[AG] 缺少 CLAUDE.md（Claude Code 适配层）')
    elif 'AGENTS.md' not in claude:
        err('[AG] CLAUDE.md 必须指向 AGENTS.md 作为唯一事实来源（禁止各自维护一份规则）')
    if len(claude) > 6 * len(agents) and len(claude) > 4000:
        warn('[AG] CLAUDE.md 体积接近 AGENTS.md，疑似复制而非引用（易漂移）')

    facts = parse_facts(agents)
    if not facts:
        return
    for key in REQUIRED_FACT_KEYS:
        if key not in facts:
            err(f'[AG] aado-facts 缺少必需键：{key}')

    # 1) 路径/命令类事实必须真实存在（去重，便于报告）
    for key in FACT_PATH_KEYS:
        val = facts.get(key, '')
        if not val:
            continue
        p = ROOT / val
        if p.exists():
            continue
        if key in OPTIONAL_PATH_KEYS:
            hint = '先跑 tools/build_p1_a.py' if key == 'slice_out' else '新克隆请先建 venv（CI 上属正常）'
            warn(f'[AG] aado-facts 的 {key}={val} 尚不存在：{hint}')
        else:
            err(f'[AG] aado-facts 的 {key} 指向不存在的路径：{val}')

    # 2) 环境事实必须与本机实测一致（不允许想当然）
    #    口径：**主次版本号必须一致**（补丁号允许差异，CI 的 3.12.x 场景不应误报）
    def mm(v: str) -> str:
        parts = v.split('.')
        return '.'.join(parts[:2]) if len(parts) >= 2 else v

    venv_py = facts.get('venv_python', '')
    declared = facts.get('python_version', '')
    ci_declared = facts.get('ci_python_version', '')
    running = '%d.%d.%d' % sys.version_info[:3]
    if venv_py and (ROOT / venv_py).exists():
        try:
            out = subprocess.run([str(ROOT / venv_py), '-c',
                                  'import sys;print("%d.%d.%d" % sys.version_info[:3])'],
                                 capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            err(f'[AG] 无法执行 {venv_py} 读取版本：{exc}')
            out = ''
        if out and declared and mm(out) != mm(declared):
            err(f'[AG] AGENTS.md 声明 python_version={declared}，venv 实测 {out}'
                '（主次版本漂移，必须同步）')
    else:
        # 新克隆 / CI 无 venv：退化为「以当前解释器为准」
        allowed = {mm(declared)} if declared else set()
        if ci_declared:
            allowed.add(mm(ci_declared))
        if allowed and mm(running) not in allowed:
            err(f'[AG] 当前解释器 {running} 与 AGENTS.md 声明的运行版本 '
                f'{sorted(allowed)} 主次版本不一致（请同步 python_version / ci_python_version）')
        else:
            warn(f'[AG] 未找到 {venv_py}，按当前解释器 {running} 核对：与声明一致')

    # 3) 依赖声明与 requirements 文件的交集（近似断言，避免维护第二份清单）
    req = facts.get('requirements', '')
    if req and (ROOT / req).exists():
        pkgs = {re.split(r'[<>=!]', ln.strip(), 1)[0].lower()
                for ln in read(ROOT / req).splitlines()
                if ln.strip() and not ln.strip().startswith('#')}
        for expect in ('numpy', 'pillow'):
            if expect not in pkgs:
                warn(f'[AG] {req} 中未见 {expect}（AGENTS.md 声称依赖它，请核对）')

    # 4) 能力声明必须为封闭布尔值
    for key in ('ffmpeg', 'gpu', 'paid_api'):
        val = facts.get(key, '')
        if val and val not in ('true', 'false'):
            err(f'[AG] aado-facts 的 {key} 必须为 true/false，当前 {val!r}')

    # 5) 跨文件事实一致性：README **所有** Demo QC 通过率出现处都必须与事实块一致
    #    （只校验第一处是漏洞：README 在多处提到 24/24，漏一处即自证通过）
    readme = read(ROOT / 'README.md')
    declared_qc = facts.get('demo_qc_expected', '')
    if declared_qc and readme:
        seen = [f'{a}/{b}' for a, b in re.findall(r'(\d+)\s*/\s*(\d+)\s*(?:通过|PASS)', readme)]
        if declared_qc in seen:
            bad = sorted({s for s in seen if s not in (declared_qc, '84/84', '62/62', '13/13')})
            if bad:
                err(f'[AG] README 存在与 aado-facts 的 demo_qc_expected={declared_qc} 不一致的通过率：{bad}')
        elif seen:
            warn(f'[AG] README 提到通过率 {sorted(set(seen))}，但事实块 demo_qc_expected={declared_qc}；'
                 '若与 Demo 无关可忽略')

    # 6) 子代理并行写者上限必须是整数（本项目约定单写者）
    mpw = facts.get('max_parallel_writers', '')
    if mpw and not mpw.isdigit():
        err(f'[AG] aado-facts 的 max_parallel_writers 必须为整数，当前 {mpw!r}')


def check_doc_links() -> None:
    """断链检查：仓库内所有 .md 的相对链接目标必须存在（防文档引用不存在的文件）。"""
    skip = {'.venv', '.git', '.claude', 'node_modules', '__pycache__'}
    broken = []
    for p in ROOT.rglob('*.md'):
        rel = p.relative_to(ROOT)
        if any(part in skip for part in rel.parts):
            continue
        for m in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', read(p)):
            target = m.group(1).strip()
            if target.startswith(('http://', 'https://', '#', 'mailto:', '<', '/')):
                continue
            target = target.split('#')[0]
            if not target.endswith('.md'):
                continue
            if not (p.parent / target).resolve().exists():
                broken.append(f'{rel} → {target}')
    for b in broken:
        err(f'[DOC] 断链：{b}')


def check_docs_index() -> None:
    """docs/README.md 的「文档清单」必须与 docs/ 下实际 .md 一一对应（索引一致性，防文档游离）。
    docs/modules/ 由 docs/modules/README.md 自索引，并由 check_module_docs 与 PRD 三方一致校验，故在此排除。"""
    index = ROOT / 'docs' / 'README.md'
    if not index.exists():
        err('[DOC] 缺少 docs/README.md（权威索引 + 归位约定）')
        return
    text = read(index)
    if '## 四、文档清单' not in text:
        err('[DOC] docs/README.md 缺少「## 四、文档清单」章节')
        return
    body = text.split('## 四、文档清单', 1)[1].split('## 五、', 1)[0]
    listed = set()
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith('|') or '---' in line:
            continue
        cells = [c.strip().strip('`') for c in line.strip('|').split('|')]
        if len(cells) < 2 or not cells[1].endswith('.md'):
            continue
        d = cells[0].rstrip('/')
        f = cells[1]
        rel_dir = '' if d == 'docs' else d[len('docs/'):]
        listed.add(f'{rel_dir}/{f}' if rel_dir else f)
    actual = {p.relative_to(ROOT / 'docs').as_posix()
              for p in (ROOT / 'docs').rglob('*.md')
              if p.relative_to(ROOT / 'docs').as_posix() != 'README.md'
              and not p.relative_to(ROOT / 'docs').as_posix().startswith('modules/')}
    missing = sorted(actual - listed)
    stale = sorted(listed - actual)
    if missing:
        err('[DOC] docs/ 下文件未登记进 docs/README.md 清单：' + '、'.join(missing))
    if stale:
        err('[DOC] docs/README.md 清单引用了不存在的文件：' + '、'.join(stale))


def main() -> int:
    ap = argparse.ArgumentParser(description='PRD 治理门禁')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all', action='store_true', help='全量结构体检')
    g.add_argument('--staged', action='store_true', help='预提交：暂存区 vs HEAD')
    g.add_argument('--range', metavar='BASE..HEAD', help='CI：范围校验（用 BASE 作为对比点）')
    g.add_argument('--new-entry', action='store_true', help='生成台账条目')
    g.add_argument('--agent-docs', action='store_true',
                   help='Agent 指令文件一致性（AGENTS.md / CLAUDE.md）')
    ap.add_argument('--type', default='修订', choices=sorted(VALID_TYPE))
    ap.add_argument('--level', default='L2', choices=sorted(VALID_LEVEL))
    ap.add_argument('--files', nargs='*', default=[])
    ap.add_argument('--refs', nargs='*', default=[])
    ap.add_argument('--summary', default='')
    ap.add_argument('--author', default='Agent')
    args = ap.parse_args()

    if args.new_entry:
        if not args.files:
            print('错误：--new-entry 需要 --files', file=sys.stderr)
            return 2
        return new_entry(args)

    if args.agent_docs:
        check_agent_docs()
        for w in warns:
            print(f'警告 {w}')
        if errors:
            print(f'\n✗ Agent 文档检查未通过：{len(errors)} 项违规\n')
            for e in errors:
                print(f'  {e}')
            return 1
        print('✓ Agent 文档检查通过：AGENTS.md（唯一事实来源）/ CLAUDE.md（适配层）一致，'
              '事实块可验证、命令与路径真实存在')
        return 0

    check_file_level_log()
    check_stability_a()
    check_stability_b()
    check_module_docs()
    if args.staged:
        check_registration('HEAD', staged=True)
    elif args.range:
        base = args.range.split('..')[0]
        check_registration(base, staged=False)
    else:
        load_ledger()
    check_refs()
    check_governance_self()
    # Agent 指令文件一致性 + 文档断链/索引一致性 也纳入全量体检
    if args.all:
        check_agent_docs()
        check_doc_links()
        check_docs_index()

    for w in warns:
        print(f'警告 {w}')
    if errors:
        print(f'\n✗ PRD 治理门禁未通过：{len(errors)} 项违规\n')
        for e in errors:
            print(f'  {e}')
        return 1
    print('✓ PRD 治理门禁通过：强规则一（变更登记）、强规则二（两个稳定）、强规则三（模块文档登记）均满足')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
