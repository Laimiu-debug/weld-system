import React, { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FileTextOutlined,
  ExperimentOutlined,
  TeamOutlined,
  ToolOutlined,
  DatabaseOutlined,
  SettingOutlined,
  SafetyCertificateOutlined,
  PartitionOutlined,
  BarChartOutlined,
  CrownOutlined,
  PlusOutlined,
  SearchOutlined,
  BellOutlined,
  MenuFoldOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'
import BrandMark from '@/components/Brand/BrandMark'
import ProductIcon from '@/components/icons/ProductIcon'
import './Welcome.css'

const CAPABILITIES = [
  {
    icon: <ProductIcon kind="wps" size={22} />,
    title: 'WPS / PQR / pPQR',
    description: '工艺规程与评定记录统一建档，版本可追溯，导出 Word / PDF。',
  },
  {
    icon: <ProductIcon kind="library" size={22} />,
    title: '模板与共享库',
    description: '模块化模板、企业共享库，适配不同工艺标准与协作场景。',
  },
  {
    icon: <ProductIcon kind="enterprise" size={22} />,
    title: '企业协作审批',
    description: '多级审批工作流、角色权限与工厂级数据隔离。',
  },
  {
    icon: <ProductIcon kind="quality" size={22} />,
    title: '焊工·设备·质量',
    description: '焊工资质、设备台账与质量检验同平台联动管理。',
  },
] as const

const STEPS = [
  {
    num: '01',
    title: '创建文档',
    description: '选用模板快速生成 WPS / PQR，参数与技术要求一次填齐。',
  },
  {
    num: '02',
    title: '审批流转',
    description: '按企业流程推送审批，状态实时可见，全程留痕可查。',
  },
  {
    num: '03',
    title: '导出交付',
    description: '一键导出正式文档，同步现场与质量团队随时查阅。',
  },
] as const

const SIDE_MENUS = [
  { icon: <ProductIcon kind="dashboard" />, label: '仪表盘', active: true },
  { icon: <ProductIcon kind="library" />, label: '资源库' },
  { icon: <ProductIcon kind="wps" />, label: 'WPS管理' },
  { icon: <ProductIcon kind="pqr" />, label: 'PQR管理' },
  { icon: <ProductIcon kind="ppqr" />, label: 'pPQR管理' },
  { icon: <ProductIcon kind="welder" />, label: '焊工管理' },
  { icon: <ProductIcon kind="equipment" />, label: '设备管理' },
  { icon: <ProductIcon kind="quality" />, label: '质量管理' },
] as const

const OVERVIEW_CARDS = [
  { icon: <ProductIcon kind="wps" />, title: 'WPS记录', value: '12', color: '#38bdf8' },
  { icon: <ProductIcon kind="pqr" />, title: 'PQR记录', value: '8', color: '#22c55e' },
  { icon: <ProductIcon kind="welder" />, title: '认证焊工', value: '24', color: '#f59e0b' },
  { icon: <ProductIcon kind="equipment" />, title: '设备台账', value: '6', color: '#8b5cf6' },
] as const

/** 还原真实「侧栏 + 仪表盘」界面，避免与产品不符的假图 */
const AppShellPreview: React.FC = () => (
  <div className="welcome-shell" aria-hidden>
    <aside className="welcome-shell__sider">
      <div className="welcome-shell__logo">
        <span className="welcome-shell__logo-mark">
          <BrandMark size={32} />
        </span>
        <span className="welcome-shell__logo-text">
          <strong>焊序</strong>
          <em>Weld Sequence</em>
        </span>
      </div>
      <nav className="welcome-shell__menu">
        {SIDE_MENUS.map((item) => (
          <div
            key={item.label}
            className={`welcome-shell__menu-item${'active' in item && item.active ? ' is-active' : ''}`}
          >
            <span className="welcome-shell__menu-icon">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
    </aside>

    <div className="welcome-shell__main">
      <header className="welcome-shell__header">
        <span className="welcome-shell__header-left">
          <MenuFoldOutlined />
          <span className="welcome-shell__search">
            <SearchOutlined />
            搜索 WPS / PQR / 焊工…
          </span>
        </span>
        <span className="welcome-shell__header-right">
          <BellOutlined />
          <span className="welcome-shell__avatar">工</span>
        </span>
      </header>

      <div className="welcome-shell__body">
        <div className="welcome-shell__banner">
          <div>
            <div className="welcome-shell__banner-title">欢迎回来，工程师</div>
            <div className="welcome-shell__banner-desc">
              这是您的焊序概览，高效管理焊接工艺、资质评定和焊工信息。
            </div>
          </div>
          <div className="welcome-shell__banner-stats">
            <div>
              <b>12</b>
              <span>WPS记录</span>
            </div>
            <div>
              <b>8</b>
              <span>PQR记录</span>
            </div>
            <div>
              <b>24</b>
              <span>认证焊工</span>
            </div>
          </div>
        </div>

        <div className="welcome-shell__row">
          <div className="welcome-shell__panel">
            <div className="welcome-shell__panel-head">
              <CrownOutlined />
              <span>个人专业版</span>
            </div>
            <div className="welcome-shell__panel-sub">存储 128MB / 500MB</div>
            <div className="welcome-shell__bar">
              <i style={{ width: '26%' }} />
            </div>
          </div>
          <div className="welcome-shell__panel">
            <div className="welcome-shell__panel-head">
              <SettingOutlined />
              <span>快速操作</span>
            </div>
            <div className="welcome-shell__actions">
              <span>
                <PlusOutlined /> 创建WPS
              </span>
              <span>
                <PlusOutlined /> 创建PQR
              </span>
              <span>
                <BarChartOutlined /> 报表
              </span>
            </div>
          </div>
        </div>

        <div className="welcome-shell__cards">
          {OVERVIEW_CARDS.map((card) => (
            <div key={card.title} className="welcome-shell__card">
              <span className="welcome-shell__card-icon" style={{ color: card.color }}>
                {card.icon}
              </span>
              <div>
                <div className="welcome-shell__card-label">{card.title}</div>
                <div className="welcome-shell__card-value">{card.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
)

const Welcome: React.FC = () => {
  const navigate = useNavigate()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="welcome-page">
      <PublicNavbar />

      <section className="welcome-hero">
        <div className="welcome-hero__glow" aria-hidden />
        <div className="welcome-hero__inner">
          <div className="welcome-hero__copy">
            <p className="welcome-eyebrow">焊接工艺数字化管理</p>
            <h1 className="welcome-brand">焊序</h1>
            <p className="welcome-headline">把 WPS / PQR 管成可审批、可追溯的数字资产</p>
            <p className="welcome-lead">
              覆盖工艺创建、审批流转与文档导出，服务焊接工程师与制造企业质量体系。
            </p>
            <div className="welcome-cta">
              <button
                type="button"
                className="welcome-btn welcome-btn--primary"
                onClick={() => navigate('/register')}
              >
                免费开始
                <ArrowRightOutlined />
              </button>
              <button
                type="button"
                className="welcome-btn welcome-btn--ghost"
                onClick={() => navigate('/login')}
              >
                登录账号
              </button>
            </div>
          </div>

          <div className="welcome-hero__visual">
            <AppShellPreview />
          </div>
        </div>
      </section>

      <section className="welcome-section welcome-flow" aria-labelledby="welcome-flow-title">
        <div className="welcome-section__inner">
          <div className="welcome-section__head welcome-section__head--center">
            <span className="welcome-kicker">工作流</span>
            <h2 id="welcome-flow-title" className="welcome-h2">
              三步完成工艺文档闭环
            </h2>
            <p className="welcome-section-lead">从起草到现场使用，少一次来回，多一份可追溯记录。</p>
          </div>

          <div className="welcome-steps">
            {STEPS.map((step) => (
              <article key={step.num} className="welcome-step">
                <div className="welcome-step__num">{step.num}</div>
                <h3 className="welcome-step__title">{step.title}</h3>
                <p className="welcome-step__desc">{step.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="welcome-section welcome-capabilities" aria-labelledby="welcome-cap-title">
        <div className="welcome-section__inner">
          <div className="welcome-section__head">
            <span className="welcome-kicker">能力</span>
            <h2 id="welcome-cap-title" className="welcome-h2">
              与登录后工作台一致的专业能力
            </h2>
            <p className="welcome-section-lead">
              仪表盘、WPS/PQR、焊工设备与质量模块同一套工作区，所见即所用。
            </p>
          </div>

          <div className="welcome-cap-list">
            {CAPABILITIES.map((item) => (
              <article key={item.title} className="welcome-cap">
                <div className="welcome-cap__icon">{item.icon}</div>
                <div>
                  <h3 className="welcome-cap__title">{item.title}</h3>
                  <p className="welcome-cap__desc">{item.description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="welcome-cta-band" aria-labelledby="welcome-cta-title">
        <div className="welcome-cta-band__inner">
          <h2 id="welcome-cta-title" className="welcome-h2">
            今天就开始规范管理工艺文件
          </h2>
          <p className="welcome-section-lead">基础版永久免费，注册即可进入与上图一致的工作台。</p>
          <div className="welcome-cta">
            <button
              type="button"
              className="welcome-btn welcome-btn--light"
              onClick={() => navigate('/register')}
            >
              免费注册
            </button>
            <button
              type="button"
              className="welcome-btn welcome-btn--outline-light"
              onClick={() => navigate('/features')}
            >
              了解功能
            </button>
          </div>
        </div>
      </section>

      <footer className="welcome-footer">
        <div className="welcome-footer__inner">
          <div className="welcome-footer__grid">
            <div>
              <p className="welcome-footer__brand">焊序</p>
              <p className="welcome-footer__about">
                专业焊接工艺管理平台，帮助工程师与企业高效管理 WPS、PQR 与生产质量资料。
              </p>
            </div>
            <div className="welcome-footer__col">
              <h4>产品</h4>
              <nav>
                <Link to="/features">产品功能</Link>
                <Link to="/analytics">统计分析</Link>
                <Link to="/about">关于我们</Link>
              </nav>
            </div>
            <div className="welcome-footer__col">
              <h4>账户</h4>
              <nav>
                <Link to="/login">登录</Link>
                <Link to="/register">注册</Link>
                <Link to="/features">功能介绍</Link>
              </nav>
            </div>
            <div className="welcome-footer__col">
              <h4>法律</h4>
              <nav>
                <Link to="/terms-of-service">用户协议</Link>
                <Link to="/privacy-policy">隐私政策</Link>
                <Link to="/refund-policy">退款政策</Link>
                <Link to="/pricing-info">价格说明</Link>
              </nav>
            </div>
          </div>
          <div className="welcome-footer__bar">
            © {new Date().getFullYear()} 焊序 ·{' '}
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">
              鲁ICP备2025191429号-1
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Welcome
