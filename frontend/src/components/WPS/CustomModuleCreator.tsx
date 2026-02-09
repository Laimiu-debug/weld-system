/**
 * 自定义模块创建器
 * 用于创建和编辑用户自定义的字段模块
 */
import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  Card,
  Row,
  Col,
  InputNumber,
  message,
  Divider,
  Tag,
  Collapse,
  Alert,
  Empty,
  Tabs,
  Radio
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  BlockOutlined,
  TableOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons'
import type { TabsProps } from 'antd'
import { FieldDefinition, FieldModule } from '@/types/wpsModules'
import customModuleService, { CustomModuleCreate } from '@/services/customModules'
import TableFieldEditor from './TableFieldEditor'
import ModuleFormRenderer from './ModuleFormRenderer'

const { TextArea } = Input
const { Option } = Select

interface FieldEditorProps {
  field: FieldDefinition & { key: string }
  onChange: (field: FieldDefinition & { key: string }) => void
  onDelete: () => void
}

const FieldEditor: React.FC<FieldEditorProps> = ({ field, onChange, onDelete }) => {
  return (
    <Card
      size="small"
      style={{ marginBottom: 16 }}
      extra={
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={onDelete}
        />
      }
    >
      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="字段键名" required>
            <Input
              value={field.key}
              onChange={(e) => onChange({ ...field, key: e.target.value })}
              placeholder="field_name"
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="字段标签" required>
            <Input
              value={field.label}
              onChange={(e) => onChange({ ...field, label: e.target.value })}
              placeholder="字段显示名称"
            />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="字段类型" required>
            <Select
              value={field.type}
              onChange={(value) => onChange({ ...field, type: value })}
            >
              <Option value="text">文本</Option>
              <Option value="number">数字</Option>
              <Option value="select">下拉选择</Option>
              <Option value="date">日期</Option>
              <Option value="textarea">多行文本</Option>
              <Option value="file">文件</Option>
              <Option value="image">图片</Option>
              <Option value="table">
                <TableOutlined /> 表格
              </Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={6}>
          <Form.Item label="单位">
            <Input
              value={field.unit}
              onChange={(e) => onChange({ ...field, unit: e.target.value })}
              placeholder="如: mm, °C"
            />
          </Form.Item>
        </Col>
        <Col span={6}>
          <Form.Item label="占位符">
            <Input
              value={field.placeholder}
              onChange={(e) => onChange({ ...field, placeholder: e.target.value })}
              placeholder="输入提示"
            />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item label="必填">
            <Switch
              checked={field.required}
              onChange={(checked) => onChange({ ...field, required: checked })}
            />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item label="只读">
            <Switch
              checked={field.readonly}
              onChange={(checked) => onChange({ ...field, readonly: checked })}
            />
          </Form.Item>
        </Col>
        <Col span={4}>
          <Form.Item label="多选">
            <Switch
              checked={field.multiple}
              onChange={(checked) => onChange({ ...field, multiple: checked })}
            />
          </Form.Item>
        </Col>
      </Row>

      {field.type === 'number' && (
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item label="最小值">
              <InputNumber
                value={field.min}
                onChange={(value) => onChange({ ...field, min: value || undefined })}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="最大值">
              <InputNumber
                value={field.max}
                onChange={(value) => onChange({ ...field, max: value || undefined })}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
      )}

      {field.type === 'select' && (
        <Form.Item label="选项（每行一个）">
          <TextArea
            value={field.options?.join('\n')}
            onChange={(e) =>
              onChange({
                ...field,
                options: e.target.value.split('\n').filter((o) => o.trim())
              })
            }
            rows={3}
            placeholder="选项1&#10;选项2&#10;选项3"
          />
        </Form.Item>
      )}

      {(field.type === 'file' || field.type === 'image') && (
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="接受的文件类型">
              <Input
                value={field.accept}
                onChange={(e) => onChange({ ...field, accept: e.target.value })}
                placeholder={field.type === 'image' ? 'image/*' : '.pdf,.doc,.docx'}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="最大文件大小 (MB)">
              <InputNumber
                value={field.maxSize ? field.maxSize / (1024 * 1024) : undefined}
                onChange={(value) => onChange({ ...field, maxSize: value ? value * 1024 * 1024 : undefined })}
                min={0}
                step={1}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
      )}

      {field.type === 'table' && (
        <div>
          <Divider style={{ margin: '12px 0' }}>表格设计</Divider>
          <TableFieldEditor
            value={field.tableDefinition}
            onChange={(tableDefinition) => onChange({ ...field, tableDefinition })}
          />
        </div>
      )}
    </Card>
  )
}

