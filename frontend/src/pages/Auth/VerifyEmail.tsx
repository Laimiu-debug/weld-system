import React, { useEffect, useState } from 'react'
import { Alert, Button, Card, Result, Spin, Typography } from 'antd'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { authService } from '@/services/auth'

const { Paragraph } = Typography

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [messageText, setMessageText] = useState('正在验证邮箱...')

  useEffect(() => {
    const run = async () => {
      if (!token) {
        setStatus('error')
        setMessageText('缺少验证令牌，请使用邮件中的完整链接。')
        return
      }
      const ok = await authService.verifyEmail(token)
      if (ok) {
        setStatus('success')
        setMessageText('邮箱验证成功，现在可以登录。')
        return
      }
      setStatus('error')
      setMessageText('验证链接无效或已过期，请重新发送验证邮件。')
    }
    void run()
  }, [token])

  if (status === 'loading') {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Spin size="large" tip={messageText} />
      </div>
    )
  }

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 p-4">
      <Card className="max-w-lg w-full">
        {status === 'success' ? (
          <Result
            status="success"
            title="邮箱已验证"
            subTitle={messageText}
            extra={<Button type="primary" onClick={() => navigate('/login')}>去登录</Button>}
          />
        ) : (
          <Result
            status="error"
            title="验证失败"
            subTitle={messageText}
            extra={[
              <Button key="login" onClick={() => navigate('/login')}>返回登录</Button>,
              <Button key="register" onClick={() => navigate('/register')}>重新注册</Button>,
            ]}
          />
        )}
        <Alert type="info" showIcon message={<Paragraph className="mb-0">如果没有收到邮件，可在登录页使用同一邮箱重新发送验证邮件。</Paragraph>} />
      </Card>
    </div>
  )
}

export default VerifyEmail
