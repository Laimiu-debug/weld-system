# 审批系统快速集成指南

本指南帮助您快速将审批功能集成到WPS/PQR/pPQR文档管理系统中。

## 第一步：运行数据库迁移

```bash
cd backend
alembic upgrade head
```

这将创建以下表：
- `approval_workflow_definitions` - 审批工作流定义
- `approval_instances` - 审批实例
- `approval_history` - 审批历史
- `approval_notifications` - 审批通知

## 第二步：更新文档模型（可选）

如果需要在文档表中添加审批状态字段，可以在WPS/PQR/pPQR模型中添加：

```python
# backend/app/models/wps.py
class WPS(Base):
    # ... 现有字段 ...
    
    # 添加审批相关字段
    approval_instance_id = Column(Integer, ForeignKey('approval_instances.id'), nullable=True)
    approval_status = Column(String(20), nullable=True)  # pending, approved, rejected
    
    # 关系
    approval_instance = relationship("ApprovalInstance", foreign_keys=[approval_instance_id])
```

## 第三步：在文档详情页集成审批按钮

### 3.1 导入组件

```tsx
// frontend/src/pages/WPS/WPSDetail.tsx
import { ApprovalButton } from '@/components/Approval/ApprovalButton';
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory';
```

### 3.2 添加审批按钮

在文档详情页的操作按钮区域添加：

```tsx
<ApprovalButton
  documentType="wps"
  documentId={wpsId}
  documentTitle={wps.title}
  instanceId={wps.approval_instance_id}
  status={wps.approval_status}
  canApprove={checkApprovalPermission()}
  canSubmit={wps.status === 'draft' && !wps.approval_instance_id}
  canCancel={wps.approval_instance_id && wps.submitter_id === currentUser.id}
  onSuccess={() => {
    // 刷新文档数据
    fetchWPSDetail();
  }}
/>
```

### 3.3 添加审批历史Tab

在文档详情的Tabs中添加审批历史：

```tsx
<Tabs>
  <TabPane tab="基本信息" key="basic">
    {/* 现有内容 */}
  </TabPane>
  
  <TabPane tab="审批历史" key="approval">
    {wps.approval_instance_id && (
      <ApprovalHistory instanceId={wps.approval_instance_id} />
    )}
  </TabPane>
</Tabs>
```

## 第四步：在文档列表页添加批量提交

### 4.1 导入API

```tsx
// frontend/src/pages/WPS/WPSList.tsx
import { approvalApi } from '@/services/approval';
```

### 4.2 添加批量提交按钮

```tsx
const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);

// 批量提交审批
const handleBatchSubmit = async () => {
  try {
    await approvalApi.submitForApproval({
      document_type: 'wps',
      document_ids: selectedRowKeys,
      notes: '批量提交审批'
    });
    message.success('批量提交成功');
    setSelectedRowKeys([]);
    fetchList();
  } catch (error) {
    message.error('批量提交失败');
  }
};

// 在表格上方添加按钮
{selectedRowKeys.length > 0 && (
  <Button 
    type="primary" 
    onClick={handleBatchSubmit}
  >
    批量提交审批 ({selectedRowKeys.length})
  </Button>
)}
```

## 第五步：添加审批管理页面

### 5.1 创建路由

```tsx
// frontend/src/routes/index.tsx
import ApprovalList from '@/pages/Approval/ApprovalList';

{
  path: '/approval',
  name: '审批管理',
  icon: 'CheckCircleOutlined',
  component: ApprovalList,
}
```

### 5.2 在菜单中添加入口

```tsx
// frontend/src/layouts/BasicLayout.tsx
const menuItems = [
  // ... 其他菜单项 ...
  {
    key: '/approval',
    icon: <CheckCircleOutlined />,
    label: '审批管理',
  },
];
```

## 第六步：配置审批工作流（后台管理）

### 6.1 创建默认工作流

可以通过API或数据库直接插入默认工作流：

```python
# backend/scripts/init_approval_workflows.py
from app.models.approval import ApprovalWorkflowDefinition
from app.core.database import SessionLocal

db = SessionLocal()

# WPS审批工作流
wps_workflow = ApprovalWorkflowDefinition(
    name="WPS标准审批流程",
    code="WPS_STANDARD",
    document_type="wps",
    company_id=None,  # 系统默认
    steps=[
        {
            "step_number": 1,
            "step_name": "部门经理审批",
            "approver_type": "role",
            "approver_ids": [2],  # 部门经理角色ID
            "approval_mode": "any",
            "time_limit_hours": 48
        },
        {
            "step_number": 2,
            "step_name": "技术总监审批",
            "approver_type": "role",
            "approver_ids": [1],  # 企业管理员角色ID
            "approval_mode": "any",
            "time_limit_hours": 24
        }
    ],
    is_active=True,
    is_default=True
)

db.add(wps_workflow)
db.commit()
```

