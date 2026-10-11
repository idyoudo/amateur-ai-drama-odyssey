# CLAUDE.md —— Claude Code 适配层

> **本文件刻意保持很薄。事实与规则只在 [AGENTS.md](AGENTS.md) 里维护一份，避免多份指令互相漂移。**
> 接手本仓库请**先完整读 [AGENTS.md](AGENTS.md)**，再回来看下面的 Claude Code 专属注意事项。

## 一句话现状

好莱坞级 AI 短剧（AADO）的 PRD + 可运行代理样片 Demo + P1 主干首个切片；
治理由 `tools/prd_guard.py` 强制（两条强规则）；**无 ffmpeg / 无 GPU / 无付费凭据**，纯 CPU 自证。

## 收工前必跑（全绿才算完成）

```bash
python3 tools/prd_guard.py --all                     # 期望 ✓
. .venv/bin/activate
(cd demo && python3 verify.py && python3 report.py)   # 期望 24/24
python3 tools/build_p1_a.py --out out/p1a             # 期望 checks_failed=0
python3 tools/verify_p1_a.py --out out/p1a --determinism
```

## Claude Code 专属注意事项

1. **Python 一律用 `.venv`**：系统 `python3` 没有 numpy/Pillow，只有 `python3 tools/prd_guard.py` 这类纯标准库脚本可以直接跑。
   跑 demo 或切片命令前先 `source .venv/bin/activate`，或直接用 `.venv/bin/python`。
2. **语言版本是 3.9.6**：不要写 3.10+ 语法（`match`、运行时 `X | Y`、`dict | dict`）。
3. **不要交互式提问**：本项目的工作方式是「争议走多智能体选举，不走请示」。
   有歧义就列出结构化选项、自己跑选举（5 名独立评估员、多数决）并把记录写进 `docs/plans/*选举记录.md`。
4. **改了 `PRD/` 下任何文件就必须登记**（三处台账），否则提交会被钩子拒绝；只改代码/文档不需要登记。
   命令模板见 [AGENTS.md](AGENTS.md) 第 2 节。
5. **长命令放后台**：`demo/build_demo.py`、`verify_p1_a.py --determinism` 是分钟级任务，
   用后台任务跑并等它结束，不要在前台阻塞。
6. **`.claude/worktrees/`**：Claude Code 的 worktree 会整份复制仓库（含 `PRD/`）。
   在 worktree 里改动**不会被主线看到**，收工前确认自己动的是主线工作区。
7. **删文件前先确认替代件非空**；不要清理 `demo/out/`（它是 PRD/96、PRD/97 的证据来源）。
8. **多 Agent 并行时**：本仓库约定**同一时间只有一个写者**（`max_parallel_writers = 1`），
   子代理只写各自的文件，不要并发改同一目录。
9. 收工报告要能机器复核：给**命令 + 数字**，并显式列出**没验证的部分**（不要含糊成「应该没问题」）。

## 事实块的唯一来源

环境与命令等机器可读事实写在 [AGENTS.md](AGENTS.md) 第 8 节的 `aado-facts` 块里，
由 `python3 tools/prd_guard.py --agent-docs` 校验（版本、路径、命令可达性），
**不要在 CLAUDE.md 里另抄一份**。

## 变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立 Claude Code 适配层：指向 AGENTS.md 作为唯一事实来源，只保留 Claude Code 专属注意事项（venv、3.9 语法、禁止交互式提问、PRD 登记、后台长任务、worktree 陷阱、单写者约定） |
