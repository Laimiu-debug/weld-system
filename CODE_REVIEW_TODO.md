# 焊序：Debug 与优化 TODO

更新时间：2026-08-19

## 当前验证结果

- [x] 完成项目结构、入口、配置、路由、依赖和部署文件的首轮检查。
- [x] `python -m compileall -q app` 通过，未发现 Python 语法错误。
- [x] `backend/tests` 下 `pytest` 现可收集并运行：44 个单元测试通过。根目录旧 `test_*.py` 仍未迁移，不在默认 `testpaths` 内。
- [ ] 用户端和管理端尚未完成 TypeScript、ESLint、Vite 构建验证：`npm ci` 长时间无进展后已中止，导致 `tsc`、`eslint`、`vite` 尚不可用。需要在 Node 18/20 LTS 的干净环境或 CI 中复测。
- [x] 生产依赖审计已执行（npm 官方 registry）：用户端 10 项告警（6 high、4 moderate），管理端 9 项告警（8 high、1 moderate）。
- [ ] Docker 联调未执行：当前机器没有可用的 Docker 命令。
- [x] GitHub Actions `backend-unit` 已加入：compileall + `pytest tests/unit`。

## P0：发布前必须处理

- [x] 修复 WPS/PQR/pPQR 导出接口的越权访问。
  - 导出与相关按 ID 读取/更新/下载改为 `require_document_access` + `DataAccessMiddleware.check_access`。
  - 覆盖：`wps_export.py`、`pqr_export.py`、`ppqr_export.py`，以及 `pqr.py` 的试样、评定、PDF/Excel/批量导出。
  - 自动化测试：`backend/tests/unit/test_document_access.py`、`test_export_authorization.py`（同租户 200、跨租户 403、缺失 404、未登录 401/403）。
  - 上线后请用真实账号再做一次跨租户导出冒烟。

- [x] 删除管理端的凭据/令牌日志和客户端伪造 JWT 逻辑。
  - 重写 `admin-portal/src/services/auth.ts`：只保存后端签发的 JWT，失败不再客户端造 token。
  - 删除 `TestLogin.tsx`、`AuthTest.tsx`、`DebugPage.tsx`、`public/test-auth.html`、`public/fix-auth.html` 及对应路由。
  - 后端删除 `/admin/auth/test-token` 与登录调试打印；`verify_token` 去掉 DEVELOPMENT/`eval` 旁路。
  - **运维必做**：轮换管理员 `Laimiu` 密码，旧值已从仓库移除且禁止再用于初始化脚本。

- [x] 移除仓库中的生产凭据并轮换现有密钥。
  - Compose 改为从根目录 `.env` 注入 `POSTGRES_PASSWORD` / `REDIS_PASSWORD`，生产配置不再发布 5432/6379/8000。
  - `Settings` 在 `DEVELOPMENT=false` 时拒绝默认 JWT secret、已泄露的数据库/Redis 密码。
  - **运维必做**：复制 `.env.example` 为 `.env` 并生成新密钥；更新 `backend/.env.production` 中的 `SECRET_KEY`、`DATABASE_URL`、`REDIS_URL`；轮换线上 PostgreSQL、Redis、JWT secret 与管理员密码。已提交过的旧值视为泄露。

- [x] 修复管理端生产镜像无法从干净仓库构建的问题。
  - `admin-portal/Dockerfile` 与 `Dockerfile.prod` 改为多阶段构建：`npm ci && npm run build:check`。
  - 增加 `admin-portal/.dockerignore`。

- [x] 修复前端发布使用持久化 `dist` volume 导致旧资源残留的问题。
  - 删除 `frontend_dist` / `admin_dist` named volume。
  - 网关 Nginx 改为反代 `frontend:80` 与 `admin-portal:80`，静态文件来自镜像层。
  - **运维必做**：部署后删除旧 volume（`docker volume rm` 对应 `*_frontend_dist` / `*_admin_dist`），再 `compose build && up`，确认 `index.html` 引用的 JS hash 已更新。

## P1：稳定性与正确性

- [x] 重建后端测试体系，使 `pytest` 可重复运行。
  - `[tool.pytest.ini_options]`、`testpaths = ["tests"]`、`norecursedirs` 已配置。
  - 单元测试无需外部服务即可运行（44 passed）。根目录旧 `test_*.py` 尚未迁移，默认不收集。

- [x] 统一 Python 依赖来源并补齐运行依赖。
  - `pyproject.toml` 为依赖真源（含 pytz、psycopg2-binary、导出库）；`[project.optional-dependencies] dev` 放测试/格式化工具。
  - `requirements.txt` 仍给 Docker 使用，并已补上 pytz。未生成 poetry/uv lock。

- [x] 统一数据库迁移流程（基线）。
  - 补齐 `alembic.ini` / `env.py`，串联已有 revision；启动不再 `create_all`。
  - 空库请先运行 `python -m app.scripts.bootstrap_schema` 再 `alembic upgrade head`。历史 `backend/migrations` 脚本未并入。

- [x] 修复全局异常处理与敏感信息泄漏。
  - 只保留一套处理器；日志脱敏 Authorization 等敏感头；响应不再返回 traceback / 原始 `str(e)`。
  - 个别业务端点仍可能把 `str(e)` 放进 detail，需后续按模块清扫。

