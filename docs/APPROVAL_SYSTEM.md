# 审批系统使用文档

## 概述

本文档介绍WPS/PQR/pPQR文档管理系统的审批功能。审批系统支持基于工作区的灵活审批流程，包括多级审批、批量操作、通知提醒等功能。

## 功能特性

### 1. 基于工作区的审批逻辑

- **个人工作区**：文档创建后无需审批，直接生效
- **企业工作区**：文档需要经过配置的审批流程才能生效

### 2. 角色权限管理

在企业管理 > 角色设置中，每个角色都有审批权限配置：

- **企业管理员**：拥有所有文档类型的审批权限
- **部门经理**：拥有WPS、PQR、pPQR的审批权限
- **普通员工**：只能查看，无审批权限

权限配置示例：
```json
{
  "wps_management": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": true,
    "approve": true
  }
}
```

### 3. 审批工作流

#### 工作流定义

每个文档类型可以配置独立的审批工作流，包括：

- **工作流名称和代码**：标识工作流
- **文档类型**：WPS、PQR、pPQR、设备、焊材、焊工等
- **审批步骤**：支持多级审批
- **审批人类型**：角色、用户、部门
- **审批模式**：任一通过、全部通过、顺序审批

#### 审批步骤配置示例

```json
{
  "steps": [
    {
      "step_number": 1,
      "step_name": "部门经理审批",
      "approver_type": "role",
      "approver_ids": [2],
      "approval_mode": "any",
      "time_limit_hours": 48
    },
    {
      "step_number": 2,
      "step_name": "技术总监审批",
      "approver_type": "user",
      "approver_ids": [5, 6],
      "approval_mode": "all",
      "time_limit_hours": 24
    }
  ]
}
```

### 4. 审批操作

#### 提交审批

```typescript
// 单个文档提交
await approvalApi.submitForApproval({
  document_type: 'wps',
  document_ids: [123],
  notes: '请审批'
});

// 批量提交
await approvalApi.submitForApproval({
  document_type: 'wps',
  document_ids: [123, 124, 125],
  notes: '批量提交审批'
});
```

#### 审批操作

- **批准**：同意文档，进入下一审批步骤或完成审批
- **拒绝**：拒绝文档，审批流程结束
- **退回**：退回给提交人修改
- **取消**：提交人可以取消待审批的文档

```typescript
// 批准
await approvalApi.approve(instanceId, {
  comment: '审批通过',
  attachments: []
});

// 拒绝
await approvalApi.reject(instanceId, {
  comment: '不符合要求',
  attachments: []
});

// 退回
await approvalApi.return(instanceId, {
  comment: '请修改后重新提交',
  attachments: []
});

// 取消
await approvalApi.cancel(instanceId, '不需要审批了');
```

### 5. 批量操作

支持批量审批操作，提高审批效率：

```typescript
// 批量批准
await approvalApi.batchApprove({
  instance_ids: [1, 2, 3],
  comment: '批量批准'
});

// 批量拒绝
await approvalApi.batchReject({
  instance_ids: [4, 5, 6],
  comment: '批量拒绝'
});
```

### 6. 审批历史

每个审批实例都有完整的审批历史记录，包括：

- 操作步骤
- 操作人
- 操作时间
- 操作类型（提交、批准、拒绝、退回、取消）
- 审批意见
- 附件

### 7. 通知系统

审批过程中会自动发送通知：

- **提交审批**：通知审批人有新的审批请求
- **审批通过**：通知提交人审批已通过
- **审批拒绝**：通知提交人审批被拒绝
- **审批退回**：通知提交人需要修改
- **超时提醒**：提醒审批人及时处理

## 数据库表结构

### approval_workflow_definitions（审批工作流定义表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 工作流名称 |
| code | String | 工作流代码 |
| document_type | String | 文档类型 |
| company_id | Integer | 企业ID（可选） |
| steps | JSONB | 审批步骤配置 |
| is_active | Boolean | 是否启用 |
| is_default | Boolean | 是否默认 |

### approval_instances（审批实例表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| workflow_id | Integer | 工作流ID |
| document_type | String | 文档类型 |
| document_id | Integer | 文档ID |
| status | String | 状态 |
| current_step | Integer | 当前步骤 |
| submitter_id | Integer | 提交人ID |
| submitted_at | DateTime | 提交时间 |
| completed_at | DateTime | 完成时间 |

### approval_history（审批历史表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| instance_id | Integer | 审批实例ID |
| step_number | Integer | 步骤编号 |
| action | String | 操作类型 |
| operator_id | Integer | 操作人ID |
| comment | Text | 审批意见 |
| created_at | DateTime | 操作时间 |

### approval_notifications（审批通知表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| instance_id | Integer | 审批实例ID |
| recipient_id | Integer | 接收人ID |
| notification_type | String | 通知类型 |
| is_read | Boolean | 是否已读 |
| created_at | DateTime | 创建时间 |

## API接口

### 提交审批

```
POST /api/v1/approvals/submit
```

### 审批操作

```
POST /api/v1/approvals/{instance_id}/approve
POST /api/v1/approvals/{instance_id}/reject
POST /api/v1/approvals/{instance_id}/return
POST /api/v1/approvals/{instance_id}/cancel
```

### 批量操作

```
POST /api/v1/approvals/batch/approve
POST /api/v1/approvals/batch/reject
```

### 查询接口

```
GET /api/v1/approvals/pending              # 待我审批
GET /api/v1/approvals/my-submissions       # 我提交的
GET /api/v1/approvals/{instance_id}        # 审批详情
GET /api/v1/approvals/{instance_id}/history # 审批历史
GET /api/v1/approvals/statistics           # 审批统计
```

## 前端组件使用

### ApprovalButton 组件

在文档详情页添加审批按钮：

```tsx
import { ApprovalButton } from '@/components/Approval/ApprovalButton';

<ApprovalButton
  documentType="wps"
  documentId={123}
  documentTitle="WPS-001"
  canSubmit={true}
  onSuccess={() => {
    // 刷新页面
  }}
/>
```

### ApprovalHistory 组件

显示审批历史：

```tsx
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory';

<ApprovalHistory instanceId={456} showCard={true} />
```

### ApprovalList 页面

审批列表页面：

```tsx
import { ApprovalList } from '@/pages/Approval/ApprovalList';

<ApprovalList
  workspaceType="enterprise"
  workspaceId="1"
/>
```

## 数据库迁移

运行以下命令创建审批系统相关表：

```bash
cd backend
alembic upgrade head
```

## 注意事项

1. **权限检查**：所有审批操作都会检查用户权限
2. **工作区隔离**：个人工作区和企业工作区的审批逻辑完全独立
3. **审批状态**：文档状态会随审批流程自动更新
4. **通知发送**：确保配置了邮件服务以发送邮件通知
5. **批量操作**：批量操作会逐个处理，部分失败不影响其他成功的操作

## 后续优化建议

1. 添加审批超时自动处理机制
2. 支持审批流程的动态调整
3. 添加审批统计报表
4. 支持审批委托功能
5. 添加审批模板快速配置