### 6.2 企业自定义工作流

企业可以在管理后台创建自己的审批工作流，覆盖系统默认流程。

## 第七步：权限配置

确保角色权限中包含审批权限。系统已经为默认角色配置了审批权限：

- **企业管理员**: 所有文档类型的审批权限
- **部门经理**: WPS/PQR/pPQR的审批权限
- **普通员工**: 无审批权限

如需修改，可在企业管理 > 角色设置中调整。

## 第八步：测试审批流程

### 8.1 提交审批

1. 以普通员工身份登录
2. 创建一个WPS文档
3. 在企业工作区中，点击"提交审批"按钮
4. 填写备注，提交

### 8.2 审批文档

1. 以部门经理身份登录
2. 进入"审批管理"页面
3. 在"待我审批"Tab中查看待审批文档
4. 点击"批准"或"拒绝"按钮
5. 填写审批意见，确认

### 8.3 查看审批历史

1. 在文档详情页
2. 切换到"审批历史"Tab
3. 查看完整的审批流程和历史记录

## 常见问题

### Q1: 个人工作区的文档需要审批吗？

A: 不需要。个人工作区的文档无需审批，直接生效。只有企业工作区的文档才需要审批。

### Q2: 如何修改审批流程？

A: 企业管理员可以在后台创建自定义的审批工作流，覆盖系统默认流程。

### Q3: 批量操作失败怎么办？

A: 批量操作会逐个处理，部分失败不影响其他成功的操作。失败的项目会在返回结果中列出。

### Q4: 如何取消已提交的审批？

A: 只有提交人可以取消待审批或审批中的文档。已完成的审批无法取消。

### Q5: 审批通知如何发送？

A: 系统会自动发送应用内通知。如需邮件通知，请确保配置了邮件服务。

## 完整示例

### WPS详情页完整集成示例

```tsx
import React, { useState, useEffect } from 'react';
import { Card, Tabs, Button, Space, message } from 'antd';
import { ApprovalButton } from '@/components/Approval/ApprovalButton';
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory';
import { wpsApi } from '@/services/wps';

const { TabPane } = Tabs;

const WPSDetail: React.FC = ({ match }) => {
  const [wps, setWps] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const wpsId = match.params.id;

  useEffect(() => {
    fetchWPSDetail();
  }, [wpsId]);

  const fetchWPSDetail = async () => {
    setLoading(true);
    try {
      const response = await wpsApi.getDetail(wpsId);
      setWps(response.data);
    } catch (error) {
      message.error('获取WPS详情失败');
    } finally {
      setLoading(false);
    }
  };

  const checkApprovalPermission = () => {
    // 检查当前用户是否有审批权限
    const permissions = getCurrentUserPermissions();
    return permissions?.wps_management?.approve || false;
  };

  return (
    <Card
      title={`WPS详情 - ${wps?.title || ''}`}
      extra={
        <Space>
          <ApprovalButton
            documentType="wps"
            documentId={wpsId}
            documentTitle={wps?.title}
            instanceId={wps?.approval_instance_id}
            status={wps?.approval_status}
            canApprove={checkApprovalPermission()}
            canSubmit={wps?.status === 'draft' && !wps?.approval_instance_id}
            canCancel={wps?.approval_instance_id && wps?.submitter_id === currentUser.id}
            onSuccess={fetchWPSDetail}
          />
          <Button onClick={() => history.back()}>返回</Button>
        </Space>
      }
      loading={loading}
    >
      <Tabs defaultActiveKey="basic">
        <TabPane tab="基本信息" key="basic">
          {/* WPS基本信息 */}
        </TabPane>
        
        <TabPane tab="技术参数" key="technical">
          {/* 技术参数 */}
        </TabPane>
        
        <TabPane tab="审批历史" key="approval">
          {wps?.approval_instance_id ? (
            <ApprovalHistory instanceId={wps.approval_instance_id} showCard={false} />
          ) : (
            <Empty description="暂无审批记录" />
          )}
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default WPSDetail;
```

## 下一步

- 配置邮件服务以启用邮件通知
- 创建企业自定义审批工作流
- 设置审批超时提醒
- 查看审批统计报表

## 技术支持

如有问题，请参考：
- [审批系统使用文档](./APPROVAL_SYSTEM.md)
- [审批系统实现总结](./APPROVAL_IMPLEMENTATION_SUMMARY.md)

