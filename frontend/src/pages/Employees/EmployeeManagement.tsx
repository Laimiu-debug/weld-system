import React from 'react'
import { Alert, Button, Card, Space } from 'antd'
import { Navigate, useNavigate } from 'react-router-dom'
import workspaceService from '@/services/workspace'

// Keep the legacy entry, while using the enterprise's authoritative member/invitation flow.
const EmployeeManagement: React.FC = () => {
  const navigate = useNavigate()
  const workspace = workspaceService.getCurrentWorkspaceFromStorage()
  if (workspace?.type === 'enterprise') return <Navigate to="/enterprise/employees" replace />
  return <Card title="员工管理">
    <Alert type="info" showIcon message="员工账号与邀请由企业工作区管理" description="请从右上角切换到所属企业，再管理成员或邀请同事加入。个人工作区可维护焊工档案，不会创建企业员工关系。" />
    <Space style={{ marginTop: 16 }}><Button onClick={() => navigate('/welders')}>管理焊工档案</Button><Button onClick={() => navigate('/profile')}>查看工作区</Button></Space>
  </Card>
}
export default EmployeeManagement
