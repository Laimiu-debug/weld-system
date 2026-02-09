# 工作区修复测试指南

## 测试目的
验证企业数据共享问题的修复是否生效

## 测试前准备

### 1. 清除浏览器缓存
1. 打开浏览器开发者工具 (F12)
2. 进入 Application -> Local Storage
3. 找到并删除旧的 `currentWorkspace` key（如果存在）
4. 刷新页面

### 2. 检查 localStorage
在浏览器控制台执行:
```javascript
// 检查当前工作区信息
const workspace = localStorage.getItem('current_workspace')
console.log('当前工作区:', JSON.parse(workspace))

// 应该看到类似这样的输出:
// {
//   type: 'enterprise',
//   company_id: 1,
//   factory_id: 1,
//   name: '企业工作区',
//   ...
// }
```

## 测试步骤

### 测试1: 验证工作区信息正确读取

1. 登录企业账号
2. 切换到企业工作区
3. 打开浏览器控制台
4. 进入生产任务页面
5. 查看控制台输出，应该看到:
   ```
   === 加载工作区信息 ===
   { type: 'enterprise', company_id: 1, factory_id: 1, ... }
   ```

**预期结果**: 
- ✅ `type` 为 `'enterprise'`
- ✅ `company_id` 有值（不是 undefined）
- ✅ `factory_id` 有值（如果有工厂）

### 测试2: 验证企业任务创建

1. 在企业工作区下创建一个新的生产任务
2. 填写任务信息并提交
3. 查看浏览器 Network 标签中的请求
4. 找到 `POST /api/v1/production/tasks` 请求
5. 查看请求参数:
   ```
   workspace_type: enterprise
   company_id: 1
   factory_id: 1
   ```

**预期结果**:
- ✅ `workspace_type` 为 `'enterprise'`（不是 'personal'）
- ✅ `company_id` 有值
- ✅ 任务创建成功

### 测试3: 验证数据库中的任务数据

在后端执行:
```bash
cd backend
python check_production_tasks.py
```

查看最新创建的任务:
```
ID: X
  任务编号: TASK-20251021-XXXXXX
  任务名称: 测试任务
  工作区类型: enterprise  ✅ 应该是 enterprise
  企业ID: 1              ✅ 应该有值
  用户ID: XX
  访问级别: company       ✅ 应该是 company
```

**预期结果**:
- ✅ `workspace_type` = `'enterprise'`
- ✅ `company_id` 有值
- ✅ `access_level` = `'company'`

### 测试4: 验证企业数据共享

1. 使用企业账号A创建一个生产任务
2. 登出，使用同一企业的账号B登录
3. 进入生产任务列表页面
4. 查看是否能看到账号A创建的任务

**预期结果**:
- ✅ 账号B可以看到账号A创建的企业任务
- ✅ 任务列表中显示正确的任务信息

### 测试5: 验证设备列表过滤

1. 在企业工作区下打开生产任务创建页面
2. 点击"使用设备"下拉框
3. 查看浏览器 Network 标签中的请求
4. 找到 `GET /api/v1/equipment` 请求
5. 查看请求参数:
   ```
   workspace_type: company
   ```

**预期结果**:
- ✅ `workspace_type` 为 `'company'`（不是 'personal'）
- ✅ 下拉框中只显示企业设备
- ✅ 不显示个人设备

### 测试6: 验证个人工作区隔离

1. 切换到个人工作区
2. 创建一个新的生产任务
3. 查看数据库中的任务数据

**预期结果**:
- ✅ `workspace_type` = `'personal'`
- ✅ `company_id` = `NULL`
- ✅ `access_level` = `'private'`
- ✅ 其他用户看不到这个任务

## 常见问题排查

### 问题1: 工作区类型仍然是 'personal'

**可能原因**:
- 浏览器缓存未清除
- localStorage 中仍然使用旧的 key

**解决方法**:
1. 清除浏览器缓存
2. 删除 localStorage 中的 `currentWorkspace` key
3. 刷新页面
4. 重新切换工作区

### 问题2: company_id 为 undefined

**可能原因**:
- 前端代码未更新
- 使用了错误的字段名 `companyId` 而不是 `company_id`

**解决方法**:
1. 确认前端代码已更新
2. 检查 localStorage 中的数据格式
3. 重新构建前端项目

### 问题3: 设备列表仍然显示个人设备

**可能原因**:
- 前端传递的 `workspace_type` 参数错误
- 后端设备API未正确应用工作区过滤

**解决方法**:
1. 检查 Network 标签中的请求参数
2. 查看后端控制台的调试日志
3. 确认后端代码已更新

## 调试技巧

### 1. 查看前端控制台日志
```javascript
// 在生产任务页面，应该看到这些日志:
=== 加载工作区信息 ===
{ type: 'enterprise', company_id: 1, factory_id: 1, ... }

=== 生产任务页面 - 加载数据 ===
工作区类型: enterprise
企业ID: 1
工厂ID: 1

=== 获取设备列表 ===
localStorage工作区: { type: 'enterprise', company_id: 1, ... }
API workspace_type: company
```

### 2. 查看后端控制台日志
```
[生产任务列表] 用户ID: XX
[生产任务列表] 工作区类型: enterprise
[生产任务列表] 企业ID: 1
[生产任务列表] 工厂ID: 1

[数据隔离] 模型: ProductionTask
[数据隔离] 用户ID: XX
[数据隔离] 工作区类型: enterprise
[数据隔离] 企业ID: 1
[数据隔离] 应用企业工作区过滤
```

### 3. 使用浏览器开发者工具
1. Network 标签: 查看API请求参数
2. Application 标签: 查看 localStorage 数据
3. Console 标签: 查看前端日志

## 成功标准

所有以下条件都满足时，修复成功:

- ✅ 企业工作区下创建的任务 `workspace_type='enterprise'`
- ✅ 企业工作区下创建的任务 `company_id` 有值
- ✅ 同一企业的员工可以看到彼此创建的任务
- ✅ 设备列表正确显示企业设备
- ✅ 个人工作区和企业工作区数据完全隔离
- ✅ 前端控制台没有错误日志
- ✅ 后端控制台显示正确的工作区过滤日志

