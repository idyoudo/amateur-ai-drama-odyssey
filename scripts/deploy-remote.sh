#!/usr/bin/env bash
# AADO 远端部署入口（对齐 retail 约定；当前仅部署隔离的 postgres，api/worker 随 P1 实现补入）
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-root@101.200.220.4}"
REMOTE_REPO_DIR="${REMOTE_REPO_DIR:-/data/next-ai-ws/amateur-ai-drama-odyssey}"
REMOTE_RUNTIME_DIR="${REMOTE_RUNTIME_DIR:-/data/runtime/amateur-ai-drama-odyssey}"
BRANCH="${BRANCH:-main}"
ENV_FILE="${ENV_FILE:-.env}"
REPO_URL="$(git remote get-url origin)"

[[ "$(git branch --show-current)" == "$BRANCH" ]] || { echo "当前分支必须是 $BRANCH" >&2; exit 1; }
git diff --check -- docker-compose.prod.yml scripts/deploy-remote.sh
git push origin "$BRANCH"

ssh "$REMOTE_HOST" "REMOTE_REPO_DIR='$REMOTE_REPO_DIR' REMOTE_RUNTIME_DIR='$REMOTE_RUNTIME_DIR' REPO_URL='$REPO_URL' BRANCH='$BRANCH' sh -s" <<'REMOTE_SYNC'
set -eu
mkdir -p "$REMOTE_REPO_DIR" "$REMOTE_RUNTIME_DIR"

if [ ! -d "$REMOTE_REPO_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$REMOTE_REPO_DIR"
else
  git -C "$REMOTE_REPO_DIR" fetch origin "$BRANCH"
  git -C "$REMOTE_REPO_DIR" checkout "$BRANCH"
  git -C "$REMOTE_REPO_DIR" pull --ff-only origin "$BRANCH"
fi

install -m 0644 "$REMOTE_REPO_DIR/docker-compose.prod.yml" "$REMOTE_RUNTIME_DIR/docker-compose.prod.yml"
REMOTE_SYNC

if [[ -f "$ENV_FILE" ]]; then
  scp "$ENV_FILE" "$REMOTE_HOST:$REMOTE_RUNTIME_DIR/.env.from-local"
fi

ssh "$REMOTE_HOST" "REMOTE_RUNTIME_DIR='$REMOTE_RUNTIME_DIR' sh -s" <<'REMOTE_DEPLOY'
set -eu
cd "$REMOTE_RUNTIME_DIR"

# 合并本地 .env 的缺失键（不覆盖远端已有）
if [ -f .env.from-local ]; then
  while IFS= read -r line; do
    case "$line" in \#*|"") continue;; esac
    key="${line%%=*}"
    grep -q "^${key}=" .env 2>/dev/null || echo "$line" >> .env
  done < .env.from-local
fi
rm -f .env.from-local

if [ ! -f .env ]; then
  pw="$(openssl rand -hex 24)"
  printf 'POSTGRES_PASSWORD=%s\nDATABASE_URL=postgres://aado:%s@postgres:5432/AADO\n' "$pw" "$pw" > .env
fi

# 鉴权凭据回退（本地 .env 未提供时随机生成）
grep -q '^ADMIN_USERNAME=' .env 2>/dev/null || echo 'ADMIN_USERNAME=admin' >> .env
grep -q '^ADMIN_PASSWORD=' .env 2>/dev/null || printf 'ADMIN_PASSWORD=%s\n' "$(openssl rand -hex 12)" >> .env
grep -q '^SECRET_KEY=' .env 2>/dev/null || printf 'SECRET_KEY=%s\n' "$(openssl rand -hex 32)" >> .env
chmod 600 .env

docker compose --env-file .env -f docker-compose.prod.yml up -d postgres --wait --wait-timeout 90
build_log="/tmp/aado-build-$$.log"
if ! docker compose --env-file .env -f docker-compose.prod.yml build api worker >"$build_log" 2>&1; then
  cat "$build_log"
  rm -f "$build_log"
  echo "构建失败：api/worker 镜像未更新，已中止部署" >&2
  exit 1
fi
if grep -q "failed to solve" "$build_log"; then
  cat "$build_log"
  rm -f "$build_log"
  echo "构建失败：镜像源或依赖解析失败，已中止部署" >&2
  exit 1
fi
rm -f "$build_log"
docker compose --env-file .env -f docker-compose.prod.yml up -d api worker --wait --wait-timeout 180
docker compose --env-file .env -f docker-compose.prod.yml ps
docker exec amateur-ai-drama-odyssey-postgres-1 psql -U aado -d AADO -Atc "SELECT current_database(), current_user"
REMOTE_DEPLOY

echo "远程部署完成：代码 ${REMOTE_HOST}:${REMOTE_REPO_DIR}；运行态 ${REMOTE_HOST}:${REMOTE_RUNTIME_DIR}；postgres 已隔离启动。"
