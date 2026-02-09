import React from 'react'
import { Typography, Card, Divider, Space, Alert, Table, Tag } from 'antd'
import { CrownOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const PricingTerms: React.FC = () => {
  // 个人版套餐对比数据
  const personalPricingData = [
    { key: '1', feature: 'WPS文件数量', free: '10个', personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个' },
    { key: '2', feature: 'PQR文件数量', free: '10个', personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个' },
    { key: '3', feature: 'pPQR文件数量', free: '不支持', personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个' },
    { key: '4', feature: '焊材管理', free: '不支持', personal_pro: '50个', personal_advanced: '100个', personal_flagship: '200个' },
    { key: '5', feature: '焊工管理', free: '不支持', personal_pro: '20个', personal_advanced: '50个', personal_flagship: '100个' },
    { key: '6', feature: '设备管理', free: '不支持', personal_pro: '不支持', personal_advanced: '20个', personal_flagship: '50个' },
    { key: '7', feature: '生产/质量管理', free: '不支持', personal_pro: '不支持', personal_advanced: '支持', personal_flagship: '支持' },
  ]

  // 企业版套餐对比数据
  const enterprisePricingData = [
    { key: '1', feature: 'WPS文件数量', enterprise: '200个', enterprise_pro: '400个', enterprise_pro_max: '500个' },
    { key: '2', feature: 'PQR文件数量', enterprise: '200个', enterprise_pro: '400个', enterprise_pro_max: '500个' },
    { key: '3', feature: 'pPQR文件数量', enterprise: '200个', enterprise_pro: '400个', enterprise_pro_max: '500个' },
    { key: '4', feature: '焊材管理', enterprise: '500个', enterprise_pro: '1000个', enterprise_pro_max: '2000个' },
    { key: '5', feature: '焊工管理', enterprise: '200个', enterprise_pro: '500个', enterprise_pro_max: '1000个' },
    { key: '6', feature: '设备管理', enterprise: '100个', enterprise_pro: '300个', enterprise_pro_max: '500个' },
    { key: '7', feature: '员工管理', enterprise: '10人', enterprise_pro: '20人', enterprise_pro_max: '50人' },
    { key: '8', feature: '多工厂数量', enterprise: '1个', enterprise_pro: '3个', enterprise_pro_max: '5个' },
  ]

  const personalColumns = [
    { title: '功能特性', dataIndex: 'feature', key: 'feature', width: 150, fixed: 'left' as const },
    { title: <><Tag color="default">个人免费版</Tag><br/><Text type="secondary">¥0</Text></>, dataIndex: 'free', key: 'free', align: 'center' as const },
    { title: <><Tag color="blue">个人专业版</Tag><br/><Text type="secondary">¥19/月</Text></>, dataIndex: 'personal_pro', key: 'personal_pro', align: 'center' as const },
    { title: <><Tag color="gold">个人高级版</Tag><br/><Text type="secondary">¥49/月</Text></>, dataIndex: 'personal_advanced', key: 'personal_advanced', align: 'center' as const },
    { title: <><Tag color="purple">个人旗舰版</Tag><br/><Text type="secondary">¥99/月</Text></>, dataIndex: 'personal_flagship', key: 'personal_flagship', align: 'center' as const },
  ]

  const enterpriseColumns = [
    { title: '功能特性', dataIndex: 'feature', key: 'feature', width: 150, fixed: 'left' as const },
    { title: <><Tag color="cyan">企业版</Tag><br/><Text type="secondary">¥199/月</Text></>, dataIndex: 'enterprise', key: 'enterprise', align: 'center' as const },
    { title: <><Tag color="geekblue">企业版PRO</Tag><br/><Text type="secondary">¥399/月</Text></>, dataIndex: 'enterprise_pro', key: 'enterprise_pro', align: 'center' as const },
    { title: <><Tag color="magenta">企业版PRO MAX</Tag><br/><Text type="secondary">¥899/月</Text></>, dataIndex: 'enterprise_pro_max', key: 'enterprise_pro_max', align: 'center' as const },
  ]

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#f0f2f5', 
      padding: '40px 20px' 
    }}>
      <Card 
        style={{ 
          maxWidth: 1200, 
          margin: '0 auto',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <CrownOutlined style={{ fontSize: 48, color: '#faad14', marginBottom: 16 }} />
            <Title level={2}>价格与自动续费说明</Title>
            <Text type="secondary">最后更新日期：2025年10月29日</Text>
          </div>

          <Divider />

          <Typography>
            {/* 个人版套餐 */}
            <Title level={3}>一、个人版会员套餐</Title>

            <Alert
              message="个人版优惠"
              description="季付享9折优惠，年付享8折优惠！"
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              columns={personalColumns}
              dataSource={personalPricingData}
              pagination={false}
              bordered
              scroll={{ x: 800 }}
              style={{ marginBottom: 24 }}
            />

            <Paragraph>
              <Title level={4}>个人版价格说明：</Title>
              <ul>
                <li><strong>个人免费版</strong>：永久免费，适合个人用户试用基础功能</li>
                <li><strong>个人专业版</strong>：¥19/月，¥51/季（9折），¥183/年（8折）</li>
                <li><strong>个人高级版</strong>：¥49/月，¥132/季（9折），¥470/年（8折）</li>
                <li><strong>个人旗舰版</strong>：¥99/月，¥267/季（9折），¥950/年（8折）</li>
              </ul>
            </Paragraph>

            <Divider />

            {/* 企业版套餐 */}
            <Title level={3}>二、企业版会员套餐</Title>

            <Alert
              message="企业版优惠"
              description="季付享9折优惠，年付享8折优惠！企业版支持多工厂管理和员工协作。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Table
              columns={enterpriseColumns}
              dataSource={enterprisePricingData}
              pagination={false}
              bordered
              scroll={{ x: 800 }}
              style={{ marginBottom: 24 }}
            />

            <Paragraph>
              <Title level={4}>企业版价格说明：</Title>
              <ul>
                <li><strong>企业版</strong>：¥199/月，¥537/季（9折），¥1910/年（8折）</li>
                <li><strong>企业版PRO</strong>：¥399/月，¥1077/季（9折），¥3830/年（8折）</li>
                <li><strong>企业版PRO MAX</strong>：¥899/月，¥2427/季（9折），¥8630/年（8折）</li>
              </ul>
            </Paragraph>

            <Divider />

            <Title level={3}>三、自动续费说明</Title>
            <Title level={4}>2.1 什么是自动续费</Title>
            <Paragraph>
              自动续费是一项便捷的服务，开通后系统会在您的会员到期前自动为您续费，
              确保您的服务不中断。您无需手动操作，即可持续享受会员权益。
            </Paragraph>

            <Title level={4}>2.2 如何开通自动续费</Title>
            <Paragraph>
              您可以在以下场景开通自动续费：
            </Paragraph>
            <ul>
              <li>首次购买会员时，勾选"开通自动续费"选项</li>
              <li>在"个人中心" → "订阅管理"中开通自动续费</li>
              <li>会员到期前，通过系统提醒开通自动续费</li>
            </ul>

            <Title level={4}>2.3 自动续费规则</Title>
            <ul>
              <li><Text strong>续费时间：</Text>系统将在您的会员到期前24小时自动扣费续费</li>
              <li><Text strong>续费周期：</Text>与您当前的订阅周期一致（月付续月，年付续年）</li>
              <li><Text strong>续费价格：</Text>按照续费时的官方价格执行（可能与首次购买价格不同）</li>
              <li><Text strong>扣费方式：</Text>从您绑定的支付方式中自动扣费</li>
              <li><Text strong>续费通知：</Text>扣费前3天、扣费当天会通过邮件/短信/站内消息提醒您</li>
            </ul>

            <Title level={4}>2.4 如何关闭自动续费</Title>
            <Paragraph>
              您可以随时关闭自动续费，不收取任何费用：
            </Paragraph>
            <ul>
              <li>登录系统，进入"个人中心" → "订阅管理"</li>
              <li>找到当前订阅，点击"管理自动续费"</li>
              <li>点击"关闭自动续费"按钮，确认操作</li>
              <li>关闭后，您的会员权益将持续到当前订阅期结束</li>
            </ul>

            <Alert
              message="重要提示"
              description="关闭自动续费后，您的会员权益将在当前订阅期结束后失效。如需继续使用，请在到期前手动续费。"
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />

            <Title level={4}>2.5 自动续费失败</Title>
            <Paragraph>
              如果自动续费失败（如余额不足、支付方式失效等），系统会：
            </Paragraph>
            <ul>
              <li>立即通过邮件/短信/站内消息通知您</li>
              <li>在接下来的3天内每天重试一次</li>
              <li>如3天后仍未成功，您的会员权益将暂停</li>
              <li>您可以手动完成支付以恢复会员权益</li>
            </ul>

            <Title level={3}>四、支付方式</Title>
            <Paragraph>
              我们支持以下支付方式：
            </Paragraph>
            <ul>
              <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 支付宝</li>
              <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 微信支付</li>
              <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 银行卡支付</li>
              <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 企业对公转账（仅限企业版）</li>
            </ul>

            <Title level={3}>五、发票说明</Title>
            <Title level={4}>4.1 个人用户</Title>
            <Paragraph>
              个人用户可以申请电子发票，发票类型为"增值税电子普通发票"。
            </Paragraph>

            <Title level={4}>4.2 企业用户</Title>
            <Paragraph>
              企业用户可以申请增值税专用发票或增值税普通发票。
              申请时需提供企业税务信息（企业名称、纳税人识别号、地址、电话、开户行及账号等）。
            </Paragraph>

            <Title level={4}>4.3 发票申请</Title>
            <Paragraph>
              您可以在"个人中心" → "订阅管理" → "发票管理"中申请发票。
              我们将在收到申请后5个工作日内开具并发送至您的邮箱。
            </Paragraph>

            <Title level={3}>六、升级与降级</Title>
            <Title level={4}>5.1 套餐升级</Title>
            <Paragraph>
              您可以随时升级到更高级别的套餐。升级后：
            </Paragraph>
            <ul>
              <li>立即享受新套餐的全部权益</li>
              <li>原套餐剩余时长将按比例折算成新套餐时长</li>
              <li>只需补齐差价即可</li>
            </ul>

            <Title level={4}>5.2 套餐降级</Title>
            <Paragraph>
              您可以在当前订阅期结束前申请降级。降级后：
            </Paragraph>
            <ul>
              <li>降级将在当前订阅期结束后生效</li>
              <li>降级后的权益将相应调整</li>
              <li>如您的数据超出新套餐限制，需要在降级前清理</li>
            </ul>

            <Title level={3}>七、退款政策</Title>
            <Paragraph>
              关于退款的详细规定，请参见《退款政策》。
            </Paragraph>

            <Title level={3}>八、价格调整</Title>
            <Paragraph>
              我们保留调整价格的权利。价格调整将提前30天通知您。
            </Paragraph>
            <ul>
              <li>已购买的订阅不受价格调整影响</li>
              <li>自动续费用户将按新价格续费（续费前会通知）</li>
              <li>如您不接受新价格，可以在调整前关闭自动续费</li>
            </ul>

            <Title level={3}>九、常见问题</Title>
            <Title level={4}>Q1: 开通自动续费有优惠吗？</Title>
            <Paragraph>
              A: 目前开通自动续费暂无额外优惠，但我们会不定期推出自动续费专享活动，请关注系统通知。
            </Paragraph>

            <Title level={4}>Q2: 自动续费可以随时关闭吗？</Title>
            <Paragraph>
              A: 是的，您可以随时关闭自动续费，不收取任何费用。关闭后，您的会员权益将持续到当前订阅期结束。
            </Paragraph>

            <Title level={4}>Q3: 如果我关闭了自动续费，还能重新开通吗？</Title>
            <Paragraph>
              A: 可以。您可以随时在"个人中心" → "订阅管理"中重新开通自动续费。
            </Paragraph>

            <Title level={4}>Q4: 自动续费失败会影响我的数据吗？</Title>
            <Paragraph>
              A: 不会。即使自动续费失败，您的数据仍然安全保存。
              但您可能无法使用部分会员功能，直到完成续费。
            </Paragraph>

            <Title level={4}>Q5: 企业版和个人版有什么区别？</Title>
            <Paragraph>
              A: 企业版支持多工厂管理和员工协作功能，配额更高，适合团队使用。
              个人版仅支持单人使用，配额相对较低，适合个人用户。
            </Paragraph>

            <Title level={3}>十、联系我们</Title>
            <Paragraph>
              如果您对价格或自动续费有任何疑问，请通过以下方式联系我们：
            </Paragraph>
            <ul>
              <li><Text strong>销售咨询：</Text>sales@weldingsystem.com</li>
              <li><Text strong>客服电话：</Text>400-XXX-XXXX</li>
              <li><Text strong>在线客服：</Text>登录系统后点击右下角客服图标</li>
            </ul>

            <Divider />

            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <Text type="secondary">
                本说明的解释权归焊接工艺管理系统所有
              </Text>
            </div>
          </Typography>
        </Space>
      </Card>
    </div>
  )
}

export default PricingTerms

