import React, { useState } from 'react'
import { Button, Card, Form, Input, Result, Typography, message } from 'antd'
import { MailOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { authService } from '@/services/auth'

const { Title, Paragraph } = Typography

const ForgotPassword: React.FC = () => {
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { email: string }) => {
    setLoading(true)
    try {
      const ok = await authService.forgotPassword({ email: values.email })
      if (!ok) {
        message.error('发送失败，请稍后重试')
        return
      }
      setSubmitted(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        {submitted ? (
          <Result
            status="success"
            title="如果该邮箱已注册，将收到密码重置邮件"
            subTitle="请检查收件箱（含垃圾邮件）。重置链接通常在数分钟内到达。"
            extra={<Link to="/login"><Button type="primary">返回登录</Button></Link>}
          />
        ) : (
          <>
            <Title level={3} className="text-center">忘记密码</Title>
            <Paragraph type="secondary" className="text-center">
              输入注册邮箱，我们会发送重置链接。无论邮箱是否存在，都会显示同一提示，避免泄露账号信息。
            </Paragraph>
            <Form layout="vertical" onFinish={onFinish}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效邮箱' },
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="you@example.com" autoComplete="email" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                发送重置邮件
              </Button>
            </Form>
            <div className="text-center mt-4">
              <Link to="/login">返回登录</Link>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

export default ForgotPassword
