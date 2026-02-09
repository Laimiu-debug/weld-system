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
  Steps,
  Avatar,
  Popconfirm,
  Transfer,
  TreeSelect,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  FileTextOutlined,
  SendOutlined,
  SettingOutlined,
  BranchesOutlined,
  HistoryOutlined,
  EyeOutlined,
  ApproveOutlined,
  StopOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input
const { Step } = Steps

interface WorkflowDefinition {
  id: string
  name: string
  description: string
  category: string
  triggerType: 'manual' | 'automatic' | 'scheduled'
  triggerConditions: string[]
  steps: WorkflowStep[]
  isActive: boolean
  createdBy: string
  createdAt: string
  updatedAt: string
}

interface WorkflowStep {
  id: string
  name: string
  type: 'approval' | 'notification' | 'task' | 'condition' | 'parallel' | 'end'
  assigneeType: 'user' | 'role' | 'department' | 'dynamic'
  assignees: string[]
  conditions: string[]
  actions: string[]
  timeLimit?: number
  order: number
}

interface WorkflowInstance {
  id: string
  workflowId: string
  workflowName: string
  title: string
  description: string
  initiator: string
  initiatorId: string
  currentStep: number
  currentStepName: string
  status: 'pending' | 'in_progress' | 'completed' | 'rejected' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  formData: Record<string, any>
  attachments: string[]
  history: WorkflowHistory[]
  createdAt: string
  updatedAt: string
  completedAt?: string
}

interface WorkflowHistory {
  id: string
  stepId: string
  stepName: string
  action: 'submit' | 'approve' | 'reject' | 'return' | 'cancel'
  actor: string
  actorId: string
  comment: string
  timestamp: string
  attachments?: string[]
}

interface Task {
  id: string
  instanceId: string
  instanceTitle: string
  stepId: string
  stepName: string
  assignee: string
  assigneeId: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  dueDate: string
  formData: Record<string, any>
  createdAt: string
  updatedAt: string
  completedAt?: string
}

const WorkflowManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [workflowDefinitions, setWorkflowDefinitions] = useState<WorkflowDefinition[]>([])
  const [workflowInstances, setWorkflowInstances] = useState<WorkflowInstance[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [filteredInstances, setFilteredInstances] = useState<WorkflowInstance[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'start' | 'approve'>('create')
  const [currentItem, setCurrentItem] = useState<any>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('instances')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  // 模拟数据
  useEffect(() => {
    generateMockData()
  }, [])

  const generateMockData = () => {
    const mockWorkflowDefinitions: WorkflowDefinition[] = [
      {
        id: '1',
        name: 'WPS审批流程',
        description: '焊接工艺规范的审批流程',
        category: '技术审批',
        triggerType: 'manual',
        triggerConditions: ['WPS创建'],
        steps: [
          {
            id: '1',
            name: '提交申请',
            type: 'task',
            assigneeType: 'user',
            assignees: ['applicant'],
            conditions: [],
            actions: ['填写WPS信息'],
            order: 1,
          },
          {
            id: '2',
            name: '技术审核',
            type: 'approval',
            assigneeType: 'role',
            assignees: ['technical_engineer'],
            conditions: [],
            actions: ['审核技术参数'],
            timeLimit: 48,
            order: 2,
          },
          {
            id: '3',
            name: '质量审核',
            type: 'approval',
            assigneeType: 'role',
            assignees: ['quality_engineer'],
            conditions: [],
            actions: ['审核质量要求'],
            timeLimit: 48,
            order: 3,
          },
          {
            id: '4',
            name: '最终批准',
            type: 'approval',
            assigneeType: 'user',
            assignees: ['chief_engineer'],
            conditions: [],
            actions: ['最终批准'],
            timeLimit: 24,
            order: 4,
          },
        ],
        isActive: true,
        createdBy: '系统管理员',
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      },
      {
        id: '2',
        name: '设备采购审批',
        description: '设备采购申请的审批流程',
        category: '采购审批',
        triggerType: 'manual',
        triggerConditions: ['设备采购申请'],
        steps: [
          {
            id: '1',
            name: '提交申请',
            type: 'task',
            assigneeType: 'user',
            assignees: ['applicant'],
            conditions: [],
            actions: ['填写采购需求'],
            order: 1,
          },
          {
            id: '2',
            name: '部门审核',
            type: 'approval',
            assigneeType: 'department',
            assignees: ['department_head'],
            conditions: [],
            actions: ['审核需求合理性'],
            timeLimit: 72,
            order: 2,
          },
          {
            id: '3',
            name: '财务审核',
            type: 'approval',
            assigneeType: 'role',
            assignees: ['finance'],
            conditions: [],
            actions: ['审核预算'],
            timeLimit: 48,
            order: 3,
          },
        ],
        isActive: true,
        createdBy: '采购部',
        createdAt: '2024-01-15',
        updatedAt: '2024-01-15',
      },
    ]

    const mockWorkflowInstances: WorkflowInstance[] = [
      {
        id: '1',
        workflowId: '1',
        workflowName: 'WPS审批流程',
        title: '压力容器焊接WPS审批',
        description: '不锈钢压力容器焊接工艺规范审批',
        initiator: '张工程师',
        initiatorId: 'user001',
        currentStep: 2,
        currentStepName: '技术审核',
        status: 'in_progress',
        priority: 'high',
        formData: {
          wpsCode: 'WPS-2024-001',
          material: 'S30408',
          thickness: '12mm',
          process: 'GTAW+SMAW',
        },
        attachments: ['wps_document.pdf', 'drawing.dwg'],
        history: [
          {
            id: '1',
            stepId: '1',
            stepName: '提交申请',
            action: 'submit',
            actor: '张工程师',
            actorId: 'user001',
            comment: '提交WPS审批申请',
            timestamp: '2024-02-15 09:00:00',
          },
        ],
        createdAt: '2024-02-15 09:00:00',
        updatedAt: '2024-02-15 10:30:00',
      },
      {
        id: '2',
        workflowId: '2',
        workflowName: '设备采购审批',
        title: '数字化焊机采购申请',
        description: '采购一台数字化逆变焊机',
        initiator: '李主任',
        initiatorId: 'user002',
        currentStep: 1,
        currentStepName: '提交申请',
        status: 'pending',
        priority: 'medium',
        formData: {
          equipmentName: '数字化逆变焊机',
          model: 'YD-400KR2',
          quantity: 1,
          budget: 35000,
        },
        attachments: ['quotation.pdf'],
        history: [],
        createdAt: '2024-02-16 14:00:00',
        updatedAt: '2024-02-16 14:00:00',
      },
    ]

    const mockTasks: Task[] = [
      {
        id: '1',
        instanceId: '1',
        instanceTitle: '压力容器焊接WPS审批',
        stepId: '2',
        stepName: '技术审核',
        assignee: '王工',
        assigneeId: 'user003',
        status: 'pending',
        priority: 'high',
        dueDate: '2024-02-17',
        formData: {},
        createdAt: '2024-02-15 10:30:00',
        updatedAt: '2024-02-15 10:30:00',
      },
      {
        id: '2',
        instanceId: '2',
        instanceTitle: '数字化焊机采购申请',
        stepId: '1',
        stepName: '提交申请',
        assignee: '李主任',
        assigneeId: 'user002',
        status: 'in_progress',
        priority: 'medium',
        dueDate: '2024-02-20',
        formData: {},
        createdAt: '2024-02-16 14:00:00',
        updatedAt: '2024-02-16 15:30:00',
      },
    ]

    setWorkflowDefinitions(mockWorkflowDefinitions)
    setWorkflowInstances(mockWorkflowInstances)
    setFilteredInstances(mockWorkflowInstances)
    setTasks(mockTasks)
  }

  // 获取统计数据
  const getWorkflowStats = () => {
    const pendingCount = workflowInstances.filter(instance => instance.status === 'pending').length
    const inProgressCount = workflowInstances.filter(instance => instance.status === 'in_progress').length
    const completedCount = workflowInstances.filter(instance => instance.status === 'completed').length
    const myTasksCount = tasks.filter(task => task.assignee === '当前用户' && task.status === 'pending').length
    const overdueTasksCount = tasks.filter(task =>
      dayjs(task.dueDate).isBefore(dayjs()) && task.status !== 'completed'
    ).length

    return {
      totalInstances: workflowInstances.length,
      pendingCount,
      inProgressCount,
      completedCount,
      myTasksCount,
      overdueTasksCount,
    }
  }

  const stats = getWorkflowStats()

  // 搜索过滤
  const handleSearch = (value: string) => {
    const filtered = workflowInstances.filter(
      instance =>
        instance.title.toLowerCase().includes(value.toLowerCase()) ||
        instance.workflowName.toLowerCase().includes(value.toLowerCase()) ||
        instance.initiator.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredInstances(filtered)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    setFilterStatus(status)
    if (status === 'all') {
      setFilteredInstances(workflowInstances)
    } else {
      const filtered = workflowInstances.filter(instance => instance.status === status)
      setFilteredInstances(filtered)
    }
  }

  // 查看详情
  const handleView = (record: WorkflowInstance) => {
    setCurrentItem(record)
    setModalType('view')
    setIsModalVisible(true)
  }

  // 审批
  const handleApprove = (record: WorkflowInstance) => {
    setCurrentItem(record)
    setModalType('approve')
    setIsModalVisible(true)
    form.resetFields()
  }

  // 删除
  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个流程实例吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        const newInstances = workflowInstances.filter(instance => instance.id !== id)
        setWorkflowInstances(newInstances)
        setFilteredInstances(newInstances)
        message.success('删除成功')
      },
    })
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      pending: { color: 'default', text: '待处理', icon: <ClockCircleOutlined /> },
      in_progress: { color: 'processing', text: '进行中', icon: <BranchesOutlined /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      rejected: { color: 'error', text: '已拒绝', icon: <CloseCircleOutlined /> },
      cancelled: { color: 'warning', text: '已取消', icon: <StopOutlined /> },
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

  // 流程实例表格列定义
  const instanceColumns: ColumnsType<WorkflowInstance> = [
    {
      title: '流程信息',
      key: 'workflow',
      width: 200,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.title}</div>
          <div className="text-sm text-gray-500">{record.workflowName}</div>
          <div className="text-xs text-gray-400">
            {getPriorityConfig(record.priority).text} · {record.initiator}
          </div>
        </div>
      ),
    },
    {
      title: '当前步骤',
      key: 'currentStep',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-sm">{record.currentStepName}</div>
          <div className="text-xs text-gray-500">
            步骤 {record.currentStep} / {workflowDefinitions.find(w => w.id === record.workflowId)?.steps.length || 0}
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
      render: (_, record) => {
        const workflow = workflowDefinitions.find(w => w.id === record.workflowId)
        const totalSteps = workflow?.steps.length || 1
        const progress = (record.currentStep / totalSteps) * 100

        return (
          <Progress
            percent={progress}
            size="small"
            status={record.status === 'completed' ? 'success' :
                   record.status === 'rejected' ? 'exception' : 'normal'}
          />
        )
      },
    },
    {
      title: '发起时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      render: (date: string) => (
        <div>
          <div>{dayjs(date).format('MM-DD HH:mm')}</div>
          <div className="text-xs text-gray-500">
            {dayjs(date).fromNow()}
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          {record.status === 'in_progress' && (
            <Tooltip title="审批">
              <Button
                type="text"
                size="small"
                icon={<ApproveOutlined />}
                onClick={() => handleApprove(record)}
              />
            </Tooltip>
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

  // 任务表格列定义
  const taskColumns: ColumnsType<Task> = [
    {
      title: '任务信息',
      key: 'task',
      width: 200,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.stepName}</div>
          <div className="text-sm text-gray-500">{record.instanceTitle}</div>
          <div className="text-xs text-gray-400">
            {getPriorityConfig(record.priority).text}
          </div>
        </div>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'assignee',
      key: 'assignee',
      width: 100,
      render: (assignee: string) => (
        <div className="flex items-center">
          <Avatar size="small" icon={<UserOutlined />} className="mr-2" />
          {assignee}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'default', text: '待处理' },
          in_progress: { color: 'processing', text: '进行中' },
          completed: { color: 'success', text: '已完成' },
          overdue: { color: 'error', text: '已逾期' },
        }
        const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '截止时间',
      dataIndex: 'dueDate',
      key: 'dueDate',
      width: 120,
      render: (date: string, record) => {
        const isOverdue = dayjs(date).isBefore(dayjs()) && record.status !== 'completed'
        return (
          <div className={isOverdue ? 'text-red-600' : 'text-gray-600'}>
            <div>{dayjs(date).format('MM-DD HH:mm')}</div>
            <div className="text-xs">
              {isOverdue ? '已逾期' : dayjs(date).fromNow()}
            </div>
          </div>
        )
      },
    },
  ]

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (modalType === 'approve' && currentItem) {
        // 审批逻辑
        const updatedInstance = workflowInstances.map(instance =>
          instance.id === currentItem.id
            ? {
                ...instance,
                currentStep: instance.currentStep + 1,
                status: values.action === 'approve' ? 'completed' : 'rejected',
                history: [
                  ...instance.history,
                  {
                    id: Date.now().toString(),
                    stepId: instance.currentStep.toString(),
                    stepName: instance.currentStepName,
                    action: values.action,
                    actor: '当前用户',
                    actorId: 'current_user',
                    comment: values.comment,
                    timestamp: dayjs().format('YYYY-MM-DD HH:mm:ss'),
                  },
                ],
                updatedAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
                completedAt: values.action === 'approve' ? dayjs().format('YYYY-MM-DD HH:mm:ss') : undefined,
              }
            : instance
        )
        setWorkflowInstances(updatedInstance)
        setFilteredInstances(updatedInstance)
        message.success(values.action === 'approve' ? '审批通过' : '已拒绝')
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
      <Title level={2} className="mb-6">工作流管理</Title>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="总流程数"
              value={stats.totalInstances}
              valueStyle={{ color: '#1890ff' }}
              prefix={<BranchesOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="待处理"
              value={stats.pendingCount}
              valueStyle={{ color: '#fa8c16' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="进行中"
              value={stats.inProgressCount}
              valueStyle={{ color: '#52c41a' }}
              prefix={<BranchesOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="已完成"
              value={stats.completedCount}
              valueStyle={{ color: '#722ed1' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="我的待办"
              value={stats.myTasksCount}
              valueStyle={{ color: '#f5222d' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="逾期任务"
              value={stats.overdueTasksCount}
              valueStyle={{ color: '#fa541c' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'instances',
            label: '流程实例',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索流程名称、发起人"
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
                        <Option value="pending">待处理</Option>
                        <Option value="in_progress">进行中</Option>
                        <Option value="completed">已完成</Option>
                        <Option value="rejected">已拒绝</Option>
                      </Select>
                    </Space>

                    <Space>
                      <Button icon={<PlusOutlined />} type="primary">
                        发起流程
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 流程实例列表 */}
                <Card>
                  <Table
                    columns={instanceColumns}
                    dataSource={filteredInstances}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      total: filteredInstances.length,
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                    }}
                    scroll={{ x: 1000 }}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'tasks',
            label: '我的待办',
            children: (
              <Card>
                <Table
                  columns={taskColumns}
                  dataSource={tasks.filter(task => task.assignee === '当前用户')}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    total: tasks.filter(task => task.assignee === '当前用户').length,
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                />
              </Card>
            ),
          },
          {
            key: 'definitions',
            label: '流程定义',
            children: (
              <Card>
                <div className="mb-4">
                  <Button type="primary" icon={<PlusOutlined />}>
                    新建流程
                  </Button>
                </div>

                <Row gutter={16}>
                  {workflowDefinitions.map(workflow => (
                    <Col span={12} key={workflow.id} className="mb-4">
                      <Card
                        title={workflow.name}
                        size="small"
                        extra={
                          <Space>
                            <Tag color={workflow.isActive ? 'success' : 'default'}>
                              {workflow.isActive ? '启用' : '禁用'}
                            </Tag>
                            <Button type="text" size="small" icon={<SettingOutlined />} />
                          </Space>
                        }
                      >
                        <div className="mb-2">
                          <Text type="secondary">{workflow.description}</Text>
                        </div>
                        <div className="mb-2">
                          <Tag>{workflow.category}</Tag>
                          <Tag>{workflow.triggerType}</Tag>
                        </div>
                        <Steps size="small" current={-1}>
                          {workflow.steps.slice(0, 3).map(step => (
                            <Step key={step.id} title={step.name} />
                          ))}
                          {workflow.steps.length > 3 && (
                            <Step title="..." />
                          )}
                        </Steps>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            ),
          },
        ]}
      />

      {/* 详情/审批模态框 */}
      <Modal
        title={
          modalType === 'view' ? '流程详情' :
          modalType === 'approve' ? '流程审批' :
          '操作'
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
              key="reject"
              danger
              loading={loading}
              onClick={() => form.setFieldsValue({ action: 'reject' })}
            >
              拒绝
            </Button>,
            <Button
              key="approve"
              type="primary"
              loading={loading}
              onClick={() => form.setFieldsValue({ action: 'approve' })}
            >
              通过
            </Button>,
          ] : []
        }
        width={800}
      >
        {modalType === 'view' && currentItem && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="流程名称">{currentItem.title}</Descriptions.Item>
              <Descriptions.Item label="流程类型">{currentItem.workflowName}</Descriptions.Item>
              <Descriptions.Item label="发起人">{currentItem.initiator}</Descriptions.Item>
              <Descriptions.Item label="优先级">
                <Tag color={getPriorityConfig(currentItem.priority).color}>
                  {getPriorityConfig(currentItem.priority).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="当前步骤">{currentItem.currentStepName}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusConfig(currentItem.status).color}>
                  {getStatusConfig(currentItem.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="发起时间">{currentItem.createdAt}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{currentItem.updatedAt}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Title level={4}>流程进度</Title>
            <Steps
              current={currentItem.currentStep - 1}
              status={currentItem.status === 'completed' ? 'finish' :
                     currentItem.status === 'rejected' ? 'error' : 'process'}
            >
              {workflowDefinitions
                .find(w => w.id === currentItem.workflowId)
                ?.steps.map(step => (
                  <Step key={step.id} title={step.name} />
                ))}
            </Steps>

            <Divider />

            <Title level={4}>表单数据</Title>
            <Descriptions column={1} bordered>
              {Object.entries(currentItem.formData).map(([key, value]) => (
                <Descriptions.Item key={key} label={key}>
                  {String(value)}
                </Descriptions.Item>
              ))}
            </Descriptions>

            <Divider />

            <Title level={4}>审批历史</Title>
            <Timeline>
              {currentItem.history.map((history, index) => (
                <Timeline.Item key={history.id}>
                  <div>
                    <div className="font-medium">{history.actor}</div>
                    <div className="text-sm text-gray-500">
                      {history.stepName} · {history.action}
                    </div>
                    <div className="text-xs text-gray-400">{history.comment}</div>
                    <div className="text-xs text-gray-400">{history.timestamp}</div>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </div>
        )}

        {modalType === 'approve' && currentItem && (
          <div>
            <Alert
              message="审批确认"
              description={`您正在审批流程"${currentItem.title}"的当前步骤"${currentItem.currentStepName}"`}
              type="info"
              showIcon
              className="mb-4"
            />

            <Form form={form} layout="vertical">
              <Form.Item
                name="action"
                label="审批结果"
                rules={[{ required: true, message: '请选择审批结果' }]}
              >
                <Radio.Group>
                  <Radio value="approve">通过</Radio>
                  <Radio value="reject">拒绝</Radio>
                  <Radio value="return">退回</Radio>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                name="comment"
                label="审批意见"
                rules={[{ required: true, message: '请输入审批意见' }]}
              >
                <TextArea rows={4} placeholder="请输入审批意见" />
              </Form.Item>
            </Form>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default WorkflowManagement