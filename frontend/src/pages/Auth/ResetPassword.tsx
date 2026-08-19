import React, { useState } from 'react'
import { Button, Card, Form, Input, Result, Typography, message } from 'antd'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { authService } from '@/services/auth'

const { Title, Paragraph } = Typography

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const onFinish = async (values: { new_password: string; confirm_password: string }) => {
    if (!token) {
      message.error('缺少重置令牌')
      return
    }
    setLoading(true)
    try {
      const ok = await authService.resetPassword({
        token,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      })
      if (!ok) {
        message.error('重置失败，链接可能已过期')
        return
      }
      setDone(true)
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <Card className="w-full max-w-md">
          <Result
            status="error"
            title="重置链接无效"
            subTitle="请使用邮件中的完整链接，或重新申请重置密码。"
            extra={<Link to="/forgot-password"><Button type="primary">重新申请</Button></Link>}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        {done ? (
          <Result
            status="success"
            title="密码已重置"
            extra={<Button type="primary" onClick={() => navigate('/login')}>去登录</Button>}
          />
        ) : (
          <>
            <Title level={3} className="text-center">设置新密码</Title>
            <Paragraph type="secondary" className="text-center">请输入新密码并确认。</Paragraph>
            <Form layout="vertical" onFinish={onFinish}>
              <Form.Item
                name="new_password"
                label="新密码"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 8, message: '密码至少 8 位' },
                ]}
              >
                <Input.Password autoComplete="new-password" />
              </Form.Item>
              <Form.Item
                name="confirm_password"
                label="确认密码"
                dependencies={['new_password']}
                rules={[
                  { required: true, message: '请再次输入密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password autoComplete="new-password" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                确认重置
              </Button>
            </Form>
          </>
        )}
      </Card>
    </div>
  )
}

export default ResetPassword
