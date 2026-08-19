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
  Select,
  DatePicker,
  InputNumber,
  message,
  Tooltip,
  Dropdown,
  Badge,
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  Tabs,
  Descriptions,
  Progress,
  Timeline,
  Avatar,
  Upload,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
  FilterOutlined,
  MoreOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  CalendarOutlined,
  UserOutlined,
  ToolOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  UploadOutlined,
  FireOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import {
  getProductionTasks,
  createProductionTask,
  updateProductionTask,
  deleteProductionTask,
  updateProductionTaskStatus,
  type ProductionTask as APIProductionTask,
  type ProductionTaskCreate,
} from '../../services/production'
import weldersService from '../../services/welders'
import equipmentService from '../../services/equipment'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input

interface ProductionTask {
  id: string
  taskNumber: string
  taskName: string
  projectName: string
  projectCode: string
  wpsId: string
  wpsName: string
  status: 'pending' | 'in_progress' | 'completed' | 'paused' | 'cancelled'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  assignedWelder: string
  assignedWelderId: string
  assignedEquipment: string
  assignedEquipmentId: string
  startDate: string
  endDate: string
  actualStartDate?: string
  actualEndDate?: string
  progressPercentage: number
  estimatedHours: number
  actualHours: number
  materials: string[]
  qualityRequirements: string
  specifications: string
  location: string
  supervisor: string
  notes: string
  createdDate: string
  updatedDate: string
  createdBy: string
}

interface ProductionLog {
  id: string
  taskId: string
  action: string
  timestamp: string
  operator: string
  details: string
  previousStatus?: string
  newStatus?: string
}

