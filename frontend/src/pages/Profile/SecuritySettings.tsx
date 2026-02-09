import React, { useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  Divider,
  message,
  Row,
  Col,
  Space,
  Switch,
  Alert,
  List,
  Modal,
  QRCode,
  Tag,
  Statistic,
} from 'antd'
import {
  SafetyOutlined,
  LockOutlined,
  KeyOutlined,
  MobileOutlined,
  MailOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  QrcodeOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'

const { Title, Text, Paragraph } = Typography
const { Password } = Input

interface SecuritySettings {
  // 密码设置
  currentPassword: string
  newPassword: string
  confirmPassword: string

  // 两步验证设置
  twoFactorEnabled: boolean
  twoFactorSecret: string
  backupCodes: string[]

  // 登录安全
  loginNotifications: boolean
  sessionTimeout: boolean
  autoLogout: boolean
  autoLogoutMinutes: number

  // 应用安全
  apiAccessEnabled: boolean
  apiAccessToken: string
  trustedDevices: Device[]
}

interface Device {
  id: string
  name: string
  type: string
  lastUsed: string
  isCurrent: boolean
}

interface LoginLog {
  id: string
  time: string
  ip: string
  location: string
  device: string
  status: 'success' | 'failed'
}

const SecuritySettingsPage: React.FC = () => {
  const { user } = useAuthStore()
  const [passwordForm] = Form.useForm()
  const [twoFactorForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [showQRCodeModal, setShowQRCodeModal] = useState(false)
  const [showBackupCodesModal, setShowBackupCodesModal] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(0)

  // 模拟数据
  const [settings, setSettings] = useState<SecuritySettings>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    twoFactorEnabled: false,
    twoFactorSecret: 'JBSWY3DPEHPK3PXP',
    backupCodes: [
      '12345678', '87654321', '11223344', '44332211',
      '55667788', '88776655', '99887766', '66778899',
      '12121212', '34343434', '56565656', '78787878'
    ],
    loginNotifications: true,
    sessionTimeout: true,
    autoLogout: false,
    autoLogoutMinutes: 30,
    apiAccessEnabled: false,
    apiAccessToken: '',
    trustedDevices: [
      {
        id: '1',
        name: 'Chrome - Windows',
        type: 'desktop',
        lastUsed: '2024-01-20 14:30:00',
        isCurrent: true,
      },
      {
        id: '2',
        name: 'Safari - iPhone',
        type: 'mobile',
        lastUsed: '2024-01-19 09:15:00',
        isCurrent: false,
      },
    ],
  })

  // 模拟登录日志
  const [loginLogs] = useState<LoginLog[]>([
    {
      id: '1',
      time: '2024-01-20 14:30:00',
      ip: '192.168.1.100',
      location: '北京市朝阳区',
      device: 'Chrome - Windows',
      status: 'success',
    },
    {
      id: '2',
      time: '2024-01-20 09:15:00',
      ip: '192.168.1.100',
      location: '北京市朝阳区',
      device: 'Safari - iPhone',
      status: 'success',
    },
    {
      id: '3',
      time: '2024-01-19 23:45:00',
      ip: '10.0.0.1',
      location: '上海市浦东新区',
      device: 'Firefox - Windows',
      status: 'failed',
    },
  ])

  // 计算密码强度
  const calculatePasswordStrength = (password: string) => {
    let strength = 0
    if (password.length >= 8) strength += 25
    if (/[a-z]/.test(password)) strength += 25
    if (/[A-Z]/.test(password)) strength += 25
    if (/[0-9]/.test(password)) strength += 12.5
    if (/[^a-zA-Z0-9]/.test(password)) strength += 12.5
    return strength
  }

  // 处理密码更改
  const handlePasswordChange = async (values: any) => {
    setLoading(true)
    try {
      // 这里应该调用API更改密码
      // const success = await authService.changePassword(values)

      message.success('密码修改成功')
      passwordForm.resetFields()
      setPasswordStrength(0)
    } catch (error) {
      message.error('密码修改失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 处理两步验证切换
  const handleTwoFactorToggle = async (enabled: boolean) => {
    try {
      if (enabled) {
        setShowQRCodeModal(true)
      } else {
        // 禁用两步验证需要验证当前密码
        Modal.confirm({
          title: '确认禁用两步验证',
          content: '禁用两步验证会降低账户安全性，确定要继续吗？',
          okText: '确定',
          cancelText: '取消',
          onOk: async () => {
            // 调用API禁用两步验证
            setSettings(prev => ({ ...prev, twoFactorEnabled: false }))
            message.success('两步验证已禁用')
          },
        })
      }
    } catch (error) {
      message.error('操作失败，请稍后重试')
    }
  }

  // 启用两步验证
  const handleEnableTwoFactor = async (values: any) => {
    setLoading(true)
    try {
      // 这里应该调用API验证两步验证码并启用
      setSettings(prev => ({ ...prev, twoFactorEnabled: true }))
      setShowQRCodeModal(false)
      message.success('两步验证已启用')
      twoFactorForm.resetFields()
    } catch (error) {
      message.error('验证码错误，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 移除信任设备
  const handleRemoveDevice = async (deviceId: string) => {
    try {
      // 调用API移除设备
      setSettings(prev => ({
        ...prev,
        trustedDevices: prev.trustedDevices.filter(d => d.id !== deviceId)
      }))
      message.success('设备已移除')
    } catch (error) {
      message.error('移除失败，请稍后重试')
    }
  }

  // 生成新的API令牌
  const handleGenerateApiToken = async () => {
    try {
      // 调用API生成新令牌
      const newToken = 'sk_' + Math.random().toString(36).substring(2, 15)
      setSettings(prev => ({ ...prev, apiAccessToken: newToken }))
      message.success('API令牌已生成')
    } catch (error) {
      message.error('生成失败，请稍后重试')
    }
  }

  // 复制到剪贴板
  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const getSecurityScore = () => {
    let score = 0
    if (settings.twoFactorEnabled) score += 30
    if (settings.loginNotifications) score += 20
    if (settings.sessionTimeout) score += 20
    if (settings.autoLogout) score += 15
    if (settings.trustedDevices.length <= 2) score += 15
    return score
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>安全设置</Title>
        <Text type="secondary">管理您的账户安全和隐私设置</Text>
      </div>

      {/* 安全评分 */}
      <Card className="mb-6">
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} md={8}>
            <Statistic
              title="安全评分"
              value={getSecurityScore()}
              suffix="/ 100"
              valueStyle={{
                color: getSecurityScore() >= 80 ? '#52c41a' :
                       getSecurityScore() >= 60 ? '#fa8c16' : '#f5222d'
              }}
              prefix={<SafetyOutlined />}
            />
          </Col>
          <Col xs={24} md={16}>
            <Alert
              message={getSecurityScore() >= 80 ? '账户安全状况良好' :
                      getSecurityScore() >= 60 ? '账户安全性中等，建议加强' :
                      '账户安全性较低，请立即加强安全设置'}
              type={getSecurityScore() >= 80 ? 'success' :
                    getSecurityScore() >= 60 ? 'warning' : 'error'}
              showIcon
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={[24, 24]}>
        {/* 密码设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <LockOutlined />
                <span>密码设置</span>
              </Space>
            }
          >
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordChange}
            >
              <Form.Item
                name="currentPassword"
                label="当前密码"
                rules={[{ required: true, message: '请输入当前密码' }]}
              >
                <Password
                  placeholder="请输入当前密码"
                  visibilityToggle={{
                    visible: showCurrentPassword,
                    onVisibleChange: setShowCurrentPassword,
                  }}
                  prefix={<LockOutlined />}
                />
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
                  visibilityToggle={{
                    visible: showNewPassword,
                    onVisibleChange: setShowNewPassword,
                  }}
                  prefix={<LockOutlined />}
                  onChange={(e) => setPasswordStrength(calculatePasswordStrength(e.target.value))}
                />
              </Form.Item>

              {passwordStrength > 0 && (
                <div className="mb-4">
                  <Text type="secondary">密码强度：</Text>
                  <div
                    className="mt-1"
                    style={{
                      width: '100%',
                      height: '4px',
                      backgroundColor: '#f0f0f0',
                      borderRadius: '2px',
                      overflow: 'hidden'
                    }}
                  >
                    <div
                      style={{
                        width: `${passwordStrength}%`,
                        height: '100%',
                        backgroundColor: passwordStrength >= 75 ? '#52c41a' :
                                        passwordStrength >= 50 ? '#fa8c16' : '#f5222d',
                        transition: 'width 0.3s ease'
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
                <Password
                  placeholder="请再次输入新密码"
                  visibilityToggle={{
                    visible: showConfirmPassword,
                    onVisibleChange: setShowConfirmPassword,
                  }}
                  prefix={<LockOutlined />}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<LockOutlined />}
                  loading={loading}
                  block
                >
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 两步验证 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <MobileOutlined />
                <span>两步验证</span>
              </Space>
            }
          >
            <div className="mb-4">
              <Row justify="space-between" align="middle">
                <Col>
                  <Text>启用两步验证可以为您的账户提供额外的安全保护。</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.twoFactorEnabled}
                    onChange={handleTwoFactorToggle}
                  />
                </Col>
              </Row>
            </div>

            {settings.twoFactorEnabled && (
              <Alert
                message="两步验证已启用"
                description="您的账户已启用两步验证保护"
                type="success"
                showIcon
                icon={<CheckCircleOutlined />}
                className="mb-4"
              />
            )}

            {settings.twoFactorEnabled && (
              <div className="text-center">
                <Button
                  icon={<QrcodeOutlined />}
                  onClick={() => setShowBackupCodesModal(true)}
                >
                  查看备用恢复码
                </Button>
              </div>
            )}
          </Card>
        </Col>

        {/* 登录安全 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SafetyOutlined />
                <span>登录安全</span>
              </Space>
            }
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>登录通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      当账户在新设备登录时发送邮件通知
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.loginNotifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, loginNotifications: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>会话超时</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      长时间不活动时自动登出
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.sessionTimeout}
                    onChange={(checked) => setSettings(prev => ({ ...prev, sessionTimeout: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>自动登出</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      设定自动登出时间（分钟）
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.autoLogout}
                    onChange={(checked) => setSettings(prev => ({ ...prev, autoLogout: checked }))}
                  />
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 信任设备 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <MobileOutlined />
                <span>信任设备</span>
              </Space>
            }
          >
            <List
              dataSource={settings.trustedDevices}
              renderItem={(device) => (
                <List.Item
                  actions={[
                    device.isCurrent && <Tag color="green">当前设备</Tag>,
                    !device.isCurrent && (
                      <Button
                        size="small"
                        danger
                        onClick={() => handleRemoveDevice(device.id)}
                      >
                        移除
                      </Button>
                    ),
                  ].filter(Boolean)}
                >
                  <List.Item.Meta
                    title={device.name}
                    description={
                      <Space direction="vertical" size="small">
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          最后使用：{device.lastUsed}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          类型：{device.type === 'desktop' ? '桌面设备' : '移动设备'}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 两步验证二维码模态框 */}
      <Modal
        title="启用两步验证"
        open={showQRCodeModal}
        onCancel={() => setShowQRCodeModal(false)}
        footer={null}
        width={480}
      >
        <div className="text-center mb-4">
          <Paragraph>
            请使用认证器应用（如 Google Authenticator、Microsoft Authenticator）扫描下方二维码
          </Paragraph>
          <div className="flex justify-center mb-4">
            <QRCode value={`otpauth://totp/WeldingSystem:${user?.email}?secret=${settings.twoFactorSecret}&issuer=WeldingSystem`} />
          </div>
          <Space direction="vertical" size="small" className="mb-4">
            <Text strong>或手动输入密钥：</Text>
            <Space>
              <Text code>{settings.twoFactorSecret}</Text>
              <Button
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyToClipboard(settings.twoFactorSecret)}
              />
            </Space>
          </Space>
        </div>

        <Form
          form={twoFactorForm}
          layout="vertical"
          onFinish={handleEnableTwoFactor}
        >
          <Form.Item
            name="verificationCode"
            label="验证码"
            rules={[{ required: true, message: '请输入验证码' }]}
          >
            <Input
              placeholder="请输入6位验证码"
              maxLength={6}
              style={{ textAlign: 'center' }}
            />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Button onClick={() => setShowQRCodeModal(false)}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
              >
                启用两步验证
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 备用恢复码模态框 */}
      <Modal
        title="备用恢复码"
        open={showBackupCodesModal}
        onCancel={() => setShowBackupCodesModal(false)}
        footer={[
          <Button key="close" onClick={() => setShowBackupCodesModal(false)}>
            关闭
          </Button>,
          <Button
            key="copy"
            type="primary"
            icon={<CopyOutlined />}
            onClick={() => handleCopyToClipboard(settings.backupCodes.join('\n'))}
          >
            复制所有代码
          </Button>,
        ]}
        width={640}
      >
        <Alert
          message="请妥善保存这些恢复码"
          description="当您无法使用认证器应用时，可以使用这些代码来登录您的账户。每个代码只能使用一次。"
          type="warning"
          showIcon
          className="mb-4"
        />

        <Row gutter={[16, 16]}>
          {settings.backupCodes.map((code, index) => (
            <Col xs={12} sm={8} md={6} key={index}>
              <Input value={code} readOnly style={{ textAlign: 'center' }} />
            </Col>
          ))}
        </Row>
      </Modal>
    </div>
  )
}

export default SecuritySettingsPage