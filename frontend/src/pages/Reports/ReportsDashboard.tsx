import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Button,
  Space,
  DatePicker,
  Table,
  Tag,
  Progress,
  Alert,
  Spin,
} from 'antd'
import {
  FileTextOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import reportsService, { ReportStatistics } from '@/services/reports'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const EMPTY_STATS: ReportStatistics = {
  wps: { total: 0, approved: 0, pending: 0, rejected: 0 },
  pqr: { total: 0, completed: 0, in_progress: 0 },
  quality: { total: 0, passed: 0, failed: 0, pass_rate: 0 },
  production: { total: 0, completed: 0, in_progress: 0, overdue: 0 },
  ppqr: { total: 0, converted: 0 },
  materials: { total: 0, low_stock: 0, out_of_stock: 0 },
  welders: { total: 0 },
  equipment: { total: 0 },
}

const ReportsDashboard: React.FC = () => {
  const navigate = useNavigate()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<ReportStatistics>(EMPTY_STATS)
  const [catalog, setCatalog] = useState<Array<{ key: string; name: string; path: string }>>([])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [statsResp, catalogResp] = await Promise.all([
        reportsService.getStatistics(
          dateRange[0].format('YYYY-MM-DD'),
          dateRange[1].format('YYYY-MM-DD')
        ),
        reportsService.getCatalog(),
      ])
      const statsPayload = (statsResp as any)?.data?.data || (statsResp as any)?.data
      const catalogPayload = (catalogResp as any)?.data?.data?.items || (catalogResp as any)?.data?.items
      if (statsPayload?.wps) {
        setStats(statsPayload)
      }
      if (Array.isArray(catalogPayload)) {
        setCatalog(catalogPayload)
      }
    } catch (error) {
      console.error('加载报表统计失败', error)
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  useEffect(() => {
    loadData()
  }, [loadData])

  const percent = (part: number, total: number) => (total > 0 ? Math.round((part / total) * 100) : 0)

  const columns = [
    {
      title: '报表名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'key',
      key: 'key',
      render: (key: string) => <Tag color="blue">{key.toUpperCase()}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: { path: string }) => (
        <Button type="link" onClick={() => navigate(record.path)}>
          查看
        </Button>
      ),
    },
  ]

  return (
    <div className="list-page">
      <ListPageHeader
        title="统计概览"
        description="基于当前工作区真实数据汇总"
      />

      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker
              value={dateRange}
              onChange={(range) => {
                if (range?.[0] && range[1]) {
                  setDateRange([range[0], range[1]])
                }
              }}
            />
          </Col>
          <Col>
            <Button icon={<FilterOutlined />} onClick={loadData}>
              筛选
            </Button>
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="WPS文档"
                value={stats.wps.total}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
              <div className="mt-3">
                <Text type="secondary" className="text-xs">
                  已批准: {stats.wps.approved} | 待审核: {stats.wps.pending} | 已拒绝: {stats.wps.rejected}
                </Text>
                <Progress percent={percent(stats.wps.approved, stats.wps.total)} size="small" className="mt-2" />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="PQR记录"
                value={stats.pqr.total}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
              <div className="mt-3">
                <Text type="secondary" className="text-xs">
                  已完成: {stats.pqr.completed} | 进行中: {stats.pqr.in_progress}
                </Text>
                <Progress
                  percent={percent(stats.pqr.completed, stats.pqr.total)}
                  size="small"
                  className="mt-2"
                  strokeColor="#52c41a"
                />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="质量检验"
                value={stats.quality.total}
                prefix={<PieChartOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
              <div className="mt-3">
                <Text type="secondary" className="text-xs">
                  通过: {stats.quality.passed} | 失败: {stats.quality.failed}
                </Text>
                <Progress
                  percent={percent(stats.quality.passed, stats.quality.total)}
                  size="small"
                  className="mt-2"
                  strokeColor="#fa8c16"
                />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="生产任务"
                value={stats.production.total}
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
              <div className="mt-3">
                <Text type="secondary" className="text-xs">
                  已完成: {stats.production.completed} | 进行中: {stats.production.in_progress} | 逾期: {stats.production.overdue}
                </Text>
                <Progress
                  percent={percent(stats.production.completed, stats.production.total)}
                  size="small"
                  className="mt-2"
                  strokeColor="#722ed1"
                />
              </div>
            </Card>
          </Col>
        </Row>
      </Spin>

      <Card title="快速查看报表" className="mb-6">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Button block size="large" icon={<FileTextOutlined />} onClick={() => navigate('/reports/wps')}>
              WPS统计报表
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button block size="large" icon={<BarChartOutlined />} onClick={() => navigate('/reports/pqr')}>
              PQR统计报表
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button block size="large" icon={<PieChartOutlined />} onClick={() => navigate('/quality')}>
              质量检验
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button block size="large" icon={<LineChartOutlined />} onClick={() => navigate('/reports/usage')}>
              使用统计报表
            </Button>
          </Col>
        </Row>
      </Card>

      <Card title="可用报表">
        <Table
          columns={columns}
          dataSource={catalog}
          rowKey="key"
          pagination={false}
        />
      </Card>

      <Alert
        message="报表说明"
        description="以上数字来自当前工作区的真实记录，可按创建/检验日期筛选。"
        type="info"
        showIcon
        className="mt-6"
      />
    </div>
  )
}

export default ReportsDashboard
