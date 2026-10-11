# AADO 远端部署规范（构建 / 发布 / 打包 / 数据库）

> 本文定义 AADO 的**远端拓扑、数据库、构建打包、发布流程与安全铁律**，参照 `retail-trading-odyssey` 的部署约定，
> 但**两项目在目录、数据卷、数据库三个层面完全隔离**。远端主机：`root@101.200.220.4`。

## 一、拓扑与隔离（与 retail 完全分离）

| 项 | retail-trading-odyssey | AADO（本项目） |
|----|------------------------|----------------|
| 代码目录 | `/data/next-ai-ws/retail-trading-odyssey` | `/data/next-ai-ws/amateur-ai-drama-odyssey` |
| 运行目录 | `/data/runtime/retail-trading-odyssey` | `/data/runtime/amateur-ai-drama-odyssey` |
| PostgreSQL 容器 | `retail-trading-odyssey-postgres-1` | `amateur-ai-drama-odyssey-postgres-1` |
| PG 数据卷 | `retail-trading-odyssey_rto_pgdata` | `amateur-ai-drama-odyssey_aado_pgdata` |
| PG 库 / 用户 | `RTO` / `dev` | `AADO` / `aado` |
| PG 宿主机端口 | `5432` | `5433`（避开 retail） |

**隔离铁律**：

- 代码目录与运行目录是**两套物理目录**，互不共享、互不引用。
- 数据库用**独立的 postgres 容器 + 独立命名卷 + 独立账号**，绝不在 retail 的 pg 里建库或建账号。
- 运行目录只放 `.env` + `docker-compose.prod.yml` + 运行态文件，**禁止作为 Git checkout**；Git 操作只在代码目录进行。

## 二、数据库规范

| 项 | 值 |
|----|----|
| 镜像 | `postgres:16-alpine` |
| 库名 | `AADO`（大写，与 retail 的 `RTO` 同风格；手动建库须加引号） |
| 用户 | `aado`（独立超级用户，不与 retail 的 `dev` 混用） |
| 密码 | `POSTGRES_PASSWORD`，部署脚本用 `openssl rand -hex 24` 生成，只存远端 `.env`（`chmod 600`），不入 Git |
| 数据卷 | `aado_pgdata`（命名卷，全名带 compose 项目前缀 `amateur-ai-drama-odyssey_`） |
| 宿主机端口 | `5433:5432` |
| 容器内连接串 | `postgres://aado:${POSTGRES_PASSWORD}@postgres:5432/AADO` |
| 宿主机连接串 | `postgres://aado:${POSTGRES_PASSWORD}@localhost:5433/AADO` |

库由容器首次启动时 `POSTGRES_DB=AADO` 自动创建；如需手动补库，容器内执行：

```bash
docker exec amateur-ai-drama-odyssey-postgres-1 psql -U aado -d postgres -c 'CREATE DATABASE "AADO"'
```

## 三、构建与打包

- 技术栈：**Python monorepo**（FastAPI + SQLAlchemy/Alembic + PG 自建队列），见 `docs/architecture.md`。
- 镜像构建上下文固定为代码目录 `/data/next-ai-ws/amateur-ai-drama-odyssey`。
- 服务形态（实现阶段补入）：`apps/api`（FastAPI 控制面）、`apps/worker`（PG `SKIP LOCKED` 队列 worker），各自 Dockerfile target；媒体/QC 核心在 `film/` 包，随镜像打入。
- 依赖锁定：`requirements.txt` / `pyproject.toml`；媒体降级路径用 `numpy`/`Pillow`（无 ffmpeg 也能自证），生产可加 ffmpeg 加速。
- **当前阶段**：`docker-compose.prod.yml` 仅含 `postgres` 服务（先落地数据隔离）；`api`/`worker` 服务随 P1 实现补入，构建流程不变。

## 四、发布流程（deploy-remote.sh）

发布入口：`./scripts/deploy-remote.sh`（本机运行，脚本内部 push `main`）。

流程（对齐 retail，当前为可用子集）：

1. 校验当前分支为 `main`；
2. `git push origin main`；
3. SSH 到远端：`mkdir -p` 代码/运行目录；代码目录首次 `git clone`、否则 `fetch + pull --ff-only`（历史分叉时旧目录改名保留）；
4. 把 `docker-compose.prod.yml` 复制到运行目录；
5. 运行目录 `.env` 缺失时生成 `POSTGRES_PASSWORD`（`openssl rand -hex 24`）并写 `DATABASE_URL`，`chmod 600`；
6. `docker compose --env-file .env -f docker-compose.prod.yml up -d postgres --wait`；
7. 验收：`docker compose ps` + 容器内 `psql -U aado -d AADO` 查当前库/用户。

**发布纪律**：不要临场拼装完整 ssh/scp/compose 流程，统一走 `deploy-remote.sh`；不要在运行目录 `git pull`；依赖缺失时在 compose 补齐并保持脚本/文档可复现。

## 五、安全铁律（禁止）

- 禁止 `docker compose down -v`（删数据卷）。
- 禁止 `docker volume rm` 任何 `*_pgdata` 卷，禁止 `docker system prune --volumes`。
- 禁止提交 `.env`、真实密钥、数据库密码到 Git。
- 禁止在 retail 的 postgres 容器里建 AADO 的库/账号（破坏隔离）。

## 六、验收命令

```bash
ssh root@101.200.220.4 'cd /data/runtime/amateur-ai-drama-odyssey && docker compose --env-file .env -f docker-compose.prod.yml ps'
ssh root@101.200.220.4 'docker exec amateur-ai-drama-odyssey-postgres-1 psql -U aado -d AADO -c "SELECT current_database(), current_user"'
```

## 变更记录

| 日期 | 修订人 | 变更内容 |
|------|--------|----------|
| 2026-10-11 | Agent | 建立远端部署规范：与 retail 三方隔离（目录/数据卷/数据库）、独立 postgres（AADO/aado/5433/aado_pgdata）、构建打包、发布流程、安全铁律 |
