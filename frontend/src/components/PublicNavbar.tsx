import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { MenuOutlined, CloseOutlined } from '@ant-design/icons'

const PublicNavbar: React.FC = () => {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isActive = (path: string) => location.pathname === path

  const navLinks = [
    { path: '/', label: '首页' },
    { path: '/features', label: '产品功能' },
    { path: '/analytics', label: '统计分析' },
    { path: '/about', label: '关于我们' },
  ]

  return (
    <nav
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #E2E8F0',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: 64,
        }}
      >
        {/* Logo */}
        <Link
          to="/"
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: '#1F5EFF',
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span style={{ fontSize: 28 }}>⚡</span>
          焊序
        </Link>

        {/* Desktop Navigation */}
        <div
          style={{
            display: 'flex',
            gap: 32,
            alignItems: 'center',
          }}
          className="desktop-nav"
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              style={{
                fontSize: 16,
                fontWeight: 500,
                color: isActive(link.path) ? '#1F5EFF' : '#4A5568',
                textDecoration: 'none',
                padding: '8px 0',
                borderBottom: isActive(link.path) ? '2px solid #1F5EFF' : '2px solid transparent',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => {
                if (!isActive(link.path)) {
                  e.currentTarget.style.color = '#1F5EFF'
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive(link.path)) {
                  e.currentTarget.style.color = '#4A5568'
                }
              }}
            >
              {link.label}
            </Link>
          ))}

          {/* CTA Buttons */}
          <div style={{ display: 'flex', gap: 12, marginLeft: 16 }}>
            <Link to="/login">
              <button
                style={{
                  padding: '8px 20px',
                  fontSize: 14,
                  fontWeight: 500,
                  color: '#1F5EFF',
                  background: 'transparent',
                  border: '1px solid #1F5EFF',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#F0F5FF'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                登录
              </button>
            </Link>
            <Link to="/register">
              <button
                style={{
                  padding: '8px 20px',
                  fontSize: 14,
                  fontWeight: 500,
                  color: '#fff',
                  background: '#1F5EFF',
                  border: 'none',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#1850E0'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#1F5EFF'
                }}
              >
                免费注册
              </button>
            </Link>
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{
            display: 'none',
            background: 'transparent',
            border: 'none',
            fontSize: 24,
            color: '#1F5EFF',
            cursor: 'pointer',
          }}
        >
          {mobileMenuOpen ? <CloseOutlined /> : <MenuOutlined />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div
          className="mobile-menu"
          style={{
            display: 'none',
            background: '#fff',
            borderTop: '1px solid #E2E8F0',
            padding: '16px 24px',
          }}
        >
          {/* Mobile menu content will be added here */}
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav {
            display: none !important;
          }
          .mobile-menu-btn {
            display: block !important;
          }
        }
      `}</style>
    </nav>
  )
}

export default PublicNavbar

