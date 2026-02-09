import React, { useEffect, useState } from 'react'
import { 
  Table, 
  Button, 
  message, 
  Tag, 
  Space, 
  Card, 
  Modal, 
  Descriptions,
  Badge,
  Input,
  Select
} from 'antd'
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  EyeOutlined,
  ReloadOutlined 
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Search } = Input
const { Option } = Select

interface PendingPayment {
  order_id: string
  user_id: string
  user_name: string
  user_email: string
  plan_id: string
  plan_name: string
  amount: number
  payment_method: string
  transaction_id: string
  status: string
  created_at: string
  updated_at: string
}

const PendingPayments: React.FC = () => {
  const [payments, setPayments] = useState<PendingPayment[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPayment, setSelectedPayment] = useState<PendingPayment | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('pending_confirm')

  // 加载待确认支付列表
  const loadPendingPayments = async () => {
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/payments/pending?status=${statusFilter}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setPayments(data)
      } else {
        message.error('加载失败')
      }
    } catch (error) {
      message.error('网络错误')
    } finally {
      setLoading(false)
    }
  }

  // 确认支付
  const confirmPayment = async (orderId: string) => {
    Modal.confirm({
      title: '确认支付',
      content: '确定要确认这笔支付吗？确认后将立即开通会员权益。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch('/api/v1/payments/admin/confirm-payment', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ order_id: orderId })
          })

          if (response.ok) {
            message.success('支付已确认，会员已开通')
            loadPendingPayments()
          } else {
            const data = await response.json()
            message.error(data.detail || '确认失败')
          }
        } catch (error) {
          message.error('网络错误')
        }
      }
    })
  }

  // 拒绝支付
  const rejectPayment = async (orderId: string) => {
    Modal.confirm({
      title: '拒绝支付',
      content: '确定要拒绝这笔支付吗？',
      okText: '拒绝',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await fetch('/api/v1/payments/admin/reject-payment', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ order_id: orderId })
          })

          if (response.ok) {
            message.success('支付已拒绝')
            loadPendingPayments()
          } else {
            const data = await response.json()
            message.error(data.detail || '操作失败')
          }
        } catch (error) {
          message.error('网络错误')
        }
      }
    })
  }

  // 查看详情
  const viewDetail = (payment: PendingPayment) => {
    setSelectedPayment(payment)
    setDetailVisible(true)
  }

  useEffect(() => {
    loadPendingPayments()
    // 每30秒自动刷新
    const interval = setInterval(loadPendingPayments, 30000)
    return () => clearInterval(interval)
  }, [statusFilter])

  const columns: ColumnsType<PendingPayment> = [
    {
      title: '订单号',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 200,
      fixed: 'left',
      render: (text) => <span style={{ fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: '用户',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
    },
    {
      title: '套餐',
      dataIndex: 'plan_name',
      key: 'plan_name',
      width: 150,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (amount) => (
        <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
          ¥{amount.toFixed(2)}
        </span>
      )
    },
    {
      title: '支付方式',
      dataIndex: 'payment_method',
      key: 'payment_method',
      width: 100,
      render: (method) => (
        <Tag color={method === 'alipay' ? 'blue' : 'green'}>
          {method === 'alipay' ? '支付宝' : '微信'}
        </Tag>
      )
    },
    {
      title: '交易号',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 180,
      render: (text) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{text}</span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          'pending_confirm': { text: '待确认', color: 'orange' },
          'success': { text: '已确认', color: 'green' },
          'rejected': { text: '已拒绝', color: 'red' },
        }
        const config = statusMap[status] || { text: status, color: 'default' }
        return <Badge status={config.color as any} text={config.text} />
      }
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text) => new Date(text).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending_confirm' && (
            <>
              <Button 
                type="link" 
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => confirmPayment(record.order_id)}
                style={{ color: '#52c41a' }}
              >
                确认
              </Button>
              <Button 
                type="link" 
                size="small"
                danger
                icon={<CloseCircleOutlined />}
                onClick={() => rejectPayment(record.order_id)}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      )
    }
  ]

  // 过滤数据
  const filteredPayments = payments.filter(payment => {
    if (!searchText) return true
    return (
      payment.order_id.toLowerCase().includes(searchText.toLowerCase()) ||
      payment.user_name.toLowerCase().includes(searchText.toLowerCase()) ||
      payment.transaction_id.toLowerCase().includes(searchText.toLowerCase())
    )
  })

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="待确认支付" 
        extra={
          <Space>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 120 }}
            >
              <Option value="pending_confirm">待确认</Option>
              <Option value="success">已确认</Option>
              <Option value="rejected">已拒绝</Option>
              <Option value="all">全部</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadPendingPayments}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Search
            placeholder="搜索订单号、用户名或交易号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 400 }}
            allowClear
          />

          <Table 
            columns={columns} 
            dataSource={filteredPayments} 
            loading={loading}
            rowKey="order_id"
            scroll={{ x: 1400 }}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`
            }}
          />
        </Space>
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="支付详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={
          selectedPayment?.status === 'pending_confirm' ? [
            <Button key="reject" danger onClick={() => {
              rejectPayment(selectedPayment.order_id)
              setDetailVisible(false)
            }}>
              拒绝支付
            </Button>,
            <Button key="confirm" type="primary" onClick={() => {
              confirmPayment(selectedPayment.order_id)
              setDetailVisible(false)
            }}>
              确认支付
            </Button>
          ] : [
            <Button key="close" onClick={() => setDetailVisible(false)}>
              关闭
            </Button>
          ]
        }
        width={700}
      >
        {selectedPayment && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="订单号" span={2}>
              {selectedPayment.order_id}
            </Descriptions.Item>
            <Descriptions.Item label="用户名">
              {selectedPayment.user_name}
            </Descriptions.Item>
            <Descriptions.Item label="用户邮箱">
              {selectedPayment.user_email}
            </Descriptions.Item>
            <Descriptions.Item label="套餐">
              {selectedPayment.plan_name}
            </Descriptions.Item>
            <Descriptions.Item label="金额">
              <span style={{ color: '#ff4d4f', fontWeight: 'bold', fontSize: 16 }}>
                ¥{selectedPayment.amount.toFixed(2)}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="支付方式">
              <Tag color={selectedPayment.payment_method === 'alipay' ? 'blue' : 'green'}>
                {selectedPayment.payment_method === 'alipay' ? '支付宝' : '微信'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {selectedPayment.status === 'pending_confirm' && (
                <Badge status="warning" text="待确认" />
              )}
              {selectedPayment.status === 'success' && (
                <Badge status="success" text="已确认" />
              )}
              {selectedPayment.status === 'rejected' && (
                <Badge status="error" text="已拒绝" />
              )}
            </Descriptions.Item>
            <Descriptions.Item label="交易号" span={2}>
              <span style={{ fontFamily: 'monospace' }}>
                {selectedPayment.transaction_id}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="提交时间">
              {new Date(selectedPayment.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedPayment.updated_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default PendingPayments

