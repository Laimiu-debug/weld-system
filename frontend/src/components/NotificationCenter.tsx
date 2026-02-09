import React, { useState, useEffect } from 'react'
import {
  Popover,
  Badge,
  Button,
  List,
  Typography,
  Space,
  Tag,
  Empty,
  Spin,
  message,
  Tabs,
  Divider,
  Modal,
} from 'antd'
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  CheckCircleOutlined,
  ToolOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  type Notification,
} from '@/services/notifications'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Paragraph } = Typography

interface NotificationCenterProps {
  style?: React.CSSProperties
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ style }) => {
  const [visible, setVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [activeTab, setActiveTab] = useState('all')
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null)

  // 获取通知列表
  const fetchNotifications = async (unreadOnly = false) => {
    setLoading(true)
    try {
      const data = await getNotifications({
        unread_only: unreadOnly,
        page: 1,
        page_size: 50,
      })
      setNotifications(data.items)
      setUnreadCount(data.unread_count)
    } catch (error) {
      console.error('获取通知失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 获取未读数量
  const fetchUnreadCount = async () => {
    try {
      const data = await getUnreadCount()
      setUnreadCount(data.unread_count)
    } catch (error) {
      console.error('获取未读数量失败:', error)
    }
  }

  // 标记为已读
  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await markAsRead(notificationId)
      message.success('已标记为已读')
      // 立即刷新列表和未读数量
      await Promise.all([
        fetchNotifications(activeTab === 'unread'),
        fetchUnreadCount()
      ])
    } catch (error) {
      message.error('操作失败')
    }
  }

  // 全部标记为已读
  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead()
      message.success('全部已标记为已读')
      // 立即刷新列表和未读数量
      await Promise.all([
        fetchNotifications(activeTab === 'unread'),
        fetchUnreadCount()
      ])
    } catch (error) {
      message.error('操作失败')
    }
  }

  // 删除通知
  const handleDelete = async (notificationId: number) => {
    try {
      await deleteNotification(notificationId)
      message.success('已删除')
      // 立即刷新列表和未读数量
      await Promise.all([
        fetchNotifications(activeTab === 'unread'),
        fetchUnreadCount()
      ])
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 打开弹窗时加载数据
  const handleVisibleChange = (newVisible: boolean) => {
    setVisible(newVisible)
    if (newVisible) {
      fetchNotifications(activeTab === 'unread')
    }
  }

  // 切换Tab时重新加载
  const handleTabChange = (key: string) => {
    setActiveTab(key)
    fetchNotifications(key === 'unread')
  }

  // 查看通知详情
  const handleViewDetail = (notification: Notification) => {
    setSelectedNotification(notification)
    setDetailModalVisible(true)
    // 如果是未读的，自动标记为已读
    if (!notification.is_read) {
      handleMarkAsRead(notification.id)
    }
  }

  // 定期刷新未读数量
  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 60000) // 每分钟刷新一次
    return () => clearInterval(interval)
  }, [])

  // 获取通知类型图标
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'maintenance':
        return <ToolOutlined style={{ color: '#722ed1' }} />
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
    }
  }

  // 获取优先级标签
  const getPriorityTag = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return <Tag color="red">紧急</Tag>
      case 'high':
        return <Tag color="orange">重要</Tag>
      case 'normal':
        return null
      case 'low':
        return null
      default:
        return null
    }
  }

  // 通知内容
  const content = (
    <div style={{ width: 400, maxHeight: 600, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Text strong>通知中心</Text>
          {unreadCount > 0 && (
            <Button type="link" size="small" onClick={handleMarkAllAsRead}>
              全部已读
            </Button>
          )}
        </Space>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        size="small"
        style={{ padding: '0 16px' }}
        items={[
          {
            key: 'all',
            label: `全部 (${notifications.length})`,
          },
          {
            key: 'unread',
            label: `未读 (${unreadCount})`,
          },
        ]}
      />

      <div style={{ flex: 1, overflow: 'auto', maxHeight: 450 }}>
        <Spin spinning={loading}>
          {notifications.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无通知"
              style={{ padding: '40px 0' }}
            />
          ) : (
            <List
              dataSource={notifications}
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  style={{
                    padding: '12px 16px',
                    background: item.is_read ? 'transparent' : '#f0f7ff',
                    borderBottom: '1px solid #f0f0f0',
                  }}
                  actions={[
                    <Button
                      type="text"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewDetail(item)}
                      title="查看详情"
                    />,
                    !item.is_read && (
                      <Button
                        type="text"
                        size="small"
                        icon={<CheckOutlined />}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleMarkAsRead(item.id)
                        }}
                        title="标记已读"
                      />
                    ),
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      danger
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(item.id)
                      }}
                      title="删除"
                    />,
                  ].filter(Boolean)}
                >
                  <List.Item.Meta
                    avatar={getNotificationIcon(item.type)}
                    title={
                      <Space>
                        <Text strong={!item.is_read}>{item.title}</Text>
                        {getPriorityTag(item.priority)}
                        {item.is_pinned && <Tag color="blue">置顶</Tag>}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Paragraph
                          ellipsis={{ rows: 2 }}
                          style={{ margin: 0, fontSize: '12px', cursor: 'pointer' }}
                          onClick={() => handleViewDetail(item)}
                        >
                          {item.content}
                        </Paragraph>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {item.publish_at ? dayjs(item.publish_at).fromNow() : ''}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Spin>
      </div>
    </div>
  )

  return (
    <>
      <Popover
        content={content}
        trigger="click"
        open={visible}
        onOpenChange={handleVisibleChange}
        placement="bottomRight"
        overlayStyle={{ paddingTop: 8 }}
      >
        <Badge count={unreadCount} size="small" offset={[-2, 2]}>
          <Button
            type="text"
            icon={<BellOutlined />}
            style={{
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              ...style,
            }}
          />
        </Badge>
      </Popover>

      {/* 通知详情弹窗 */}
      <Modal
        title={
          <Space>
            {selectedNotification && getNotificationIcon(selectedNotification.type)}
            <span>{selectedNotification?.title}</span>
            {selectedNotification && getPriorityTag(selectedNotification.priority)}
            {selectedNotification?.is_pinned && <Tag color="blue">置顶</Tag>}
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          selectedNotification && !selectedNotification.is_read && (
            <Button
              key="mark-read"
              type="primary"
              onClick={() => {
                handleMarkAsRead(selectedNotification.id)
                setDetailModalVisible(false)
              }}
            >
              标记已读
            </Button>
          ),
        ].filter(Boolean)}
        width={600}
      >
        {selectedNotification && (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            {/* 通知内容 */}
            <div>
              <Text strong>通知内容：</Text>
              <div style={{
                marginTop: 8,
                padding: 12,
                background: '#f5f5f5',
                borderRadius: 4,
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6
              }}>
                {selectedNotification.content}
              </div>
            </div>

            <Divider style={{ margin: 0 }} />

            {/* 通知信息 */}
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <div>
                <Text type="secondary">通知类型：</Text>
                <Space>
                  {getNotificationIcon(selectedNotification.type)}
                  <Text>
                    {selectedNotification.type === 'info' && '信息'}
                    {selectedNotification.type === 'warning' && '警告'}
                    {selectedNotification.type === 'error' && '错误'}
                    {selectedNotification.type === 'success' && '成功'}
                    {selectedNotification.type === 'maintenance' && '维护'}
                  </Text>
                </Space>
              </div>

              <div>
                <Text type="secondary">优先级：</Text>
                <Text>
                  {selectedNotification.priority === 'urgent' && '紧急'}
                  {selectedNotification.priority === 'high' && '重要'}
                  {selectedNotification.priority === 'normal' && '普通'}
                  {selectedNotification.priority === 'low' && '低'}
                </Text>
              </div>

              {selectedNotification.publish_at && (
                <div>
                  <Text type="secondary">发布时间：</Text>
                  <Text>
                    {dayjs(selectedNotification.publish_at).format('YYYY-MM-DD HH:mm:ss')}
                    {' '}
                    ({dayjs(selectedNotification.publish_at).fromNow()})
                  </Text>
                </div>
              )}

              {selectedNotification.expire_at && (
                <div>
                  <Text type="secondary">过期时间：</Text>
                  <Text>
                    {dayjs(selectedNotification.expire_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Text>
                </div>
              )}

              {selectedNotification.read_at && (
                <div>
                  <Text type="secondary">已读时间：</Text>
                  <Text>
                    {dayjs(selectedNotification.read_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Text>
                </div>
              )}

              <div>
                <Text type="secondary">阅读状态：</Text>
                <Tag color={selectedNotification.is_read ? 'success' : 'warning'}>
                  {selectedNotification.is_read ? '已读' : '未读'}
                </Tag>
              </div>
            </Space>
          </Space>
        )}
      </Modal>
    </>
  )
}

export default NotificationCenter

