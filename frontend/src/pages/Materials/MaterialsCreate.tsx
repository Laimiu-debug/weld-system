import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Form,
  Input,
  Button,
  Card,
  Row,
  Col,
  Select,
  InputNumber,
  Typography,
  Space,
  message,
  Steps,
  Modal,
  Descriptions,
  Alert,
} from 'antd'
import {
  SaveOutlined,
  EyeOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import { MaterialType } from '@/types'
import materialsService from '@/services/materials'
import { workspaceService } from '@/services/workspace'

const { Title } = Typography
const { Option } = Select
const { Step } = Steps

interface MaterialsCreateForm {
  // 基本信息
  material_code: string
  material_name: string
  material_type: MaterialType
  specification: string
  manufacturer: string
  
  // 库存信息
  current_stock: number
  unit: string
  min_stock_level: number
  storage_location: string
  
  // 价格信息
  unit_price: number
  currency: string
  
  // 其他信息
  notes: string
}

const MaterialsCreate: React.FC<{ editing?: boolean }> = ({ editing = false }) => {
  const [form] = Form.useForm<MaterialsCreateForm>()
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [previewData, setPreviewData] = useState<Partial<MaterialsCreateForm> | null>(null)
  const [initialLoading, setInitialLoading] = useState(editing)
  const [loadError, setLoadError] = useState('')
  const [retry, setRetry] = useState(0)
  const [workspace] = useState(() => workspaceService.getCurrentWorkspaceFromStorage())
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  useEffect(() => {
    if (!editing) return
    let active = true
    setInitialLoading(true)
    setLoadError('')
    form.resetFields()
    if (!workspace || !Number.isSafeInteger(Number(id)) || Number(id) <= 0) {
      setLoadError('请确认焊材编号并选择工作区')
      setInitialLoading(false)
      return
    }
    materialsService.getMaterialById(Number(id), workspace.type,
      workspace.type === 'enterprise' ? workspace.company_id : undefined, workspace.factory_id)
      .then(response => {
        if (!response.success || !response.data?.id) throw new Error('未返回焊材资料')
        if (active) form.setFieldsValue(response.data as MaterialsCreateForm)
      })
      .catch(() => { if (active) setLoadError('无法加载焊材，请返回列表确认记录和访问权限') })
      .finally(() => { if (active) setInitialLoading(false) })
    return () => { active = false }
  }, [editing, id, workspace, form, retry])

  // 步骤配置
  const steps = [
    {
      title: '基本信息',
      description: '填写焊材的基本信息',
    },
    {
      title: '库存信息',
      description: '设置库存相关信息',
    },
    {
      title: '价格信息',
      description: '设置价格相关信息',
    },
    {
      title: '其他信息',
      description: '填写其他备注信息',
    },
  ]

  // 处理步骤变化
  const handleStepChange = (step: number) => {
    setCurrentStep(step)
  }

  // 处理下一步
  const handleNext = async () => {
    try {
      // 验证当前步骤的表单
      const fields = getStepFields(currentStep)
      await form.validateFields(fields)
      
      
      // 进入下一步
      if (currentStep < steps.length - 1) {
        handleStepChange(currentStep + 1)
      } else {
        // 最后一步，提交表单
        await handleSubmit()
      }
    } catch (error) {
      message.error('请完成当前步骤的必填项')
    }
  }

  // 处理上一步
  const handlePrev = () => {
    if (currentStep > 0) {
      handleStepChange(currentStep - 1)
    }
  }

  // 获取当前步骤需要验证的字段
  const getStepFields = (step: number): string[] => {
    const stepFields: string[][] = [
      // 基本信息
      ['material_code', 'material_name', 'material_type', 'specification', 'manufacturer'],
      // 库存信息
      ['current_stock', 'unit', 'min_stock_level', 'storage_location'],
      // 价格信息
      ['unit_price', 'currency'],
      // 其他信息
      [],
    ]
    
    return stepFields[step] || []
  }

  // 处理表单提交
  const handleSubmit = async () => {
    if (!workspace) {
      message.warning('请先选择工作区')
      return
    }
    setLoading(true)
    try {
      const values = await form.validateFields()
      const companyId = workspace.type === 'enterprise' ? workspace.company_id : undefined
      const { current_stock: _stock, unit: _unit, ...updates } = values
      const response = editing
        ? await materialsService.updateMaterial(Number(id), updates, workspace.type, companyId, workspace.factory_id)
        : await materialsService.createMaterial(values, workspace.type, companyId, workspace.factory_id)
      if (!response.success || !response.data?.id) throw new Error('保存未成功')
      message.success(editing ? '焊材已更新' : '焊材添加成功')
      navigate(`/materials/${response.data.id}`)
    } catch (error) {
      const fields = (error as { errorFields?: { name: string[] }[] }).errorFields
      if (fields?.length) {
        const step = steps.findIndex((_, index) => getStepFields(index).includes(fields[0].name[0]))
        if (step >= 0) setCurrentStep(step)
      }
      message.error('保存失败，请检查填写内容后重试，已保留当前输入')
    } finally {
      setLoading(false)
    }
  }

  // 处理预览
  const handlePreview = () => {
    setPreviewData(form.getFieldsValue(true))
  }

  // 渲染当前步骤的表单
  const renderStepForm = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="material_code"
                label="焊材编号"
                rules={[{ required: true, message: '请输入焊材编号' }]}
              >
                <Input placeholder="例如: MAT-2024-001" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="material_name"
                label="焊材名称"
                rules={[{ required: true, message: '请输入焊材名称' }]}
              >
                <Input placeholder="请输入焊材名称" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
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
            <Col xs={24} sm={12}>
              <Form.Item
                name="specification"
                label="规格"
                rules={[{ required: true, message: '请输入规格' }]}
              >
                <Input placeholder="例如: 3.2mm" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="manufacturer"
                label="制造商"
                rules={[{ required: true, message: '请输入制造商' }]}
              >
                <Input placeholder="请输入制造商" />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 1:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="current_stock"
                label="当前库存"
                rules={[{ required: true, message: '请输入当前库存' }]}
              >
                <InputNumber
                  disabled={editing}
                  min={0}
                  precision={2}
                  placeholder="请输入当前库存"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit"
                label="单位"
                rules={[{ required: true, message: '请选择单位' }]}
              >
                <Select placeholder="请选择单位" disabled={editing}>
                  <Option value="kg">kg</Option>
                  <Option value="m">m</Option>
                  <Option value="L">L</Option>
                  <Option value="个">个</Option>
                  <Option value="瓶">瓶</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="min_stock_level"
                label="最低库存水平"
                rules={[{ required: true, message: '请输入最低库存水平' }]}
              >
                <InputNumber
                  min={0}
                  precision={2}
                  placeholder="请输入最低库存水平"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="storage_location"
                label="存储位置"
                rules={[{ required: true, message: '请输入存储位置' }]}
              >
                <Input placeholder="例如: A-01-03" />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 2:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit_price"
                label="单价"
                rules={[{ required: true, message: '请输入单价' }]}
              >
                <InputNumber
                  min={0}
                  precision={2}
                  placeholder="请输入单价"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="currency"
                label="货币"
                rules={[{ required: true, message: '请选择货币' }]}
              >
                <Select placeholder="请选择货币">
                  <Option value="CNY">人民币 (CNY)</Option>
                  <Option value="USD">美元 (USD)</Option>
                  <Option value="EUR">欧元 (EUR)</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 3:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Form.Item name="notes" label="备注">
                <Input.TextArea
                  rows={4}
                  placeholder="请输入其他备注信息"
                />
              </Form.Item>
            </Col>
          </Row>
        )
      
      default:
        return null
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Space><Button onClick={() => navigate('/materials')}>返回列表</Button>
          <Title level={2}>{editing ? '编辑焊材' : '添加焊材'}</Title></Space>
      </div>

      {loadError || !workspace ? <Alert type="error" showIcon message={loadError || '请先选择工作区'} action={workspace && <Button onClick={() => setRetry(value => value + 1)}>重试</Button>} /> : <Card loading={initialLoading}>
        <Alert type="info" showIcon message={`保存到工作区：${workspace.name || (workspace.type === 'personal' ? '个人工作区' : '企业工作区')}`} style={{ marginBottom: 16 }} />
        {editing && <Alert type="info" showIcon message="库存数量和单位不在此处修改；请在详情页办理入库或出库，以保留库存流水。" style={{ marginBottom: 16 }} />}
        {/* 步骤指示器 */}
        <Steps current={currentStep} className="mb-6">
          {steps.map((step, index) => (
            <Step
              key={index}
              title={step.title}
              description={step.description}
              icon={index < currentStep ? <CheckOutlined /> : undefined}
            />
          ))}
        </Steps>

        {/* 表单区域 */}
        <Form
          form={form}
          layout="vertical"
          disabled={loading}
          initialValues={{
            unit: 'kg',
            currency: 'CNY',
          }}
        >
          {steps.map((_, index) => <div key={index} hidden={index !== currentStep}>{renderStepForm(index)}</div>)}
        </Form>

        {/* 操作按钮 */}
        <div className="flex justify-between mt-6">
          <Button
            icon={<LeftOutlined />}
            onClick={handlePrev}
            disabled={currentStep === 0 || loading}
          >
            上一步
          </Button>

          <Space>
            <Button
              icon={<EyeOutlined />}
              onClick={handlePreview}
            >
              预览
            </Button>
            <Button
              type="primary"
              icon={currentStep === steps.length - 1 ? <SaveOutlined /> : <RightOutlined />}
              onClick={handleNext}
              loading={loading}
            >
              {currentStep === steps.length - 1 ? (editing ? '保存修改' : '添加焊材') : '下一步'}
            </Button>
          </Space>
        </div>
      </Card>}
      <Modal title="焊材信息预览" open={previewData !== null} onCancel={() => setPreviewData(null)} footer={<Button onClick={() => setPreviewData(null)}>继续填写</Button>}>
        <Descriptions bordered column={1} items={previewData ? [
          { key: 'code', label: '焊材编号', children: previewData.material_code || '—' },
          { key: 'name', label: '焊材名称', children: previewData.material_name || '—' },
          { key: 'type', label: '类型', children: ({ electrode: '焊条', wire: '焊丝', flux: '焊剂', gas: '保护气体' } as Record<string, string>)[previewData.material_type || ''] || '—' },
          { key: 'spec', label: '规格', children: previewData.specification || '—' },
          { key: 'maker', label: '制造商', children: previewData.manufacturer || '—' },
          { key: 'stock', label: '库存', children: `${previewData.current_stock ?? '—'} ${previewData.unit || ''}` },
          { key: 'min', label: '最低库存', children: previewData.min_stock_level ?? '—' },
          { key: 'location', label: '存储位置', children: previewData.storage_location || '—' },
          { key: 'price', label: '单价', children: `${previewData.unit_price ?? '—'} ${previewData.currency || ''}` },
          { key: 'notes', label: '备注', children: previewData.notes || '—' },
        ] : []} />
      </Modal>
    </div>
  )
}

export default MaterialsCreate
