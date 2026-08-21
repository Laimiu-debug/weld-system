import React, { useState } from 'react'
import { Modal, Image, Input, Button, message, Steps, Alert, Space, Typography } from 'antd'
import { CopyOutlined, CheckCircleOutlined } from '@ant-design/icons'

const { Text, Title } = Typography

interface ManualPaymentModalProps {
  visible: boolean
  orderId: string
  amount: number
  planName: string
  paymentMethod: 'alipay' | 'wechat'
  onSuccess: () => void
  onCancel: () => void
}

const ManualPaymentModal: React.FC<ManualPaymentModalProps> = ({
  visible,
  orderId,
  amount,
  planName,
  paymentMethod,
  onSuccess,
  onCancel
}) => {
  const [step, setStep] = useState(0)
  const [transactionId, setTransactionId] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // 收款码图片路径
  const qrCodePath = paymentMethod === 'alipay'
    ? '/qrcode/alipay.JPG'
    : '/qrcode/wechat.JPG'

  const paymentName = paymentMethod === 'alipay' ? '支付宝' : '微信'

  // 复制订单号
  const copyOrderId = () => {
    navigator.clipboard.writeText(orderId)
    message.success('订单号已复制')
  }

  // 提交支付凭证
  const handleSubmit = async () => {
    if (!transactionId || transactionId.trim().length === 0) {
      message.error('请输入支付凭证号')
      return
    }

    setSubmitting(true)
    try {
      const response = await fetch('/api/v1/payments/manual-confirm', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          order_id: orderId,
          transaction_id: transactionId.trim(),
          payment_method: paymentMethod
        })
      })

      const data = await response.json()

      if (response.ok) {
        message.success('支付凭证已提交，请等待管理员确认')
        setStep(2)
      } else {
        message.error(data.detail || '提交失败，请重试')
      }
    } catch (error) {
      message.error('网络错误，请重试')
    } finally {
      setSubmitting(false)
    }
  }

  // 重置状态
  const handleClose = () => {
    setStep(0)
    setTransactionId('')
    onCancel()
  }

  return (
    <Modal
      title={`${paymentName}扫码支付`}
      open={visible}
      onCancel={handleClose}
      footer={null}
      width={600}
      destroyOnClose
    >
      <Steps current={step} style={{ marginBottom: 32 }}>
        <Steps.Step title="扫码支付" />
        <Steps.Step title="提交凭证" />
        <Steps.Step title="等待确认" />
      </Steps>

      {/* 第一步：扫码支付 */}
      {step === 0 && (
        <div style={{ textAlign: 'center' }}>
          <Alert
            message="支付说明"
            description={
              <div style={{ textAlign: 'left' }}>
                <p>1. 请使用{paymentName}扫描下方二维码</p>
                <p>2. 支付时请在备注中填写订单号</p>
                <p>3. 支付完成后点击"我已完成支付"</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 24, textAlign: 'left' }}
          />

          <Title level={4}>请使用{paymentName}扫码支付</Title>
          
          <div style={{ 
            display: 'inline-block',
            padding: 20,
            background: '#f5f5f5',
            borderRadius: 8,
            marginBottom: 20
          }}>
            <Image 
              src={qrCodePath} 
              width={280} 
              preview={false}
              fallback="/qrcode/placeholder.svg"
            />
          </div>

          <div style={{ 
            background: '#fff7e6',
            border: '1px solid #ffd591',
            borderRadius: 8,
            padding: 20,
            marginBottom: 20
          }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <Text type="secondary">支付金额：</Text>
                <Text strong style={{ fontSize: 28, color: '#ff4d4f' }}>
                  ¥{amount.toFixed(2)}
                </Text>
              </div>
              
              <div>
                <Text type="secondary">订单号：</Text>
                <Text strong>{orderId}</Text>
                <Button 
                  type="link" 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={copyOrderId}
                >
                  复制
                </Button>
              </div>
              
              <div>
                <Text type="secondary">套餐：</Text>
                <Text strong>{planName}</Text>
              </div>
            </Space>
          </div>

          <Alert
            message={
              <span>
                <strong style={{ color: '#ff4d4f' }}>重要：</strong>
                请在支付备注中填写订单号：<strong>{orderId}</strong>
              </span>
            }
            type="warning"
            showIcon
            style={{ marginBottom: 20 }}
          />

          <Button 
            type="primary" 
            size="large"
            onClick={() => setStep(1)}
            block
          >
            我已完成支付
          </Button>
        </div>
      )}

      {/* 第二步：提交凭证 */}
      {step === 1 && (
        <div>
          <Alert
            message="如何查找交易号？"
            description={
              <div>
                <p><strong>{paymentName}查找方法：</strong></p>
                {paymentMethod === 'alipay' ? (
                  <ol style={{ paddingLeft: 20, margin: 0 }}>
                    <li>打开支付宝APP</li>
                    <li>点击右下角"我的" → "账单"</li>
                    <li>找到刚才的支付记录</li>
                    <li>点击进入详情页</li>
                    <li>复制"交易号"（20位数字）</li>
                  </ol>
                ) : (
                  <ol style={{ paddingLeft: 20, margin: 0 }}>
                    <li>打开微信APP</li>
                    <li>点击右下角"我" → "服务" → "钱包" → "账单"</li>
                    <li>找到刚才的支付记录</li>
                    <li>点击进入详情页</li>
                    <li>复制"交易单号"</li>
                  </ol>
                )}
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Title level={5}>请输入支付凭证</Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
            请在{paymentName}的交易记录中找到交易号，并填写在下方
          </Text>

          <Input
            placeholder={`请输入${paymentName}交易号`}
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            size="large"
            style={{ marginBottom: 24 }}
            maxLength={50}
          />

          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button size="large" onClick={() => setStep(0)}>
              返回
            </Button>
            <Button 
              type="primary" 
              size="large"
              onClick={handleSubmit}
              loading={submitting}
            >
              提交凭证
            </Button>
          </Space>
        </div>
      )}

      {/* 第三步：等待确认 */}
      {step === 2 && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <CheckCircleOutlined 
            style={{ fontSize: 72, color: '#52c41a', marginBottom: 24 }} 
          />
          
          <Title level={3}>支付凭证已提交</Title>
          
          <div style={{ 
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 8,
            padding: 24,
            marginBottom: 24,
            textAlign: 'left'
          }}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text type="secondary">订单号：</Text>
                <Text strong>{orderId}</Text>
              </div>
              <div>
                <Text type="secondary">支付金额：</Text>
                <Text strong>¥{amount.toFixed(2)}</Text>
              </div>
              <div>
                <Text type="secondary">交易号：</Text>
                <Text strong>{transactionId}</Text>
              </div>
            </Space>
          </div>

          <Alert
            message="接下来会发生什么？"
            description={
              <div style={{ textAlign: 'left' }}>
                <p>✓ 我们将在 <strong>1-24小时</strong> 内确认您的支付</p>
                <p>✓ 确认后会自动开通会员权益</p>
                <p>✓ 您可以在"我的订单"中查看进度</p>
                <p>✓ 开通后会发送通知到您的邮箱</p>
              </div>
            }
            type="success"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Space>
            <Button onClick={handleClose}>
              关闭
            </Button>
            <Button type="primary" onClick={onSuccess}>
              查看我的订单
            </Button>
          </Space>
        </div>
      )}
    </Modal>
  )
}

export default ManualPaymentModal

