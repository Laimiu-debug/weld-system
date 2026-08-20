import React, { useCallback, useEffect, useState } from 'react'
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
  Table,
  Tag,
  Badge,
  Spin,
  Modal,
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
import { usePreferencesStore } from '@/store/preferencesStore'
import {
  clearAllNotifications,
  deleteNotification,
  getNotifications,
  markAllAsRead,
  markAsRead,
  type Notification,
} from '@/services/notifications'
import type { EmailDigestFrequency, UserSystemPreferences } from '@/types/preferences'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select

type NotificationPrefKey = keyof Pick<
  UserSystemPreferences,
  | 'emailNotifications'
  | 'pushNotifications'
  | 'smsNotifications'
  | 'desktopNotifications'
  | 'quietHoursEnabled'
  | 'quietHoursStart'
  | 'quietHoursEnd'
  | 'systemUpdates'
  | 'securityAlerts'
  | 'maintenance'
  | 'wpsUpdates'
  | 'pqrApprovals'
  | 'qualityAlerts'
  | 'equipmentMaintenance'
  | 'materialAlerts'
  | 'welderCertifications'
  | 'productionDeadlines'
  | 'emailDigestFrequency'
>

const NotificationSettingsPage: React.FC = () => {
  const { user } = useAuthStore()
  const preferences = usePreferencesStore((s) => s.preferences)
  const setPreferences = usePreferencesStore((s) => s.setPreferences)
  const saveToServer = usePreferencesStore((s) => s.saveToServer)
  const loadFromServer = usePreferencesStore((s) => s.loadFromServer)

  const [loading, setLoading] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const loadNotifications = useCallback(async (nextPage = page, nextSize = pageSize) => {
    setListLoading(true)
    try {
      const data = await getNotifications({
        page: nextPage,
        page_size: nextSize,
      })
      setNotifications(data.items || [])
      setUnreadCount(data.unread_count || 0)
      setTotal(data.total || 0)
    } catch (error) {
      console.error(error)
      message.error('加载通知列表失败')
    } finally {
      setListLoading(false)
    }
  }, [page, pageSize])

  useEffect(() => {
    void loadFromServer()
  }, [loadFromServer])

  useEffect(() => {
    void loadNotifications(page, pageSize)
  }, [page, pageSize, loadNotifications])

  const patchSetting = <K extends NotificationPrefKey>(key: K, value: UserSystemPreferences[K]) => {
    setPreferences({ [key]: value } as Partial<UserSystemPreferences>)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveToServer()
      if (preferences.desktopNotifications && 'Notification' in window) {
        if (Notification.permission === 'default') {
          await Notification.requestPermission()
        }
      }
      message.success('通知设置保存成功')
    } catch (error) {
      message.error('保存失败，请稍后重试')
    } finally {
      setSaving(false)
    }
  }

  const handleMarkAsRead = async (notificationId: number) => {
    setLoading(true)
    try {
      await markAsRead(notificationId)
      message.success('已标记为已读')
      await loadNotifications()
    } catch (error) {
      // api 拦截器已提示
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteNotification = async (notificationId: number) => {
    setLoading(true)
    try {
      await deleteNotification(notificationId)
      message.success('通知已删除')
      await loadNotifications()
    } catch (error) {
      // api 拦截器已提示
    } finally {
      setLoading(false)
    }
  }

  const handleMarkAllAsRead = async () => {
    setLoading(true)
    try {
      await markAllAsRead()
      message.success('所有通知已标记为已读')
      await loadNotifications()
    } catch (error) {
      // api 拦截器已提示
    } finally {
      setLoading(false)
    }
  }

  const handleClearAllNotifications = () => {
    Modal.confirm({
      title: '确认清空全部通知？',
      content: '清空后可在新通知到达时重新显示，此操作仅影响当前账号。',
      okText: '清空',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true)
        try {
          await clearAllNotifications()
          message.success('所有通知已清空')
          await loadNotifications(1, pageSize)
          setPage(1)
        } finally {
          setLoading(false)
        }
      },
    })
  }

  const getNotificationIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      info: <InfoCircleOutlined style={{ color: '#1F5EFF' }} />,
      success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      warning: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
      error: <ExclamationCircleOutlined style={{ color: '#f5222d' }} />,
      maintenance: <DesktopOutlined style={{ color: '#722ed1' }} />,
    }
    return iconMap[type] || <BellOutlined />
  }

  const getPriorityTag = (priority: string) => {
    const config: Record<string, { color: string; text: string }> = {
      urgent: { color: 'red', text: '紧急' },
      high: { color: 'red', text: '高' },
      normal: { color: 'orange', text: '中' },
      medium: { color: 'orange', text: '中' },
      low: { color: 'green', text: '低' },
    }
    return config[priority] || { color: 'default', text: priority || '普通' }
  }

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
      render: (title: string, record: Notification) => (
        <Space direction="vertical" size={0}>
          <Text strong={!record.is_read}>{title}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.content}
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
      dataIndex: 'publish_at',
      key: 'publish_at',
      width: 160,
      render: (time: string | null, record: Notification) =>
        dayjs(time || record.created_at || undefined).format('MM-DD HH:mm'),
    },
    {
      title: '状态',
      dataIndex: 'is_read',
      key: 'is_read',
      width: 80,
      render: (read: boolean) => (
        <Tag color={read ? 'default' : 'processing'}>{read ? '已读' : '未读'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: Notification) => (
        <Space size="small">
          {!record.is_read && (
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => void handleMarkAsRead(record.id)}
            />
          )}
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => void handleDeleteNotification(record.id)}
          />
        </Space>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>通知设置</Title>
        <Text type="secondary">管理通知偏好，并查看真实消息中心记录</Text>
      </div>

      <Spin spinning={listLoading && notifications.length === 0}>
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={24} sm={12} md={6}>
            <Card>
              <div className="text-center">
                <Badge count={unreadCount} size="small">
                  <BellOutlined style={{ fontSize: 24, color: '#1F5EFF' }} />
                </Badge>
                <div className="mt-2">
                  <Text type="secondary">未读通知</Text>
                  <Title level={3} className="mt-0">
                    {unreadCount}
                  </Title>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <div className="text-center">
                <MailOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                <div className="mt-2">
                  <Text type="secondary">邮件通知</Text>
                  <Title level={3} className="mt-0">
                    {preferences.emailNotifications ? '已开启' : '已关闭'}
                  </Title>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <div className="text-center">
                <MobileOutlined style={{ fontSize: 24, color: '#fa8c16' }} />
                <div className="mt-2">
                  <Text type="secondary">推送通知</Text>
                  <Title level={3} className="mt-0">
                    {preferences.pushNotifications ? '已开启' : '已关闭'}
                  </Title>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <div className="text-center">
                <DesktopOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                <div className="mt-2">
                  <Text type="secondary">桌面通知</Text>
                  <Title level={3} className="mt-0">
                    {preferences.desktopNotifications ? '已开启' : '已关闭'}
                  </Title>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        <Row gutter={[24, 24]}>
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
                    <Text strong>邮件通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      通过邮件接收重要通知
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.emailNotifications}
                      onChange={(checked) => patchSetting('emailNotifications', checked)}
                    />
                  </Col>
                </Row>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Text strong>推送通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      在浏览器中接收推送通知
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.pushNotifications}
                      onChange={(checked) => patchSetting('pushNotifications', checked)}
                    />
                  </Col>
                </Row>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Text strong>短信通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      紧急通知时发送短信（需已绑定手机）
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.smsNotifications}
                      onChange={(checked) => patchSetting('smsNotifications', checked)}
                    />
                  </Col>
                </Row>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Text strong>桌面通知</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      允许浏览器桌面弹窗
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.desktopNotifications}
                      onChange={(checked) => patchSetting('desktopNotifications', checked)}
                    />
                  </Col>
                </Row>
              </Space>
            </Card>
          </Col>

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
                    <Text strong>启用免打扰</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      时段内不发送邮件/短信/推送；站内信仍会保留
                    </Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.quietHoursEnabled}
                      onChange={(checked) => patchSetting('quietHoursEnabled', checked)}
                    />
                  </Col>
                </Row>
                {preferences.quietHoursEnabled && (
                  <Row gutter={[16, 16]}>
                    <Col xs={24} md={12}>
                      <Text>开始时间：</Text>
                      <TimePicker
                        format="HH:mm"
                        style={{ width: '100%' }}
                        value={dayjs(preferences.quietHoursStart, 'HH:mm')}
                        onChange={(time) =>
                          patchSetting('quietHoursStart', time ? time.format('HH:mm') : '22:00')
                        }
                      />
                    </Col>
                    <Col xs={24} md={12}>
                      <Text>结束时间：</Text>
                      <TimePicker
                        format="HH:mm"
                        style={{ width: '100%' }}
                        value={dayjs(preferences.quietHoursEnd, 'HH:mm')}
                        onChange={(time) =>
                          patchSetting('quietHoursEnd', time ? time.format('HH:mm') : '08:00')
                        }
                      />
                    </Col>
                  </Row>
                )}
              </Space>
            </Card>
          </Col>

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
                      checked={preferences.systemUpdates}
                      onChange={(checked) => patchSetting('systemUpdates', checked)}
                    />
                  </Col>
                </Row>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Text>安全警报</Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.securityAlerts}
                      onChange={(checked) => patchSetting('securityAlerts', checked)}
                    />
                  </Col>
                </Row>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Text>维护通知</Text>
                  </Col>
                  <Col>
                    <Switch
                      checked={preferences.maintenance}
                      onChange={(checked) => patchSetting('maintenance', checked)}
                    />
                  </Col>
                </Row>
              </Space>
            </Card>
          </Col>

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
                {(
                  [
                    ['wpsUpdates', 'WPS更新'],
                    ['pqrApprovals', 'PQR/审批'],
                    ['qualityAlerts', '质量警报'],
                    ['equipmentMaintenance', '设备维护'],
                    ['materialAlerts', '材料警报'],
                    ['welderCertifications', '焊工资质'],
                    ['productionDeadlines', '生产截止日期'],
                  ] as Array<[NotificationPrefKey, string]>
                ).map(([key, label]) => (
                  <Row justify="space-between" align="middle" key={key}>
                    <Col>
                      <Text>{label}</Text>
                    </Col>
                    <Col>
                      <Switch
                        checked={Boolean(preferences[key])}
                        onChange={(checked) => patchSetting(key, checked as never)}
                      />
                    </Col>
                  </Row>
                ))}
              </Space>
            </Card>
          </Col>

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
                    value={preferences.emailDigestFrequency}
                    onChange={(value: EmailDigestFrequency) =>
                      patchSetting('emailDigestFrequency', value)
                    }
                    style={{ width: '100%', marginTop: 8 }}
                  >
                    <Option value="immediate">立即发送</Option>
                    <Option value="daily">每日摘要（暂仅保存偏好）</Option>
                    <Option value="weekly">每周摘要（暂仅保存偏好）</Option>
                    <Option value="never">不发送</Option>
                  </Select>
                </Col>
                <Col xs={24} md={12}>
                  <Text strong>通知邮箱：</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text>{user?.email || '-'}</Text>
                  </div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    短信通知号码：{user?.phone || '未绑定（请到安全设置绑定）'}
                  </Text>
                </Col>
              </Row>
            </Card>
          </Col>

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
                  <Button size="small" loading={loading} onClick={() => void handleMarkAllAsRead()}>
                    全部已读
                  </Button>
                  <Button size="small" loading={loading} onClick={handleClearAllNotifications}>
                    清空全部
                  </Button>
                </Space>
              }
            >
              <Table
                columns={notificationColumns}
                dataSource={notifications}
                rowKey="id"
                loading={listLoading || loading}
                pagination={{
                  current: page,
                  pageSize,
                  total,
                  showSizeChanger: true,
                  onChange: (nextPage, nextSize) => {
                    setPage(nextPage)
                    setPageSize(nextSize)
                  },
                }}
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
            loading={saving}
            onClick={() => void handleSave()}
          >
            保存设置
          </Button>
        </div>
      </Spin>
    </div>
  )
}

export default NotificationSettingsPage
