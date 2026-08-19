import React from 'react'
import { Typography, Card, Divider, Space } from 'antd'
import { SafetyCertificateOutlined } from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const PrivacyPolicy: React.FC = () => {
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
            <SafetyCertificateOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <Title level={2}>隐私政策</Title>
            <Text type="secondary">最后更新日期：2025年10月29日</Text>
          </div>

          <Divider />

          <Typography>
            <Title level={3}>引言</Title>
            <Paragraph>
              欢迎使用焊序（以下简称"本系统"或"我们"）。我们非常重视您的隐私保护和个人信息安全。
              本隐私政策旨在向您说明我们如何收集、使用、存储、共享和保护您的个人信息，以及您享有的相关权利。
            </Paragraph>
            <Paragraph>
              请您在使用本系统前，仔细阅读并充分理解本隐私政策。如果您不同意本隐私政策的任何内容，
              请您立即停止使用本系统。您使用或继续使用本系统，即表示您同意我们按照本隐私政策收集、使用、存储和共享您的相关信息。
            </Paragraph>

            <Title level={3}>一、我们收集的信息</Title>
            <Title level={4}>1.1 您主动提供的信息</Title>
            <Paragraph>
              在您注册账号、使用本系统服务时，您可能需要向我们提供以下信息：
            </Paragraph>
            <ul>
              <li><Text strong>账号信息：</Text>用户名、邮箱地址、手机号码、密码等</li>
              <li><Text strong>企业信息：</Text>企业名称、统一社会信用代码、企业地址、联系方式等</li>
              <li><Text strong>个人信息：</Text>姓名、职位、部门、工号等</li>
              <li><Text strong>业务数据：</Text>焊接工艺规程(WPS)、工艺评定记录(PQR)、焊工信息、设备信息、材料信息等</li>
            </ul>

            <Title level={4}>1.2 我们自动收集的信息</Title>
            <Paragraph>
              在您使用本系统服务时，我们可能会自动收集以下信息：
            </Paragraph>
            <ul>
              <li><Text strong>设备信息：</Text>设备型号、操作系统版本、设备标识符、IP地址等</li>
              <li><Text strong>日志信息：</Text>访问时间、访问页面、操作记录、错误日志等</li>
              <li><Text strong>位置信息：</Text>基于IP地址的大致地理位置（如需要）</li>
            </ul>

            <Title level={3}>二、我们如何使用收集的信息</Title>
            <Paragraph>
              我们会将收集的信息用于以下目的：
            </Paragraph>
            <ul>
              <li><Text strong>提供服务：</Text>为您提供焊接工艺管理、文档编辑、数据存储等核心功能</li>
              <li><Text strong>账号管理：</Text>创建和管理您的账号，验证您的身份</li>
              <li><Text strong>改进服务：</Text>分析使用情况，优化产品功能和用户体验</li>
              <li><Text strong>安全保障：</Text>检测和防范安全威胁，保护您的账号和数据安全</li>
              <li><Text strong>客户支持：</Text>响应您的咨询和投诉，提供技术支持</li>
              <li><Text strong>通知推送：</Text>向您发送系统通知、更新提醒、营销信息（您可以选择退订）</li>
              <li><Text strong>法律合规：</Text>遵守适用的法律法规和监管要求</li>
            </ul>

            <Title level={3}>三、信息的存储</Title>
            <Title level={4}>3.1 存储地点</Title>
            <Paragraph>
              您的个人信息和业务数据将存储在中华人民共和国境内的服务器上。
              如需跨境传输，我们将严格遵守相关法律法规的要求。
            </Paragraph>

            <Title level={4}>3.2 存储期限</Title>
            <Paragraph>
              我们仅在实现本隐私政策所述目的所必需的期限内保留您的个人信息。
              在您注销账号或要求删除信息后，我们将在合理期限内删除或匿名化处理您的个人信息，
              除非法律法规另有规定。
            </Paragraph>

            <Title level={3}>四、信息的共享、转让和公开披露</Title>
            <Title level={4}>4.1 共享</Title>
            <Paragraph>
              我们不会与第三方共享您的个人信息，除非：
            </Paragraph>
            <ul>
              <li>获得您的明确同意</li>
              <li>根据法律法规或监管机构的要求</li>
              <li>与我们的关联公司共享（我们会要求其遵守本隐私政策）</li>
              <li>与授权合作伙伴共享（仅限于提供服务所必需，且受保密协议约束）</li>
            </ul>

            <Title level={4}>4.2 转让</Title>
            <Paragraph>
              我们不会将您的个人信息转让给任何公司、组织和个人，除非：
            </Paragraph>
            <ul>
              <li>获得您的明确同意</li>
              <li>在涉及合并、收购或破产清算时，如涉及个人信息转让，我们会要求新的持有您个人信息的公司、组织继续受本隐私政策的约束</li>
            </ul>

            <Title level={4}>4.3 公开披露</Title>
            <Paragraph>
              我们仅会在以下情况下公开披露您的个人信息：
            </Paragraph>
            <ul>
              <li>获得您的明确同意</li>
              <li>基于法律法规、法律程序、诉讼或政府主管部门的强制性要求</li>
            </ul>

            <Title level={3}>五、信息安全</Title>
            <Paragraph>
              我们非常重视信息安全，采取了以下措施保护您的个人信息：
            </Paragraph>
            <ul>
              <li><Text strong>数据加密：</Text>使用SSL/TLS加密传输，对敏感数据进行加密存储</li>
              <li><Text strong>访问控制：</Text>严格的权限管理和身份认证机制</li>
              <li><Text strong>安全审计：</Text>定期进行安全评估和漏洞扫描</li>
              <li><Text strong>备份恢复：</Text>定期备份数据，确保数据可恢复性</li>
              <li><Text strong>员工培训：</Text>对员工进行信息安全培训，签署保密协议</li>
            </ul>
            <Paragraph>
              尽管我们已采取合理措施保护您的信息，但请您理解，由于技术限制和各种恶意手段的存在，
              即便我们竭尽所能加强安全措施，也无法始终保证信息的百分之百安全。
            </Paragraph>

            <Title level={3}>六、您的权利</Title>
            <Paragraph>
              根据相关法律法规，您享有以下权利：
            </Paragraph>
            <ul>
              <li><Text strong>访问权：</Text>您有权访问您的个人信息</li>
              <li><Text strong>更正权：</Text>您有权更正不准确或不完整的个人信息</li>
              <li><Text strong>删除权：</Text>在特定情况下，您有权要求删除您的个人信息</li>
              <li><Text strong>撤回同意：</Text>您有权撤回您此前作出的同意</li>
              <li><Text strong>注销账号：</Text>您有权注销您的账号</li>
              <li><Text strong>投诉举报：</Text>您有权向监管部门投诉举报</li>
            </ul>
            <Paragraph>
              如需行使上述权利，请通过本隐私政策底部的联系方式与我们联系。
            </Paragraph>

            <Title level={3}>七、未成年人保护</Title>
            <Paragraph>
              本系统主要面向企业用户，不针对未成年人。如果您是未成年人，请在监护人的陪同下阅读本隐私政策，
              并在监护人同意的前提下使用本系统。
            </Paragraph>

            <Title level={3}>八、隐私政策的更新</Title>
            <Paragraph>
              我们可能会不时更新本隐私政策。更新后的隐私政策将在本页面发布，并在页面顶部标注最后更新日期。
              如果更新内容会导致您在本隐私政策下权利的实质减少，我们将在更新前通过显著方式通知您。
            </Paragraph>

            <Title level={3}>九、联系我们</Title>
            <Paragraph>
              如果您对本隐私政策有任何疑问、意见或建议，或需要行使您的权利，请通过以下方式联系我们：
            </Paragraph>
            <ul>
              <li><Text strong>邮箱：</Text>privacy@weldingsystem.com</li>
              <li><Text strong>电话：</Text>400-XXX-XXXX</li>
              <li><Text strong>地址：</Text>中国（请根据实际情况填写）</li>
            </ul>
            <Paragraph>
              我们将在收到您的请求后15个工作日内予以回复。
            </Paragraph>

            <Divider />

            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <Text type="secondary">
                本隐私政策的解释权归焊序所有
              </Text>
            </div>
          </Typography>
        </Space>
      </Card>
    </div>
  )
}

export default PrivacyPolicy

