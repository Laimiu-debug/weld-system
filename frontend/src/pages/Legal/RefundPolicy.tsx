import React from 'react'
import { Typography, Card, Divider, Space, Alert } from 'antd'
import { DollarOutlined } from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const RefundPolicy: React.FC = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#f0f2f5', 
      padding: '40px 20px' 
    }}>
      <Card 
        style={{ 
          maxWidth: 1000, 
          margin: '0 auto',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <DollarOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <Title level={2}>退款政策</Title>
            <Text type="secondary">最后更新日期：2025年10月29日</Text>
          </div>

          <Divider />

          <Alert
            message="重要提示"
            description="请在购买前仔细阅读本退款政策。一旦您完成支付，即表示您已充分理解并同意本退款政策的全部内容。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Typography>
            <Title level={3}>一、退款原则</Title>
            <Paragraph>
              焊序致力于为用户提供优质的服务。我们理解在某些情况下，
              您可能需要申请退款。本退款政策旨在明确退款的条件、流程和时限。
            </Paragraph>

            <Title level={3}>二、可退款情形</Title>
            <Title level={4}>2.1 服务未开通</Title>
            <Paragraph>
              如果您已完成支付但服务尚未开通（通常在支付后24小时内），您可以申请全额退款。
            </Paragraph>

            <Title level={4}>2.2 技术故障</Title>
            <Paragraph>
              如果因我们的技术故障导致您无法正常使用服务，且在合理期限内（通常为7个工作日）
              未能解决问题，您可以申请按比例退款或全额退款。
            </Paragraph>

            <Title level={4}>2.3 重复支付</Title>
            <Paragraph>
              如果您因系统错误或其他原因重复支付，我们将在核实后退还重复支付的款项。
            </Paragraph>

            <Title level={4}>2.4 服务降级</Title>
            <Paragraph>
              如果我们对服务进行了重大调整，导致服务质量明显下降，
              且您在调整后7天内提出退款申请，我们将按比例退还剩余服务期的费用。
            </Paragraph>

            <Title level={3}>三、不可退款情形</Title>
            <Title level={4}>3.1 已使用的服务</Title>
            <Paragraph>
              对于已经开通并使用超过7天的服务，原则上不予退款。
              但如果存在本政策第二条所述的特殊情况，我们将根据实际情况处理。
            </Paragraph>

            <Title level={4}>3.2 违规使用</Title>
            <Paragraph>
              如果您因违反《用户服务协议》而被终止服务，已支付的费用不予退还。
            </Paragraph>

            <Title level={4}>3.3 主观原因</Title>
            <Paragraph>
              因您个人原因（如不再需要、改变主意等）导致的退款申请，
              我们将根据具体情况决定是否退款及退款金额。
            </Paragraph>

            <Title level={4}>3.4 促销活动</Title>
            <Paragraph>
              通过促销活动、优惠券、折扣等方式购买的服务，
              如活动规则中明确说明不可退款，则不予退款。
            </Paragraph>

            <Title level={3}>四、退款金额计算</Title>
            <Title level={4}>4.1 全额退款</Title>
            <Paragraph>
              适用于服务未开通、重复支付等情况，退还您实际支付的全部金额。
            </Paragraph>

            <Title level={4}>4.2 按比例退款</Title>
            <Paragraph>
              适用于服务已部分使用的情况，退款金额计算公式如下：
            </Paragraph>
            <Paragraph>
              <Text code>
                退款金额 = 实际支付金额 × (剩余天数 / 总天数)
              </Text>
            </Paragraph>
            <Paragraph>
              <Text type="secondary">
                注：剩余天数从退款申请审核通过之日起计算；
                如使用了优惠券或折扣，退款金额将基于实际支付金额计算。
              </Text>
            </Paragraph>

            <Title level={4}>4.3 扣除费用</Title>
            <Paragraph>
              在某些情况下，我们可能会扣除以下费用：
            </Paragraph>
            <ul>
              <li>支付渠道手续费（如适用）</li>
              <li>已使用的资源费用（如超出免费额度的存储空间、流量等）</li>
              <li>其他合理费用</li>
            </ul>

            <Title level={3}>五、退款流程</Title>
            <Title level={4}>5.1 提交申请</Title>
            <Paragraph>
              您可以通过以下方式提交退款申请：
            </Paragraph>
            <ul>
              <li>在系统内通过"个人中心" → "订阅管理" → "申请退款"提交</li>
              <li>发送邮件至 refund@weldingsystem.com，邮件标题注明"退款申请"</li>
              <li>拨打客服电话 400-XXX-XXXX</li>
            </ul>
            <Paragraph>
              申请时请提供以下信息：
            </Paragraph>
            <ul>
              <li>账号信息（用户名、邮箱或手机号）</li>
              <li>订单号</li>
              <li>退款原因</li>
              <li>相关证明材料（如适用）</li>
            </ul>

            <Title level={4}>5.2 审核处理</Title>
            <Paragraph>
              我们将在收到您的退款申请后3个工作日内完成审核，并通过邮件或站内消息通知您审核结果。
            </Paragraph>

            <Title level={4}>5.3 退款到账</Title>
            <Paragraph>
              退款申请审核通过后，我们将在5个工作日内将款项退还至您的原支付账户。
              具体到账时间取决于支付渠道的处理速度，通常为3-7个工作日。
            </Paragraph>

            <Title level={3}>六、特殊说明</Title>
            <Title level={4}>6.1 企业版退款</Title>
            <Paragraph>
              企业版用户的退款申请需要由企业管理员提交，并提供企业相关证明文件。
              退款金额将退还至企业支付账户。
            </Paragraph>

            <Title level={4}>6.2 自动续费退款</Title>
            <Paragraph>
              如果您开通了自动续费，但在续费后希望退款，请参考本政策第二条和第三条的规定。
              建议您在不需要继续使用服务时，提前关闭自动续费功能。
            </Paragraph>

            <Title level={4}>6.3 第三方支付</Title>
            <Paragraph>
              如果您通过第三方支付平台（如支付宝、微信支付等）完成支付，
              退款将原路退回至您的支付账户。如遇到退款问题，请同时联系支付平台客服。
            </Paragraph>

            <Title level={3}>七、争议解决</Title>
            <Paragraph>
              如果您对退款决定有异议，可以通过以下方式申诉：
            </Paragraph>
            <ul>
              <li>发送邮件至 appeal@weldingsystem.com</li>
              <li>拨打客服电话 400-XXX-XXXX</li>
            </ul>
            <Paragraph>
              我们将在收到申诉后5个工作日内重新审核并给予答复。
            </Paragraph>

            <Title level={3}>八、政策变更</Title>
            <Paragraph>
              我们保留随时修改本退款政策的权利。修改后的政策将在本页面发布，
              并在页面顶部标注最后更新日期。修改后的政策仅适用于修改后发生的交易。
            </Paragraph>

            <Title level={3}>九、联系我们</Title>
            <Paragraph>
              如果您对本退款政策有任何疑问，或需要申请退款，请通过以下方式联系我们：
            </Paragraph>
            <ul>
              <li><Text strong>退款专用邮箱：</Text>refund@weldingsystem.com</li>
              <li><Text strong>客服电话：</Text>400-XXX-XXXX（工作时间：周一至周五 9:00-18:00）</li>
              <li><Text strong>在线客服：</Text>登录系统后点击右下角客服图标</li>
            </ul>

            <Divider />

            <Alert
              message="温馨提示"
              description={
                <div>
                  <p>• 为了保障您的权益，请在购买前充分了解服务内容和本退款政策</p>
                  <p>• 如有疑问，请在购买前咨询客服</p>
                  <p>• 保留好订单号和支付凭证，以便在需要时申请退款</p>
                  <p>• 我们承诺公平、公正地处理每一笔退款申请</p>
                </div>
              }
              type="success"
              showIcon
              style={{ marginTop: 24 }}
            />

            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <Text type="secondary">
                本退款政策的解释权归焊序所有
              </Text>
            </div>
          </Typography>
        </Space>
      </Card>
    </div>
  )
}

export default RefundPolicy

