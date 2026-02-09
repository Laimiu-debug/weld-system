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
  Spin,
  Empty,
  Typography,
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
  ToolOutlined,
  CalendarOutlined,
  SettingOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import {
  equipmentService,
  Equipment,
  EquipmentType,
  EquipmentStatus,
  EquipmentStatistics,
  MaintenanceAlert,
  EquipmentListParams,
  CreateEquipmentData,
  UpdateEquipmentData
} from '@/services/equipment'
import { workspaceService } from '@/services/workspace'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input
const { Title, Paragraph } = Typography


const EquipmentList: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [statistics, setStatistics] = useState<EquipmentStatistics | null>(null)
  const [maintenanceAlerts, setMaintenanceAlerts] = useState<MaintenanceAlert[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [filters, setFilters] = useState<EquipmentListParams>({})
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'view' | 'edit'>('view')
  const [currentEquipment, setCurrentEquipment] = useState<Equipment | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('equipment')
  const [searchKeyword, setSearchKeyword] = useState('')

  // 加载设备列表
  const loadEquipment = async (params?: EquipmentListParams) => {
    setLoading(true)
    try {
      const queryParams: EquipmentListParams = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        ...filters,
        ...params
      }

      if (searchKeyword) {
        queryParams.search = searchKeyword
      }

      // 添加工作区类型参数
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      if (currentWorkspace) {
        // 注意：前端使用 'enterprise'，但后端 API 接受 'company'
        queryParams.workspace_type = currentWorkspace.type === 'enterprise' ? 'company' : 'personal'
      }

      const response = await equipmentService.getEquipmentList(queryParams)

      if (response.success) {
        setEquipment(response.data.items)
        setPagination(prev => ({
          ...prev,
          total: response.data.total
        }))
      } else {
        message.error(response.message || '获取设备列表失败')
      }
    } catch (error: any) {
      console.error('获取设备列表失败:', error)
      // API拦截器已经显示了错误消息，这里不需要再显示
      if (!error.response) {
        message.error('网络错误，请检查连接')
      }
    } finally {
      setLoading(false)
    }
  }

  // 加载统计信息
  const loadStatistics = async () => {
    try {
      const response = await equipmentService.getEquipmentStatistics()
      if (response.success) {
        setStatistics(response.data)
      }
    } catch (error: any) {
      console.error('获取统计信息失败:', error)
    }
  }

  // 加载维护提醒
  const loadMaintenanceAlerts = async () => {
    try {
      const response = await equipmentService.getMaintenanceAlerts(30)
      if (response.success) {
        setMaintenanceAlerts(response.data.items)
      }
    } catch (error: any) {
      console.error('获取维护提醒失败:', error)
    }
  }

  // 初始化数据
  useEffect(() => {
    loadEquipment()
    loadStatistics()
    loadMaintenanceAlerts()
  }, [])

  // 监听工作区切换
  useEffect(() => {
    const handleWorkspaceSwitch = () => {
      console.log('工作区切换，重新加载设备')
      loadEquipment()
    }

    // 监听工作区切换事件
    window.addEventListener('workspace-switched', handleWorkspaceSwitch)

    return () => {
      window.removeEventListener('workspace-switched', handleWorkspaceSwitch)
    }
  }, [])

  // 分页处理
  const handleTableChange = (page: number, pageSize: number) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize
    }))
    loadEquipment({
      skip: (page - 1) * pageSize,
      limit: pageSize
    })
  }

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchKeyword(value)
    setPagination(prev => ({ ...prev, current: 1 }))
    loadEquipment({ search: value })
  }

  // 类型过滤
  const handleTypeFilter = (type: string) => {
    const newFilters = { ...filters }
    if (type === 'all') {
      delete newFilters.equipment_type
    } else {
      newFilters.equipment_type = type as EquipmentType
    }
    setFilters(newFilters)
    setPagination(prev => ({ ...prev, current: 1 }))
    loadEquipment(newFilters)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    const newFilters = { ...filters }
    if (status === 'all') {
      delete newFilters.status
    } else {
      newFilters.status = status as EquipmentStatus
    }
    setFilters(newFilters)
    setPagination(prev => ({ ...prev, current: 1 }))
    loadEquipment(newFilters)
  }

  // 刷新数据
  const handleRefresh = () => {
    loadEquipment()
    loadStatistics()
    loadMaintenanceAlerts()
  }

  
  // 创建设备
  const handleCreate = () => {
    setCurrentEquipment(null)
    setModalType('create')
    form.resetFields()
    setIsModalVisible(true)
  }

  // 查看详情
  const handleView = (record: Equipment) => {
    setCurrentEquipment(record)
    setModalType('view')
    setIsModalVisible(true)
  }

  // 编辑设备
  const handleEdit = (record: Equipment) => {
    setCurrentEquipment(record)
    setModalType('edit')
    setIsModalVisible(true)
    // 设置表单初始值
    form.setFieldsValue({
      ...record,
      // 转换日期格式
      purchase_date: record.purchase_date ? dayjs(record.purchase_date) : null,
      warranty_expiry_date: record.warranty_expiry_date ? dayjs(record.warranty_expiry_date) : null,
      installation_date: record.installation_date ? dayjs(record.installation_date) : null,
      commissioning_date: record.commissioning_date ? dayjs(record.commissioning_date) : null,
      last_maintenance_date: record.last_maintenance_date ? dayjs(record.last_maintenance_date) : null,
      next_maintenance_date: record.next_maintenance_date ? dayjs(record.next_maintenance_date) : null,
    })
  }

  // 删除设备
  const handleDelete = async (equipmentId: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个设备吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await equipmentService.deleteEquipment(equipmentId)
          if (response.success) {
            message.success('删除成功')
            handleRefresh()
          } else {
            message.error(response.message || '删除失败')
          }
        } catch (error: any) {
          console.error('删除设备失败:', error)
          // API拦截器已经显示了错误消息，这里不需要再显示
          // 只在拦截器没有处理的情况下显示（如网络错误）
          if (!error.response) {
            message.error('网络错误，请检查连接')
          }
        }
      },
    })
  }

  // 更新设备状态
  const handleStatusUpdate = (record: Equipment) => {
    Modal.confirm({
      title: '更新设备状态',
      content: (
        <div>
          <p>当前状态: {equipmentService.formatEquipmentStatus(record.status).text}</p>
          <p>请选择新的状态:</p>
          <Select
            style={{ width: '100%', marginTop: 8 }}
            placeholder="选择新状态"
            onChange={(value) => {
              updateEquipmentStatus(record.id.toString(), value)
            }}
          >
            {equipmentService.getEquipmentStatusOptions().map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </div>
      ),
      okText: '取消',
      cancelButtonProps: { style: { display: 'none' } },
    })
  }

  // 执行状态更新
  const updateEquipmentStatus = async (equipmentId: string, newStatus: EquipmentStatus) => {
    try {
      const response = await equipmentService.updateEquipmentStatus(equipmentId, {
        status: newStatus
      })
      if (response.success) {
        message.success('状态更新成功')
        handleRefresh()
        Modal.destroyAll()
      } else {
        message.error(response.message || '状态更新失败')
      }
    } catch (error: any) {
      console.error('更新状态失败:', error)
      // API拦截器已经显示了错误消息
      if (!error.response) {
        message.error('网络错误，请检查连接')
      }
    }
  }

  // 处理表单提交
  const handleFormSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      // 转换日期格式并过滤掉 undefined 值
      const formData: any = {}

      // 复制所有非日期、非undefined的字段
      Object.keys(values).forEach(key => {
        const value = values[key]
        // 跳过日期字段（稍后单独处理）和 undefined 值
        if (!['purchase_date', 'warranty_expiry_date', 'installation_date', 'commissioning_date'].includes(key)
            && value !== undefined) {
          formData[key] = value
        }
      })

      // 处理日期字段 - 只有当日期存在时才添加到对象中
      if (values.purchase_date) {
        formData.purchase_date = values.purchase_date.format('YYYY-MM-DD')
      }
      if (values.warranty_expiry_date) {
        formData.warranty_expiry_date = values.warranty_expiry_date.format('YYYY-MM-DD')
      }
      if (values.installation_date) {
        formData.installation_date = values.installation_date.format('YYYY-MM-DD')
      }
      if (values.commissioning_date) {
        formData.commissioning_date = values.commissioning_date.format('YYYY-MM-DD')
      }

      console.log('提交的设备数据:', formData)

      if (modalType === 'create') {
        const response = await equipmentService.createEquipment(formData as CreateEquipmentData)
        if (response.success) {
          message.success('创建成功')
          handleRefresh()
          setIsModalVisible(false)
          form.resetFields()
        } else {
          message.error(response.message || '创建失败')
        }
      } else if (modalType === 'edit' && currentEquipment) {
        const response = await equipmentService.updateEquipment(currentEquipment.id.toString(), formData as UpdateEquipmentData)
        if (response.success) {
          message.success('更新成功')
          handleRefresh()
          setIsModalVisible(false)
          form.resetFields()
        } else {
          message.error(response.message || '更新失败')
        }
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      // API拦截器已经显示了错误消息
      if (!error.response) {
        message.error('网络错误，请检查连接')
      }
    } finally {
      setLoading(false)
    }
  }

  
  
  // 表格列定义
  const columns: ColumnsType<Equipment> = [
    {
      title: '设备信息',
      key: 'equipment',
      width: 280,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.equipment_name}</div>
          <div className="text-sm text-gray-500">编号: {record.equipment_code}</div>
          <div className="text-xs text-gray-400">{record.manufacturer} · {record.model}</div>
        </div>
      ),
    },
    {
      title: '设备类型',
      dataIndex: 'equipment_type',
      key: 'equipment_type',
      width: 100,
      render: (type: EquipmentType) => (
        <Tag color="blue">{equipmentService.formatEquipmentType(type)}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: EquipmentStatus) => {
        const config = equipmentService.formatEquipmentStatus(status)
        return (
          <Tag color={config.color}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '位置',
      key: 'location',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-sm">{record.location}</div>
          {record.workshop && <div className="text-xs text-gray-500">{record.workshop}</div>}
        </div>
      ),
    },
    {
      title: '使用率',
      key: 'utilization',
      width: 120,
      render: (_, record) => {
        const utilizationRate = record.utilization_rate || 0
        return (
          <div>
            <Progress
              percent={utilizationRate}
              size="small"
              status={utilizationRate >= 80 ? 'success' : utilizationRate >= 60 ? 'normal' : 'exception'}
            />
            <div className="text-xs text-gray-500 mt-1">{utilizationRate}%</div>
          </div>
        )
      },
    },
    {
      title: '运行时长',
      dataIndex: 'total_operating_hours',
      key: 'total_operating_hours',
      width: 100,
      render: (hours: number) => (
        <span className="text-gray-600">{hours || 0}h</span>
      ),
    },
    {
      title: '下次维护',
      key: 'maintenance',
      width: 120,
      render: (_, record) => {
        if (!record.next_maintenance_date) {
          return <span className="text-gray-400">未设置</span>
        }

        const daysUntil = dayjs(record.next_maintenance_date).diff(dayjs(), 'day')
        let color = 'text-gray-600'
        if (daysUntil < 0) color = 'text-red-600 font-medium'
        else if (daysUntil <= 7) color = 'text-orange-600'

        return (
          <div className={color}>
            <div>{dayjs(record.next_maintenance_date).format('MM-DD')}</div>
            <div className="text-xs">
              {daysUntil < 0 ? '已逾期' : daysUntil <= 7 ? `${daysUntil}天后` : `${daysUntil}天后`}
            </div>
          </div>
        )
      },
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
          <Dropdown
            menu={{
              items: [
                {
                  key: 'status',
                  label: '更新状态',
                  icon: <SettingOutlined />,
                  onClick: () => handleStatusUpdate(record),
                },
                {
                  key: 'delete',
                  label: '删除设备',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleDelete(record.id.toString()),
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

  
  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">设备管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="设备总数"
                value={statistics?.total_equipment || 0}
                valueStyle={{ color: '#1890ff' }}
                prefix={<SettingOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="正常运行"
                value={statistics?.operational || 0}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="空闲"
                value={statistics?.idle || 0}
                valueStyle={{ color: '#1890ff' }}
                prefix={<SettingOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="维护中"
                value={statistics?.maintenance || 0}
                valueStyle={{ color: '#faad14' }}
                prefix={<ToolOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="故障/维修"
                value={(statistics?.broken || 0) + (statistics?.repair || 0)}
                valueStyle={{ color: '#f5222d' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="需维护"
                value={statistics?.upcoming_maintenance || 0}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* 预警信息 */}
        {maintenanceAlerts.length > 0 && (
          <Alert
            message={
              <div>
                <div className="mb-2 font-medium">设备维护提醒</div>
                {maintenanceAlerts.slice(0, 3).map(alert => (
                  <div key={alert.id} className="text-sm">
                    • {alert.equipment_name} ({alert.equipment_code}) - {alert.urgency === 'urgent' ? '紧急' : '即将'}需要维护
                  </div>
                ))}
                {maintenanceAlerts.length > 3 && (
                  <div className="text-sm">• 还有 {maintenanceAlerts.length - 3} 台设备需要维护</div>
                )}
              </div>
            }
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
            key: 'equipment',
            label: '设备列表',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索设备名称、编号、制造商、型号、序列号"
                        allowClear
                        enterButton={<SearchOutlined />}
                        style={{ width: 350 }}
                        onSearch={handleSearch}
                        onChange={(e) => !e.target.value && handleSearch('')}
                      />
                      <Select
                        placeholder="类型筛选"
                        style={{ width: 140 }}
                        onChange={handleTypeFilter}
                        value={filters.equipment_type || 'all'}
                      >
                        <Option value="all">全部类型</Option>
                        {equipmentService.getEquipmentTypeOptions().map(option => (
                          <Option key={option.value} value={option.value}>
                            {option.label}
                          </Option>
                        ))}
                      </Select>
                      <Select
                        placeholder="状态筛选"
                        style={{ width: 120 }}
                        onChange={handleStatusFilter}
                        value={filters.status || 'all'}
                      >
                        <Option value="all">全部状态</Option>
                        {equipmentService.getEquipmentStatusOptions().map(option => (
                          <Option key={option.value} value={option.value}>
                            {option.label}
                          </Option>
                        ))}
                      </Select>
                    </Space>

                    <Space>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={handleRefresh}
                        loading={loading}
                      >
                        刷新
                      </Button>
                      <Button icon={<ImportOutlined />}>批量导入</Button>
                      <Button icon={<ExportOutlined />}>导出数据</Button>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleCreate}
                      >
                        新增设备
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 设备列表表格 */}
                <Card>
                  {equipment.length === 0 && !loading ? (
                    <Empty
                      description="暂无设备数据"
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    >
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleCreate}
                      >
                        添加第一个设备
                      </Button>
                    </Empty>
                  ) : (
                    <Table
                      columns={columns}
                      dataSource={equipment}
                      rowKey="id"
                      loading={loading}
                      pagination={{
                        current: pagination.current,
                        pageSize: pagination.pageSize,
                        total: pagination.total,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                        onChange: handleTableChange,
                        onShowSizeChange: (current, size) => handleTableChange(current, size),
                      }}
                      rowSelection={{
                        selectedRowKeys,
                        onChange: setSelectedRowKeys,
                      }}
                      scroll={{ x: 1400 }}
                    />
                  )}
                </Card>
              </>
            ),
          },
          {
            key: 'maintenance',
            label: '维护记录',
            children: (
              <Card>
                <div className="text-center py-8">
                  <Title level={4}>维护记录管理</Title>
                  <Paragraph type="secondary">
                    设备维护记录功能正在开发中，敬请期待...
                  </Paragraph>
                  <Empty
                    description="暂无维护记录"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              </Card>
            ),
          },
          {
            key: 'usage',
            label: '使用记录',
            children: (
              <Card>
                <div className="text-center py-8">
                  <Title level={4}>设备使用记录</Title>
                  <Paragraph type="secondary">
                    设备使用记录功能正在开发中，敬请期待...
                  </Paragraph>
                  <Empty
                    description="暂无使用记录"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              </Card>
            ),
          },
          {
            key: 'schedule',
            label: '维护计划',
            children: (
              <Card>
                <div className="text-center py-8">
                  <Title level={4}>设备维护计划</Title>
                  <Paragraph type="secondary">
                    设备维护计划功能正在开发中，敬请期待...
                  </Paragraph>
                  <Empty
                    description="暂无维护计划"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                </div>
              </Card>
            ),
          },
        ]}
      />

      {/* 设备详情/编辑/创建模态框 */}
      <Modal
        title={
          modalType === 'view' ? '设备详情' :
          modalType === 'edit' ? '编辑设备' :
          '新增设备'
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
              onClick={handleFormSubmit}
            >
              {modalType === 'edit' ? '更新' : modalType === 'create' ? '创建' : '确认'}
            </Button>,
          ]
        }
        width={modalType === 'view' ? 1000 : 800}
      >
        {modalType === 'view' && currentEquipment && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="设备名称">{currentEquipment.equipment_name}</Descriptions.Item>
              <Descriptions.Item label="设备编号">{currentEquipment.equipment_code}</Descriptions.Item>
              <Descriptions.Item label="设备类型">
                {equipmentService.formatEquipmentType(currentEquipment.equipment_type)}
              </Descriptions.Item>
              <Descriptions.Item label="制造商">{currentEquipment.manufacturer}</Descriptions.Item>
              <Descriptions.Item label="品牌">{currentEquipment.brand}</Descriptions.Item>
              <Descriptions.Item label="型号">{currentEquipment.model}</Descriptions.Item>
              <Descriptions.Item label="序列号">{currentEquipment.serial_number}</Descriptions.Item>
              <Descriptions.Item label="设备类别">{currentEquipment.category}</Descriptions.Item>
              <Descriptions.Item label="位置">{currentEquipment.location}</Descriptions.Item>
              <Descriptions.Item label="车间">{currentEquipment.workshop}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={equipmentService.formatEquipmentStatus(currentEquipment.status).color}>
                  {equipmentService.formatEquipmentStatus(currentEquipment.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="关键设备">
                {currentEquipment.is_critical ? <Tag color="red">是</Tag> : <Tag>否</Tag>}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="技术参数" column={2} bordered>
              <Descriptions.Item label="额定功率">{currentEquipment.rated_power} kW</Descriptions.Item>
              <Descriptions.Item label="额定电压">{currentEquipment.rated_voltage} V</Descriptions.Item>
              <Descriptions.Item label="额定电流">{currentEquipment.rated_current} A</Descriptions.Item>
              <Descriptions.Item label="最大容量">{currentEquipment.max_capacity}</Descriptions.Item>
              <Descriptions.Item label="工作范围">{currentEquipment.working_range}</Descriptions.Item>
              <Descriptions.Item label="技术规格">{currentEquipment.specifications}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="运行数据" column={2} bordered>
              <Descriptions.Item label="运行工时">{currentEquipment.total_operating_hours || 0} 小时</Descriptions.Item>
              <Descriptions.Item label="维护工时">{currentEquipment.total_maintenance_hours || 0} 小时</Descriptions.Item>
              <Descriptions.Item label="使用次数">{currentEquipment.usage_count || 0}</Descriptions.Item>
              <Descriptions.Item label="维护次数">{currentEquipment.maintenance_count || 0}</Descriptions.Item>
              <Descriptions.Item label="使用率">{currentEquipment.utilization_rate || 0}%</Descriptions.Item>
              <Descriptions.Item label="可用率">{currentEquipment.availability_rate || 0}%</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="维护信息" column={2} bordered>
              <Descriptions.Item label="上次维护">{currentEquipment.last_maintenance_date || '未维护'}</Descriptions.Item>
              <Descriptions.Item label="下次维护">{currentEquipment.next_maintenance_date || '未设置'}</Descriptions.Item>
              <Descriptions.Item label="维护间隔">{currentEquipment.maintenance_interval_days || 0} 天</Descriptions.Item>
              <Descriptions.Item label="上次检验">{currentEquipment.last_inspection_date || '未检验'}</Descriptions.Item>
              <Descriptions.Item label="下次检验">{currentEquipment.next_inspection_date || '未设置'}</Descriptions.Item>
              <Descriptions.Item label="检验间隔">{currentEquipment.inspection_interval_days || 0} 天</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="采购信息" column={2} bordered>
              <Descriptions.Item label="采购日期">{currentEquipment.purchase_date || '未知'}</Descriptions.Item>
              <Descriptions.Item label="采购价格">¥{currentEquipment.purchase_price || 0}</Descriptions.Item>
              <Descriptions.Item label="供应商">{currentEquipment.supplier || '未知'}</Descriptions.Item>
              <Descriptions.Item label="保修期">{currentEquipment.warranty_period || 0} 月</Descriptions.Item>
              <Descriptions.Item label="保修到期">{currentEquipment.warranty_expiry_date || '未知'}</Descriptions.Item>
              <Descriptions.Item label="安装日期">{currentEquipment.installation_date || '未安装'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="附加信息" column={1} bordered>
              <Descriptions.Item label="设备描述">{currentEquipment.description || '无'}</Descriptions.Item>
              <Descriptions.Item label="备注信息">{currentEquipment.notes || '无'}</Descriptions.Item>
              <Descriptions.Item label="标签">{currentEquipment.tags || '无'}</Descriptions.Item>
              <Descriptions.Item label="访问级别">{currentEquipment.access_level}</Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {(modalType === 'edit' || modalType === 'create') && (
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              status: 'operational',
              currency: 'CNY',
              access_level: 'private',
            }}
          >
            {/* 基本信息 */}
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="equipment_code"
                  label="设备编号"
                  rules={[{ required: true, message: '请输入设备编号' }]}
                >
                  <Input placeholder="例如: EQ-WM-001" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="equipment_name"
                  label="设备名称"
                  rules={[{ required: true, message: '请输入设备名称' }]}
                >
                  <Input placeholder="例如: 数字化逆变焊机" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="equipment_type"
                  label="设备类型"
                  rules={[{ required: true, message: '请选择设备类型' }]}
                >
                  <Select placeholder="选择设备类型">
                    {equipmentService.getEquipmentTypeOptions().map(option => (
                      <Option key={option.value} value={option.value}>
                        {option.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="category"
                  label="设备类别"
                >
                  <Input placeholder="例如: 手工焊设备" />
                </Form.Item>
              </Col>
            </Row>

            {/* 制造商信息 */}
            <Divider orientation="left">制造商信息</Divider>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="manufacturer"
                  label="制造商"
                >
                  <Input placeholder="例如: 松下" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="brand"
                  label="品牌"
                >
                  <Input placeholder="例如: Panasonic" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="model"
                  label="型号"
                >
                  <Input placeholder="例如: YD-400KR2" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="serial_number"
                  label="序列号"
                >
                  <Input placeholder="设备序列号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="supplier"
                  label="供应商"
                >
                  <Input placeholder="供应商名称" />
                </Form.Item>
              </Col>
            </Row>

            {/* 技术参数 */}
            <Divider orientation="left">技术参数</Divider>
            <Row gutter={16}>
              <Col span={6}>
                <Form.Item
                  name="rated_power"
                  label="额定功率 (kW)"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    placeholder="0.00"
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item
                  name="rated_voltage"
                  label="额定电压 (V)"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    placeholder="0.00"
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item
                  name="rated_current"
                  label="额定电流 (A)"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    placeholder="0.00"
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item
                  name="max_capacity"
                  label="最大容量"
                >
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    placeholder="0.00"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="specifications"
              label="技术规格"
            >
              <TextArea rows={2} placeholder="详细技术规格说明" />
            </Form.Item>

            {/* 位置和状态 */}
            <Divider orientation="left">位置和状态</Divider>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="location"
                  label="存放位置"
                >
                  <Input placeholder="存放位置" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="workshop"
                  label="车间"
                >
                  <Input placeholder="所属车间" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="area"
                  label="区域"
                >
                  <Input placeholder="所属区域" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="status"
                  label="设备状态"
                >
                  <Select placeholder="选择设备状态">
                    {equipmentService.getEquipmentStatusOptions().map(option => (
                      <Option key={option.value} value={option.value}>
                        {option.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="access_level"
                  label="访问级别"
                >
                  <Select placeholder="选择访问级别">
                    <Option value="private">私有</Option>
                    <Option value="factory">工厂</Option>
                    <Option value="company">公司</Option>
                    <Option value="public">公开</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            {/* 备注 */}
            <Form.Item
              name="notes"
              label="备注信息"
            >
              <TextArea rows={2} placeholder="其他备注信息" />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default EquipmentList