import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  DatePicker,
  Select,
  Row,
  Col,
  Statistic,
  Timeline,
  Modal,
  Descriptions,
  Alert,
  Tooltip,
  Badge,
  Empty,
  Input,
  message,
} from 'antd'
import { apiService } from '@/services/api'
import {
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  FileTextOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  CreditCardOutlined,
  WechatOutlined,
  AlipayOutlined,
  FilterOutlined,
  SearchOutlined,
  BarChartOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface SubscriptionRecord {
  id: string
  orderId: string
  planName: string
  planType: 'basic' | 'professional' | 'enterprise' | 'custom'
  amount: number
  currency: string
  status: 'paid' | 'pending' | 'failed' | 'cancelled' | 'refunded'
  paymentMethod: 'alipay' | 'wechat' | 'bank' | 'credit_card' | string
  startDate: string
  endDate: string
  createdAt: string
  paidAt?: string
  invoiceUrl?: string
  description: string
  autoRenew: boolean
  discountAmount?: number
  originalAmount?: number
  features: string[]
  transactionStatus?: string
}

interface TransactionLog {
  id: string
  subscriptionId: string
  action: string
  description: string
  timestamp: string
  operator: string
  ip: string
  amount: number  // 添加金额字段
  status: string  // 添加状态字段
}

const SubscriptionHistory: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<SubscriptionRecord[]>([])
  const [transactions, setTransactions] = useState<TransactionLog[]>([])
  const [loading, setLoading] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedSubscription, setSelectedSubscription] = useState<SubscriptionRecord | null>(null)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(1, 'year'),
    dayjs(),
  ])
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterPlan, setFilterPlan] = useState<string>('')
  const [searchText, setSearchText] = useState('')

  // 获取真实的订阅数据
  const fetchSubscriptionHistory = async () => {
    setLoading(true)
    try {
      const response = await apiService.get('/members/history')

      if (response.success && response.data && Array.isArray(response.data.data)) {
        const data = response.data.data

        const formattedSubscriptions = data.map((item: any) => {
          const firstTransaction = item.transactions && item.transactions.length > 0 ? item.transactions[0] : null
          const unpaidTx = (item.transactions || []).find((tx: any) =>
            ['pending', 'pending_confirm', 'failed', 'rejected'].includes(tx.status)
          )

          return {
            id: item.id?.toString() || Date.now().toString(),
            orderId: unpaidTx?.transaction_id || firstTransaction?.transaction_id || `SUB-${item.id}`,
            planName: getPlanDisplayName(item.plan_id) || '未知套餐',
            planType: getPlanTypeFromId(item.plan_id),
            amount: unpaidTx?.amount ?? item.price ?? 0,
            currency: item.currency || 'CNY',
            status: item.status === 'active' ? 'paid' :
                   item.status === 'cancelled' ? 'cancelled' :
                   item.status === 'expired' ? 'failed' :
                   item.status === 'pending' ? 'pending' : 'pending',
            paymentMethod: unpaidTx?.payment_method || item.payment_method || 'unknown',
            startDate: item.start_date || '',
            endDate: item.end_date || '',
            createdAt: item.created_at || '',
            paidAt: item.last_payment_date || '',
            invoiceUrl: undefined,
            description: `${getPlanDisplayName(item.plan_id) || '未知套餐'} - ${getBillingCycleName(item.billing_cycle) || 'unknown'}`,
            autoRenew: false,
            features: [],
            transactionStatus: unpaidTx?.status || firstTransaction?.status,
          }
        })

        setSubscriptions(formattedSubscriptions)

        const allTransactions: TransactionLog[] = []
        data.forEach((item: any) => {
          if (item.transactions && Array.isArray(item.transactions)) {
            item.transactions.forEach((tx: any) => {
              allTransactions.push({
                id: tx.id?.toString() || Date.now().toString(),
                subscriptionId: item.id?.toString() || '',
                action: tx.status === 'success' ? '支付成功' :
                       tx.status === 'pending' ? '待支付' :
                       tx.status === 'pending_confirm' ? '待确认' :
                       tx.status === 'failed' ? '支付失败' :
                       tx.status === 'rejected' ? '已拒绝' : '未知状态',
                description: tx.description || `${tx.payment_method} 支付 ¥${tx.amount}`,
                timestamp: tx.transaction_date || tx.created_at || '',
                operator: '系统',
                ip: '-',
                amount: tx.amount || 0,
                status: tx.status || 'unknown',
              })
            })
          }
        })
        setTransactions(allTransactions)
      } else {
        setSubscriptions([])
        setTransactions([])
      }
    } catch (error) {
      console.error('获取订阅历史失败:', error)
      setSubscriptions([])
      setTransactions([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchSubscriptionHistory()
  }, [])

  const handleDeleteUnpaid = (record: SubscriptionRecord) => {
    Modal.confirm({
      title: '删除未支付订单',
      content: `确定删除订单 ${record.orderId} 吗？删除后不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await apiService.delete(`/payments/orders/${record.orderId}`)
          if (!response.success) {
            throw new Error(response.message || '删除失败')
          }
          message.success('订单已删除')
          await fetchSubscriptionHistory()
        } catch (error) {
          const detail = error instanceof Error ? error.message : '删除失败'
          message.error(detail)
        }
      },
    })
  }

  // 辅助函数：根据plan_id获取planType
  const getPlanTypeFromId = (planId: string) => {
    if (planId?.includes('free') || planId === 'free') return 'basic'
    if (planId?.includes('pro')) return 'professional'
    if (planId?.includes('enterprise')) return 'enterprise'
    return 'custom'
  }

  // 辅助函数：根据plan_id获取显示名称
  const getPlanDisplayName = (planId: string) => {
    const planNames: Record<string, string> = {
      'free': '个人免费版',
      'personal_pro': '个人专业版',
      'personal_advanced': '个人高级版',
      'personal_flagship': '个人旗舰版',
      'enterprise': '企业版',
      'enterprise_pro': '企业版PRO',
      'enterprise_pro_max': '企业版PRO MAX',
    }
    return planNames[planId] || planId
  }

  // 辅助函数：获取计费周期名称
  const getBillingCycleName = (cycle: string) => {
    const cycleNames: Record<string, string> = {
      'monthly': '月付',
      'quarterly': '季付',
      'yearly': '年付',
    }
    return cycleNames[cycle] || cycle
  }

  // 辅助函数：格式化日期
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('zh-CN')
    } catch (error) {
      return dateString
    }
  }

  // 统计数据
  const getStatistics = () => {
    const total = subscriptions.length
    const paid = subscriptions.filter(sub => sub.status === 'paid').length
    const pending = subscriptions.filter(sub => sub.status === 'pending').length
    const failed = subscriptions.filter(sub => sub.status === 'failed').length
    const refunded = subscriptions.filter(sub => sub.status === 'refunded').length

    // 统计所有成功支付的交易金额
    // 注意: transactions 数组中的交易记录才是实际支付的金额(包含补差价计算)
    const successfulTransactions = transactions.filter(tx =>
      tx.status === 'success' // 使用原始状态字段
    )

    // 计算总消费金额
    const totalAmount = successfulTransactions.reduce((sum, tx) => {
      return sum + (tx.amount || 0)
    }, 0)

    const successfulPaymentCount = successfulTransactions.length

    return {
      total,
      paid,
      pending,
      failed,
      refunded,
      totalAmount: parseFloat(totalAmount.toFixed(2)),
      averageAmount: successfulPaymentCount > 0 ? parseFloat((totalAmount / successfulPaymentCount).toFixed(2)) : 0,
    }
  }

  const stats = getStatistics()

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      paid: { color: 'success', text: '已支付', icon: <CheckCircleOutlined /> },
      pending: { color: 'processing', text: '待支付', icon: <ClockCircleOutlined /> },
      failed: { color: 'error', text: '支付失败', icon: <CloseCircleOutlined /> },
      cancelled: { color: 'default', text: '已取消', icon: <ExclamationCircleOutlined /> },
      refunded: { color: 'warning', text: '已退款', icon: <ExclamationCircleOutlined /> },
    }
    return statusMap[status as keyof typeof statusMap] || { color: 'default', text: status, icon: null }
  }

  // 获取支付方式配置
  const getPaymentMethodConfig = (method: string) => {
    const methodMap: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      alipay: { color: 'blue', text: '支付宝', icon: <AlipayOutlined /> },
      wechat: { color: 'green', text: '微信支付', icon: <WechatOutlined /> },
      credit_card: { color: 'purple', text: '信用卡', icon: <CreditCardOutlined /> },
    }
    return methodMap[method] || { color: 'default', text: method || '未知', icon: null }
  }

  // 获取套餐配置
  const getPlanConfig = (type: string) => {
    const planMap = {
      basic: { color: 'green', text: '基础版' },
      professional: { color: 'blue', text: '专业版' },
      enterprise: { color: 'purple', text: '企业版' },
      custom: { color: 'orange', text: '定制版' },
    }
    return planMap[type as keyof typeof planMap] || { color: 'default', text: type }
  }

  // 过滤数据
  const filteredSubscriptions = subscriptions.filter(subscription => {
    const matchDate = dateRange ? (
      dayjs(subscription.createdAt).isAfter(dateRange[0]) &&
      dayjs(subscription.createdAt).isBefore(dateRange[1])
    ) : true
    const matchStatus = !filterStatus || subscription.status === filterStatus
    const matchPlan = !filterPlan || subscription.planType === filterPlan
    const matchSearch = !searchText ||
      subscription.orderId.toLowerCase().includes(searchText.toLowerCase()) ||
      subscription.planName.toLowerCase().includes(searchText.toLowerCase())

    return matchDate && matchStatus && matchPlan && matchSearch
  })

  // 查看详情
  const handleViewDetail = (subscription: SubscriptionRecord) => {
    setSelectedSubscription(subscription)
    setDetailModalVisible(true)
  }

  // 获取相关交易记录
  const getRelatedTransactions = (subscriptionId: string) => {
    return transactions.filter(tx => tx.subscriptionId === subscriptionId)
  }

  const columns: ColumnsType<SubscriptionRecord> = [
    {
      title: '订单信息',
      key: 'order',
      render: (_, record) => (
        <div>
          <div>
            <Text strong>{record.orderId}</Text>
          </div>
          <div>
            <Text type="secondary" className="text-xs">
              {dayjs(record.createdAt).format('YYYY-MM-DD HH:mm')}
            </Text>
          </div>
        </div>
      ),
    },
    {
      title: '套餐类型',
      dataIndex: 'planName',
      key: 'plan',
      render: (plan, record) => {
        const config = getPlanConfig(record.planType)
        return <Tag color={config.color}>{plan}</Tag>
      },
    },
    {
      title: '金额',
      key: 'amount',
      render: (_, record) => (
        <div>
          <Text strong>¥{record.amount.toLocaleString()}</Text>
          {record.originalAmount && record.originalAmount > record.amount && (
            <div>
              <Text type="secondary" delete className="text-xs">
                ¥{record.originalAmount.toLocaleString()}
              </Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: '支付方式',
      dataIndex: 'paymentMethod',
      key: 'paymentMethod',
      render: (method) => {
        const config = getPaymentMethodConfig(method)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = getStatusConfig(status)
        return (
          <Badge
            status={status === 'paid' ? 'success' : status === 'pending' ? 'processing' : 'error'}
            text={config.text}
          />
        )
      },
    },
    {
      title: '服务期限',
      key: 'period',
      render: (_, record) => (
        <div>
          <div>
            <Text className="text-xs">{dayjs(record.startDate).format('YYYY-MM-DD')}</Text>
          </div>
          <div>
            <Text className="text-xs">至</Text>
          </div>
          <div>
            <Text className="text-xs">{dayjs(record.endDate).format('YYYY-MM-DD')}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '自动续费',
      dataIndex: 'autoRenew',
      key: 'autoRenew',
      render: () => (
        <Tag color="default">暂不支持</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => {
        const canDelete =
          record.status === 'pending' ||
          ['pending', 'pending_confirm', 'failed', 'rejected'].includes(record.transactionStatus || '')
        return (
          <Space>
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            >
              查看
            </Button>
            {canDelete && (
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDeleteUnpaid(record)}
              >
                删除
              </Button>
            )}
            {record.invoiceUrl && record.status === 'paid' && (
              <Button
                type="text"
                icon={<DownloadOutlined />}
                onClick={() => console.log('下载发票', record.invoiceUrl)}
              >
                发票
              </Button>
            )}
          </Space>
        )
      },
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>订阅历史</Title>
        <Text type="secondary">查看和管理您的订阅记录和支付历史</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总订阅数"
              value={stats.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已支付"
              value={stats.paid}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总消费"
              value={stats.totalAmount}
              precision={2}
              valueStyle={{ color: '#fa8c16' }}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均消费"
              value={stats.averageAmount}
              valueStyle={{ color: '#722ed1' }}
              prefix="¥"
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选条件 */}
      <Card className="mb-6">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates?.[0] && dates?.[1] ? [dates[0], dates[1]] : null)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="状态筛选"
              value={filterStatus}
              onChange={setFilterStatus}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="paid">已支付</Option>
              <Option value="pending">待支付</Option>
              <Option value="failed">支付失败</Option>
              <Option value="cancelled">已取消</Option>
              <Option value="refunded">已退款</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="套餐筛选"
              value={filterPlan}
              onChange={setFilterPlan}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="basic">基础版</Option>
              <Option value="professional">专业版</Option>
              <Option value="enterprise">企业版</Option>
              <Option value="custom">定制版</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索订单号或套餐"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button icon={<FilterOutlined />}>
              应用筛选
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 订阅列表 */}
      <Card title="订阅记录">
        <Table
          columns={columns}
          dataSource={filteredSubscriptions}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          locale={{
            emptyText: <Empty description="暂无订阅记录" />,
          }}
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="订阅详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedSubscription && (
          <div>
            <Descriptions title="基本信息" bordered column={2}>
              <Descriptions.Item label="订单号">{selectedSubscription.orderId}</Descriptions.Item>
              <Descriptions.Item label="套餐名称">{selectedSubscription.planName}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(selectedSubscription.createdAt).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="支付时间">
                {selectedSubscription.paidAt ? dayjs(selectedSubscription.paidAt).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="服务期限">
                {dayjs(selectedSubscription.startDate).format('YYYY-MM-DD')} 至 {dayjs(selectedSubscription.endDate).format('YYYY-MM-DD')}
              </Descriptions.Item>
              <Descriptions.Item label="自动续费">
                <Tag color={selectedSubscription.autoRenew ? 'green' : 'default'}>
                  {selectedSubscription.autoRenew ? '已开启' : '已关闭'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <Descriptions title="支付信息" bordered column={2} className="mt-4">
              <Descriptions.Item label="订单金额">
                ¥{selectedSubscription.amount.toLocaleString()} {selectedSubscription.currency}
              </Descriptions.Item>
              <Descriptions.Item label="原价">
                {selectedSubscription.originalAmount ?
                  `¥${selectedSubscription.originalAmount.toLocaleString()}` :
                  '-'
                }
              </Descriptions.Item>
              <Descriptions.Item label="优惠金额">
                {selectedSubscription.discountAmount ?
                  `¥${selectedSubscription.discountAmount.toLocaleString()}` :
                  '-'
                }
              </Descriptions.Item>
              <Descriptions.Item label="支付方式">
                <Tag color={getPaymentMethodConfig(selectedSubscription.paymentMethod).color}
                     icon={getPaymentMethodConfig(selectedSubscription.paymentMethod).icon}>
                  {getPaymentMethodConfig(selectedSubscription.paymentMethod).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="支付状态">
                <Badge
                  status={selectedSubscription.status === 'paid' ? 'success' : 'error'}
                  text={getStatusConfig(selectedSubscription.status).text}
                />
              </Descriptions.Item>
              <Descriptions.Item label="描述">{selectedSubscription.description}</Descriptions.Item>
            </Descriptions>

            <Card title="套餐功能" size="small" className="mt-4">
              <div className="max-h-40 overflow-y-auto">
                <Space wrap>
                  {selectedSubscription.features.map((feature, index) => (
                    <Tag key={index} color="blue" icon={<CheckOutlined />}>
                      {feature}
                    </Tag>
                  ))}
                </Space>
              </div>
            </Card>

            <Card title="操作记录" size="small" className="mt-4">
              <Timeline
                items={getRelatedTransactions(selectedSubscription.id).map((tx) => ({
                  children: (
                    <div>
                      <div className="font-medium">{tx.action}</div>
                      <div className="text-sm text-gray-500">{tx.description}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {tx.operator} · {dayjs(tx.timestamp).format('YYYY-MM-DD HH:mm:ss')} · {tx.ip}
                      </div>
                    </div>
                  ),
                  color: tx.action.includes('成功') ? 'green' : tx.action.includes('失败') ? 'red' : 'blue',
                }))}
              />
            </Card>

            {selectedSubscription.invoiceUrl && selectedSubscription.status === 'paid' && (
              <div className="mt-4 text-right">
                <Button type="primary" icon={<DownloadOutlined />}>
                  下载发票
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SubscriptionHistory
