# 焊接系统管理员门户

## 📋 概述

这是焊接系统的管理员门户，提供完整的用户管理、系统监控、会员管理和统计功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（如果还没有）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

确保PostgreSQL数据库已启动，并更新 `backend/.env` 文件中的数据库连接信息：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### 3. 初始化系统

```bash
# 使用便捷脚本初始化并启动
python start-admin-system.py

# 或者手动初始化
cd backend
python scripts/init_admin_system.py
```

### 4. 启动服务

#### 方法1: 使用启动脚本（推荐）
```bash
python start-admin-system.py
```

#### 方法2: 手动启动
```bash
# 启动后端服务
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动管理员门户前端（需要先构建）
cd admin-portal
npm run dev
```

### 5. 访问系统

- **管理员门户**: http://localhost:3001
- **API文档**: http://localhost:8000/docs
- **管理员API**: http://localhost:8000/api/v1/admin

## 🔑 默认管理员账号

- **邮箱**: Laimiu.new@gmail.com
- **密码**: ghzzz123
- **权限**: 超级管理员

⚠️ **重要**: 首次登录后建议修改密码！

## 📊 功能特性

### 1. 用户管理
- ✅ 用户列表查看和搜索
- ✅ 用户详情查看
- ✅ 用户启用/禁用
- ✅ 用户会员等级调整
- ✅ 用户删除

### 2. 会员管理
- ✅ 订阅计划管理
- ✅ 订阅列表查看
- ✅ 会员等级升级
- ✅ 配额管理
- ✅ 即将过期订阅提醒

### 3. 系统监控
- ✅ 系统状态监控
- ✅ 性能指标监控
- ✅ 错误日志查看
- ✅ 系统配置管理

### 4. 数据统计
- ✅ 用户统计分析
- ✅ 订阅统计分析
- ✅ 增长趋势分析
- ✅ 会员等级分布

### 5. 公告管理
- ✅ 系统公告创建
- ✅ 公告发布和置顶
- ✅ 目标受众设置
- ✅ 公告到期管理

## 🗄️ 数据库结构

### 核心表

1. **users** - 用户表
   - 基础用户信息
   - 会员系统字段
   - 配额使用统计

2. **admins** - 管理员表
   - 管理员级别和权限
   - 关联用户表

3. **system_announcements** - 系统公告表
   - 公告内容和状态
   - 发布和过期时间

4. **system_logs** - 系统日志表
   - 操作日志记录
   - 错误信息追踪

5. **subscription_plans** - 订阅计划表
   - 会员等级定义
   - 功能配额限制

## 🔧 API接口

### 管理员认证
```
POST /api/v1/admin/auth/login
POST /api/v1/admin/auth/logout
GET  /api/v1/admin/auth/me
```

### 用户管理
```
GET    /api/v1/admin/users
GET    /api/v1/admin/users/{user_id}
POST   /api/v1/admin/users/{user_id}/adjust-membership
POST   /api/v1/admin/users/{user_id}/enable
POST   /api/v1/admin/users/{user_id}/disable
DELETE /api/v1/admin/users/{user_id}
```

### 会员管理
```
GET    /api/v1/admin/membership/subscription-plans
POST   /api/v1/admin/membership/subscription-plans
PUT    /api/v1/admin/membership/subscription-plans/{plan_id}
DELETE /api/v1/admin/membership/subscription-plans/{plan_id}
GET    /api/v1/admin/membership/subscriptions
POST   /api/v1/admin/membership/users/{user_id}/upgrade-membership
```

### 系统管理
```
GET /api/v1/admin/system/status
GET /api/v1/admin/statistics/overview
GET /api/v1/admin/statistics/users
GET /api/v1/admin/statistics/subscriptions
GET /api/v1/admin/logs/errors
GET  /api/v1/admin/config
PUT  /api/v1/admin/config
```

### 公告管理
```
GET    /api/v1/admin/announcements
POST   /api/v1/admin/announcements
PUT    /api/v1/admin/announcements/{announcement_id}
POST   /api/v1/admin/announcements/{announcement_id}/publish
DELETE /api/v1/admin/announcements/{announcement_id}
```

## 🔐 权限控制

### 管理员级别
- **super_admin**: 超级管理员，拥有所有权限
- **admin**: 普通管理员，拥有部分管理权限

### 权限范围
- 用户管理
- 系统配置
- 会员管理
- 公告管理
- 日志查看

## 🎨 前端技术栈

- React 18
- TypeScript
- Ant Design
- React Router
- Axios
- Zustand (状态管理)

## 🛠️ 后端技术栈

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT认证
- Python 3.8+

## 📝 开发说明

### 添加新的管理员权限

1. 在 `backend/app/models/admin.py` 中更新权限字段
2. 在 `backend/app/api/admin_deps.py` 中添加权限检查
3. 在前端添加相应的权限控制

### 添加新的会员等级

1. 在数据库 `subscription_plans` 表中添加新计划
2. 更新 `backend/app/services/membership_service.py` 中的配额限制
3. 在前端更新会员等级显示

### 自定义系统配置

在 `backend/app/services/system_service.py` 的 `get_system_config` 方法中添加新的配置项。

## 🚨 安全注意事项

1. **修改默认密码**: 首次登录后建议修改Laimiu.new@gmail.com的密码
2. **权限最小化**: 只给管理员必要的权限
3. **日志审计**: 定期检查系统日志，发现异常操作
4. **HTTPS**: 生产环境必须使用HTTPS
5. **备份**: 定期备份数据库

## 📞 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL是否启动
   - 验证数据库连接字符串
   - 确认数据库用户权限

2. **管理员登录失败**
   - 检查默认管理员是否创建
   - 验证密码哈希算法
   - 确认JWT配置正确

3. **前端无法访问后端API**
   - 检查CORS配置
   - 验证API端点URL
   - 确认后端服务运行状态

### 日志位置

- **应用日志**: backend/logs/
- **系统日志**: 数据库 system_logs 表
- **错误日志**: 控制台输出和日志文件

## 🔄 更新和维护

### 数据库迁移
```bash
# 创建新的迁移文件
# 手动执行迁移脚本
psql -d database_name -f migrations/add_admin_and_system_tables.sql
```

### 重新初始化
```bash
# 完全重新初始化（注意：会删除所有数据）
python backend/scripts/init_admin_system.py
```

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个系统。

---

**注意**: 这是一个完整的管理员门户系统，包含了会员管理的所有核心功能。您可以根据具体需求进行定制和扩展。