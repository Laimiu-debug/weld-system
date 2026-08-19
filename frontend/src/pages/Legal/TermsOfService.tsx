import React from 'react'
import { Typography, Card, Divider, Space } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const TermsOfService: React.FC = () => {
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
            <FileTextOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <Title level={2}>用户服务协议</Title>
            <Text type="secondary">最后更新日期：2025年10月29日</Text>
          </div>

          <Divider />

          <Typography>
            <Title level={3}>重要提示</Title>
            <Paragraph>
              欢迎您使用焊序（以下简称"本系统"或"我们"）！
            </Paragraph>
            <Paragraph>
              <Text strong>
                请您在注册成为用户之前，仔细阅读本《用户服务协议》（以下简称"本协议"）的全部内容，
                特别是免除或限制责任的条款、法律适用和争议解决条款。
              </Text>
            </Paragraph>
            <Paragraph>
              您点击"同意"或"注册"按钮，或您使用本系统服务，即表示您已充分阅读、理解并接受本协议的全部内容，
              与我们达成协议并成为本系统的用户。如果您不同意本协议的任何内容，请您立即停止注册或使用本系统服务。
            </Paragraph>

            <Title level={3}>一、协议的范围</Title>
            <Title level={4}>1.1 协议适用主体</Title>
            <Paragraph>
              本协议是您与焊序运营方之间关于您使用本系统服务所订立的协议。
            </Paragraph>

            <Title level={4}>1.2 协议关系及冲突条款</Title>
            <Paragraph>
              本协议内容同时包括我们可能不断发布的关于本系统服务的相关协议、规则等内容。
              上述内容一经正式发布，即为本协议不可分割的组成部分，您同样应当遵守。
            </Paragraph>

            <Title level={3}>二、账号注册与使用</Title>
            <Title level={4}>2.1 用户资格</Title>
            <Paragraph>
              您确认，在您完成注册程序或以其他我们允许的方式实际使用本系统服务时，您应当是具备完全民事权利能力和完全民事行为能力的自然人、法人或其他组织。
            </Paragraph>
            <Paragraph>
              若您是未成年人，您应在监护人的陪同下阅读本协议，并在取得监护人对您使用本系统服务的行为，
              以及对本协议全部条款的同意之后，方可使用本系统服务。
            </Paragraph>

            <Title level={4}>2.2 账号注册</Title>
            <ul>
              <li>您需要使用有效的邮箱地址或手机号码注册账号</li>
              <li>您应提供真实、准确、完整的注册信息</li>
              <li>您应及时更新您的注册信息，以保持其真实性、准确性和完整性</li>
              <li>您不得冒充他人或使用他人名义注册账号</li>
              <li>您不得恶意注册账号（包括但不限于频繁注册、批量注册账号等）</li>
            </ul>

            <Title level={4}>2.3 账号安全</Title>
            <ul>
              <li>您应妥善保管您的账号和密码，不得将账号出借、转让或出租给他人使用</li>
              <li>如发现账号被盗用或存在其他安全问题，您应立即通知我们</li>
              <li>因您保管不善导致的账号被盗用，由您自行承担责任</li>
              <li>您应对您账号下的所有行为负责</li>
            </ul>

            <Title level={3}>三、服务内容</Title>
            <Title level={4}>3.1 服务范围</Title>
            <Paragraph>
              本系统为您提供以下服务：
            </Paragraph>
            <ul>
              <li><Text strong>焊接工艺管理：</Text>WPS（焊接工艺规程）、PQR（工艺评定记录）、pPQR（预评定记录）的创建、编辑、存储和管理</li>
              <li><Text strong>资源管理：</Text>焊工信息、设备信息、材料信息的管理</li>
              <li><Text strong>模板管理：</Text>自定义模板的创建和使用</li>
              <li><Text strong>共享库：</Text>企业内部或跨企业的资源共享</li>
              <li><Text strong>数据导出：</Text>文档导出为PDF、Word等格式</li>
              <li><Text strong>权限管理：</Text>基于角色的访问控制</li>
              <li><Text strong>其他功能：</Text>我们可能不时推出的新功能</li>
            </ul>

            <Title level={4}>3.2 服务变更</Title>
            <Paragraph>
              我们保留随时修改、中断或终止部分或全部服务的权利。
              如因系统维护或升级需要暂停服务，我们将尽可能提前通知您。
            </Paragraph>

            <Title level={3}>四、用户行为规范</Title>
            <Title level={4}>4.1 您承诺遵守以下规定：</Title>
            <ul>
              <li>遵守中华人民共和国相关法律法规</li>
              <li>不得利用本系统从事违法犯罪活动</li>
              <li>不得上传、发布违法、违规、侵权或不良信息</li>
              <li>不得干扰或破坏本系统的正常运行</li>
              <li>不得侵犯他人的合法权益</li>
              <li>不得进行任何可能对本系统造成不合理负荷的行为</li>
              <li>不得使用任何自动化程序、软件、引擎、网络爬虫、网页分析工具等访问本系统</li>
            </ul>

            <Title level={4}>4.2 违规处理</Title>
            <Paragraph>
              如您违反本协议的约定，我们有权采取以下措施：
            </Paragraph>
            <ul>
              <li>警告</li>
              <li>限制或禁止使用部分或全部功能</li>
              <li>暂停或终止您的账号</li>
              <li>删除违规内容</li>
              <li>追究法律责任</li>
            </ul>

            <Title level={3}>五、知识产权</Title>
            <Title level={4}>5.1 系统知识产权</Title>
            <Paragraph>
              本系统的所有内容，包括但不限于文字、图片、图形、音频、视频、软件、程序、版面设计等，
              其知识产权均归我们或相关权利人所有。未经我们书面许可，您不得擅自使用。
            </Paragraph>

            <Title level={4}>5.2 用户内容</Title>
            <Paragraph>
              您在本系统上传、发布的内容（包括但不限于WPS、PQR、pPQR等文档），其知识产权归您或相关权利人所有。
            </Paragraph>
            <Paragraph>
              您授予我们在全球范围内、免费的、非独家的许可使用权利（包括但不限于复制、发行、出租、展览、表演、
              放映、广播、信息网络传播、摄制、改编、翻译、汇编等），以便我们为您提供服务。
            </Paragraph>

            <Title level={3}>六、隐私保护</Title>
            <Paragraph>
              我们非常重视您的隐私保护。关于我们如何收集、使用、存储和保护您的个人信息，
              请详细阅读我们的《隐私政策》。
            </Paragraph>

            <Title level={3}>七、免责声明</Title>
            <Title level={4}>7.1 服务中断或故障</Title>
            <Paragraph>
              因以下情况导致的服务中断或故障，我们不承担责任：
            </Paragraph>
            <ul>
              <li>系统维护、升级</li>
              <li>不可抗力（如自然灾害、战争、罢工等）</li>
              <li>您的设备或网络问题</li>
              <li>第三方原因（如电信运营商、云服务提供商等）</li>
              <li>黑客攻击、病毒侵入等</li>
            </ul>

            <Title level={4}>7.2 用户内容</Title>
            <Paragraph>
              您应对您上传、发布的内容负责。因您的内容导致的任何纠纷或损失，由您自行承担责任。
            </Paragraph>

            <Title level={4}>7.3 第三方链接</Title>
            <Paragraph>
              本系统可能包含第三方网站或服务的链接。我们对第三方网站或服务的内容、隐私政策等不承担责任。
            </Paragraph>

            <Title level={3}>八、付费服务</Title>
            <Title level={4}>8.1 会员服务</Title>
            <Paragraph>
              本系统提供免费版和付费会员服务。付费会员服务的具体内容、价格、续费规则等，
              请参见《价格与自动续费说明》。
            </Paragraph>

            <Title level={4}>8.2 退款政策</Title>
            <Paragraph>
              关于退款的具体规定，请参见《退款政策》。
            </Paragraph>

            <Title level={3}>九、协议的变更</Title>
            <Paragraph>
              我们有权根据需要修改本协议。修改后的协议将在本页面发布，并在页面顶部标注最后更新日期。
            </Paragraph>
            <Paragraph>
              如果您不同意修改后的协议，您有权停止使用本系统服务。
              如果您继续使用本系统服务，即视为您接受修改后的协议。
            </Paragraph>

            <Title level={3}>十、协议的终止</Title>
            <Title level={4}>10.1 您可以通过以下方式终止本协议：</Title>
            <ul>
              <li>停止使用本系统服务</li>
              <li>注销您的账号</li>
            </ul>

            <Title level={4}>10.2 我们可以在以下情况下终止本协议：</Title>
            <ul>
              <li>您违反本协议的约定</li>
              <li>您长期未使用本系统服务</li>
              <li>因法律法规或监管要求</li>
              <li>因业务调整需要停止服务</li>
            </ul>

            <Title level={3}>十一、法律适用与争议解决</Title>
            <Title level={4}>11.1 法律适用</Title>
            <Paragraph>
              本协议的订立、执行、解释及争议解决均适用中华人民共和国法律。
            </Paragraph>

            <Title level={4}>11.2 争议解决</Title>
            <Paragraph>
              因本协议产生的任何争议，双方应友好协商解决。
              协商不成的，任何一方均可向我们所在地有管辖权的人民法院提起诉讼。
            </Paragraph>

            <Title level={3}>十二、其他</Title>
            <Title level={4}>12.1 可分割性</Title>
            <Paragraph>
              如本协议的任何条款被认定为无效或不可执行，该条款应被视为可分割，
              且不影响本协议其余条款的有效性和可执行性。
            </Paragraph>

            <Title level={4}>12.2 完整协议</Title>
            <Paragraph>
              本协议构成您与我们之间关于使用本系统服务的完整协议，
              取代双方之前就同一事项达成的任何口头或书面协议。
            </Paragraph>

            <Title level={3}>十三、联系我们</Title>
            <Paragraph>
              如果您对本协议有任何疑问，请通过以下方式联系我们：
            </Paragraph>
            <ul>
              <li><Text strong>邮箱：</Text>support@weldingsystem.com</li>
              <li><Text strong>电话：</Text>400-XXX-XXXX</li>
              <li><Text strong>地址：</Text>中国（请根据实际情况填写）</li>
            </ul>

            <Divider />

            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <Text type="secondary">
                本协议的解释权归焊序所有
              </Text>
            </div>
          </Typography>
        </Space>
      </Card>
    </div>
  )
}

export default TermsOfService

