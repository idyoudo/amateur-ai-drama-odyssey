"""M13 任务编排与可靠性 · 契约层（slice 1）。

本包只落地**类型系统与不变量**（状态机/幂等指纹/checkpoint/intent/fencing）的纯函数契约，
不含 PG 队列/SQLAlchemy/worker 进程（下一片）。依据：PRD/M13、docs/designs/任务编排设计.md。
"""
