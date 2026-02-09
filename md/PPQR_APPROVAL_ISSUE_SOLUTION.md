# pPQR无法提交审批问题解决方案

## 问题描述

pPQR文档无法提交审批，"提交审批"按钮不显示。

## 根本原因

**数据库中没有配置pPQR的审批工作流！**

### 技术分析

1. **后端逻辑** (`backend/app/api/v1/endpoints/ppqr.py` 第167行):
   ```python
   can_submit_approval = approval_service.should_require_approval('ppqr', workspace_context)
   ```

2. **审批服务检查** (`backend/app/services/approval_service.py` 第122行):
   ```python
   workflow = self.get_workflow_for_document(document_type, workspace_context)
   return workflow is not None  # 如果没有工作流，返回False
   ```

3. **前端按钮显示** (`frontend/src/components/Approval/ApprovalButton.tsx` 第207行):
   ```tsx
   {canSubmit && (  // canSubmit为False时，按钮不显示
     <Button>提交审批</Button>
   )}
   ```

**结论**: 如果数据库中没有pPQR的审批工作流定义，`can_submit_approval`会返回`False`，导致前端不显示"提交审批"按钮。

## 解决方案

### 方案1: 使用Swagger UI创建工作流（推荐⭐）

这是最简单直接的方法：

#### 步骤：

1. **访问Swagger UI**
   ```
   http://localhost:8000/api/v1/docs
   ```

2. **登录认证**
   - 点击右上角的 🔓 **Authorize** 按钮
   - 在浏览器控制台（F12）中输入：`localStorage.getItem('token')`
   - 复制token值
   - 在弹出框中输入：`Bearer <你的token>`
   - 点击 **Authorize**

3. **创建工作流**
   - 找到 **POST /api/v1/approvals/workflows** 接口
   - 点击 **Try it out**
   - 在Request body中粘贴以下JSON：

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

   - 点击 **Execute**
   - 查看响应，应该返回200状态码

4. **验证**
   - 刷新pPQR列表页面
   - "提交审批"按钮应该出现了！

### 方案2: 使用SQL脚本

如果您有数据库访问权限：

1. **运行SQL脚本**
   ```bash
   psql -U postgres -d welding_db -f setup_approval_workflows.sql
   ```

2. **或者手动执行SQL**
   ```sql
   INSERT INTO approval_workflow_definitions (
       name,
       description,
       document_type,
       company_id,
       steps,
       is_active,
       created_at,
       updated_at
   ) VALUES (
       'pPQR标准审批流程',
       'pPQR文档的标准审批流程',
       'ppqr',
       1,  -- 修改为您的实际company_id
       '[
           {
               "step_name": "技术审核",
               "approver_type": "role",
               "approver_ids": [2],
               "approval_mode": "any",
               "time_limit_hours": 48
           }
       ]'::jsonb,
       true,
       NOW(),
       NOW()
   );
   ```

### 方案3: 使用系统管理界面

如果系统有审批工作流管理界面：

1. 登录系统
2. 切换到企业工作区
3. 进入"系统管理" -> "审批管理" -> "工作流配置"
4. 点击"新建工作流"
5. 填写以下信息：
   - 名称：pPQR标准审批流程
   - 文档类型：ppqr
   - 添加审批步骤（技术审核、质量审批等）
6. 保存

## 验证步骤

创建工作流后，按以下步骤验证：

### 1. 检查工作流是否创建成功

访问：`http://localhost:8000/api/v1/docs`

使用 **GET /api/v1/approvals/workflows** 接口，参数：
- `document_type`: ppqr

应该能看到刚创建的工作流。

### 2. 检查pPQR列表

1. 刷新pPQR列表页面
2. 查看任意一个pPQR卡片
3. 应该能看到"提交审批"按钮

### 3. 测试提交审批

1. 点击"提交审批"按钮
2. 填写备注（可选）
3. 点击确定
4. 应该显示"提交审批成功"
5. pPQR状态应该变为"审批中"

## 常见问题

### Q1: 创建工作流后，按钮还是不显示？

**检查清单：**
- ✅ 确认在企业工作区中（个人工作区不支持审批）
- ✅ 刷新页面（Ctrl+F5 强制刷新）
- ✅ 检查浏览器控制台是否有错误
- ✅ 检查后端日志

### Q2: 提示"未找到ppqr的审批工作流"？

**原因：** 工作流的`document_type`不正确或`is_active`为false

**解决：**
```sql
-- 检查工作流
SELECT * FROM approval_workflow_definitions WHERE document_type = 'ppqr';

-- 确保is_active为true
UPDATE approval_workflow_definitions 
SET is_active = true 
WHERE document_type = 'ppqr';
```

### Q3: 提示"该工作区不需要审批流程"？

**原因：** 在个人工作区中操作

**解决：** 切换到企业工作区

### Q4: 角色ID 2和3是什么？

**说明：**
- 角色ID 2 通常是"技术审核员"或"工程师"
- 角色ID 3 通常是"质量审批员"或"质量经理"

**查看系统中的角色：**
```sql
SELECT id, name FROM roles ORDER BY id;
```

根据实际情况修改`approver_ids`。

### Q5: 如何修改审批步骤？

使用 **PUT /api/v1/approvals/workflows/{workflow_id}** 接口更新工作流配置。

## 工作流配置说明

### 审批步骤参数

| 参数 | 说明 | 示例 |
|------|------|------|
| step_name | 步骤名称 | "技术审核" |
| approver_type | 审批人类型 | "role"（角色）或"user"（用户） |
| approver_ids | 审批人ID列表 | [2, 3] |
| approval_mode | 审批模式 | "any"（任意一人）或"all"（所有人） |
| time_limit_hours | 时限（小时） | 48 |

### 审批模式说明

- **any**: 任意一个审批人通过即可进入下一步
- **all**: 所有审批人都必须通过才能进入下一步

## 相关文件

- `setup_approval_workflows.sql` - SQL脚本（包含PQR和pPQR工作流）
- `create_ppqr_workflow.py` - Python脚本（使用API创建）
- `check_ppqr_workflow.sql` - 检查工作流的SQL脚本

## 总结

pPQR无法提交审批的根本原因是**缺少审批工作流配置**。

**最快的解决方法：**
1. 访问 http://localhost:8000/api/v1/docs
2. 使用 POST /api/v1/approvals/workflows 接口
3. 创建pPQR审批工作流
4. 刷新页面

创建工作流后，pPQR就可以正常提交审批了！

