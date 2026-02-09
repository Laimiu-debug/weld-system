import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Button,
  Table,
  Statistic,
  Typography,
  Tag,
  Progress,
  Alert,
  Space,
  Divider,
  Timeline,
} from 'antd'
import {
  FileTextOutlined,
  DownloadOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  BarChartOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface PQRData {
  id: string
  pqrNumber: string
  wpsNumber: string
  title: string
  status: 'in_progress' | 'completed' | 'failed' | 'cancelled'
  createdAt: string
  completedAt?: string
  tester: string
  results: {
    tensile: string
    bend: string
    impact: string
    hardness: string
    visual: string
  }
  score: number
  notes: string
}

interface TimelineItem {
  time: string
  content: string
  status: 'success' | 'warning' | 'error' | 'info'
}

const PQRReport: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ])
  const [loading, setLoading] = useState(false)
  const [pqrData, setPqrData] = useState<PQRData[]>([])

  // 模拟数据
  useEffect(() => {
    const mockData: PQRData[] = [
      {
        id: '1',
        pqrNumber: 'PQR-2024-001',
        wpsNumber: 'WPS-2024-001',
        title: '压力容器筒体焊接工艺评定',
        status: 'completed',
        createdAt: '2024-01-15',
        completedAt: '2024-01-18',
        tester: '张工程师',
        results: {
          tensile: '合格',
          bend: '合格',
          impact: '合格',
          hardness: '合格',
          visual: '合格',
        },
        score: 95,
        notes: '所有测试项目均符合要求',
      },
      {
        id: '2',
        pqrNumber: 'PQR-2024-002',
        wpsNumber: 'WPS-2024-002',
        title: '管道对接焊缝工艺评定',
        status: 'completed',
        createdAt: '2024-01-18',
        completedAt: '2024-01-20',
        tester: '李工程师',
        results: {
          tensile: '合格',
          bend: '合格',
          impact: '合格',
          hardness: '合格',
          visual: '合格',
        },
        score: 92,
        notes: '测试结果良好，符合规范要求',
      },
      {
        id: '3',
        pqrNumber: 'PQR-2024-003',
        wpsNumber: 'WPS-2024-003',
        title: '不锈钢储罐焊接工艺评定',
        status: 'in_progress',
        createdAt: '2024-01-20',
        tester: '王工程师',
        results: {
          tensile: '待测',
          bend: '待测',
          impact: '待测',
          hardness: '待测',
          visual: '待测',
        },
        score: 0,
        notes: '正在进行拉伸试验',
      },
      {
        id: '4',
        pqrNumber: 'PQR-2024-004',
        wpsNumber: 'WPS-2024-004',
        title: '热交换器管束焊接工艺评定',
        status: 'failed',
        createdAt: '2024-01-22',
        completedAt: '2024-01-24',
        tester: '赵工程师',
        results: {
          tensile: '不合格',
          bend: '合格',
          impact: '合格',
          hardness: '合格',
          visual: '合格',
        },
        score: 60,
        notes: '拉伸试验不符合要求，需要重新评定',
      },
      {
        id: '5',
        pqrNumber: 'PQR-2024-005',
        wpsNumber: 'WPS-2024-005',
        title: '储罐罐底焊接工艺评定',
        status: 'cancelled',
        createdAt: '2024-01-23',
        tester: '钱工程师',
        results: {
          tensile: '未测',
          bend: '未测',
          impact: '未测',
          hardness: '未测',
          visual: '未测',
        },
        score: 0,
        notes: '测试取消，原因：设备故障',
      },
    ]
    setPqrData(mockData)
  }, [])

  // 计算统计数据
  const getStatistics = () => {
    const total = pqrData.length
    const completed = pqrData.filter(item => item.status === 'completed').length
    const inProgress = pqrData.filter(item => item.status === 'in_progress').length
    const failed = pqrData.filter(item => item.status === 'failed').length
    const cancelled = pqrData.filter(item => item.status === 'cancelled').length
    const avgScore = pqrData
      .filter(item => item.status === 'completed')
      .reduce((sum, item) => sum + item.score, 0) / (completed || 1)

    return {
      total,
      completed,
      inProgress,
      failed,
      cancelled,
      avgScore: Math.round(avgScore),
      passRate: total > 0 ? Math.round((completed / total) * 100) : 0,
    }
  }

  const stats = getStatistics()

  // 处理筛选
  const handleFilter = () => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }

  // 处理导出
  const handleExport = (format: string) => {
    console.log(`导出${format}格式报告`)
  }

  const columns = [
    {
      title: 'PQR编号',
      dataIndex: 'pqrNumber',
      key: 'pqrNumber',
      render: (text: string, record: PQRData) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: 'WPS编号',
      dataIndex: 'wpsNumber',
      key: 'wpsNumber',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '评定项目',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
          in_progress: { color: 'processing', text: '进行中', icon: <ClockCircleOutlined /> },
          completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
          failed: { color: 'error', text: '失败', icon: <ExclamationCircleOutlined /> },
          cancelled: { color: 'default', text: '已取消', icon: <ClockCircleOutlined /> },
        }
        const config = statusConfig[status] || statusConfig.in_progress
        return <Tag color={config.color} icon={config.icon}>{config.text}</Tag>
      },
    },
    {
      title: '测试工程师',
      dataIndex: 'tester',
      key: 'tester',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '完成时间',
      dataIndex: 'completedAt',
      key: 'completedAt',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '评分',
      dataIndex: 'score',
      key: 'score',
      render: (score: number, record: PQRData) => {
        if (record.status !== 'completed') return '-'
        return (
          <Space>
            <Text>{score}</Text>
            <Progress
              percent={score}
              size="small"
              status={score >= 90 ? 'success' : score >= 70 ? 'normal' : 'exception'}
              style={{ width: 60 }}
            />
          </Space>
        )
      },
    },
  ]

  const timelineData: TimelineItem[] = [
    {
      time: '2024-01-24',
      content: 'PQR-2024-004 测试完成',
      status: 'error',
    },
    {
      time: '2024-01-20',
      content: 'PQR-2024-003 开始测试',
      status: 'info',
    },
    {
      time: '2024-01-20',
      content: 'PQR-2024-002 测试完成',
      status: 'success',
    },
    {
      time: '2024-01-18',
      content: 'PQR-2024-001 测试完成',
      status: 'success',
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>PQR统计报表</Title>
        <Text type="secondary">工艺评定记录统计分析报告</Text>
      </div>

      {/* 筛选条件 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker value={dateRange} onChange={setDateRange} />
          </Col>
          <Col>
            <Select placeholder="状态筛选" style={{ width: 120 }} allowClear>
              <Option value="in_progress">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Col>
          <Col>
            <Button icon={<FilterOutlined />} onClick={handleFilter}>
              筛选
            </Button>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={() => handleExport('excel')}>
                导出Excel
              </Button>
              <Button icon={<DownloadOutlined />} onClick={() => handleExport('pdf')}>
                导出PDF
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="PQR总数"
              value={stats.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                通过率: {stats.passRate}%
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均评分"
              value={stats.avgScore}
              suffix="/ 100"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="进行中"
              value={stats.inProgress}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12}>
          <Card title="测试结果分布">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div className="flex justify-between">
                <Text>已完成</Text>
                <Tag color="success">{stats.completed}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>进行中</Text>
                <Tag color="processing">{stats.inProgress}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>失败</Text>
                <Tag color="error">{stats.failed}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>已取消</Text>
                <Tag color="default">{stats.cancelled}</Tag>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card title="评分分布">
            <Space direction="vertical" style={{ width: '100%' }}>
              {pqrData
                .filter(item => item.status === 'completed')
                .sort((a, b) => b.score - a.score)
                .slice(0, 5)
                .map((item) => (
                  <div key={item.id} className="flex justify-between">
                    <Text>{item.pqrNumber}</Text>
                    <Space>
                      <Text>{item.score}分</Text>
                      <Progress
                        percent={item.score}
                        size="small"
                        status={item.score >= 90 ? 'success' : item.score >= 70 ? 'normal' : 'exception'}
                        style={{ width: 80 }}
                      />
                    </Space>
                  </div>
                ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* PQR列表 */}
      <Card title="PQR详细列表" className="mb-6">
        <Table
          columns={columns}
          dataSource={pqrData}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 时间线 */}
      <Card title="最近活动时间线">
        <Timeline
          items={timelineData.map((item, index) => ({
            key: index,
            children: (
              <div>
                <Text strong>{item.time}</Text>
                <br />
                <Text>{item.content}</Text>
              </div>
            ),
            color:
              item.status === 'success'
                ? 'green'
                : item.status === 'error'
                ? 'red'
                : item.status === 'warning'
                ? 'orange'
                : 'blue',
          }))}
        />
      </Card>

      <Divider />

      {/* 导出说明 */}
      <Alert
        message="导出说明"
        description="Excel格式适合数据分析，PDF格式适合打印和分享。导出的数据将包含完整的测试结果和评分信息。"
        type="info"
        showIcon
      />
    </div>
  )
}

export default PQRReport