import React, { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import PublicNavbar from '@/components/PublicNavbar'
import PublicFooter from '@/components/PublicFooter'
import '@/styles/PublicPage.css'

const AXIS_STYLE = {
  axisLine: { lineStyle: { color: 'rgba(20,24,31,0.12)' } },
  axisLabel: { color: '#6b7385', fontSize: 12 },
  splitLine: { lineStyle: { color: 'rgba(20,24,31,0.06)' } },
}

const Analytics: React.FC = () => {
  const trendChartRef = useRef<HTMLDivElement>(null)
  const pieChartRef = useRef<HTMLDivElement>(null)
  const barChartRef = useRef<HTMLDivElement>(null)
  const chartsRef = useRef<ECharts[]>([])

  useEffect(() => {
    window.scrollTo(0, 0)

    const charts: ECharts[] = []
    const timer = window.setTimeout(() => {
      if (trendChartRef.current) {
        const chart = echarts.init(trendChartRef.current)
        chart.setOption({
          color: ['#1F5EFF', '#2F7A4A', '#C96A2B'],
          tooltip: { trigger: 'axis' },
          legend: {
            data: ['WPS', 'PQR', 'pPQR'],
            top: 0,
            textStyle: { color: '#6b7385', fontSize: 12 },
          },
          grid: { left: 40, right: 16, top: 44, bottom: 28 },
          xAxis: {
            type: 'category',
            data: ['1月', '2月', '3月', '4月', '5月', '6月'],
            ...AXIS_STYLE,
          },
          yAxis: { type: 'value', ...AXIS_STYLE },
          series: [
            {
              name: 'WPS',
              type: 'line',
              data: [120, 132, 101, 134, 90, 230],
              smooth: true,
              symbol: 'circle',
              symbolSize: 6,
              areaStyle: { color: 'rgba(31,94,255,0.08)' },
            },
            {
              name: 'PQR',
              type: 'line',
              data: [220, 182, 191, 234, 290, 330],
              smooth: true,
              symbol: 'circle',
              symbolSize: 6,
              areaStyle: { color: 'rgba(47,122,74,0.08)' },
            },
            {
              name: 'pPQR',
              type: 'line',
              data: [150, 232, 201, 154, 190, 330],
              smooth: true,
              symbol: 'circle',
              symbolSize: 6,
              areaStyle: { color: 'rgba(201,106,43,0.08)' },
            },
          ],
        })
        charts.push(chart)
      }

      if (pieChartRef.current) {
        const chart = echarts.init(pieChartRef.current)
        chart.setOption({
          tooltip: { trigger: 'item' },
          legend: {
            orient: 'vertical',
            right: 8,
            top: 'middle',
            textStyle: { color: '#6b7385', fontSize: 12 },
          },
          series: [
            {
              name: '文档类型',
              type: 'pie',
              radius: ['42%', '68%'],
              center: ['38%', '50%'],
              avoidLabelOverlap: true,
              itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
              label: { show: false },
              data: [
                { value: 1048, name: 'WPS', itemStyle: { color: '#1F5EFF' } },
                { value: 735, name: 'PQR', itemStyle: { color: '#2F7A4A' } },
                { value: 580, name: 'pPQR', itemStyle: { color: '#C96A2B' } },
                { value: 484, name: '其他', itemStyle: { color: '#9AA3B2' } },
              ],
            },
          ],
        })
        charts.push(chart)
      }

      if (barChartRef.current) {
        const chart = echarts.init(barChartRef.current)
        chart.setOption({
          color: ['#2F7A4A', '#C96A2B', '#D64545'],
          tooltip: { trigger: 'axis' },
          legend: {
            data: ['通过', '待审', '驳回'],
            top: 0,
            textStyle: { color: '#6b7385', fontSize: 12 },
          },
          grid: { left: 40, right: 16, top: 44, bottom: 28 },
          xAxis: {
            type: 'category',
            data: ['1月', '2月', '3月', '4月', '5月', '6月'],
            ...AXIS_STYLE,
          },
          yAxis: { type: 'value', ...AXIS_STYLE },
          series: [
            {
              name: '通过',
              type: 'bar',
              barMaxWidth: 22,
              data: [320, 332, 301, 334, 390, 430],
              itemStyle: { borderRadius: [4, 4, 0, 0] },
            },
            {
              name: '待审',
              type: 'bar',
              barMaxWidth: 22,
              data: [120, 132, 101, 134, 90, 130],
              itemStyle: { borderRadius: [4, 4, 0, 0] },
            },
            {
              name: '驳回',
              type: 'bar',
              barMaxWidth: 22,
              data: [20, 32, 21, 24, 10, 20],
              itemStyle: { borderRadius: [4, 4, 0, 0] },
            },
          ],
        })
        charts.push(chart)
      }

      chartsRef.current = charts
    }, 80)

    const onResize = () => {
      chartsRef.current.forEach((chart) => chart.resize())
    }
    window.addEventListener('resize', onResize)

    return () => {
      window.clearTimeout(timer)
      window.removeEventListener('resize', onResize)
      chartsRef.current.forEach((chart) => {
        try {
          chart.dispose()
        } catch {
          /* ignore */
        }
      })
      chartsRef.current = []
    }
  }, [])

  const stats = [
    {
      title: '总文档数',
      value: '2,847',
      suffix: '份',
      icon: <FileTextOutlined />,
      trend: 12.5,
      up: true,
    },
    {
      title: '通过率',
      value: '94.2',
      suffix: '%',
      icon: <CheckCircleOutlined />,
      trend: 2.3,
      up: true,
    },
    {
      title: '平均审批时长',
      value: '2.4',
      suffix: '天',
      icon: <ClockCircleOutlined />,
      trend: 15.2,
      up: false,
    },
    {
      title: '活跃用户',
      value: '156',
      suffix: '人',
      icon: <TeamOutlined />,
      trend: 8.7,
      up: true,
    },
  ] as const

  const capabilities = [
    {
      title: '实时数据监控',
      text: '追踪文档量、通过率、审批时长等关键指标，管理者随时掌握业务节奏。',
    },
    {
      title: '多维度统计',
      text: '按时间、部门、人员、文档类型交叉分析，匹配不同管理视角。',
    },
    {
      title: '趋势分析',
      text: '用历史数据识别波动与规律，为产能与质量决策提供依据。',
    },
    {
      title: 'CSV 报表导出',
      text: 'WPS、PQR 与使用统计可导出 CSV，便于存档和二次分析。',
    },
  ] as const

  return (
    <div className="public-page">
      <PublicNavbar />

      <header className="public-hero">
        <div className="public-hero__glow" aria-hidden />
        <div className="public-hero__inner">
          <p className="public-eyebrow">Analytics</p>
          <h1 className="public-brand-mark">焊序</h1>
          <p className="public-hero__title">用数据读懂工艺与审批节奏</p>
          <p className="public-hero__lead">
            文档趋势、类型分布与审批状态一屏呈现。以下为产品能力示意，登录后可查看企业真实数据。
          </p>
          <div className="public-cta-row">
            <Link to="/register" className="public-btn public-btn--primary">
              免费体验
              <ArrowRightOutlined />
            </Link>
            <Link to="/features" className="public-btn public-btn--ghost">
              了解产品功能
            </Link>
          </div>
        </div>
      </header>

      <section className="public-section" style={{ paddingTop: 8 }}>
        <div className="public-section__inner">
          <div className="public-kpi-grid">
            {stats.map((stat) => (
              <article key={stat.title} className="public-kpi">
                <div className="public-kpi__label">
                  {stat.icon}
                  {stat.title}
                </div>
                <div className="public-kpi__value">
                  {stat.value}
                  <small>{stat.suffix}</small>
                </div>
                <div className="public-kpi__trend">
                  {stat.up ? (
                    <span className="up">
                      <ArrowUpOutlined /> {stat.trend}%
                    </span>
                  ) : (
                    <span className="down">
                      <ArrowDownOutlined /> {stat.trend}%
                    </span>
                  )}{' '}
                  较上月
                </div>
              </article>
            ))}
          </div>

          <div className="public-chart-grid">
            <article className="public-chart">
              <h3 className="public-chart__title">文档创建趋势</h3>
              <p className="public-chart__hint">近六月 WPS / PQR / pPQR 创建量示意</p>
              <div ref={trendChartRef} className="public-chart__canvas" />
            </article>
            <article className="public-chart">
              <h3 className="public-chart__title">文档类型分布</h3>
              <p className="public-chart__hint">当前库内文档构成示意</p>
              <div ref={pieChartRef} className="public-chart__canvas" />
            </article>
            <article className="public-chart public-chart--wide">
              <h3 className="public-chart__title">审批状态统计</h3>
              <p className="public-chart__hint">通过、待审与驳回的月度对比示意</p>
              <div ref={barChartRef} className="public-chart__canvas" />
            </article>
          </div>
        </div>
      </section>

      <section className="public-section public-section--alt">
        <div className="public-section__inner">
          <div className="public-section__head">
            <h2 className="public-section__title">统计分析能力</h2>
            <p className="public-section__desc">不只是好看的图表，而是可落地的管理指标与导出能力。</p>
          </div>
          <div className="public-capability-list">
            {capabilities.map((item) => (
              <article key={item.title} className="public-capability">
                <h4>{item.title}</h4>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="public-banner">
        <div className="public-banner__inner">
          <h2>开始使用数据分析</h2>
          <p>注册后即可在工作区查看真实业务指标与导出报表。</p>
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

export default Analytics