- [x] 让启动和健康检查真实反映依赖状态。
  - `GET /health`：liveness；`GET /ready` 与 `GET /api/v1/health`：readiness（Postgres + Redis，失败 503）。
  - 生产启动时依赖不可用则拒绝启动。

- [ ] 修正异步路由中使用同步 SQLAlchemy Session 的阻塞问题。
  - 现状：大量 `async def` 端点内部执行同步 ORM 查询，会阻塞事件循环。
  - 验收：统一改为同步端点 + 同步 Session，或完整迁移到 AsyncSession；用并发压测确认延迟和吞吐改善。

- [x] 完成或下线返回占位数据的业务接口。
  - 质量不合格品/统计、生产进度/记录/统计、pPQR 转换/统计、报表改为真实聚合；旧 files 上传仍为 501。
  - 会员支付与续费：创单使用 `transaction_id`；状态查询读库；回调按商户订单号激活；续费/自动续费不再未扣款即延期。

- [x] 将密码重置、修改密码、邮箱验证等敏感参数从 query string 移到请求体。
  - `change-password` / `forgot-password` / `reset-password` / `verify-email` / `resend-verification` 使用 JSON body。
  - 忘记密码不再枚举邮箱，也不再返回 reset_token。

- [x] 为登录、验证码、找回密码增加限流（导出限流仍待做）。
  - 按 IP + 账号组合限流；Redis 优先，失败回退内存。
  - 支付创单与回调已按 IP/用户限流。

## P2：工程质量与可维护性

- [ ] 升级并修复前端依赖安全告警。
  - 优先直接依赖：`axios`、`react-router-dom`，用户端还包括 `echarts`；更新 lockfile 后重新运行生产和全量 `npm audit`。
  - 验收：无 high/critical；对无法立即升级的告警记录可利用性判断、缓解措施和到期时间。

- [x] 建立 CI 质量门禁（后端单元测试）。
  - `.github/workflows/ci.yml`：安装最小依赖、compileall、`pytest tests/unit`。
  - 前端 type-check/lint/build/audit 与 Compose 冒烟尚未加入。

- [ ] 清理生产仓库中的一次性修复脚本、备份和调试资产。
  - 重点：后端根目录大量 `check_*`、`fix_*`、`reset_*`、`test_*`，已提交的 SQL 备份、静态 OpenAPI 快照和公开 HTML 调试页。
  - 验收：保留的运维命令移入受控 CLI，默认只读、要求显式环境和确认；备份不入 Git，调试页面不进入生产镜像。

- [ ] 拆分超大模块并收敛重复实现。
  - 重点：`welder_service.py`（约 75 KB）、`enterprise.py`（约 56 KB）、多处 40–55 KB React 页面，以及两版焊口示意图生成器。
  - 验收：按业务用例拆分 service/hook/component；抽取共享筛选、分页、权限和表单逻辑；关键模块有单元测试后再重构。

- [ ] 统一 API 响应模型和错误协议。
  - 现状：大量端点使用 `response_model=dict` 和手工 `{success,data,message}`，类型约束弱且错误格式不一致。
  - 验收：定义泛型分页/成功/错误模型，生成的 OpenAPI 可直接产出两套前端客户端类型。

- [ ] 审查并补齐数据库索引、唯一约束和 N+1 查询。
  - 重点：所有 tenant/workspace/company/factory 过滤列，文档编号，状态 + 时间排序，审批待办，通知未读和报表聚合。
  - 验收：对主要列表与仪表盘保存 `EXPLAIN ANALYZE` 基线，设定查询数和 P95 延迟预算。

- [ ] 合并前端重复认证状态与 API 封装。
  - 现状：用户端同时存在 AuthContext 和 Zustand authStore，管理端认证又有独立 fetch/apiService 路径，容易产生 token 和用户状态不一致。
  - 验收：每个应用只有一个认证真源；刷新、登出、401 并发、跨标签页同步都有自动化测试。

- [ ] 优化前端包体和首屏加载。
  - 对大型页面和编辑器按路由懒加载；检查 Ant Design、ECharts、TipTap 的按需引入；构建时输出 bundle analyzer 报告并设体积预算。

- [ ] 补齐可观测性。
  - 使用 request ID、结构化日志、统一耗时指标；采集 API 错误率、数据库池、Redis、Celery、导出任务和支付回调指标；配置告警阈值。

- [ ] 修正文档与环境声明。
  - README 引用了当前仓库不存在的部署文档/脚本，并声明 Node >=16；应以实际支持的 Node LTS、Python、Compose 版本和可复制命令为准。
  - 增加“本地开发”“测试”“迁移”“备份恢复”“密钥轮换”“故障排查”文档。

## 建议执行顺序

1. 先处理越权、凭据/JWT、默认密钥与调试入口（P0 安全项）。
2. 修复干净构建和前端发布链路，确保每次发布的是确定产物。
3. 修复 pytest/依赖/迁移，建立 CI 门禁，获得可靠回归基线。
4. 完成占位功能和异常/健康检查，再进行异步模型、查询和包体优化。
5. 最后拆分大文件、统一响应模型与认证状态，持续补齐可观测性和文档。
