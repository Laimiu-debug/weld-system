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
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ToolOutlined,
  CalendarOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  UserOutlined,
  DollarOutlined,
  FilterOutlined,
  ExportOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input

interface MaintenanceTask {
  id: string
  taskId: string
  equipmentId: string
  equipmentName: string
  equipmentCode: string
  taskType: 'routine' | 'preventive' | 'corrective' | 'emergency'
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'overdue'
  assignedTechnician: string
  scheduledDate: string
  estimatedDuration: number
  estimatedCost: number
  actualDuration?: number
  actualCost?: number
  completedDate?: string
  partsRequired: string[]
  partsUsed: string[]
  workNotes: string
  completionNotes?: string
  createdBy: string
  createdAt: string
  updatedAt: string
}

interface MaintenanceStats {
  totalTasks: number
  pendingTasks: number
  inProgressTasks: number
  completedTasks: number
  overdueTasks: number
  totalCost: number
  avgDuration: number
}

const MaintenanceManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<MaintenanceTask[]>([])
  const [filteredTasks, setFilteredTasks] = useState<MaintenanceTask[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'complete'>('create')
  const [currentTask, setCurrentTask] = useState<MaintenanceTask | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('tasks')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')

  // 模拟数据
  useEffect(() => {
    generateMockData()
  }, [])

  const generateMockData = () => {
    const mockTasks: MaintenanceTask[] = [
      {
        id: '1',
        taskId: 'MT-2024-001',
        equipmentId: '1',
        equipmentName: '数字化逆变焊机',
        equipmentCode: 'EQP-2024-001',
        taskType: 'routine',
        title: '季度例行维护',
        description: '清洁设备内部灰尘，检查风扇运转，校准电流参数',
        priority: 'medium',
        status: 'pending',
        assignedTechnician: '张技师',
        scheduledDate: '2024-02-15',
        estimatedDuration: 4,
        estimatedCost: 1200,
        partsRequired: ['清洁剂', '润滑油', '标准件'],
        partsUsed: [],
        workNotes: '按计划进行季度维护',
        createdBy: '系统自动',
        createdAt: '2024-01-15',
        updatedAt: '2024-01-15',
      },
      {
        id: '2',
        equipmentId: '4',
        equipmentName: 'CO2焊机',
        equipmentCode: 'EQP-2024-004',
        taskType: 'preventive',
        title: '送丝机构保养',
        description: '检查送丝轮磨损，更换送丝软管，清理导电嘴',
        priority: 'low',
        status: 'in_progress',
        assignedTechnician: '李技师',
        scheduledDate: '2024-02-10',
        estimatedDuration: 3,
        estimatedCost: 800,
        actualDuration: 2,
        actualCost: 600,
        partsRequired: ['送丝轮', '送丝软管', '导电嘴'],
        partsUsed: ['送丝轮'],
        workNotes: '正在更换送丝轮',
        createdBy: '王管理员',
        createdAt: '2024-01-10',
        updatedAt: '2024-02-10',
      },
      {
        id: '3',
        equipmentId: '3',
        equipmentName: '超声波探伤仪',
        equipmentCode: 'EQP-2024-003',
        taskType: 'corrective',
        title: '紧急故障维修',
        description: '设备无法启动，需要检查电源和主板',
        priority: 'urgent',
        status: 'overdue',
        assignedTechnician: '王技师',
        scheduledDate: '2024-01-25',
        estimatedDuration: 8,
        estimatedCost: 3500,
        partsRequired: ['电源模块', '备用电池'],
        partsUsed: [],
        workNotes: '等待备件到货',
        createdBy: '系统自动',
        createdAt: '2024-01-20',
        updatedAt: '2024-01-26',
      },
      {
        id: '4',
        equipmentId: '2',
        equipmentName: '等离子切割机',
        equipmentCode: 'EQP-2024-002',
        taskType: 'routine',
        title: '月度检查',
        description: '检查气体管路，更换滤芯，校准切割参数',
        priority: 'medium',
        status: 'completed',
        assignedTechnician: '张技师',
        scheduledDate: '2024-02-01',
        estimatedDuration: 2,
        estimatedCost: 500,
        actualDuration: 1.5,
        actualCost: 450,
        completedDate: '2024-02-01',
        partsRequired: ['滤芯', '密封圈'],
        partsUsed: ['滤芯'],
        workNotes: '月度检查完成',
        completionNotes: '设备运行正常，切割质量良好',
        createdBy: '李管理员',
        createdAt: '2024-01-01',
        updatedAt: '2024-02-01',
      },
    ]

    setTasks(mockTasks)
    setFilteredTasks(mockTasks)
  }

  // 获取统计数据
  const getMaintenanceStats = (): MaintenanceStats => {
    const totalCost = tasks.reduce((sum, task) => sum + (task.actualCost || task.estimatedCost), 0)
    const completedTasksWithDuration = tasks.filter(task => task.status === 'completed' && task.actualDuration)
    const avgDuration = completedTasksWithDuration.length > 0
      ? completedTasksWithDuration.reduce((sum, task) => sum + (task.actualDuration || 0), 0) / completedTasksWithDuration.length
      : 0

    return {
      totalTasks: tasks.length,
      pendingTasks: tasks.filter(task => task.status === 'pending').length,
      inProgressTasks: tasks.filter(task => task.status === 'in_progress').length,
      completedTasks: tasks.filter(task => task.status === 'completed').length,
      overdueTasks: tasks.filter(task => task.status === 'overdue').length,
      totalCost,
      avgDuration: Math.round(avgDuration * 10) / 10,
    }
  }

  const stats = getMaintenanceStats()

  // 搜索过滤
  const handleSearch = (value: string) => {
    const filtered = tasks.filter(
      task =>
        task.title.toLowerCase().includes(value.toLowerCase()) ||
        task.equipmentName.toLowerCase().includes(value.toLowerCase()) ||
        task.equipmentCode.toLowerCase().includes(value.toLowerCase()) ||
        task.assignedTechnician.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredTasks(filtered)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    setFilterStatus(status)
    applyFilters(status, filterType)
  }

  // 类型过滤
  const handleTypeFilter = (type: string) => {
    setFilterType(type)
    applyFilters(filterStatus, type)
  }

  const applyFilters = (status: string, type: string) => {
    let filtered = tasks

    if (status !== 'all') {
      filtered = filtered.filter(task => task.status === status)
    }

    if (type !== 'all') {
      filtered = filtered.filter(task => task.taskType === type)
    }

    setFilteredTasks(filtered)
  }

  // 查看详情
  const handleView = (record: MaintenanceTask) => {
    setCurrentTask(record)
    setModalType('view')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 编辑
  const handleEdit = (record: MaintenanceTask) => {
    setCurrentTask(record)
    setModalType('edit')
    setIsModalVisible(true)
    form.setFieldsValue({
      ...record,
      scheduledDate: dayjs(record.scheduledDate),
      completedDate: record.completedDate ? dayjs(record.completedDate) : undefined,
    })
  }

  // 完成任务
  const handleComplete = (record: MaintenanceTask) => {
    setCurrentTask(record)
    setModalType('complete')
    setIsModalVisible(true)
    form.setFieldsValue({
      ...record,
      scheduledDate: dayjs(record.scheduledDate),
      completedDate: dayjs(),
    })
  }

  // 删除
  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个维护任务吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        const newTasks = tasks.filter(task => task.id !== id)
        setTasks(newTasks)
        setFilteredTasks(newTasks)
        message.success('删除成功')
      },
    })
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      pending: { color: 'default', text: '待处理', icon: <ClockCircleOutlined /> },
      in_progress: { color: 'processing', text: '进行中', icon: <ToolOutlined /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      cancelled: { color: 'error', text: '已取消', icon: <ExclamationCircleOutlined /> },
      overdue: { color: 'error', text: '已逾期', icon: <WarningOutlined /> },
    }
    return statusMap[status as keyof typeof statusMap] || { color: 'default', text: status, icon: null }
  }

  // 获取类型配置
  const getTypeConfig = (type: string) => {
    const typeMap = {
      routine: { color: 'blue', text: '例行维护' },
      preventive: { color: 'green', text: '预防性维护' },
      corrective: { color: 'orange', text: '故障维修' },
      emergency: { color: 'red', text: '紧急维修' },
    }
    return typeMap[type as keyof typeof typeMap] || { color: 'default', text: type }
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
  const columns: ColumnsType<MaintenanceTask> = [
    {
      title: '任务信息',
      key: 'task',
      width: 200,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.title}</div>
          <div className="text-sm text-gray-500">{record.taskId}</div>
          <div className="text-xs text-gray-400">
            {getTypeConfig(record.taskType).text} · {getPriorityConfig(record.priority).text}
          </div>
        </div>
      ),
    },
    {
      title: '设备信息',
      key: 'equipment',
      width: 180,
      render: (_, record) => (
        <div>
          <div className="text-sm font-medium">{record.equipmentName}</div>
          <div className="text-xs text-gray-500">{record.equipmentCode}</div>
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
      title: '负责人',
      key: 'technician',
      width: 120,
      render: (_, record) => (
        <div className="flex items-center">
          <UserOutlined className="mr-1" />
          {record.assignedTechnician}
        </div>
      ),
    },
    {
      title: '计划时间',
      dataIndex: 'scheduledDate',
      key: 'scheduledDate',
      width: 120,
      render: (date: string, record) => {
        const daysUntil = dayjs(date).diff(dayjs(), 'day')
        let color = 'text-gray-600'
        if (record.status === 'overdue' || daysUntil < 0) color = 'text-red-600 font-medium'
        else if (daysUntil <= 3) color = 'text-orange-600'
        else if (daysUntil <= 7) color = 'text-blue-600'

        return (
          <div className={color}>
            <div>{dayjs(date).format('MM-DD')}</div>
            <div className="text-xs">
              {record.status === 'overdue' ? '已逾期' :
               daysUntil < 0 ? `${Math.abs(daysUntil)}天前` :
               daysUntil === 0 ? '今天' : `${daysUntil}天后`}
            </div>
          </div>
        )
      },
    },
    {
      title: '成本',
      key: 'cost',
      width: 100,
      render: (_, record) => (
        <div className="flex items-center">
          <DollarOutlined className="mr-1" />
          <span>¥{record.actualCost || record.estimatedCost}</span>
        </div>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      width: 120,
      render: (_, record) => {
        let percent = 0
        let status: 'normal' | 'success' | 'exception' = 'normal'

        if (record.status === 'completed') {
          percent = 100
          status = 'success'
        } else if (record.status === 'in_progress') {
          percent = 50
          status = 'normal'
        } else if (record.status === 'overdue') {
          percent = 75
          status = 'exception'
        }

        return (
          <Progress
            percent={percent}
            size="small"
            status={status}
            format={() => `${percent}%`}
          />
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
              icon={<FileTextOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          {record.status !== 'completed' && (
            <>
              <Tooltip title="编辑">
                <Button
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>
              {record.status === 'in_progress' && (
                <Tooltip title="完成任务">
                  <Button
                    type="text"
                    size="small"
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleComplete(record)}
                  />
                </Tooltip>
              )}
            </>
          )}
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

      if (modalType === 'complete' && currentTask) {
        // 完成任务逻辑
        const updatedTask = tasks.map(task =>
          task.id === currentTask.id
            ? {
                ...task,
                ...values,
                status: 'completed',
                completedDate: values.completedDate.format('YYYY-MM-DD'),
                actualDuration: values.actualDuration,
                actualCost: values.actualCost,
                completionNotes: values.completionNotes,
                partsUsed: values.partsUsed || [],
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            : task
        )
        setTasks(updatedTask)
        setFilteredTasks(updatedTask)
        message.success('任务已完成')
      } else if (modalType === 'create') {
        // 创建任务逻辑
        const newTask: MaintenanceTask = {
          ...values,
          id: Date.now().toString(),
          taskId: `MT-${dayjs().format('YYYY')}-${String(tasks.length + 1).padStart(3, '0')}`,
          status: 'pending',
          scheduledDate: values.scheduledDate.format('YYYY-MM-DD'),
          partsRequired: values.partsRequired || [],
          partsUsed: [],
          workNotes: values.workNotes || '',
          createdBy: '当前用户',
          createdAt: dayjs().format('YYYY-MM-DD'),
          updatedAt: dayjs().format('YYYY-MM-DD'),
        }
        setTasks([...tasks, newTask])
        setFilteredTasks([...tasks, newTask])
        message.success('创建成功')
      } else if (modalType === 'edit' && currentTask) {
        // 编辑任务逻辑
        const updatedTask = tasks.map(task =>
          task.id === currentTask.id
            ? {
                ...task,
                ...values,
                scheduledDate: values.scheduledDate.format('YYYY-MM-DD'),
                completedDate: values.completedDate ? values.completedDate.format('YYYY-MM-DD') : undefined,
                partsRequired: values.partsRequired || [],
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            : task
        )
        setTasks(updatedTask)
        setFilteredTasks(updatedTask)
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
        <h1 className="text-2xl font-bold text-gray-900 mb-4">维护管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总任务数"
                value={stats.totalTasks}
                valueStyle={{ color: '#1890ff' }}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="待处理"
                value={stats.pendingTasks}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="进行中"
                value={stats.inProgressTasks}
                valueStyle={{ color: '#1890ff' }}
                prefix={<ToolOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已完成"
                value={stats.completedTasks}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已逾期"
                value={stats.overdueTasks}
                valueStyle={{ color: '#f5222d' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="总成本"
                value={stats.totalCost}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 预警信息 */}
        {stats.overdueTasks > 0 && (
          <Alert
            message={`有 ${stats.overdueTasks} 个维护任务已逾期，请立即处理`}
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
            key: 'tasks',
            label: '维护任务',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索任务标题、设备、负责人"
                        allowClear
                        enterButton={<SearchOutlined />}
                        style={{ width: 300 }}
                        onSearch={handleSearch}
                        onChange={(e) => !e.target.value && handleSearch('')}
                      />
                      <Select
                        placeholder="类型筛选"
                        style={{ width: 120 }}
                        value={filterType}
                        onChange={handleTypeFilter}
                      >
                        <Option value="all">全部类型</Option>
                        <Option value="routine">例行维护</Option>
                        <Option value="preventive">预防性维护</Option>
                        <Option value="corrective">故障维修</Option>
                        <Option value="emergency">紧急维修</Option>
                      </Select>
                      <Select
                        placeholder="状态筛选"
                        style={{ width: 120 }}
                        value={filterStatus}
                        onChange={handleStatusFilter}
                      >
                        <Option value="all">全部状态</Option>
                        <Option value="pending">待处理</Option>
                        <Option value="in_progress">进行中</Option>
                        <Option value="completed">已完成</Option>
                        <Option value="overdue">已逾期</Option>
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
                        新建任务
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 任务列表表格 */}
                <Card>
                  <Table
                    columns={columns}
                    dataSource={filteredTasks}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      total: filteredTasks.length,
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                    }}
                    rowSelection={{
                      selectedRowKeys,
                      onChange: setSelectedRowKeys,
                    }}
                    scroll={{ x: 1200 }}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'schedule',
            label: '维护日历',
            children: (
              <Card>
                <div className="text-center py-8 text-gray-500">
                  <CalendarOutlined className="text-4xl mb-4" />
                  <div>维护日历视图</div>
                  <div className="text-sm">可在此查看按日期排列的维护计划</div>
                </div>
              </Card>
            ),
          },
        ]}
      />

      {/* 任务详情/编辑/完成模态框 */}
      <Modal
        title={
          modalType === 'view' ? '任务详情' :
          modalType === 'edit' ? '编辑任务' :
          modalType === 'complete' ? '完成任务' :
          '新建任务'
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={
          modalType === 'view' ? [
            <Button key="close" onClick={() => setIsModalVisible(false)}>
              关闭
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
              {modalType === 'complete' ? '完成任务' :
               modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={modalType === 'view' ? 800 : 600}
      >
        {modalType === 'view' && currentTask && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="任务编号">{currentTask.taskId}</Descriptions.Item>
              <Descriptions.Item label="任务标题">{currentTask.title}</Descriptions.Item>
              <Descriptions.Item label="任务类型">
                <Tag color={getTypeConfig(currentTask.taskType).color}>
                  {getTypeConfig(currentTask.taskType).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                <Tag color={getPriorityConfig(currentTask.priority).color}>
                  {getPriorityConfig(currentTask.priority).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusConfig(currentTask.status).color}>
                  {getStatusConfig(currentTask.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="负责人">{currentTask.assignedTechnician}</Descriptions.Item>
              <Descriptions.Item label="计划日期">{currentTask.scheduledDate}</Descriptions.Item>
              <Descriptions.Item label="完成日期">{currentTask.completedDate || '未完成'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="任务描述" column={1} bordered>
              <Descriptions.Item label="描述">{currentTask.description}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="成本信息" column={2} bordered>
              <Descriptions.Item label="预计成本">¥{currentTask.estimatedCost}</Descriptions.Item>
              <Descriptions.Item label="实际成本">¥{currentTask.actualCost || '未完成'}</Descriptions.Item>
              <Descriptions.Item label="预计时长">{currentTask.estimatedDuration}小时</Descriptions.Item>
              <Descriptions.Item label="实际时长">{currentTask.actualDuration ? `${currentTask.actualDuration}小时` : '未完成'}</Descriptions.Item>
            </Descriptions>

            {currentTask.completionNotes && (
              <>
                <Divider />
                <Descriptions title="完成备注" column={1} bordered>
                  <Descriptions.Item label="备注">{currentTask.completionNotes}</Descriptions.Item>
                </Descriptions>
              </>
            )}
          </div>
        )}

        {(modalType === 'create' || modalType === 'edit' || modalType === 'complete') && (
          <Form form={form} layout="vertical">
            <Form.Item
              name="title"
              label="任务标题"
              rules={[{ required: true, message: '请输入任务标题' }]}
            >
              <Input placeholder="请输入任务标题" />
            </Form.Item>

            <Form.Item
              name="description"
              label="任务描述"
              rules={[{ required: true, message: '请输入任务描述' }]}
            >
              <TextArea rows={3} placeholder="请详细描述维护内容" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="taskType"
                  label="任务类型"
                  rules={[{ required: true, message: '请选择任务类型' }]}
                >
                  <Select placeholder="请选择任务类型">
                    <Option value="routine">例行维护</Option>
                    <Option value="preventive">预防性维护</Option>
                    <Option value="corrective">故障维修</Option>
                    <Option value="emergency">紧急维修</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
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
                  name="assignedTechnician"
                  label="负责人"
                  rules={[{ required: true, message: '请输入负责人' }]}
                >
                  <Input placeholder="请输入负责人姓名" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="scheduledDate"
                  label="计划日期"
                  rules={[{ required: true, message: '请选择计划日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="estimatedDuration"
                  label="预计时长（小时）"
                  rules={[{ required: true, message: '请输入预计时长' }]}
                >
                  <InputNumber
                    placeholder="请输入预计时长"
                    style={{ width: '100%' }}
                    min={0.5}
                    step={0.5}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
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
              </Col>
            </Row>

            {modalType === 'complete' && (
              <>
                <Divider />
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="actualDuration"
                      label="实际时长（小时）"
                      rules={[{ required: true, message: '请输入实际时长' }]}
                    >
                      <InputNumber
                        placeholder="请输入实际时长"
                        style={{ width: '100%' }}
                        min={0.5}
                        step={0.5}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="actualCost"
                      label="实际成本"
                      rules={[{ required: true, message: '请输入实际成本' }]}
                    >
                      <InputNumber
                        placeholder="请输入实际成本"
                        style={{ width: '100%' }}
                        min={0}
                        precision={2}
                        prefix="¥"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  name="completedDate"
                  label="完成日期"
                  rules={[{ required: true, message: '请选择完成日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>

                <Form.Item
                  name="completionNotes"
                  label="完成备注"
                >
                  <TextArea rows={3} placeholder="请输入完成备注" />
                </Form.Item>
              </>
            )}

            <Form.Item
              name="workNotes"
              label="工作备注"
            >
              <TextArea rows={2} placeholder="请输入工作备注" />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default MaintenanceManagement