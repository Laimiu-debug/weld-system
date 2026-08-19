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
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  Descriptions,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  BarcodeOutlined,
  ReloadOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { workspaceService } from '@/services/workspace'
import materialsService, { Material, MaterialCreate, MaterialUpdate } from '@/services/materials'
import StockInModal from './StockInModal'
import StockOutModal from './StockOutModal'

const { Search } = Input
const { Option } = Select
const { TextArea } = Input

const MaterialsList: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [materials, setMaterials] = useState<Material[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [materialTypeFilter, setMaterialTypeFilter] = useState<string | undefined>()
  const [lowStockFilter, setLowStockFilter] = useState<boolean | undefined>()
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view'>('create')
  const [currentMaterial, setCurrentMaterial] = useState<Material | null>(null)
  const [form] = Form.useForm()

  // 出入库相关状态
  const [stockInVisible, setStockInVisible] = useState(false)
  const [stockOutVisible, setStockOutVisible] = useState(false)
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)

  // 获取焊材列表
  const fetchMaterials = async () => {
    // 获取当前工作区
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    setLoading(true)
    try {
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
        factory_id: currentWorkspace.factory_id,
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchText || undefined,
        material_type: materialTypeFilter,
        low_stock: lowStockFilter,
      }

      const response = await materialsService.getMaterialsList(params)

      if (response.success) {
        const { items, total: totalCount } = response.data
        setMaterials(items || [])
        setTotal(totalCount || 0)
      } else {
        message.error('获取焊材列表失败')
      }
    } catch (error: any) {
      console.error('获取焊材列表失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else {
        message.error('获取焊材列表失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 初始加载和工作区变化时重新加载
  useEffect(() => {
    fetchMaterials()
  }, [currentPage, pageSize, searchText, materialTypeFilter, lowStockFilter])

  // 监听工作区切换
  useEffect(() => {
    const handleWorkspaceSwitch = () => {
      fetchMaterials()
    }

    window.addEventListener('workspace-switched', handleWorkspaceSwitch)
    return () => {
      window.removeEventListener('workspace-switched', handleWorkspaceSwitch)
    }
  }, [])

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value)
    setCurrentPage(1) // 重置到第一页
  }

  // 处理筛选
  const handleFilterChange = (type?: string, lowStock?: boolean) => {
    setMaterialTypeFilter(type)
    setLowStockFilter(lowStock)
    setCurrentPage(1) // 重置到第一页
  }

  // 处理创建焊材
  const handleCreate = () => {
    setModalType('create')
    setCurrentMaterial(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  // 处理编辑焊材
  const handleEdit = (material: Material) => {
    setModalType('edit')
    setCurrentMaterial(material)
    form.setFieldsValue({
      material_code: material.material_code,
      material_name: material.material_name,
      material_type: material.material_type,
      specification: material.specification,
      manufacturer: material.manufacturer,
      current_stock: material.current_stock,
      unit: material.unit,
      min_stock_level: material.min_stock_level,
      reorder_point: material.reorder_point,
      unit_price: material.unit_price,
      storage_location: material.storage_location,
      supplier: material.supplier,
      batch_number: material.batch_number,
      production_date: material.production_date ? dayjs(material.production_date) : undefined,
      expiry_date: material.expiry_date ? dayjs(material.expiry_date) : undefined,
      quality_certificate: material.quality_certificate,
      notes: material.notes,
    })
    setIsModalVisible(true)
  }

  // 处理查看焊材
  const handleView = (material: Material) => {
    setModalType('view')
    setCurrentMaterial(material)
    setIsModalVisible(true)
  }

  // 处理删除焊材
  const handleDelete = async (materialId: number) => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条焊材记录吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await materialsService.deleteMaterial(
            materialId,
            currentWorkspace.type,
            currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
            currentWorkspace.factory_id
          )

          if (response.success) {
            message.success('删除成功')
            fetchMaterials() // 重新加载列表
          } else {
            message.error('删除失败')
          }
        } catch (error: any) {
          console.error('删除焊材失败:', error)
          if (error.response?.data?.detail) {
            message.error(error.response.data.detail)
          } else {
            message.error('删除失败，请稍后重试')
          }
        }
      },
    })
  }

  // 处理批量删除
  const handleBatchDelete = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的焊材')
      return
    }

    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 条焊材记录吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await materialsService.batchDeleteMaterials(
            selectedRowKeys.map(key => Number(key)),
            currentWorkspace.type,
            currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
            currentWorkspace.factory_id
          )

          if (response.success) {
            message.success('批量删除成功')
            setSelectedRowKeys([])
            fetchMaterials() // 重新加载列表
          } else {
            message.error('批量删除失败')
          }
        } catch (error: any) {
          console.error('批量删除焊材失败:', error)
          if (error.response?.data?.detail) {
            message.error(error.response.data.detail)
          } else {
            message.error('批量删除失败，请稍后重试')
          }
        }
      },
    })
  }

  // 处理表单提交
  const handleModalOk = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    try {
      const values = await form.validateFields()

      // 转换日期格式
      const formData: MaterialCreate | MaterialUpdate = {
        ...values,
        production_date: values.production_date ? values.production_date.format('YYYY-MM-DD') : undefined,
        expiry_date: values.expiry_date ? values.expiry_date.format('YYYY-MM-DD') : undefined,
      }

      setLoading(true)

      if (modalType === 'create') {
        const response = await materialsService.createMaterial(
          formData as MaterialCreate,
          currentWorkspace.type,
          currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
          currentWorkspace.factory_id
        )

        if (response.success) {
          message.success('创建成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchMaterials() // 重新加载列表
        } else {
          message.error('创建失败')
        }
      } else if (modalType === 'edit' && currentMaterial) {
        const response = await materialsService.updateMaterial(
          currentMaterial.id,
          formData as MaterialUpdate,
          currentWorkspace.type,
          currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
          currentWorkspace.factory_id
        )

        if (response.success) {
          message.success('更新成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchMaterials() // 重新加载列表
        } else {
          message.error('更新失败')
        }
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else if (error.errorFields) {
        message.error('请检查表单填写是否正确')
      } else {
        message.error('操作失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 处理模态框取消
  const handleModalCancel = () => {
    setIsModalVisible(false)
    form.resetFields()
    setCurrentMaterial(null)
  }

  // 获取统计数据
  const getMaterialsStats = () => {
    // 安全检查：确保materials是数组
    const materialsList = Array.isArray(materials) ? materials : []

    const totalValue = materialsList.reduce((sum, item) => sum + (item.current_stock * (item.unit_price || 0)), 0)
    const lowStockCount = materialsList.filter(item =>
      item.min_stock_level && item.current_stock < item.min_stock_level
    ).length

    return {
      totalTypes: total,
      totalValue,
      lowStock: lowStockCount,
      totalStock: materialsList.reduce((sum, item) => sum + item.current_stock, 0),
    }
  }

  const stats = getMaterialsStats()

  // 表格列定义
  const columns: ColumnsType<Material> = [
    {
      title: '焊材信息',
      key: 'material',
      width: 280,
      fixed: 'left',
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.material_name}</div>
          <div className="text-sm text-gray-500">编号: {record.material_code}</div>
          <div className="text-xs text-gray-400">
            {record.specification} {record.manufacturer && `· ${record.manufacturer}`}
          </div>
        </div>
      ),
    },
    {
      title: '类别',
      dataIndex: 'material_type',
      key: 'material_type',
      width: 100,
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: '当前库存',
      key: 'stock',
      width: 150,
      render: (_, record) => {
        const isLowStock = record.min_stock_level && record.current_stock < record.min_stock_level
        return (
          <div>
            <div className={`font-medium ${isLowStock ? 'text-red-600' : ''}`}>
              {record.current_stock} {record.unit}
            </div>
            {record.min_stock_level && (
              <div className="text-xs text-gray-500">
                最小: {record.min_stock_level} {record.unit}
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: '库存状态',
      key: 'status',
      width: 100,
      render: (_, record) => {
        const isLowStock = record.min_stock_level && record.current_stock < record.min_stock_level
        const isOutOfStock = record.current_stock === 0

        if (isOutOfStock) {
          return <Tag color="error" icon={<ExclamationCircleOutlined />}>缺货</Tag>
        } else if (isLowStock) {
          return <Tag color="warning" icon={<WarningOutlined />}>低库存</Tag>
        } else {
          return <Tag color="success" icon={<CheckCircleOutlined />}>正常</Tag>
        }
      },
    },
    {
      title: '单价',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 100,
      render: (price: number | undefined) => price ? `¥${price.toFixed(2)}` : '-',
    },
    {
      title: '存放位置',
      dataIndex: 'storage_location',
      key: 'storage_location',
      width: 120,
      render: (location: string | undefined) => location || '-',
    },
    {
      title: '供应商',
      dataIndex: 'supplier',
      key: 'supplier',
      width: 150,
      render: (supplier: string | undefined) => supplier || '-',
    },
    {
      title: '保质期',
      key: 'expiry',
      width: 120,
      render: (_, record) => {
        if (!record.expiry_date) return '-'

        const daysUntil = dayjs(record.expiry_date).diff(dayjs(), 'day')
        let color = 'text-gray-600'
        if (daysUntil < 0) color = 'text-red-600 font-medium'
        else if (daysUntil < 30) color = 'text-orange-600'

        return (
          <div className={color}>
            <div>{dayjs(record.expiry_date).format('YYYY-MM-DD')}</div>
            <div className="text-xs">
              {daysUntil < 0 ? '已过期' : `${daysUntil}天后过期`}
            </div>
          </div>
        )
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="入库">
            <Button
              type="text"
              size="small"
              icon={<ArrowDownOutlined />}
              style={{ color: '#52c41a' }}
              onClick={() => {
                setSelectedMaterial(record)
                setStockInVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title="出库">
            <Button
              type="text"
              size="small"
              icon={<ArrowUpOutlined />}
              style={{ color: '#ff4d4f' }}
              onClick={() => {
                setSelectedMaterial(record)
                setStockOutVisible(true)
              }}
            />
          </Tooltip>
          <Divider type="vertical" />
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
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">焊材管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="焊材总数"
                value={stats.totalTypes}
                valueStyle={{ color: '#1890ff' }}
                prefix={<BarcodeOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="库存总值"
                value={stats.totalValue}
                precision={2}
                prefix="¥"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="总库存量"
                value={stats.totalStock}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="库存不足"
                value={stats.lowStock}
                valueStyle={{ color: '#faad14' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* 预警信息 */}
        {stats.lowStock > 0 && (
          <Alert
            message={`有 ${stats.lowStock} 种焊材库存不足，请及时补货`}
            type="warning"
            showIcon
            closable
            className="mb-4"
          />
        )}
      </div>

      {/* 工具栏 */}
      <Card className="mb-4">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <Space size="middle" wrap>
            <Search
              placeholder="搜索焊材名称、编号"
              allowClear
              enterButton={<SearchOutlined />}
              style={{ width: 300 }}
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleSearch('')}
            />
            <Select
              placeholder="类别筛选"
              style={{ width: 120 }}
              allowClear
              onChange={(value) => handleFilterChange(value, lowStockFilter)}
            >
              <Option value="electrode">焊条</Option>
              <Option value="wire">焊丝</Option>
              <Option value="flux">焊剂</Option>
              <Option value="gas">保护气体</Option>
            </Select>
            <Select
              placeholder="库存状态"
              style={{ width: 120 }}
              allowClear
              onChange={(value) => handleFilterChange(materialTypeFilter, value)}
            >
              <Option value={true}>低库存</Option>
              <Option value={false}>正常</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchMaterials()}
            >
              刷新
            </Button>
          </Space>

          <Space>
            {selectedRowKeys.length > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBatchDelete}
              >
                批量删除 ({selectedRowKeys.length})
              </Button>
            )}
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新增焊材
            </Button>
          </Space>
        </div>
      </Card>

      {/* 焊材列表表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={Array.isArray(materials) ? materials : []}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page)
              setPageSize(size || 20)
            },
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 焊材详情/编辑/创建模态框 */}
      <Modal
        title={
          modalType === 'view' ? '焊材详情' :
          modalType === 'edit' ? '编辑焊材' :
          '新增焊材'
        }
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={
          modalType === 'view' ? [
            <Button key="close" onClick={handleModalCancel}>
              关闭
            </Button>,
          ] : [
            <Button key="cancel" onClick={handleModalCancel}>
              取消
            </Button>,
            <Button
              key="submit"
              type="primary"
              loading={loading}
              onClick={handleModalOk}
            >
              {modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={modalType === 'view' ? 900 : 800}
      >
        {modalType === 'view' && currentMaterial && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="焊材名称">{currentMaterial.material_name}</Descriptions.Item>
              <Descriptions.Item label="焊材编号">{currentMaterial.material_code}</Descriptions.Item>
              <Descriptions.Item label="类别">{currentMaterial.material_type}</Descriptions.Item>
              <Descriptions.Item label="规格">{currentMaterial.specification || '-'}</Descriptions.Item>
              <Descriptions.Item label="制造商">{currentMaterial.manufacturer || '-'}</Descriptions.Item>
              <Descriptions.Item label="批号">{currentMaterial.batch_number || '-'}</Descriptions.Item>
              <Descriptions.Item label="质量证书">{currentMaterial.quality_certificate || '-'}</Descriptions.Item>
              <Descriptions.Item label="单位">{currentMaterial.unit}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="库存信息" column={2} bordered>
              <Descriptions.Item label="当前库存">
                {currentMaterial.current_stock} {currentMaterial.unit}
              </Descriptions.Item>
              <Descriptions.Item label="最小库存">
                {currentMaterial.min_stock_level || '-'} {currentMaterial.min_stock_level ? currentMaterial.unit : ''}
              </Descriptions.Item>
              <Descriptions.Item label="补货点">
                {currentMaterial.reorder_point || '-'} {currentMaterial.reorder_point ? currentMaterial.unit : ''}
              </Descriptions.Item>
              <Descriptions.Item label="存放位置">{currentMaterial.storage_location || '-'}</Descriptions.Item>
              <Descriptions.Item label="单价">
                {currentMaterial.unit_price ? `¥${currentMaterial.unit_price.toFixed(2)}/${currentMaterial.unit}` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="总价值">
                {currentMaterial.unit_price ? `¥${(currentMaterial.current_stock * currentMaterial.unit_price).toFixed(2)}` : '-'}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="供应商信息" column={2} bordered>
              <Descriptions.Item label="供应商">{currentMaterial.supplier || '-'}</Descriptions.Item>
              <Descriptions.Item label="生产日期">
                {currentMaterial.production_date ? dayjs(currentMaterial.production_date).format('YYYY-MM-DD') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="到期日期">
                {currentMaterial.expiry_date ? dayjs(currentMaterial.expiry_date).format('YYYY-MM-DD') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(currentMaterial.created_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="备注" span={2}>{currentMaterial.notes || '-'}</Descriptions.Item>
            </Descriptions>
          </div>
        )}

        {(modalType === 'create' || modalType === 'edit') && (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="material_code"
                  label="焊材编号"
                  rules={[{ required: true, message: '请输入焊材编号' }]}
                >
                  <Input placeholder="请输入焊材编号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="material_name"
                  label="焊材名称"
                  rules={[{ required: true, message: '请输入焊材名称' }]}
                >
                  <Input placeholder="请输入焊材名称" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="material_type"
                  label="焊材类型"
                  rules={[{ required: true, message: '请选择焊材类型' }]}
                >
                  <Select placeholder="请选择焊材类型">
                    <Option value="electrode">焊条</Option>
                    <Option value="wire">焊丝</Option>
                    <Option value="flux">焊剂</Option>
                    <Option value="gas">保护气体</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="specification"
                  label="规格"
                >
                  <Input placeholder="请输入规格" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="manufacturer"
                  label="制造商"
                >
                  <Input placeholder="请输入制造商" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="supplier"
                  label="供应商"
                >
                  <Input placeholder="请输入供应商" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="current_stock"
                  label="当前库存"
                  rules={[{ required: true, message: '请输入当前库存' }]}
                >
                  <InputNumber
                    placeholder="请输入当前库存"
                    style={{ width: '100%' }}
                    min={0}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="unit"
                  label="单位"
                  rules={[{ required: true, message: '请输入单位' }]}
                >
                  <Input placeholder="如: kg, 支, 瓶" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="unit_price"
                  label="单价"
                >
                  <InputNumber
                    placeholder="请输入单价"
                    style={{ width: '100%' }}
                    min={0}
                    precision={2}
                    prefix="¥"
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="min_stock_level"
                  label="最小库存"
                >
                  <InputNumber
                    placeholder="请输入最小库存"
                    style={{ width: '100%' }}
                    min={0}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="reorder_point"
                  label="补货点"
                >
                  <InputNumber
                    placeholder="请输入补货点"
                    style={{ width: '100%' }}
                    min={0}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="storage_location"
                  label="存放位置"
                >
                  <Input placeholder="请输入存放位置" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="batch_number"
                  label="批号"
                >
                  <Input placeholder="请输入批号" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="production_date"
                  label="生产日期"
                >
                  <DatePicker style={{ width: '100%' }} placeholder="请选择生产日期" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="expiry_date"
                  label="到期日期"
                >
                  <DatePicker style={{ width: '100%' }} placeholder="请选择到期日期" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="quality_certificate"
              label="质量证书"
            >
              <Input placeholder="请输入质量证书编号" />
            </Form.Item>

            <Form.Item
              name="notes"
              label="备注"
            >
              <TextArea rows={3} placeholder="请输入备注信息" />
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* 入库弹窗 */}
      <StockInModal
        visible={stockInVisible}
        material={selectedMaterial}
        onCancel={() => {
          setStockInVisible(false)
          setSelectedMaterial(null)
        }}
        onSuccess={() => {
          setStockInVisible(false)
          setSelectedMaterial(null)
          fetchMaterials() // 刷新列表
        }}
      />

      {/* 出库弹窗 */}
      <StockOutModal
        visible={stockOutVisible}
        material={selectedMaterial}
        onCancel={() => {
          setStockOutVisible(false)
          setSelectedMaterial(null)
        }}
        onSuccess={() => {
          setStockOutVisible(false)
          setSelectedMaterial(null)
          fetchMaterials() // 刷新列表
        }}
      />
    </div>
  )
}

export default MaterialsList
