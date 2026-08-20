import React, { useEffect, useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  message,
  Row,
  Col,
  Space,
  Switch,
  Alert,
  List,
  Tag,
  Statistic,
  InputNumber,
  Spin,
  Divider,
  Modal,
} from 'antd'
import {
  SafetyOutlined,
  LockOutlined,
  MailOutlined,
  MobileOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { authService } from '@/services/auth'
import { securityService, SecurityOverview } from '@/services/security'
import { usePreferencesStore } from '@/store/preferencesStore'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography
const { Password } = Input

const SecuritySettingsPage: React.FC = () => {
  const [passwordForm] = Form.useForm()
  const [phoneForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [savingPrefs, setSavingPrefs] = useState(false)
  const [loadingOverview, setLoadingOverview] = useState(true)
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [overview, setOverview] = useState<SecurityOverview | null>(null)
  const [phoneModalOpen, setPhoneModalOpen] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [bindingPhone, setBindingPhone] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const setPreferences = usePreferencesStore((s) => s.setPreferences)
  const refreshUserInfo = useAuthStore((s) => s.refreshUserInfo)

  const loadOverview = async () => {
    setLoadingOverview(true)
    try {
      const data = await securityService.getOverview()
      setOverview(data)
      setPreferences({
        loginNotifications: data.loginNotifications,
        sessionTimeout: data.sessionTimeout,
        autoLogout: data.autoLogout,
        autoLogoutMinutes: data.autoLogoutMinutes,
      })
    } catch (error) {
      console.error(error)
      message.error('加载安全设置失败')
    } finally {
      setLoadingOverview(false)
    }
  }

  useEffect(() => {
    void loadOverview()
  }, [])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = window.setTimeout(() => setCountdown((c) => c - 1), 1000)
    return () => window.clearTimeout(timer)
  }, [countdown])

  const calculatePasswordStrength = (password: string) => {
    let strength = 0
    if (password.length >= 8) strength += 25
    if (/[a-z]/.test(password)) strength += 25
    if (/[A-Z]/.test(password)) strength += 25
    if (/[0-9]/.test(password)) strength += 12.5
    if (/[^a-zA-Z0-9]/.test(password)) strength += 12.5
    return strength
  }

  const handlePasswordChange = async (values: {
    currentPassword: string
    newPassword: string
    confirmPassword: string
  }) => {
    setLoading(true)
    try {
      const success = await authService.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
        confirm_password: values.confirmPassword,
      })
      if (!success) {
        message.error('密码修改失败，请确认当前密码是否正确')
        return
      }
      message.success('密码修改成功')
      passwordForm.resetFields()
      setPasswordStrength(0)
      await loadOverview()
    } catch (error: any) {
      message.error(error?.message || '密码修改失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const updateSecurityPref = async (
    patch: Partial<
      Pick<
        SecurityOverview,
        'loginNotifications' | 'sessionTimeout' | 'autoLogout' | 'autoLogoutMinutes'
      >
    >
  ) => {
    if (!overview) return
    const next = { ...overview, ...patch }
    setOverview(next)
    setPreferences(patch)
    setSavingPrefs(true)
    try {
      const saved = await securityService.updateSettings(patch)
      setOverview(saved)
      setPreferences({
        loginNotifications: saved.loginNotifications,
        sessionTimeout: saved.sessionTimeout,
        autoLogout: saved.autoLogout,
        autoLogoutMinutes: saved.autoLogoutMinutes,
      })
      message.success('安全偏好已保存')
    } catch (error) {
      message.error('保存失败，请稍后重试')
      await loadOverview()
    } finally {
      setSavingPrefs(false)
    }
  }

  const handleResendVerification = async () => {
    if (!overview?.email) return
    setLoading(true)
    try {
      const ok = await authService.resendVerificationEmail(overview.email)
      if (ok) {
        message.success('验证邮件已发送，请查收邮箱')
        await refreshUserInfo()
      } else {
        message.error('发送失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  const openPhoneModal = () => {
    phoneForm.resetFields()
    setCountdown(0)
    setPhoneModalOpen(true)
  }

  const handleSendPhoneCode = async () => {
    try {
      const phone = await phoneForm.validateFields(['phone']).then((v) => v.phone as string)
      setSendingCode(true)
      await securityService.sendPhoneBindCode({ phone })
      message.success('验证码已发送')
      setCountdown(60)
    } catch (error: any) {
      if (error?.errorFields) return
      // 接口错误已由 api 拦截器提示
    } finally {
      setSendingCode(false)
    }
  }

  const handleBindPhone = async () => {
    try {
      const values = await phoneForm.validateFields()
      setBindingPhone(true)
      await securityService.bindPhone({
        phone: values.phone,
        verification_code: values.verification_code,
        current_password: values.current_password,
      })
      message.success(overview?.phone ? '手机号换绑成功' : '手机号绑定成功')
      setPhoneModalOpen(false)
      phoneForm.resetFields()
      await Promise.all([loadOverview(), refreshUserInfo()])
    } catch (error: any) {
      if (error?.errorFields) return
      // 接口错误已由 api 拦截器提示
    } finally {
      setBindingPhone(false)
    }
  }

  const score = overview?.security_score ?? 0
  const hasPhone = Boolean(overview?.phone)

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>安全设置</Title>
        <Text type="secondary">管理密码、登录安全与近期登录活动</Text>
      </div>

      <Spin spinning={loadingOverview}>
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={[24, 16]} align="middle">
            <Col xs={24} md={8}>
              <Statistic
                title="安全评分"
                value={score}
                suffix="/ 100"
                valueStyle={{
                  color: score >= 80 ? '#52c41a' : score >= 60 ? '#fa8c16' : '#f5222d',
                }}
                prefix={<SafetyOutlined />}
              />
            </Col>
            <Col xs={24} md={16}>
              <Alert
                message={
                  score >= 80
                    ? '账户安全状况良好'
                    : score >= 60
                      ? '账户安全性中等，建议开启更多保护'
                      : '账户安全性较低，请尽快完善安全设置'
                }
                type={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'}
                showIcon
              />
            </Col>
          </Row>
        </Card>

        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <LockOutlined />
                  <span>修改密码</span>
                </Space>
              }
            >
              <Form form={passwordForm} layout="vertical" onFinish={handlePasswordChange}>
                <Form.Item
                  name="currentPassword"
                  label="当前密码"
                  rules={[{ required: true, message: '请输入当前密码' }]}
                >
                  <Password placeholder="请输入当前密码" prefix={<LockOutlined />} />
                </Form.Item>

                <Form.Item
                  name="newPassword"
                  label="新密码"
                  rules={[
                    { required: true, message: '请输入新密码' },
                    { min: 8, message: '密码至少8个字符' },
                  ]}
                >
                  <Password
                    placeholder="请输入新密码"
                    prefix={<LockOutlined />}
                    onChange={(e) =>
                      setPasswordStrength(calculatePasswordStrength(e.target.value))
                    }
                  />
                </Form.Item>

                {passwordStrength > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <Text type="secondary">密码强度</Text>
                    <div
                      style={{
                        marginTop: 6,
                        width: '100%',
                        height: 4,
                        backgroundColor: '#f0f0f0',
                        borderRadius: 2,
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${passwordStrength}%`,
                          height: '100%',
                          backgroundColor:
                            passwordStrength >= 75
                              ? '#52c41a'
                              : passwordStrength >= 50
                                ? '#fa8c16'
                                : '#f5222d',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>
                )}

                <Form.Item
                  name="confirmPassword"
                  label="确认新密码"
                  dependencies={['newPassword']}
                  rules={[
                    { required: true, message: '请确认新密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('newPassword') === value) {
                          return Promise.resolve()
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'))
                      },
                    }),
                  ]}
                >
                  <Password placeholder="请再次输入新密码" prefix={<LockOutlined />} />
                </Form.Item>

                <Button type="primary" htmlType="submit" loading={loading} block>
                  修改密码
                </Button>
              </Form>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <SafetyOutlined />
                  <span>账户与登录安全</span>
                </Space>
              }
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary">登录邮箱</Text>
                  <div>
                    <MailOutlined style={{ marginRight: 8 }} />
                    {overview?.email || '-'}
                    {overview?.is_verified ? (
                      <Tag color="success" style={{ marginLeft: 8 }}>
                        已验证
                      </Tag>
                    ) : (
                      <Tag color="warning" style={{ marginLeft: 8 }}>
                        未验证
                      </Tag>
                    )}
                  </div>
                  {!overview?.is_verified && overview?.email && (
                    <Button
                      type="link"
                      size="small"
                      style={{ paddingLeft: 0, marginTop: 4 }}
                      onClick={handleResendVerification}
                      loading={loading}
                    >
                      重新发送验证邮件
                    </Button>
                  )}
                </div>

                <div>
                  <Text type="secondary">绑定手机</Text>
                  <div>
                    <MobileOutlined style={{ marginRight: 8 }} />
                    {overview?.phone || '未绑定'}
                    {hasPhone ? (
                      <Tag color="success" style={{ marginLeft: 8 }}>
                        已绑定
                      </Tag>
                    ) : (
                      <Tag color="warning" style={{ marginLeft: 8 }}>
                        未绑定
                      </Tag>
                    )}
                  </div>
                  <Button
                    type="link"
                    size="small"
                    style={{ paddingLeft: 0, marginTop: 4 }}
                    onClick={openPhoneModal}
                  >
                    {hasPhone ? '换绑手机号' : '绑定手机号'}
                  </Button>
                </div>

                <Divider style={{ margin: '8px 0' }} />

                <div>
                  <Text type="secondary">最近登录</Text>
                  <div>
                    {overview?.last_login_at
                      ? dayjs(overview.last_login_at).format('YYYY-MM-DD HH:mm:ss')
                      : '暂无记录'}
                  </div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    IP：{overview?.last_login_ip || '-'}
                  </Text>
                </div>

                <Row justify="space-between" align="middle">
                  <Col>
                    <Text strong>登录通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      新设备登录时发送邮件提醒（需邮箱已验证）
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={!!overview?.loginNotifications}
                      loading={savingPrefs}
                      onChange={(checked) =>
                        void updateSecurityPref({ loginNotifications: checked })
                      }
                    />
                  </Col>
                </Row>

                <Row justify="space-between" align="middle">
                  <Col>
                    <Text strong>会话超时自动退出</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      长时间无操作后自动登出
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={!!overview?.sessionTimeout || !!overview?.autoLogout}
                      loading={savingPrefs}
                      onChange={(checked) =>
                        void updateSecurityPref({
                          sessionTimeout: checked,
                          autoLogout: checked,
                        })
                      }
                    />
                  </Col>
                </Row>

                {(overview?.sessionTimeout || overview?.autoLogout) && (
                  <Form.Item label="无操作自动退出时间（分钟）" style={{ marginBottom: 0 }}>
                    <InputNumber
                      min={5}
                      max={240}
                      value={overview?.autoLogoutMinutes || 30}
                      onChange={(value) => {
                        if (typeof value === 'number') {
                          void updateSecurityPref({ autoLogoutMinutes: value })
                        }
                      }}
                    />
                  </Form.Item>
                )}
              </Space>
            </Card>
          </Col>
        </Row>

        <Card
          style={{ marginTop: 24 }}
          title={
            <Space>
              <WarningOutlined />
              <span>近期登录活动</span>
            </Space>
          }
        >
          <List
            locale={{ emptyText: '暂无登录记录' }}
            dataSource={overview?.recent_logins || []}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Text>
                        {item.time
                          ? dayjs(item.time).format('YYYY-MM-DD HH:mm:ss')
                          : '-'}
                      </Text>
                      {item.status === 'failed' ? (
                        <Tag color="error">失败</Tag>
                      ) : item.message === 'password_changed' ? (
                        <Tag color="processing">改密</Tag>
                      ) : (
                        <Tag color="success" icon={<CheckCircleOutlined />}>
                          成功
                        </Tag>
                      )}
                    </Space>
                  }
                  description={
                    <Text type="secondary">
                      {item.device || '未知设备'} · IP {item.ip || '-'}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      </Spin>

      <Modal
        title={hasPhone ? '换绑手机号' : '绑定手机号'}
        open={phoneModalOpen}
        onCancel={() => setPhoneModalOpen(false)}
        onOk={() => void handleBindPhone()}
        confirmLoading={bindingPhone}
        okText={hasPhone ? '确认换绑' : '确认绑定'}
        destroyOnClose
      >
        <Form form={phoneForm} layout="vertical" style={{ marginTop: 8 }}>
          {hasPhone && (
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              message={`当前绑定：${overview?.phone}`}
              description="换绑需验证登录密码，并为新号码完成短信验证。"
            />
          )}
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的中国大陆手机号' },
            ]}
          >
            <Input prefix={<MobileOutlined />} placeholder="请输入要绑定的手机号" maxLength={11} />
          </Form.Item>
          <Form.Item label="短信验证码" required>
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item
                name="verification_code"
                noStyle
                rules={[
                  { required: true, message: '请输入验证码' },
                  { pattern: /^\d{6}$/, message: '验证码为6位数字' },
                ]}
              >
                <Input placeholder="请输入6位验证码" maxLength={6} style={{ width: '100%' }} />
              </Form.Item>
              <Button
                onClick={() => void handleSendPhoneCode()}
                loading={sendingCode}
                disabled={countdown > 0}
              >
                {countdown > 0 ? `${countdown}s` : '获取验证码'}
              </Button>
            </Space.Compact>
          </Form.Item>
          {hasPhone && (
            <Form.Item
              name="current_password"
              label="当前登录密码"
              rules={[{ required: true, message: '换绑请输入当前登录密码' }]}
            >
              <Password prefix={<LockOutlined />} placeholder="请输入当前登录密码" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default SecuritySettingsPage
