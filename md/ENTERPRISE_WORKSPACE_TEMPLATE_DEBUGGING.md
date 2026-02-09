# 企业工作区模板创建调试指南

## 问题描述

用户在企业工作区创建的模板没有显示在模板列表中。

## 工作区 ID 格式

- **个人工作区**: `personal_{user_id}`
- **企业工作区**: `enterprise_{company_id}`

## 调试步骤

### 1. 检查前端工作区信息

打开浏览器开发者工具（F12），在控制台执行：

```javascript
// 检查当前工作区
const workspace = localStorage.getItem('current_workspace')
console.log('当前工作区:', workspace)

// 应该输出类似：
// {"id":"enterprise_1","type":"enterprise","name":"公司名称",...}
```

**预期结果**：
- 如果在企业工作区，`id` 应该是 `enterprise_{company_id}` 格式
- 如果在个人工作区，`id` 应该是 `personal_{user_id}` 格式

### 2. 检查后端日志

创建模板时，查看后端服务器的日志输出。应该看到类似：

```
========== 创建模板请求 ==========
当前用户: 21 (testuser176070001)
用户会员类型: enterprise
X-Workspace-ID header: enterprise_1
创建模板请求数据: ...
工作区上下文:
  - workspace_type: enterprise
  - user_id: 21
  - company_id: 1
  - factory_id: None
模板创建成功:
  - ID: aws_d1_1_111_u0021_251023
  - 名称: 测试模板
  - workspace_type: enterprise
  - template_source: enterprise
========== 创建模板完成 ==========
```

### 3. 关键检查点

#### 3.1 X-Workspace-ID Header

- ✅ 应该包含 `enterprise_{company_id}` 或 `personal_{user_id}`
- ❌ 如果为空或 undefined，说明 `current_workspace` 没有被正确保存

#### 3.2 工作区上下文

- ✅ 企业工作区应该有 `company_id` 和 `workspace_type: enterprise`
- ❌ 如果 `company_id` 为 None，说明用户不是该企业的成员

#### 3.3 模板创建结果

- ✅ `template_source` 应该是 `enterprise`（企业工作区）或 `user`（个人工作区）
- ❌ 如果是 `system`，说明工作区上下文识别错误

### 4. 常见问题

#### 问题 1：X-Workspace-ID 为空

**原因**：`current_workspace` 没有被保存到 localStorage

**解决方案**：
1. 检查工作区切换是否成功
2. 在浏览器控制台执行：
   ```javascript
   // 手动保存工作区
   const workspace = {
     id: 'enterprise_1',  // 替换为实际的企业ID
     type: 'enterprise',
     name: '公司名称'
   }
   localStorage.setItem('current_workspace', JSON.stringify(workspace))
   ```
3. 刷新页面后重试

#### 问题 2：company_id 为 None

**原因**：用户不是该企业的成员

**解决方案**：
1. 检查用户是否已加入企业
2. 检查 `company_employees` 表中是否有该用户的记录
3. 确保员工状态是 `active`

#### 问题 3：模板创建成功但不显示

**原因**：模板列表查询的工作区上下文与创建时不同

**解决方案**：
1. 检查 `get_available_templates` 方法的过滤条件
2. 确保创建和查询时的工作区上下文一致
3. 检查模板的 `is_active` 字段是否为 True

### 5. 数据库查询

如果需要直接查询数据库验证：

```sql
-- 查看用户创建的所有模板
SELECT id, name, workspace_type, company_id, template_source, is_active
FROM wps_templates
WHERE user_id = 21
ORDER BY created_at DESC;

-- 查看企业工作区的模板
SELECT id, name, workspace_type, company_id, template_source, is_active
FROM wps_templates
WHERE workspace_type = 'enterprise' AND company_id = 1
ORDER BY created_at DESC;

-- 查看用户是否是企业成员
SELECT user_id, company_id, status, role
FROM company_employees
WHERE user_id = 21;
```

## 修复步骤

1. **确认工作区切换成功**
   - 在工作区切换器中选择企业工作区
   - 检查页面标题或工作区指示器是否更新

2. **检查 localStorage**
   - 打开开发者工具
   - 检查 `current_workspace` 是否包含正确的企业 ID

3. **创建模板**
   - 填写模板信息
   - 添加模块
   - 点击保存

4. **验证结果**
   - 检查后端日志中的工作区上下文
   - 检查模板是否出现在列表中
   - 如果没有，查看数据库中是否创建了模板

## 相关代码位置

- **前端工作区管理**: `frontend/src/services/workspace.ts`
- **前端 API 拦截器**: `frontend/src/services/api.ts` (第 30-41 行)
- **后端工作区上下文**: `backend/app/api/v1/endpoints/wps_templates.py` (第 25-67 行)
- **后端模板创建**: `backend/app/services/wps_template_service.py` (第 152-211 行)
- **后端模板查询**: `backend/app/services/wps_template_service.py` (第 26-113 行)

