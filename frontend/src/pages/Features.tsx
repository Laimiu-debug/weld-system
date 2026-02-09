import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileTextOutlined,
  ToolOutlined,
  TeamOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  BarChartOutlined,
  CloudOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'

const Features: React.FC = () => {
  const [activeTab, setActiveTab] = useState('wps')

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const coreFeatures = [
    {
      icon: <FileTextOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: 'WPS/PQR管理',
      description: '完整的焊接工艺规程和工艺评定记录管理系统',
      details: [
        '模板化文档创建',
        '版本控制和历史追踪',
        '智能审批流程',
        '一键导出PDF/Word',
      ],
    },
    {
      icon: <ToolOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: '模块化模板',
      description: '灵活的模块化模板系统，适应不同焊接工艺标准',
      details: [
        '自定义模板创建',
        '模块拖拽组合',
        '企业模板共享',
        '标准模板库',
      ],
    },
    {
      icon: <TeamOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: '企业协作',
      description: '多人协作、权限管理、审批流程一体化',
      details: [
        '角色权限管理',
        '多级审批流程',
        '实时协作编辑',
        '消息通知提醒',
      ],
    },
    {
      icon: <SafetyOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: '数据安全',
      description: '企业级数据安全保障，符合行业标准',
      details: [
        '数据加密存储',
        '定期自动备份',
        '操作日志审计',
        '权限细粒度控制',
      ],
    },
    {
      icon: <BarChartOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: '统计分析',
      description: '全面的数据统计和可视化分析功能',
      details: [
        '实时数据监控',
        '多维度统计报表',
        '趋势分析预测',
        '自定义报表导出',
      ],
    },
    {
      icon: <CloudOutlined style={{ fontSize: 32, color: '#1F5EFF' }} />,
      title: '云端存储',
      description: '安全可靠的云端存储，随时随地访问',
      details: [
        '无限云端存储',
        '多设备同步',
        '离线访问支持',
        '快速搜索检索',
      ],
    },
  ]

  const tabItems = [
    {
      key: 'wps',
      label: 'WPS管理',
      content: (
        <div style={{ padding: 32, background: '#F7FAFC', borderRadius: 12 }}>
          <h4 style={{ fontSize: 24, fontWeight: 600, color: '#1A202C', marginBottom: 16, margin: '0 0 16px 0' }}>焊接工艺规程管理</h4>
          <p style={{ fontSize: 16, color: '#4A5568', marginBottom: 24, lineHeight: 1.6, margin: '0 0 24px 0' }}>
            提供完整的WPS生命周期管理，从创建、审批到归档的全流程数字化解决方案。
          </p>
          <ul style={{ fontSize: 16, lineHeight: 2, listStyle: 'none', padding: 0, margin: 0 }}>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>基于模板快速创建WPS文档</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>智能表单验证，确保数据完整性</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>多级审批流程，符合企业管理规范</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>版本控制，追踪每次修改记录</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>一键导出为PDF或Word格式</span>
            </li>
          </ul>
        </div>
      ),
    },
    {
      key: 'pqr',
      label: 'PQR管理',
      content: (
        <div style={{ padding: 32, background: '#F7FAFC', borderRadius: 12 }}>
          <h4 style={{ fontSize: 24, fontWeight: 600, color: '#1A202C', marginBottom: 16, margin: '0 0 16px 0' }}>工艺评定记录管理</h4>
          <p style={{ fontSize: 16, color: '#4A5568', marginBottom: 24, lineHeight: 1.6, margin: '0 0 24px 0' }}>
            完整的PQR管理系统，支持工艺评定的全过程记录和管理。
          </p>
          <ul style={{ fontSize: 16, lineHeight: 2, listStyle: 'none', padding: 0, margin: 0 }}>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>详细的试验数据记录</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>测试结果可视化展示</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>附件管理（照片、报告等）</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>风险评估和合规性检查</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>与WPS关联管理</span>
            </li>
          </ul>
        </div>
      ),
    },
    {
      key: 'collaboration',
      label: '团队协作',
      content: (
        <div style={{ padding: 32, background: '#F7FAFC', borderRadius: 12 }}>
          <h4 style={{ fontSize: 24, fontWeight: 600, color: '#1A202C', marginBottom: 16, margin: '0 0 16px 0' }}>企业级协作功能</h4>
          <p style={{ fontSize: 16, color: '#4A5568', marginBottom: 24, lineHeight: 1.6, margin: '0 0 24px 0' }}>
            支持多人协作、权限管理、审批流程的一体化协作平台。
          </p>
          <ul style={{ fontSize: 16, lineHeight: 2, listStyle: 'none', padding: 0, margin: 0 }}>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>灵活的角色权限配置</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>自定义审批流程</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>实时消息通知</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>操作日志审计</span>
            </li>
            <li style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
              <CheckCircleOutlined style={{ color: '#38A169', fontSize: 18 }} />
              <span>企业资源共享</span>
            </li>
          </ul>
        </div>
      ),
    },
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(to bottom, #f8fafc, #e2e8f0)' }}>
      {/* 导航栏 */}
      <PublicNavbar />

      {/* Hero Section */}
      <div style={{ background: 'linear-gradient(135deg, #1F5EFF 0%, #1850E0 100%)', padding: '100px 24px 80px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: 56, fontWeight: 700, color: '#fff', marginBottom: 24, lineHeight: 1.2, margin: '0 0 24px 0' }}>
            强大的功能，助力焊接管理
          </h1>
          <p style={{ fontSize: 20, color: 'rgba(255, 255, 255, 0.9)', marginBottom: 40, maxWidth: 800, margin: '0 auto 40px' }}>
            从文档创建到审批流程，从数据统计到团队协作，我们提供全方位的焊接工艺管理解决方案
          </p>
          <div style={{ display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fff', fontSize: 16 }}>
              <CheckCircleOutlined style={{ fontSize: 20, color: '#38A169' }} />
              <span>永久免费基础版</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fff', fontSize: 16 }}>
              <RocketOutlined style={{ fontSize: 20, color: '#FFC857' }} />
              <span>快速上手</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fff', fontSize: 16 }}>
              <ThunderboltOutlined style={{ fontSize: 20, color: '#38A169' }} />
              <span>高效协作</span>
            </div>
          </div>
        </div>
      </div>

      {/* Core Features */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: 60 }}>
          <h2 style={{ fontSize: 36, fontWeight: 700, color: '#1A202C', marginBottom: 16, margin: '0 0 16px 0' }}>核心功能</h2>
          <p style={{ fontSize: 18, color: '#4A5568', maxWidth: 600, margin: '0 auto' }}>
            专为焊接行业打造的全流程管理系统
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: 32,
            marginBottom: 40,
          }}
        >
          {coreFeatures.map((feature, index) => (
            <div
              key={index}
              style={{
                background: '#fff',
                padding: 32,
                borderRadius: 12,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                border: '1px solid #E2E8F0',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)'
                e.currentTarget.style.boxShadow = '0 12px 24px rgba(31, 94, 255, 0.15)'
                e.currentTarget.style.borderColor = '#1F5EFF'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)'
                e.currentTarget.style.borderColor = '#E2E8F0'
              }}
            >
              <div style={{ marginBottom: 20 }}>{feature.icon}</div>
              <h3 style={{ fontSize: 20, fontWeight: 600, color: '#1A202C', marginBottom: 12, margin: '0 0 12px 0' }}>{feature.title}</h3>
              <p style={{ fontSize: 14, color: '#718096', marginBottom: 20, lineHeight: 1.6, margin: '0 0 20px 0' }}>{feature.description}</p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {feature.details.map((detail, idx) => (
                  <li
                    key={idx}
                    style={{
                      fontSize: 14,
                      color: '#4A5568',
                      marginBottom: 8,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <CheckCircleOutlined style={{ color: '#38A169', fontSize: 16, flexShrink: 0 }} />
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Tabs */}
      <div style={{ background: 'white', padding: '80px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, textAlign: 'center', marginBottom: 48, color: '#1A202C', margin: '0 0 48px 0' }}>
            功能详解
          </h2>

          {/* Tab Navigation */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 40, borderBottom: '2px solid #E2E8F0' }}>
            {tabItems.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: '12px 32px',
                  fontSize: 16,
                  fontWeight: 500,
                  color: activeTab === tab.key ? '#1F5EFF' : '#4A5568',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: activeTab === tab.key ? '2px solid #1F5EFF' : '2px solid transparent',
                  marginBottom: -2,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== tab.key) {
                    e.currentTarget.style.color = '#1F5EFF'
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== tab.key) {
                    e.currentTarget.style.color = '#4A5568'
                  }
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div>
            {tabItems.find((tab) => tab.key === activeTab)?.content}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ background: 'linear-gradient(135deg, #1F5EFF 0%, #1850E0 100%)', padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ fontSize: 36, fontWeight: 700, color: '#fff', marginBottom: 24, margin: '0 0 24px 0' }}>
            准备好开始了吗？
          </h2>
          <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)', marginBottom: 32, margin: '0 0 32px 0' }}>
            立即注册，体验专业的焊接工艺管理系统
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/register">
              <button
                style={{
                  background: 'white',
                  color: '#1F5EFF',
                  borderRadius: 8,
                  height: 48,
                  padding: '0 32px',
                  fontWeight: 500,
                  border: 'none',
                  fontSize: 16,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                免费注册
              </button>
            </Link>
            <Link to="/login">
              <button
                style={{
                  background: 'transparent',
                  color: 'white',
                  borderRadius: 8,
                  height: 48,
                  padding: '0 32px',
                  fontWeight: 500,
                  border: '2px solid white',
                  fontSize: 16,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                立即登录
              </button>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ background: '#1A1D23', color: 'white', padding: '60px 24px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 40, marginBottom: 40 }}>
            <div>
              <h4 style={{ fontSize: 18, fontWeight: 600, color: 'white', marginBottom: 16, margin: '0 0 16px 0' }}>
                好汉焊接
              </h4>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 14, lineHeight: 1.6, margin: 0 }}>
                专业的焊接工艺管理平台，为焊接行业提供全方位的数字化解决方案
              </p>
            </div>
            <div>
              <h5 style={{ fontSize: 16, fontWeight: 600, color: 'white', marginBottom: 16, margin: '0 0 16px 0' }}>
                产品
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <Link to="/features" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, transition: 'color 0.3s' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#1F5EFF'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                >
                  产品功能
                </Link>
                <Link to="/analytics" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, transition: 'color 0.3s' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#1F5EFF'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                >
                  统计分析
                </Link>
              </div>
            </div>
            <div>
              <h5 style={{ fontSize: 16, fontWeight: 600, color: 'white', marginBottom: 16, margin: '0 0 16px 0' }}>
                支持
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <Link to="/about" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, transition: 'color 0.3s' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#1F5EFF'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                >
                  关于我们
                </Link>
              </div>
            </div>
            <div>
              <h5 style={{ fontSize: 16, fontWeight: 600, color: 'white', marginBottom: 16, margin: '0 0 16px 0' }}>
                法律
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <Link to="/privacy-policy" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, transition: 'color 0.3s' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#1F5EFF'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                >
                  隐私政策
                </Link>
                <Link to="/terms-of-service" style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, transition: 'color 0.3s' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#1F5EFF'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.7)'}
                >
                  服务条款
                </Link>
              </div>
            </div>
          </div>
          <div
            style={{
              borderTop: '1px solid rgba(255,255,255,0.1)',
              marginTop: 40,
              paddingTop: 24,
              textAlign: 'center',
              color: 'rgba(255,255,255,0.5)',
              fontSize: 14,
            }}
          >
            <span style={{ color: 'rgba(255,255,255,0.5)' }}>
              © 2025 好焊网. All rights reserved. | 鲁ICP备2025191429号-1
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Features
