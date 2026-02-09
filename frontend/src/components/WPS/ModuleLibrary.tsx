/**
 * 模块库组件
 * 显示所有可用的字段模块
 */
import React, { useState, useEffect } from 'react'
import { Card, Input, Space, Spin, Tabs, Empty, message } from 'antd'
import type { TabsProps } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useDraggable } from '@dnd-kit/core'
import { PRESET_MODULES, getAllCategories, setCustomModulesCache } from '@/constants/wpsModules'
import { PQR_PRESET_MODULES } from '@/constants/pqrModules'
import { PPQR_PRESET_MODULES } from '@/constants/ppqrModules'
import customModuleService, { CustomModuleSummary, CustomModuleResponse } from '@/services/customModules'
import { FieldModule } from '@/types/wpsModules'
import ModuleCard from './ModuleCard'

interface DraggableModuleCardProps {
  module: FieldModule
  moduleType: string
}

const DraggableModuleCard: React.FC<DraggableModuleCardProps> = ({ module, moduleType }) => {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `${moduleType}-${module.id}`, // 使用带类型前缀的唯一 ID
    data: module // 传递原始模块数据（不带前缀）
  })

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1
      }
    : undefined

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <ModuleCard module={module} draggable={true} />
    </div>
  )
}

interface ModuleLibraryProps {
  onModuleSelect?: (moduleId: string) => void
  moduleType?: 'wps' | 'pqr' | 'ppqr' // 模块类型，用于显示对应的预设模块
}

const ModuleLibrary: React.FC<ModuleLibraryProps> = ({
  onModuleSelect,
  moduleType = 'wps' // 默认为WPS类型
}) => {
  const [customModules, setCustomModules] = useState<CustomModuleSummary[]>([])
  const [customModulesDetail, setCustomModulesDetail] = useState<CustomModuleResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('all')

  useEffect(() => {
    loadCustomModules()
  }, [])

  const loadCustomModules = async () => {
    try {
      setLoading(true)
      // 先获取模块列表
      const modules = await customModuleService.getCustomModules()
      setCustomModules(modules)

      // 再获取每个模块的完整详情(包括字段定义)
      const detailPromises = modules.map(m => customModuleService.getCustomModule(m.id))
      const details = await Promise.all(detailPromises)
      setCustomModulesDetail(details)
    } catch (error) {
      console.error('加载自定义模块失败:', error)
      message.error('加载自定义模块失败')
    } finally {
      setLoading(false)
    }
  }

  // 转换自定义模块为FieldModule格式(使用完整的字段定义)
  const convertedCustomModules: FieldModule[] = customModulesDetail.map((m) => ({
    id: m.id,
    name: m.name,
    description: m.description || '',
    icon: m.icon,
    category: m.category as any,
    repeatable: m.repeatable,
    fields: m.fields || {} // 使用完整的字段定义
  }))

  // 更新全局缓存,以便在模板画布中使用
  useEffect(() => {
    setCustomModulesCache(convertedCustomModules)
  }, [customModulesDetail])

  // 根据模块类型选择预设模块
  const getPresetModules = () => {
    switch (moduleType) {
      case 'pqr':
        return PQR_PRESET_MODULES
      case 'ppqr':
        return PPQR_PRESET_MODULES
      default:
        return PRESET_MODULES
    }
  }

  // 合并所有模块 - 使用Map去重，以moduleId为key
  const presetModules = getPresetModules()
  const moduleMap = new Map<string, FieldModule>()

  // 先添加预设模块
  presetModules.forEach(module => {
    moduleMap.set(module.id, module)
  })

  // 再添加自定义模块（不会覆盖预设模块）
  convertedCustomModules.forEach(module => {
    if (!moduleMap.has(module.id)) {
      moduleMap.set(module.id, module)
    }
  })

  const allModules = Array.from(moduleMap.values())

  // 过滤模块
  const filteredModules = allModules.filter((m) => {
    const matchSearch =
      searchText === '' ||
      m.name.toLowerCase().includes(searchText.toLowerCase()) ||
      m.description?.toLowerCase().includes(searchText.toLowerCase())

    const matchCategory = activeCategory === 'all' || m.category === activeCategory

    return matchSearch && matchCategory
  })

  // 按分类分组 - 从当前所有模块中获取分类，而不是只从WPS模块
  const categories = Array.from(new Set(allModules.map(m => m.category)))
  const modulesByCategory: Record<string, FieldModule[]> = {}
  categories.forEach((cat) => {
    modulesByCategory[cat] = filteredModules.filter((m) => m.category === cat)
  })

  const getCategoryName = (category: string) => {
    const nameMap: Record<string, string> = {
      basic: '基本信息',
      material: '材料信息',
      gas: '气体信息',
      electrical: '电气参数',
      motion: '运动参数',
      equipment: '设备信息',
      calculation: '计算结果'
    }
    return nameMap[category] || category
  }

  // 渲染模块列表
  const renderModuleList = (modules: FieldModule[], tabKey: string) => (
    <Spin spinning={loading}>
      <div style={{ maxHeight: 500, overflow: 'auto', paddingRight: 8 }}>
        {modules.length === 0 ? (
          <Empty description="没有找到模块" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          modules.map((module) => (
            <DraggableModuleCard
              key={`${moduleType}-${tabKey}-${module.id}`}
              module={module}
              moduleType={moduleType}
            />
          ))
        )}
      </div>
    </Spin>
  )

  // 构建 Tabs items
  const tabItems: TabsProps['items'] = [
    {
      key: 'all',
      label: '全部',
      children: renderModuleList(filteredModules, 'all')
    },
    ...categories.map((category) => ({
      key: category,
      label: getCategoryName(category),
      children: renderModuleList(modulesByCategory[category] || [], category)
    }))
  ]

  return (
    <Card
      title="模块库"
      size="small"
      styles={{ body: { padding: '12px' } }}
      style={{ height: '100%' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 搜索框 */}
        <Input
          prefix={<SearchOutlined />}
          placeholder="搜索模块..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />

        {/* 分类标签 */}
        <Tabs
          activeKey={activeCategory}
          onChange={setActiveCategory}
          size="small"
          tabPosition="top"
          items={tabItems}
        />

        {/* 提示信息 */}
        <div style={{ fontSize: 12, color: '#999', textAlign: 'center' }}>
          拖拽模块到右侧画布
        </div>
      </Space>
    </Card>
  )
}

export default ModuleLibrary