interface CustomModuleCreatorProps {
  visible: boolean
  onClose: () => void
  onSuccess?: () => void
  copyFromModule?: FieldModule | null
}

const CustomModuleCreator: React.FC<CustomModuleCreatorProps> = ({
  visible,
  onClose,
  onSuccess,
  copyFromModule
}) => {
  const [form] = Form.useForm()
  const [fields, setFields] = useState<(FieldDefinition & { key: string })[]>([])
  const [loading, setLoading] = useState(false)

  // 当 copyFromModule 改变时，初始化表单和字段
  useEffect(() => {
    if (visible && copyFromModule) {
      // 初始化表单
      form.setFieldsValue({
        name: `${copyFromModule.name}(副本)`,
        description: copyFromModule.description,
        icon: copyFromModule.icon,
        category: copyFromModule.category,
        module_type: 'wps',  // 默认为WPS类型
        repeatable: copyFromModule.repeatable,
        is_shared: false,
        access_level: 'private'
      })

      // 初始化字段
      const copiedFields = Object.entries(copyFromModule.fields).map(([key, field]) => ({
        key,
        ...field
      }))
      setFields(copiedFields)
    } else if (visible) {
      // 清空表单并设置默认值
      form.resetFields()
      form.setFieldsValue({
        module_type: 'wps',  // 默认为WPS类型
        category: 'basic',
        repeatable: false,
        is_shared: false,
        access_level: 'private'
      })
      setFields([])
    }
  }, [visible, copyFromModule, form])

  const handleAddField = () => {
    setFields([
      ...fields,
      {
        key: `field_${fields.length + 1}`,
        label: '',
        type: 'text',
        required: false,
        readonly: false
      }
    ])
  }

  const handleFieldChange = (index: number, field: FieldDefinition & { key: string }) => {
    const newFields = [...fields]
    newFields[index] = field
    setFields(newFields)
  }

  const handleFieldDelete = (index: number) => {
    setFields(fields.filter((_, i) => i !== index))
  }

  // 渲染编辑标签页
  const renderEditorTab = () => (
    <Form form={form} layout="vertical">
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="模块名称"
            name="name"
            rules={[{ required: true, message: '请输入模块名称' }]}
          >
            <Input placeholder="如: 预热参数" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="模块分类"
            name="category"
            rules={[{ required: true, message: '请选择模块分类' }]}
          >
            <Select placeholder="选择分类">
              <Option value="basic">基本信息</Option>
              <Option value="parameters">参数信息</Option>
              <Option value="materials">材料信息</Option>
              <Option value="tests">测试/试验</Option>
              <Option value="results">结果/评价</Option>
              <Option value="equipment">设备信息</Option>
              <Option value="attachments">附件</Option>
              <Option value="notes">备注</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={24}>
          <Form.Item
            label="适用类型"
            name="module_type"
            rules={[{ required: true, message: '请选择适用类型' }]}
            tooltip="选择此模块可用于哪种类型的记录。选择'通用'则可用于所有类型。"
          >
            <Radio.Group>
              <Radio value="wps">WPS（焊接工艺规程）</Radio>
              <Radio value="pqr">PQR（焊接工艺评定记录）</Radio>
              <Radio value="ppqr">pPQR（预焊接工艺评定记录）</Radio>
              <Radio value="common">通用（适用于所有类型）</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>
      </Row>

      <Form.Item label="模块描述" name="description">
        <TextArea rows={2} placeholder="简要描述模块的用途" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item label="图标" name="icon">
            <Input placeholder="如: FireOutlined" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="可重复" name="repeatable" valuePropName="checked">
            <Switch />
            <span style={{ marginLeft: 8, color: '#999' }}>用于多层多道焊</span>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item label="共享" name="is_shared" valuePropName="checked">
            <Switch />
            <span style={{ marginLeft: 8, color: '#999' }}>企业内共享</span>
          </Form.Item>
        </Col>
      </Row>

      <Divider>字段定义</Divider>

      {fields.map((field, index) => (
        <FieldEditor
          key={index}
          field={field}
          onChange={(newField) => handleFieldChange(index, newField)}
          onDelete={() => handleFieldDelete(index)}
        />
      ))}

      <Button
        type="dashed"
        block
        icon={<PlusOutlined />}
        onClick={handleAddField}
        style={{ marginBottom: 16 }}
      >
        添加字段
      </Button>

      {fields.length > 0 && (
        <Card size="small" title="字段预览">
          <Space wrap>
            {fields.map((field) => (
              <Tag
                key={field.key}
                color={field.type === 'table' ? 'purple' : 'blue'}
                icon={field.type === 'table' ? <TableOutlined /> : undefined}
              >
                {field.label || field.key} ({field.type})
                {field.unit && ` [${field.unit}]`}
                {field.required && ' *'}
                {field.type === 'table' && field.tableDefinition &&
                  ` (${field.tableDefinition.rows.length}行)`
                }
              </Tag>
            ))}
          </Space>
        </Card>
      )}
    </Form>
  )

  // 渲染预览标签页
  const renderPreviewTab = () => {
    if (fields.length === 0) {
      return <Empty description="请先添加字段" />
    }

    // 构建自定义字段对象
    const customFieldsObj: Record<string, FieldDefinition> = {}
    fields.forEach((field) => {
      const { key, ...fieldDef } = field
      customFieldsObj[key] = fieldDef
    })

    return (
      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
        <Form layout="vertical">
          <ModuleFormRenderer
            modules={[
              {
                instanceId: 'preview_custom',
                moduleId: 'custom_preview',
                order: 1,
                customName: form.getFieldValue('name') || '自定义模块'
              }
            ]}
            form={form}
            customFields={customFieldsObj}
          />
        </Form>
      </div>
    )
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (fields.length === 0) {
        message.error('请至少添加一个字段')
        return
      }

      // 转换字段格式
      const fieldsObject: Record<string, FieldDefinition> = {}
      fields.forEach((field) => {
        const { key, ...fieldDef } = field
        fieldsObject[key] = fieldDef
      })

      const moduleData: CustomModuleCreate = {
        name: values.name,
        description: values.description,
        icon: values.icon || 'BlockOutlined',
        module_type: values.module_type || 'wps',  // 添加module_type字段
        category: values.category,
        repeatable: values.repeatable || false,
        fields: fieldsObject,
        is_shared: values.is_shared || false,
        access_level: values.access_level || 'private'
      }

      setLoading(true)
      await customModuleService.createCustomModule(moduleData)
      message.success('自定义模块创建成功！')
      form.resetFields()
      setFields([])
      onSuccess?.()
      onClose()
    } catch (error: any) {
      console.error('创建模块失败:', error)
      message.error(error.response?.data?.detail || '创建模块失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={copyFromModule ? `复制模块: ${copyFromModule.name}` : "创建自定义模块"}
      open={visible}
      onCancel={onClose}
      width={900}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {copyFromModule ? '保存副本' : '创建模块'}
        </Button>
      ]}
    >
      {copyFromModule && (
        <Alert
          message="您正在复制预设模块"
          description={`模块名称已自动添加"(副本)"后缀，您可以修改名称和其他配置后保存`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        items={[
          {
            key: 'editor',
            label: '编辑',
            children: renderEditorTab()
          },
          {
            key: 'preview',
            label: '预览',
            disabled: fields.length === 0,
            children: renderPreviewTab()
          }
        ]}
      />
    </Modal>
  )
}

export default CustomModuleCreator

