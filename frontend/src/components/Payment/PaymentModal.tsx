import React, { useEffect, useState } from 'react'
import {
  Modal,
  QRCode,
  Spin,
  Result,
  Button,
  Space,
  Typography,
  Alert,
  Statistic,
  Card,
  Steps,
  message
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  WechatOutlined,
  AlipayOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { apiService } from '@/services/api'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface PaymentModalProps {
  visible: boolean
  orderId: string
  amount: number
  planName: string
  paymentMethod: 'alipay' | 'wechat' | 'bank'
  onSuccess: () => void
  onCancel: () => void
}

type PaymentStatus = 'loading' | 'pending' | 'success' | 'failed' | 'timeout'

const PaymentModal: React.FC<PaymentModalProps> = ({
  visible,
  orderId,
  amount,
  planName,
  paymentMethod,
  onSuccess,
  onCancel
}) => {
  const [status, setStatus] = useState<PaymentStatus>('loading')
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [countdown, setCountdown] = useState(300) // 5分钟倒计时
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)
  const [countdownInterval, setCountdownInterval] = useState<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (visible && orderId) {
      initPayment()
    }

    return () => {
      // 清理定时器
      if (pollingInterval) clearInterval(pollingInterval)
      if (countdownInterval) clearInterval(countdownInterval)
    }
  }, [visible, orderId])

  const initPayment = async () => {
    try {
      setStatus('loading')
      
      // 获取支付二维码
      const response = await apiService.post(`/payments/create`, {
        plan_id: orderId,
        billing_cycle: 'monthly',
        payment_method: paymentMethod,
        auto_renew: false
      })

      if (response.data?.success) {
        const paymentUrl = response.data.payment_url || response.data.qr_code
        setQrCodeUrl(paymentUrl)
        setStatus('pending')
        
        // 开始轮询支付状态
        startPolling()
        // 开始倒计时
        startCountdown()
      } else {
        setStatus('failed')
        message.error('创建支付订单失败')
      }
    } catch (error) {
      console.error('Payment initialization failed:', error)
      setStatus('failed')
      message.error('创建支付订单失败，请稍后重试')
    }
  }

  const startPolling = () => {
    const interval = setInterval(async () => {
      try {
        const response = await apiService.get(`/payments/status/${orderId}`)
        
        if (response.data?.success) {
          const paymentStatus = response.data.data?.status
          
          if (paymentStatus === 'success') {
            setStatus('success')
            if (pollingInterval) clearInterval(pollingInterval)
            if (countdownInterval) clearInterval(countdownInterval)
            
            // 延迟2秒后调用成功回调
            setTimeout(() => {
              onSuccess()
            }, 2000)
          } else if (paymentStatus === 'failed') {
            setStatus('failed')
            if (pollingInterval) clearInterval(pollingInterval)
            if (countdownInterval) clearInterval(countdownInterval)
          }
        }
      } catch (error) {
        console.error('Payment status check failed:', error)
      }
    }, 3000) // 每3秒查询一次

    setPollingInterval(interval)
  }

  const startCountdown = () => {
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          setStatus('timeout')
          if (pollingInterval) clearInterval(pollingInterval)
          if (countdownInterval) clearInterval(countdownInterval)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    setCountdownInterval(interval)
  }

  const handleRetry = () => {
    setCountdown(300)
    initPayment()
  }

  const getPaymentIcon = () => {
    switch (paymentMethod) {
      case 'alipay':
        return <AlipayOutlined style={{ fontSize: 48, color: '#1677ff' }} />
      case 'wechat':
        return <WechatOutlined style={{ fontSize: 48, color: '#07c160' }} />
      default:
        return null
    }
  }

  const getPaymentMethodName = () => {
    switch (paymentMethod) {
      case 'alipay':
        return '支付宝'
      case 'wechat':
        return '微信支付'
      case 'bank':
        return '银行转账'
      default:
        return '未知'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const renderContent = () => {
    switch (status) {
      case 'loading':
        return (
          <div className="text-center py-12">
            <Spin size="large" tip="正在创建支付订单..." />
          </div>
        )

      case 'pending':
        return (
          <div className="text-center">
            <Space direction="vertical" size="large" className="w-full">
              {/* 支付方式图标 */}
              <div>{getPaymentIcon()}</div>

              {/* 二维码 */}
              <Card className="inline-block">
                {qrCodeUrl ? (
                  <QRCode value={qrCodeUrl} size={256} />
                ) : (
                  <div style={{ width: 256, height: 256 }} className="flex items-center justify-center">
                    <Spin />
                  </div>
                )}
              </Card>

              {/* 提示信息 */}
              <div>
                <Title level={4}>请使用{getPaymentMethodName()}扫码支付</Title>
                <Paragraph type="secondary">
                  订单金额：<Text strong className="text-2xl text-red-500">¥{amount.toFixed(2)}</Text>
                </Paragraph>
              </div>

              {/* 倒计时 */}
              <Alert
                message={
                  <Space>
                    <LoadingOutlined />
                    <span>等待支付中... 剩余时间：{formatTime(countdown)}</span>
                  </Space>
                }
                type="info"
                showIcon={false}
              />

              {/* 支付步骤 */}
              <Steps current={1} size="small" className="mt-4">
                <Step title="创建订单" />
                <Step title="扫码支付" />
                <Step title="支付完成" />
              </Steps>
            </Space>
          </div>
        )

      case 'success':
        return (
          <Result
            status="success"
            title="支付成功！"
            subTitle={`您已成功升级到${planName}，感谢您的支持！`}
            icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            extra={[
              <Button type="primary" key="ok" onClick={onSuccess}>
                完成
              </Button>
            ]}
          />
        )

      case 'failed':
        return (
          <Result
            status="error"
            title="支付失败"
            subTitle="支付过程中出现错误，请重试或联系客服"
            icon={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            extra={[
              <Button type="primary" key="retry" onClick={handleRetry} icon={<ReloadOutlined />}>
                重新支付
              </Button>,
              <Button key="cancel" onClick={onCancel}>
                取消
              </Button>
            ]}
          />
        )

      case 'timeout':
        return (
          <Result
            status="warning"
            title="支付超时"
            subTitle="支付二维码已过期，请重新发起支付"
            extra={[
              <Button type="primary" key="retry" onClick={handleRetry} icon={<ReloadOutlined />}>
                重新支付
              </Button>,
              <Button key="cancel" onClick={onCancel}>
                取消
              </Button>
            ]}
          />
        )

      default:
        return null
    }
  }

  return (
    <Modal
      title={status === 'pending' ? '扫码支付' : '支付状态'}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
      centered
      maskClosable={false}
    >
      {renderContent()}
    </Modal>
  )
}

export default PaymentModal

