# 焊序用户门户前端 - 安装指南

## 系统要求

- Node.js 16.0 或更高版本
- npm 7.0 或更高版本

## 安装步骤

### 1. 进入项目目录

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

如果安装过程中遇到问题，可以尝试使用以下命令：

```bash
npm install --legacy-peer-deps
```

### 3. 启动开发服务器

```bash
npm run dev
```

## 常见问题及解决方案

### 问题1: npm install 失败

**解决方案:**
1. 清除npm缓存：
   ```bash
   npm cache clean --force
   ```
2. 删除node_modules和package-lock.json：
   ```bash
   rm -rf node_modules package-lock.json
   ```
3. 重新安装依赖：
   ```bash
   npm install
   ```

### 问题2: TypeScript类型错误

**解决方案:**
1. 确保已安装所有依赖：
   ```bash
   npm install
   ```
2. 重新生成类型定义：
   ```bash
   npm run type-check
   ```

### 问题3: Vite开发服务器启动失败

**解决方案:**
1. 检查端口是否被占用：
   ```bash
   netstat -tulpn | grep :3000
   ```
2. 更改端口：
   ```bash
   npm run dev -- --port 3001
   ```

## 开发环境配置

### 环境变量

复制 `.env.example` 到 `.env` 并配置相应的环境变量：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=焊序
VITE_ENABLE_MOCK_DATA=true
```

## 构建生产版本

```bash
npm run build
```

## 代码检查

```bash
npm run lint
npm run type-check
```

## 项目结构

```
frontend/
├── public/                     # 静态资源
├── src/                        # 源代码
│   ├── components/             # 通用组件
│   ├── pages/                 # 页面组件
│   ├── services/              # API服务
│   ├── store/                 # 状态管理
│   ├── types/                 # TypeScript类型
│   ├── styles/                # 样式文件
│   ├── App.tsx                # 根组件
│   └── main.tsx               # 应用入口
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 技术栈

- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全的JavaScript
- **Vite** - 快速构建工具
- **Ant Design 5.0+** - 企业级UI组件库
- **React Query** - 服务端状态管理
- **Zustand** - 轻量级客户端状态管理
- **React Router 6** - 单页应用路由管理

## 开发指南

### 代码规范

项目使用ESLint和Prettier进行代码规范检查：

```bash
npm run lint
npm run format
```

### 组件开发

1. 使用函数式组件和React Hooks
2. 遵循TypeScript严格模式
3. 使用Ant Design组件库
4. 遵循模块化和组件化开发原则

### 状态管理

1. 使用Zustand进行客户端状态管理
2. 使用React Query进行服务端状态管理
3. 保持状态结构扁平化

### 样式

1. 使用Ant Design的主题系统
2. 遵循响应式设计原则
3. 使用CSS Modules或Tailwind CSS

## 联系方式

如有问题或建议，请联系开发团队。

---

*文档更新时间: 2025-10-16*
*版本: 1.0*