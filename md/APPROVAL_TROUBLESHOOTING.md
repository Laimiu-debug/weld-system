# PQR/pPQR 审批功能故障排查指南

## 问题描述
- CORS错误: `Access-Control-Allow-Origin` header缺失
- 500内部服务器错误

## 解决步骤

### 1. 重启后端服务器 ⭐ 最重要

代码更改后必须重启后端服务器才能生效。

```powershell
# 停止当前运行的后端服务器 (Ctrl+C)

# 进入后端目录
cd backend

# 重新启动服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 检查后端日志

启动后端后，查看终端输出，确认：
- ✓ 服务器成功启动在 `http://0.0.0.0:8000`
- ✓ CORS中间件已配置
- ✓ 数据库连接成功

### 3. 配置审批工作流

#### 方法A: 使用管理界面（推荐）

1. 登录系统
2. 进入企业工作区
3. 访问"审批管理" -> "工作流配置"
4. 为PQR和pPQR创建审批工作流

#### 方法B: 使用API

访问 `http://localhost:8000/api/v1/docs` 并使用以下端点：

**POST /api/v1/approvals/workflows**

请求体示例（PQR）:
```json
{
  "name": "PQR标准审批流程",
  "description": "PQR文档的标准审批流程",
  "document_type": "pqr",
  "steps": [
    {
      "step_name": "技术审核",
      "approver_type": "role",
      "approver_ids": [2],
      "approval_mode": "any",
      "time_limit_hours": 48
    },
    {
      "step_name": "质量审批",
      "approver_type": "role",
      "approver_ids": [3],
      "approval_mode": "any",
      "time_limit_hours": 24
    }
  ]
}
```

请求体示例（pPQR）:
```json
{
  "name": "pPQR标准审批流程",
  "description": "pPQR文档的标准审批流程",
  "document_type": "ppqr",
  "steps": [
    {
      "step_name": "技术审核",
      "approver_type": "role",
      "approver_ids": [2],
      "approval_mode": "any",
      "time_limit_hours": 48
    }
  ]
}
```

#### 方法C: 使用SQL脚本

运行 `setup_approval_workflows.sql` 文件：

```powershell
# 连接到PostgreSQL数据库
psql -U postgres -d welding_db -f setup_approval_workflows.sql
```

### 4. 验证工作流配置

使用以下API检查工作流是否创建成功：

**GET /api/v1/approvals/workflows?document_type=pqr**
**GET /api/v1/approvals/workflows?document_type=ppqr**

### 5. 检查工作区设置

确保您在企业工作区中操作（审批功能仅在企业工作区可用）：

1. 检查浏览器localStorage中的 `current_workspace`
2. 确认 `workspace_type` 为 `enterprise`
3. 确认有 `company_id`

### 6. 测试审批功能

#### 测试提交审批

1. 打开PQR列表页面
2. 点击某个PQR的"提交审批"按钮
3. 填写审批备注
4. 提交

#### 预期结果

- ✓ 提交成功，显示"提交审批成功"消息
- ✓ PQR状态变为"审批中"
- ✓ 审批按钮变为"查看审批"或"取消审批"

### 7. 常见错误及解决方案

#### 错误1: "该工作区不需要审批流程"

**原因**: 在个人工作区中尝试提交审批

**解决**: 切换到企业工作区

#### 错误2: "未找到pqr的审批工作流"

**原因**: 没有为PQR配置审批工作流

**解决**: 按照步骤3配置工作流

#### 错误3: CORS错误

**原因**: 
- 后端服务器未运行
- CORS配置不正确

**解决**:
1. 确认后端服务器正在运行
2. 检查 `backend/app/core/config.py` 中 `DEVELOPMENT = True`
3. 重启后端服务器

#### 错误4: 500内部服务器错误

**原因**: 
- 数据库连接失败
- 工作流配置错误
- 代码错误

**解决**:
1. 查看后端终端的详细错误日志
2. 检查数据库连接
3. 检查工作流配置是否正确

### 8. 调试工具

#### 使用测试脚本

运行 `test_approval_api.py` 进行诊断：

```powershell
python test_approval_api.py
```

#### 查看API文档

访问 `http://localhost:8000/api/v1/docs` 查看完整的API文档

#### 检查数据库

```sql
-- 查看审批工作流
SELECT * FROM approval_workflow_definitions WHERE document_type IN ('pqr', 'ppqr');

-- 查看审批实例
SELECT * FROM approval_instances WHERE document_type IN ('pqr', 'ppqr');

-- 查看审批历史
SELECT * FROM approval_history ORDER BY created_at DESC LIMIT 10;
```

## 快速检查清单

- [ ] 后端服务器正在运行
- [ ] 前端开发服务器正在运行
- [ ] 已登录系统
- [ ] 在企业工作区中
- [ ] 已配置PQR审批工作流
- [ ] 已配置pPQR审批工作流
- [ ] 用户有相应的角色权限
- [ ] 数据库连接正常

## 需要帮助？

如果以上步骤都无法解决问题，请：

1. 复制后端终端的完整错误日志
2. 复制浏览器控制台的错误信息
3. 提供以下信息：
   - 当前工作区类型
   - 用户角色
   - 操作步骤

