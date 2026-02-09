import React, { useState, useMemo } from 'react'
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
  Tabs,
  Spin,
  Empty,
  Divider,
  Switch,
} from 'antd'
import {
  FileTextOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  DownloadOutlined,
  FilterOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  FireOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select
const { TabPane } = Tabs

interface ReportData {
  wpsData: Array<{
    month: string
    count: number
    approved: number
    pending: number
    rejected: number
  }>
  pqrData: Array<{
    month: string
    total: number
    qualified: number
    failed: number
    pending: number
  }>
  materialUsage: Array<{
    material: string
    usage: number
    cost: number
  }>
  qualityStats: Array<{
    category: string
    passed: number
    failed: number
    rate: number
  }>
  welderPerformance: Array<{
    name: string
    projects: number
    successRate: number
    experience: string
  }>
  equipmentUtilization: Array<{
    equipment: string
    utilization: number
    maintenanceHours: number
    status: 'good' | 'warning' | 'error'
  }>
}

const EnhancedReportsDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'quarter' | 'year'>('month')
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)

  // 模拟数据
  const reportData: ReportData = useMemo(() => ({
    wpsData: [
      { month: '2024-01', count: 45, approved: 38, pending: 5, rejected: 2 },
      { month: '2024-02', count: 52, approved: 44, pending: 6, rejected: 2 },
      { month: '2024-03', count: 48, approved: 41, pending: 5, rejected: 2 },
      { month: '2024-04', count: 58, approved: 50, pending: 6, rejected: 2 },
      { month: '2024-05', count: 62, approved: 54, pending: 6, rejected: 2 },
      { month: '2024-06', count: 55, approved: 47, pending: 6, rejected: 2 },
    ],
    pqrData: [
      { month: '2024-01', total: 12, qualified: 10, failed: 1, pending: 1 },
      { month: '2024-02', total: 15, qualified: 13, failed: 1, pending: 1 },
      { month: '2024-03', total: 14, qualified: 12, failed: 1, pending: 1 },
      { month: '2024-04', total: 18, qualified: 16, failed: 1, pending: 1 },
      { month: '2024-05', total: 20, qualified: 18, failed: 1, pending: 1 },
      { month: '2024-06', total: 17, qualified: 15, failed: 1, pending: 1 },
    ],
    materialUsage: [
      { material: 'E7018焊条', usage: 1250, cost: 18750 },
      { material: 'ER308L焊丝', usage: 890, cost: 26700 },
      { material: 'Q235钢板', usage: 3450, cost: 103500 },
      { material: '304不锈钢', usage: 1200, cost: 72000 },
      { material: '保护气体', usage: 450, cost: 13500 },
    ],
    qualityStats: [
      { category: '外观检查', passed: 342, failed: 18, rate: 95.0 },
      { category: '尺寸检测', passed: 328, failed: 32, rate: 91.1 },
      { category: '无损检测', passed: 315, failed: 45, rate: 87.5 },
      { category: '力学性能', passed: 338, failed: 22, rate: 93.9 },
      { category: '耐压试验', passed: 342, failed: 18, rate: 95.0 },
    ],
    welderPerformance: [
      { name: '张师傅', projects: 45, successRate: 98.2, experience: '高级焊工' },
      { name: '李师傅', projects: 38, successRate: 96.8, experience: '高级焊工' },
      { name: '王师傅', projects: 42, successRate: 94.5, experience: '中级焊工' },
      { name: '刘师傅', projects: 35, successRate: 92.1, experience: '中级焊工' },
      { name: '陈师傅', projects: 28, successRate: 89.3, experience: '初级焊工' },
    ],
    equipmentUtilization: [
      { equipment: '焊机001', utilization: 85, maintenanceHours: 12, status: 'good' },
      { equipment: '焊机002', utilization: 92, maintenanceHours: 8, status: 'good' },
      { equipment: '焊机003', utilization: 78, maintenanceHours: 24, status: 'warning' },
      { equipment: '焊机004', utilization: 65, maintenanceHours: 36, status: 'error' },
      { equipment: '切割机001', utilization: 88, maintenanceHours: 10, status: 'good' },
    ],
  }), [])

  // 统计数据
  const stats = useMemo(() => {
    const totalWPS = reportData.wpsData.reduce((sum, item) => sum + item.count, 0)
    const totalApproved = reportData.wpsData.reduce((sum, item) => sum + item.approved, 0)
    const totalPQR = reportData.pqrData.reduce((sum, item) => sum + item.total, 0)
    const totalQualified = reportData.pqrData.reduce((sum, item) => sum + item.qualified, 0)
    const totalInspections = reportData.qualityStats.reduce((sum, item) => sum + item.passed + item.failed, 0)
    const totalPassed = reportData.qualityStats.reduce((sum, item) => sum + item.passed, 0)
    const totalMaterialCost = reportData.materialUsage.reduce((sum, item) => sum + item.cost, 0)

    return {
      totalWPS,
      approvedWPS: totalApproved,
      pendingWPS: totalWPS - totalApproved,
      totalPQR,
      qualifiedPQR: totalQualified,
      failedPQR: totalPQR - totalQualified,
      totalInspections,
      passedInspections: totalPassed,
      failedInspections: totalInspections - totalPassed,
      totalMaterialCost,
      averageQualityRate: (totalPassed / totalInspections * 100).toFixed(1),
    }
  }, [reportData])

  // 处理刷新
  const handleRefresh = async () => {
    setLoading(true)
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    setLoading(false)
  }

  // 处理导出
  const handleExport = (type: 'excel' | 'pdf' | 'csv') => {
    console.log(`导出${type.toUpperCase()}格式报表`)
  }

  // 简单的图表组件（模拟recharts）
  const SimpleBarChart = ({ data, title }: { data: any[], title: string }) => (
    <Card title={title} size="small">
      <div className="h-48 flex items-end justify-around space-x-2">
        {data.map((item, index) => (
          <div key={index} className="flex flex-col items-center flex-1">
            <div className="text-xs text-center mb-1">{item.value}</div>
            <div
              className="w-full bg-blue-500 rounded-t"
              style={{ height: `${(item.value / Math.max(...data.map(d => d.value))) * 100}%` }}
            />
            <div className="text-xs text-center mt-1">{item.label}</div>
          </div>
        ))}
      </div>
    </Card>
  )

  // 简单的饼图组件
  const SimplePieChart = ({ data, title }: { data: any[], title: string }) => {
    const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1']
    const total = data.reduce((sum, item) => sum + item.value, 0)

    return (
      <Card title={title} size="small">
        <div className="flex justify-center">
          <div className="relative w-32 h-32">
            <div className="absolute inset-0 rounded-full border-8 border-gray-200"></div>
            {data.map((item, index) => {
              const percentage = (item.value / total) * 100
              const angle = (percentage / 100) * 360
              return (
                <div
                  key={index}
                  className="absolute inset-0 rounded-full border-8"
                  style={{
                    borderColor: colors[index % colors.length],
                    clipPath: `polygon(50% 50%, ${50 + 50 * Math.cos((angle - 90) * Math.PI / 180)}% ${50 + 50 * Math.sin((angle - 90) * Math.PI / 180)}%, 50% 0%)`,
                    transform: `rotate(${index === 0 ? 0 : data.slice(0, index).reduce((sum, d) => sum + (d.value / total) * 360, 0)}deg)`,
                  }}
                />
              )
            })}
          </div>
        </div>
        <div className="mt-4 space-y-2">
          {data.map((item, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <div className="flex items-center">
                <div
                  className="w-3 h-3 rounded mr-2"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span>{item.label}</span>
              </div>
              <span className="font-medium">{item.value}</span>
            </div>
          ))}
        </div>
      </Card>
    )
  }

  // WPS趋势图表数据
  const wpsTrendData = reportData.wpsData.map(item => ({
    label: dayjs(item.month).format('MM月'),
    value: item.count,
  }))

  // PQR质量分布数据
  const pqrQualityData = [
    { label: '合格', value: stats.qualifiedPQR },
    { label: '不合格', value: stats.failedPQR },
  ]

  // 材料成本分布数据
  const materialCostData = reportData.materialUsage.map(item => ({
    label: item.material,
    value: item.cost,
  }))

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <Title level={2} className="mb-2">数据统计中心</Title>
            <Text type="secondary">实时监控系统运行状态和业务指标</Text>
          </div>
          <Space>
            <div className="flex items-center">
              <Text className="mr-2">自动刷新</Text>
              <Switch checked={autoRefresh} onChange={setAutoRefresh} />
            </div>
            <Button icon={<DownloadOutlined />} onClick={() => handleExport('excel')}>
              导出报表
            </Button>
            <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleRefresh} loading={loading}>
              刷新数据
            </Button>
          </Space>
        </div>
      </div>

      {/* 时间筛选器 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker value={dateRange} onChange={setDateRange} />
          </Col>
          <Col>
            <Select value={selectedPeriod} onChange={setSelectedPeriod} style={{ width: 120 }}>
              <Option value="month">月度</Option>
              <Option value="quarter">季度</Option>
              <Option value="year">年度</Option>
            </Select>
          </Col>
          <Col>
            <Button icon={<FilterOutlined />}>高级筛选</Button>
          </Col>
        </Row>
      </Card>

      {/* 关键指标 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="WPS文档总数"
              value={stats.totalWPS}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix={
                <span className="text-xs text-green-500">
                  <TrendingUpOutlined /> +12%
                </span>
              }
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                已批准: {stats.approvedWPS} | 待审核: {stats.pendingWPS}
              </Text>
              <Progress
                percent={Math.round((stats.approvedWPS / stats.totalWPS) * 100)}
                size="small"
                className="mt-1"
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="PQR完成率"
              value={Number(stats.averageQualityRate)}
              precision={1}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <span className="text-xs text-green-500">
                  <TrendingUpOutlined /> +5%
                </span>
              }
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                合格: {stats.qualifiedPQR} | 总计: {stats.totalPQR}
              </Text>
              <Progress
                percent={Number(stats.averageQualityRate)}
                size="small"
                className="mt-1"
                strokeColor="#52c41a"
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="质量检验通过率"
              value={Math.round((stats.passedInspections / stats.totalInspections) * 100)}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#fa8c16' }}
              suffix={
                <span className="text-xs text-green-500">
                  <TrendingUpOutlined /> +3%
                </span>
              }
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                通过: {stats.passedInspections} | 失败: {stats.failedInspections}
              </Text>
              <Progress
                percent={Math.round((stats.passedInspections / stats.totalInspections) * 100)}
                size="small"
                className="mt-1"
                strokeColor="#fa8c16"
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="材料总成本"
              value={stats.totalMaterialCost}
              prefix="¥"
              precision={0}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix={
                <span className="text-xs text-red-500">
                  <TrendingDownOutlined /> -8%
                </span>
              }
            />
            <div className="mt-2">
              <Text type="secondary" className="text-xs">
                本月材料消耗成本统计
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Tabs defaultActiveKey="overview" className="mb-6">
        <TabPane tab="数据概览" key="overview">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <SimpleBarChart data={wpsTrendData} title="WPS文档趋势" />
            </Col>
            <Col xs={24} lg={12}>
              <SimplePieChart data={pqrQualityData} title="PQR质量分布" />
            </Col>
            <Col xs={24} lg={12}>
              <SimplePieChart data={materialCostData} title="材料成本分布" />
            </Col>
            <Col xs={24} lg={12}>
              <Card title="质量检查通过率" size="small">
                <div className="space-y-3">
                  {reportData.qualityStats.map((item, index) => (
                    <div key={index}>
                      <div className="flex justify-between items-center mb-1">
                        <Text className="text-sm">{item.category}</Text>
                        <Text className="text-sm font-medium">{item.rate}%</Text>
                      </div>
                      <Progress
                        percent={item.rate}
                        size="small"
                        strokeColor={item.rate >= 95 ? '#52c41a' : item.rate >= 90 ? '#faad14' : '#f5222d'}
                      />
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="人员绩效" key="performance">
          <Card title="焊工绩效排名">
            <Table
              dataSource={reportData.welderPerformance}
              rowKey="name"
              pagination={false}
              size="small"
              columns={[
                {
                  title: '排名',
                  key: 'rank',
                  render: (_, __, index) => (
                    <div className="flex items-center">
                      {index < 3 && <TrophyOutlined className="mr-2" style={{ color: index === 0 ? '#ffd700' : index === 1 ? '#c0c0c0' : '#cd7f32' }} />}
                      <span>{index + 1}</span>
                    </div>
                  ),
                },
                {
                  title: '姓名',
                  dataIndex: 'name',
                  key: 'name',
                },
                {
                  title: '经验等级',
                  dataIndex: 'experience',
                  key: 'experience',
                  render: (level: string) => (
                    <Tag color={level === '高级焊工' ? 'green' : level === '中级焊工' ? 'blue' : 'orange'}>
                      {level}
                    </Tag>
                  ),
                },
                {
                  title: '参与项目',
                  dataIndex: 'projects',
                  key: 'projects',
                },
                {
                  title: '成功率',
                  dataIndex: 'successRate',
                  key: 'successRate',
                  render: (rate: number) => (
                    <div className="flex items-center">
                      <Progress
                        percent={rate}
                        size="small"
                        style={{ width: 80 }}
                        strokeColor={rate >= 95 ? '#52c41a' : rate >= 90 ? '#faad14' : '#f5222d'}
                      />
                      <span className="ml-2 text-sm">{rate}%</span>
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </TabPane>

        <TabPane tab="设备状态" key="equipment">
          <Row gutter={[16, 16]}>
            {reportData.equipmentUtilization.map((equipment, index) => (
              <Col xs={24} sm={12} md={8} key={index}>
                <Card size="small">
                  <div className="flex justify-between items-center mb-3">
                    <Text strong>{equipment.equipment}</Text>
                    <Tag color={equipment.status === 'good' ? 'green' : equipment.status === 'warning' ? 'orange' : 'red'}>
                      {equipment.status === 'good' ? '正常' : equipment.status === 'warning' ? '警告' : '故障'}
                    </Tag>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>利用率</span>
                        <span>{equipment.utilization}%</span>
                      </div>
                      <Progress
                        percent={equipment.utilization}
                        size="small"
                        strokeColor={equipment.utilization >= 80 ? '#52c41a' : equipment.utilization >= 60 ? '#faad14' : '#f5222d'}
                      />
                    </div>
                    <div className="text-sm text-gray-600">
                      维护时长: {equipment.maintenanceHours}小时
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        <TabPane tab="材料分析" key="materials">
          <Card title="材料使用分析">
            <Table
              dataSource={reportData.materialUsage}
              rowKey="material"
              pagination={false}
              size="small"
              columns={[
                {
                  title: '材料名称',
                  dataIndex: 'material',
                  key: 'material',
                },
                {
                  title: '使用量',
                  dataIndex: 'usage',
                  key: 'usage',
                  render: (usage: number) => `${usage.toLocaleString()} 单位`,
                },
                {
                  title: '成本',
                  dataIndex: 'cost',
                  key: 'cost',
                  render: (cost: number) => `¥${cost.toLocaleString()}`,
                },
                {
                  title: '单位成本',
                  key: 'unitCost',
                  render: (_, record) => `¥${(record.cost / record.usage).toFixed(2)}`,
                },
                {
                  title: '成本占比',
                  key: 'percentage',
                  render: (_, record) => {
                    const total = reportData.materialUsage.reduce((sum, item) => sum + item.cost, 0)
                    const percentage = (record.cost / total * 100).toFixed(1)
                    return (
                      <div className="flex items-center">
                        <Progress
                          percent={Number(percentage)}
                          size="small"
                          style={{ width: 60 }}
                        />
                        <span className="ml-2 text-sm">{percentage}%</span>
                      </div>
                    )
                  },
                },
              ]}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 实时监控提示 */}
      <Alert
        message="实时数据监控"
        description="系统正在实时监控各项业务指标，数据每5分钟自动更新一次。如需查看历史趋势，请选择相应的时间范围。"
        type="info"
        showIcon
        icon={<ClockCircleOutlined />}
      />
    </div>
  )
}

export default EnhancedReportsDashboard