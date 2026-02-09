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
} from 'antd'
import {
  FileTextOutlined,
  DownloadOutlined,
  FilterOutlined,
  BarChartOutlined,
  PieChartOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface WPSData {
  id: string
  wpsNumber: string
  title: string
  version: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  createdBy: string
  createdAt: string
  projectCount: number
  lastUsed: string
}

const WPSReport: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ])
  const [loading, setLoading] = useState(false)
  const [wpsData, setWpsData] = useState<WPSData[]>([])

  // 模拟数据
  useEffect(() => {
    const mockData: WPSData[] = [
      {
        id: '1',
        wpsNumber: 'WPS-2024-001',
        title: '压力容器筒体焊接工艺',
        version: '1.0',
        status: 'approved',
        createdBy: '张工程师',
        createdAt: '2024-01-15',
        projectCount: 12,
        lastUsed: '2024-01-20',
      },
      {
        id: '2',
        wpsNumber: 'WPS-2024-002',
        title: '管道对接焊缝工艺',
        version: '2.0',
        status: 'approved',
        createdBy: '李工程师',
        createdAt: '2024-01-18',
        projectCount: 8,
        lastUsed: '2024-01-19',
      },
      {
        id: '3',
        wpsNumber: 'WPS-2024-003',
        title: '不锈钢储罐焊接工艺',
        version: '1.0',
        status: 'pending',
        createdBy: '王工程师',
        createdAt: '2024-01-20',
        projectCount: 5,
        lastUsed: '2024-01-21',
      },
      {
        id: '4',
        wpsNumber: 'WPS-2024-004',
        title: '热交换器管束焊接工艺',
        version: '1.0',
        status: 'draft',
        createdBy: '赵工程师',
        createdAt: '2024-01-22',
        projectCount: 3,
        lastUsed: '',
      },
      {
        id: '5',
        wpsNumber: 'WPS-2024-005',
        title: '储罐罐底焊接工艺',
        version: '1.0',
        status: 'rejected',
        createdBy: '钱工程师',
        createdAt: '2024-01-23',
        projectCount: 2,
        lastUsed: '',
      },
    ]
    setWpsData(mockData)
  }, [])

  // 计算统计数据
  const getStatistics = () => {
    const total = wpsData.length
    const approved = wpsData.filter(item => item.status === 'approved').length
    const pending = wpsData.filter(item => item.status === 'pending').length
    const rejected = wpsData.filter(item => item.status === 'rejected').length
    const draft = wpsData.filter(item => item.status === 'draft').length
    const totalProjects = wpsData.reduce((sum, item) => sum + item.projectCount, 0)

    return {
      total,
      approved,
      pending,
      rejected,
      draft,
      totalProjects,
      approvalRate: total > 0 ? Math.round((approved / total) * 100) : 0,
    }
  }

  const stats = getStatistics()

  // 处理筛选
  const handleFilter = () => {
    setLoading(true)
    // 模拟API调用
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
      title: 'WPS编号',
      dataIndex: 'wpsNumber',
      key: 'wpsNumber',
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          pending: { color: 'processing', text: '待审核' },
          approved: { color: 'success', text: '已批准' },
          rejected: { color: 'error', text: '已拒绝' },
        }
        const config = statusConfig[status] || statusConfig.draft
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '创建者',
      dataIndex: 'createdBy',
      key: 'createdBy',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '关联项目',
      dataIndex: 'projectCount',
      key: 'projectCount',
      render: (count: number) => <Text>{count} 个</Text>,
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsed',
      key: 'lastUsed',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>WPS统计报表</Title>
        <Text type="secondary">焊接工艺规程统计分析报告</Text>
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
              <Option value="draft">草稿</Option>
              <Option value="pending">待审核</Option>
              <Option value="approved">已批准</Option>
              <Option value="rejected">已拒绝</Option>
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
              title="WPS总数"
              value={stats.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已批准"
              value={stats.approved}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                通过率: {stats.approvalRate}%
              </Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats.pending}
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="关联项目"
              value={stats.totalProjects}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 状态分布 */}
      <Card title="状态分布" className="mb-6">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <div className="mb-4">
              <Text strong>审批进度</Text>
            </div>
            <Progress
              percent={stats.approvalRate}
              status={stats.approvalRate >= 80 ? 'success' : 'active'}
              strokeColor={{
                from: '#108ee9',
                to: '#87d068',
              }}
            />
            <div className="mt-3">
              <Space>
                <Tag color="success">已批准: {stats.approved}</Tag>
                <Tag color="processing">待审核: {stats.pending}</Tag>
                <Tag color="default">草稿: {stats.draft}</Tag>
                <Tag color="error">已拒绝: {stats.rejected}</Tag>
              </Space>
            </div>
          </Col>
          <Col xs={24} sm={12}>
            <div className="mb-4">
              <Text strong>使用频率</Text>
            </div>
            <Space direction="vertical" style={{ width: '100%' }}>
              {wpsData.slice(0, 5).map((item) => (
                <div key={item.id} className="flex justify-between">
                  <Text>{item.wpsNumber}</Text>
                  <Space>
                    <Text type="secondary">{item.projectCount} 项目</Text>
                    <Progress
                      percent={Math.min((item.projectCount / 15) * 100, 100)}
                      size="small"
                      style={{ width: 80 }}
                    />
                  </Space>
                </div>
              ))}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* WPS列表 */}
      <Card title="WPS详细列表">
        <Table
          columns={columns}
          dataSource={wpsData}
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

      <Divider />

      {/* 导出说明 */}
      <Alert
        message="导出说明"
        description="Excel格式适合数据分析，PDF格式适合打印和分享。导出的数据将根据当前筛选条件生成。"
        type="info"
        showIcon
      />
    </div>
  )
}

export default WPSReport