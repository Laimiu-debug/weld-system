import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Result,
  Button,
  Card,
  Descriptions,
  Space,
  Spin,
  Typography,
  Timeline,
  Tag
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  HomeOutlined,
  FileTextOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { apiService } from '@/services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography

interface PaymentInfo {
  order_id: string
  status: 'success' | 'failed' | 'pending'
  amount: number
  plan_name: string
  transaction_id: string
  paid_at?: string
  failure_reason?: string
}

const PaymentResult: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null)

  const orderId = searchParams.get('order_id')
  const status = searchParams.get('status')

  useEffect(() => {
    if (orderId) {
      fetchPaymentStatus()
    } else {
      setLoading(false)
    }
  }, [orderId])

  const fetchPaymentStatus = async () => {
    try {
      setLoading(true)
      const response = await apiService.get(`/payments/status/${orderId}`)
      
      if (response.data?.success) {
        setPaymentInfo(response.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch payment status:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    navigate('/membership/upgrade')
  }

  const handleGoHome = () => {
    navigate('/dashboard')
  }

  const handleViewMembership = () => {
    navigate('/membership/current')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spin size="large" tip="正在查询支付结果..." />
      </div>
    )
  }

  if (!orderId || !paymentInfo) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <Card className="max-w-2xl w-full">
          <Result
            status="404"
            title="未找到支付信息"
            subTitle="无法找到相关的支付订单信息"
            extra={
              <Button type="primary" onClick={handleGoHome}>
                返回首页
              </Button>
            }
          />
        </Card>
      </div>
    )
  }

  const renderSuccessResult = () => (
    <Result
      status="success"
      icon={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: 72 }} />}
      title={<Title level={2}>支付成功！</Title>}
      subTitle="恭喜您，会员升级成功！"
      extra={[
        <Button type="primary" size="large" key="membership" onClick={handleViewMembership}>
          查看会员信息
        </Button>,
        <Button size="large" key="home" onClick={handleGoHome}>
          返回首页
        </Button>
      ]}
    >
      <Card className="mt-6 text-left">
        <Descriptions title="订单详情" column={1} bordered>
          <Descriptions.Item label="订单号">
            <Text copyable>{paymentInfo.order_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="交易号">
            <Text copyable>{paymentInfo.transaction_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="套餐名称">
            <Tag color="blue">{paymentInfo.plan_name}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="支付金额">
            <Text strong className="text-xl text-red-500">
              ¥{paymentInfo.amount.toFixed(2)}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="支付时间">
            {paymentInfo.paid_at ? dayjs(paymentInfo.paid_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="支付状态">
            <Tag color="success">支付成功</Tag>
          </Descriptions.Item>
        </Descriptions>

        <div className="mt-6">
          <Title level={5}>接下来您可以：</Title>
          <Timeline className="mt-4">
            <Timeline.Item color="green">
              <Space>
                <CheckCircleOutlined />
                <span>会员权益已激活</span>
              </Space>
            </Timeline.Item>
            <Timeline.Item color="blue">
              <Space>
                <FileTextOutlined />
                <span>开始使用高级功能</span>
              </Space>
            </Timeline.Item>
            <Timeline.Item color="blue">
              <Space>
                <HomeOutlined />
                <span>探索更多功能</span>
              </Space>
            </Timeline.Item>
          </Timeline>
        </div>
      </Card>
    </Result>
  )

  const renderFailedResult = () => (
    <Result
      status="error"
      icon={<CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 72 }} />}
      title={<Title level={2}>支付失败</Title>}
      subTitle={paymentInfo.failure_reason || '支付过程中出现错误，请重试'}
      extra={[
        <Button type="primary" size="large" key="retry" icon={<ReloadOutlined />} onClick={handleRetry}>
          重新支付
        </Button>,
        <Button size="large" key="home" onClick={handleGoHome}>
          返回首页
        </Button>
      ]}
    >
      <Card className="mt-6 text-left">
        <Descriptions title="订单详情" column={1} bordered>
          <Descriptions.Item label="订单号">
            <Text copyable>{paymentInfo.order_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="套餐名称">
            {paymentInfo.plan_name}
          </Descriptions.Item>
          <Descriptions.Item label="订单金额">
            <Text strong>¥{paymentInfo.amount.toFixed(2)}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="支付状态">
            <Tag color="error">支付失败</Tag>
          </Descriptions.Item>
          {paymentInfo.failure_reason && (
            <Descriptions.Item label="失败原因">
              <Text type="danger">{paymentInfo.failure_reason}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>

        <div className="mt-6">
          <Title level={5}>常见问题：</Title>
          <ul className="mt-4 space-y-2">
            <li>• 请确认支付账户余额充足</li>
            <li>• 请检查网络连接是否正常</li>
            <li>• 如有疑问，请联系客服：400-xxx-xxxx</li>
          </ul>
        </div>
      </Card>
    </Result>
  )

  const renderPendingResult = () => (
    <Result
      status="info"
      title={<Title level={2}>支付处理中</Title>}
      subTitle="您的支付正在处理中，请稍候..."
      extra={[
        <Button type="primary" size="large" key="refresh" icon={<ReloadOutlined />} onClick={fetchPaymentStatus}>
          刷新状态
        </Button>,
        <Button size="large" key="home" onClick={handleGoHome}>
          返回首页
        </Button>
      ]}
    >
      <Card className="mt-6 text-left">
        <Descriptions title="订单详情" column={1} bordered>
          <Descriptions.Item label="订单号">
            <Text copyable>{paymentInfo.order_id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="套餐名称">
            {paymentInfo.plan_name}
          </Descriptions.Item>
          <Descriptions.Item label="订单金额">
            <Text strong>¥{paymentInfo.amount.toFixed(2)}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="支付状态">
            <Tag color="processing">处理中</Tag>
          </Descriptions.Item>
        </Descriptions>

        <div className="mt-6">
          <Spin /> <Text className="ml-2">支付结果确认中，请稍候...</Text>
        </div>
      </Card>
    </Result>
  )

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        <Card>
          {paymentInfo.status === 'success' && renderSuccessResult()}
          {paymentInfo.status === 'failed' && renderFailedResult()}
          {paymentInfo.status === 'pending' && renderPendingResult()}
        </Card>
      </div>
    </div>
  )
}

export default PaymentResult

