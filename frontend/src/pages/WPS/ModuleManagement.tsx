/**
 * 模块管理页面
 * 用于管理预设模块和用户自定义模块
 */
import React, { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Button,
  Table,
  Space,
  Tag,
  message,
  Modal,
  Tabs,
  Descriptions,
  Badge,
  Tooltip,
  Input,
  Select,
  Row,
  Col,
  Statistic,
  Dropdown,
  Empty,
  Popconfirm
} from 'antd'
import type { TabsProps, MenuProps, TableColumnsType } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  BlockOutlined,
  FireOutlined,
  ThunderboltOutlined,
  ToolOutlined,
  ArrowLeftOutlined,
  CopyOutlined,
  ShareAltOutlined,
  SearchOutlined,
  FilterOutlined,
  MoreOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
  HolderOutlined,
  ExportOutlined,
  ImportOutlined
} from '@ant-design/icons'
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useNavigate } from 'react-router-dom'
import customModuleService, { CustomModuleSummary } from '@/services/customModules'
import { SharedLibraryService } from '@/services/sharedLibrary'
import CustomModuleCreator from '@/components/WPS/CustomModuleCreator'
import ModulePreview from '@/components/WPS/ModulePreview'
import { PRESET_MODULES, getModulesByCategory } from '@/constants/wpsModules'
import { FieldModule } from '@/types/wpsModules'

const { Search } = Input

// 可拖拽的表格行组件
interface DraggableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  'data-row-key': string
}

const DraggableRow: React.FC<DraggableRowProps> = (props) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: props['data-row-key'],
  })

  const style: React.CSSProperties = {
    ...props.style,
    transform: CSS.Transform.toString(transform),
    transition,
    cursor: 'move',
    ...(isDragging ? { position: 'relative', zIndex: 9999 } : {}),
  }

  return (
    <tr {...props} ref={setNodeRef} style={style} {...attributes} {...listeners} />
  )
}

