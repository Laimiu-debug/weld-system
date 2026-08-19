# 焊序 - 管理员门户

这是焊序的管理员门户前端应用，用于系统管理员进行用户管理、系统监控、数据统计等管理操作。

## 功能特性

- 🔐 **安全认证**: 管理员身份验证和权限控制
- 👥 **用户管理**: 用户信息管理、会员等级调整、账号状态控制
- 🏢 **企业管理**: 企业认证、员工管理、组织架构管理
- 💳 **订阅管理**: 订阅状态监控、财务管理、退款处理
- 📊 **数据统计**: 用户增长、收入统计、使用分析
- 🖥️ **系统监控**: 系统状态、性能监控、日志查看
- 📢 **公告管理**: 系统公告发布、内容管理
- ⚙️ **系统配置**: 系统参数设置、功能开关控制
- 🛡️ **安全管理**: 权限管理、安全日志、IP白名单

## 技术栈

- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI组件库
- **React Query** - 数据状态管理
- **React Router** - 路由管理
- **Axios** - HTTP客户端
- **Recharts** - 图表组件

## 开始使用

### 环境要求

- Node.js >= 16.0.0
- npm >= 7.0.0

### 安装依赖

```bash
npm install
```

### 环境配置

复制环境变量示例文件：

```bash
cp .env.example .env
```

根据实际情况修改 `.env` 文件中的配置：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=焊序 - 管理员门户
VITE_APP_VERSION=1.0.0
```

### 开发运行

```bash
npm run dev
```

应用将在 `http://localhost:3001` 启动。

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
admin-portal/
├── src/
│   ├── components/          # 公共组件
│   ├── pages/              # 页面组件
│   ├── services/           # API服务
│   ├── hooks/              # 自定义钩子
│   ├── types/              # TypeScript类型定义
│   ├── utils/              # 工具函数
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   └── index.css           # 全局样式
├── public/                 # 静态资源
├── package.json            # 项目配置
├── tsconfig.json           # TypeScript配置
├── vite.config.ts          # Vite配置
└── README.md               # 项目文档
```

## 开发指南

### 添加新页面

1. 在 `src/pages/` 目录下创建页面组件
2. 在 `src/App.tsx` 中添加路由配置
3. 在 `src/components/Layout.tsx` 中添加菜单项

### 添加新API

1. 在 `src/types/` 中定义相关类型
2. 在 `src/services/api.ts` 中添加API方法
3. 在页面组件中使用 `useQuery` 或 `useMutation` 调用API

### 权限控制

使用 `useAuth` 钩子进行权限检查：

```tsx
const { checkPermission } = useAuth();

if (!checkPermission('user_management')) {
  return <div>权限不足</div>;
}
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t welding-admin-portal .

# 运行容器
docker run -p 3001:80 welding-admin-portal
```

### 传统部署

1. 构建项目：`npm run build`
2. 将 `dist` 目录部署到Web服务器
3. 配置反向代理指向API服务器

## 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 支持

如有问题或建议，请提交 Issue 或联系开发团队。