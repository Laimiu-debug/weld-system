import React, { useState } from 'react'
import { Button, Card, Form, Input, Result, Typography, message } from 'antd'
import { MailOutlined, SafetyOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { authService } from '@/services/auth'

const { Title, Paragraph } = Typography

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate()
  const [step, setStep] = useState<'email' | 'reset' | 'done'>('email')
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(false)
  const [countdown, setCountdown] = useState(0)

  const startCountdown = () => {
    setCountdown(60)
    const timer = window.setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          window.clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const sendCode = async (targetEmail: string) => {
    setSending(true)
    try {
      await authService.sendVerificationCode({
        account: targetEmail,
        account_type: 'email',
        purpose: 'reset_password',
      })
      message.success('若该邮箱已注册，将收到 6 位验证码')
      startCountdown()
      setEmail(targetEmail)
      setStep('reset')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      message.error(typeof detail === 'string' ? detail : detail?.message || '发送失败，请稍后重试')
    } finally {
      setSending(false)
    }
  }

  const onEmailFinish = async (values: { email: string }) => {
    await sendCode(values.email.trim().toLowerCase())
  }

  const onResetFinish = async (values: {
    verification_code: string
    new_password: string
    confirm_password: string
  }) => {
    setLoading(true)
    try {
      await authService.resetPasswordWithCode({
        email,
        verification_code: values.verification_code,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      })
      setStep('done')
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      message.error(typeof detail === 'string' ? detail : detail?.message || '重置失败，请检查验证码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        {step === 'done' ? (
          <Result
            status="success"
            title="密码已重置"
            subTitle="请使用新密码登录。"
            extra={
              <Button type="primary" onClick={() => navigate('/login')}>
                去登录
              </Button>
            }
          />
        ) : step === 'email' ? (
          <>
            <Title level={3} className="text-center">
              忘记密码
            </Title>
            <Paragraph type="secondary" className="text-center">
              输入注册邮箱，我们会发送 6 位验证码用于重置密码。
            </Paragraph>
            <Form layout="vertical" onFinish={onEmailFinish}>
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
              <Button type="primary" htmlType="submit" loading={sending} block>
                发送验证码
              </Button>
            </Form>
            <div className="text-center mt-4">
              <Link to="/login">返回登录</Link>
            </div>
          </>
        ) : (
          <>
            <Title level={3} className="text-center">
              重置密码
            </Title>
            <Paragraph type="secondary" className="text-center">
              验证码已发送至 {email}
            </Paragraph>
            <Form layout="vertical" onFinish={onResetFinish}>
              <Form.Item
                name="verification_code"
                label="邮箱验证码"
                rules={[
                  { required: true, message: '请输入验证码' },
                  { pattern: /^\d{6}$/, message: '验证码为 6 位数字' },
                ]}
              >
                <Input
                  prefix={<SafetyOutlined />}
                  placeholder="6 位验证码"
                  maxLength={6}
                  addonAfter={
                    <Button
                      type="link"
                      style={{ padding: 0, height: 'auto' }}
                      disabled={countdown > 0 || sending}
                      loading={sending}
                      onClick={() => sendCode(email)}
                    >
                      {countdown > 0 ? `${countdown}s` : '重新发送'}
                    </Button>
                  }
                />
              </Form.Item>
              <Form.Item
                name="new_password"
                label="新密码"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 8, message: '密码至少 8 位' },
                ]}
              >
                <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
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
                <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                确认重置
              </Button>
            </Form>
            <div className="text-center mt-4">
              <Button type="link" onClick={() => setStep('email')}>
                换一个邮箱
              </Button>
              <Link to="/login">返回登录</Link>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

export default ForgotPassword
