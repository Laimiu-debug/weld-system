import React, { useState, useEffect } from 'react'
import { Button, Card, Typography, Space, Divider, Tag, Spin } from 'antd'
import { workspaceService, Workspace } from '@/services/workspace'
import { useAuthStore } from '@/store/authStore'

const { Title, Text, Paragraph } = Typography

const DebugWorkspace: React.FC = () => {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [debugInfo, setDebugInfo] = useState<any>({})

  const runDebug = async () => {
    setLoading(true)
    try {
      console.log('=== 开始工作区调试 ===')

      // 1. 获取用户信息
      console.log('1. 当前用户信息:', user)

      // 2. 获取工作区列表
      const workspacesResponse = await workspaceService.getUserWorkspaces()
      console.log('2. 工作区API响应:', workspacesResponse)

      let workspaces: any[] = []
      if (Array.isArray(workspacesResponse)) {
        workspaces = workspacesResponse
      } else if (workspacesResponse?.data) {
        workspaces = Array.isArray(workspacesResponse.data) ? workspacesResponse.data : [workspacesResponse.data]
      }

      console.log('3. 解析后的工作区数据:', workspaces)

      // 3. 获取当前工作区
      const currentResponse = await workspaceService.getCurrentWorkspace()
      console.log('4. 当前工作区响应:', currentResponse)

      // 4. 检查权限
      const permissionChecks = workspaces.map(workspace => ({
        id: workspace.id,
        name: workspace.name,
        type: workspace.type,
        role: workspace.role,
        canSwitch: workspaceService.canSwitchToWorkspace(workspace)
      }))

      console.log('5. 权限检查结果:', permissionChecks)

      // 5. 尝试切换（仅记录请求，不实际切换）
      const switchRequests = workspaces.map(workspace => {
        const canSwitch = workspaceService.canSwitchToWorkspace(workspace)
        return {
          id: workspace.id,
          name: workspace.name,
          canSwitch: canSwitch.allowed,
          reason: canSwitch.reason,
          request: canSwitch.allowed ? {
            workspace_id: workspace.id
          } : null
        }
      })

      console.log('6. 切换请求模拟:', switchRequests)

      setDebugInfo({
        user: user,
        workspacesCount: workspaces.length,
        workspaces: workspaces,
        currentWorkspace: currentResponse,
        permissionChecks: permissionChecks,
        switchRequests: switchRequests
      })

    } catch (error) {
      console.error('调试过程中出错:', error)
      setDebugInfo({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>工作区调试工具</Title>
      <Paragraph>
        此工具用于诊断工作区相关的问题，包括数据获取、权限检查和切换操作。
      </Paragraph>

      <Space direction="vertical" style={{ width: '100%' }}>
        <Button type="primary" onClick={runDebug} loading={loading}>
          运行调试检查
        </Button>

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>正在调试...</div>
          </div>
        )}

        {debugInfo.error && (
          <Card title="错误信息" style={{ borderColor: '#ff4d4f' }}>
            <Text type="danger">{debugInfo.error}</Text>
          </Card>
        )}

        {debugInfo.user && (
          <Card title="用户信息">
            <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
              {JSON.stringify(debugInfo.user, null, 2)}
            </pre>
          </Card>
        )}

        {debugInfo.workspaces && (
          <Card title={`工作区列表 (${debugInfo.workspacesCount}个)`}>
            {debugInfo.workspaces.map((workspace: any, index: number) => (
              <div key={index} style={{ marginBottom: '16px', padding: '12px', border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>{workspace.name}</Text>
                  <Space wrap>
                    <Tag>ID: {workspace.id}</Tag>
                    <Tag color={workspace.type === 'personal' ? 'blue' : 'green'}>
                      {workspace.type}
                    </Tag>
                    {workspace.role && <Tag color="orange">角色: {workspace.role}</Tag>}
                    {workspace.department && <Tag color="purple">部门: {workspace.department}</Tag>
                    {workspace.status && <Tag color={workspace.status === 'active' ? 'green' : 'red'}>
                      状态: {workspace.status}
                    </Tag>}
                  </Space>
                  <Text type="secondary">{workspace.description}</Text>
                </Space>
              </div>
            ))}
          </Card>
        )}

        {debugInfo.currentWorkspace && (
          <Card title="当前工作区">
            <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
              {JSON.stringify(debugInfo.currentWorkspace, null, 2)}
            </pre>
          </Card>
        )}

        {debugInfo.permissionChecks && (
          <Card title="权限检查结果">
            {debugInfo.permissionChecks.map((check: any, index: number) => (
              <div key={index} style={{ marginBottom: '8px' }}>
                <Space>
                  <Text strong>{check.name}</Text>
                  <Tag color={check.canSwitch.allowed ? 'green' : 'red'}>
                    {check.canSwitch.allowed ? '✓ 可切换' : '✗ 不可切换'}
                  </Tag>
                  {check.canSwitch.reason && <Text type="danger">原因: {check.canSwitch.reason}</Text>}
                </Space>
              </div>
            ))}
          </Card>
        )}

        <Divider />
        <Text type="secondary">
          请打开浏览器开发者工具的控制台查看详细的调试信息。
        </Text>
      </Space>
    </div>
  )
}

export default DebugWorkspace