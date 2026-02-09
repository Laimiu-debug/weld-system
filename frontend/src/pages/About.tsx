import React, { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Row, Col, Card } from 'antd'
import {
  RocketOutlined,
  EyeOutlined,
  HeartOutlined,
  MailOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'

const About: React.FC = () => {
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const values = [
    {
      icon: <RocketOutlined style={{ fontSize: 48, color: '#1F5EFF' }} />,
      title: '创新驱动',
      description: '持续创新，为焊接行业提供最先进的数字化解决方案',
    },
    {
      icon: <EyeOutlined style={{ fontSize: 48, color: '#38A169' }} />,
      title: '专业专注',
      description: '深耕焊接工艺管理领域，提供专业可靠的服务',
    },
    {
      icon: <HeartOutlined style={{ fontSize: 48, color: '#FFC857' }} />,
      title: '客户至上',
      description: '以客户需求为中心，提供优质的产品和服务体验',
    },
  ]

  const contactInfo = [
    {
      icon: <MailOutlined style={{ fontSize: 24, color: '#1F5EFF' }} />,
      label: '邮箱',
      value: 'contact@sdhaohan.cn',
    },
    {
      icon: <PhoneOutlined style={{ fontSize: 24, color: '#1F5EFF' }} />,
      label: '电话',
      value: '400-XXX-XXXX',
    },
    {
      icon: <EnvironmentOutlined style={{ fontSize: 24, color: '#1F5EFF' }} />,
      label: '地址',
      value: '山东省',
    },
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}>
      {/* 导航栏 */}
      <PublicNavbar />

      {/* Hero Section */}
      <div style={{ padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h1 style={{ fontSize: 48, marginBottom: 24, fontWeight: 700, color: '#1A202C', margin: '0 0 24px 0' }}>
            关于好焊网
          </h1>
          <p style={{ fontSize: 20, color: '#4A5568', marginBottom: 40, lineHeight: 1.6, margin: '0 0 40px 0' }}>
            专注于为焊接行业提供专业的数字化管理解决方案
          </p>
        </div>
      </div>

      {/* Mission & Vision */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px 80px' }}>
        <Row gutter={[48, 48]}>
          <Col xs={24} md={12}>
            <Card style={{ height: '100%', borderRadius: 16, border: '1px solid #e5e7eb' }}>
              <h3 style={{ color: '#1F5EFF', marginBottom: 24, fontSize: 24, fontWeight: 600, margin: '0 0 24px 0' }}>
                我们的使命
              </h3>
              <p style={{ fontSize: 18, color: '#4A5568', lineHeight: 1.8, margin: 0 }}>
                通过数字化技术，提升焊接工艺管理效率，降低企业运营成本，推动焊接行业的数字化转型。
              </p>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card style={{ height: '100%', borderRadius: 16, border: '1px solid #e5e7eb' }}>
              <h3 style={{ color: '#1F5EFF', marginBottom: 24, fontSize: 24, fontWeight: 600, margin: '0 0 24px 0' }}>
                我们的愿景
              </h3>
              <p style={{ fontSize: 18, color: '#4A5568', lineHeight: 1.8, margin: 0 }}>
                成为焊接工艺管理领域最值得信赖的数字化平台，为全球焊接企业提供优质服务。
              </p>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Core Values */}
      <div style={{ background: 'white', padding: '80px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', marginBottom: 48, fontSize: 36, fontWeight: 700, color: '#1A202C', margin: '0 0 48px 0' }}>
            核心价值观
          </h2>
          <Row gutter={[32, 32]}>
            {values.map((value, index) => (
              <Col xs={24} md={8} key={index}>
                <div style={{ textAlign: 'center', padding: 24 }}>
                  <div style={{ marginBottom: 24 }}>{value.icon}</div>
                  <h4 style={{ marginBottom: 16, fontSize: 20, fontWeight: 600, color: '#1A202C', margin: '0 0 16px 0' }}>
                    {value.title}
                  </h4>
                  <p style={{ color: '#4A5568', fontSize: 16, lineHeight: 1.6, margin: 0 }}>
                    {value.description}
                  </p>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* Contact Section */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 24px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: 48, fontSize: 36, fontWeight: 700, color: '#1A202C', margin: '0 0 48px 0' }}>
          联系我们
        </h2>
        <Row gutter={[32, 32]} justify="center">
          {contactInfo.map((info, index) => (
            <Col xs={24} md={8} key={index}>
              <Card
                style={{
                  textAlign: 'center',
                  borderRadius: 16,
                  border: '1px solid #e5e7eb',
                }}
              >
                <div style={{ marginBottom: 16 }}>{info.icon}</div>
                <h5 style={{ marginBottom: 8, color: '#4A5568', fontSize: 16, fontWeight: 600, margin: '0 0 8px 0' }}>
                  {info.label}
                </h5>
                <span style={{ fontSize: 16, color: '#1F5EFF' }}>{info.value}</span>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* CTA Section */}
      <div style={{ background: '#1F5EFF', padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ color: 'white', marginBottom: 24, fontSize: 36, fontWeight: 700, margin: '0 0 24px 0' }}>
            加入我们，开启数字化之旅
          </h2>
          <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)', marginBottom: 32, lineHeight: 1.6, margin: '0 0 32px 0' }}>
            立即注册，体验专业的焊接工艺管理系统
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
            <Link
              to="/register"
              style={{
                display: 'inline-block',
                background: 'white',
                color: '#1F5EFF',
                borderRadius: 8,
                height: 48,
                padding: '0 32px',
                fontWeight: 500,
                border: 'none',
                textDecoration: 'none',
                lineHeight: '48px',
                cursor: 'pointer',
              }}
            >
              免费注册
            </Link>
            <Link
              to="/login"
              style={{
                display: 'inline-block',
                background: 'transparent',
                color: 'white',
                borderRadius: 8,
                height: 48,
                padding: '0 32px',
                fontWeight: 500,
                border: '2px solid white',
                textDecoration: 'none',
                lineHeight: '44px',
                cursor: 'pointer',
              }}
            >
              立即登录
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ background: '#1A1D23', color: 'white', padding: '48px 24px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Row gutter={[32, 32]}>
            <Col xs={24} md={6}>
              <h4 style={{ color: 'white', marginBottom: 16, fontSize: 18, fontWeight: 600, margin: '0 0 16px 0' }}>
                好焊网
              </h4>
              <p style={{ color: 'rgba(255,255,255,0.7)', margin: 0 }}>
                专业的焊接工艺管理平台
              </p>
            </Col>
            <Col xs={24} md={6}>
              <h5 style={{ color: 'white', marginBottom: 16, fontSize: 16, fontWeight: 600, margin: '0 0 16px 0' }}>
                产品
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Link to="/features" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
                  产品功能
                </Link>
                <Link to="/analytics" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
                  统计分析
                </Link>
              </div>
            </Col>
            <Col xs={24} md={6}>
              <h5 style={{ color: 'white', marginBottom: 16, fontSize: 16, fontWeight: 600, margin: '0 0 16px 0' }}>
                支持
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Link to="/about" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
                  关于我们
                </Link>
              </div>
            </Col>
            <Col xs={24} md={6}>
              <h5 style={{ color: 'white', marginBottom: 16, fontSize: 16, fontWeight: 600, margin: '0 0 16px 0' }}>
                法律
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Link to="/privacy-policy" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
                  隐私政策
                </Link>
                <Link to="/terms-of-service" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none' }}>
                  服务条款
                </Link>
              </div>
            </Col>
          </Row>
          <div
            style={{
              borderTop: '1px solid rgba(255,255,255,0.1)',
              marginTop: 32,
              paddingTop: 24,
              textAlign: 'center',
              color: 'rgba(255,255,255,0.5)',
            }}
          >
            <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 14 }}>
              © 2025 好焊网. All rights reserved. | 鲁ICP备2025191429号-1
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default About
