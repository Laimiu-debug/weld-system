# 焊序：Debug 与优化 TODO

更新时间：2026-08-20

## 当前验证结果

- [x] 完成项目结构、入口、配置、路由、依赖和部署文件的首轮检查。
- [x] `python -m compileall -q app` 通过，未发现 Python 语法错误。
- [x] `backend/tests` 下 `pytest` 现可收集并运行。根目录旧 `test_*.py` 仍未迁移，不在默认 `testpaths` 内。
- [x] GitHub Actions 已加入后端单测、迁移回退/升级、双前端 lint/type-check/build/audit 与三套 Docker 镜像构建门禁。
- [x] 生产依赖审计已使用 npm 官方 registry 执行：用户端与管理端均为 0 个已知漏洞；Vite 8 已落地。
- [x] Docker Compose 配置、容器健康状态与本地 HTTP 冒烟已验证；完整业务流程联调仍待补充。

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
  - 单元测试无需外部服务即可运行（79 passed）。根目录旧 `test_*.py` 尚未迁移，默认不收集。

- [x] 统一 Python 依赖来源并补齐运行依赖。
  - `pyproject.toml` 为依赖真源（含 pytz、psycopg2-binary、导出库）；`[project.optional-dependencies] dev` 放测试/格式化工具。
  - `requirements.txt` 仍给 Docker 使用，并已补上 pytz。未生成 poetry/uv lock。

- [x] 统一数据库迁移流程（基线）。
  - 补齐 `alembic.ini` / `env.py`，串联已有 revision；启动不再 `create_all`。
  - 已下线企业角色运行时建表接口；开发启动也不再执行 `ALTER TABLE`。
  - 空库请先运行 `python -m app.scripts.bootstrap_schema` 再 `alembic upgrade head`。历史 `backend/migrations` 脚本未并入。

- [x] 修复全局异常处理与敏感信息泄漏。
  - 只保留一套处理器；日志脱敏 Authorization 等敏感头；响应不再返回 traceback / 原始 `str(e)`。
  - 全局处理器会屏蔽 5xx 与常见数据库/堆栈技术细节；高敏调试打印已继续清扫。
  - 个别业务端点仍保留 `str(e)` 或 `print`，需后续按模块逐步改为结构化日志。

- [x] 让启动和健康检查真实反映依赖状态。
  - `GET /health`：liveness；`GET /ready` 与 `GET /api/v1/health`：readiness（Postgres + Redis，失败 503）。
  - 生产启动时依赖不可用则拒绝启动。

- [x] 修正异步路由中使用同步 SQLAlchemy Session 的阻塞问题。
  - 无 `await` 的 `async def` 端点已改为同步 `def` + 同步 Session。
  - 仍保持 async：支付回调（读取 request body）与头像上传（`await file.read()`）。
  - 未做 AsyncSession 全量迁移，也未做并发压测。

- [x] 完成或下线返回占位数据的业务接口。
  - 质量不合格品/统计、生产进度/记录/统计、pPQR 转换/统计、报表改为真实聚合。
  - `files` 上传/下载改为本地 `UPLOAD_DIR/files`，校验扩展名、大小与路径穿越。
  - 邮箱验证、忘记/重置密码、质量/生产创建与编辑页、焊工导出、生产日志入口已接到真实接口。
  - 会员支付与续费：创单使用 `transaction_id`；状态查询读库；回调按商户订单号激活；续费/自动续费不再未扣款即延期。

- [x] 将密码重置、修改密码、邮箱验证等敏感参数从 query string 移到请求体。
  - `change-password` / `forgot-password` / `reset-password` / `verify-email` / `resend-verification` 使用 JSON body。
  - 忘记密码不再枚举邮箱，也不再返回 reset_token。

- [x] 为登录、验证码、找回密码、导出增加限流。
  - 按 IP + 账号组合限流；Redis 优先，失败回退内存。
  - 支付创单与回调已按 IP/用户限流。
  - WPS/PQR/pPQR Word/PDF 导出：`enforce_export_limit`，每用户每分钟 20 次。

## P2：工程质量与可维护性

- [x] 升级并修复前端依赖安全告警（基线）。
  - `axios` 已升到当前 1.x 修复线；用户端 `echarts` / `uuid` 同步升级。
  - Vite 已升级到 8.2.1，并配置 vendor/antd/editor 分包；生产关闭 sourcemap。
  - 生产 `npm audit --omit=dev` 当前为 0 个已知漏洞（npm 官方 registry）。

- [x] 建立 CI 质量门禁（后端单元测试 + 前端/管理端构建）。
  - `.github/workflows/ci.yml`：compileall、单测、空库初始化、Alembic 回退/升级和 Docker 镜像构建。
  - `frontend-build` / `admin-build`：Node 20、`npm ci`、lint、type-check、`vite build` 与阻断式 `npm audit`。
  - 两端 type-check 与 Hooks 调用规则 lint 全绿；Compose 配置、容器健康状态与 HTTP 冒烟已验证。
  - `react-hooks/exhaustive-deps` 历史警告仍需按页面审查，避免机械补依赖导致重复请求或渲染循环。

