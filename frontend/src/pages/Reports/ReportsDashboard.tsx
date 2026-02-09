import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Button,
  Space,
  DatePicker,
  Select,
  Table,
  Tag,
  Progress,
  Alert,
} from 'antd'
import {
  FileTextOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  DownloadOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

const ReportsDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])

  // 模拟数据
  const stats = {
    totalWPS: 156,
    approvedWPS: 128,
    pendingWPS: 18,
    rejectedWPS: 10,
    totalPQR: 89,
    completedPQR: 76,
    inProgressPQR: 8,
    totalInspections: 342,
    passedInspections: 315,
    failedInspections: 27,
    totalProjects: 45,
    completedProjects: 38,
    inProgressProjects: 7,
  }

  const recentReports = [
    {
      id: '1',
      name: '2024年1月WPS统计报告',
      type: 'WPS报告',
      status: 'completed',
      createdAt: '2024-02-01 10:30:00',
      downloadCount: 24,
    },
    {
      id: '2',
      name: '2024年1月质量检验报告',
      type: '质量报告',
      status: 'completed',
      createdAt: '2024-02-01 09:15:00',
      downloadCount: 18,
    },
    {
      id: '3',
      name: '设备使用统计报告',
      type: '设备报告',
      status: 'processing',
      createdAt: '2024-02-01 08:45:00',
      downloadCount: 0,
    },
    {
      id: '4',
      name: '焊工资质统计报告',
      type: '资质报告',
      status: 'completed',
      createdAt: '2024-01-31 16:20:00',
      downloadCount: 32,
    },
  ]

  const columns = [
    {
      title: '报告名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          'WPS报告': 'blue',
          '质量报告': 'green',
          '设备报告': 'orange',
          '资质报告': 'purple',
        }
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          completed: { color: 'success', text: '已完成' },
          processing: { color: 'processing', text: '生成中' },
          failed: { color: 'error', text: '失败' },
        }
        const config = statusMap[status] || statusMap.completed
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '下载次数',
      dataIndex: 'downloadCount',
      key: 'downloadCount',
      render: (count: number) => <Text>{count}</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: any) => (
        <Space>
          <Button
            type="text"
            icon={<DownloadOutlined />}
            disabled={record.status !== 'completed'}
          >
            下载
          </Button>
        </Space>
      ),
    },
  ]

  const handleGenerateReport = (type: string) => {
    // 处理报告生成
    console.log(`生成${type}报告`)
  }

  const handleDownloadReport = (id: string) => {
    // 处理报告下载
    console.log(`下载报告 ${id}`)
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>报表统计</Title>
        <Text type="secondary">查看和生成各类统计报表</Text>
      </div>

      {/* 时间筛选 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker value={dateRange} onChange={setDateRange} />
          </Col>
          <Col>
            <Button icon={<FilterOutlined />}>筛选</Button>
          </Col>
          <Col>
            <Button icon={<DownloadOutlined />} type="primary">
              批量导出
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        {/* WPS统计 */}
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="WPS文档"
              value={stats.totalWPS}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div className="mt-3">
              <Text type="secondary" className="text-xs">
                已批准: {stats.approvedWPS} | 待审核: {stats.pendingWPS} | 已拒绝: {stats.rejectedWPS}
              </Text>
              <Progress
                percent={Math.round((stats.approvedWPS / stats.totalWPS) * 100)}
                size="small"
                className="mt-2"
              />
            </div>
          </Card>
        </Col>

        {/* PQR统计 */}
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="PQR记录"
              value={stats.totalPQR}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div className="mt-3">
              <Text type="secondary" className="text-xs">
                已完成: {stats.completedPQR} | 进行中: {stats.inProgressPQR}
              </Text>
              <Progress
                percent={Math.round((stats.completedPQR / stats.totalPQR) * 100)}
                size="small"
                className="mt-2"
                strokeColor="#52c41a"
              />
            </div>
          </Card>
        </Col>

        {/* 质量检验统计 */}
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="质量检验"
              value={stats.totalInspections}
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div className="mt-3">
              <Text type="secondary" className="text-xs">
                通过: {stats.passedInspections} | 失败: {stats.failedInspections}
              </Text>
              <Progress
                percent={Math.round((stats.passedInspections / stats.totalInspections) * 100)}
                size="small"
                className="mt-2"
                strokeColor="#fa8c16"
              />
            </div>
          </Card>
        </Col>

        {/* 项目统计 */}
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={stats.totalProjects}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div className="mt-3">
              <Text type="secondary" className="text-xs">
                已完成: {stats.completedProjects} | 进行中: {stats.inProgressProjects}
              </Text>
              <Progress
                percent={Math.round((stats.completedProjects / stats.totalProjects) * 100)}
                size="small"
                className="mt-2"
                strokeColor="#722ed1"
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card title="快速生成报表" className="mb-6">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Button
              block
              size="large"
              icon={<FileTextOutlined />}
              onClick={() => handleGenerateReport('WPS')}
            >
              WPS统计报表
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button
              block
              size="large"
              icon={<BarChartOutlined />}
              onClick={() => handleGenerateReport('PQR')}
            >
              PQR统计报表
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button
              block
              size="large"
              icon={<PieChartOutlined />}
              onClick={() => handleGenerateReport('Quality')}
            >
              质量检验报表
            </Button>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Button
              block
              size="large"
              icon={<LineChartOutlined />}
              onClick={() => handleGenerateReport('Usage')}
            >
              使用统计报表
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 最近报表 */}
      <Card title="最近报表">
        <Table
          columns={columns}
          dataSource={recentReports}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 系统提示 */}
      <Alert
        message="报表说明"
        description="报表生成可能需要一些时间，请耐心等待。生成完成后会自动在此列表中显示。"
        type="info"
        showIcon
        className="mt-6"
      />
    </div>
  )
}

export default ReportsDashboard