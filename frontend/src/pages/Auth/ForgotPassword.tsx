import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const ForgotPassword: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <Title level={2} className="text-center mb-6 text-blue-600">
          忘记密码
        </Title>
        <Card>
          <p>忘记密码页面组件 - 开发中</p>
        </Card>
      </div>
    </div>
  )
}

export default ForgotPassword