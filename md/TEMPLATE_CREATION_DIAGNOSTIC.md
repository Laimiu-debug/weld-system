# 模板创建诊断指南

## 快速诊断

### 步骤 1：验证工作区切换

1. 打开应用
2. 点击右上角的工作区切换器
3. 选择企业工作区
4. 确认页面显示"企业工作区"或类似标识

### 步骤 2：打开浏览器控制台

按 `F12` 打开开发者工具，切换到"控制台"标签

### 步骤 3：检查工作区信息

在控制台执行以下命令：

```javascript
// 检查 localStorage 中的工作区信息
const workspace = localStorage.getItem('current_workspace')
console.log('当前工作区:', workspace)

// 解析并检查工作区 ID
if (workspace) {
  const ws = JSON.parse(workspace)
  console.log('工作区 ID:', ws.id)
  console.log('工作区类型:', ws.type)
  console.log('公司 ID:', ws.company_id)
  console.log('是否为企业工作区:', ws.id.startsWith('enterprise_'))
}
```

**预期输出**（企业工作区）：
```
当前工作区: {"id":"enterprise_4","type":"enterprise","name":"...","company_id":4,...}
工作区 ID: enterprise_4
工作区类型: enterprise
公司 ID: 4
是否为企业工作区: true
```

### 步骤 4：创建模板

1. 导航到 WPS 模板管理页面
2. 点击"创建模板"按钮
3. 填写模板信息：
   - 模板名称：`测试模板 - 企业`
   - 焊接工艺：选择一个（可选）
   - 标准：选择一个（可选）
4. 添加至少一个模块
5. 点击"保存模板"按钮

### 步骤 5：检查前端日志

在浏览器控制台中应该看到：

```
提交模板数据: {
  name: '测试模板 - 企业',
  description: undefined,
  welding_process: undefined,
  standard: undefined,
  workspace_type: 'enterprise',  // ✅ 应该是 'enterprise'
  module_instances: [...]
}
工作区类型: enterprise
模板创建响应: {success: true, data: {...}, timestamp: '...'}
```

**如果看到 `workspace_type: 'personal'`，说明修复未生效**

### 步骤 6：检查后端日志

查看后端服务器的输出，应该看到：

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
  - 名称: 测试模板 - 企业
  - workspace_type: enterprise
  - template_source: enterprise
========== 创建模板完成 ==========
```

**关键检查点**：
- ✅ `X-Workspace-ID header: enterprise_4` - 工作区 ID 正确
- ✅ `workspace_type: enterprise` - 工作区类型正确
- ✅ `company_id: 4` - 公司 ID 正确
- ✅ `template_source: enterprise` - 模板来源正确

### 步骤 7：验证模板显示

1. 刷新模板列表页面
2. 新创建的模板应该出现在列表中
3. 检查模板的工作区类型标签

## 常见问题排查

### 问题 1：工作区 ID 为 `personal_21`

**原因**：用户仍在个人工作区

**解决方案**：
1. 点击工作区切换器
2. 选择企业工作区
3. 等待页面刷新
4. 重新创建模板

### 问题 2：`X-Workspace-ID header: null`

**原因**：localStorage 中没有保存工作区信息

**解决方案**：
1. 刷新页面
2. 重新切换工作区
3. 检查浏览器是否允许 localStorage

### 问题 3：`workspace_type: 'personal'`（前端日志）

**原因**：前端代码未正确读取工作区信息

**解决方案**：
1. 清除浏览器缓存
2. 硬刷新页面（Ctrl+Shift+R）
3. 检查浏览器控制台是否有错误

### 问题 4：模板创建成功但不显示

**原因**：模板列表查询的工作区上下文与创建时不同

**解决方案**：
1. 确保仍在企业工作区
2. 刷新模板列表页面
3. 检查后端日志中的 `template_source` 是否为 `enterprise`

## 数据库验证

如果需要直接查询数据库验证：

```sql
-- 查看用户创建的所有模板
SELECT id, name, workspace_type, company_id, template_source, is_active, created_at
FROM wps_templates
WHERE user_id = 21
ORDER BY created_at DESC;

-- 查看企业工作区的模板
SELECT id, name, workspace_type, company_id, template_source, is_active, created_at
FROM wps_templates
WHERE workspace_type = 'enterprise' AND company_id = 4
ORDER BY created_at DESC;

-- 查看模板来源分布
SELECT template_source, COUNT(*) as count
FROM wps_templates
WHERE user_id = 21
GROUP BY template_source;
```

## 修复验证清单

- [ ] 工作区切换器显示企业工作区
- [ ] localStorage 中的工作区 ID 以 `enterprise_` 开头
- [ ] 前端日志显示 `workspace_type: 'enterprise'`
- [ ] 后端日志显示 `X-Workspace-ID header: enterprise_4`
- [ ] 后端日志显示 `workspace_type: enterprise`
- [ ] 后端日志显示 `template_source: enterprise`
- [ ] 模板出现在模板列表中
- [ ] 模板的工作区类型标签正确

## 需要帮助？

如果问题仍未解决，请提供以下信息：

1. 浏览器控制台的完整日志
2. 后端服务器的完整日志
3. 当前工作区信息（`localStorage.getItem('current_workspace')`）
4. 用户 ID 和公司 ID

