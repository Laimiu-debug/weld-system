import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button, Descriptions, Tag, Space, Alert, Typography } from 'antd'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/auth'

const { Title, Paragraph, Text } = Typography

const LoginDebug: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, loading } = useAuthStore()
  const [localStorageData, setLocalStorageData] = useState<any>({})

  useEffect(() => {
    // 读取localStorage数据
    const data = {
      access_token: localStorage.getItem('access_token'),
      refresh_token: localStorage.getItem('refresh_token'),
      user_info: localStorage.getItem('user_info'),
      auth_storage: localStorage.getItem('auth-storage'),
    }
    setLocalStorageData(data)
  }, [])

  const handleTestLogin = async () => {
    const { login } = useAuthStore.getState()
    const success = await login('test@test.com', 'test123')
    console.log('测试登录结果:', success)
    
    // 刷新localStorage数据
    setTimeout(() => {
      const data = {
        access_token: localStorage.getItem('access_token'),
        refresh_token: localStorage.getItem('refresh_token'),
        user_info: localStorage.getItem('user_info'),
        auth_storage: localStorage.getItem('auth-storage'),
      }
      setLocalStorageData(data)
    }, 500)
  }

  const handleClearStorage = () => {
    localStorage.clear()
    sessionStorage.clear()
    window.location.reload()
  }

  const handleNavigateToDashboard = () => {
    navigate('/dashboard', { replace: true })
  }

  const handleForceNavigate = () => {
    window.location.href = '/dashboard'
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>登录状态调试页面</Title>
      <Paragraph>
        这个页面用于调试登录状态和路由跳转问题
      </Paragraph>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 当前状态 */}
        <Card title="当前认证状态" bordered>
          <Descriptions column={1}>
            <Descriptions.Item label="是否已认证">
              {isAuthenticated ? (
                <Tag color="success">已认证 ✅</Tag>
              ) : (
                <Tag color="error">未认证 ❌</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="加载状态">
              {loading ? (
                <Tag color="processing">加载中...</Tag>
              ) : (
                <Tag color="default">空闲</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="用户信息">
              {user ? (
                <div>
                  <div>ID: {user.id}</div>
                  <div>用户名: {user.username}</div>
                  <div>邮箱: {user.email}</div>
                  <div>姓名: {user.full_name}</div>
                  <div>会员等级: {user.membership_tier}</div>
                </div>
              ) : (
                <Text type="secondary">无</Text>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* localStorage数据 */}
        <Card title="localStorage 数据" bordered>
          <Descriptions column={1}>
            <Descriptions.Item label="access_token">
              {localStorageData.access_token ? (
                <Text code>{localStorageData.access_token.substring(0, 50)}...</Text>
              ) : (
                <Tag color="error">不存在</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="refresh_token">
              {localStorageData.refresh_token ? (
                <Text code>{localStorageData.refresh_token.substring(0, 50)}...</Text>
              ) : (
                <Tag color="error">不存在</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="user_info">
              {localStorageData.user_info ? (
                <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                  {JSON.stringify(JSON.parse(localStorageData.user_info), null, 2)}
                </pre>
              ) : (
                <Tag color="error">不存在</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="auth-storage (Zustand)">
              {localStorageData.auth_storage ? (
                <pre style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                  {JSON.stringify(JSON.parse(localStorageData.auth_storage), null, 2)}
                </pre>
              ) : (
                <Tag color="error">不存在</Tag>
              )}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 诊断信息 */}
        <Card title="诊断信息" bordered>
          {!isAuthenticated && !localStorageData.access_token && (
            <Alert
              message="未登录状态"
              description="用户未登录，localStorage中没有token"
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />
          )}

          {!isAuthenticated && localStorageData.access_token && (
            <Alert
              message="状态不一致"
              description="localStorage中有token，但authStore的isAuthenticated为false。这可能是状态同步问题。"
              type="warning"
              showIcon
              style={{ marginBottom: '16px' }}
            />
          )}

          {isAuthenticated && !localStorageData.access_token && (
            <Alert
              message="状态异常"
              description="authStore显示已认证，但localStorage中没有token。这是异常状态。"
              type="error"
              showIcon
              style={{ marginBottom: '16px' }}
            />
          )}

          {isAuthenticated && localStorageData.access_token && (
            <Alert
              message="正常登录状态"
              description="用户已登录，状态正常。可以尝试跳转到仪表盘。"
              type="success"
              showIcon
              style={{ marginBottom: '16px' }}
            />
          )}
        </Card>

        {/* 操作按钮 */}
        <Card title="测试操作" bordered>
          <Space wrap>
            <Button type="primary" onClick={handleTestLogin}>
              测试登录 (test@test.com)
            </Button>
            <Button onClick={handleNavigateToDashboard}>
              使用 navigate() 跳转到仪表盘
            </Button>
            <Button onClick={handleForceNavigate}>
              使用 window.location 强制跳转
            </Button>
            <Button danger onClick={handleClearStorage}>
              清除所有存储并刷新
            </Button>
          </Space>
        </Card>

        {/* 控制台日志提示 */}
        <Card title="调试提示" bordered>
          <Alert
            message="请打开浏览器控制台"
            description={
              <div>
                <p>按 F12 打开开发者工具，切换到 Console 标签页</p>
                <p>所有操作都会在控制台输出详细日志，包括：</p>
                <ul>
                  <li>🔐 登录流程的每一步</li>
                  <li>📊 API响应数据</li>
                  <li>✅ 状态更新信息</li>
                  <li>🔄 路由跳转信息</li>
                </ul>
              </div>
            }
            type="info"
            showIcon
          />
        </Card>

        {/* 返回登录页 */}
        <Card>
          <Button onClick={() => navigate('/login')}>返回登录页</Button>
        </Card>
      </Space>
    </div>
  )
}

export default LoginDebug

