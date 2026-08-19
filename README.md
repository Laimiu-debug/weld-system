# 焊序（焊接工艺管理系统）

基于 Web 的焊接工艺文件管理平台，覆盖 WPS、PQR、pPQR 的创建、审批与导出，以及焊工、设备、生产与质量记录。

## 运行环境

- Python **3.11**
- Node.js **20 LTS**（npm 10）
- PostgreSQL **15**
- Redis **7**
- Docker Compose **v2**（生产编排）

## 仓库结构

```
backend/         FastAPI API（依赖真源 pyproject.toml，镜像用 requirements.txt）
frontend/        用户门户（Vite + React 18 + Ant Design 5）
admin-portal/    管理门户
nginx/           反向代理
docs/            运维与专项文档
docker-compose.yml
.env.example
```

## 本地开发

完整步骤见 [`docs/OPERATIONS.md`](docs/OPERATIONS.md)。最短路径：

1. 复制 `.env.example` 为 `.env`，填写强随机 `POSTGRES_PASSWORD` / `REDIS_PASSWORD`。
2. 后端：

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -e ".[dev]"
# 或：pip install -r requirements.txt
copy .env.example .env         # 并设置 DEVELOPMENT=true
alembic upgrade head           # 空库先 python -m app.scripts.bootstrap_schema
uvicorn app.main:app --reload --port 8000
```

3. 用户端 / 管理端：

```bash
cd frontend && npm ci && npm run dev      # http://localhost:3000
cd admin-portal && npm ci && npm run dev  # http://localhost:3001
```

## 测试与 CI

```bash
cd backend
python -m compileall -q app
python -m pytest tests/unit -q --tb=short
```

GitHub Actions（`.github/workflows/ci.yml`）：后端 compileall + pytest；用户端与管理端 `npm ci && vite build`。

## 生产部署

使用根目录 `docker-compose.yml`。密钥从 `.env` 注入，不要把 PostgreSQL / Redis / API 端口暴露到公网。步骤、迁移、备份与密钥轮换见 [`docs/OPERATIONS.md`](docs/OPERATIONS.md)。

生产健康检查：

- `GET /health`：进程存活
- `GET /ready` 或 `GET /api/v1/health`：PostgreSQL + Redis，失败返回 503

## 文档

- [运维手册](docs/OPERATIONS.md)（本地开发、测试、迁移、备份、密钥轮换、故障排查）
- [用户端](frontend/README.md) / [管理端](admin-portal/README.md)
- 支付、审批等专项说明在 `docs/`；历史实现纪要在 `md/`、`modules/`，不作为部署依据
- 工程缺口跟踪：[`CODE_REVIEW_TODO.md`](CODE_REVIEW_TODO.md)
