import React from 'react'
import { Alert, Button, Card } from 'antd'
import { useNavigate } from 'react-router-dom'
import workspaceService from '@/services/workspace'

const EnterpriseWorkspaceGate: React.FC<React.PropsWithChildren> = ({ children }) => {
  const navigate = useNavigate()
  const workspace = workspaceService.getCurrentWorkspaceFromStorage()
  if (workspace?.type === 'enterprise') return <>{children}</>
  return <Card title="企业员工与邀请">
    <Alert type="info" showIcon message="请先切换到企业工作区" description="员工账号和邀请属于企业。请使用右上角工作区切换器选择所属企业；个人工作区可维护焊工档案。" />
    <Button style={{ marginTop: 16 }} onClick={() => navigate('/welders')}>管理焊工档案</Button>
  </Card>
}
export default EnterpriseWorkspaceGate