const ProductionList: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<ProductionTask[]>([])
  const [filteredData, setFilteredData] = useState<ProductionTask[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'start' | 'pause' | 'complete'>('create')
  const [currentTask, setCurrentTask] = useState<ProductionTask | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('tasks')

  // 工作区信息
  const [workspaceType, setWorkspaceType] = useState<string>('personal')
  const [companyId, setCompanyId] = useState<number | undefined>()
  const [factoryId, setFactoryId] = useState<number | undefined>()

  // 焊工和设备列表
  const [welders, setWelders] = useState<any[]>([])
  const [equipments, setEquipments] = useState<any[]>([])
  const [loadingWelders, setLoadingWelders] = useState(false)
  const [loadingEquipments, setLoadingEquipments] = useState(false)

  // 分页信息
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })

  // 筛选条件
  const [filters, setFilters] = useState({
    search: '',
    status: undefined as string | undefined,
    priority: undefined as string | undefined,
  })

  // 加载工作区信息
  useEffect(() => {
    const workspace = localStorage.getItem('current_workspace')
    if (workspace) {
      const workspaceData = JSON.parse(workspace)
      setWorkspaceType(workspaceData.type || 'personal')
      setCompanyId(workspaceData.company_id)
      setFactoryId(workspaceData.factory_id)
    }
  }, [])

  // 加载数据 - 只在工作区信息完全加载后才调用
  useEffect(() => {
    // 确保工作区类型已设置
    if (!workspaceType) return

    // 如果是企业工作区,确保companyId已设置
    if (workspaceType === 'enterprise' && !companyId) {
      return
    }

    fetchTasks()
    fetchWelders()
    fetchEquipments()
  }, [workspaceType, companyId, factoryId, pagination.current, pagination.pageSize, filters])

  // 获取焊工列表
  const fetchWelders = async () => {
    try {
      setLoadingWelders(true)

      // 从localStorage获取最新的工作区信息
      const workspace = localStorage.getItem('current_workspace')
      const workspaceData = workspace ? JSON.parse(workspace) : null

      const response = await weldersService.getList({
        skip: 0,
        limit: 1000, // 获取所有焊工用于下拉选择
      })

      if (response.success && response.data) {
        setWelders(response.data.items || [])
      }
    } catch (error) {
      console.error('获取焊工列表失败:', error)
    } finally {
      setLoadingWelders(false)
    }
  }

  // 获取设备列表
  const fetchEquipments = async () => {
    try {
      setLoadingEquipments(true)

      // 从localStorage获取最新的工作区信息
      const workspace = localStorage.getItem('current_workspace')
      const workspaceData = workspace ? JSON.parse(workspace) : null

      // 注意：前端使用 'enterprise'，但后端 API 接受 'company'
      const apiWorkspaceType = workspaceData?.type === 'enterprise' ? 'company' : 'personal'

      const response = await equipmentService.getEquipmentList({
        skip: 0,
        limit: 1000, // 获取所有设备用于下拉选择
        workspace_type: apiWorkspaceType,
      })

      if (response.success && response.data) {
        setEquipments(response.data.items || [])
      }
    } catch (error) {
      console.error('获取设备列表失败:', error)
    } finally {
      setLoadingEquipments(false)
    }
  }

  // 获取生产任务列表
  const fetchTasks = async () => {
    try {
      setLoading(true)
      const response = await getProductionTasks({
        workspace_type: workspaceType,
        company_id: companyId,
        factory_id: factoryId,
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: filters.search || undefined,
        status: filters.status,
        priority: filters.priority,
      })

      if (response.success) {
        // 转换API数据格式为前端格式
        const convertedTasks: ProductionTask[] = response.data.items.map((item: APIProductionTask) => ({
          id: item.id.toString(),
          taskNumber: item.task_number,
          taskName: item.task_name,
          projectName: '', // 需要从关联数据获取
          projectCode: '',
          wpsId: item.wps_id?.toString() || '',
          wpsName: '',
          status: item.status as any,
          priority: item.priority as any,
          assignedWelder: '',
          assignedWelderId: item.assigned_welder_id?.toString() || '',
          assignedEquipment: '',
          assignedEquipmentId: '',
          startDate: item.planned_start_date || '',
          endDate: item.planned_end_date || '',
          actualStartDate: item.actual_start_date,
          actualEndDate: item.actual_end_date,
          progressPercentage: item.progress_percentage,
          estimatedHours: item.planned_duration_hours || 0,
          actualHours: item.actual_duration_hours || 0,
          materials: [],
          qualityRequirements: item.quality_standards || '',
          specifications: item.technical_requirements || '',
          location: '',
          supervisor: '',
          notes: item.description || '',
          createdDate: item.created_at,
          updatedDate: item.updated_at,
          createdBy: '',
        }))

        setTasks(convertedTasks)
        setFilteredData(convertedTasks)
        setPagination({
          ...pagination,
          total: response.data.total,
        })
      }
    } catch (error) {
      console.error('获取生产任务列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 获取统计数据
  const getTaskStats = (data: ProductionTask[] = []) => {
    const totalTasks = data.length
    const inProgressCount = data.filter(item => item.status === 'in_progress').length
    const pendingCount = data.filter(item => item.status === 'pending').length
    const completedCount = data.filter(item => item.status === 'completed').length
    const pausedCount = data.filter(item => item.status === 'paused').length
    const urgentCount = data.filter(item => item.priority === 'urgent').length
    const overdueCount = data.filter(item => {
      const isOverdue = dayjs(item.endDate).isBefore(dayjs()) && item.status !== 'completed'
      return isOverdue
    }).length

    const avgProgress = data.length > 0
      ? Math.round(data.reduce((sum, item) => sum + item.progressPercentage, 0) / data.length)
      : 0

    const totalEstimatedHours = data.reduce((sum, item) => sum + item.estimatedHours, 0)
    const totalActualHours = data.reduce((sum, item) => sum + item.actualHours, 0)

    return {
      totalTasks,
      inProgress: inProgressCount,
      pending: pendingCount,
      completed: completedCount,
      paused: pausedCount,
      urgent: urgentCount,
      overdue: overdueCount,
      avgProgress,
      totalEstimatedHours,
      totalActualHours,
      efficiency: totalEstimatedHours > 0 ? Math.round((totalActualHours / totalEstimatedHours) * 100) : 0,
    }
  }

  const stats = getTaskStats(filteredData)

  // 搜索过滤
  const handleSearch = (value: string) => {
    const filtered = tasks.filter(
      item =>
        item.taskName.toLowerCase().includes(value.toLowerCase()) ||
        item.taskNumber.toLowerCase().includes(value.toLowerCase()) ||
        item.projectName.toLowerCase().includes(value.toLowerCase()) ||
        item.projectCode.toLowerCase().includes(value.toLowerCase()) ||
        item.assignedWelder.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredData(filtered)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    if (status === 'all') {
      setFilteredData(tasks)
    } else {
      const filtered = tasks.filter(item => item.status === status)
      setFilteredData(filtered)
    }
  }

  // 优先级过滤
  const handlePriorityFilter = (priority: string) => {
    if (priority === 'all') {
      setFilteredData(tasks)
    } else {
      const filtered = tasks.filter(item => item.priority === priority)
      setFilteredData(filtered)
    }
  }

  // 查看详情
  const handleView = (record: ProductionTask) => {
    setCurrentTask(record)
    setModalType('view')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 创建任务
  const handleCreate = () => {
    setModalType('create')
    setCurrentTask(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  // 编辑
  const handleEdit = (record: ProductionTask) => {
    setCurrentTask(record)
    setModalType('edit')
    setIsModalVisible(true)
    form.setFieldsValue({
      task_number: record.taskNumber,
      task_name: record.taskName,
      project_name: record.projectName,
      task_type: record.taskType,
      priority: record.priority,
      status: record.status,
      assigned_welder_id: record.assignedWelderId ? parseInt(record.assignedWelderId) : undefined,
      equipment_id: record.assignedEquipmentId ? parseInt(record.assignedEquipmentId) : undefined,
      planned_start_date: record.startDate ? dayjs(record.startDate) : null,
      planned_end_date: record.endDate ? dayjs(record.endDate) : null,
      planned_duration_hours: record.estimatedHours,
      workload: record.actualHours,
      material_spec: record.specifications,
      wps_standard: record.wpsName,
      description: record.description,
      technical_requirements: record.technicalRequirements,
      safety_requirements: record.notes,
      quality_standards: record.qualityStandards,
    })
  }

  // 开始任务
  const handleStartTask = (record: ProductionTask) => {
    setCurrentTask(record)
    setModalType('start')
    setIsModalVisible(true)
    form.resetFields()
  }

  // 暂停任务
  const handlePauseTask = (record: ProductionTask) => {
    setCurrentTask(record)
    setModalType('pause')
    setIsModalVisible(true)
    form.resetFields()
  }

  // 完成任务
  const handleCompleteTask = (record: ProductionTask) => {
    setCurrentTask(record)
    setModalType('complete')
    setIsModalVisible(true)
    form.resetFields()
  }

  // 删除
  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个生产任务吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          // 调用后端API删除
          await deleteProductionTask(parseInt(id), workspaceType, companyId, factoryId)

          // 删除成功后重新加载列表
          fetchTasks()
          message.success('删除成功')
        } catch (error) {
          console.error('删除失败:', error)
          // 错误消息已在service中显示
        }
      },
    })
  }

  // 获取状态颜色和文本
  const getStatusConfig = (status: string) => {
    const statusMap = {
      pending: { color: 'default', text: '待开始', icon: <ClockCircleOutlined /> },
      in_progress: { color: 'processing', text: '进行中', icon: <PlayCircleOutlined /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      paused: { color: 'warning', text: '已暂停', icon: <PauseCircleOutlined /> },
      cancelled: { color: 'error', text: '已取消', icon: <StopOutlined /> },
    }
    return statusMap[status as keyof typeof statusMap] || { color: 'default', text: status, icon: null }
  }

  // 获取优先级颜色和文本
  const getPriorityConfig = (priority: string) => {
    const priorityMap = {
      low: { color: 'default', text: '低', icon: null },
      normal: { color: 'blue', text: '普通', icon: null },
      high: { color: 'orange', text: '高', icon: <WarningOutlined /> },
      urgent: { color: 'red', text: '紧急', icon: <FireOutlined /> },
    }
    return priorityMap[priority as keyof typeof priorityMap] || { color: 'default', text: priority, icon: null }
  }

  // 表格列定义
  const columns: ColumnsType<ProductionTask> = [
    {
      title: '任务信息',
      key: 'task',
      width: 280,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.taskName}</div>
          <div className="text-sm text-gray-500">{record.taskNumber}</div>
          <div className="text-xs text-gray-400">{record.projectCode} · {record.projectName}</div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
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
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const config = getPriorityConfig(priority)
        return (
          <Tag color={config.color}>
            {config.icon} {config.text}
          </Tag>
        )
      },
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_, record) => (
        <div>
          <Progress
            percent={record.progressPercentage}
            size="small"
            status={record.progressPercentage === 100 ? 'success' : 'normal'}
          />
          <div className="text-xs text-gray-500 mt-1">
            {record.actualHours}h / {record.estimatedHours}h
          </div>
        </div>
      ),
    },
    {
      title: '焊工/设备',
      key: 'assignment',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-sm flex items-center">
            <UserOutlined className="mr-1" />
            {record.assignedWelder}
          </div>
          <div className="text-xs text-gray-500 flex items-center">
            <ToolOutlined className="mr-1" />
            {record.assignedEquipment}
          </div>
        </div>
      ),
    },
    {
      title: '计划时间',
      key: 'schedule',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-sm">{record.startDate}</div>
          <div className="text-xs text-gray-500">~ {record.endDate}</div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
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
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {record.status === 'pending' && (
            <Tooltip title="开始任务">
              <Button
                type="text"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStartTask(record)}
              />
            </Tooltip>
          )}
          {record.status === 'in_progress' && (
            <>
              <Tooltip title="暂停任务">
                <Button
                  type="text"
                  size="small"
                  icon={<PauseCircleOutlined />}
                  onClick={() => handlePauseTask(record)}
                />
              </Tooltip>
              <Tooltip title="完成任务">
                <Button
                  type="text"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleCompleteTask(record)}
                />
              </Tooltip>
            </>
          )}
          {record.status === 'paused' && (
            <Tooltip title="继续任务">
              <Button
                type="text"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStartTask(record)}
              />
            </Tooltip>
          )}
          <Dropdown
            menu={{
              items: [
                {
                  key: 'delete',
                  label: '删除任务',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDelete(record.id),
                },
              ],
            }}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (modalType === 'start') {
        // 开始任务逻辑
        const updatedTasks = tasks.map(item =>
          item.id === currentTask!.id
            ? {
                ...item,
                status: 'in_progress',
                actualStartDate: dayjs().format('YYYY-MM-DD'),
                progressPercentage: 5,
                actualHours: 0,
              }
            : item
        )
        setTasks(updatedTasks)
        setFilteredData(updatedTasks)
        message.success('任务已开始')
      } else if (modalType === 'pause') {
        // 暂停任务逻辑
        const updatedTasks = tasks.map(item =>
          item.id === currentTask!.id
            ? {
                ...item,
                status: 'paused',
              }
            : item
        )
        setTasks(updatedTasks)
        setFilteredData(updatedTasks)
        message.success('任务已暂停')
      } else if (modalType === 'complete') {
        // 完成任务逻辑
        const updatedTasks = tasks.map(item =>
          item.id === currentTask!.id
            ? {
                ...item,
                status: 'completed',
                actualEndDate: dayjs().format('YYYY-MM-DD'),
                progressPercentage: 100,
              }
            : item
        )
        setTasks(updatedTasks)
        setFilteredData(updatedTasks)
        message.success('任务已完成')
      } else if (modalType === 'create') {
        // 创建任务 - 使用真实API
        // 生成任务编号
        const taskNumber = `TASK-${dayjs().format('YYYYMMDD')}-${Math.random().toString(36).substr(2, 6).toUpperCase()}`

        const formData: any = {
          task_number: taskNumber,
          task_name: values.task_name,
          task_type: values.task_type || undefined,
          description: values.description || undefined,
          technical_requirements: values.technical_requirements || undefined,
          planned_start_date: values.planned_start_date ? values.planned_start_date.format('YYYY-MM-DD HH:mm:ss') : undefined,
          planned_end_date: values.planned_end_date ? values.planned_end_date.format('YYYY-MM-DD HH:mm:ss') : undefined,
          assigned_welder_id: values.assigned_welder_id || undefined,
          assigned_equipment_id: values.assigned_equipment_id || values.equipment_id || undefined,
          wps_id: values.wps_id || undefined,
        }

        const response = await createProductionTask(formData, workspaceType, companyId, factoryId)
        if (response.success) {
          message.success('创建成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchTasks() // 重新加载列表
        }
      } else if (modalType === 'edit' && currentTask) {
        // 编辑任务 - 使用真实API
        const formData: any = {
          task_number: values.task_number || currentTask.taskNumber,
          task_name: values.task_name,
          task_type: values.task_type || undefined,
          description: values.description || undefined,
          technical_requirements: values.technical_requirements || undefined,
          planned_start_date: values.planned_start_date ? values.planned_start_date.format('YYYY-MM-DD HH:mm:ss') : undefined,
          planned_end_date: values.planned_end_date ? values.planned_end_date.format('YYYY-MM-DD HH:mm:ss') : undefined,
          assigned_welder_id: values.assigned_welder_id || undefined,
          assigned_equipment_id: values.assigned_equipment_id || values.equipment_id || undefined,
          wps_id: values.wps_id || undefined,
        }

        const response = await updateProductionTask(parseInt(currentTask.id), formData, workspaceType, companyId, factoryId)
        if (response.success) {
          message.success('更新成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchTasks() // 重新加载列表
        }
      }

      if (modalType !== 'create' && modalType !== 'edit') {
        setIsModalVisible(false)
        form.resetFields()
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      if (error.response?.data?.detail) {
        // 处理后端验证错误
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          // Pydantic验证错误
          const errorMessages = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('; ')
          message.error(`验证失败: ${errorMessages}`)
        } else if (typeof detail === 'string') {
          message.error(detail)
        } else {
          message.error('操作失败，请检查输入')
        }
      } else if (error.errorFields) {
        message.error('请检查表单填写')
      } else {
        message.error('操作失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">生产管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="任务总数"
                value={stats.totalTasks}
                valueStyle={{ color: '#1890ff' }}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="进行中"
                value={stats.inProgress}
                valueStyle={{ color: '#52c41a' }}
                prefix={<PlayCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="已完成"
                value={stats.completed}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="紧急任务"
                value={stats.urgent}
                valueStyle={{ color: '#f5222d' }}
                prefix={<FireOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="平均进度"
                value={stats.avgProgress}
                suffix="%"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="工时效率"
                value={stats.efficiency}
                suffix="%"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 预警信息 */}
        {stats.overdue > 0 && (
          <Alert
            message={`有 ${stats.overdue} 个任务已逾期，请及时处理`}
            type="error"
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
            label: '生产任务',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索任务名称、编号、项目、焊工"
                        allowClear
                        enterButton={<SearchOutlined />}
                        style={{ width: 350 }}
                        onSearch={handleSearch}
                        onChange={(e) => !e.target.value && handleSearch('')}
                      />
                      <Select
                        placeholder="状态筛选"
                        style={{ width: 120 }}
                        onChange={handleStatusFilter}
                        defaultValue="all"
                      >
                        <Option value="all">全部状态</Option>
                        <Option value="pending">待开始</Option>
                        <Option value="in_progress">进行中</Option>
                        <Option value="completed">已完成</Option>
                        <Option value="paused">已暂停</Option>
                        <Option value="cancelled">已取消</Option>
                      </Select>
                      <Select
                        placeholder="优先级筛选"
                        style={{ width: 120 }}
                        onChange={handlePriorityFilter}
                        defaultValue="all"
                      >
                        <Option value="all">全部优先级</Option>
                        <Option value="low">低</Option>
                        <Option value="normal">普通</Option>
                        <Option value="high">高</Option>
                        <Option value="urgent">紧急</Option>
                      </Select>
                    </Space>

                    <Space>
                      <Button icon={<ImportOutlined />}>批量导入</Button>
                      <Button icon={<ExportOutlined />}>导出数据</Button>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleCreate}
                      >
                        创建任务
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 生产任务列表表格 */}
                <Card>
                  <Table
                    columns={columns}
                    dataSource={filteredData}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      total: filteredData.length,
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
            key: 'logs',
            label: '生产日志',
            children: (
              <Card
                extra={
                  filteredData.length > 0 ? (
                    <Button type="link" onClick={() => navigate(`/production/${filteredData[0].id}?tab=logs`)}>
                      打开最近任务日志
                    </Button>
                  ) : null
                }
              >
                <Table
                  rowKey="id"
                  dataSource={filteredData}
                  pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 个任务` }}
                  columns={[
                    { title: '任务编号', dataIndex: 'taskNumber', key: 'taskNumber', width: 160 },
                    { title: '任务名称', dataIndex: 'taskName', key: 'taskName' },
                    {
                      title: '状态',
                      dataIndex: 'status',
                      key: 'status',
                      width: 120,
                      render: (status: ProductionTask['status']) => {
                        const config = getStatusConfig(status)
                        return <Tag color={config.color}>{config.text}</Tag>
                      },
                    },
                    { title: '更新时间', dataIndex: 'updatedDate', key: 'updatedDate', width: 180 },
                    {
                      title: '操作',
                      key: 'actions',
                      width: 140,
                      render: (_: unknown, record: ProductionTask) => (
                        <Button type="link" onClick={() => navigate(`/production/${record.id}?tab=logs`)}>
                          查看日志
                        </Button>
                      ),
                    },
                  ]}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* 任务详情/编辑/状态变更模态框 */}
      <Modal
        title={
          modalType === 'view' ? '任务详情' :
          modalType === 'edit' ? '编辑任务' :
          modalType === 'start' ? '开始任务' :
          modalType === 'pause' ? '暂停任务' :
          modalType === 'complete' ? '完成任务' :
          '创建任务'
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
              {modalType === 'start' ? '确认开始' :
               modalType === 'pause' ? '确认暂停' :
               modalType === 'complete' ? '确认完成' :
               modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={modalType === 'view' ? 1000 : 900}
      >
        {modalType === 'view' && currentTask && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="任务名称">{currentTask.taskName}</Descriptions.Item>
              <Descriptions.Item label="任务编号">{currentTask.taskNumber}</Descriptions.Item>
              <Descriptions.Item label="项目名称">{currentTask.projectName}</Descriptions.Item>
              <Descriptions.Item label="项目编号">{currentTask.projectCode}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusConfig(currentTask.status).color}>
                  {getStatusConfig(currentTask.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                <Tag color={getPriorityConfig(currentTask.priority).color}>
                  {getPriorityConfig(currentTask.priority).text}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="执行信息" column={2} bordered>
              <Descriptions.Item label="焊工">{currentTask.assignedWelder}</Descriptions.Item>
              <Descriptions.Item label="设备">{currentTask.assignedEquipment}</Descriptions.Item>
              <Descriptions.Item label="位置">{currentTask.location}</Descriptions.Item>
              <Descriptions.Item label="监工">{currentTask.supervisor}</Descriptions.Item>
              <Descriptions.Item label="计划时间">
                {currentTask.startDate} ~ {currentTask.endDate}
              </Descriptions.Item>
              <Descriptions.Item label="实际时间">
                {currentTask.actualStartDate || '未开始'} ~ {currentTask.actualEndDate || '进行中'}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="进度信息" column={2} bordered>
              <Descriptions.Item label="进度">
                <Progress percent={currentTask.progressPercentage} />
              </Descriptions.Item>
              <Descriptions.Item label="工时">
                {currentTask.actualHours}h / {currentTask.estimatedHours}h
              </Descriptions.Item>
              <Descriptions.Item label="WPS">{currentTask.wpsName}</Descriptions.Item>
              <Descriptions.Item label="规格">{currentTask.specifications}</Descriptions.Item>
              <Descriptions.Item label="质量要求" span={2}>
                {currentTask.qualityRequirements}
              </Descriptions.Item>
              <Descriptions.Item label="使用材料" span={2}>
                {currentTask.materials.join(', ')}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="其他信息" column={1} bordered>
              <Descriptions.Item label="备注">{currentTask.notes}</Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {modalType === 'start' && currentTask && (
          <div>
            <Alert
              message="开始任务"
              description={`确定要开始任务 "${currentTask.taskName}" 吗？`}
              type="info"
              showIcon
              className="mb-4"
            />
            <Form form={form} layout="vertical">
              <Form.Item
                name="notes"
                label="开始备注"
              >
                <TextArea rows={3} placeholder="请输入开始任务的备注信息" />
              </Form.Item>
            </Form>
          </div>
        )}

        {modalType === 'pause' && currentTask && (
          <div>
            <Alert
              message="暂停任务"
              description={`确定要暂停任务 "${currentTask.taskName}" 吗？`}
              type="warning"
              showIcon
              className="mb-4"
            />
            <Form form={form} layout="vertical">
              <Form.Item
                name="reason"
                label="暂停原因"
                rules={[{ required: true, message: '请输入暂停原因' }]}
              >
                <TextArea rows={3} placeholder="请输入暂停任务的原因" />
              </Form.Item>
            </Form>
          </div>
        )}

        {modalType === 'complete' && currentTask && (
          <div>
            <Alert
              message="完成任务"
              description={`确定要完成任务 "${currentTask.taskName}" 吗？`}
              type="success"
              showIcon
              className="mb-4"
            />
            <Form form={form} layout="vertical">
              <Form.Item
                name="actualHours"
                label="实际工时"
                rules={[{ required: true, message: '请输入实际工时' }]}
              >
                <InputNumber
                  placeholder="请输入实际工时"
                  style={{ width: '100%' }}
                  min={0}
                  suffix="小时"
                />
              </Form.Item>
              <Form.Item
                name="qualityResult"
                label="质量检验结果"
                rules={[{ required: true, message: '请输入质量检验结果' }]}
              >
                <TextArea rows={3} placeholder="请输入质量检验结果" />
              </Form.Item>
            </Form>
          </div>
        )}

        {(modalType === 'create' || modalType === 'edit') && (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="task_name"
                  label="任务名称"
                  rules={[{ required: true, message: '请输入任务名称' }]}
                >
                  <Input placeholder="例如: 压力容器焊接任务" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="project_name"
                  label="项目名称"
                >
                  <Input placeholder="例如: 化工设备制造项目" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="task_type"
                  label="任务类型"
                >
                  <Select placeholder="选择任务类型">
                    <Option value="焊接">焊接</Option>
                    <Option value="切割">切割</Option>
                    <Option value="组装">组装</Option>
                    <Option value="检验">检验</Option>
                    <Option value="返修">返修</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="priority"
                  label="优先级"
                  initialValue="normal"
                >
                  <Select placeholder="选择优先级">
                    <Option value="low">低</Option>
                    <Option value="normal">正常</Option>
                    <Option value="high">高</Option>
                    <Option value="urgent">紧急</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="assigned_welder_id"
                  label="指定焊工"
                >
                  <Select
                    placeholder="选择焊工"
                    showSearch
                    loading={loadingWelders}
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={welders.map(welder => ({
                      value: welder.id,
                      label: `${welder.full_name || welder.name || '未命名'} (${welder.welder_code || welder.welder_number || '无编号'}) - ${welder.skill_level || ''}`,
                    }))}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="assigned_equipment_id"
                  label="使用设备"
                >
                  <Select
                    placeholder="选择设备"
                    showSearch
                    loading={loadingEquipments}
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={equipments.map(equipment => ({
                      value: equipment.id,
                      label: `${equipment.equipment_name || '未命名'} (${equipment.equipment_code || '无编号'}) - ${equipment.equipment_type || ''}`,
                    }))}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="planned_start_date"
                  label="开始时间"
                >
                  <DatePicker
                    showTime
                    style={{ width: '100%' }}
                    placeholder="选择开始时间"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="planned_end_date"
                  label="预计完成时间"
                >
                  <DatePicker
                    showTime
                    style={{ width: '100%' }}
                    placeholder="选择预计完成时间"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="workload"
                  label="工作量"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    placeholder="0.00"
                    addonAfter="米"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="material_spec"
                  label="材料规格"
                >
                  <Input placeholder="例如: Q345R δ=12mm" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="wps_standard"
              label="WPS标准"
            >
              <Select placeholder="选择WPS标准">
                <Option value="WPS-001">碳钢焊接工艺规程</Option>
                <Option value="WPS-002">不锈钢焊接工艺规程</Option>
                <Option value="WPS-003">铝合金焊接工艺规程</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="description"
              label="任务描述"
            >
              <TextArea
                rows={4}
                placeholder="请详细描述生产任务要求、技术要点等..."
              />
            </Form.Item>

            <Form.Item
              name="technical_requirements"
              label="技术要求"
            >
              <TextArea
                rows={3}
                placeholder="焊接质量要求、检验标准、验收条件等..."
              />
            </Form.Item>

            <Form.Item
              name="safety_requirements"
              label="安全要求"
            >
              <TextArea
                rows={3}
                placeholder="安全防护措施、操作规程、应急预案等..."
              />
            </Form.Item>

            <Form.Item
              name="attachments"
              label="相关文档"
              valuePropName="fileList"
              getValueFromEvent={(e) => {
                if (Array.isArray(e)) {
                  return e
                }
                return e?.fileList
              }}
            >
              <Upload.Dragger
                multiple
                action="/api/upload"
                showUploadList={true}
              >
                <p className="ant-upload-drag-icon">
                  <UploadOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持技术图纸、工艺文件、检验标准等文档
                </p>
              </Upload.Dragger>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default ProductionList