#!/bin/sh
# 安装 Git 钩子：让「强规则一/二」在本机提交时生效（克隆后必须执行一次）
set -e
ROOT="$(git rev-parse --show-toplevel)"
git -C "$ROOT" config core.hooksPath .githooks
chmod +x "$ROOT/.githooks/pre-commit" 2>/dev/null || true
echo "已启用 PRD 治理钩子：core.hooksPath=$(git -C "$ROOT" config core.hooksPath)"
echo "自检：python3 tools/prd_guard.py --all"
