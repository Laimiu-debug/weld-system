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
import reportsService from '@/services/reports'
import { equipmentService } from '@/services/equipment'
import wpsService from '@/services/wps'
import { downloadCsv } from '@/utils/csv'
import ListPageHeader from '@/components/ListPageHeader'

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

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsResp, usageResp, wpsList] = await Promise.all([
        reportsService.getStatistics(dateRange[0].format('YYYY-MM-DD'), dateRange[1].format('YYYY-MM-DD')),
        equipmentService.getUsageRecords({ skip: 0, limit: 100 }),
        wpsService.getWPSList({ skip: 0, limit: 50 }),
      ])
      const stats = (statsResp as any)?.data?.data || (statsResp as any)?.data || {}
      const usageItems = usageResp.success ? (usageResp.data.items || []) : []
      const wpsItems = Array.isArray(wpsList) ? wpsList : []

      setUsageData([
        ...wpsItems.slice(0, 20).map((item) => ({
          id: `wps-${item.id}`,
          category: 'wps' as const,
          action: '更新WPS',
          user: item.company || '-',
          timestamp: item.updated_at || item.created_at,
          details: `${item.wps_number} ${item.title}`,
        })),
        ...usageItems.map((item) => ({
          id: `eq-${item.id}`,
          category: 'equipment' as const,
          action: '设备使用',
          user: String(item.operator_id || '-'),
          timestamp: item.start_time || item.usage_date || item.created_at || '',
          details: `${item.equipment_name} (${item.equipment_code}) ${item.duration_hours || 0}小时`,
        })),
      ])
      setUserUsage([
        {
          userId: 'workspace',
          userName: '当前工作区',
          department: '-',
          wpsCount: stats.wps?.total || wpsItems.length,
          pqrCount: stats.pqr?.total || 0,
          qualityCount: stats.quality?.total || 0,
          lastActive: dayjs().format('YYYY-MM-DD'),
        },
      ])
      setEquipmentUsage(
        usageItems.map((item) => ({
          id: String(item.id),
          equipmentName: item.equipment_name,
          usageHours: item.duration_hours || 0,
          utilizationRate: 0,
          maintenanceHours: 0,
          projectsCompleted: 0,
          efficiency: 0,
        })),
      )
    } catch {
      setUsageData([])
      setUserUsage([])
      setEquipmentUsage([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  // 计算统计数据
  const getStatistics = () => {
    const totalUsage = usageData.length
    const wpsUsage = usageData.filter(item => item.category === 'wps').length
    const pqrUsage = usageData.filter(item => item.category === 'pqr').length
    const qualityUsage = usageData.filter(item => item.category === 'quality').length
    const equipmentEventCount = usageData.filter(item => item.category === 'equipment').length
    const materialsUsage = usageData.filter(item => item.category === 'materials').length

    const avgUtilization = equipmentUsage.length > 0
      ? Math.round(equipmentUsage.reduce((sum, item) => sum + item.utilizationRate, 0) / equipmentUsage.length)
      : 0

    const totalUsageHours = equipmentUsage.reduce((sum, item) => sum + item.usageHours, 0)
    const avgEfficiency = equipmentUsage.length > 0
      ? Math.round(equipmentUsage.reduce((sum, item) => sum + item.efficiency, 0) / equipmentUsage.length)
      : 0

    return {
      totalUsage,
      wpsUsage,
      pqrUsage,
      qualityUsage,
      equipmentUsage: equipmentEventCount,
      materialsUsage,
      avgUtilization,
      totalUsageHours,
      avgEfficiency,
    }
  }

  const stats = getStatistics()

  // 处理筛选
  const handleFilter = () => {
    void loadData()
  }

  const handleExport = () => {
    downloadCsv(
      `usage-report-${dayjs().format('YYYYMMDD')}.csv`,
      ['时间', '类别', '操作', '用户', '详情'],
      usageData.map((item) => [item.timestamp, item.category, item.action, item.user, item.details]),
    )
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
    <div className="list-page">
      <ListPageHeader
        title="使用统计"
        description="系统使用情况与操作统计分析"
      />

      {/* 筛选条件 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker value={dateRange} onChange={(dates) => { if (dates?.[0] && dates[1]) setDateRange([dates[0], dates[1]]) }} />
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
              <Button icon={<DownloadOutlined />} onClick={handleExport}>
                导出CSV
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
        description="导出为 CSV，可用 Excel 打开。数据包含当前筛选范围内的使用记录。"
        type="info"
        showIcon
      />
    </div>
  )
}

export default UsageReport
