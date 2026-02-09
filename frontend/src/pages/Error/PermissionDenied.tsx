import React from 'react'
import { Result, Button } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const PermissionDenied: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Result
        status="403"
        icon={<LockOutlined style={{ fontSize: 72, color: '#ff4d4f' }} />}
        title="权限不足"
        subTitle="抱歉，您没有权限访问此页面。请联系管理员为您分配相应的角色和权限。"
        extra={[
          <Button type="primary" key="dashboard" onClick={() => navigate('/dashboard')}>
            返回仪表盘
          </Button>,
          <Button key="back" onClick={() => navigate(-1)}>
            返回上一页
          </Button>,
        ]}
      />
    </div>
  )
}

export default PermissionDenied

