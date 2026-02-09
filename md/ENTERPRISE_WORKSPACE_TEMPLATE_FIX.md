# 企业工作区模板创建修复

## 问题描述

用户在企业工作区创建的模板没有显示在模板列表中，无论是在个人工作区还是企业工作区都看不到。

## 根本原因

前端在创建模板时，`workspace_type` 字段被硬编码为 `'personal'`，导致所有模板都被创建为个人工作区的模板。

**问题代码位置**：`frontend/src/components/WPS/TemplateBuilder.tsx` 第 339 行

```typescript
workspace_type: values.workspace_type || 'personal',  // ❌ 总是默认为 'personal'
```

## 修复方案

### 修改文件：`frontend/src/components/WPS/TemplateBuilder.tsx`

在 `handleSave` 函数中，根据当前工作区信息动态设置 `workspace_type`：

```typescript
const handleSave = async () => {
  try {
    const values = await form.validateFields()

    if (modules.length === 0) {
      message.error('请至少添加一个模块')
      return
    }

    // 获取当前工作区信息，确定 workspace_type
    const currentWorkspaceStr = localStorage.getItem('current_workspace')
    let workspaceType = 'personal'
    
    if (currentWorkspaceStr) {
      try {
        const currentWorkspace = JSON.parse(currentWorkspaceStr)
        // 根据工作区 ID 格式判断工作区类型
        if (currentWorkspace.id && currentWorkspace.id.startsWith('enterprise_')) {
          workspaceType = 'enterprise'
        }
      } catch (e) {
        console.warn('解析工作区信息失败，使用默认值 personal')
      }
    }

    const template = {
      name: values.name,
      description: values.description,
      welding_process: values.welding_process,
      standard: values.standard,
      workspace_type: workspaceType,  // ✅ 动态设置
      module_instances: modules
    }

    setLoading(true)
    console.log('提交模板数据:', template)
    console.log('工作区类型:', workspaceType)
    await onSave(template)
    // ...
  }
}
```

## 工作流程

### 前端流程

1. 用户在企业工作区创建模板
2. `current_workspace` 保存在 localStorage，格式为 `enterprise_{company_id}`
3. 前端 API 拦截器自动添加 `X-Workspace-ID` 头部
4. `TemplateBuilder` 组件读取 localStorage 中的工作区信息
5. 根据工作区 ID 格式判断工作区类型：
   - 如果 ID 以 `enterprise_` 开头 → `workspace_type = 'enterprise'`
   - 否则 → `workspace_type = 'personal'`
6. 将 `workspace_type` 包含在模板数据中发送到后端

### 后端流程

1. 后端接收创建模板请求
2. 从 `X-Workspace-ID` 头部解析工作区上下文
3. 使用工作区上下文中的 `workspace_type` 创建模板
4. 模板被创建为企业工作区的模板

## 验证步骤

### 1. 检查前端工作区信息

打开浏览器开发者工具（F12），在控制台执行：

```javascript
// 检查当前工作区
const workspace = localStorage.getItem('current_workspace')
console.log('当前工作区:', workspace)

// 应该输出类似：
// {"id":"enterprise_4","type":"enterprise","name":"...","company_id":4,...}
```

### 2. 创建模板

1. 确保在企业工作区（工作区切换器显示企业工作区）
2. 打开 WPS 模板管理页面
3. 点击"创建模板"按钮
4. 填写模板信息并添加模块
5. 点击"保存模板"按钮

### 3. 检查浏览器控制台

应该看到类似的日志：

```
提交模板数据: {name: '2345', ..., workspace_type: 'enterprise', ...}
工作区类型: enterprise
模板创建响应: {success: true, data: {...}, timestamp: '...'}
```

### 4. 检查后端日志

后端应该输出：

```
========== 创建模板请求 ==========
当前用户: 21 (testuser176070001)
用户会员类型: enterprise
X-Workspace-ID header: enterprise_4
创建模板请求数据: ...
工作区上下文:
  - workspace_type: enterprise
  - user_id: 21
  - company_id: 4
  - factory_id: 5
模板创建成功:
  - ID: aws_d1_1_111_u0021_251023
  - 名称: 2345
  - workspace_type: enterprise
  - template_source: enterprise
========== 创建模板完成 ==========
```

### 5. 验证模板显示

1. 刷新模板列表页面
2. 新创建的模板应该出现在列表中
3. 模板的工作区类型应该是"企业"

## 关键点

- ✅ 前端正确读取 localStorage 中的工作区信息
- ✅ 前端 API 拦截器正确发送 `X-Workspace-ID` 头部
- ✅ 后端根据 `X-Workspace-ID` 头部解析工作区上下文
- ✅ 模板被创建为正确的工作区类型
- ✅ 模板在对应工作区的列表中显示

## 相关文件

- `frontend/src/components/WPS/TemplateBuilder.tsx` - 修复的主文件
- `frontend/src/services/api.ts` - API 拦截器（已正确实现）
- `backend/app/api/v1/endpoints/wps_templates.py` - 后端创建模板端点
- `backend/app/services/wps_template_service.py` - 模板服务

