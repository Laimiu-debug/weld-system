# 焊序主链路冒烟清单

用于发布前或联调后的人工验证。默认环境：用户端、管理端、后端均已启动，PostgreSQL / Redis 健康。

勾选约定：`[ ]` 未测，`[x]` 通过。失败请记下账号、路径、`X-Request-ID` 与截图。

## 0. 就绪

- [ ] `GET /health` 返回 200
- [ ] `GET /ready` 或 `GET /api/v1/health` 返回 200（Postgres + Redis）
- [ ] 用户端可打开登录页；管理端可打开登录页

## 1. 账号与认证

- [ ] 注册新用户（邮箱验证若开启则完成验证）
- [ ] 登录 / 退出 / 再登录
- [ ] 忘记密码 → 重置密码 → 新密码登录
- [ ] 未登录访问受保护路由会跳转登录

## 2. 企业与权限

- [ ] 创建或加入企业工作区
- [ ] `/enterprise/employees`：邀请/启用/禁用员工
- [ ] `/enterprise/roles`：角色增删改与权限勾选
- [ ] `/enterprise/approval-workflows`：创建审批流并设为某文档类型默认
- [ ] 无权限账号访问受限菜单得到拒绝页（非白屏）

## 3. 工艺文档（WPS / PQR / pPQR）

- [ ] 创建 WPS → 编辑 → 详情 → 列表可见
- [ ] 提交审批 → 审批人通过/驳回 → 状态正确
- [ ] 导出 Word/PDF（同租户成功）
- [ ] 另一企业账号访问同 ID 导出 → 403（跨租户）
- [ ] 创建 PQR → 关联/编辑 → 导出
- [ ] 创建 pPQR → 编辑 → 导出
- [ ] 模板管理：新建模板 → 用模板创建 WPS

## 4. 资源与生产质检

- [ ] 焊工：创建 → 证书/持证项目 → 详情 → 履历导出（若启用）
- [ ] 设备：创建 → 维护/使用记录 Tab 可读写
- [ ] 材料：入库/列表/详情
- [ ] 生产任务：创建 → 编辑 → 详情
- [ ] 生产计划：`/production/plans` 创建/编辑/删除
- [ ] 质量检验：按项目/容器/焊缝/片子录入 → 缺陷与定位落库 → 详情可见图片附件
- [ ] 质量标准：`/quality/standards` CRUD
- [ ] 员工绩效：`/employees/performance` CRUD
- [ ] 自定义报表：`/reports/custom` 保存模板并运行汇总

## 5. 会员与支付

- [ ] 查看当前会员与配额
- [ ] 升级页创单成功（返回 `transaction_id`）
- [ ] 开发环境 `PAYMENT_PROVIDER=mock` 时可模拟完成；生产非 mock 时 `/payments/mock-complete/*` 不可用
- [ ] 支付成功后会员等级/到期日更新
- [ ] 管理端「待确认支付」可审核（若走人工确认）

## 6. 管理端闭环

- [ ] 管理员登录（勿使用已轮换作废的旧默认口令）
- [ ] 用户列表/详情：启停、调会员、验邮箱
- [ ] 企业列表/详情
- [ ] 订阅与定价计划可读写
- [ ] 共享库待审资源可通过/驳回
- [ ] 公告发布
- [ ] 系统监控与错误日志为真实接口数据（非空壳假数据）

## 7. 报表与通知

- [ ] WPS / PQR / 使用报表有数据并可导出 CSV
- [ ] 通知中心可读；关闭某类偏好后不再收到该类通知

## 8. 发布回归（可选但建议）

- [ ] `cd backend && python -m compileall -q app && python -m pytest tests/unit -q`
- [ ] `cd frontend && npm ci && npm run build:check`
- [ ] `cd admin-portal && npm ci && npm run build:check`
- [ ] 生产镜像构建后 `index.html` 引用的 JS hash 已更新（无旧 dist volume）

## 真实页面对照（勿再挂演示页）

| 能力 | 路径 |
|------|------|
| 企业员工 | `/enterprise/employees` |
| 企业角色 | `/enterprise/roles` |
| 审批流 | `/enterprise/approval-workflows` |
| 个人侧员工（非企业菜单） | `/employees` |
| 设备 / 生产 / 质量 / 报表 | `/equipment` `/production` `/quality` `/reports` |
