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
  DatePicker,
  Typography,
  Space,
  message,
  Steps,
  Alert,
} from 'antd'
import {
  SaveOutlined,
  EyeOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import { PPQRRecord } from '@/types'
import { useAuthStore } from '@/store/authStore'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select
const { Step } = Steps

interface PPQRCreateForm {
  // 基本信息
  ppqr_number: string
  title: string
  planned_test_date: string
  
  // 预备工艺参数
  base_material: string
  base_material_thickness: number
  filler_material: string
  welding_process: string
  joint_type: string
  welding_position: string
  
  // 提议参数
  proposed_parameters: {
    current_range: string
    voltage_range: string
    travel_speed: string
    heat_input_range: string
  }
  
  // 评审信息
  review_comments: string
  notes: string
}

const PPQRCreate: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState<Partial<PPQRCreateForm>>({})
  const navigate = useNavigate()
  const { user } = useAuthStore()

  // 步骤配置
  const steps = [
    {
      title: '基本信息',
      description: '填写pPQR的基本信息',
    },
    {
      title: '工艺参数',
      description: '设置预备工艺参数',
    },
    {
      title: '建议参数',
      description: '输入建议的焊接参数',
    },
    {
      title: '评审信息',
      description: '填写评审相关信息',
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
      ['ppqr_number', 'title', 'planned_test_date'],
      // 工艺参数
      ['base_material', 'base_material_thickness', 'filler_material', 'welding_process', 'joint_type', 'welding_position'],
      // 建议参数
      ['proposed_parameters.current_range', 'proposed_parameters.voltage_range', 'proposed_parameters.travel_speed'],
      // 评审信息
      ['review_comments'],
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
      
      // 这里应该调用实际的API创建pPQR
      console.log('Creating PPQR with data:', finalData)
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      message.success('pPQR创建成功')
      navigate('/ppqr')
    } catch (error) {
      message.error('创建失败，请稍后重试')
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
                name="ppqr_number"
                label="pPQR编号"
                rules={[{ required: true, message: '请输入pPQR编号' }]}
              >
                <Input placeholder="例如: PPQR-2024-001" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="title"
                label="标题"
                rules={[{ required: true, message: '请输入标题' }]}
              >
                <Input placeholder="请输入pPQR标题" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="planned_test_date"
                label="计划测试日期"
                rules={[{ required: true, message: '请选择计划测试日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 1:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="base_material"
                label="母材"
                rules={[{ required: true, message: '请输入母材' }]}
              >
                <Input placeholder="例如: Q235" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="base_material_thickness"
                label="母材厚度 (mm)"
                rules={[{ required: true, message: '请输入母材厚度' }]}
              >
                <Input
                  type="number"
                  min={0}
                  step={0.1}
                  placeholder="请输入厚度"
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="filler_material"
                label="焊材"
                rules={[{ required: true, message: '请输入焊材' }]}
              >
                <Input placeholder="例如: E7018" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="welding_process"
                label="焊接方法"
                rules={[{ required: true, message: '请选择焊接方法' }]}
              >
                <Select placeholder="请选择焊接方法">
                  <Option value="SMAW">SMAW (手工焊)</Option>
                  <Option value="GMAW">GMAW (熔化极气体保护焊)</Option>
                  <Option value="GTAW">GTAW (钨极氩弧焊)</Option>
                  <Option value="FCAW">FCAW (药芯焊丝电弧焊)</Option>
                  <Option value="SAW">SAW (埋弧焊)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="joint_type"
                label="接头类型"
                rules={[{ required: true, message: '请选择接头类型' }]}
              >
                <Select placeholder="请选择接头类型">
                  <Option value="Butt Joint">对接接头</Option>
                  <Option value="T-Joint">T形接头</Option>
                  <Option value="Corner Joint">角接接头</Option>
                  <Option value="Lap Joint">搭接接头</Option>
                  <Option value="Edge Joint">边缘接头</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="welding_position"
                label="焊接位置"
                rules={[{ required: true, message: '请选择焊接位置' }]}
              >
                <Select placeholder="请选择焊接位置">
                  <Option value="1G">1G (平焊)</Option>
                  <Option value="2G">2G (横焊)</Option>
                  <Option value="3G">3G (立焊)</Option>
                  <Option value="4G">4G (仰焊)</Option>
                  <Option value="1F">1F (平角焊)</Option>
                  <Option value="2F">2F (横角焊)</Option>
                  <Option value="3F">3F (立角焊)</Option>
                  <Option value="4F">4F (仰角焊)</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 2:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Alert
                message="建议参数"
                description="请输入建议的焊接参数范围，这些参数将在正式PQR测试中使用。"
                type="info"
                showIcon
                className="mb-4"
              />
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name={['proposed_parameters', 'current_range']}
                label="电流范围"
                rules={[{ required: true, message: '请输入电流范围' }]}
              >
                <Input placeholder="例如: 90-130A" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name={['proposed_parameters', 'voltage_range']}
                label="电压范围"
                rules={[{ required: true, message: '请输入电压范围' }]}
              >
                <Input placeholder="例如: 22-28V" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name={['proposed_parameters', 'travel_speed']}
                label="焊接速度"
                rules={[{ required: true, message: '请输入焊接速度' }]}
              >
                <Input placeholder="例如: 3-5 cm/min" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name={['proposed_parameters', 'heat_input_range']}
                label="热输入范围"
              >
                <Input placeholder="例如: 0.8-1.5 kJ/mm" />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 3:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Form.Item
                name="review_comments"
                label="评审意见"
                rules={[{ required: true, message: '请输入评审意见' }]}
              >
                <TextArea
                  rows={4}
                  placeholder="请详细描述预备工艺的评审意见，包括技术可行性、风险评估等。"
                />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="notes" label="备注">
                <TextArea
                  rows={3}
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
        <Title level={2}>创建pPQR</Title>
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
            planned_test_date: dayjs(),
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
              {currentStep === steps.length - 1 ? '创建pPQR' : '下一步'}
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default PPQRCreate