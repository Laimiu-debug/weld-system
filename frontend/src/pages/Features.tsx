import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileTextOutlined,
  ToolOutlined,
  TeamOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  CloudOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import PublicNavbar from '@/components/PublicNavbar'
import PublicFooter from '@/components/PublicFooter'
import '@/styles/PublicPage.css'

const CORE_FEATURES = [
  {
    icon: <FileTextOutlined />,
    title: 'WPS / PQR 管理',
    description: '焊接工艺规程与工艺评定记录全生命周期管理。',
    details: ['模板化创建', '版本与历史追踪', '智能审批流程', '一键导出 PDF / Word'],
  },
  {
    icon: <ToolOutlined />,
    title: '模块化模板',
    description: '按标准组合模块，适配不同焊接工艺规范。',
    details: ['自定义模板', '模块拖拽组合', '企业模板共享', '标准模板库'],
  },
  {
    icon: <TeamOutlined />,
    title: '企业协作',
    description: '多人协作、权限与审批一体，减少线下流转。',
    details: ['角色权限', '多级审批', '员工邀请入职', '消息提醒'],
  },
  {
    icon: <SafetyOutlined />,
    title: '数据安全',
    description: '工作区隔离与可追溯审批，保障企业数据边界。',
    details: ['加密存储', '工作区隔离', '审批留痕', '细粒度权限'],
  },
  {
    icon: <BarChartOutlined />,
    title: '统计分析',
    description: '多维度报表与导出，支撑工艺与质量决策。',
    details: ['实时监控', '多维统计', 'WPS / PQR 用量', 'CSV 导出'],
  },
  {
    icon: <CloudOutlined />,
    title: '云端访问',
    description: '按会员配额存储，多端随时查阅与协作。',
    details: ['配额存储', '多设备访问', '检索与导出', '企业资源共享'],
  },
] as const

const DETAIL_TABS = [
  {
    key: 'wps',
    label: 'WPS 管理',
    title: '焊接工艺规程管理',
    lead: '覆盖创建、审批到归档的全流程数字化，减少重复填表与版本混乱。',
    points: [
      '基于模板快速创建 WPS',
      '智能表单校验，保证关键字段完整',
      '多级审批，符合企业管理规范',
      '版本控制，追踪每次修改',
      '一键导出 PDF 或 Word',
    ],
    panelTitle: '工艺文档一次建好',
    panelText: '从模板到正式文档，参数、技术要求与审批记录同屏可查。',
    stats: [
      { value: '全流程', label: '创建到归档' },
      { value: '可追溯', label: '版本与审批' },
    ],
  },
  {
    key: 'pqr',
    label: 'PQR 管理',
    title: '工艺评定记录管理',
    lead: '试验数据、附件与合规检查集中管理，并与 WPS 关联引用。',
    points: [
      '详细试验数据记录',
      '测试结果可视化',
      '附件管理（照片、报告）',
      '风险评估与合规检查',
      '与 WPS 关联管理',
    ],
    panelTitle: '评定结果可核验',
    panelText: '试验与附件留存完整，方便质量与工艺团队复核。',
    stats: [
      { value: '关联', label: 'WPS 引用' },
      { value: '可视化', label: '试验数据' },
    ],
  },
  {
    key: 'collaboration',
    label: '团队协作',
    title: '企业级协作能力',
    lead: '权限、审批与通知联动，让工艺、质量、现场在同一工作区内协作。',
    points: [
      '灵活的角色权限配置',
      '自定义审批流程',
      '实时消息通知',
      '审批历史可查',
      '企业资源共享',
    ],
    panelTitle: '审批不掉队',
    panelText: '待办推送、状态可见、历史可查，缩短跨部门等待时间。',
    stats: [
      { value: '多级', label: '审批流程' },
      { value: '实时', label: '消息提醒' },
    ],
  },
] as const

const Features: React.FC = () => {
  const [activeTab, setActiveTab] = useState<(typeof DETAIL_TABS)[number]['key']>('wps')
  const active = DETAIL_TABS.find((tab) => tab.key === activeTab) ?? DETAIL_TABS[0]

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="public-page">
      <PublicNavbar />

      <header className="public-hero">
        <div className="public-hero__glow" aria-hidden />
        <div className="public-hero__inner">
          <p className="public-eyebrow">Product</p>
          <h1 className="public-brand-mark">焊序</h1>
          <p className="public-hero__title">焊接工艺管理的完整能力图谱</p>
          <p className="public-hero__lead">
            从文档创建到审批流转，从焊工设备到统计分析，用同一套工作区把工艺、质量与现场协同起来。
          </p>
          <ul className="public-hero__meta">
            <li>
              <span className="dot" aria-hidden />
              永久免费基础版
            </li>
            <li>
              <span className="dot" aria-hidden />
              模板化快速上手
            </li>
            <li>
              <span className="dot" aria-hidden />
              企业级协作与隔离
            </li>
          </ul>
          <div className="public-cta-row">
            <Link to="/register" className="public-btn public-btn--primary">
              免费注册
              <ArrowRightOutlined />
            </Link>
            <Link to="/analytics" className="public-btn public-btn--ghost">
              查看统计分析
            </Link>
          </div>
        </div>
      </header>

      <section className="public-section">
        <div className="public-section__inner">
          <div className="public-section__head public-section__head--center">
            <h2 className="public-section__title">核心功能</h2>
            <p className="public-section__desc">专为焊接行业打造的全流程管理能力，按模块清晰拆分。</p>
          </div>
          <div className="public-feature-grid">
            {CORE_FEATURES.map((feature) => (
              <article key={feature.title} className="public-feature">
                <div className="public-feature__icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
                <ul>
                  {feature.details.map((detail) => (
                    <li key={detail}>
                      <CheckCircleOutlined className="check" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="public-section public-section--alt">
        <div className="public-section__inner">
          <div className="public-section__head">
            <h2 className="public-section__title">功能详解</h2>
            <p className="public-section__desc">按场景深入了解 WPS、PQR 与团队协作如何落地。</p>
          </div>

          <div className="public-tabs" role="tablist" aria-label="功能详解">
            {DETAIL_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.key}
                className={`public-tab${activeTab === tab.key ? ' is-active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="public-detail" role="tabpanel">
            <div className="public-detail__copy">
              <h3>{active.title}</h3>
              <p>{active.lead}</p>
              <ul>
                {active.points.map((point) => (
                  <li key={point}>
                    <CheckCircleOutlined className="check" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
            <aside className="public-detail__panel" aria-hidden>
              <strong>{active.panelTitle}</strong>
              <p>{active.panelText}</p>
              <div className="public-detail__stats">
                {active.stats.map((stat) => (
                  <div key={stat.label}>
                    <em>{stat.value}</em>
                    <span>{stat.label}</span>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        </div>
      </section>

      <section className="public-banner">
        <div className="public-banner__inner">
          <h2>准备好开始了吗？</h2>
          <p>注册即可体验文档、审批与统计分析的完整工作流。</p>
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

export default Features
