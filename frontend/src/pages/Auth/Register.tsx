import React, { useEffect, useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  message,
  Spin,
  Divider,
  Space,
  Alert,
  Modal,
  Checkbox
} from 'antd'
import { UserOutlined, LockOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import enterpriseService from '@/services/enterprise'

const { Title, Text } = Typography

const Register: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [errorInfo, setErrorInfo] = useState<{
    type: 'email_exists' | 'username_exists' | 'general_error' | null
    message: string
    account?: string
  }>({ type: null, message: '' })
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inviteToken = searchParams.get('invite') || undefined
  const [inviteInfo, setInviteInfo] = useState<{ company_name?: string; email?: string } | null>(null)
  const [registrationEnabled, setRegistrationEnabled] = useState(true)
  const [maintenanceMode, setMaintenanceMode] = useState(false)
  const { register, isAuthenticated } = useAuthStore()

  useEffect(() => {
    const loadPublicConfig = async () => {
      try {
        const base = import.meta.env.VITE_API_BASE_URL || '/api/v1'
        const resp = await fetch(`${base}/system/public-config`)
        if (!resp.ok) return
        const body = await resp.json()
        const data = body?.data || body
        if (typeof data?.registration_enabled === 'boolean') {
          setRegistrationEnabled(data.registration_enabled)
        }
        if (typeof data?.maintenance_mode === 'boolean') {
          setMaintenanceMode(data.maintenance_mode)
        }
      } catch {
        // 公开配置失败时不阻断页面
      }
    }
    void loadPublicConfig()
  }, [])

  useEffect(() => {
    if (!inviteToken) return
    const load = async () => {
      try {
        const response = await enterpriseService.previewInvitation(inviteToken)
        const data = response.data?.data || response.data
        setInviteInfo(data)
        if (data?.email) {
          form.setFieldsValue({ account: data.email })
        }
      } catch {
        message.error('邀请链接无效或已过期')
      }
    }
    void load()
  }, [inviteToken, form])

  const onFinish = async (values: any) => {
    if ((!registrationEnabled && !inviteToken) || maintenanceMode) {
      message.error(maintenanceMode ? '系统维护中，暂时无法注册' : '系统已关闭新用户注册')
      return
    }
    setLoading(true)
    setConfirmLoading(true)

    try {
      // 清除之前的错误信息
      setErrorInfo({ type: null, message: '' })

      // 判断账号是邮箱还是手机号
      const account = values.account
      const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(account)
      const isPhone = /^1[3-9]\d{9}$/.test(account)

      const success = await register({
        email: isEmail ? account : `${values.username}@welding.com`, // 如果是手机号，生成格式化的邮箱
        password: values.password,
        username: values.username,
        full_name: values.username, // 使用用户名作为姓名
        phone: isPhone ? account : undefined, // 如果是手机号，设置为phone字段
        invite_token: inviteToken,
      })

      if (success) {
        message.success('注册成功！请查收验证邮件后再登录')
        form.resetFields()
        navigate('/login')
      } else {
        message.error('注册失败，请检查输入信息')
      }
    } catch (error: any) {
      console.error('Registration error:', error)

      // 根据错误类型显示不同的错误信息
      if (error.response?.data?.detail) {
        const errorMsg = error.response.data.detail

        if (typeof errorMsg === 'string') {
          if (errorMsg.includes('邮箱') || errorMsg.includes('email')) {
            setErrorInfo({
              type: 'email_exists',
              message: '该邮箱已被注册',
              account: values.account
            })
            Modal.confirm({
              title: '邮箱已被注册',
              icon: <ExclamationCircleOutlined />,
              content: '该邮箱地址已经被注册过了。您可以尝试忘记密码找回账户，或使用其他邮箱重新注册。',
              okText: '找回密码',
              cancelText: '更换邮箱',
              onOk: () => {
                navigate('/forgot-password')
              },
              onCancel: () => {
                form.setFieldsValue({ account: '' })
              }
            })
          } else if (errorMsg.includes('用户名') || errorMsg.includes('username')) {
            setErrorInfo({
              type: 'username_exists',
              message: '该用户名已被使用',
              account: values.username
            })
            Modal.confirm({
              title: '用户名已被使用',
              icon: <ExclamationCircleOutlined />,
              content: '该用户名已经被使用了。请选择其他用户名重新注册。',
              okText: '更换用户名',
              cancelText: '取消',
              onOk: () => {
                form.setFieldsValue({ username: '' })
              }
            })
          } else if (errorMsg.includes('password')) {
            setErrorInfo({
              type: 'general_error',
              message: '密码格式不符合安全要求，请使用更复杂的密码'
            })
          } else {
            setErrorInfo({
              type: 'general_error',
              message: '注册失败，请检查输入信息是否正确'
            })
          }
        } else if (errorMsg === 'Internal server error') {
          setErrorInfo({
            type: 'general_error',
            message: '系统繁忙，请稍后再试'
          })
        } else {
          setErrorInfo({
            type: 'general_error',
            message: '注册失败，请检查输入信息'
          })
        }
      } else {
        setErrorInfo({
          type: 'general_error',
          message: '网络连接异常，请检查网络后重试'
        })
      }
    } finally {
      setLoading(false)
      setConfirmLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Title level={2} className="text-blue-600 mb-2">
            焊序
          </Title>
          <Text type="secondary">专业的焊接工艺管理平台</Text>
        </div>

        <Card className="shadow-lg">
          <Title level={3} className="text-center mb-6">
            用户注册
          </Title>

          {inviteInfo?.company_name && (
            <Alert
              type="info"
              showIcon
              className="mb-4"
              message={`你正在加入企业：${inviteInfo.company_name}`}
              description="请使用邀请邮箱完成注册，加入后可进入企业工作区。"
            />
          )}

          {(maintenanceMode || (!registrationEnabled && !inviteToken)) && (
            <Alert
              type="warning"
              showIcon
              className="mb-4"
              message={maintenanceMode ? '系统维护中' : '暂不开放注册'}
              description={
                maintenanceMode
                  ? '系统正在维护，请稍后再试。'
                  : '管理员已关闭新用户注册，如需账号请联系管理员。'
              }
            />
          )}

          {errorInfo.type && (
            <Alert
              type="error"
              message={errorInfo.message}
              showIcon
              closable
              onClose={() => setErrorInfo({ type: null, message: '' })}
              className="mb-4"
              action={
                errorInfo.type === 'email_exists' && (
                  <Button size="small" type="link" onClick={() => navigate('/forgot-password')}>
                    忘记密码
                  </Button>
                )
              }
            />
          )}

          <Form
            form={form}
            name="register"
            onFinish={onFinish}
            scrollToFirstError
            layout="vertical"
            size="large"
          >
            <Form.Item
              name="account"
              label="账号"
              rules={[
                { required: true, message: '请输入账号（邮箱或手机号）' },
                {
                  validator: (_, value) => {
                    if (!value) return Promise.resolve()
                    // 检查是否是有效的邮箱或手机号
                    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
                    const isPhone = /^1[3-9]\d{9}$/.test(value)
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
                autoComplete="email"
                disabled={Boolean(inviteInfo?.email)}
              />
            </Form.Item>

            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 2, message: '用户名至少2个字符' },
                { max: 30, message: '用户名不能超过30个字符' },
                { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                autoComplete="username"
              />
            </Form.Item>

  
            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少8个字符' },
                { max: 50, message: '密码不能超过50个字符' },
                {
                  validator: (_, value) => {
                    if (!value) return Promise.resolve()
                    // 检查密码强度（至少包含两种不同类型的字符）
                    let score = 0
                    if (/[a-z]/.test(value)) score++ // 小写字母
                    if (/[A-Z]/.test(value)) score++ // 大写字母
                    if (/\d/.test(value)) score++ // 数字
                    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) score++ // 特殊字符

                    if (score < 2) {
                      return Promise.reject(new Error('密码至少包含以下两种字符：大小写字母、数字、特殊字符'))
                    }
                    return Promise.resolve()
                  }
                }
              ]}
              hasFeedback
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="new-password"
              />
            </Form.Item>

            <Form.Item
              name="confirm_password"
              label="确认密码"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'))
                  },
                }),
              ]}
              hasFeedback
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请再次输入密码"
                autoComplete="new-password"
              />
            </Form.Item>

            {/* 用户协议和隐私政策勾选框 */}
            <Form.Item
              name="agreement"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value
                      ? Promise.resolve()
                      : Promise.reject(new Error('请阅读并同意用户协议和隐私政策')),
                },
              ]}
            >
              <Checkbox>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  我已阅读并同意{' '}
                  <Link to="/terms-of-service" target="_blank" style={{ color: '#1890ff' }}>
                    《用户服务协议》
                  </Link>
                  {' '}和{' '}
                  <Link to="/privacy-policy" target="_blank" style={{ color: '#1890ff' }}>
                    《隐私政策》
                  </Link>
                </Text>
              </Checkbox>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                disabled={maintenanceMode || (!registrationEnabled && !inviteToken)}
              >
                {loading ? '注册中...' : '立即注册'}
              </Button>
            </Form.Item>
          </Form>

          <Divider>
            <Text type="secondary">已有账户？</Text>
          </Divider>

          <div className="text-center">
            <Space direction="vertical" size="small" className="w-full">
              <Text>
                已有账户？{' '}
                <Link to="/login" className="text-blue-600 hover:text-blue-800">
                  立即登录
                </Link>
              </Text>
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
              <Link to="/refund-policy" style={{ fontSize: '12px', color: '#8c8c8c' }}>
                退款政策
              </Link>
            </Space>
          </div>
        </Card>

        <div className="text-center mt-6">
          <Text type="secondary" className="text-sm">
            如遇问题，请联系客服支持
          </Text>
        </div>
      </div>

      {confirmLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="text-center p-8">
            <Spin size="large" />
            <div className="mt-4">
              <Text>正在注册您的账户，请稍候...</Text>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export default Register
