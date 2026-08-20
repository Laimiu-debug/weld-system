# 运维手册

适用仓库：焊序。命令以仓库根目录为起点，Windows 把 `source venv/bin/activate` 换成 `venv\Scripts\activate`。

## 本地开发

1. 复制根目录 `.env.example` 为 `.env`，生成强随机数据库/Redis 密码。已泄露的旧口令禁止继续使用。
2. 后端复制 `backend/.env`（可参考 `.env.example`），开发时设置 `DEVELOPMENT=true`，并填写 `FRONTEND_URL`（默认 `http://localhost:3000`）、SMTP（验证邮件/重置密码）。
3. Python 3.11：`cd backend && python -m venv venv && pip install -e ".[dev]"`。
4. 空库：`python -m app.scripts.bootstrap_schema`，然后 `alembic upgrade head`。启动时不再 `create_all`。
5. `uvicorn app.main:app --reload --port 8000`。
6. 用户端 Node 20：`cd frontend && npm ci && npm run dev`（默认 3000）。
7. 管理端：`cd admin-portal && npm ci && npm run dev`（默认 3001）。

不要使用仓库中不存在的 `deploy.sh` / `DEPLOYMENT_GUIDE.md`。生产用 Compose。

## 测试

```bash
cd backend
python -m compileall -q app
python -m pytest tests/unit -q --tb=short
```

根目录遗留的 `test_*.py` 不在默认 `testpaths` 内。CI 会执行双前端的 lint、type-check、Vite 构建、依赖审计，以及后端迁移回退/升级和 Docker 镜像构建。

## 数据库迁移

```bash
cd backend
alembic current
alembic upgrade head
alembic downgrade -1    # 仅在明确需要回滚时
```

新索引等结构变更必须进 `backend/alembic/versions/`，不要只靠模型 `create_all`。

## 备份与恢复

生产 Compose 默认启动 `backup` 服务：每天生成 PostgreSQL custom-format
备份和上传目录压缩包，保存到 `postgres_backups` volume，默认保留 14 天。
可通过 `BACKUP_INTERVAL_SECONDS` 和 `BACKUP_RETENTION_DAYS` 调整。该 volume
仍位于本机，正式环境应同步到异地对象存储。

查看备份：

```bash
docker compose exec backup ls -lh /backups
```

恢复前必须先停写并把目标备份复制到受控临时目录；恢复步骤应先在隔离环境演练。

手工备份与恢复：

```bash
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup-$(date +%Y%m%d).sql
docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backup-YYYYMMDD.sql
```

备份文件不要提交到 Git。上传目录在 `backend/storage/uploads`（Compose volume `backend_uploads`）。

## 周期任务

生产 Compose 默认启动 `celery-worker` 与 `celery-beat`。每日通知任务在
Asia/Shanghai 08:00 执行，小时任务在每个整点执行。开发 Compose 默认不启动
周期任务；需要联调时执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile operations up -d celery-worker celery-beat
```

检查任务进程：

```bash
docker compose logs --tail=100 celery-worker celery-beat
```

## 密钥轮换

生产 `DEVELOPMENT=false` 时拒绝默认 JWT secret 和已泄露密码。轮换后更新：

- 根目录 `.env`：`POSTGRES_PASSWORD`、`REDIS_PASSWORD`
- `backend/.env.production`：`SECRET_KEY`、`DATABASE_URL`、`REDIS_URL`
- 管理员密码（初始化脚本里的历史口令视为已泄露）

生产环境还必须把 `PAYMENT_PROVIDER` 配置为 `xunhu` 或 `pingpp`，填写对应凭据，且 `PAYMENT_NOTIFY_URL` / `PAYMENT_RETURN_URL` 必须使用 HTTPS；`mock` 仅允许开发测试。

轮换 JWT secret 会使现有登录失效，需要用户重新登录。

## 故障排查

| 现象 | 处理 |
| --- | --- |
| `/ready` 503 | 看响应里的 `postgres` / `redis` / `db_pool`；确认 Compose 健康检查与密码一致 |
| 验证/重置邮件不到 | 查 `FRONTEND_URL`、SMTP；接口为防枚举始终返回同一文案 |
| 前端静态资源是旧的 | 网关反代镜像内 Nginx，不要用 named `dist` volume；重建镜像 |
| 导出 429 | 每用户每分钟 20 次 |
| 跨租户 403 | 导出与按 ID 读取走 `require_document_access` |
| 请求对不上日志 | 使用响应头 `X-Request-ID`，生产日志为 JSON |

一次性 `check_*` / `fix_*` 脚本不进入生产镜像（见 `backend/.dockerignore`），不要在生产容器里执行。
