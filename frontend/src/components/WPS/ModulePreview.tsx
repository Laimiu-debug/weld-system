/**
 * 模块预览组件
 * 显示模块在实际 WPS 表单中的渲染效果
 */
import React from 'react'
import { Card, Form, Row, Col, Empty, Spin, Tag, Space, Divider, Typography, Descriptions } from 'antd'
import {
  FileTextOutlined,
  ToolOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  SettingOutlined,
  CalculatorOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { FieldModule } from '@/types/wpsModules'
import ModuleFormRenderer from './ModuleFormRenderer'
import { getModuleById } from '@/constants/wpsModules'

const { Text, Title } = Typography

interface ModulePreviewProps {
  module: FieldModule
  loading?: boolean
}

const ModulePreview: React.FC<ModulePreviewProps> = ({ module, loading = false }) => {
  const [form] = Form.useForm()

  if (!module) {
    return <Empty description="未选择模块" />
  }

  // 获取分类图标
  const getCategoryIcon = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      basic: <FileTextOutlined style={{ color: '#1890ff' }} />,
      material: <ToolOutlined style={{ color: '#52c41a' }} />,
      gas: <ExperimentOutlined style={{ color: '#faad14' }} />,
      electrical: <ThunderboltOutlined style={{ color: '#f5222d' }} />,
      motion: <DashboardOutlined style={{ color: '#722ed1' }} />,
      equipment: <SettingOutlined style={{ color: '#13c2c2' }} />,
      calculation: <CalculatorOutlined style={{ color: '#eb2f96' }} />
    }
    return iconMap[category] || <FileTextOutlined />
  }

  // 获取分类名称
  const getCategoryName = (category: string) => {
    const categoryMap: Record<string, string> = {
      basic: '基本信息',
      material: '材料信息',
      gas: '气体信息',
      electrical: '电气参数',
      motion: '运动参数',
      equipment: '设备信息',
      calculation: '计算结果'
    }
    return categoryMap[category] || category
  }

  // 获取字段类型标签颜色
  const getFieldTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      text: 'blue',
      number: 'green',
      select: 'orange',
      date: 'purple',
      textarea: 'cyan',
      file: 'magenta',
      image: 'red',
      table: 'geekblue'
    }
    return colorMap[type] || 'default'
  }

  // 检查是否是自定义模块（不在预设模块中）
  const isCustomModule = !getModuleById(module.id)

  // 将模块转换为模块实例格式以供 ModuleFormRenderer 使用
  const moduleInstances = [
    {
      instanceId: `preview_${module.id}`,
      moduleId: isCustomModule ? 'custom_preview' : module.id,
      order: 1,
      customName: module.name
    }
  ]

  return (
    <Spin spinning={loading}>
      <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        {/* 模块基本信息 */}
        <Card
          size="small"
          style={{ marginBottom: 16 }}
          styles={{ body: { padding: '16px' } }}
        >
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 标题行 */}
            <div>
              <Space size="middle">
                {getCategoryIcon(module.category)}
                <Title level={4} style={{ margin: 0 }}>
                  {module.name}
                </Title>
                <Tag color={isCustomModule ? 'purple' : 'blue'}>
                  {isCustomModule ? '自定义模块' : '预设模块'}
                </Tag>
                {module.repeatable && (
                  <Tag color="green" icon={<CheckCircleOutlined />}>
                    可重复
                  </Tag>
                )}
              </Space>
            </div>

            {/* 描述信息 */}
            <Descriptions column={2} size="small">
              <Descriptions.Item label="模块分类">
                <Tag color="default">{getCategoryName(module.category)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="字段数量">
                <Text strong>{Object.keys(module.fields).length}</Text> 个字段
              </Descriptions.Item>
              {module.description && (
                <Descriptions.Item label="模块描述" span={2}>
                  <Text type="secondary">{module.description}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* 字段列表 */}
            <div>
              <Text strong style={{ fontSize: 13 }}>字段列表：</Text>
              <div style={{ marginTop: 8 }}>
                <Space wrap>
                  {Object.entries(module.fields).map(([key, field]) => (
                    <Tag
                      key={key}
                      color={getFieldTypeColor(field.type)}
                      style={{ marginBottom: 4 }}
                    >
                      {field.label || key}
                      <Text type="secondary" style={{ fontSize: 11, marginLeft: 4 }}>
                        ({field.type})
                      </Text>
                      {field.required && <Text type="danger"> *</Text>}
                      {field.unit && <Text type="secondary"> [{field.unit}]</Text>}
                    </Tag>
                  ))}
                </Space>
              </div>
            </div>
          </Space>
        </Card>

        <Divider orientation="left" style={{ margin: '16px 0' }}>
          <Space>
            <FileTextOutlined />
            <Text strong>表单预览</Text>
          </Space>
        </Divider>

        {/* 表单预览 */}
        <Card
          size="small"
          title={
            <Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                以下是该模块在 WPS 表单中的实际渲染效果
              </Text>
            </Space>
          }
          styles={{ body: { padding: '16px', backgroundColor: '#fafafa' } }}
        >
          <Form form={form} layout="vertical">
            <ModuleFormRenderer
              modules={moduleInstances}
              form={form}
              customFields={isCustomModule ? module.fields : undefined}
            />
          </Form>
        </Card>
      </div>
    </Spin>
  )
}

export default ModulePreview

