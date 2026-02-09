import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
} from 'antd'
import {
  SaveOutlined,
  EyeOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import { WeldingMaterial, MaterialType } from '@/types'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography
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

const MaterialsCreate: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState<Partial<MaterialsCreateForm>>({})
  const navigate = useNavigate()
  const { user } = useAuthStore()

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
      
      // 保存当前步骤的数据
      const values = form.getFieldsValue(fields)
      setFormData(prev => ({ ...prev, ...values }))
      
      // 进入下一步
      if (currentStep < steps.length - 1) {
        handleStepChange(currentStep + 1)
      } else {
        // 最后一步，提交表单
        handleSubmit()
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
    setLoading(true)
    try {
      // 获取所有表单数据
      const allValues = form.getFieldsValue()
      const finalData = { ...formData, ...allValues }
      
      // 这里应该调用实际的API创建焊材
      console.log('Creating Material with data:', finalData)
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      message.success('焊材添加成功')
      navigate('/materials')
    } catch (error) {
      message.error('添加失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 处理预览
  const handlePreview = () => {
    const allValues = form.getFieldsValue()
    const previewData = { ...formData, ...allValues }
    
    // 这里可以打开一个预览模态框或新页面
    console.log('Preview data:', previewData)
    message.info('预览功能开发中')
  }

  // 渲染当前步骤的表单
  const renderStepForm = () => {
    switch (currentStep) {
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
                initialValue="kg"
              >
                <Select placeholder="请选择单位">
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
                  addonBefore="¥"
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="currency"
                label="货币"
                rules={[{ required: true, message: '请选择货币' }]}
                initialValue="CNY"
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
        <Title level={2}>添加焊材</Title>
      </div>

      <Card>
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
          initialValues={{
            unit: 'kg',
            currency: 'CNY',
          }}
        >
          {renderStepForm()}
        </Form>

        {/* 操作按钮 */}
        <div className="flex justify-between mt-6">
          <Button
            icon={<LeftOutlined />}
            onClick={handlePrev}
            disabled={currentStep === 0}
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
              {currentStep === steps.length - 1 ? '添加焊材' : '下一步'}
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default MaterialsCreate