import React from 'react'
import { Layout, Space, Typography, Divider } from 'antd'
import { Link } from 'react-router-dom'
import {
  SafetyCertificateOutlined,
  FileTextOutlined,
  DollarOutlined,
  CrownOutlined,
} from '@ant-design/icons'

const { Footer: AntFooter } = Layout
const { Text } = Typography

interface FooterProps {
  style?: React.CSSProperties
  className?: string
}

const Footer: React.FC<FooterProps> = ({ style, className }) => {
  const currentYear = new Date().getFullYear()

  return (
    <AntFooter
      style={{
        textAlign: 'center',
        background: '#001529',
        color: 'rgba(255, 255, 255, 0.65)',
        padding: '24px 50px',
        ...style,
      }}
      className={className}
    >
      <Space
        direction="vertical"
        size="middle"
        style={{ width: '100%' }}
      >
        {/* 法律政策链接 */}
        <Space
          split={<Divider type="vertical" style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }} />}
          wrap
          style={{ justifyContent: 'center' }}
        >
          <Link
            to="/privacy-policy"
            style={{
              color: 'rgba(255, 255, 255, 0.65)',
              transition: 'color 0.3s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#1890ff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.65)')}
          >
            <SafetyCertificateOutlined /> 隐私政策
          </Link>
          <Link
            to="/terms-of-service"
            style={{
              color: 'rgba(255, 255, 255, 0.65)',
              transition: 'color 0.3s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#1890ff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.65)')}
          >
            <FileTextOutlined /> 用户协议
          </Link>
          <Link
            to="/refund-policy"
            style={{
              color: 'rgba(255, 255, 255, 0.65)',
              transition: 'color 0.3s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#1890ff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.65)')}
          >
            <DollarOutlined /> 退款政策
          </Link>
          <Link
            to="/pricing-terms"
            style={{
              color: 'rgba(255, 255, 255, 0.65)',
              transition: 'color 0.3s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#1890ff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.65)')}
          >
            <CrownOutlined /> 价格说明
          </Link>
        </Space>

        {/* 版权信息 */}
        <Text style={{ color: 'rgba(255, 255, 255, 0.45)', fontSize: '12px' }}>
          Copyright © {currentYear} 焊接工艺管理系统. All Rights Reserved.
        </Text>

        {/* 备案信息 */}
        <a
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: 'rgba(255, 255, 255, 0.45)',
            fontSize: '12px',
            textDecoration: 'none',
            transition: 'color 0.3s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.85)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.45)')}
        >
          鲁ICP备2025191429号-1
        </a>
      </Space>
    </AntFooter>
  )
}

export default Footer