- [x] 清理生产仓库中的一次性修复脚本、备份和调试资产（基线）。
  - 已删除未鉴权的 WPS 模板 `debug/test-create`、`debug/test` 与 WPS `debug/token`。
  - 已删除根目录/后端一次性 `check_*` / `fix_*` / `debug_user.py`、SQL 备份、焊口示意图测试页与 V2/V3 生成器。
  - `backend/.dockerignore` 排除根目录 `check_*` / `fix_*` / `test_*.py` 和 SQL 备份。
  - `backend/migrations` 历史 SQL 与 `backend/scripts` 运维脚本仍保留，未并入 Alembic/CLI。

- [x] 拆分超大模块并收敛重复实现（基线）。
  - 企业工厂/部门从 `enterprise.py` 拆到 `enterprise_org.py`；共享校验在 `enterprise_deps.py`。
  - 焊口示意图保留生产使用的 V1 字段与 V4 字段，删除未挂路由的 V2/V3 与测试页。
  - `welder_service.py` 超大类、40KB+ React 页面尚未按用例拆分。

- [x] 统一 API 响应模型和错误协议（基线）。
  - 管理端列表/详情/统计改为 `success_payload`（含 `request_id`）；错误 detail 不再拼接 `str(e)`。
  - 企业员工配额/统计同样走 `success_payload`。
  - 大量业务端点仍是手工 dict，未完成全量迁移与客户端类型生成。

- [x] 审查并补齐数据库索引、唯一约束和 N+1 查询（基线）。
  - WPS/PQR/pPQR 列表的审批实例/工作流改为批量加载（`approval_lookup`）。
  - `_can_approve` 改为一次加载用户企业角色权限，列表不再按行查员工/角色。
  - 已加通知未读、公告发布、审批状态+时间、质量 owner/结果、员工 user+company+status 索引。
  - 未保存 EXPLAIN ANALYZE 基线。

- [x] 合并前端重复认证状态与 API 封装（基线）。
  - 用户端 `AuthContext` 改为 Zustand `authStore` 的薄封装；`App` 监听 `storage` 做跨标签页登录/登出同步。
  - 管理端共享库已改走 `apiService.authGet/authPost`；登录页 `fetch` 保留。401 并发刷新与自动化测试未补齐。

- [x] 优化前端包体和首屏加载（基线）。
  - 路由级懒加载已有；Vite 8 构建按 react/antd/echarts/editor/vendor 分包，生产不输出 sourcemap。
  - 尚未引入 bundle analyzer 报告与体积预算；Ant Design / TipTap 仍为整包引入。

- [x] 补齐可观测性（基线）。
  - 请求中间件写入 `X-Request-ID` / `X-Process-Time`，日志带 request_id；生产 JSON 日志。
  - `/ready` 增加数据库连接池快照。
  - 尚未采集 Celery/导出/支付的独立指标与告警。

- [x] 补齐周期任务与自动备份运行入口。
  - Compose 增加 Celery worker/beat，通知任务按小时与每天 08:00 调度，并具备自动重试。
  - Compose 增加 PostgreSQL 与上传文件每日备份、原子落盘及默认 14 天保留策略；本地开发默认不启动 operations profile。
  - 仍建议将备份同步到异地对象存储，并定期执行恢复演练。

- [x] 修正文档与环境声明。
  - README 改为实际支持的 Python 3.11、Node 20、PostgreSQL 15、Redis 7、Compose v2。
  - 运维步骤见 `docs/OPERATIONS.md`（本地开发、测试、迁移、备份、密钥轮换、故障排查）。
  - 删除对仓库中不存在的 `deploy.sh` / `DEPLOYMENT_GUIDE.md` 的引用。

- [x] 设备维护/使用记录与质量图片。
  - 维护/使用记录 CRUD + 列表页三 Tab；质量详情接真实记录与 files 上传/查看。

- [x] 报表与管理端占位页（本轮）。
  - WPS/PQR/使用报表改走真实列表与统计，支持导出 CSV。
  - 管理端系统监控接 `/system/status` 与错误日志；企业/订阅列表可导出 CSV。
  - 焊工编辑页接真实详情/更新；WPS/PQR 批量导出改为可下载 CSV。
  - 焊工创建预览改为表单 Modal；个人员工页去掉工厂/邀请假数据，改走企业接口。
  - 管理端安全管理页列出真实 `admins` 账号，安全日志来自用户最近登录与错误日志。

## 建议执行顺序

1. 先处理越权、凭据/JWT、默认密钥与调试入口（P0 安全项）。
2. 修复干净构建和前端发布链路，确保每次发布的是确定产物。
3. 修复 pytest/依赖/迁移，建立 CI 门禁，获得可靠回归基线。
4. P1 占位功能、邮箱验证、同步端点与导出限流已落地。
5. P2 基线已补：脚本清理、企业模块拆分、审批权限批量加载、管理端统一响应、Vite 8 分包。
   - 2026-08-21：删除 9 个未路由 mock 页；管理端移除 `useMockData`/`mockData`；下线未挂载 `*_old`/`admin_simple|complete`；`welder_service` 履历段拆到 `welder_career_mixin`；根目录手工 `test_*.py` 迁入 `legacy_tests/`；主链路见 `docs/SMOKE_CHECKLIST.md`。
   - 2026-08-21：业务缺口——待办审批按步骤 `approver_ids` 过滤；WPS `search_wps` 接入 workspace；管理调整会员/启停与会员升级补齐 SystemLog + 用户通知。
   - 剩余：API 响应全量迁移、证书段再拆分、按冒烟清单完成联调勾选。
