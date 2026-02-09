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
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DownloadOutlined,
  FilterOutlined,
  UserOutlined,
  CalendarOutlined,
  ToolOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface UsageData {
  id: string
  category: 'wps' | 'pqr' | 'equipment' | 'materials' | 'quality'
  action: string
  user: string
  timestamp: string
  details: string
}

interface UserUsage {
  userId: string
  userName: string
  department: string
  wpsCount: number
  pqrCount: number
  qualityCount: number
  lastActive: string
}

interface EquipmentUsage {
  id: string
  equipmentName: string
  usageHours: number
  utilizationRate: number
  maintenanceHours: number
  projectsCompleted: number
  efficiency: number
}

const UsageReport: React.FC = () => {
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ])
  const [loading, setLoading] = useState(false)
  const [usageData, setUsageData] = useState<UsageData[]>([])
  const [userUsage, setUserUsage] = useState<UserUsage[]>([])
  const [equipmentUsage, setEquipmentUsage] = useState<EquipmentUsage[]>([])

  // 模拟数据
  useEffect(() => {
    const mockUsageData: UsageData[] = [
      {
        id: '1',
        category: 'wps',
        action: '创建WPS',
        user: '张工程师',
        timestamp: '2024-01-20 14:30:00',
        details: '创建了WPS-2024-005 储罐罐底焊接工艺',
      },
      {
        id: '2',
        category: 'quality',
        action: '质量检验',
        user: '李检验员',
        timestamp: '2024-01-20 15:45:00',
        details: '完成了WPS-2024-002 焊缝外观检验',
      },
      {
        id: '3',
        category: 'equipment',
        action: '设备使用',
        user: '王师傅',
        timestamp: '2024-01-20 16:20:00',
        details: '使用了焊机EQP-2024-001，工时3.5小时',
      },
      {
        id: '4',
        category: 'pqr',
        action: 'PQR测试',
        user: '赵工程师',
        timestamp: '2024-01-20 17:10:00',
        details: '完成PQR-2024-002 拉伸试验',
      },
      {
        id: '5',
        category: 'materials',
        action: '材料出库',
        user: '钱管理员',
        timestamp: '2024-01-20 18:00:00',
        details: '出库E7018焊丝5kg',
      },
    ]

    const mockUserUsage: UserUsage[] = [
      {
        userId: '1',
        userName: '张工程师',
        department: '技术部',
        wpsCount: 12,
        pqrCount: 8,
        qualityCount: 15,
        lastActive: '2024-01-20 18:30:00',
      },
      {
        userId: '2',
        userName: '李检验员',
        department: '质量部',
        wpsCount: 3,
        pqrCount: 2,
        qualityCount: 45,
        lastActive: '2024-01-20 17:45:00',
      },
      {
        userId: '3',
        userName: '王师傅',
        department: '生产一部',
        wpsCount: 0,
        pqrCount: 0,
        qualityCount: 8,
        lastActive: '2024-01-20 16:20:00',
      },
    ]

    const mockEquipmentUsage: EquipmentUsage[] = [
      {
        id: '1',
        equipmentName: '数字化逆变焊机',
        usageHours: 1250,
        utilizationRate: 85,
        maintenanceHours: 24,
        projectsCompleted: 15,
        efficiency: 92,
      },
      {
        id: '2',
        equipmentName: '等离子切割机',
        usageHours: 890,
        utilizationRate: 65,
        maintenanceHours: 72,
        projectsCompleted: 10,
        efficiency: 88,
      },
      {
        id: '3',
        equipmentName: '超声波探伤仪',
        usageHours: 560,
        utilizationRate: 45,
        maintenanceHours: 120,
        projectsCompleted: 8,
        efficiency: 75,
      },
    ]

    setUsageData(mockUsageData)
    setUserUsage(mockUserUsage)
    setEquipmentUsage(mockEquipmentUsage)
  }, [])

  // 计算统计数据
  const getStatistics = () => {
    const totalUsage = usageData.length
    const wpsUsage = usageData.filter(item => item.category === 'wps').length
    const pqrUsage = usageData.filter(item => item.category === 'pqr').length
    const qualityUsage = usageData.filter(item => item.category === 'quality').length
    const equipmentUsage = usageData.filter(item => item.category === 'equipment').length
    const materialsUsage = usageData.filter(item => item.category === 'materials').length

    const avgUtilization = equipmentUsageData.length > 0
      ? Math.round(equipmentUsageData.reduce((sum, item) => sum + item.utilizationRate, 0) / equipmentUsageData.length)
      : 0

    const totalUsageHours = equipmentUsageData.reduce((sum, item) => sum + item.usageHours, 0)
    const avgEfficiency = equipmentUsageData.length > 0
      ? Math.round(equipmentUsageData.reduce((sum, item) => sum + item.efficiency, 0) / equipmentUsageData.length)
      : 0

    return {
      totalUsage,
      wpsUsage,
      pqrUsage,
      qualityUsage,
      equipmentUsage,
      materialsUsage,
      avgUtilization,
      totalUsageHours,
      avgEfficiency,
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

  const usageColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => (
        <Space>
          <CalendarOutlined />
          <Text>{dayjs(time).format('MM-DD HH:mm')}</Text>
        </Space>
      ),
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
      render: (user: string) => (
        <Space>
          <UserOutlined />
          <Text>{user}</Text>
        </Space>
      ),
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const categoryConfig: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
          wps: { color: 'blue', text: 'WPS', icon: <FileTextOutlined /> },
          pqr: { color: 'green', text: 'PQR', icon: <FileTextOutlined /> },
          quality: { color: 'orange', text: '质量', icon: <FileTextOutlined /> },
          equipment: { color: 'purple', text: '设备', icon: <ToolOutlined /> },
          materials: { color: 'cyan', text: '材料', icon: <FileTextOutlined /> },
        }
        const config = categoryConfig[category] || categoryConfig.wps
        return <Tag color={config.color} icon={config.icon}>{config.text}</Tag>
      },
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      render: (details: string) => <Text>{details}</Text>,
    },
  ]

  const userColumns = [
    {
      title: '用户',
      dataIndex: 'userName',
      key: 'userName',
      render: (name: string) => (
        <Space>
          <UserOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (dept: string) => <Tag color="blue">{dept}</Tag>,
    },
    {
      title: 'WPS使用',
      dataIndex: 'wpsCount',
      key: 'wpsCount',
      render: (count: number) => <Text>{count} 次</Text>,
    },
    {
      title: 'PQR使用',
      dataIndex: 'pqrCount',
      key: 'pqrCount',
      render: (count: number) => <Text>{count} 次</Text>,
    },
    {
      title: '质量检验',
      dataIndex: 'qualityCount',
      key: 'qualityCount',
      render: (count: number) => <Text>{count} 次</Text>,
    },
    {
      title: '最后活跃',
      dataIndex: 'lastActive',
      key: 'lastActive',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm'),
    },
  ]

  const equipmentColumns = [
    {
      title: '设备名称',
      dataIndex: 'equipmentName',
      key: 'equipmentName',
      render: (name: string) => (
        <Space>
          <ToolOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '使用工时',
      dataIndex: 'usageHours',
      key: 'usageHours',
      render: (hours: number) => <Text>{hours} 小时</Text>,
    },
    {
      title: '使用率',
      dataIndex: 'utilizationRate',
      key: 'utilizationRate',
      render: (rate: number) => (
        <Space>
          <Text>{rate}%</Text>
          <Progress percent={rate} size="small" style={{ width: 80 }} />
        </Space>
      ),
    },
    {
      title: '效率',
      dataIndex: 'efficiency',
      key: 'efficiency',
      render: (efficiency: number) => (
        <Space>
          <Text>{efficiency}%</Text>
          <Progress
            percent={efficiency}
            size="small"
            status={efficiency >= 90 ? 'success' : efficiency >= 70 ? 'normal' : 'exception'}
            style={{ width: 80 }}
          />
        </Space>
      ),
    },
    {
      title: '完成项目',
      dataIndex: 'projectsCompleted',
      key: 'projectsCompleted',
      render: (count: number) => <Text>{count} 个</Text>,
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>使用统计报表</Title>
        <Text type="secondary">系统使用情况和统计分析报告</Text>
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
            <Select placeholder="类别筛选" style={{ width: 120 }} allowClear>
              <Option value="wps">WPS</Option>
              <Option value="pqr">PQR</Option>
              <Option value="quality">质量检验</Option>
              <Option value="equipment">设备使用</Option>
              <Option value="materials">材料管理</Option>
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
              title="总操作次数"
              value={stats.totalUsage}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="设备总工时"
              value={stats.totalUsageHours}
              suffix="小时"
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均使用率"
              value={stats.avgUtilization}
              suffix="%"
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均效率"
              value={stats.avgEfficiency}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 分类统计 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card title="模块使用分布">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div className="flex justify-between">
                <Text>WPS</Text>
                <Tag color="blue">{stats.wpsUsage}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>PQR</Text>
                <Tag color="green">{stats.pqrUsage}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>质量检验</Text>
                <Tag color="orange">{stats.qualityUsage}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>设备使用</Text>
                <Tag color="purple">{stats.equipmentUsage}</Tag>
              </div>
              <div className="flex justify-between">
                <Text>材料管理</Text>
                <Tag color="cyan">{stats.materialsUsage}</Tag>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card title="用户活跃度 TOP 5">
            <Space direction="vertical" style={{ width: '100%' }}>
              {userUsage.slice(0, 5).map((user) => (
                <div key={user.userId} className="flex justify-between">
                  <Text>{user.userName}</Text>
                  <Tag color="blue">{user.wpsCount + user.pqrCount + user.qualityCount} 次操作</Tag>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 设备使用统计 */}
      <Card title="设备使用统计" className="mb-6">
        <Table
          columns={equipmentColumns}
          dataSource={equipmentUsage}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>

      {/* 用户使用统计 */}
      <Card title="用户使用统计" className="mb-6">
        <Table
          columns={userColumns}
          dataSource={userUsage}
          rowKey="userId"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 使用记录 */}
      <Card title="详细使用记录">
        <Table
          columns={usageColumns}
          dataSource={usageData}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
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
        description="Excel格式适合数据分析，PDF格式适合打印和分享。导出的数据将包含完整的使用统计、用户活跃度和设备效率信息。"
        type="info"
        showIcon
      />
    </div>
  )
}

export default UsageReport