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
    <nav className="public-navbar">
      <div className="public-navbar__inner">
        <Link to="/" className="public-navbar__brand">
          焊序
        </Link>

        <div className="public-navbar__desktop">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`public-navbar__link${isActive(link.path) ? ' is-active' : ''}`}
            >
              {link.label}
            </Link>
          ))}

          <div className="public-navbar__actions">
            <Link to="/login" className="public-navbar__btn public-navbar__btn--ghost">
              登录
            </Link>
            <Link to="/register" className="public-navbar__btn public-navbar__btn--solid">
              免费注册
            </Link>
          </div>
        </div>

        <button
          type="button"
          className="public-navbar__menu-btn"
          aria-label={mobileMenuOpen ? '关闭菜单' : '打开菜单'}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          {mobileMenuOpen ? <CloseOutlined /> : <MenuOutlined />}
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="public-navbar__mobile">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`public-navbar__mobile-link${isActive(link.path) ? ' is-active' : ''}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="public-navbar__mobile-actions">
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              登录
            </Link>
            <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
              免费注册
            </Link>
          </div>
        </div>
      )}

      <style>{`
        .public-navbar {
          position: sticky;
          top: 0;
          z-index: 1000;
          background: rgba(247, 248, 250, 0.82);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(20, 24, 31, 0.06);
          font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        }

        .public-navbar__inner {
          max-width: 1120px;
          margin: 0 auto;
          padding: 0 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          height: 64px;
        }

        .public-navbar__brand {
          font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
          font-size: 1.35rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          color: #14181f;
          text-decoration: none;
        }

        .public-navbar__desktop {
          display: flex;
          gap: 28px;
          align-items: center;
        }

        .public-navbar__link {
          font-size: 14px;
          font-weight: 500;
          color: #6b7385;
          text-decoration: none;
          padding: 6px 0;
          border-bottom: 2px solid transparent;
          transition: color 160ms ease, border-color 160ms ease;
        }

        .public-navbar__link:hover,
        .public-navbar__link.is-active {
          color: #1f5eff;
        }

        .public-navbar__link.is-active {
          border-bottom-color: #1f5eff;
        }

        .public-navbar__actions {
          display: flex;
          gap: 10px;
          margin-left: 8px;
        }

        .public-navbar__btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 36px;
          padding: 0 16px;
          font-size: 13px;
          font-weight: 600;
          border-radius: 6px;
          text-decoration: none;
          transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
        }

        .public-navbar__btn--ghost {
          color: #1f5eff;
          border: 1px solid rgba(31, 94, 255, 0.45);
          background: transparent;
        }

        .public-navbar__btn--ghost:hover {
          background: rgba(31, 94, 255, 0.06);
        }

        .public-navbar__btn--solid {
          color: #fff;
          background: #1f5eff;
          border: 1px solid #1f5eff;
        }

        .public-navbar__btn--solid:hover {
          background: #1546c9;
          border-color: #1546c9;
        }

        .public-navbar__menu-btn {
          display: none;
          background: transparent;
          border: none;
          font-size: 22px;
          color: #14181f;
          cursor: pointer;
          padding: 8px;
        }

        .public-navbar__mobile {
          display: none;
          background: #fff;
          border-top: 1px solid rgba(20, 24, 31, 0.06);
          padding: 12px 24px 20px;
        }

        .public-navbar__mobile-link {
          display: block;
          padding: 12px 0;
          font-size: 15px;
          font-weight: 500;
          color: #3a4254;
          text-decoration: none;
          border-bottom: 1px solid rgba(20, 24, 31, 0.06);
        }

        .public-navbar__mobile-link.is-active {
          color: #1f5eff;
        }

        .public-navbar__mobile-actions {
          display: flex;
          gap: 12px;
          margin-top: 16px;
        }

        .public-navbar__mobile-actions a {
          flex: 1;
          text-align: center;
          padding: 12px;
          border-radius: 6px;
          font-weight: 600;
          text-decoration: none;
          font-size: 14px;
        }

        .public-navbar__mobile-actions a:first-child {
          color: #1f5eff;
          border: 1px solid rgba(31, 94, 255, 0.45);
        }

        .public-navbar__mobile-actions a:last-child {
          color: #fff;
          background: #1f5eff;
        }

        @media (max-width: 768px) {
          .public-navbar__desktop {
            display: none;
          }
          .public-navbar__menu-btn {
            display: block;
          }
          .public-navbar__mobile {
            display: block;
          }
        }
      `}</style>
    </nav>
  )
}

export default PublicNavbar
