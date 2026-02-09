# 焊接工艺管理系统

## 🎯 项目简介

焊接工艺管理系统是一个基于 Web 的企业级焊接工艺文件管理平台，支持 WPS（焊接工艺规程）、PQR（焊接工艺评定记录）、pPQR（预焊接工艺评定记录）等文档的创建、编辑、审批和管理。

### 核心功能

- 📝 **模块化模板系统**: 灵活的模块组合，快速创建工艺文档
- 👥 **多租户架构**: 支持个人用户和企业工作空间
- 🔄 **审批工作流**: 完整的文档审批流程
- 📊 **数据统计**: 实时数据分析和报表
- 🔐 **权限管理**: 细粒度的角色和权限控制
- 💾 **数据隔离**: 企业数据完全隔离，确保安全

---

## 🏗️ 技术架构

### 后端技术栈
- **Python 3.11** - 主要开发语言
- **FastAPI 0.104+** - 高性能异步 Web 框架
- **SQLAlchemy 2.0+** - 现代化 ORM
- **PostgreSQL 15** - 企业级关系数据库
- **Redis 7** - 高性能缓存
- **Alembic** - 数据库版本控制

### 前端技术栈
- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Ant Design 5** - 企业级 UI 组件库
- **React Query** - 服务端状态管理
- **Zustand** - 客户端状态管理

### 部署技术栈
- **Docker** - 容器化部署
- **Docker Compose** - 服务编排
- **Nginx** - 反向代理和静态文件服务
- **Let's Encrypt** - 免费 SSL 证书

---

## 🚀 快速开始

### 开发环境

#### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 前端 - 用户门户
```bash
cd frontend
npm install
npm run dev
```

#### 前端 - 管理门户
```bash
cd admin-portal
npm install
npm run dev
```

### 生产环境部署

**完整部署指南请查看**: [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md)

#### 快速部署（推荐）

```bash
# 1. 克隆代码
git clone <你的仓库地址>
cd <项目目录>

# 2. 配置环境变量
vim backend/.env.production
# 填写 QQ 邮箱授权码等配置

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

---

## 📚 文档索引

### 部署相关
- 📖 [**完整部署指南**](./DEPLOYMENT_GUIDE.md) - 详细的部署步骤和配置说明
- 📧 [**QQ 邮箱配置**](./QQ_EMAIL_SETUP.md) - 如何获取 QQ 邮箱授权码
- ⚡ [**快速部署参考**](./QUICK_DEPLOY.md) - 常用命令和快速参考
- ✅ [**部署检查清单**](./DEPLOYMENT_CHECKLIST.md) - 部署前后的检查项
- 📦 [**部署文件说明**](./DEPLOYMENT_FILES_SUMMARY.md) - 所有部署文件的详细说明

### 开发相关
- 📘 [**后端文档**](./backend/README.md) - 后端开发指南
- 📗 [**前端文档**](./frontend/README.md) - 前端开发指南
- 📙 [**管理门户文档**](./admin-portal/README.md) - 管理门户开发指南

### 功能模块
- 🔧 [**模块开发文档**](./modules/development-docs.md) - 各功能模块开发指南
- 📋 [**WPS 模板系统**](./frontend/WPS_TEMPLATE_SYSTEM_README.md) - WPS 模板系统说明

---

## 🌐 在线访问

### 生产环境
- **用户门户**: https://sdhaohan.cn
- **管理门户**: https://laimiu.sdhaohan.cn
- **API 文档**: https://api.sdhaohan.cn/api/v1/docs

### 开发环境
- **用户门户**: http://localhost:3000
- **管理门户**: http://localhost:3001
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/v1/docs

---

## 📋 项目结构

```
焊接工艺管理系统/
├── backend/                    # 后端服务
│   ├── app/                    # 应用代码
│   │   ├── api/                # API 路由
│   │   ├── core/               # 核心配置
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic 模式
│   │   └── services/           # 业务逻辑
│   ├── alembic/                # 数据库迁移
│   ├── Dockerfile              # Docker 镜像
│   ├── requirements.txt        # Python 依赖
│   └── .env.production         # 生产环境配置
│
├── frontend/                   # 用户门户前端
│   ├── src/                    # 源代码
│   │   ├── components/         # 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 服务
│   │   └── store/              # 状态管理
│   ├── Dockerfile              # Docker 镜像
│   ├── package.json            # 依赖配置
│   └── .env.production         # 生产环境配置
│
├── admin-portal/               # 管理门户前端
│   ├── src/                    # 源代码
│   ├── Dockerfile              # Docker 镜像
│   ├── package.json            # 依赖配置
│   └── .env.production         # 生产环境配置
│
├── nginx/                      # Nginx 配置
│   ├── nginx.conf              # 主配置
│   ├── conf.d/                 # 站点配置
│   └── certbot/                # SSL 证书
│
├── docker-compose.yml          # Docker 编排
├── deploy.sh                   # 部署脚本
├── .gitignore                  # Git 忽略配置
│
└── 文档/
    ├── DEPLOYMENT_GUIDE.md
    ├── QQ_EMAIL_SETUP.md
    ├── QUICK_DEPLOY.md
    └── ...
```

---

## 🔧 环境要求

### 开发环境
- **Node.js**: >= 16.0.0
- **Python**: >= 3.11
- **PostgreSQL**: >= 15
- **Redis**: >= 7

### 生产环境
- **服务器**: 2核4GB 以上
- **操作系统**: Ubuntu 20.04/22.04 或 CentOS 7/8
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0

---

## 🛠️ 常用命令

### Docker 管理
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

### 数据库管理
```bash
# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 创建管理员账号
docker-compose exec backend python create_admin.py admin@example.com Admin@123456

# 备份数据库
docker-compose exec postgres pg_dump -U weld_user weld_db > backup.sql
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **项目主页**: https://sdhaohan.cn
- **问题反馈**: 请使用 GitHub Issues
- **邮箱**: 2564786659@qq.com

---

## 🎉 致谢

感谢所有为本项目做出贡献的开发者！

---

**开始使用**: 查看 [部署指南](./DEPLOYMENT_GUIDE.md) 快速部署你的系统！

