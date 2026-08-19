# 焊序 - 用户门户前端

## 项目概述

这是焊序的用户门户前端，基于React 18 + TypeScript + Vite + Ant Design构建。

## 技术栈

- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全的JavaScript
- **Vite** - 快速构建工具
- **Ant Design 5.0+** - 企业级UI组件库
- **React Query** - 服务端状态管理
- **Zustand** - 轻量级客户端状态管理
- **React Router 6** - 单页应用路由管理
- **Axios** - HTTP客户端

## 快速开始

### 方式一：使用快速启动脚本（推荐）

**Windows用户:**
```bash
双击运行 quick-start.bat
```

**Linux/macOS用户:**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

### 方式二：手动安装

1. 进入项目目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

## 系统要求

- Node.js 16.0 或更高版本
- npm 7.0 或更高版本

## 项目结构

```
frontend/
├── public/                     # 静态资源
├── src/                        # 源代码
│   ├── components/             # 通用组件
│   │   ├── Layout.tsx         # 布局组件
│   │   └── LoadingSpinner.tsx # 加载组件
│   ├── pages/                 # 页面组件
│   │   ├── Auth/              # 认证页面
│   │   │   ├── Login.tsx      # 登录页面
│   │   │   ├── Register.tsx   # 注册页面
│   │   │   ├── ForgotPassword.tsx # 忘记密码
│   │   │   └── ResetPassword.tsx # 重置密码
│   │   ├── Dashboard/         # 仪表盘
│   │   │   └── index.tsx      # 仪表盘页面
│   │   ├── WPS/               # WPS管理
│   │   │   ├── WPSList.tsx    # WPS列表
│   │   │   ├── WPSCreate.tsx  # 创建WPS
│   │   │   ├── WPSEdit.tsx    # 编辑WPS
│   │   │   └── WPSDetail.tsx  # WPS详情
│   │   ├── PQR/               # PQR管理
│   │   │   ├── PQRList.tsx    # PQR列表
│   │   │   ├── PQRCreate.tsx  # 创建PQR
│   │   │   ├── PQREdit.tsx    # 编辑PQR
│   │   │   └── PQRDetail.tsx  # PQR详情
│   │   ├── pPQR/              # pPQR管理
│   │   │   ├── PPQRList.tsx   # pPQR列表
│   │   │   ├── PPQRCreate.tsx # 创建pPQR
│   │   │   ├── PPQREdit.tsx   # 编辑pPQR
│   │   │   └── PPQRDetail.tsx # pPQR详情
│   │   ├── Profile/           # 个人中心
│   │   │   └── ProfileInfo.tsx # 个人信息
│   │   └── Membership/        # 会员管理
│   │       └── MembershipCurrent.tsx # 当前套餐
│   ├── services/              # API服务
│   │   ├── api.ts            # API客户端
│   │   └── auth.ts           # 认证服务
│   ├── store/                 # 状态管理
│   │   └── authStore.ts      # 认证状态
│   ├── types/                 # TypeScript类型
│   │   └── index.ts          # 类型定义
│   ├── styles/                # 样式文件
│   │   └── globals.css       # 全局样式
│   ├── App.tsx                # 根组件
│   ├── main.tsx               # 应用入口
│   └── vite-env.d.ts          # Vite类型定义
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
├── quick-start.bat            # Windows快速启动脚本
├── quick-start.sh             # Linux/macOS快速启动脚本
├── INSTALL.md                 # 安装指南
├── TROUBLESHOOTING.md         # 故障排除指南
└── README.md
```

## 已完成功能

### 1. 项目基础架构
- ✅ 创建项目基础配置文件
- ✅ 配置TypeScript和Vite
- ✅ 设置路径别名和环境变量

### 2. UI布局和导航
- ✅ 设计响应式布局组件
- ✅ 实现侧边栏导航
- ✅ 创建顶部导航栏
- ✅ 添加用户信息和会员状态显示

### 3. 认证系统
- ✅ 实现认证服务层
- ✅ 创建认证状态管理
- ✅ 设计登录页面UI
- ✅ 添加路由守卫组件

### 4. 仪表盘
- ✅ 创建仪表盘页面
- ✅ 添加统计卡片
- ✅ 实现快速操作区域
- ✅ 显示最近记录列表

### 5. WPS管理模块
- ✅ 创建WPS列表页面
- ✅ 实现搜索和筛选功能
- ✅ 创建WPS创建页面（多步骤表单）
- ✅ 添加WPS详情和编辑页面占位

### 6. PQR管理模块
- ✅ 创建PQR列表页面
- ✅ 实现搜索和筛选功能
- ✅ 创建PQR创建页面（多步骤表单）
- ✅ 添加PQR详情和编辑页面占位

### 7. pPQR管理模块
- ✅ 创建pPQR列表页面
- ✅ 实现搜索和筛选功能
- ✅ 创建pPQR创建页面（多步骤表单）
- ✅ 添加pPQR详情和编辑页面占位

### 8. 个人中心
- ✅ 创建个人信息页面
- ✅ 实现用户信息编辑功能

### 9. 会员管理
- ✅ 创建会员中心页面
- ✅ 显示当前套餐和使用配额
- ✅ 实现套餐对比功能

### 10. API服务和状态管理
- ✅ 创建基础API客户端
- ✅ 实现请求/响应拦截器
- ✅ 添加错误处理机制
- ✅ 实现状态管理和权限控制

## 待完成功能

### 1. 其他业务模块
- [ ] 焊材管理模块
- [ ] 焊工管理模块
- [ ] 设备管理模块
- [ ] 生产管理模块
- [ ] 质量管理模块
- [ ] 报表统计模块
- [ ] 企业员工管理模块

### 2. 个人中心完善
- [ ] 系统设置页面
- [ ] 安全设置页面
- [ ] 通知设置页面

### 3. 会员体系完善
- [ ] 套餐升级页面
- [ ] 支付页面
- [ ] 订阅历史页面

### 4. 响应式设计
- [ ] 移动端适配优化
- [ ] 平板端适配优化

### 5. 错误处理和用户体验优化
- [ ] 全局错误处理
- [ ] 加载状态优化
- [ ] 用户反馈机制

## 开发说明

### 运行项目

1. 安装依赖
```bash
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

3. 构建生产版本
```bash
npm run build
```

### 环境变量配置

复制 `.env.example` 到 `.env` 并配置相应的环境变量：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=焊序
VITE_ENABLE_MOCK_DATA=true
```

### 代码规范

项目使用以下工具进行代码规范检查：

- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化
- **TypeScript** - 类型检查

## 故障排除

如果遇到问题，请参考以下文档：

1. [安装指南](./INSTALL.md) - 详细的安装步骤
2. [故障排除指南](./TROUBLESHOOTING.md) - 常见问题及解决方案

## 功能特性

### 会员体系

- **免费版**: 基础功能，有限制
- **专业版**: 完整WPS/PQR/pPQR功能
- **高级版**: 包含设备和生产管理
- **旗舰版**: 包含所有功能和报表
- **企业版**: 包含员工管理和多工厂支持

### 权限控制

- 基于会员等级的功能权限
- 企业用户的员工权限管理
- 资源访问控制

### 响应式设计

- 移动端适配
- 平板端适配
- 桌面端优化

## 部署

### 开发环境

```bash
npm run dev
```

### 生产环境

```bash
npm run build
npm run preview
```

## 联系方式

如有问题或建议，请联系开发团队。

---

*文档更新时间: 2025-10-16*
*版本: 1.0*