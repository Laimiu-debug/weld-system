# 焊接工艺管理系统 - 用户门户前端开发计划

## 项目概述

根据开发文档，用户门户是焊接工艺管理系统的核心前端界面，为个人用户和企业用户提供11个主要功能模块。本文档详细规划了用户门户前端的设计和实现方案。

## 技术栈

根据开发文档中的技术选型：

- **React 18 + TypeScript** - 现代化前端框架，类型安全
- **Vite 5.0+** - 快速构建工具，热重载支持
- **Ant Design 5.0+** - 企业级UI组件库，丰富的组件生态
- **React Query (TanStack Query)** - 服务端状态管理，缓存和同步
- **Zustand** - 轻量级客户端状态管理
- **React Router 6** - 单页应用路由管理
- **Axios** - HTTP客户端，请求拦截和错误处理

## 项目结构

```
frontend/
├── public/                     # 静态资源
│   ├── favicon.ico
│   └── images/
├── src/                        # 源代码
│   ├── main.tsx               # 应用入口
│   ├── App.tsx                # 根组件
│   ├── vite-env.d.ts          # Vite类型定义
│   ├── components/            # 通用组件
│   │   ├── Layout/            # 布局组件
│   │   ├── Forms/             # 表单组件
│   │   ├── Tables/            # 表格组件
│   │   ├── Charts/            # 图表组件
│   │   └── Common/            # 通用组件
│   ├── pages/                 # 页面组件
│   │   ├── Auth/              # 认证页面
│   │   ├── Dashboard/         # 仪表盘
│   │   ├── WPS/              # WPS管理
│   │   ├── PQR/              # PQR管理
│   │   ├── pPQR/             # pPQR管理
│   │   ├── Materials/        # 焊材管理
│   │   ├── Welders/          # 焊工管理
│   │   ├── Equipment/        # 设备管理
│   │   ├── Production/       # 生产管理
│   │   ├── Quality/          # 质量管理
│   │   ├── Reports/          # 报表统计
│   │   ├── Employees/        # 员工管理（企业会员）
│   │   ├── Profile/          # 个人中心
│   │   └── Membership/       # 会员升级
│   ├── hooks/                 # 自定义Hooks
│   │   ├── useAuth.ts
│   │   ├── useWPS.ts
│   │   ├── usePQR.ts
│   │   └── useWebSocket.ts
│   ├── services/              # API服务
│   │   ├── api.ts            # API客户端
│   │   ├── auth.ts           # 认证服务
│   │   ├── wps.ts            # WPS服务
│   │   ├── pqr.ts            # PQR服务
│   │   └── user.ts           # 用户服务
│   ├── store/                 # 状态管理
│   │   ├── index.ts
│   │   ├── authStore.ts
│   │   └── wpsStore.ts
│   ├── types/                 # TypeScript类型
│   │   ├── auth.ts
│   │   ├── wps.ts
│   │   ├── pqr.ts
│   │   └── api.ts
│   ├── utils/                 # 工具函数
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   └── styles/                # 样式文件
│       ├── globals.css
│       └── components.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.example
```

## 功能模块设计

### 1. 用户认证系统

**页面组件**:
- `pages/Auth/Login.tsx` - 登录页面
- `pages/Auth/Register.tsx` - 注册页面
- `pages/Auth/ForgotPassword.tsx` - 忘记密码
- `pages/Auth/ResetPassword.tsx` - 重置密码

**功能特性**:
- 支持邮箱/用户名登录
- 游客体验模式（只读访问）
- 密码强度验证
- 登录失败限制
- JWT Token管理
- 自动刷新Token

### 2. 仪表盘 (Dashboard)

**页面组件**:
- `pages/Dashboard/index.tsx` - 主仪表盘

**功能特性**:
- 系统概览数据展示
- WPS/PQR/pPQR统计图表
- 会员使用情况展示
- 最近活动记录
- 快速操作入口
- 会员等级状态显示

### 3. WPS管理 (Welding Procedure Specification)

**页面组件**:
- `pages/WPS/WPSList.tsx` - WPS列表
- `pages/WPS/WPSDetail.tsx` - WPS详情
- `pages/WPS/WPSCreate.tsx` - 创建WPS
- `pages/WPS/WPSEdit.tsx` - 编辑WPS
- `pages/WPS/WPSTemplate.tsx` - WPS模板

**功能特性**:
- WPS记录的增删改查
- 版本控制管理
- 状态管理（草稿、审核、批准、归档）
- 搜索和筛选功能
- 批量操作
- 导出功能（PDF/Excel）
- 权限控制（基于会员等级）

### 4. PQR管理 (Procedure Qualification Record)

**页面组件**:
- `pages/PQR/PQRList.tsx` - PQR列表
- `pages/PQR/PQRDetail.tsx` - PQR详情
- `pages/PQR/PQRCreate.tsx` - 创建PQR
- `pages/PQR/PQREdit.tsx` - 编辑PQR

