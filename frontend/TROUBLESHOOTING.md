# 焊序用户门户前端 - 故障排除指南

## 常见问题及解决方案

### 1. TypeScript类型错误

**问题描述:**
- 找不到模块"react"或其相应的类型声明
- 找不到模块"antd"或其相应的类型声明
- 找不到模块"react-router-dom"或其相应的类型声明

**解决方案:**
1. 确保已安装所有依赖：
   ```bash
   npm install
   ```

2. 如果安装后仍有问题，尝试清除缓存并重新安装：
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

3. 确保TypeScript配置正确：
   ```bash
   npm run type-check
   ```

### 2. Vite开发服务器启动失败

**问题描述:**
- 端口被占用
- 找不到模块"vite"或其相应的类型声明

**解决方案:**
1. 检查端口是否被占用：
   ```bash
   netstat -tulpn | grep :3000
   ```

2. 更改端口：
   ```bash
   npm run dev -- --port 3001
   ```

3. 确保已安装Vite：
   ```bash
   npm install vite @vitejs/plugin-react --save-dev
   ```

### 3. 路径别名问题

**问题描述:**
- 找不到模块"@/components/Layout"或其相应的类型声明

**解决方案:**
1. 确保vite.config.ts中正确配置了路径别名：
   ```ts
   import { defineConfig } from 'vite'
   import path from 'path'
   
   export default defineConfig({
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       },
     },
   })
   ```

2. 确保tsconfig.json中也配置了路径映射：
   ```json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "paths": {
         "@/*": ["src/*"]
       }
     }
   }
   ```

### 4. Ant Design样式问题

**问题描述:**
- Ant Design组件样式不正确
- 图标不显示

**解决方案:**
1. 确保已正确导入Ant Design样式：
   ```tsx
   import 'antd/dist/reset.css'
   ```

2. 确保已安装图标包：
   ```bash
   npm install @ant-design/icons
   ```

### 5. React Query问题

**问题描述:**
- React Query无法正常工作
- 查询状态不更新

**解决方案:**
1. 确保已正确设置QueryClient：
   ```tsx
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
   
   const queryClient = new QueryClient()
   
   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         {/* 你的应用 */}
       </QueryClientProvider>
     )
   }
   ```

### 6. Zustand状态管理问题

**问题描述:**
- 状态更新不生效
- 无法访问状态

**解决方案:**
1. 确保已正确导入和使用store：
   ```tsx
   import { useAuthStore } from '@/store/authStore'
   
   function Component() {
     const { user, login } = useAuthStore()
     // 使用状态
   }
   ```

### 7. 表单验证问题

**问题描述:**
- Ant Design表单验证不工作
- 表单提交失败

**解决方案:**
1. 确保已正确设置表单实例：
   ```tsx
   import { Form } from 'antd'
   
   function Component() {
     const [form] = Form.useForm()
     
     const handleSubmit = async (values) => {
       // 处理表单提交
     }
     
     return (
       <Form form={form} onFinish={handleSubmit}>
         {/* 表单项 */}
       </Form>
     )
   }
   ```

### 8. 路由问题

**问题描述:**
- 页面导航不工作
- 路由参数获取失败

**解决方案:**
1. 确保已正确设置路由：
   ```tsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom'
   
   function App() {
     return (
       <BrowserRouter>
         <Routes>
           <Route path="/" element={<Home />} />
           <Route path="/about" element={<About />} />
         </Routes>
       </BrowserRouter>
     )
   }
   ```

2. 确保已正确获取路由参数：
   ```tsx
   import { useParams } from 'react-router-dom'
   
   function Component() {
     const { id } = useParams()
     // 使用参数
   }
   ```

## 开发环境问题

### 1. Node.js版本不兼容

**问题描述:**
- Node.js版本过低
- npm命令不可用

**解决方案:**
1. 确保Node.js版本 >= 16.0.0：
   ```bash
   node --version
   ```

2. 如果版本过低，请升级Node.js或使用nvm：
   ```bash
   nvm install 18
   nvm use 18
   ```

### 2. npm安装失败

**问题描述:**
- npm install失败
- 网络连接问题

**解决方案:**
1. 尝试使用国内镜像：
   ```bash
   npm config set registry https://registry.npmmirror.com
   ```

2. 使用yarn替代npm：
   ```bash
   npm install -g yarn
   yarn install
   ```

## 生产环境问题

### 1. 构建失败

**问题描述:**
- npm run build失败
- TypeScript编译错误

**解决方案:**
1. 检查TypeScript错误：
   ```bash
   npm run type-check
   ```

2. 修复所有类型错误后重新构建：
   ```bash
   npm run build
   ```

### 2. 部署后页面空白

**问题描述:**
- 部署后页面空白
- 控制台报错

**解决方案:**
1. 检查构建输出：
   ```bash
   npm run build
   npm run preview
   ```

2. 确保服务器配置正确，支持SPA路由。

## 获取帮助

如果以上解决方案无法解决您的问题，请尝试以下步骤：

1. 查看控制台错误信息
2. 检查网络请求是否正常
3. 确认所有依赖已正确安装
4. 尝试在新的环境中重新安装项目

如需更多帮助，请联系开发团队。

---

*文档更新时间: 2025-10-16*
*版本: 1.0*