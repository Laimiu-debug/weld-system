import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  message,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Select,
  DatePicker,
  InputNumber,
  Descriptions,
  Progress,
  Timeline,
  Badge,
  Tabs,
  Divider,
  TreeSelect,
  Transfer,
  Gantt,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  CalendarOutlined,
  ProjectOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  ToolOutlined,
  FilterOutlined,
  ExportOutlined,
  ScheduleOutlined,
  FlagOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input
const { TreeNode } = TreeSelect

interface ProductionPlan {
  id: string
  planCode: string
  planName: string
  projectId: string
  projectName: string
  productType: string
  productCode: string
  productName: string
  quantity: number
  unit: string
  plannedStartDate: string
  plannedEndDate: string
  actualStartDate?: string
  actualEndDate?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'draft' | 'approved' | 'in_progress' | 'completed' | 'cancelled' | 'delayed'
  progress: number
  assignedTeam: string
  teamLeader: string
  requiredEquipment: string[]
  requiredMaterials: { name: string; quantity: number; unit: string }[]
  qualityStandards: string[]
  estimatedCost: number
  actualCost?: number
  remarks: string
  createdBy: string
  approvedBy?: string
  createdAt: string
  updatedAt: string
}

interface ProductionTask {
  id: string
  planId: string
  taskName: string
  taskType: 'preparation' | 'welding' | 'assembly' | 'inspection' | 'packaging'
  sequence: number
  estimatedDuration: number
  actualDuration?: number
  dependencies: string[]
  assignedTo: string
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  startDate?: string
  endDate?: string
  notes: string
}

interface ProductionStats {
  totalPlans: number
  activePlans: number
  completedPlans: number
  delayedPlans: number
  totalOutput: number
  onTimeDelivery: number
  totalCost: number
}

const ProductionPlanManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [plans, setPlans] = useState<ProductionPlan[]>([])
  const [filteredPlans, setFilteredPlans] = useState<ProductionPlan[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'approve'>('create')
  const [currentPlan, setCurrentPlan] = useState<ProductionPlan | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('plans')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterPriority, setFilterPriority] = useState<string>('all')

  // 模拟数据
  useEffect(() => {
    generateMockData()
  }, [])

  const generateMockData = () => {
    const mockPlans: ProductionPlan[] = [
      {
        id: '1',
        planCode: 'PP-2024-001',
        planName: '压力容器焊接生产计划',
        projectId: 'P001',
        projectName: '化工设备项目A',
        productType: '压力容器',
        productCode: 'PV-2024-001',
        productName: '不锈钢压力容器',
        quantity: 15,
        unit: '台',
        plannedStartDate: '2024-02-01',
        plannedEndDate: '2024-03-15',
        actualStartDate: '2024-02-01',
        priority: 'high',
        status: 'in_progress',
        progress: 65,
        assignedTeam: '焊接一组',
        teamLeader: '张工',
        requiredEquipment: ['数字化逆变焊机', 'CO2焊机', '超声波探伤仪'],
        requiredMaterials: [
          { name: '不锈钢焊条', quantity: 450, unit: 'kg' },
          { name: '保护气体', quantity: 30, unit: '瓶' },
        ],
        qualityStandards: ['GB150-2011', 'ASME VIII'],
        estimatedCost: 850000,
        actualCost: 520000,
        remarks: '重点项目，确保质量和进度',
        createdBy: '生产计划部',
        approvedBy: '李总工',
        createdAt: '2024-01-15',
        updatedAt: '2024-02-20',
      },
      {
        id: '2',
        planCode: 'PP-2024-002',
        planName: '管道焊接生产计划',
        projectId: 'P002',
        projectName: '管道工程项目B',
        productType: '管道',
        productCode: 'PIPE-2024-001',
        productName: '碳钢管道',
        quantity: 1200,
        unit: '米',
        plannedStartDate: '2024-02-10',
        plannedEndDate: '2024-03-30',
        actualStartDate: '2024-02-12',
        priority: 'medium',
        status: 'in_progress',
        progress: 35,
        assignedTeam: '焊接二组',
        teamLeader: '王工',
        requiredEquipment: ['CO2焊机', '管道切割机'],
        requiredMaterials: [
          { name: 'ER50-6焊丝', quantity: 240, unit: 'kg' },
          { name: 'CO2气体', quantity: 50, unit: '瓶' },
        ],
        qualityStandards: ['GB/T 3323-2019'],
        estimatedCost: 680000,
        actualCost: 220000,
        remarks: '按计划进行中',
        createdBy: '生产计划部',
        approvedBy: '李总工',
        createdAt: '2024-01-20',
        updatedAt: '2024-02-20',
      },
      {
        id: '3',
        planCode: 'PP-2024-003',
        planName: '钢结构焊接计划',
        projectId: 'P003',
        projectName: '建筑工程项目C',
        productType: '钢结构',
        productCode: 'STL-2024-001',
        productName: '钢梁结构',
        quantity: 85,
        unit: '吨',
        plannedStartDate: '2024-01-15',
        plannedEndDate: '2024-02-28',
        actualStartDate: '2024-01-18',
        actualEndDate: '2024-02-25',
        priority: 'medium',
        status: 'completed',
        progress: 100,
        assignedTeam: '焊接三组',
        teamLeader: '刘工',
        requiredEquipment: ['电弧焊机', '切割机'],
        requiredMaterials: [
          { name: 'J422焊条', quantity: 850, unit: 'kg' },
        ],
        qualityStandards: ['GB50017-2017'],
        estimatedCost: 450000,
        actualCost: 435000,
        remarks: '项目已完成，质量良好',
        createdBy: '生产计划部',
        approvedBy: '李总工',
        createdAt: '2024-01-05',
        updatedAt: '2024-02-25',
      },
      {
        id: '4',
        planCode: 'PP-2024-004',
        planName: '储罐制造计划',
        projectId: 'P004',
        projectName: '储罐制造项目D',
        productType: '储罐',
        productCode: 'TK-2024-001',
        productName: '立式储罐',
        quantity: 8,
        unit: '台',
        plannedStartDate: '2024-02-20',
        plannedEndDate: '2024-04-30',
        priority: 'urgent',
        status: 'approved',
        progress: 0,
        assignedTeam: '焊接一组',
        teamLeader: '张工',
        requiredEquipment: ['自动化焊机', '卷板机', '探伤设备'],
        requiredMaterials: [
          { name: '钢板', quantity: 120, unit: '吨' },
          { name: '焊材', quantity: 3.5, unit: '吨' },
        ],
        qualityStandards: ['GB50128-2014', 'API 650'],
        estimatedCost: 1200000,
        remarks: '紧急项目，需要优先安排',
        createdBy: '生产计划部',
        approvedBy: '李总工',
        createdAt: '2024-01-25',
        updatedAt: '2024-02-15',
      },
    ]

    setPlans(mockPlans)
    setFilteredPlans(mockPlans)
  }

  // 获取统计数据
  const getProductionStats = (): ProductionStats => {
    const activePlans = plans.filter(plan => ['approved', 'in_progress'].includes(plan.status))
    const completedPlans = plans.filter(plan => plan.status === 'completed')
    const delayedPlans = plans.filter(plan =>
      plan.status === 'delayed' ||
      (dayjs(plan.plannedEndDate).isBefore(dayjs()) && plan.status !== 'completed')
    )
    const totalOutput = plans.reduce((sum, plan) => sum + (plan.status === 'completed' ? plan.quantity : 0), 0)
    const onTimeDelivery = completedPlans.length > 0
      ? Math.round((completedPlans.filter(plan =>
          dayjs(plan.actualEndDate).isSameOrBefore(plan.plannedEndDate)
        ).length / completedPlans.length) * 100)
      : 0
    const totalCost = plans.reduce((sum, plan) => sum + (plan.actualCost || plan.estimatedCost), 0)

    return {
      totalPlans: plans.length,
      activePlans: activePlans.length,
      completedPlans: completedPlans.length,
      delayedPlans: delayedPlans.length,
      totalOutput,
      onTimeDelivery,
      totalCost,
    }
  }

  const stats = getProductionStats()

  // 搜索过滤
  const handleSearch = (value: string) => {
    const filtered = plans.filter(
      plan =>
        plan.planName.toLowerCase().includes(value.toLowerCase()) ||
        plan.planCode.toLowerCase().includes(value.toLowerCase()) ||
        plan.productName.toLowerCase().includes(value.toLowerCase()) ||
        plan.projectName.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredPlans(filtered)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    setFilterStatus(status)
    applyFilters(status, filterPriority)
  }

  // 优先级过滤
  const handlePriorityFilter = (priority: string) => {
    setFilterPriority(priority)
    applyFilters(filterStatus, priority)
  }

  const applyFilters = (status: string, priority: string) => {
    let filtered = plans

    if (status !== 'all') {
      filtered = filtered.filter(plan => plan.status === status)
    }

    if (priority !== 'all') {
      filtered = filtered.filter(plan => plan.priority === priority)
    }

    setFilteredPlans(filtered)
  }

  // 查看详情
  const handleView = (record: ProductionPlan) => {
    setCurrentPlan(record)
    setModalType('view')
    setIsModalVisible(true)
    form.setFieldsValue({
      ...record,
      plannedStartDate: dayjs(record.plannedStartDate),
      plannedEndDate: dayjs(record.plannedEndDate),
      actualStartDate: record.actualStartDate ? dayjs(record.actualStartDate) : undefined,
      actualEndDate: record.actualEndDate ? dayjs(record.actualEndDate) : undefined,
    })
  }

  // 编辑
  const handleEdit = (record: ProductionPlan) => {
    setCurrentPlan(record)
    setModalType('edit')
    setIsModalVisible(true)
    form.setFieldsValue({
      ...record,
      plannedStartDate: dayjs(record.plannedStartDate),
      plannedEndDate: dayjs(record.plannedEndDate),
      actualStartDate: record.actualStartDate ? dayjs(record.actualStartDate) : undefined,
      actualEndDate: record.actualEndDate ? dayjs(record.actualEndDate) : undefined,
    })
  }

  // 审批
  const handleApprove = (record: ProductionPlan) => {
    setCurrentPlan(record)
    setModalType('approve')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 删除
  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个生产计划吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        const newPlans = plans.filter(plan => plan.id !== id)
        setPlans(newPlans)
        setFilteredPlans(newPlans)
        message.success('删除成功')
      },
    })
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      draft: { color: 'default', text: '草稿', icon: <FileTextOutlined /> },
      approved: { color: 'processing', text: '已批准', icon: <CheckCircleOutlined /> },
      in_progress: { color: 'blue', text: '进行中', icon: <ClockCircleOutlined /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      cancelled: { color: 'error', text: '已取消', icon: <ExclamationCircleOutlined /> },
      delayed: { color: 'warning', text: '延期', icon: <ExclamationCircleOutlined /> },
    }
    return statusMap[status as keyof typeof statusMap] || { color: 'default', text: status, icon: null }
  }

  // 获取优先级配置
  const getPriorityConfig = (priority: string) => {
    const priorityMap = {
      low: { color: 'default', text: '低' },
      medium: { color: 'blue', text: '中' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' },
    }
    return priorityMap[priority as keyof typeof priorityMap] || { color: 'default', text: priority }
  }

  // 表格列定义
  const columns: ColumnsType<ProductionPlan> = [
    {
      title: '计划信息',
      key: 'plan',
      width: 200,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.planName}</div>
          <div className="text-sm text-gray-500">{record.planCode}</div>
          <div className="text-xs text-gray-400">
            {getPriorityConfig(record.priority).text} · {record.productType}
          </div>
        </div>
      ),
    },
    {
      title: '项目信息',
      key: 'project',
      width: 180,
      render: (_, record) => (
        <div>
          <div className="text-sm font-medium">{record.projectName}</div>
          <div className="text-xs text-gray-500">{record.productName}</div>
          <div className="text-xs text-gray-400">
            {record.quantity} {record.unit}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = getStatusConfig(status)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '进度',
      key: 'progress',
      width: 120,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.progress}
            size="small"
            status={record.status === 'completed' ? 'success' :
                   record.status === 'delayed' ? 'exception' : 'normal'}
          />
          <div className="text-xs text-gray-500 mt-1">{record.progress}%</div>
        </div>
      ),
    },
    {
      title: '时间计划',
      key: 'schedule',
      width: 150,
      render: (_, record) => {
        const startDate = dayjs(record.plannedStartDate)
        const endDate = dayjs(record.plannedEndDate)
        const totalDays = endDate.diff(startDate, 'day')
        const isDelayed = dayjs().isAfter(endDate) && record.status !== 'completed'

        return (
          <div className={isDelayed ? 'text-red-600' : 'text-gray-600'}>
            <div className="text-xs">{startDate.format('MM-DD')} ~ {endDate.format('MM-DD')}</div>
            <div className="text-xs">
              {totalDays}天
              {isDelayed && <span className="text-red-600 ml-1">(已延期)</span>}
            </div>
          </div>
        )
      },
    },
    {
      title: '负责团队',
      key: 'team',
      width: 120,
      render: (_, record) => (
        <div>
          <div className="text-sm">{record.assignedTeam}</div>
          <div className="text-xs text-gray-500">{record.teamLeader}</div>
        </div>
      ),
    },
    {
      title: '成本',
      key: 'cost',
      width: 100,
      render: (_, record) => {
        const cost = record.actualCost || record.estimatedCost
        const actualCost = record.actualCost
        const estimatedCost = record.estimatedCost

        return (
          <div>
            <div className="text-sm">¥{(cost / 10000).toFixed(1)}万</div>
            {actualCost && (
              <div className="text-xs text-gray-500">
                实际/预计: {(actualCost / estimatedCost * 100).toFixed(0)}%
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<ProjectOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          {record.status === 'draft' && (
            <Tooltip title="审批">
              <Button
                type="text"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => handleApprove(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (modalType === 'approve' && currentPlan) {
        // 审批逻辑
        const updatedPlan = plans.map(plan =>
          plan.id === currentPlan.id
            ? {
                ...plan,
                status: 'approved',
                approvedBy: '当前用户',
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            : plan
        )
        setPlans(updatedPlan)
        setFilteredPlans(updatedPlan)
        message.success('审批成功')
      } else if (modalType === 'create') {
        // 创建计划逻辑
        const newPlan: ProductionPlan = {
          ...values,
          id: Date.now().toString(),
          planCode: `PP-${dayjs().format('YYYY')}-${String(plans.length + 1).padStart(3, '0')}`,
          status: 'draft',
          progress: 0,
          plannedStartDate: values.plannedStartDate.format('YYYY-MM-DD'),
          plannedEndDate: values.plannedEndDate.format('YYYY-MM-DD'),
          actualStartDate: values.actualStartDate ? values.actualStartDate.format('YYYY-MM-DD') : undefined,
          actualEndDate: values.actualEndDate ? values.actualEndDate.format('YYYY-MM-DD') : undefined,
          createdBy: '当前用户',
          createdAt: dayjs().format('YYYY-MM-DD'),
          updatedAt: dayjs().format('YYYY-MM-DD'),
        }
        setPlans([...plans, newPlan])
        setFilteredPlans([...plans, newPlan])
        message.success('创建成功')
      } else if (modalType === 'edit' && currentPlan) {
        // 编辑计划逻辑
        const updatedPlan = plans.map(plan =>
          plan.id === currentPlan.id
            ? {
                ...plan,
                ...values,
                plannedStartDate: values.plannedStartDate.format('YYYY-MM-DD'),
                plannedEndDate: values.plannedEndDate.format('YYYY-MM-DD'),
                actualStartDate: values.actualStartDate ? values.actualStartDate.format('YYYY-MM-DD') : undefined,
                actualEndDate: values.actualEndDate ? values.actualEndDate.format('YYYY-MM-DD') : undefined,
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            : plan
        )
        setPlans(updatedPlan)
        setFilteredPlans(updatedPlan)
        message.success('更新成功')
      }

      setIsModalVisible(false)
      form.resetFields()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">生产计划管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总计划数"
                value={stats.totalPlans}
                valueStyle={{ color: '#1890ff' }}
                prefix={<ScheduleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="进行中"
                value={stats.activePlans}
                valueStyle={{ color: '#52c41a' }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已完成"
                value={stats.completedPlans}
                valueStyle={{ color: '#722ed1' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="延期数量"
                value={stats.delayedPlans}
                valueStyle={{ color: '#f5222d' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总产量"
                value={stats.totalOutput}
                suffix="单位"
                valueStyle={{ color: '#fa8c16' }}
                prefix={<ProjectOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="按时交付率"
                value={stats.onTimeDelivery}
                suffix="%"
                valueStyle={{ color: '#13c2c2' }}
                prefix={<FlagOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* 预警信息 */}
        {stats.delayedPlans > 0 && (
          <Alert
            message={`有 ${stats.delayedPlans} 个生产计划已延期，请立即处理`}
            type="warning"
            showIcon
            closable
            className="mb-4"
          />
        )}
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'plans',
            label: '生产计划',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索计划名称、编号、项目、产品"
                        allowClear
                        enterButton={<SearchOutlined />}
                        style={{ width: 300 }}
                        onSearch={handleSearch}
                        onChange={(e) => !e.target.value && handleSearch('')}
                      />
                      <Select
                        placeholder="状态筛选"
                        style={{ width: 120 }}
                        value={filterStatus}
                        onChange={handleStatusFilter}
                      >
                        <Option value="all">全部状态</Option>
                        <Option value="draft">草稿</Option>
                        <Option value="approved">已批准</Option>
                        <Option value="in_progress">进行中</Option>
                        <Option value="completed">已完成</Option>
                        <Option value="delayed">延期</Option>
                      </Select>
                      <Select
                        placeholder="优先级筛选"
                        style={{ width: 120 }}
                        value={filterPriority}
                        onChange={handlePriorityFilter}
                      >
                        <Option value="all">全部优先级</Option>
                        <Option value="low">低</Option>
                        <Option value="medium">中</Option>
                        <Option value="high">高</Option>
                        <Option value="urgent">紧急</Option>
                      </Select>
                    </Space>

                    <Space>
                      <Button icon={<ExportOutlined />}>导出数据</Button>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => {
                          setModalType('create')
                          setIsModalVisible(true)
                          form.resetFields()
                        }}
                      >
                        新建计划
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 计划列表表格 */}
                <Card>
                  <Table
                    columns={columns}
                    dataSource={filteredPlans}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      total: filteredPlans.length,
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                    }}
                    rowSelection={{
                      selectedRowKeys,
                      onChange: setSelectedRowKeys,
                    }}
                    scroll={{ x: 1400 }}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'gantt',
            label: '甘特图',
            children: (
              <Card>
                <div className="text-center py-8 text-gray-500">
                  <ScheduleOutlined className="text-4xl mb-4" />
                  <div>生产计划甘特图</div>
                  <div className="text-sm">可在此查看项目时间线和依赖关系</div>
                </div>
              </Card>
            ),
          },
          {
            key: 'resources',
            label: '资源调度',
            children: (
              <Card>
                <div className="text-center py-8 text-gray-500">
                  <TeamOutlined className="text-4xl mb-4" />
                  <div>资源调度视图</div>
                  <div className="text-sm">可在此查看人员和设备资源分配情况</div>
                </div>
              </Card>
            ),
          },
        ]}
      />

      {/* 计划详情/编辑/审批模态框 */}
      <Modal
        title={
          modalType === 'view' ? '计划详情' :
          modalType === 'edit' ? '编辑计划' :
          modalType === 'approve' ? '审批计划' :
          '新建计划'
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={
          modalType === 'view' ? [
            <Button key="close" onClick={() => setIsModalVisible(false)}>
              关闭
            </Button>,
          ] : modalType === 'approve' ? [
            <Button key="cancel" onClick={() => setIsModalVisible(false)}>
              取消
            </Button>,
            <Button
              key="approve"
              type="primary"
              loading={loading}
              onClick={handleSubmit}
            >
              批准
            </Button>,
          ] : [
            <Button key="cancel" onClick={() => setIsModalVisible(false)}>
              取消
            </Button>,
            <Button
              key="submit"
              type="primary"
              loading={loading}
              onClick={handleSubmit}
            >
              {modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={modalType === 'view' ? 1000 : 800}
      >
        {modalType === 'view' && currentPlan && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="计划编号">{currentPlan.planCode}</Descriptions.Item>
              <Descriptions.Item label="计划名称">{currentPlan.planName}</Descriptions.Item>
              <Descriptions.Item label="项目名称">{currentPlan.projectName}</Descriptions.Item>
              <Descriptions.Item label="产品名称">{currentPlan.productName}</Descriptions.Item>
              <Descriptions.Item label="产品类型">{currentPlan.productType}</Descriptions.Item>
              <Descriptions.Item label="数量">{currentPlan.quantity} {currentPlan.unit}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusConfig(currentPlan.status).color}>
                  {getStatusConfig(currentPlan.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                <Tag color={getPriorityConfig(currentPlan.priority).color}>
                  {getPriorityConfig(currentPlan.priority).text}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="时间计划" column={2} bordered>
              <Descriptions.Item label="计划开始日期">{currentPlan.plannedStartDate}</Descriptions.Item>
              <Descriptions.Item label="计划结束日期">{currentPlan.plannedEndDate}</Descriptions.Item>
              <Descriptions.Item label="实际开始日期">{currentPlan.actualStartDate || '未开始'}</Descriptions.Item>
              <Descriptions.Item label="实际结束日期">{currentPlan.actualEndDate || '未完成'}</Descriptions.Item>
              <Descriptions.Item label="进度">
                <Progress percent={currentPlan.progress} size="small" />
              </Descriptions.Item>
              <Descriptions.Item label="负责团队">{currentPlan.assignedTeam}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="成本信息" column={2} bordered>
              <Descriptions.Item label="预计成本">¥{currentPlan.estimatedCost.toLocaleString()}</Descriptions.Item>
              <Descriptions.Item label="实际成本">
                {currentPlan.actualCost ? `¥${currentPlan.actualCost.toLocaleString()}` : '未完成'}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="质量标准" column={1} bordered>
              <Descriptions.Item label="标准">
                {currentPlan.qualityStandards.map((standard, index) => (
                  <Tag key={index} color="blue">{standard}</Tag>
                ))}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="备注" column={1} bordered>
              <Descriptions.Item label="备注">{currentPlan.remarks}</Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {(modalType === 'create' || modalType === 'edit') && (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="planName"
                  label="计划名称"
                  rules={[{ required: true, message: '请输入计划名称' }]}
                >
                  <Input placeholder="请输入计划名称" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="projectName"
                  label="项目名称"
                  rules={[{ required: true, message: '请输入项目名称' }]}
                >
                  <Input placeholder="请输入项目名称" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="productType"
                  label="产品类型"
                  rules={[{ required: true, message: '请输入产品类型' }]}
                >
                  <Input placeholder="请输入产品类型" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="productName"
                  label="产品名称"
                  rules={[{ required: true, message: '请输入产品名称' }]}
                >
                  <Input placeholder="请输入产品名称" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="productCode"
                  label="产品编码"
                >
                  <Input placeholder="请输入产品编码" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="quantity"
                  label="数量"
                  rules={[{ required: true, message: '请输入数量' }]}
                >
                  <InputNumber
                    placeholder="请输入数量"
                    style={{ width: '100%' }}
                    min={1}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="unit"
                  label="单位"
                  rules={[{ required: true, message: '请输入单位' }]}
                >
                  <Input placeholder="请输入单位" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="priority"
                  label="优先级"
                  rules={[{ required: true, message: '请选择优先级' }]}
                >
                  <Select placeholder="请选择优先级">
                    <Option value="low">低</Option>
                    <Option value="medium">中</Option>
                    <Option value="high">高</Option>
                    <Option value="urgent">紧急</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="plannedStartDate"
                  label="计划开始日期"
                  rules={[{ required: true, message: '请选择计划开始日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="plannedEndDate"
                  label="计划结束日期"
                  rules={[{ required: true, message: '请选择计划结束日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="assignedTeam"
                  label="负责团队"
                  rules={[{ required: true, message: '请输入负责团队' }]}
                >
                  <Input placeholder="请输入负责团队" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="teamLeader"
                  label="团队负责人"
                  rules={[{ required: true, message: '请输入团队负责人' }]}
                >
                  <Input placeholder="请输入团队负责人" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="estimatedCost"
              label="预计成本"
              rules={[{ required: true, message: '请输入预计成本' }]}
            >
              <InputNumber
                placeholder="请输入预计成本"
                style={{ width: '100%' }}
                min={0}
                precision={2}
                prefix="¥"
              />
            </Form.Item>

            <Form.Item
              name="remarks"
              label="备注"
            >
              <TextArea rows={3} placeholder="请输入备注" />
            </Form.Item>
          </Form>
        )}

        {modalType === 'approve' && currentPlan && (
          <div>
            <Alert
              message="审批确认"
              description={`确定要批准生产计划"${currentPlan.planName}"吗？批准后计划将进入执行阶段。`}
              type="info"
              showIcon
              className="mb-4"
            />
            <Descriptions title="计划信息" column={2} bordered>
              <Descriptions.Item label="计划编号">{currentPlan.planCode}</Descriptions.Item>
              <Descriptions.Item label="计划名称">{currentPlan.planName}</Descriptions.Item>
              <Descriptions.Item label="项目名称">{currentPlan.projectName}</Descriptions.Item>
              <Descriptions.Item label="产品数量">{currentPlan.quantity} {currentPlan.unit}</Descriptions.Item>
              <Descriptions.Item label="计划时间">
                {currentPlan.plannedStartDate} ~ {currentPlan.plannedEndDate}
              </Descriptions.Item>
              <Descriptions.Item label="预计成本">¥{currentPlan.estimatedCost.toLocaleString()}</Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ProductionPlanManagement