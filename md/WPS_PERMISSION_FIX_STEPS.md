# WPS权限问题修复步骤

## 问题现象

```
GET http://localhost:8000/api/v1/wps/?skip=0&limit=20 403 (Forbidden)
```

用户 `testuser176070001@example.com` 访问WPS列表时收到403权限错误。

## 问题分析

### ✅ 后端检查结果

用户信息：
- **用户ID**: 21
- **Email**: testuser176070001@example.com
- **会员类型**: enterprise（企业会员）
- **会员等级**: enterprise
- **是否激活**: True
- **企业ID**: 4
- **角色**: admin
- **状态**: active

可用工作区：
1. **个人工作区**: `personal_21`
2. **企业工作区**: `enterprise_4`（默认）

### ✅ 权限逻辑检查

后端代码（`backend/app/api/v1/endpoints/wps.py` 第94-103行）：

```python
# Check permission (enterprise members have access by default)
if current_user.membership_type != "enterprise":
    print(f"DEBUG WPS: Non-enterprise user, checking permissions")
    if not user_service.has_permission(db, current_user.id, "wps", "read"):
        print(f"DEBUG WPS: Permission denied for non-enterprise user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限"
        )
else:
    print(f"DEBUG WPS: Enterprise user, permission granted")
```

**结论**：企业会员应该自动拥有WPS访问权限。

### ❌ 前端问题

前端代码已经修改（添加了`X-Workspace-ID` header），但**浏览器可能还在使用缓存的旧代码**。

## 修复步骤

### 步骤1：清除浏览器缓存并重新加载

1. **打开浏览器开发者工具**（F12）
2. **右键点击刷新按钮** → 选择"清空缓存并硬性重新加载"
   - 或按 `Ctrl+Shift+R`（Windows）/ `Cmd+Shift+R`（Mac）
3. **清除localStorage**（可选，如果上面不行）：
   ```javascript
   // 在浏览器控制台执行
   localStorage.clear()
   location.reload()
   ```

### 步骤2：检查工作区信息

访问：`http://localhost:5173/check_workspace.html`

**预期结果**：
```json
{
  "id": "enterprise_4",
  "type": "enterprise",
  "name": "testuser176070001's Company",
  "company_id": 4,
  "factory_id": 5,
  ...
}
```

**如果显示"未设置"**：
1. 刷新主页面
2. 重新登录
3. 等待Layout组件加载工作区信息

### 步骤3：检查API请求

1. **打开开发者工具** → **Network标签**
2. **访问WPS列表页面**
3. **查看请求详情**

**预期请求头**：
```
GET /api/v1/wps/?skip=0&limit=20
Authorization: Bearer <token>
X-Workspace-ID: enterprise_4
```

**如果没有`X-Workspace-ID` header**：
- 前端代码没有正确加载
- 需要重启前端开发服务器

### 步骤4：重启前端开发服务器（如果需要）

```bash
# 停止当前服务器（Ctrl+C）
# 然后重新启动
cd frontend
npm run dev
```

### 步骤5：查看后端日志

后端应该输出类似的调试信息：

```
DEBUG WPS: User 21, membership_type=enterprise, workspace_id=enterprise_4
DEBUG WPS: Enterprise user, permission granted
```

**如果看到**：
```
DEBUG WPS: Non-enterprise user, checking permissions
DEBUG WPS: Permission denied for non-enterprise user
```

说明用户的`membership_type`不是"enterprise"，需要检查数据库。

## 常见问题排查

### 问题1：仍然403错误

**可能原因**：
1. 前端代码没有正确加载
2. localStorage中没有工作区信息
3. Token过期

**解决方案**：
```javascript
// 在浏览器控制台检查
console.log('Token:', localStorage.getItem('token'))
console.log('User:', JSON.parse(localStorage.getItem('user')))
console.log('Workspace:', JSON.parse(localStorage.getItem('current_workspace')))
```

如果任何一个为null，重新登录。

### 问题2：工作区信息为null

**解决方案**：

1. **手动设置工作区**（临时方案）：
```javascript
// 在浏览器控制台执行
const workspace = {
  id: "enterprise_4",
  type: "enterprise",
  name: "testuser176070001's Company",
  company_id: 4,
  factory_id: 5,
  user_id: 21,
  is_default: false,
  role: "admin"
}
localStorage.setItem('current_workspace', JSON.stringify(workspace))
location.reload()
```

