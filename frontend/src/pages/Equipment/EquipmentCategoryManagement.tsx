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
  Popconfirm,
  Row,
  Col,
  Statistic,
  Divider,
  Tree,
  Typography,
  Badge,
  Select,
  InputNumber,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  SettingOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  ToolOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Search } = Input
const { Title, Text } = Typography
const { Option } = Select

interface EquipmentCategory {
  id: string
  name: string
  code: string
  parentId: string | null
  level: number
  description: string
  icon: string
  color: string
  equipmentCount: number
  maintenanceInterval: number
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
  children?: EquipmentCategory[]
}

interface CategoryStats {
  totalCategories: number
  activeCategories: number
  totalEquipment: number
  avgMaintenanceInterval: number
}

const EquipmentCategoryManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<EquipmentCategory[]>([])
  const [filteredCategories, setFilteredCategories] = useState<EquipmentCategory[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view'>('create')
  const [currentCategory, setCurrentCategory] = useState<EquipmentCategory | null>(null)
  const [form] = Form.useForm()
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([])
  const [viewMode, setViewMode] = useState<'tree' | 'table'>('tree')

  // 模拟数据
  useEffect(() => {
    generateMockData()
  }, [])

  const generateMockData = () => {
    const mockCategories: EquipmentCategory[] = [
      {
        id: '1',
        name: '焊接设备',
        code: 'EQP_WELD',
        parentId: null,
        level: 1,
        description: '各类焊接工艺设备，包括电弧焊、气体保护焊等',
        icon: 'tool',
        color: '#1890ff',
        equipmentCount: 15,
        maintenanceInterval: 90,
        status: 'active',
        createdAt: '2023-01-01',
        updatedAt: '2024-01-01',
        children: [
          {
            id: '11',
            name: '电弧焊机',
            code: 'EQP_WELD_ARC',
            parentId: '1',
            level: 2,
            description: '手工电弧焊、氩弧焊等设备',
            icon: 'thunderbolt',
            color: '#52c41a',
            equipmentCount: 8,
            maintenanceInterval: 60,
            status: 'active',
            createdAt: '2023-01-01',
            updatedAt: '2024-01-01',
            children: [
              {
                id: '111',
                name: '手工电弧焊机',
                code: 'EQP_WELD_ARC_MANUAL',
                parentId: '11',
                level: 3,
                description: '传统手工电弧焊设备',
                icon: 'edit',
                color: '#13c2c2',
                equipmentCount: 4,
                maintenanceInterval: 45,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
              {
                id: '112',
                name: '氩弧焊机',
                code: 'EQP_WELD_ARC_TIG',
                parentId: '11',
                level: 3,
                description: 'TIG焊接设备',
                icon: 'fire',
                color: '#722ed1',
                equipmentCount: 4,
                maintenanceInterval: 60,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
            ],
          },
          {
            id: '12',
            name: '气体保护焊机',
            code: 'EQP_WELD_GAS',
            parentId: '1',
            level: 2,
            description: 'CO2焊、MIG/MAG焊等设备',
            icon: 'cloud',
            color: '#fa8c16',
            equipmentCount: 7,
            maintenanceInterval: 75,
            status: 'active',
            createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
            ],
          },
          {
            id: '2',
            name: '切割设备',
            code: 'EQP_CUT',
            parentId: null,
            level: 1,
            description: '各类金属切割设备',
            icon: 'scissor',
            color: '#f5222d',
            equipmentCount: 8,
            maintenanceInterval: 120,
            status: 'active',
            createdAt: '2023-01-01',
            updatedAt: '2024-01-01',
            children: [
              {
                id: '21',
                name: '等离子切割机',
                code: 'EQP_CUT_PLASMA',
                parentId: '2',
                level: 2,
                description: '等离子切割设备',
                icon: 'bolt',
                color: '#fa541c',
                equipmentCount: 3,
                maintenanceInterval: 90,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
              {
                id: '22',
                name: '激光切割机',
                code: 'EQP_CUT_LASER',
                parentId: '2',
                level: 2,
                description: '激光切割设备',
                icon: 'aim',
                color: '#eb2f96',
                equipmentCount: 5,
                maintenanceInterval: 180,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
            ],
          },
          {
            id: '3',
            name: '检测设备',
            code: 'EQP_INSPECT',
            parentId: null,
            level: 1,
            description: '质量检测和无损检测设备',
            icon: 'search',
            color: '#13c2c2',
            equipmentCount: 6,
            maintenanceInterval: 365,
            status: 'active',
            createdAt: '2023-01-01',
            updatedAt: '2024-01-01',
            children: [
              {
                id: '31',
                name: '超声波检测设备',
                code: 'EQP_INSPECT_UT',
                parentId: '3',
                level: 2,
                description: '超声波探伤设备',
                icon: 'sound',
                color: '#2f54eb',
                equipmentCount: 3,
                maintenanceInterval: 180,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
              {
                id: '32',
                name: '射线检测设备',
                code: 'EQP_INSPECT_RT',
                parentId: '3',
                level: 2,
                description: 'X射线、γ射线检测设备',
                icon: 'camera',
                color: '#722ed1',
                equipmentCount: 3,
                maintenanceInterval: 365,
                status: 'active',
                createdAt: '2023-01-01',
                updatedAt: '2024-01-01',
              },
            ],
          },
          {
            id: '4',
            name: '辅助设备',
            code: 'EQP_AUX',
            parentId: null,
            level: 1,
            description: '焊接辅助设备和工装',
            icon: 'tool',
            color: '#8c8c8c',
            equipmentCount: 12,
            maintenanceInterval: 180,
            status: 'active',
            createdAt: '2023-01-01',
            updatedAt: '2024-01-01',
          },
        ]
      }

    setCategories(mockCategories)
    setFilteredCategories(mockCategories)

    // 设置默认展开的keys
    const allKeys = extractAllKeys(mockCategories)
    setExpandedKeys(allKeys)
  }

  const extractAllKeys = (categories: EquipmentCategory[]): React.Key[] => {
    let keys: React.Key[] = []
    categories.forEach(category => {
      keys.push(category.id)
      if (category.children && category.children.length > 0) {
        keys = keys.concat(extractAllKeys(category.children))
      }
    })
    return keys
  }

  const flattenCategories = (categories: EquipmentCategory[]): EquipmentCategory[] => {
    let result: EquipmentCategory[] = []
    categories.forEach(category => {
      result.push(category)
      if (category.children && category.children.length > 0) {
        result = result.concat(flattenCategories(category.children))
      }
    })
    return result
  }

  // 获取统计数据
  const getCategoryStats = (): CategoryStats => {
    const flatCategories = flattenCategories(categories)
    const activeCount = flatCategories.filter(cat => cat.status === 'active').length
    const totalEquipment = flatCategories.reduce((sum, cat) => sum + cat.equipmentCount, 0)
    const avgInterval = flatCategories.length > 0
      ? Math.round(flatCategories.reduce((sum, cat) => sum + cat.maintenanceInterval, 0) / flatCategories.length)
      : 0

    return {
      totalCategories: flatCategories.length,
      activeCategories: activeCount,
      totalEquipment,
      avgMaintenanceInterval: avgInterval,
    }
  }

  const stats = getCategoryStats()

  // 搜索过滤
  const handleSearch = (value: string) => {
    if (!value) {
      setFilteredCategories(categories)
      return
    }

    const filtered = flattenCategories(categories).filter(
      item =>
        item.name.toLowerCase().includes(value.toLowerCase()) ||
        item.code.toLowerCase().includes(value.toLowerCase()) ||
        item.description.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredCategories(filtered)
  }

  // 查看详情
  const handleView = (record: EquipmentCategory) => {
    setCurrentCategory(record)
    setModalType('view')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 编辑
  const handleEdit = (record: EquipmentCategory) => {
    setCurrentCategory(record)
    setModalType('edit')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 删除
  const handleDelete = (id: string) => {
    const deleteCategory = (categories: EquipmentCategory[]): EquipmentCategory[] => {
      return categories.filter(cat => {
        if (cat.id === id) return false
        if (cat.children) {
          cat.children = deleteCategory(cat.children)
        }
        return true
      })
    }

    const newCategories = deleteCategory(categories)
    setCategories(newCategories)
    setFilteredCategories(newCategories)
    message.success('删除成功')
  }

  // 获取树形数据
  const getTreeData = (categories: EquipmentCategory[]): any[] => {
    return categories.map(category => ({
      title: (
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: category.color }}
            />
            <span className="font-medium">{category.name}</span>
            <Badge count={category.equipmentCount} size="small" className="ml-2" />
          </div>
          <div className="flex items-center space-x-2">
            <Tag color={category.status === 'active' ? 'success' : 'default'}>
              {category.status === 'active' ? '启用' : '禁用'}
            </Tag>
          </div>
        </div>
      ),
      key: category.id,
      children: category.children && category.children.length > 0 ? getTreeData(category.children) : undefined,
      category,
    }))
  }

  // 表格列定义
  const columns: ColumnsType<EquipmentCategory> = [
    {
      title: '分类名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <div className="flex items-center">
          <div
            className="w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: record.color }}
          />
          <span className="font-medium">{name}</span>
          <Badge count={record.equipmentCount} size="small" className="ml-2" />
        </div>
      ),
    },
    {
      title: '分类编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: number) => (
        <Tag color="blue">L{level}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '设备数量',
      dataIndex: 'equipmentCount',
      key: 'equipmentCount',
      width: 100,
      render: (count: number) => (
        <Badge count={count} showZero color="#1890ff" />
      ),
    },
    {
      title: '维护周期',
      dataIndex: 'maintenanceInterval',
      key: 'maintenanceInterval',
      width: 120,
      render: (interval: number) => `${interval}天`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
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
              icon={<SettingOutlined />}
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
          <Popconfirm
            title="确认删除"
            description="确定要删除这个分类吗？删除后关联的设备将失去分类。"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (modalType === 'create') {
        const newCategory: EquipmentCategory = {
          ...values,
          id: Date.now().toString(),
          equipmentCount: 0,
          createdAt: dayjs().format('YYYY-MM-DD'),
          updatedAt: dayjs().format('YYYY-MM-DD'),
        }

        if (values.parentId) {
          // 添加到父分类下
          const addToParent = (categories: EquipmentCategory[]): EquipmentCategory[] => {
            return categories.map(cat => {
              if (cat.id === values.parentId) {
                return {
                  ...cat,
                  children: [...(cat.children || []), newCategory],
                }
              }
              if (cat.children) {
                return {
                  ...cat,
                  children: addToParent(cat.children),
                }
              }
              return cat
            })
          }
          const newCategories = addToParent(categories)
          setCategories(newCategories)
          setFilteredCategories(newCategories)
        } else {
          // 添加为顶级分类
          setCategories([...categories, newCategory])
          setFilteredCategories([...categories, newCategory])
        }

        message.success('创建成功')
      } else if (modalType === 'edit' && currentCategory) {
        const updateCategory = (categories: EquipmentCategory[]): EquipmentCategory[] => {
          return categories.map(cat => {
            if (cat.id === currentCategory.id) {
              return {
                ...cat,
                ...values,
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            }
            if (cat.children) {
              return {
                ...cat,
                children: updateCategory(cat.children),
              }
            }
            return cat
          })
        }
        const newCategories = updateCategory(categories)
        setCategories(newCategories)
        setFilteredCategories(newCategories)
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

  // 获取父级分类选项
  const getParentOptions = (categories: EquipmentCategory[], excludeId?: string): any[] => {
    const options: any[] = []
    categories.forEach(category => {
      if (category.id !== excludeId) {
        options.push({
          label: `${'　'.repeat(category.level - 1)}${category.name}`,
          value: category.id,
        })
        if (category.children) {
          options.push(...getParentOptions(category.children, excludeId))
        }
      }
    })
    return options
  }

  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <Title level={2} className="mb-4">设备分类管理</Title>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="分类总数"
                value={stats.totalCategories}
                valueStyle={{ color: '#1890ff' }}
                prefix={<ApartmentOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="启用分类"
                value={stats.activeCategories}
                valueStyle={{ color: '#52c41a' }}
                prefix={<FolderOpenOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="设备总数"
                value={stats.totalEquipment}
                valueStyle={{ color: '#722ed1' }}
                prefix={<SettingOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="平均维护周期"
                value={stats.avgMaintenanceInterval}
                suffix="天"
                valueStyle={{ color: '#fa8c16' }}
                prefix={<ToolOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* 工具栏 */}
      <Card className="mb-4">
        <div className="flex justify-between items-center">
          <Space size="middle">
            <Search
              placeholder="搜索分类名称、编码、描述"
              allowClear
              enterButton={<SearchOutlined />}
              style={{ width: 300 }}
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleSearch('')}
            />
            <Select
              value={viewMode}
              onChange={setViewMode}
              style={{ width: 120 }}
            >
              <Option value="tree">树形视图</Option>
              <Option value="table">表格视图</Option>
            </Select>
          </Space>

          <Space>
            <Button icon={<PlusOutlined />} type="primary" onClick={() => {
              setModalType('create')
              setIsModalVisible(true)
              form.resetFields()
            }}>
              新增分类
            </Button>
          </Space>
        </div>
      </Card>

      {/* 分类列表 */}
      <Card>
        {viewMode === 'tree' ? (
          <Tree
            treeData={getTreeData(categories)}
            expandedKeys={expandedKeys}
            onExpand={setExpandedKeys}
            selectedKeys={selectedKeys}
            onSelect={setSelectedKeys}
            showIcon
            icon={({ expanded }) =>
              expanded ? <FolderOpenOutlined /> : <FolderOutlined />
            }
          />
        ) : (
          <Table
            columns={columns}
            dataSource={flattenCategories(filteredCategories)}
            rowKey="id"
            loading={loading}
            pagination={{
              total: flattenCategories(filteredCategories).length,
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
            }}
            scroll={{ x: 1000 }}
          />
        )}
      </Card>

      {/* 分类详情/编辑模态框 */}
      <Modal
        title={
          modalType === 'view' ? '分类详情' :
          modalType === 'edit' ? '编辑分类' :
          '新增分类'
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
              {modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="请输入分类名称" disabled={modalType === 'view'} />
          </Form.Item>

          <Form.Item
            name="code"
            label="分类编码"
            rules={[{ required: true, message: '请输入分类编码' }]}
          >
            <Input placeholder="请输入分类编码" disabled={modalType === 'view'} />
          </Form.Item>

          <Form.Item
            name="parentId"
            label="父级分类"
          >
            <Select
              placeholder="请选择父级分类"
              allowClear
              disabled={modalType === 'view'}
            >
              {getParentOptions(categories, currentCategory?.id).map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入分类描述' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入分类描述" disabled={modalType === 'view'} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="maintenanceInterval"
                label="维护周期（天）"
                rules={[{ required: true, message: '请输入维护周期' }]}
              >
                <InputNumber
                  placeholder="请输入维护周期"
                  style={{ width: '100%' }}
                  min={1}
                  disabled={modalType === 'view'}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select disabled={modalType === 'view'}>
                  <Option value="active">启用</Option>
                  <Option value="inactive">禁用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default EquipmentCategoryManagement