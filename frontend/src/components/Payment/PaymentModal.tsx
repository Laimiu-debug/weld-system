import React, { useEffect, useRef, useState } from 'react'
import {
  Modal,
  QRCode,
  Spin,
  Result,
  Button,
  Space,
  Typography,
  Alert,
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
  paymentMethod: 'alipay' | 'wechat'
  qrCode?: string
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
  qrCode,
  onSuccess,
  onCancel
}) => {
  const [status, setStatus] = useState<PaymentStatus>(qrCode ? 'pending' : 'loading')
  const [qrCodeUrl, setQrCodeUrl] = useState(qrCode || '')
  const [countdown, setCountdown] = useState(300)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearTimers = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
      countdownRef.current = null
    }
  }

  useEffect(() => {
    if (visible && orderId) {
      setQrCodeUrl(qrCode || '')
      setCountdown(300)
      setStatus(qrCode ? 'pending' : 'loading')
      startPolling()
      startCountdown()
    }

    return () => {
      clearTimers()
    }
  }, [visible, orderId, qrCode])

  const startPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    const checkStatus = async () => {
      try {
        const response = await apiService.get(`/payments/status/${orderId}`)
        if (response.data?.success) {
          const paymentStatus = response.data.data?.status
          if (paymentStatus === 'success') {
            setStatus('success')
            clearTimers()
            setTimeout(() => {
              onSuccess()
            }, 2000)
          } else if (paymentStatus === 'failed' || paymentStatus === 'rejected') {
            setStatus('failed')
            clearTimers()
          } else {
            setStatus('pending')
          }
        }
      } catch (error) {
        console.error('Payment status check failed:', error)
      }
    }
    void checkStatus()
    pollingRef.current = setInterval(() => {
      void checkStatus()
    }, 3000)
  }

  const startCountdown = () => {
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
      countdownRef.current = null
    }
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          setStatus('timeout')
          clearTimers()
          return 0
        }
        return prev - 1
      })
    }, 1000)
    countdownRef.current = interval
  }

  const handleRetry = () => {
    if (!qrCodeUrl) {
      message.warning('请关闭后重新发起支付')
      return
    }
    setCountdown(300)
    setStatus('pending')
    startPolling()
    startCountdown()
  }

  const getPaymentIcon = () => {
    switch (paymentMethod) {
      case 'alipay':
        return <AlipayOutlined style={{ fontSize: 48, color: '#1677ff' }} />
      case 'wechat':
        return <WechatOutlined style={{ fontSize: 48, color: '#07c160' }} />
      default: {
        const _exhaustive: never = paymentMethod
        return _exhaustive
      }
    }
  }

  const getPaymentMethodName = () => {
    switch (paymentMethod) {
      case 'alipay':
        return '支付宝'
      case 'wechat':
        return '微信支付'
      default: {
        const _exhaustive: never = paymentMethod
        return _exhaustive
      }
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
            <Spin size="large" tip="正在确认支付订单..." />
          </div>
        )

      case 'pending':
        return (
          <div className="text-center">
            <Space direction="vertical" size="large" className="w-full">
              <div>{getPaymentIcon()}</div>
              <Card className="inline-block">
                {qrCodeUrl ? (
                  <QRCode value={qrCodeUrl} size={256} />
                ) : (
                  <div style={{ width: 256, height: 256 }} className="flex items-center justify-center">
                    <Spin />
                  </div>
                )}
              </Card>
              <div>
                <Title level={4}>请使用{getPaymentMethodName()}扫码支付</Title>
                <Paragraph type="secondary">
                  订单金额：<Text strong className="text-2xl text-red-500">¥{amount.toFixed(2)}</Text>
                </Paragraph>
              </div>
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
            subTitle={`您已成功开通${planName}，感谢您的支持！`}
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
                重新查询
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
            subTitle="可关闭后重新进入本页继续支付，请勿重复下单"
            extra={[
              <Button type="primary" key="retry" onClick={handleRetry} icon={<ReloadOutlined />}>
                继续等待
              </Button>,
              <Button key="cancel" onClick={onCancel}>
                取消
              </Button>
            ]}
          />
        )

      default: {
        const _exhaustive: never = status
        return _exhaustive
      }
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
