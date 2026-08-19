/**
 * 模块表单渲染器
 * 根据模块实例动态渲染可编辑的表单字段
 */
import React from 'react'
import { Form, Input, InputNumber, Select, DatePicker, Upload, Button, Card, Space, Row, Col, FormInstance, Tag, Table, Checkbox } from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { ModuleInstance, FieldDefinition } from '@/types/wpsModules'
import { getModuleByIdAndType } from '@/constants/wpsModules'
import DiagramField from './DiagramField'
import WeldJointDiagramField from './WeldJointDiagramField'
import WeldJointDiagramV4Field from './WeldJointDiagramV4Field'
import TableFieldRenderer from './TableFieldRenderer'
import dayjs from 'dayjs'

interface ModuleFormRendererProps {
  modules: ModuleInstance[]
  form: FormInstance
  customFields?: Record<string, FieldDefinition>  // 用于预览自定义模块
  moduleType?: 'wps' | 'pqr' | 'ppqr'  // 模块类型，用于获取对应的模块定义
  useTemplateLayout?: boolean  // 是否使用模板的行列布局（默认true）
}

const ModuleFormRenderer: React.FC<ModuleFormRendererProps> = ({
  modules,
  form,
  customFields,
  moduleType = 'wps', // 默认为WPS类型
  useTemplateLayout = true // 默认使用模板布局
}) => {
  if (!modules || modules.length === 0) {
    return (
      <Card>
        <p>没有可用的模块</p>
      </Card>
    )
  }

  /**
   * 根据模块类型获取模块定义
   */
  const getModuleDefinition = (moduleId: string) => {
    return getModuleByIdAndType(moduleId, moduleType)
  }

  /**
   * 渲染单个字段
   */
  const renderField = (fieldKey: string, field: FieldDefinition, moduleId: string, instanceId: string) => {
    const fieldName = `${instanceId}_${fieldKey}`

    switch (field.type) {
      case 'text':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
          >
            <Input
              placeholder={field.placeholder}
              disabled={field.readonly}
              suffix={field.unit && <span style={{ fontSize: 12, color: '#999' }}>{field.unit}</span>}
            />
          </Form.Item>
        )

      case 'number':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
            initialValue={field.defaultValue || field.default}
          >
            <InputNumber
              placeholder={field.placeholder}
              disabled={field.readonly}
              min={field.min}
              max={field.max}
              step={field.step}
              style={{ width: '100%' }}
              addonAfter={field.unit}
            />
          </Form.Item>
        )

      case 'select':
        // 处理 options 格式
        const selectOptions = (field.options || []).map(opt => {
          if (typeof opt === 'string') {
            return { label: opt, value: opt }
          }
          return opt
        })

        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请选择${field.label}` }] : []}
            initialValue={field.defaultValue || field.default}
          >
            <Select
              placeholder={field.placeholder}
              disabled={field.readonly}
              options={selectOptions}
            />
          </Form.Item>
        )

      case 'checkbox':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            valuePropName="checked"
            initialValue={field.defaultValue || field.default || false}
          >
            <Checkbox disabled={field.readonly}>
              {field.description || field.label}
            </Checkbox>
          </Form.Item>
        )

      case 'date':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请选择${field.label}` }] : []}
          >
            <DatePicker
              disabled={field.readonly}
              style={{ width: '100%' }}
            />
          </Form.Item>
        )

      case 'textarea':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请输入${field.label}` }] : []}
          >
            <Input.TextArea
              placeholder={field.placeholder}
              disabled={field.readonly}
              rows={4}
            />
          </Form.Item>
        )

      case 'file':
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请上传${field.label}` }] : []}
          >
            <Upload
              disabled={field.readonly}
              maxCount={1}
              accept={field.accept}
            >
              <Button>上传文件</Button>
            </Upload>
          </Form.Item>
        )

      case 'image':
        // 检查是否是特殊的图表字段（坡口图、焊层焊道图或焊接接头示意图）
        const isGrooveDiagram = fieldKey === 'groove_diagram' || field.label.includes('坡口图')
        const isWeldLayerDiagram = fieldKey === 'weld_layer_diagram' || field.label.includes('焊层焊道图')
        const isWeldJointDiagram = fieldKey === 'joint_diagram' || field.label.includes('接头示意图')

        if (isGrooveDiagram || isWeldLayerDiagram) {
          // 使用增强的图表字段组件
          return (
            <Form.Item
              key={fieldName}
              name={fieldName}
              label={field.label}
              rules={field.required ? [{ required: true, message: `请上传${field.label}` }] : []}
            >
              <DiagramField
                diagramType={isGrooveDiagram ? 'groove' : 'weld_layer'}
                label={field.label}
                disabled={field.readonly}
              />
            </Form.Item>
          )
        }

        if (isWeldJointDiagram) {
          // 使用焊接接头示意图字段组件
          return (
            <Form.Item
              key={fieldName}
              name={fieldName}
              label={field.label}
              rules={field.required ? [{ required: true, message: `请上传${field.label}` }] : []}
            >
              <WeldJointDiagramField
                label={field.label}
                disabled={field.readonly}
              />
            </Form.Item>
          )
        }

        // 检查是否是焊接接头示意图V4字段
        const isWeldJointV4Diagram = fieldKey === 'generated_diagram' || field.label.includes('焊接接头示意图V4')

        if (isWeldJointV4Diagram) {
          return (
            <Form.Item
              key={fieldName}
              name={fieldName}
              label={field.label}
              rules={field.required ? [{ required: true, message: `请上传${field.label}` }] : []}
            >
              <WeldJointDiagramV4Field
                label={field.label}
                disabled={field.readonly}
                formValues={{}}
              />
            </Form.Item>
          )
        }

        // 普通图片字段
        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请上传${field.label}` }] : []}
          >
            <Upload
              disabled={field.readonly}
              maxCount={1}
              accept={field.accept || 'image/*'}
              listType="picture-card"
              beforeUpload={() => false}
            >
              <Button>上传图片</Button>
            </Upload>
          </Form.Item>
        )

      case 'table':
        // 表格字段
        if (!field.tableDefinition) {
          return (
            <Form.Item
              key={fieldName}
              label={field.label}
            >
              <div style={{ color: '#999' }}>表格未定义</div>
            </Form.Item>
          )
        }

        return (
          <Form.Item
            key={fieldName}
            name={fieldName}
            label={field.label}
            rules={field.required ? [{ required: true, message: `请填写${field.label}` }] : []}
          >
            <TableFieldRenderer
              tableDefinition={field.tableDefinition}
              readonly={field.readonly}
            />
          </Form.Item>
        )

      default:
        return null
    }
  }

  /**
   * 渲染模块卡片
   */
  const renderModuleCard = (instance: ModuleInstance) => {
    // 如果是自定义模块预览，使用 customFields
    if (customFields && instance.moduleId === 'custom_preview') {
      const displayName = instance.customName || '自定义模块'
      return (
        <Card
          key={instance.instanceId}
          title={
            <Space>
              <span>{displayName}</span>
              <Tag color="blue">{Object.keys(customFields).length} 个字段</Tag>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[16, 16]}>
            {Object.entries(customFields).map(([fieldKey, field]) => (
              <Col key={fieldKey} xs={24} sm={12} md={8}>
                {renderField(fieldKey, field, 'custom_preview', instance.instanceId)}
              </Col>
            ))}
          </Row>
        </Card>
      )
    }

    const module = getModuleDefinition(instance.moduleId)
    if (!module) {
      return null
    }

    const displayName = instance.customName || module.name

    // 特殊处理：焊接接头示意图生成器 V4
    if (module.id === 'weld_joint_diagram_v4') {
      return renderWeldJointV4Module(instance, module, displayName)
    }

    return (
      <Card
        key={instance.instanceId}
        title={
          <Space>
            <span>{displayName}</span>
            <Tag color="blue">{Object.keys(module.fields).length} 个字段</Tag>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[16, 16]}>
          {Object.entries(module.fields).map(([fieldKey, field]) => (
            <Col key={fieldKey} xs={24} sm={12} md={8}>
              {renderField(fieldKey, field, module.id, instance.instanceId)}
            </Col>
          ))}
        </Row>
      </Card>
    )
  }

  /**
   * 渲染焊接接头示意图生成器 V4 模块
   */
  const renderWeldJointV4Module = (instance: ModuleInstance, module: any, displayName: string) => {
    const fieldName = `${instance.instanceId}_generated_diagram`

    // 获取所有参数字段的值
    const getFormValue = (key: string) => {
      return form.getFieldValue(`${instance.instanceId}_${key}`)
    }

    return (
      <Card
        key={instance.instanceId}
        title={
          <Space>
            <span>{displayName}</span>
            <Tag color="purple">参数化生成器</Tag>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {/* 只显示生成的图片，隐藏所有参数字段 */}
        {/* 参数字段仍然存在于表单中，但不显示 */}
        <div style={{ display: 'none' }}>
          {Object.entries(module.fields)
            .filter(([key]) => key !== 'generated_diagram')
            .map(([fieldKey, field]) => (
              <div key={fieldKey}>
                {renderField(fieldKey, field as FieldDefinition, module.id, instance.instanceId)}
              </div>
            ))}
        </div>

        {/* 生成的图片区域 */}
        <Form.Item
          name={fieldName}
          label="焊接接头示意图"
        >
          <WeldJointDiagramV4Field
            label="焊接接头示意图"
            formValues={{
              grooveType: getFormValue('groove_type'),
              groovePosition: getFormValue('groove_position'),
              alignment: getFormValue('alignment'),
              leftThickness: getFormValue('left_thickness'),
              leftGrooveAngle: getFormValue('left_groove_angle'),
              leftGrooveDepth: getFormValue('left_groove_depth'),
              leftBevel: getFormValue('left_bevel'),
              leftBevelPosition: getFormValue('left_bevel_position'),
              leftBevelLength: getFormValue('left_bevel_length'),
              leftBevelHeight: getFormValue('left_bevel_height'),
              rightThickness: getFormValue('right_thickness'),
              rightGrooveAngle: getFormValue('right_groove_angle'),
              rightGrooveDepth: getFormValue('right_groove_depth'),
              rightBevel: getFormValue('right_bevel'),
              rightBevelPosition: getFormValue('right_bevel_position'),
              rightBevelLength: getFormValue('right_bevel_length'),
              rightBevelHeight: getFormValue('right_bevel_height'),
              bluntEdge: getFormValue('blunt_edge'),
              rootGap: getFormValue('root_gap'),
            }}
          />
        </Form.Item>
      </Card>
    )
  }

  /**
   * 按照模板布局渲染模块（支持多列）
   */
  const renderModulesWithLayout = () => {
    // 按行分组
    const rowGroups = new Map<number, ModuleInstance[]>()
    modules.forEach(instance => {
      const rowIndex = instance.rowIndex ?? 0
      if (!rowGroups.has(rowIndex)) {
        rowGroups.set(rowIndex, [])
      }
      rowGroups.get(rowIndex)!.push(instance)
    })

    // 按行索引排序
    const sortedRows = Array.from(rowGroups.entries()).sort((a, b) => a[0] - b[0])

    return (
      <div>
        {sortedRows.map(([rowIndex, rowModules]) => {
          // 按列索引排序
          const sortedModules = rowModules.sort((a, b) => (a.columnIndex ?? 0) - (b.columnIndex ?? 0))
          const columnCount = sortedModules.length

          if (columnCount === 1) {
            // 单列：全宽显示
            return (
              <div key={rowIndex} style={{ marginBottom: 16 }}>
                {renderModuleCard(sortedModules[0])}
              </div>
            )
          } else {
            // 多列：使用 Row 和 Col 布局
            const span = Math.floor(24 / columnCount)
            return (
              <Row key={rowIndex} gutter={16} style={{ marginBottom: 16 }}>
                {sortedModules.map((instance) => (
                  <Col key={instance.instanceId} span={span}>
                    {renderModuleCard(instance)}
                  </Col>
                ))}
              </Row>
            )
          }
        })}
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3>填写表单数据</h3>
        <p style={{ color: '#666', fontSize: 12 }}>请根据各模块的要求填写相应的信息</p>
      </div>
      {useTemplateLayout ? renderModulesWithLayout() : modules.map(instance => renderModuleCard(instance))}
    </div>
  )
}

export default ModuleFormRenderer

