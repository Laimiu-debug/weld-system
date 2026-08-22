import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Space,
  Divider,
  Alert,
  Checkbox,
  Row,
  Col,
  Tabs,
  Modal,
  message,
} from 'antd'
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  MobileOutlined,
  MailOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/auth'
import BrandMark from '@/components/Brand/BrandMark'

const { Title, Text } = Typography

interface LoginForm {
  account: string // 支持邮箱或手机号
  password: string
  remember: boolean
}

interface VerificationForm {
  account: string // 支持邮箱或手机号
  verificationCode: string
  remember: boolean
}

const Login: React.FC = () => {
  const [passwordForm] = Form.useForm()
  const [verificationForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [error, setError] = useState<string>('')
  const [countdown, setCountdown] = useState(0)
  const [resendOpen, setResendOpen] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const navigate = useNavigate()
  const { login, loginWithCode } = useAuthStore()

  // 判断输入的是邮箱还是手机号
  const detectAccountType = (account: string) => {
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(account)
    const isPhone = /^1[3-9]\d{9}$/.test(account)
    return { isEmail, isPhone }
  }

  // 密码登录
  const handlePasswordLogin = async (values: LoginForm) => {
    console.log('🚀 开始处理登录请求')
    setLoading(true)
    setError('')

    try {
      // 使用 authStore 的 login 方法
      console.log('📞 调用 authStore.login')
      const success = await login(values.account, values.password)
      console.log('📊 登录结果:', success)

      if (success) {
        console.log('✅ 登录成功，准备跳转到 /dashboard')
        message.success('登录成功！')

        // 使用 setTimeout 确保状态更新完成后再跳转
        setTimeout(() => {
          console.log('🔄 执行页面跳转')
          navigate('/dashboard', { replace: true })
        }, 100)
      } else {
        console.error('❌ 登录失败')
        // toast 由 api 拦截器展示；此处只保留页面内 Alert
        setError('账号或密码错误，请重新输入')
      }
    } catch (err: any) {
      console.error('❌ 登录异常:', err)
      const detail = err?.response?.data?.detail
      const tip =
        typeof detail === 'string'
          ? detail
          : typeof detail?.message === 'string'
            ? detail.message
            : '登录失败，请稍后重试'
      setError(tip)
      if (!err?.response) {
        message.error(tip)
      }
    } finally {
      setLoading(false)
    }
  }

  // 发送验证码（登录用，优先邮箱）
  const sendVerificationCode = async (account: string) => {
    if (!account) {
      message.error('请输入邮箱')
      return
    }

    const { isEmail, isPhone } = detectAccountType(account)

    if (!isEmail && !isPhone) {
      message.error('请输入有效的邮箱地址')
      return
    }
    if (!isEmail) {
      message.error('当前登录验证码仅支持邮箱，请使用注册邮箱')
      return
    }

    setSendingCode(true)
    try {
      await authService.sendVerificationCode({
        account,
        account_type: 'email',
        purpose: 'login',
      })
      message.success('验证码已发送到邮箱')
      setCountdown(60)
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      message.error(typeof detail === 'string' ? detail : detail?.message || '发送验证码失败')
    } finally {
      setSendingCode(false)
    }
  }

  // 验证码登录
  const handleVerificationLogin = async (values: VerificationForm) => {
    setLoading(true)
    setError('')

    try {
      const { isEmail } = detectAccountType(values.account)
      if (!isEmail) {
        setError('请输入有效的邮箱地址')
        setLoading(false)
        return
      }

      const success = await loginWithCode(values.account, values.verificationCode, 'email')

      if (success) {
        message.success('登录成功！')
        setTimeout(() => {
          navigate('/dashboard', { replace: true })
        }, 100)
      } else {
        setError('验证码错误或已过期，请重新获取')
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      const tip =
        typeof detail === 'string'
          ? detail
          : typeof detail?.message === 'string'
            ? detail.message
            : '登录失败，请稍后重试'
      setError(tip)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-form-wrapper">
        <div className="text-center mb-8">
          <BrandMark size={52} style={{ display: 'block', margin: '0 auto 12px' }} />
          <Title level={2} className="text-blue-600 mb-2">
            焊序
          </Title>
          <Text type="secondary">专业的焊接工艺管理平台</Text>
        </div>

        <Card className="shadow-lg">
          <Title level={3} className="text-center mb-6">
            用户登录
          </Title>

          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              className="mb-4"
              onClose={() => setError('')}
            />
          )}

          <Tabs
            defaultActiveKey="password"
            centered
            items={[
              {
                key: 'password',
                label: (
                  <span>
                    <LockOutlined />
                    密码登录
                  </span>
                ),
                children: (
                  <Form
                    form={passwordForm}
                    name="passwordLogin"
                    initialValues={{ remember: true }}
                    onFinish={handlePasswordLogin}
                    size="large"
                    layout="vertical"
                  >
                    <Form.Item
                      name="account"
                      label="账号"
                      rules={[
                        { required: true, message: '请输入邮箱或手机号' },
                        {
                          validator: (_, value) => {
                            if (!value) return Promise.resolve()
                            const { isEmail, isPhone } = detectAccountType(value)
                            if (!isEmail && !isPhone) {
                              return Promise.reject(new Error('请输入有效的邮箱地址或手机号'))
                            }
                            return Promise.resolve()
                          }
                        }
                      ]}
                    >
                      <Input
                        prefix={<UserOutlined />}
                        placeholder="请输入邮箱地址或手机号码"
                        autoComplete="username"
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      label="密码"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 1, message: '请输入密码' },
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="请输入密码"
                        autoComplete="current-password"
                        iconRender={(visible) =>
                          visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />
                        }
                      />
                    </Form.Item>

                    <Form.Item>
                      <div className="flex justify-between items-center">
                        <Form.Item name="remember" valuePropName="checked" noStyle>
                          <Checkbox>记住我</Checkbox>
                        </Form.Item>
                        <Link to="/forgot-password" className="text-blue-600">
                          忘记密码？
                        </Link>
                      </div>
                    </Form.Item>

                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        className="w-full h-12 text-base"
                      >
                        登录
                      </Button>
                    </Form.Item>
                  </Form>
                ),
              },
              {
                key: 'verification',
                label: (
                  <span>
                    <MailOutlined />
                    邮箱验证码登录
                  </span>
                ),
                children: (
                  <Form
                    form={verificationForm}
                    name="verificationLogin"
                    initialValues={{ remember: true }}
                    onFinish={handleVerificationLogin}
                    size="large"
                    layout="vertical"
                  >
                    <Form.Item
                      name="account"
                      label="邮箱"
                      rules={[
                        { required: true, message: '请输入邮箱' },
                        { type: 'email', message: '请输入有效邮箱' },
                      ]}
                    >
                      <Input
                        prefix={<MailOutlined />}
                        placeholder="请输入注册邮箱"
                        autoComplete="username"
                      />
                    </Form.Item>

                    <Form.Item
                      name="verificationCode"
                      label="邮箱验证码"
                      rules={[
                        { required: true, message: '请输入验证码' },
                        { len: 6, message: '验证码为6位数字' },
                        { pattern: /^\d{6}$/, message: '验证码必须为6位数字' }
                      ]}
                    >
                      <Input.Search
                        placeholder="请输入6位验证码"
                        enterButton={
                          <Button
                            type="primary"
                            loading={sendingCode}
                            disabled={countdown > 0}
                            onClick={() => {
                              const account = verificationForm.getFieldValue('account')
                              sendVerificationCode(account)
                            }}
                          >
                            {countdown > 0 ? `${countdown}s` : '发送验证码'}
                          </Button>
                        }
                        autoComplete="one-time-code"
                      />
                    </Form.Item>

                    <Form.Item>
                      <div className="flex justify-between items-center">
                        <Form.Item name="remember" valuePropName="checked" noStyle>
                          <Checkbox>记住我</Checkbox>
                        </Form.Item>
                        <Text type="secondary" className="text-sm">
                          验证码有效期为10分钟
                        </Text>
                      </div>
                    </Form.Item>

                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        className="w-full h-12 text-base"
                      >
                        登录
                      </Button>
                    </Form.Item>
                  </Form>
                ),
              },
            ]}
          />


          <div className="text-center">
            <Space direction="vertical" size="small">
              <Text type="secondary">还没有账号？</Text>
              <Link to="/register" className="text-blue-600 font-medium">
                立即注册
              </Link>
              <Button type="link" onClick={() => setResendOpen(true)}>
                重新发送验证邮件
              </Button>
            </Space>
          </div>

          <Divider />

          {/* 法律政策链接 */}
          <div className="text-center">
            <Space split={<Divider type="vertical" />} size="small">
              <Link to="/privacy-policy" style={{ fontSize: '12px', color: '#8c8c8c' }}>
                隐私政策
              </Link>
              <Link to="/terms-of-service" style={{ fontSize: '12px', color: '#8c8c8c' }}>
                用户协议
              </Link>
            </Space>
          </div>
        </Card>
        <Modal
          title="重新发送验证邮件"
          open={resendOpen}
          onCancel={() => setResendOpen(false)}
          footer={null}
        >
          <Form
            layout="vertical"
            onFinish={async (values: { email: string }) => {
              setResendLoading(true)
              try {
                const ok = await authService.resendVerificationEmail(values.email)
                if (ok) {
                  message.success('如果该邮箱已注册且未验证，将收到验证邮件')
                  setResendOpen(false)
                } else {
                  message.error('发送失败，请稍后重试')
                }
              } finally {
                setResendLoading(false)
              }
            }}
          >
            <Form.Item
              name="email"
              label="注册邮箱"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效邮箱' },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="you@example.com" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={resendLoading} block>
              发送
            </Button>
          </Form>
        </Modal>
        </div>
    </div>
  )
}

export default Login