**功能特性**:
- PQR记录管理
- 评定结果记录
- 测试数据管理
- 合规性检查
- 与WPS关联管理

### 5. pPQR管理 (preliminary Procedure Qualification Record)

**页面组件**:
- `pages/pPQR/pPQRList.tsx` - pPQR列表
- `pages/pPQR/pPQRDetail.tsx` - pPQR详情
- `pages/pPQR/pPQRCreate.tsx` - 创建pPQR
- `pages/pPQR/pPQREdit.tsx` - 编辑pPQR

**功能特性**:
- 预备工艺评定管理
- 评审流程管理
- 状态跟踪（草稿、审核中、批准、拒绝）

### 6. 焊材管理 (Welding Material Management)

**页面组件**:
- `pages/Materials/MaterialList.tsx` - 焊材列表
- `pages/Materials/MaterialDetail.tsx` - 焊材详情
- `pages/Materials/MaterialCreate.tsx` - 添加焊材
- `pages/Materials/MaterialEdit.tsx` - 编辑焊材
- `pages/Materials/MaterialCalculator.tsx` - 焊材计算

**功能特性**:
- 焊材库存管理
- 使用追踪
- 供应商管理
- 焊材用量计算
- 成本核算
- 消耗预测

### 7. 焊工管理 (Welder Management)

**页面组件**:
- `pages/Welders/WelderList.tsx` - 焊工列表
- `pages/Welders/WelderDetail.tsx` - 焊工详情
- `pages/Welders/WelderCreate.tsx` - 添加焊工
- `pages/Welders/WelderEdit.tsx` - 编辑焊工

**功能特性**:
- 焊工资质管理
- 技能等级维护
- 培训记录管理
- 证书到期提醒

### 8. 设备管理 (Equipment Management)

**页面组件**:
- `pages/Equipment/EquipmentList.tsx` - 设备列表
- `pages/Equipment/EquipmentDetail.tsx` - 设备详情
- `pages/Equipment/EquipmentCreate.tsx` - 添加设备
- `pages/Equipment/EquipmentEdit.tsx` - 编辑设备
- `pages/Equipment/EquipmentMaintenance.tsx` - 维护记录

**功能特性**:
- 设备维护管理
- 使用记录
- 维修保养计划
- 设备状态监控

### 9. 生产管理 (Production Management)

**页面组件**:
- `pages/Production/TaskList.tsx` - 生产任务列表
- `pages/Production/TaskDetail.tsx` - 任务详情
- `pages/Production/TaskCreate.tsx` - 创建任务
- `pages/Production/Workflow.tsx` - 生产流程

**功能特性**:
- 生产任务管理
- 流程控制
- 进度跟踪
- 任务分配

### 10. 质量管理 (Quality Management)

**页面组件**:
- `pages/Quality/InspectionList.tsx` - 检验列表
- `pages/Quality/InspectionDetail.tsx` - 检验详情
- `pages/Quality/InspectionCreate.tsx` - 创建检验
- `pages/Quality/DefectManagement.tsx` - 缺陷管理

**功能特性**:
- 质量控制管理
- 检验记录维护
- 不合格品处理
- 质量统计分析

### 11. 报表统计 (Report & Statistics)

**页面组件**:
- `pages/Reports/Dashboard.tsx` - 报表仪表盘
- `pages/Reports/WPSReport.tsx` - WPS统计报表
- `pages/Reports/PQRReport.tsx` - PQR统计报表
- `pages/Reports/UsageReport.tsx` - 使用情况报表
- `pages/Reports/MaterialReport.tsx` - 焊材消耗报表

**功能特性**:
- 数据分析报表
- 统计图表展示
- 导出功能
- 自定义报表

### 12. 企业员工管理 (Enterprise Employee Management)

**页面组件**:
- `pages/Employees/EmployeeList.tsx` - 员工列表
- `pages/Employees/EmployeeInvite.tsx` - 邀请员工
- `pages/Employees/EmployeePermission.tsx` - 权限设置
- `pages/Employees/FactoryManagement.tsx` - 工厂管理

**功能特性**:
- 员工邀请管理
- 权限设置
- 工厂组织架构
- 员工账号管理

### 13. 个人中心 (Personal Center)

**页面组件**:
- `pages/Profile/ProfileInfo.tsx` - 个人信息
- `pages/Profile/SystemSettings.tsx` - 系统设置
- `pages/Profile/SecuritySettings.tsx` - 安全设置
- `pages/Profile/NotificationSettings.tsx` - 通知设置

**功能特性**:
- 用户个人信息管理
- 系统设置配置
- 权限查看
- 密码修改
- 通知偏好设置

### 14. 会员升级 (Membership Upgrade)

