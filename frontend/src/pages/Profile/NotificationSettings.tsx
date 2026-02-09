import React, { useState } from 'react'
import {
  Card,
  Typography,
  Switch,
  Button,
  Divider,
  message,
  Row,
  Col,
  Space,
  Select,
  TimePicker,
  InputNumber,
  Form,
  Table,
  Tag,
  Alert,
  Badge,
  List,
  Avatar,
} from 'antd'
import {
  BellOutlined,
  MailOutlined,
  MobileOutlined,
  DesktopOutlined,
  SoundOutlined,
  EyeOutlined,
  DeleteOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select

interface NotificationSettings {
  // 通知方式
  emailNotifications: boolean
  pushNotifications: boolean
  smsNotifications: boolean
  desktopNotifications: boolean

  // 通知时间段
  quietHoursEnabled: boolean
  quietHoursStart: string
  quietHoursEnd: string

  // 系统通知
  systemUpdates: boolean
  securityAlerts: boolean
  maintenance: boolean

  // 业务通知
  wpsUpdates: boolean
  pqrApprovals: boolean
  qualityAlerts: boolean
  equipmentMaintenance: boolean
  materialAlerts: boolean
  welderCertifications: boolean
  productionDeadlines: boolean

  // 邮件通知偏好
  emailDigestFrequency: 'immediate' | 'daily' | 'weekly' | 'never'
  emailCategories: string[]
}

interface NotificationRecord {
  id: string
  type: 'system' | 'business' | 'security' | 'reminder'
  title: string
  message: string
  time: string
  read: boolean
  priority: 'high' | 'medium' | 'low'
}

const NotificationSettingsPage: React.FC = () => {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('settings')

  const [settings, setSettings] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    desktopNotifications: true,
    quietHoursEnabled: false,
    quietHoursStart: '22:00',
    quietHoursEnd: '08:00',
    systemUpdates: true,
    securityAlerts: true,
    maintenance: true,
    wpsUpdates: true,
    pqrApprovals: true,
    qualityAlerts: true,
    equipmentMaintenance: true,
    materialAlerts: true,
    welderCertifications: true,
    productionDeadlines: true,
    emailDigestFrequency: 'immediate',
    emailCategories: ['all'],
  })

  // 模拟通知记录
  const [notifications, setNotifications] = useState<NotificationRecord[]>([
    {
      id: '1',
      type: 'system',
      title: '系统维护通知',
      message: '系统将于今晚23:00进行例行维护，预计持续2小时',
      time: '2024-01-20 18:30:00',
      read: false,
      priority: 'high',
    },
    {
      id: '2',
      type: 'business',
      title: 'WPS文档审核通过',
      message: '您提交的WPS-2024-001文档已通过审核',
      time: '2024-01-20 16:45:00',
      read: false,
      priority: 'medium',
    },
    {
      id: '3',
      type: 'security',
      title: '登录异常提醒',
      message: '检测到您的账户在新设备登录，请确认是否为本人操作',
      time: '2024-01-20 14:20:00',
      read: true,
      priority: 'high',
    },
    {
      id: '4',
      type: 'reminder',
      title: '设备维护提醒',
      message: '焊机W-001需要进行定期维护',
      time: '2024-01-20 10:15:00',
      read: true,
      priority: 'medium',
    },
    {
      id: '5',
      type: 'business',
      title: '质量检验报告',
      message: '新的质量检验报告已生成，请及时查看',
      time: '2024-01-20 09:30:00',
      read: false,
      priority: 'low',
    },
  ])

  // 处理设置保存
  const handleSave = async () => {
    setLoading(true)
    try {
      // 这里应该调用API保存通知设置
      // const success = await notificationSettingsService.updateSettings(settings)

      message.success('通知设置保存成功')
    } catch (error) {
      message.error('保存失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 处理通知标记已读
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      setNotifications(prev =>
        prev.map(notification =>
          notification.id === notificationId
            ? { ...notification, read: true }
            : notification
        )
      )
      message.success('已标记为已读')
    } catch (error) {
      message.error('操作失败，请稍后重试')
    }
  }

  // 处理删除通知
  const handleDeleteNotification = async (notificationId: string) => {
    try {
      setNotifications(prev =>
        prev.filter(notification => notification.id !== notificationId)
      )
      message.success('通知已删除')
    } catch (error) {
      message.error('删除失败，请稍后重试')
    }
  }

  // 批量标记已读
  const handleMarkAllAsRead = async () => {
    try {
      setNotifications(prev =>
        prev.map(notification => ({ ...notification, read: true }))
      )
      message.success('所有通知已标记为已读')
    } catch (error) {
      message.error('操作失败，请稍后重试')
    }
  }

  // 清空所有通知
  const handleClearAllNotifications = async () => {
    try {
      setNotifications([])
      message.success('所有通知已清空')
    } catch (error) {
      message.error('清空失败，请稍后重试')
    }
  }

  // 获取通知类型图标
  const getNotificationIcon = (type: string) => {
    const iconMap = {
      system: <DesktopOutlined style={{ color: '#1890ff' }} />,
      business: <InfoCircleOutlined style={{ color: '#52c41a' }} />,
      security: <ExclamationCircleOutlined style={{ color: '#f5222d' }} />,
      reminder: <BellOutlined style={{ color: '#fa8c16' }} />,
    }
    return iconMap[type as keyof typeof iconMap] || <BellOutlined />
  }

  // 获取优先级标签
  const getPriorityTag = (priority: string) => {
    const config = {
      high: { color: 'red', text: '高' },
      medium: { color: 'orange', text: '中' },
      low: { color: 'green', text: '低' },
    }
    return config[priority as keyof typeof config]
  }

  // 未读通知数量
  const unreadCount = notifications.filter(n => !n.read).length

  const notificationColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => getNotificationIcon(type),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: NotificationRecord) => (
        <Space direction="vertical" size="small">
          <Text strong={!record.read}>{title}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.message}
          </Text>
        </Space>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const config = getPriorityTag(priority)
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 180,
      render: (time: string) => dayjs(time).format('MM-DD HH:mm'),
    },
    {
      title: '状态',
      dataIndex: 'read',
      key: 'read',
      width: 80,
      render: (read: boolean) => (
        <Tag color={read ? 'default' : 'processing'}>
          {read ? '已读' : '未读'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: NotificationRecord) => (
        <Space size="small">
          {!record.read && (
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleMarkAsRead(record.id)}
            />
          )}
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDeleteNotification(record.id)}
          />
        </Space>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>通知设置</Title>
        <Text type="secondary">管理您的通知偏好和消息中心</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div className="text-center">
              <Badge count={unreadCount} size="small">
                <BellOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              </Badge>
              <div className="mt-2">
                <Text type="secondary">未读通知</Text>
                <Title level={3} className="mt-0">{unreadCount}</Title>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div className="text-center">
              <MailOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
              <div className="mt-2">
                <Text type="secondary">邮件通知</Text>
                <Title level={3} className="mt-0">
                  {settings.emailNotifications ? '已开启' : '已关闭'}
                </Title>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div className="text-center">
              <MobileOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />
              <div className="mt-2">
                <Text type="secondary">推送通知</Text>
                <Title level={3} className="mt-0">
                  {settings.pushNotifications ? '已开启' : '已关闭'}
                </Title>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <div className="text-center">
              <DesktopOutlined style={{ fontSize: '24px', color: '#722ed1' }} />
              <div className="mt-2">
                <Text type="secondary">桌面通知</Text>
                <Title level={3} className="mt-0">
                  {settings.desktopNotifications ? '已开启' : '已关闭'}
                </Title>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 通知方式设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <BellOutlined />
                <span>通知方式</span>
              </Space>
            }
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>邮件通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      通过邮件接收重要通知
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.emailNotifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, emailNotifications: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>推送通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      在浏览器中接收推送通知
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.pushNotifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, pushNotifications: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>短信通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      通过短信接收紧急通知
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.smsNotifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, smsNotifications: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>桌面通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      在桌面显示通知弹窗
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.desktopNotifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, desktopNotifications: checked }))}
                  />
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 通知时间段设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SoundOutlined />
                <span>免打扰时间</span>
              </Space>
            }
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <div>
                    <Text strong>启用免打扰</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      在指定时间段内静音通知
                    </Text>
                  </div>
                </Col>
                <Col>
                  <Switch
                    checked={settings.quietHoursEnabled}
                    onChange={(checked) => setSettings(prev => ({ ...prev, quietHoursEnabled: checked }))}
                  />
                </Col>
              </Row>

              {settings.quietHoursEnabled && (
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Text>开始时间：</Text>
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      value={dayjs(settings.quietHoursStart, 'HH:mm')}
                      onChange={(time) => setSettings(prev => ({
                        ...prev,
                        quietHoursStart: time ? time.format('HH:mm') : '22:00'
                      }))}
                    />
                  </Col>
                  <Col xs={24} md={12}>
                    <Text>结束时间：</Text>
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      value={dayjs(settings.quietHoursEnd, 'HH:mm')}
                      onChange={(time) => setSettings(prev => ({
                        ...prev,
                        quietHoursEnd: time ? time.format('HH:mm') : '08:00'
                      }))}
                    />
                  </Col>
                </Row>
              )}
            </Space>
          </Card>
        </Col>

        {/* 系统通知设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <DesktopOutlined />
                <span>系统通知</span>
              </Space>
            }
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <Text>系统更新</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.systemUpdates}
                    onChange={(checked) => setSettings(prev => ({ ...prev, systemUpdates: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>安全警报</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.securityAlerts}
                    onChange={(checked) => setSettings(prev => ({ ...prev, securityAlerts: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>维护通知</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.maintenance}
                    onChange={(checked) => setSettings(prev => ({ ...prev, maintenance: checked }))}
                  />
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 业务通知设置 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SettingOutlined />
                <span>业务通知</span>
              </Space>
            }
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row justify="space-between" align="middle">
                <Col>
                  <Text>WPS更新</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.wpsUpdates}
                    onChange={(checked) => setSettings(prev => ({ ...prev, wpsUpdates: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>PQR审批</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.pqrApprovals}
                    onChange={(checked) => setSettings(prev => ({ ...prev, pqrApprovals: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>质量警报</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.qualityAlerts}
                    onChange={(checked) => setSettings(prev => ({ ...prev, qualityAlerts: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>设备维护</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.equipmentMaintenance}
                    onChange={(checked) => setSettings(prev => ({ ...prev, equipmentMaintenance: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>材料警报</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.materialAlerts}
                    onChange={(checked) => setSettings(prev => ({ ...prev, materialAlerts: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>焊工资质</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.welderCertifications}
                    onChange={(checked) => setSettings(prev => ({ ...prev, welderCertifications: checked }))}
                  />
                </Col>
              </Row>

              <Row justify="space-between" align="middle">
                <Col>
                  <Text>生产截止日期</Text>
                </Col>
                <Col>
                  <Switch
                    checked={settings.productionDeadlines}
                    onChange={(checked) => setSettings(prev => ({ ...prev, productionDeadlines: checked }))}
                  />
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        {/* 邮件通知偏好 */}
        <Col xs={24}>
          <Card
            title={
              <Space>
                <MailOutlined />
                <span>邮件通知偏好</span>
              </Space>
            }
          >
            <Row gutter={[24, 16]}>
              <Col xs={24} md={12}>
                <Text strong>邮件摘要频率：</Text>
                <Select
                  value={settings.emailDigestFrequency}
                  onChange={(value) => setSettings(prev => ({ ...prev, emailDigestFrequency: value }))}
                  style={{ width: '100%', marginTop: 8 }}
                >
                  <Option value="immediate">立即发送</Option>
                  <Option value="daily">每日摘要</Option>
                  <Option value="weekly">每周摘要</Option>
                  <Option value="never">不发送</Option>
                </Select>
              </Col>
              <Col xs={24} md={12}>
                <Text strong>通知邮箱：</Text>
                <div style={{ marginTop: 8 }}>
                  <Text>{user?.email}</Text>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 最近通知 */}
        <Col xs={24}>
          <Card
            title={
              <Space>
                <BellOutlined />
                <span>最近通知</span>
                <Badge count={unreadCount} size="small" />
              </Space>
            }
            extra={
              <Space>
                <Button size="small" onClick={handleMarkAllAsRead}>
                  全部已读
                </Button>
                <Button size="small" onClick={handleClearAllNotifications}>
                  清空全部
                </Button>
              </Space>
            }
          >
            <Table
              columns={notificationColumns}
              dataSource={notifications}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      <Divider />

      <div className="text-right">
        <Button
          type="primary"
          icon={<CheckCircleOutlined />}
          loading={loading}
          onClick={handleSave}
        >
          保存设置
        </Button>
      </div>
    </div>
  )
}

export default NotificationSettingsPage