import React, { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Button, Row, Col, Card, Statistic } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts'
import PublicNavbar from '@/components/PublicNavbar'

const Analytics: React.FC = () => {
  const trendChartRef = useRef<HTMLDivElement>(null)
  const pieChartRef = useRef<HTMLDivElement>(null)
  const barChartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    window.scrollTo(0, 0)

    // 延迟初始化图表，确保DOM已经渲染
    const timer = setTimeout(() => {
      // 趋势图
      if (trendChartRef.current) {
        const trendChart = echarts.init(trendChartRef.current)
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['WPS', 'PQR', 'pPQR'] },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月', '5月', '6月'],
        },
        yAxis: { type: 'value' },
        series: [
          {
            name: 'WPS',
            type: 'line',
            data: [120, 132, 101, 134, 90, 230],
            smooth: true,
            itemStyle: { color: '#1F5EFF' },
          },
          {
            name: 'PQR',
            type: 'line',
            data: [220, 182, 191, 234, 290, 330],
            smooth: true,
            itemStyle: { color: '#38A169' },
          },
          {
            name: 'pPQR',
            type: 'line',
            data: [150, 232, 201, 154, 190, 330],
            smooth: true,
            itemStyle: { color: '#FFC857' },
          },
        ],
      })
    }

    // 饼图
    if (pieChartRef.current) {
      const pieChart = echarts.init(pieChartRef.current)
      pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { orient: 'vertical', left: 'left' },
        series: [
          {
            name: '文档类型',
            type: 'pie',
            radius: '50%',
            data: [
              { value: 1048, name: 'WPS', itemStyle: { color: '#1F5EFF' } },
              { value: 735, name: 'PQR', itemStyle: { color: '#38A169' } },
              { value: 580, name: 'pPQR', itemStyle: { color: '#FFC857' } },
              { value: 484, name: '其他', itemStyle: { color: '#9CA3AF' } },
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)',
              },
            },
          },
        ],
      })
    }

    // 柱状图
    if (barChartRef.current) {
      const barChart = echarts.init(barChartRef.current)
      barChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['通过', '待审', '驳回'] },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月', '5月', '6月'],
        },
        yAxis: { type: 'value' },
        series: [
          {
            name: '通过',
            type: 'bar',
            data: [320, 332, 301, 334, 390, 430],
            itemStyle: { color: '#38A169' },
          },
          {
            name: '待审',
            type: 'bar',
            data: [120, 132, 101, 134, 90, 130],
            itemStyle: { color: '#FFC857' },
          },
          {
            name: '驳回',
            type: 'bar',
            data: [20, 32, 21, 24, 10, 20],
            itemStyle: { color: '#EF4444' },
          },
        ],
      })
      }
    }, 100) // 延迟100ms初始化

    return () => {
      clearTimeout(timer)
      // 安全地销毁图表实例
      if (trendChartRef.current) {
        try {
          echarts.dispose(trendChartRef.current)
        } catch (e) {
          console.error('Failed to dispose trend chart:', e)
        }
      }
      if (pieChartRef.current) {
        try {
          echarts.dispose(pieChartRef.current)
        } catch (e) {
          console.error('Failed to dispose pie chart:', e)
        }
      }
      if (barChartRef.current) {
        try {
          echarts.dispose(barChartRef.current)
        } catch (e) {
          console.error('Failed to dispose bar chart:', e)
        }
      }
    }
  }, [])

  const stats = [
    {
      title: '总文档数',
      value: 2847,
      prefix: <FileTextOutlined />,
      suffix: '份',
      valueStyle: { color: '#1F5EFF' },
      trend: 12.5,
    },
    {
      title: '通过率',
      value: 94.2,
      suffix: '%',
      prefix: <CheckCircleOutlined />,
      valueStyle: { color: '#38A169' },
      trend: 2.3,
    },
    {
      title: '平均审批时长',
      value: 2.4,
      suffix: '天',
      prefix: <ClockCircleOutlined />,
      valueStyle: { color: '#FFC857' },
      trend: -15.2,
    },
    {
      title: '活跃用户',
      value: 156,
      suffix: '人',
      prefix: <TeamOutlined />,
      valueStyle: { color: '#8B5CF6' },
      trend: 8.7,
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
            数据统计分析
          </h1>
          <p style={{ fontSize: 20, color: '#4A5568', marginBottom: 40, lineHeight: 1.6, margin: '0 0 40px 0' }}>
            全面的数据可视化，助力科学决策
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px 60px' }}>
        <Row gutter={[24, 24]}>
          {stats.map((stat, index) => (
            <Col xs={24} sm={12} lg={6} key={index}>
              <Card style={{ borderRadius: 16, border: '1px solid #e5e7eb' }}>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  prefix={stat.prefix}
                  suffix={stat.suffix}
                  valueStyle={stat.valueStyle}
                />
                <div style={{ marginTop: 12, fontSize: 14 }}>
                  {stat.trend > 0 ? (
                    <span style={{ color: '#38A169' }}>
                      <ArrowUpOutlined /> {stat.trend}%
                    </span>
                  ) : (
                    <span style={{ color: '#EF4444' }}>
                      <ArrowDownOutlined /> {Math.abs(stat.trend)}%
                    </span>
                  )}
                  <span style={{ marginLeft: 8, color: '#9CA3AF' }}>较上月</span>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* Charts */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px 80px' }}>
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card title="文档创建趋势" style={{ borderRadius: 16, border: '1px solid #e5e7eb' }}>
              <div ref={trendChartRef} style={{ height: 400 }}></div>
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="文档类型分布" style={{ borderRadius: 16, border: '1px solid #e5e7eb' }}>
              <div ref={pieChartRef} style={{ height: 400 }}></div>
            </Card>
          </Col>
          <Col xs={24}>
            <Card title="审批状态统计" style={{ borderRadius: 16, border: '1px solid #e5e7eb' }}>
              <div ref={barChartRef} style={{ height: 400 }}></div>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Features List */}
      <div style={{ background: 'white', padding: '80px 24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', marginBottom: 48, fontSize: 36, fontWeight: 700, color: '#1A202C', margin: '0 0 48px 0' }}>
            统计分析功能
          </h2>
          <Row gutter={[32, 32]}>
            <Col xs={24} md={12}>
              <div style={{ padding: 24 }}>
                <h4 style={{ fontSize: 20, fontWeight: 600, color: '#1A202C', margin: '0 0 16px 0' }}>实时数据监控</h4>
                <p style={{ color: '#4A5568', fontSize: 16, lineHeight: 1.6, margin: 0 }}>
                  实时追踪关键业务指标，包括文档数量、通过率、审批时长等，帮助管理者及时了解业务状况。
                </p>
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div style={{ padding: 24 }}>
                <h4 style={{ fontSize: 20, fontWeight: 600, color: '#1A202C', margin: '0 0 16px 0' }}>多维度统计</h4>
                <p style={{ color: '#4A5568', fontSize: 16, lineHeight: 1.6, margin: 0 }}>
                  支持按时间、部门、人员、文档类型等多个维度进行数据统计和分析，满足不同管理需求。
                </p>
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div style={{ padding: 24 }}>
                <h4 style={{ fontSize: 20, fontWeight: 600, color: '#1A202C', margin: '0 0 16px 0' }}>趋势分析</h4>
                <p style={{ color: '#4A5568', fontSize: 16, lineHeight: 1.6, margin: 0 }}>
                  通过历史数据分析，识别业务趋势和规律，为未来决策提供数据支持。
                </p>
              </div>
            </Col>
            <Col xs={24} md={12}>
              <div style={{ padding: 24 }}>
                <h4 style={{ fontSize: 20, fontWeight: 600, color: '#1A202C', margin: '0 0 16px 0' }}>CSV 报表导出</h4>
                <p style={{ color: '#4A5568', fontSize: 16, lineHeight: 1.6, margin: 0 }}>
                  WPS、PQR 与使用统计支持导出 CSV，便于线下存档和二次分析。
                </p>
              </div>
            </Col>
          </Row>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{ background: '#1F5EFF', padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <h2 style={{ color: 'white', marginBottom: 24, fontSize: 36, fontWeight: 700, margin: '0 0 24px 0' }}>
            开始使用数据分析功能
          </h2>
          <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)', marginBottom: 32, lineHeight: 1.6, margin: '0 0 32px 0' }}>
            注册即可免费体验强大的数据统计分析功能
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
                焊序
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
              © 2025 焊序. All rights reserved. | 鲁ICP备2025191429号-1
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
