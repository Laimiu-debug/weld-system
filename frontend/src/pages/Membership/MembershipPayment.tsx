import React, { useEffect, useRef, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  QRCode,
  Result,
  Space,
  Spin,
  Statistic,
  Typography,
  message,
} from 'antd'
import {
  AlipayOutlined,
  ArrowLeftOutlined,
  LoadingOutlined,
  WechatOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiService } from '@/services/api'
import { membershipService } from '@/services/membership'
import ManualPaymentModal from '@/components/Payment/ManualPaymentModal'
import PaymentModal from '@/components/Payment/PaymentModal'

const { Title, Text, Paragraph } = Typography

type PaymentMethod = 'alipay' | 'wechat'

interface CreatedOrder {
  order_id: string
  transaction_id: string
  amount: number
  plan_name: string
  billing_cycle: string
  payment_method: PaymentMethod
  qr_code?: string | null
  payment_url?: string | null
}

const MembershipPayment: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [order, setOrder] = useState<CreatedOrder | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [manualVisible, setManualVisible] = useState(false)
  const [qrModalVisible, setQrModalVisible] = useState(false)
  const [mockAvailable, setMockAvailable] = useState(import.meta.env.DEV)
  const createdKeyRef = useRef('')

  const planId = searchParams.get('plan_id') || ''
  const billingCycle = searchParams.get('billing_cycle') || 'monthly'
  const paymentMethod = (searchParams.get('payment_method') || 'alipay') as PaymentMethod
  const subscriptionId = searchParams.get('subscription_id')

  useEffect(() => {
    const key = `${planId}|${billingCycle}|${paymentMethod}|${subscriptionId || ''}`
    if (createdKeyRef.current === key) {
      return
    }
    createdKeyRef.current = key
    void createOrder()
  }, [planId, billingCycle, paymentMethod, subscriptionId])

  const createOrder = async () => {
    setLoading(true)
    setError(null)
    setCreating(true)
    try {
      let resolvedPlanId = planId
      let resolvedCycle = billingCycle
      if (subscriptionId && !resolvedPlanId) {
        const current = await membershipService.getCurrentSubscription()
        if (!current) {
          throw new Error('未找到可续费的订阅')
        }
        resolvedPlanId = current.plan_id
        resolvedCycle = current.billing_cycle || 'monthly'
      }
      if (!resolvedPlanId) {
        throw new Error('缺少套餐信息，请从会员中心重新发起支付')
      }

      const response = await apiService.post('/payments/create', {
        plan_id: resolvedPlanId,
        billing_cycle: resolvedCycle,
        payment_method: paymentMethod,
        auto_renew: false,
        purpose: subscriptionId ? 'renew' : 'upgrade',
        existing_subscription_id: subscriptionId ? Number(subscriptionId) : undefined,
      })

      if (!response.success || !response.data) {
        throw new Error(response.message || '创建支付订单失败')
      }
      const paymentData = response.data.data || response.data
      const created: CreatedOrder = {
        order_id: paymentData.order_id || paymentData.transaction_id,
        transaction_id: paymentData.transaction_id || paymentData.order_id,
        amount: Number(paymentData.amount || 0),
        plan_name: paymentData.plan_name || resolvedPlanId,
        billing_cycle: paymentData.billing_cycle || resolvedCycle,
        payment_method: (paymentData.payment_method || paymentMethod) as PaymentMethod,
        qr_code: paymentData.qr_code,
        payment_url: paymentData.payment_url,
      }
      setOrder(created)
      if (!created.qr_code) {
        setManualVisible(true)
      } else {
        setQrModalVisible(true)
      }
    } catch (err) {
      const detail = err instanceof Error ? err.message : '创建支付订单失败'
      setError(detail)
      message.error(detail)
    } finally {
      setLoading(false)
      setCreating(false)
    }
  }

  const handleMockComplete = async () => {
    if (!order) {
      return
    }
    try {
      const response = await apiService.post(`/payments/mock-complete/${order.transaction_id}`)
      if (response.success) {
        message.success('模拟支付已完成')
        navigate(`/membership/result?order_id=${order.transaction_id}&status=success`)
        return
      }
      setMockAvailable(false)
    } catch {
      setMockAvailable(false)
      message.info('当前环境未开放模拟支付，请扫码或提交转账凭证')
    }
  }

  const handlePaid = () => {
    if (!order) {
      return
    }
    navigate(`/membership/result?order_id=${order.transaction_id}&status=success`)
  }

  const paymentIcon = () => {
    switch (paymentMethod) {
      case 'alipay':
        return <AlipayOutlined style={{ fontSize: 32, color: '#1677ff' }} />
      case 'wechat':
        return <WechatOutlined style={{ fontSize: 32, color: '#07c160' }} />
      default: {
        const _exhaustive: never = paymentMethod
        return _exhaustive
      }
    }
  }

  if (loading || creating) {
    return (
      <div className="page-container flex justify-center items-center" style={{ minHeight: 360 }}>
        <Spin size="large" tip="正在创建支付订单..." />
      </div>
    )
  }

  if (error || !order) {
    return (
      <div className="page-container">
        <Card>
          <Result
            status="error"
            title="无法发起支付"
            subTitle={error || '请返回会员中心后重试'}
            extra={[
              <Button key="back" onClick={() => navigate('/membership')}>
                返回会员中心
              </Button>,
              <Button key="retry" type="primary" onClick={() => void createOrder()}>
                重新创建订单
              </Button>,
            ]}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/membership')}>
          返回会员中心
        </Button>
        <Title level={2}>{subscriptionId ? '会员续费' : '会员支付'}</Title>
      </div>

      <Card>
        <Space direction="vertical" size="large" className="w-full">
          <Space>
            {paymentIcon()}
            <div>
              <Title level={4} className="mb-0">{order.plan_name}</Title>
              <Text type="secondary">订单号 {order.transaction_id}</Text>
            </div>
          </Space>
          <Statistic title="应付金额" value={order.amount} prefix="¥" precision={2} />
          {order.qr_code ? (
            <div className="text-center">
              <QRCode value={order.qr_code} size={200} />
              <Paragraph type="secondary" className="mt-4">
                <LoadingOutlined /> 请使用手机完成支付，系统会自动确认结果
              </Paragraph>
            </div>
          ) : (
            <Alert
              type="info"
              showIcon
              message="请按对公账户或收款码完成转账，并提交支付凭证"
            />
          )}
          <Space wrap>
            <Button type="primary" onClick={() => setQrModalVisible(Boolean(order.qr_code))}>
              打开支付窗口
            </Button>
            <Button onClick={() => setManualVisible(true)}>提交转账凭证</Button>
            {mockAvailable && (
              <Button onClick={() => void handleMockComplete()}>模拟支付成功（开发）</Button>
            )}
            <Button type="link" onClick={handlePaid}>
              我已支付，查看结果
            </Button>
          </Space>
        </Space>
      </Card>

      <PaymentModal
        visible={qrModalVisible && Boolean(order.qr_code)}
        orderId={order.transaction_id}
        amount={order.amount}
        planName={order.plan_name}
        paymentMethod={order.payment_method}
        qrCode={order.qr_code || undefined}
        onSuccess={handlePaid}
        onCancel={() => setQrModalVisible(false)}
      />
      <ManualPaymentModal
        visible={manualVisible}
        orderId={order.transaction_id}
        amount={order.amount}
        planName={order.plan_name}
        paymentMethod={order.payment_method === 'wechat' ? 'wechat' : 'alipay'}
        onSuccess={() => {
          setManualVisible(false)
          message.success('支付凭证已提交，请等待管理员确认')
          navigate('/membership/history')
        }}
        onCancel={() => setManualVisible(false)}
      />
    </div>
  )
}

export default MembershipPayment