const ModuleManagement: React.FC = () => {
  const navigate = useNavigate()
  const [customModules, setCustomModules] = useState<CustomModuleSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [creatorVisible, setCreatorVisible] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [previewModule, setPreviewModule] = useState<FieldModule | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [copyingModule, setCopyingModule] = useState<FieldModule | null>(null)

  // 搜索和筛选状态 - 自定义模块
  const [searchText, setSearchText] = useState<string>('')
  const [moduleTypeFilter, setModuleTypeFilter] = useState<string>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // 搜索和筛选状态 - 预设模块
  const [presetSearchText, setPresetSearchText] = useState<string>('')
  const [presetCategoryFilter, setPresetCategoryFilter] = useState<string>('all')

  // 分页状态
  const [pageSize, setPageSize] = useState<number>(10)
  const [currentPage, setCurrentPage] = useState<number>(1)

  // 排序状态
  const [sortField, setSortField] = useState<string>('')
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend' | null>(null)

  // 批量操作状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  // 拖拽排序状态
  const [isDragging, setIsDragging] = useState(false)
  const [customModulesOrder, setCustomModulesOrder] = useState<CustomModuleSummary[]>([])

  // 拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    loadCustomModules()
  }, [])

  const loadCustomModules = async () => {
    try {
      setLoading(true)
      const modules = await customModuleService.getCustomModules()
      setCustomModules(modules)
      setCustomModulesOrder(modules) // 初始化排序数组
    } catch (error) {
      console.error('加载自定义模块失败:', error)
      message.error('加载自定义模块失败')
    } finally {
      setLoading(false)
    }
  }

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的模块')
      return
    }

    Modal.confirm({
      title: '批量删除确认',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个模块吗？删除后无法恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await Promise.all(
            selectedRowKeys.map(id => customModuleService.deleteCustomModule(id as string))
          )
          message.success(`成功删除 ${selectedRowKeys.length} 个模块`)
          setSelectedRowKeys([])
          loadCustomModules()
        } catch (error: any) {
          console.error('批量删除失败:', error)
          message.error('批量删除失败')
        }
      }
    })
  }

  // 拖拽结束处理
  const handleDragEnd = (event: any) => {
    const { active, over } = event

    if (active.id !== over.id) {
      setCustomModulesOrder((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id)
        const newIndex = items.findIndex((item) => item.id === over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
      message.success('排序已更新')
    }
    setIsDragging(false)
  }

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个自定义模块吗？删除后无法恢复。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await customModuleService.deleteCustomModule(id)
          message.success('删除成功')
          loadCustomModules()
        } catch (error: any) {
          console.error('删除失败:', error)
          message.error(error.response?.data?.detail || '删除失败')
        }
      }
    })
  }

  const handlePreviewModule = async (module: FieldModule | any) => {
    // 如果是共享模块（有isShared标记），需要先获取完整详情
    if (module.isShared) {
      try {
        const fullModule = await customModuleService.getCustomModule(module.id)
        const fieldModule: FieldModule = {
          id: fullModule.id,
          name: fullModule.name,
          description: fullModule.description || '',
          icon: fullModule.icon,
          category: fullModule.category as any,
          repeatable: fullModule.repeatable,
          fields: fullModule.fields
        }
        setPreviewModule(fieldModule)
        setPreviewVisible(true)
      } catch (error) {
        console.error('加载共享模块详情失败:', error)
        message.error('加载共享模块详情失败')
      }
    } else {
      // 系统预设模块直接预览
      setPreviewModule(module)
      setPreviewVisible(true)
    }
  }

  const handleCopyModule = async (module: FieldModule | any) => {
    // 如果是共享模块（有isShared标记），需要先获取完整详情
    if (module.isShared) {
      try {
        const fullModule = await customModuleService.getCustomModule(module.id)
        const fieldModule: FieldModule = {
          id: fullModule.id,
          name: fullModule.name,
          description: fullModule.description || '',
          icon: fullModule.icon,
          category: fullModule.category as any,
          repeatable: fullModule.repeatable,
          fields: fullModule.fields
        }
        setCopyingModule(fieldModule)
        setCreatorVisible(true)
      } catch (error) {
        console.error('加载共享模块详情失败:', error)
        message.error('加载共享模块详情失败')
      }
    } else {
      // 系统预设模块直接复制
      setCopyingModule(module)
      setCreatorVisible(true)
    }
  }

  const handlePreviewCustomModule = async (id: string) => {
    try {
      const module = await customModuleService.getCustomModule(id)
      // 转换为 FieldModule 格式
      const fieldModule: FieldModule = {
        id: module.id,
        name: module.name,
        description: module.description || '',
        icon: module.icon,
        category: module.category as any,
        repeatable: module.repeatable,
        fields: module.fields
      }
      handlePreviewModule(fieldModule)
    } catch (error) {
      console.error('加载模块详情失败:', error)
      message.error('加载模块详情失败')
    }
  }

  const handleCopyCustomModule = async (id: string) => {
    try {
      const module = await customModuleService.getCustomModule(id)
      // 转换为 FieldModule 格式
      const fieldModule: FieldModule = {
        id: module.id,
        name: module.name,
        description: module.description || '',
        icon: module.icon,
        category: module.category as any,
        repeatable: module.repeatable,
        fields: module.fields
      }
      handleCopyModule(fieldModule)
    } catch (error) {
      console.error('加载模块详情失败:', error)
      message.error('加载模块详情失败')
    }
  }

  // 分享模块到共享库
  const handleShareModuleToLibrary = async (module: CustomModuleSummary) => {
    try {
      // 获取模块详情
      const moduleDetail = await customModuleService.getCustomModule(module.id)

      // 显示分享确认对话框
      Modal.confirm({
        title: '分享到共享库',
        content: (
          <div>
            <p>确定要将模块 "{module.name}" 分享到共享库吗？</p>
            <p style={{ color: '#666', fontSize: '12px' }}>
              分享后，其他用户可以浏览和下载您的模块。
            </p>
          </div>
        ),
        okText: '确认分享',
        cancelText: '取消',
        onOk: async () => {
          try {
            // 创建共享模块数据
            const sharedModuleData = {
              original_module_id: module.id,
              name: module.name,
              description: module.description || '',
              icon: module.icon,
              category: module.category,
              repeatable: module.repeatable,
              fields: moduleDetail.fields,
              tags: ['自定义模块', module.category],
              difficulty_level: 'beginner',
              changelog: '初始分享版本'
            }

            const response = await SharedLibraryService.shareModule(sharedModuleData)
            if (response.id) {
              message.success('分享成功！模块已提交到共享库等待审核。')

              // 显示成功信息
              setTimeout(() => {
                Modal.info({
                  title: '分享成功',
                  content: (
                    <div>
                      <p>您的模块已成功分享到共享库！</p>
                      <p>管理员审核通过后，其他用户就可以看到并使用您的模块了。</p>
                      <p style={{ marginTop: '16px' }}>
                        <Button
                          type="primary"
                          onClick={() => navigate('/shared-library')}
                        >
                          前往共享库
                        </Button>
                      </p>
                    </div>
                  ),
                  okText: '知道了'
                })
              }, 1000)
            }
          } catch (shareError: any) {
            message.error(shareError.response?.data?.detail || '分享失败，请稍后重试')
          }
        }
      })
    } catch (error) {
      message.error('分享失败，请稍后重试')
    }
  }

  const getCategoryName = (category: string) => {
    const categoryMap: Record<string, string> = {
      basic: '基本信息',
      parameters: '参数信息',
      materials: '材料信息',
      tests: '测试/试验',
      results: '结果/评价',
      equipment: '设备信息',
      attachments: '附件',
      notes: '备注',
      // 旧的分类（向后兼容）
      material: '材料信息',
      gas: '气体信息',
      electrical: '电气参数',
      motion: '运动参数',
      calculation: '计算结果'
    }
    return categoryMap[category] || category
  }

  const getCategoryColor = (category: string) => {
    const colorMap: Record<string, string> = {
      basic: 'blue',
      parameters: 'orange',
      materials: 'green',
      tests: 'purple',
      results: 'red',
      equipment: 'magenta',
      attachments: 'cyan',
      notes: 'default',
      // 旧的分类（向后兼容）
      material: 'green',
      gas: 'cyan',
      electrical: 'orange',
      motion: 'purple',
      calculation: 'red'
    }
    return colorMap[category] || 'default'
  }

  const getModuleTypeName = (moduleType: string) => {
    const typeMap: Record<string, string> = {
      wps: 'WPS',
      pqr: 'PQR',
      ppqr: 'pPQR',
      common: '通用'
    }
    return typeMap[moduleType] || moduleType
  }

  const getModuleTypeColor = (moduleType: string) => {
    const colorMap: Record<string, string> = {
      wps: 'blue',
      pqr: 'green',
      ppqr: 'orange',
      common: 'purple'
    }
    return colorMap[moduleType] || 'default'
  }

  // 筛选和排序后的自定义模块列表
  const filteredCustomModules = useMemo(() => {
    // 使用拖拽排序后的数组或原始数组
    const sourceModules = isDragging ? customModulesOrder : customModules

    let filtered = sourceModules.filter(module => {
      // 过滤掉共享模块（is_shared为true的应该显示在预设模块中）
      if (module.is_shared) return false

      // 搜索过滤
      const matchSearch = !searchText ||
        module.name.toLowerCase().includes(searchText.toLowerCase()) ||
        (module.description && module.description.toLowerCase().includes(searchText.toLowerCase()))

      // 类型过滤
      const matchType = moduleTypeFilter === 'all' || module.module_type === moduleTypeFilter

      // 分类过滤
      const matchCategory = categoryFilter === 'all' || module.category === categoryFilter

      return matchSearch && matchType && matchCategory
    })

    // 排序
    if (sortField && sortOrder) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField as keyof CustomModuleSummary]
        const bValue = b[sortField as keyof CustomModuleSummary]

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortOrder === 'ascend' ? aValue - bValue : bValue - aValue
        }

        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortOrder === 'ascend'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue)
        }

        return 0
      })
    }

    return filtered
  }, [customModules, customModulesOrder, isDragging, searchText, moduleTypeFilter, categoryFilter, sortField, sortOrder])

  // 筛选后的预设模块列表（包括共享模块）
  const filteredPresetModules = useMemo(() => {
    // 获取共享的自定义模块 - 注意：CustomModuleSummary只包含field_count,不包含完整的fields
    const sharedModules = customModules.filter(m => m.is_shared).map(m => ({
      id: m.id,
      name: m.name,
      description: m.description || '',
      category: m.category,
      module_type: m.module_type, // 保存模块类型
      fields: {}, // 占位符,实际字段数从field_count获取
      field_count: m.field_count, // 保存字段数量
      repeatable: m.repeatable,
      icon: m.icon || 'BlockOutlined',
      isShared: true // 标记为共享模块
    }))

    // 合并预设模块和共享模块
    const allPresetModules = [...PRESET_MODULES, ...sharedModules]

    return allPresetModules.filter(module => {
      // 搜索过滤
      const matchSearch = !presetSearchText ||
        module.name.toLowerCase().includes(presetSearchText.toLowerCase()) ||
        module.description.toLowerCase().includes(presetSearchText.toLowerCase())

      // 分类过滤
      const matchCategory = presetCategoryFilter === 'all' || module.category === presetCategoryFilter

      return matchSearch && matchCategory
    })
  }, [customModules, presetSearchText, presetCategoryFilter])

  // 自定义模块统计信息（不包括共享模块）
  const statistics = useMemo(() => {
    const nonSharedModules = customModules.filter(m => !m.is_shared)
    const total = nonSharedModules.length
    const byType = {
      wps: nonSharedModules.filter(m => m.module_type === 'wps').length,
      pqr: nonSharedModules.filter(m => m.module_type === 'pqr').length,
      ppqr: nonSharedModules.filter(m => m.module_type === 'ppqr').length,
      common: nonSharedModules.filter(m => m.module_type === 'common').length
    }
    return { total, byType }
  }, [customModules])

  // 预设模块统计信息（包括共享模块）
  const presetStatistics = useMemo(() => {
    const sharedCount = customModules.filter(m => m.is_shared).length
    const systemCount = PRESET_MODULES.length
    const total = systemCount + sharedCount
    const byCategory: Record<string, number> = {}

    // 统计系统模块
    PRESET_MODULES.forEach(m => {
      byCategory[m.category] = (byCategory[m.category] || 0) + 1
    })

    // 统计共享模块
    customModules.filter(m => m.is_shared).forEach(m => {
      byCategory[m.category] = (byCategory[m.category] || 0) + 1
    })

    return { total, systemCount, sharedCount, byCategory }
  }, [customModules])

  const customModuleColumns: TableColumnsType<CustomModuleSummary> = [
    {
      title: '',
      key: 'drag',
      width: 40,
      align: 'center' as const,
      render: () => <HolderOutlined style={{ cursor: 'move', color: '#999' }} />
    },
    {
      title: '模块名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      sorter: true,
      render: (text: string, record: CustomModuleSummary) => (
        <Space>
          <BlockOutlined style={{ color: '#1890ff' }} />
          <span style={{ fontWeight: 500 }}>{text}</span>
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: { showTitle: true }
    },
    {
      title: '适用类型',
      dataIndex: 'module_type',
      key: 'module_type',
      width: 100,
      align: 'center' as const,
      render: (moduleType: string) => (
        <Tag color={getModuleTypeColor(moduleType || 'wps')}>
          {getModuleTypeName(moduleType || 'wps')}
        </Tag>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      align: 'center' as const,
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{getCategoryName(category)}</Tag>
      )
    },
    {
      title: '字段数',
      dataIndex: 'field_count',
      key: 'field_count',
      width: 80,
      align: 'center' as const,
      sorter: true,
      render: (count: number) => (
        <Badge count={count} showZero color="#1890ff" />
      )
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 90,
      align: 'center' as const,
      sorter: true,
      render: (count: number) => (
        <Badge count={count} showZero color="#52c41a" />
      )
    },
    {
      title: '可重复',
      dataIndex: 'repeatable',
      key: 'repeatable',
      width: 80,
      align: 'center' as const,
      render: (repeatable: boolean) => (
        repeatable ? <Tag color="success" icon={<CheckCircleOutlined />}>是</Tag> : <Tag>否</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      align: 'center' as const,
      fixed: 'right' as const,
      render: (_: any, record: CustomModuleSummary) => {
        const menuItems: MenuProps['items'] = [
          {
            key: 'preview',
            icon: <EyeOutlined />,
            label: '预览',
            onClick: () => handlePreviewCustomModule(record.id)
          },
          {
            key: 'copy',
            icon: <CopyOutlined />,
            label: '复制',
            onClick: () => handleCopyCustomModule(record.id)
          },
          {
            key: 'share',
            icon: <ShareAltOutlined />,
            label: '分享到共享库',
            onClick: () => handleShareModuleToLibrary(record)
          },
          {
            type: 'divider'
          },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: '删除',
            danger: true,
            onClick: () => handleDelete(record.id)
          }
        ]

        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handlePreviewCustomModule(record.id)}
            >
              预览
            </Button>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button type="link" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        )
      }
    }
  ]

  const presetModuleColumns = [
    {
      title: '模块名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: any) => (
        <Space>
          <BlockOutlined style={{ color: record.isShared ? '#faad14' : '#52c41a' }} />
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.isShared ? (
            <Tag color="gold" icon={<ShareAltOutlined />}>共享</Tag>
          ) : (
            <Tag color="blue" icon={<AppstoreOutlined />}>系统</Tag>
          )}
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: { showTitle: true }
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      align: 'center' as const,
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{getCategoryName(category)}</Tag>
      )
    },
    {
      title: '字段数',
      key: 'field_count',
      width: 80,
      align: 'center' as const,
      render: (_: any, record: any) => {
        // 优先使用field_count属性(共享模块),否则计算fields对象的键数量(系统预设模块)
        const count = record.field_count !== undefined
          ? record.field_count
          : (record.fields ? Object.keys(record.fields).length : 0)
        return <Badge count={count} showZero color="#1890ff" />
      }
    },
    {
      title: '可重复',
      dataIndex: 'repeatable',
      key: 'repeatable',
      width: 80,
      align: 'center' as const,
      render: (repeatable: boolean) => (
        repeatable ? <Tag color="success" icon={<CheckCircleOutlined />}>是</Tag> : <Tag>否</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      align: 'center' as const,
      fixed: 'right' as const,
      render: (_: any, record: FieldModule) => {
        const menuItems: MenuProps['items'] = [
          {
            key: 'copy',
            icon: <CopyOutlined />,
            label: '复制为自定义',
            onClick: () => handleCopyModule(record)
          }
        ]

        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handlePreviewModule(record)}
            >
              预览
            </Button>
            <Dropdown menu={{ items: menuItems }} trigger={['click']}>
              <Button type="link" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        )
      }
    }
  ]

  // 构建 Tabs items
  const tabItems: TabsProps['items'] = [
    {
      key: 'preset',
      label: (
        <span>
          <AppstoreOutlined /> 预设模块
          <Badge count={presetStatistics.total} style={{ marginLeft: 8 }} showZero />
        </span>
      ),
      children: (
        <>
          {/* 统计信息卡片 */}
          <Row gutter={12} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card
                size="small"
                hoverable
                style={{
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  border: 'none'
                }}
              >
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>总模块数</span>}
                  value={presetStatistics.total}
                  prefix={<AppstoreOutlined style={{ color: '#fff' }} />}
                  valueStyle={{ color: '#fff', fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #1890ff' }}
              >
                <Statistic
                  title={<Tag color="blue" icon={<AppstoreOutlined />}>系统模块</Tag>}
                  value={presetStatistics.systemCount}
                  valueStyle={{ color: '#1890ff', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #faad14' }}
              >
                <Statistic
                  title={<Tag color="gold" icon={<ShareAltOutlined />}>共享模块</Tag>}
                  value={presetStatistics.sharedCount}
                  valueStyle={{ color: '#faad14', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #52c41a' }}
              >
                <Statistic
                  title="分类数"
                  value={Object.keys(presetStatistics.byCategory).length}
                  valueStyle={{ color: '#52c41a', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
          </Row>

          {/* 搜索和筛选 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16} align="middle">
              <Col span={10}>
                <Search
                  placeholder="搜索模块名称或描述"
                  allowClear
                  enterButton
                  value={presetSearchText}
                  onChange={(e) => setPresetSearchText(e.target.value)}
                  style={{ width: '100%' }}
                />
              </Col>
              <Col span={8}>
                <Select
                  placeholder="筛选分类"
                  allowClear
                  value={presetCategoryFilter === 'all' ? undefined : presetCategoryFilter}
                  onChange={(value) => setPresetCategoryFilter(value || 'all')}
                  style={{ width: '100%' }}
                  suffixIcon={<FilterOutlined />}
                >
                  <Select.Option value="basic">基本信息</Select.Option>
                  <Select.Option value="parameters">参数信息</Select.Option>
                  <Select.Option value="materials">材料信息</Select.Option>
                  <Select.Option value="tests">测试/试验</Select.Option>
                  <Select.Option value="results">结果/评价</Select.Option>
                  <Select.Option value="equipment">设备信息</Select.Option>
                  <Select.Option value="attachments">附件</Select.Option>
                  <Select.Option value="notes">备注</Select.Option>
                </Select>
              </Col>
              <Col span={6}>
                <Space>
                  <Button
                    onClick={() => {
                      setPresetSearchText('')
                      setPresetCategoryFilter('all')
                    }}
                    disabled={presetSearchText === '' && presetCategoryFilter === 'all'}
                  >
                    重置筛选
                  </Button>
                  <span style={{ color: '#999', fontSize: 12 }}>
                    {filteredPresetModules.length !== presetStatistics.total &&
                      `已筛选 ${filteredPresetModules.length}/${presetStatistics.total} 个模块`
                    }
                  </span>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 表格 */}
          <Table
            columns={presetModuleColumns as any}
            dataSource={filteredPresetModules}
            rowKey="id"
            pagination={{
              defaultPageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total) => `共 ${total} 个模块`
            }}
            scroll={{ x: 1200 }}
            size="middle"
            bordered
            rowClassName={(record, index) => index % 2 === 0 ? 'table-row-light' : 'table-row-dark'}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    presetSearchText || presetCategoryFilter !== 'all'
                      ? '没有找到符合条件的模块'
                      : '暂无预设模块'
                  }
                />
              )
            }}
          />
        </>
      )
    },
    {
      key: 'custom',
      label: (
        <span>
          <ToolOutlined /> 自定义模块
          <Badge count={statistics.total} style={{ marginLeft: 8 }} showZero />
        </span>
      ),
      children: (
        <>
          {/* 统计信息卡片 */}
          <Row gutter={12} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card
                size="small"
                hoverable
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none'
                }}
              >
                <Statistic
                  title={<span style={{ color: 'rgba(255,255,255,0.85)' }}>总模块数</span>}
                  value={statistics.total}
                  prefix={<BlockOutlined style={{ color: '#fff' }} />}
                  valueStyle={{ color: '#fff', fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #1890ff' }}
              >
                <Statistic
                  title={<Tag color="blue">WPS</Tag>}
                  value={statistics.byType.wps}
                  valueStyle={{ color: '#1890ff', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #52c41a' }}
              >
                <Statistic
                  title={<Tag color="green">PQR</Tag>}
                  value={statistics.byType.pqr}
                  valueStyle={{ color: '#52c41a', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={5}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #fa8c16' }}
              >
                <Statistic
                  title={<Tag color="orange">pPQR</Tag>}
                  value={statistics.byType.ppqr}
                  valueStyle={{ color: '#fa8c16', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
            <Col span={5}>
              <Card
                size="small"
                hoverable
                style={{ borderLeft: '3px solid #722ed1' }}
              >
                <Statistic
                  title={<Tag color="purple">通用</Tag>}
                  value={statistics.byType.common}
                  valueStyle={{ color: '#722ed1', fontSize: 24, fontWeight: 600 }}
                />
              </Card>
            </Col>
          </Row>

          {/* 搜索和筛选 */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Row gutter={16} align="middle">
                  <Col span={6}>
                    <Search
                      placeholder="搜索模块名称或描述"
                      allowClear
                      enterButton
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </Col>
                  <Col span={5}>
                    <Select
                      placeholder="筛选适用类型"
                      allowClear
                      value={moduleTypeFilter === 'all' ? undefined : moduleTypeFilter}
                      onChange={(value) => setModuleTypeFilter(value || 'all')}
                      style={{ width: '100%' }}
                      suffixIcon={<FilterOutlined />}
                    >
                      <Select.Option value="wps">
                        <Tag color="blue" style={{ marginRight: 4 }}>WPS</Tag>
                      </Select.Option>
                      <Select.Option value="pqr">
                        <Tag color="green" style={{ marginRight: 4 }}>PQR</Tag>
                      </Select.Option>
                      <Select.Option value="ppqr">
                        <Tag color="orange" style={{ marginRight: 4 }}>pPQR</Tag>
                      </Select.Option>
                      <Select.Option value="common">
                        <Tag color="purple" style={{ marginRight: 4 }}>通用</Tag>
                      </Select.Option>
                    </Select>
                  </Col>
                  <Col span={5}>
                    <Select
                      placeholder="筛选分类"
                      allowClear
                      value={categoryFilter === 'all' ? undefined : categoryFilter}
                      onChange={(value) => setCategoryFilter(value || 'all')}
                      style={{ width: '100%' }}
                      suffixIcon={<FilterOutlined />}
                    >
                      <Select.Option value="basic">基本信息</Select.Option>
                      <Select.Option value="parameters">参数信息</Select.Option>
                      <Select.Option value="materials">材料信息</Select.Option>
                      <Select.Option value="tests">测试/试验</Select.Option>
                      <Select.Option value="results">结果/评价</Select.Option>
                      <Select.Option value="equipment">设备信息</Select.Option>
                      <Select.Option value="attachments">附件</Select.Option>
                      <Select.Option value="notes">备注</Select.Option>
                    </Select>
                  </Col>
                  <Col span={5}>
                    <Select
                      placeholder="排序方式"
                      allowClear
                      value={sortField ? `${sortField}_${sortOrder}` : undefined}
                      onChange={(value) => {
                        if (!value) {
                          setSortField('')
                          setSortOrder(null)
                        } else {
                          const [field, order] = value.split('_')
                          setSortField(field)
                          setSortOrder(order as 'ascend' | 'descend')
                        }
                      }}
                      style={{ width: '100%' }}
                      suffixIcon={<SortAscendingOutlined />}
                    >
                      <Select.Option value="name_ascend">
                        <SortAscendingOutlined /> 名称升序
                      </Select.Option>
                      <Select.Option value="name_descend">
                        <SortDescendingOutlined /> 名称降序
                      </Select.Option>
                      <Select.Option value="field_count_ascend">
                        <SortAscendingOutlined /> 字段数升序
                      </Select.Option>
                      <Select.Option value="field_count_descend">
                        <SortDescendingOutlined /> 字段数降序
                      </Select.Option>
                      <Select.Option value="usage_count_ascend">
                        <SortAscendingOutlined /> 使用次数升序
                      </Select.Option>
                      <Select.Option value="usage_count_descend">
                        <SortDescendingOutlined /> 使用次数降序
                      </Select.Option>
                    </Select>
                  </Col>
                  <Col span={3}>
                    <Button
                      onClick={() => {
                        setSearchText('')
                        setModuleTypeFilter('all')
                        setCategoryFilter('all')
                        setSortField('')
                        setSortOrder(null)
                        setCurrentPage(1)
                      }}
                      disabled={searchText === '' && moduleTypeFilter === 'all' && categoryFilter === 'all' && !sortField}
                      block
                    >
                      重置
                    </Button>
                  </Col>
                </Row>
              </Col>
              <Col span={24}>
                <Row justify="space-between" align="middle">
                  <Col>
                    <Space>
                      <Popconfirm
                        title="批量删除确认"
                        description={`确定要删除选中的 ${selectedRowKeys.length} 个模块吗？`}
                        onConfirm={handleBatchDelete}
                        okText="确定"
                        cancelText="取消"
                        disabled={selectedRowKeys.length === 0}
                      >
                        <Button
                          danger
                          icon={<DeleteOutlined />}
                          disabled={selectedRowKeys.length === 0}
                        >
                          批量删除 {selectedRowKeys.length > 0 && `(${selectedRowKeys.length})`}
                        </Button>
                      </Popconfirm>
                      <Button
                        icon={isDragging ? <CheckCircleOutlined /> : <HolderOutlined />}
                        onClick={() => setIsDragging(!isDragging)}
                      >
                        {isDragging ? '完成排序' : '拖拽排序'}
                      </Button>
                    </Space>
                  </Col>
                  <Col>
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {filteredCustomModules.length !== statistics.total &&
                        `已筛选 ${filteredCustomModules.length}/${statistics.total} 个模块`
                      }
                      {selectedRowKeys.length > 0 && ` | 已选择 ${selectedRowKeys.length} 个`}
                    </span>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>

          {/* 表格 */}
          {isDragging ? (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
              onDragStart={() => setIsDragging(true)}
            >
              <SortableContext
                items={filteredCustomModules.map(m => m.id)}
                strategy={verticalListSortingStrategy}
              >
                <Table
                  columns={customModuleColumns}
                  dataSource={filteredCustomModules}
                  rowKey="id"
                  loading={loading}
                  pagination={false}
                  size="middle"
                  bordered
                  components={{
                    body: {
                      row: DraggableRow,
                    },
                  }}
                  rowClassName={(record, index) => index % 2 === 0 ? 'table-row-light' : 'table-row-dark'}
                />
              </SortableContext>
            </DndContext>
          ) : (
            <Table
              columns={customModuleColumns}
              dataSource={filteredCustomModules}
              rowKey="id"
              loading={loading}
              rowSelection={{
                selectedRowKeys,
                onChange: (keys) => setSelectedRowKeys(keys),
                selections: [
                  Table.SELECTION_ALL,
                  Table.SELECTION_INVERT,
                  Table.SELECTION_NONE,
                ],
              }}
              pagination={{
                current: currentPage,
                pageSize: pageSize,
                showSizeChanger: true,
                showQuickJumper: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                showTotal: (total) => `共 ${total} 个模块`,
                onChange: (page, size) => {
                  setCurrentPage(page)
                  if (size !== pageSize) {
                    setPageSize(size)
                    setCurrentPage(1) // 改变每页条数时回到第一页
                  }
                }
              }}
              size="middle"
              bordered
              rowClassName={(record, index) => index % 2 === 0 ? 'table-row-light' : 'table-row-dark'}
              onRow={(record) => ({
                style: { cursor: 'pointer' },
                onClick: (e) => {
                  // 如果点击的是操作按钮，不触发行点击
                  const target = e.target as HTMLElement
                  if (!target.closest('.ant-btn') && !target.closest('.ant-dropdown')) {
                    handlePreviewCustomModule(record.id)
                  }
                }
              })}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      searchText || moduleTypeFilter !== 'all' || categoryFilter !== 'all'
                        ? '没有找到符合条件的模块'
                        : '暂无自定义模块，点击上方"创建自定义模块"按钮开始创建'
                    }
                  />
                )
              }}
            />
          )}
        </>
      )
    }
  ]

  return (
    <>
      <style>{`
        .table-row-light {
          background-color: #ffffff;
        }
        .table-row-dark {
          background-color: #fafafa;
        }
        .ant-table-tbody > tr:hover > td {
          background-color: #e6f7ff !important;
        }
        .ant-table-tbody > tr {
          transition: all 0.3s;
        }
      `}</style>
      <div style={{ padding: 24, background: '#f0f2f5', minHeight: '100vh' }}>
        <Card
        title={
          <Space>
            <BlockOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <span style={{ fontSize: 18, fontWeight: 600 }}>模块管理</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/templates')}
            >
              返回模板管理
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setCopyingModule(null)
                setCreatorVisible(true)
              }}
              size="middle"
            >
              创建自定义模块
            </Button>
          </Space>
        }
        bordered={false}
        style={{ boxShadow: '0 1px 2px 0 rgba(0,0,0,0.03), 0 1px 6px -1px rgba(0,0,0,0.02), 0 2px 4px 0 rgba(0,0,0,0.02)' }}
      >
        <Tabs
          defaultActiveKey="preset"
          items={tabItems}
          size="large"
        />
      </Card>

      {/* 模块预览模态框 */}
      <Modal
        title={null}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={1000}
        footer={null}
        styles={{ body: { padding: '24px' } }}
      >
        {previewModule && <ModulePreview module={previewModule} />}
      </Modal>

      <CustomModuleCreator
        visible={creatorVisible}
        onClose={() => {
          setCreatorVisible(false)
          setCopyingModule(null)
        }}
        onSuccess={loadCustomModules}
        copyFromModule={copyingModule}
      />
      </div>
    </>
  )
}

export default ModuleManagement