2. **从服务器获取工作区**：
```javascript
// 在浏览器控制台执行
const token = localStorage.getItem('token')
fetch('/api/v1/workspace/workspaces/default', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('默认工作区:', data)
  localStorage.setItem('current_workspace', JSON.stringify(data))
  location.reload()
})
```

### 问题3：vite.svg 404错误

这是一个无关的错误，不影响功能。可以忽略或修复：

**修复方案**：
1. 检查 `frontend/public/vite.svg` 是否存在
2. 或者从HTML中移除对vite.svg的引用

## 验证成功的标志

### ✅ 工作区信息正确
- `check_workspace.html` 显示企业工作区信息
- `id` 为 `enterprise_4`
- `type` 为 `enterprise`

### ✅ API请求正确
- Network标签显示请求包含 `X-Workspace-ID: enterprise_4`
- 响应状态码为 200
- 返回WPS列表数据

### ✅ 后端日志正确
```
DEBUG WPS: User 21, membership_type=enterprise, workspace_id=enterprise_4
DEBUG WPS: Enterprise user, permission granted
```

### ✅ 功能正常
- WPS列表页面正常显示
- 可以创建新的WPS
- 可以查看WPS详情

## 代码修改总结

### 已修改文件

1. **`frontend/src/services/api.ts`**（第21-48行）
   - 添加了工作区上下文header自动注入
   - 从localStorage读取`current_workspace`
   - 在每个请求中添加`X-Workspace-ID` header

### 新增文件

1. **`frontend/check_workspace.html`**
   - 工作区信息检查工具
   - 用于诊断工作区配置问题

2. **`backend/check_user_permission.py`**
   - 用户权限检查脚本
   - 显示用户信息、企业信息、工作区信息

3. **`WPS_CREATE_PERMISSION_FIX.md`**
   - 详细的问题分析和修复文档

4. **`WPS_PERMISSION_FIX_STEPS.md`**（本文件）
   - 分步骤的修复指南

## 后续优化建议

### 1. 添加工作区初始化检查

在登录成功后立即初始化工作区，而不是依赖Layout组件的异步加载。

**修改位置**：`frontend/src/contexts/AuthContext.tsx`

```typescript
const login = async (email: string, password: string) => {
  // ... 登录逻辑 ...
  
  // 登录成功后立即获取工作区
  try {
    const workspaceResponse = await workspaceService.getDefaultWorkspace()
    if (workspaceResponse.data) {
      workspaceService.saveCurrentWorkspaceToStorage(workspaceResponse.data)
    }
  } catch (error) {
    console.error('获取默认工作区失败:', error)
  }
}
```

### 2. 添加工作区状态监控

在开发环境显示当前工作区信息，方便调试。

**新增组件**：`frontend/src/components/WorkspaceDebugInfo.tsx`

```typescript
export const WorkspaceDebugInfo = () => {
  if (import.meta.env.PROD) return null
  
  const workspace = JSON.parse(localStorage.getItem('current_workspace') || 'null')
  
  return (
    <div style={{ position: 'fixed', bottom: 0, right: 0, background: '#000', color: '#0f0', padding: '5px', fontSize: '10px' }}>
      工作区: {workspace?.id || '未设置'}
    </div>
  )
}
```

### 3. 优化错误提示

当工作区信息缺失时，提供更友好的错误提示。

**修改位置**：`frontend/src/services/api.ts`

```typescript
// 在响应拦截器中
if (error.response?.status === 403) {
  const workspace = localStorage.getItem('current_workspace')
  if (!workspace) {
    message.error('工作区信息缺失，请刷新页面或重新登录')
  } else {
    message.error('没有权限访问此资源')
  }
}
```

### 4. 添加自动化测试

测试工作区切换和权限检查功能。

**测试文件**：`frontend/src/__tests__/workspace.test.ts`

```typescript
describe('Workspace Context', () => {
  it('should add X-Workspace-ID header to requests', async () => {
    const workspace = { id: 'enterprise_4', type: 'enterprise' }
    localStorage.setItem('current_workspace', JSON.stringify(workspace))
    
    // 测试API请求是否包含正确的header
  })
})
```

## 联系支持

如果按照以上步骤仍然无法解决问题，请提供以下信息：

1. **浏览器控制台的完整错误信息**
2. **Network标签中的请求详情**（包括请求头和响应）
3. **后端日志输出**
4. **`check_workspace.html` 的显示结果**
5. **用户权限检查脚本的输出**

```bash
# 运行用户权限检查脚本
cd backend
python check_user_permission.py
```

