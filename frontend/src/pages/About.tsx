import React, { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  RocketOutlined,
  EyeOutlined,
  HeartOutlined,
  MailOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'
import PublicFooter from '@/components/PublicFooter'
import '@/styles/PublicPage.css'

const VALUES = [
  {
    icon: <RocketOutlined />,
    title: '创新驱动',
    description: '持续把数字化能力带到焊接现场，用可用、可落地的工具替代纸质与表格碎片。',
  },
  {
    icon: <EyeOutlined />,
    title: '专业专注',
    description: '深耕工艺规程、评定与质量协同，只做焊接行业真正需要的管理场景。',
  },
  {
    icon: <HeartOutlined />,
    title: '客户至上',
    description: '以企业真实流程为中心，把审批、权限与报表设计得清楚、稳妥、好上手。',
  },
] as const

const CONTACT = [
  {
    icon: <MailOutlined />,
    label: '邮箱',
    value: 'contact@sdhaohan.cn',
  },
  {
    icon: <PhoneOutlined />,
    label: '电话',
    value: '400-XXX-XXXX',
  },
  {
    icon: <EnvironmentOutlined />,
    label: '地址',
    value: '山东省',
  },
] as const

const About: React.FC = () => {
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="public-page">
      <PublicNavbar />

      <header className="public-hero">
        <div className="public-hero__glow" aria-hidden />
        <div className="public-hero__inner">
          <p className="public-eyebrow">About</p>
          <h1 className="public-brand-mark">焊序</h1>
          <p className="public-hero__title">为焊接行业而生的数字化工作台</p>
          <p className="public-hero__lead">
            我们专注工艺文档、评定记录、焊工设备与质量协同，帮助企业把分散的流程收拢到同一套可追溯的系统里。
          </p>
          <div className="public-cta-row">
            <Link to="/register" className="public-btn public-btn--primary">
              加入焊序
              <ArrowRightOutlined />
            </Link>
            <Link to="/features" className="public-btn public-btn--ghost">
              浏览产品功能
            </Link>
          </div>
        </div>
      </header>

      <section className="public-section">
        <div className="public-section__inner">
          <div className="public-section__head">
            <h2 className="public-section__title">使命与愿景</h2>
            <p className="public-section__desc">用数字化把焊接工艺管理做得更清晰、更高效、更可信赖。</p>
          </div>
          <div className="public-prose-grid">
            <article className="public-prose">
              <h3>我们的使命</h3>
              <p>
                通过数字化技术提升焊接工艺管理效率，降低企业运营成本，推动焊接行业从纸质与碎片化工具，迈向可协作、可审计的统一平台。
              </p>
            </article>
            <article className="public-prose">
              <h3>我们的愿景</h3>
              <p>
                成为焊接工艺管理领域最值得信赖的数字化平台，为工艺、质量与现场团队提供持续可靠的产品与服务。
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="public-section public-section--alt">
        <div className="public-section__inner">
          <div className="public-section__head public-section__head--center">
            <h2 className="public-section__title">核心价值观</h2>
            <p className="public-section__desc">决定我们如何做产品、如何服务客户。</p>
          </div>
          <div className="public-values">
            {VALUES.map((value) => (
              <article key={value.title} className="public-value">
                <div className="public-value__icon">{value.icon}</div>
                <h4>{value.title}</h4>
                <p>{value.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="public-section">
        <div className="public-section__inner">
          <div className="public-section__head">
            <h2 className="public-section__title">联系我们</h2>
            <p className="public-section__desc">合作咨询、产品反馈或商务洽谈，欢迎来信来电。</p>
          </div>
          <div className="public-contact">
            {CONTACT.map((item) => (
              <div key={item.label} className="public-contact__item">
                <span className="ico">{item.icon}</span>
                <div>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="public-banner">
        <div className="public-banner__inner">
          <h2>加入我们，开启数字化之旅</h2>
          <p>立即注册，体验专业的焊序工作区。</p>
          <div className="public-cta-row">
            <Link to="/register" className="public-btn public-btn--light">
              免费注册
            </Link>
            <Link to="/login" className="public-btn public-btn--outline-light">
              立即登录
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  )
}

export default About
