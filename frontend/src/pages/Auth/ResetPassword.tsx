import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const ResetPassword: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <Title level={2} className="text-center mb-6 text-blue-600">
          重置密码
        </Title>
        <Card>
          <p>重置密码页面组件 - 开发中</p>
        </Card>
      </div>
    </div>
  )
}

export default ResetPassword