/**
 * 模块卡片组件
 * 用于显示字段模块的信息
 */
import React from 'react'
import { Card, Tag, Space, Typography } from 'antd'
import {
  BlockOutlined,
  FireOutlined,
  ThunderboltOutlined,
  ToolOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  CalculatorOutlined
} from '@ant-design/icons'
import { FieldModule } from '@/types/wpsModules'

const { Text } = Typography

interface ModuleCardProps {
  module: FieldModule
  draggable?: boolean
  showDetails?: boolean
  extra?: React.ReactNode
}

const getCategoryIcon = (category: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    basic: <BlockOutlined />,
    material: <ExperimentOutlined />,
    gas: <FireOutlined />,
    electrical: <ThunderboltOutlined />,
    motion: <DashboardOutlined />,
    equipment: <ToolOutlined />,
    calculation: <CalculatorOutlined />
  }
  return iconMap[category] || <BlockOutlined />
}

const getCategoryColor = (category: string) => {
  const colorMap: Record<string, string> = {
    basic: 'blue',
    material: 'green',
    gas: 'cyan',
    electrical: 'orange',
    motion: 'purple',
    equipment: 'magenta',
    calculation: 'red'
  }
  return colorMap[category] || 'default'
}

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

const ModuleCard: React.FC<ModuleCardProps> = ({
  module,
  draggable = true,
  showDetails = true,
  extra
}) => {
  const fieldCount = Object.keys(module.fields).length

  return (
    <Card
      size="small"
      hoverable={draggable}
      style={{
        marginBottom: 8,
        cursor: draggable ? 'grab' : 'default',
        borderLeft: `3px solid ${getCategoryColor(module.category) === 'default' ? '#1890ff' : ''}`
      }}
      styles={{ body: { padding: '12px' } }}
      extra={extra}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* 模块标题 */}
        <Space>
          {getCategoryIcon(module.category)}
          <Text strong>{module.name}</Text>
          {module.repeatable && (
            <Tag color="green" style={{ fontSize: 11 }}>
              可重复
            </Tag>
          )}
        </Space>

        {/* 模块描述 */}
        {showDetails && module.description && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {module.description}
          </Text>
        )}

        {/* 模块信息 */}
        <Space wrap>
          <Tag color={getCategoryColor(module.category)} style={{ fontSize: 11 }}>
            {getCategoryName(module.category)}
          </Tag>
          <Tag color="blue" style={{ fontSize: 11 }}>
            {fieldCount} 个字段
          </Tag>
        </Space>
      </Space>
    </Card>
  )
}

export default ModuleCard

