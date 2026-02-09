import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Col, Row, Typography, Space, Divider } from 'antd'
import {
  SafetyOutlined,
  TeamOutlined,
  FileTextOutlined,
  ToolOutlined,
  LoginOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'

const { Title, Paragraph, Text } = Typography

const Welcome: React.FC = () => {
  const navigate = useNavigate()

  const features = [
    {
      icon: <FileTextOutlined style={{ fontSize: 24, color: 'white' }} />,
      title: 'WPS/PQR管理',
      description: '全面的焊接工艺规程和工艺评定记录管理系统',
    },
    {
      icon: <ToolOutlined style={{ fontSize: 24, color: 'white' }} />,
      title: '模块化模板',
      description: '灵活的模板设计，支持自定义模块和预设模板',
    },
    {
      icon: <TeamOutlined style={{ fontSize: 24, color: 'white' }} />,
      title: '企业协作',
      description: '支持多用户协作，工厂管理，员工权限控制',
    },
    {
      icon: <SafetyOutlined style={{ fontSize: 24, color: 'white' }} />,
      title: '数据安全',
      description: '完善的权限管理和数据隔离，确保数据安全',
    },
  ]

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '0'
    }}>
      {/* 导航栏 */}
      <PublicNavbar />

      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        paddingTop: '80px',
        paddingBottom: '64px'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Row gutter={48} align="middle">
            <Col xs={24} md={12}>
              <div style={{ marginBottom: 24 }}>
                <Title level={1} style={{
                  fontSize: '3rem',
                  fontWeight: 700,
                  color: '#1a202c',
                  marginBottom: 24,
                  lineHeight: 1.2
                }}>
                  <span style={{ color: '#1F5EFF' }}>好焊网</span><br />
                  专业的焊接工艺管理平台
                </Title>
                <Paragraph style={{
                  fontSize: '1.25rem',
                  color: '#4A5568',
                  marginBottom: 32,
                  lineHeight: 1.6
                }}>
                  为焊接工程师和企业提供全面的WPS/PQR/pPQR管理解决方案，
                  支持焊接工艺规程管理、审批流程和统计分析
                </Paragraph>
                <Space size="large" style={{ marginBottom: 32 }}>
                  <Button
                    type="primary"
                    size="large"
                    icon={<UserAddOutlined />}
                    onClick={() => navigate('/register')}
                    style={{
                      height: 44,
                      fontSize: 16,
                      padding: '0 24px',
                      background: '#1F5EFF',
                      borderColor: '#1F5EFF',
                      borderRadius: 8,
                      fontWeight: 500
                    }}
                  >
                    免费开始
                  </Button>
                  <Button
                    size="large"
                    icon={<LoginOutlined />}
                    onClick={() => navigate('/login')}
                    style={{
                      height: 44,
                      fontSize: 16,
                      padding: '0 24px',
                      borderColor: '#1F5EFF',
                      color: '#1F5EFF',
                      borderRadius: 8,
                      fontWeight: 500
                    }}
                  >
                    登录
                  </Button>
                </Space>
                <div style={{ display: 'flex', gap: 24, fontSize: 14, color: '#4A5568' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#38A169' }} />
                    <span>永久免费基础版</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#38A169' }} />
                    <span>企业级安全保障</span>
                  </div>
                </div>
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div style={{
                background: 'white',
                borderRadius: 16,
                padding: 24,
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
              }}>
                <div style={{
                  height: 300,
                  background: 'linear-gradient(135deg, #1F5EFF 0%, #1a4fe6 100%)',
                  borderRadius: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: 18
                }}>
                  仪表板预览
                </div>
              </div>
            </Col>
          </Row>
        </div>
      </div>

      {/* Workflow Section */}
      <div style={{ background: '#F7FAFC', padding: '64px 0' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={2} style={{ fontSize: '2rem', fontWeight: 700, color: '#1a202c', marginBottom: 16 }}>
              简单三步，高效管理
            </Title>
            <Paragraph style={{ fontSize: '1.25rem', color: '#4A5568' }}>
              从创建到审批，再到导出使用，全流程智能化管理
            </Paragraph>
          </div>

          <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
            <Col xs={24} md={8}>
              <Card
                hoverable
                style={{
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  textAlign: 'center',
                  padding: 16,
                  transition: 'all 0.3s ease'
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#1F5EFF',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  fontWeight: 'bold',
                  margin: '0 auto 16px'
                }}>
                  1
                </div>
                <Title level={4} style={{ marginBottom: 12 }}>创建文档</Title>
                <Text style={{ color: '#4A5568' }}>
                  使用模块化模板快速创建WPS/PQR文档，支持自定义参数和技术要求
                </Text>
              </Card>
            </Col>

            <Col xs={24} md={8}>
              <Card
                hoverable
                style={{
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  textAlign: 'center',
                  padding: 16,
                  transition: 'all 0.3s ease'
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#1F5EFF',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  fontWeight: 'bold',
                  margin: '0 auto 16px'
                }}>
                  2
                </div>
                <Title level={4} style={{ marginBottom: 12 }}>审批流程</Title>
                <Text style={{ color: '#4A5568' }}>
                  智能化审批工作流，支持多级审批，实时跟踪审批状态
                </Text>
              </Card>
            </Col>

            <Col xs={24} md={8}>
              <Card
                hoverable
                style={{
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  textAlign: 'center',
                  padding: 16,
                  transition: 'all 0.3s ease'
                }}
              >
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#1F5EFF',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  fontWeight: 'bold',
                  margin: '0 auto 16px'
                }}>
                  3
                </div>
                <Title level={4} style={{ marginBottom: 12 }}>导出使用</Title>
                <Text style={{ color: '#4A5568' }}>
                  一键导出PDF格式，支持分享给团队成员，移动端查看
                </Text>
              </Card>
            </Col>
          </Row>
        </div>
      </div>

      {/* Features Section */}
      <div style={{ background: 'white', padding: '64px 0' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <Title level={2} style={{ fontSize: '2rem', fontWeight: 700, color: '#1a202c', marginBottom: 16 }}>
              核心功能优势
            </Title>
            <Paragraph style={{ fontSize: '1.25rem', color: '#4A5568' }}>
              专业的功能设计，满足焊接工艺管理的全方位需求
            </Paragraph>
          </div>

          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} sm={12} md={6} key={index}>
                <Card
                  hoverable
                  style={{
                    borderRadius: 12,
                    border: '1px solid #e2e8f0',
                    textAlign: 'center',
                    padding: 8,
                    height: '100%'
                  }}
                >
                  <div style={{
                    width: 48,
                    height: 48,
                    background: '#1F5EFF',
                    borderRadius: 12,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px'
                  }}>
                    {feature.icon}
                  </div>
                  <Title level={4} style={{ fontSize: '1.125rem', marginBottom: 12 }}>
                    {feature.title}
                  </Title>
                  <Text style={{ color: '#4A5568', fontSize: 14 }}>
                    {feature.description}
                  </Text>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ background: '#1F5EFF', padding: '64px 0' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', padding: '0 24px', textAlign: 'center' }}>
          <Title level={2} style={{ fontSize: '2rem', fontWeight: 700, color: 'white', marginBottom: 16 }}>
            准备好提升焊接工艺管理效率了吗？
          </Title>
          <Paragraph style={{ fontSize: '1.25rem', color: 'rgba(255,255,255,0.9)', marginBottom: 32 }}>
            立即加入好焊网，体验专业的焊接工艺管理平台
          </Paragraph>
          <Space size="large">
            <Button
              size="large"
              icon={<UserAddOutlined />}
              onClick={() => navigate('/register')}
              style={{
                height: 44,
                fontSize: 16,
                padding: '0 32px',
                background: 'white',
                color: '#1F5EFF',
                border: 'none',
                borderRadius: 8,
                fontWeight: 600
              }}
            >
              免费注册体验
            </Button>
            <Button
              size="large"
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
              style={{
                height: 44,
                fontSize: 16,
                padding: '0 32px',
                background: 'transparent',
                borderColor: 'white',
                color: 'white',
                borderRadius: 8,
                fontWeight: 600,
                borderWidth: 2
              }}
            >
              立即登录
            </Button>
          </Space>
        </div>
      </div>

      {/* Footer */}
      <div style={{ background: '#1A1D23', padding: '48px 0' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
          <Row gutter={[32, 32]} style={{ marginBottom: 32 }}>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4} style={{ color: 'white', marginBottom: 16 }}>好焊网</Title>
                <Text style={{ color: '#9CA3AF', fontSize: 14 }}>
                  专业的焊接工艺管理平台，为焊接工程师和企业提供全面的WPS/PQR管理解决方案。
                </Text>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4} style={{ color: 'white', marginBottom: 16 }}>产品功能</Title>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <a href="/features" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>产品功能</a>
                  <a href="/analytics" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>统计分析</a>
                  <a href="#" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>模块化模板</a>
                  <a href="#" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>企业协作</a>
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4} style={{ color: 'white', marginBottom: 16 }}>支持服务</Title>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <a href="/about" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>关于我们</a>
                  <a href="#" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>使用文档</a>
                  <a href="#" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>视频教程</a>
                  <a href="#" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>技术支持</a>
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4} style={{ color: 'white', marginBottom: 16 }}>法律信息</Title>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <a href="/terms-of-service" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>用户协议</a>
                  <a href="/privacy-policy" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>隐私政策</a>
                  <a href="/refund-policy" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>退款政策</a>
                  <a href="/pricing-info" style={{ color: '#9CA3AF', fontSize: 14, textDecoration: 'none' }}>价格说明</a>
                </div>
              </div>
            </Col>
          </Row>

          <div style={{ borderTop: '1px solid #374151', paddingTop: 32, textAlign: 'center' }}>
            <Text style={{ color: '#9CA3AF', fontSize: 14 }}>
              © 2024 好焊网. 保留所有权利. {' '}
              <a
                href="https://beian.miit.gov.cn/"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#9CA3AF', textDecoration: 'none' }}
              >
                鲁ICP备2025191429号-1
              </a>
            </Text>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Welcome

