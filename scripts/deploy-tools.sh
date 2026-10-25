#!/usr/bin/env bash
# AADO 开源工具栈发布入口（ToonFlow / MoneyPrinterTurbo / NarratoAI）
# 与 AADO 主栈隔离：独立 compose 项目 aado-tools、独立目录、独立端口、统一 Basic Auth 网关。
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-root@101.200.220.4}"
REMOTE_REPO_DIR="${REMOTE_REPO_DIR:-/data/next-ai-ws/amateur-ai-drama-odyssey}"
REMOTE_RUNTIME_DIR="${REMOTE_RUNTIME_DIR:-/data/runtime/amateur-ai-drama-odyssey}"
TOOLS_ROOT="${TOOLS_ROOT:-/data/next-ai-ws/open-source}"
BRANCH="${BRANCH:-main}"

[[ "$(git branch --show-current)" == "$BRANCH" ]] || { echo "当前分支必须是 $BRANCH" >&2; exit 1; }
git push origin "$BRANCH"

ssh "$REMOTE_HOST" "REMOTE_REPO_DIR='$REMOTE_REPO_DIR' REMOTE_RUNTIME_DIR='$REMOTE_RUNTIME_DIR' TOOLS_ROOT='$TOOLS_ROOT' BRANCH='$BRANCH' sh -s" <<'REMOTE_DEPLOY'
set -eu
mkdir -p "$REMOTE_REPO_DIR" "$REMOTE_RUNTIME_DIR" "$TOOLS_ROOT"

if [ ! -d "$REMOTE_REPO_DIR/.git" ]; then
  git clone --branch "$BRANCH" "https://github.com/idyoudo/amateur-ai-drama-odyssey.git" "$REMOTE_REPO_DIR"
else
  git -C "$REMOTE_REPO_DIR" fetch origin "$BRANCH"
  git -C "$REMOTE_REPO_DIR" checkout "$BRANCH"
  git -C "$REMOTE_REPO_DIR" pull --ff-only origin "$BRANCH"
fi

install -m 0644 "$REMOTE_REPO_DIR/docker-compose.tools.yml" "$REMOTE_RUNTIME_DIR/docker-compose.tools.yml"
install -m 0644 "$REMOTE_REPO_DIR/docker/Caddyfile.tools" "$REMOTE_RUNTIME_DIR/Caddyfile.tools"

cd "$REMOTE_RUNTIME_DIR"
mkdir -p mpt/storage narrato/storage

clone_or_pull() {
  url="$1"; dir="$2"
  if [ -d "$TOOLS_ROOT/$dir/.git" ]; then
    timeout 60 git -C "$TOOLS_ROOT/$dir" fetch --all --prune || echo "警告：$dir fetch 超时，沿用当前版本"
    timeout 30 git -C "$TOOLS_ROOT/$dir" pull --ff-only || echo "警告：$dir 无法快进，沿用当前版本"
  else
    git clone --depth 1 "$url" "$TOOLS_ROOT/$dir"
  fi
}

clone_or_pull https://github.com/HBAI-Ltd/Toonflow-app.git toonflow
clone_or_pull https://github.com/harry0703/MoneyPrinterTurbo.git moneyprinterturbo
clone_or_pull https://github.com/linyqh/NarratoAI.git narratoai

# HTTP 公网非安全上下文：注入 crypto.randomUUID polyfill（幂等）
python3 "$REMOTE_REPO_DIR/docker/patches/toonflow-randomuuid.py" "$TOOLS_ROOT/toonflow/apps/web/index.html"

# Debian 官方源在本机容器内不稳定，构建前统一改写为阿里云镜像（幂等）
python3 - "$TOOLS_ROOT/narratoai/Dockerfile" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
if 'mirrors.aliyun.com' not in s:
    s = s.replace(
        'apt-get update',
        'sed -i "s|http://deb.debian.org|https://mirrors.aliyun.com|g" '
        '/etc/apt/sources.list.d/debian.sources 2>/dev/null || true; apt-get update'
    )
    open(p, 'w', encoding='utf-8').write(s)
PY

[ -f mpt/config.toml ] || cp "$TOOLS_ROOT/moneyprinterturbo/config.example.toml" mpt/config.toml
[ -f narrato/config.toml ] || cp "$TOOLS_ROOT/narratoai/config.example.toml" narrato/config.toml

if [ ! -f .env.tools ]; then
  pw="$(openssl rand -hex 12)"
  docker pull caddy:2-alpine >/dev/null
  hash="$(docker run --rm caddy:2-alpine caddy hash-password --plaintext "$pw")"
  hash_esc="$(printf '%s' "$hash" | sed 's/\$/$$/g')"
  cat > .env.tools <<EOF
TOOLS_ROOT=$TOOLS_ROOT
TOOLS_PASSWORD=$pw
TOOLS_PASSWORD_HASH=$hash_esc
MPT_IMAGE=ghcr.io/harry0703/moneyprinterturbo:latest
EOF
  chmod 600 .env.tools
fi

# shellcheck disable=SC1091
. ./.env.tools

if ! timeout 180 docker pull "$MPT_IMAGE" >/tmp/aado-mpt-pull.log 2>&1; then
  if timeout 180 docker pull ghcr.nju.edu.cn/harry0703/moneyprinterturbo:latest; then
    echo "GHCR 官方源不可达，已使用 NJU 镜像并打回官方标签"
    docker tag ghcr.nju.edu.cn/harry0703/moneyprinterturbo:latest "$MPT_IMAGE"
  else
    echo "镜像源均不可达，改为本地构建 MoneyPrinterTurbo（可能需要数分钟）"
    docker build -t "$MPT_IMAGE" "$TOOLS_ROOT/moneyprinterturbo"
  fi
fi

COMPOSE="docker compose --env-file .env.tools -f docker-compose.tools.yml"
$COMPOSE build toonflow
$COMPOSE build narratoai || echo "警告：NarratoAI 构建失败，将跳过该服务"

if docker image inspect aado-narratoai:local >/dev/null 2>&1; then
  $COMPOSE up -d
else
  $COMPOSE up -d toonflow mpt-webui mpt-api gateway
fi

echo "等待网关就绪……"
ok=0
for i in $(seq 1 24); do
  ok=1
  curl -fsS --max-time 5 -u "aado:$TOOLS_PASSWORD" http://127.0.0.1:18588/ >/dev/null || ok=0
  curl -fsS --max-time 5 -u "aado:$TOOLS_PASSWORD" http://127.0.0.1:18501/ >/dev/null || ok=0
  curl -fsS --max-time 5 -u "aado:$TOOLS_PASSWORD" http://127.0.0.1:18502/docs >/dev/null || ok=0
  if docker image inspect aado-narratoai:local >/dev/null 2>&1; then
    curl -fsS --max-time 5 -u "aado:$TOOLS_PASSWORD" http://127.0.0.1:18503/ >/dev/null || ok=0
  fi
  [ "$ok" = 1 ] && break
  sleep 10
done

$COMPOSE ps
echo "工具账号：aado"
echo "工具密码：$TOOLS_PASSWORD"
echo "凭据文件：$REMOTE_RUNTIME_DIR/.env.tools（chmod 600）"
[ "$ok" = 1 ] || { echo "部分服务未就绪，请查看 docker compose logs" >&2; exit 1; }
REMOTE_DEPLOY

echo "开源工具栈部署完成：$REMOTE_HOST:$REMOTE_RUNTIME_DIR（端口 18588 / 18501 / 18502 / 18503）"