**页面组件**:
- `pages/Membership/CurrentPlan.tsx` - 当前套餐
- `pages/Membership/UpgradePlans.tsx` - 升级套餐
- `pages/Membership/Payment.tsx` - 支付页面
- `pages/Membership/SubscriptionHistory.tsx` - 订阅历史

**功能特性**:
- 会员等级展示
- 套餐对比
- 在线升级
- 支付集成
- 订阅历史

## UI/UX设计原则

### 1. 设计风格
- **现代化、专业化的工业风格**
- **清晰的视觉层次**
- **一致的设计语言**
- **响应式设计**

### 2. 色彩方案
- **主色调**: #1890ff (Ant Design 蓝色)
- **辅助色**: #52c41a (成功绿), #faad14 (警告橙), #f5222d (错误红)
- **中性色**: #000000, #262626, #595959, #8c8c8c, #bfbfbf, #f0f0f0, #ffffff

### 3. 布局结构
- **顶部导航栏**: Logo、主导航菜单、用户信息
- **侧边栏**: 功能模块导航（可折叠）
- **主内容区**: 页面内容
- **底部**: 版权信息、链接

### 4. 交互设计
- **加载状态**: 骨架屏、进度条、加载动画
- **错误处理**: 友好的错误提示、重试机制
- **操作反馈**: 成功/失败提示、确认对话框
- **数据展示**: 表格、卡片、图表等多种形式

## 会员权限控制

### 1. 游客体验模式（免费）
- 只读查看WPS和PQR（仅示例数据）
- 无创建、修改、删除权限
- 无数据保存功能

### 2. 个人免费版
- WPS、PQR增删改查（最多10个）
- 无pPQR功能
- 基础存储空间

### 3. 个人专业版（¥19/月）
- 完整WPS、PQR、pPQR功能（最多30个）
- 基础焊材、焊工管理
- 设备管理

### 4. 个人高级版（¥49/月）
- 更多配额（最多50个）
- 生产管理、设备管理、质量管理

### 5. 个人旗舰版（¥99/月）
- 完整个人功能（最多100个）
- 报表统计功能

### 6. 企业版
- 包含个人旗舰版所有功能
- 企业员工管理
- 多工厂支持
- 数据隔离

## 响应式设计

### 1. 断点设置
- **xs**: < 576px (手机)
- **sm**: ≥ 576px (大手机)
- **md**: ≥ 768px (平板)
- **lg**: ≥ 992px (桌面)
- **xl**: ≥ 1200px (大桌面)
- **xxl**: ≥ 1600px (超大桌面)

### 2. 适配策略
- **移动端**: 隐藏侧边栏，使用底部导航
- **平板端**: 可折叠侧边栏
- **桌面端**: 完整布局展示

## 性能优化

### 1. 代码分割
- 路由级别的代码分割
- 组件懒加载
- 第三方库按需加载

### 2. 数据优化
- 虚拟滚动（大列表）
- 分页加载
- 缓存策略
- 防抖搜索

### 3. 资源优化
- 图片压缩和懒加载
- 静态资源CDN
- Gzip压缩

## 开发阶段规划

### 第一阶段 - 核心功能（立即开发）
1. 项目基础架构搭建
2. 用户认证系统
3. 会员体系基础功能
4. 仪表盘
5. WPS管理
6. PQR管理
7. pPQR管理
8. 个人中心

### 第二阶段 - 扩展功能（优先开发）
9. 焊工管理
10. 焊材管理
11. 设备管理
12. 企业员工管理

### 第三阶段 - 增强功能（后续开发）
13. 生产管理
14. 质量管理
15. 报表统计

### 第四阶段 - 优化完善（最后开发）
16. 响应式优化
17. 性能优化
18. 用户体验优化
19. 错误处理完善

## 技术实现要点

### 1. 状态管理
- 使用Zustand管理客户端状态
- React Query管理服务端状态
- 本地存储管理用户偏好

### 2. 路由管理
- React Router 6配置
- 路由守卫（权限控制）
- 懒加载路由

### 3. API集成
- Axios实例配置
- 请求/响应拦截器
- 错误处理机制
- 自动重试机制

### 4. 表单处理
- Ant Design Form组件
- 表单验证
- 动态表单
- 表单数据持久化

### 5. 数据展示
- Ant Design Table组件
- 自定义表格组件
- 图表组件（Recharts）
- 数据可视化

## 测试策略

### 1. 单元测试
- 组件测试
- Hook测试
- 工具函数测试

### 2. 集成测试
- API集成测试
- 路由测试
- 状态管理测试

### 3. 端到端测试
- 用户流程测试
- 关键功能测试

## 部署配置

### 1. 构建配置
- Vite生产构建
- 环境变量配置
- 资源优化

### 2. 部署方案
- 静态文件部署
- CDN配置
- 缓存策略

---

*文档创建时间: 2025-10-16*
*版本: 1.0*
*维护者: 开发团队*