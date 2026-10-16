#!/usr/bin/env python3
"""覆盖率报告：跑全部 verify_*.py，用 coverage 统计 film/ 覆盖率。"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VERIFIES = [f for f in sorted(os.listdir(HERE)) if f.startswith("verify_") and f.endswith(".py")]

env = dict(os.environ)
env["DATABASE_URL"] = env.get("DATABASE_URL", "sqlite:///:memory:")
env["ADMIN_USERNAME"] = "a"; env["ADMIN_PASSWORD"] = "a"; env["SECRET_KEY"] = "s"

cov = os.path.join(ROOT, ".venv", "bin", "coverage")
subprocess.run([cov, "run", "--source=film", "-m", "pytest", "--version"],
               cwd=ROOT, env=env, capture_output=True)
# 逐个跑 verify（它们被设计为独立脚本，非 pytest）
for v in VERIFIES:
    subprocess.run([cov, "run", "--append", "--source=film", os.path.join("tools", v)],
                   cwd=ROOT, env=env, capture_output=True)
r = subprocess.run([cov, "report", "--skip-covered", "--omit=*/__init__.py"],
                   cwd=ROOT, env=env, capture_output=True, text=True)
print(r.stdout)
print(r.stderr[-300:] if r.stderr else "")
