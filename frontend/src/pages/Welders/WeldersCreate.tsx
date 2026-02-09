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
  Upload,
} from 'antd'
import {
  SaveOutlined,
  EyeOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { Welder } from '@/types'
import { useAuthStore } from '@/store/authStore'
import dayjs from 'dayjs'
import weldersService from '@/services/welders'

const { Title, Text } = Typography
const { Option } = Select
const { Step } = Steps

interface WeldersCreateForm {
  // 基本信息
  welder_code: string
  full_name: string
  id_number: string
  phone?: string
  email?: string
  
  // 资质信息
  certification_number: string
  certification_level: string
  certification_date: string
  expiry_date: string
  issuing_authority: string
  qualified_processes: string[]
  welding_position: string
  base_material: string
  thickness_range: string
  
  // 其他信息
  special_skills?: string
  notes: string
  attachments: any[]
}

const WeldersCreate: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState<Partial<WeldersCreateForm>>({})
  const navigate = useNavigate()
  const { user } = useAuthStore()

  // 步骤配置
  const steps = [
    {
      title: '基本信息',
      description: '填写焊工的基本信息',
    },
    {
      title: '资质信息',
      description: '填写焊工资质证书信息',
    },
    {
      title: '技能信息',
      description: '填写焊工技能范围',
    },
    {
      title: '附件上传',
      description: '上传相关证书和文件',
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
      ['welder_code', 'full_name', 'id_number', 'phone', 'email'],
      // 资质信息
      ['certification_number', 'certification_level', 'certification_date', 'expiry_date', 'issuing_authority'],
      // 技能信息
      ['qualified_processes', 'welding_position', 'base_material', 'thickness_range'],
      // 附件上传
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

      // 转换数据格式以匹配后端API
      const apiData = {
        welder_code: finalData.welder_code,
        full_name: finalData.full_name,
        english_name: finalData.english_name,
        gender: finalData.gender,
        date_of_birth: finalData.date_of_birth ? finalData.date_of_birth.format('YYYY-MM-DD') : undefined,

        // 身份信息
        id_type: finalData.id_type || '身份证',
        id_number: finalData.id_number,
        nationality: finalData.nationality || '中国',

        // 联系信息
        phone: finalData.phone,
        email: finalData.email,
        emergency_contact: finalData.emergency_contact,
        emergency_phone: finalData.emergency_phone,
        address: finalData.address,

        // 雇佣信息
        employee_number: finalData.employee_number,
        department: finalData.department,
        position: finalData.position,
        hire_date: finalData.hire_date ? finalData.hire_date.format('YYYY-MM-DD') : undefined,
        work_experience_years: finalData.work_experience_years,

        // 技能等级
        skill_level: finalData.skill_level,
        specialization: finalData.specialization,
        qualified_processes: finalData.qualified_processes ? JSON.stringify(finalData.qualified_processes) : undefined,
        qualified_positions: finalData.qualified_positions ? JSON.stringify(finalData.qualified_positions) : undefined,
        qualified_materials: finalData.qualified_materials ? JSON.stringify(finalData.qualified_materials) : undefined,

        // 主要证书信息
        primary_certification_number: finalData.certification_number,
        primary_certification_level: finalData.certification_level,
        primary_certification_date: finalData.certification_date ? finalData.certification_date.format('YYYY-MM-DD') : undefined,
        primary_expiry_date: finalData.expiry_date ? finalData.expiry_date.format('YYYY-MM-DD') : undefined,
        primary_issuing_authority: finalData.issuing_authority,

        // 状态信息
        status: 'active',
        certification_status: 'valid',

        // 附加信息
        description: finalData.special_skills,
        notes: finalData.notes,
        tags: finalData.tags,
      }

      // 调用API创建焊工
      const response = await weldersService.create(apiData)

      if (response.success) {
        message.success('焊工添加成功')
        navigate('/welders')
      } else {
        message.error(response.message || '添加失败')
      }
    } catch (error: any) {
      console.error('创建焊工失败:', error)
      message.error(error.response?.data?.detail || '添加失败，请稍后重试')
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

  // 处理文件上传
  const handleUploadChange = (info: any) => {
    if (info.file.status === 'done') {
      message.success(`${info.file.name} 上传成功`)
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 上传失败`)
    }
  }

  // 渲染当前步骤的表单
  const renderStepForm = () => {
    switch (currentStep) {
      case 0:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="welder_code"
                label="焊工编号"
                rules={[{ required: true, message: '请输入焊工编号' }]}
              >
                <Input placeholder="例如: WLD-2024-001" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="full_name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input placeholder="请输入姓名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="id_number"
                label="身份证号"
                rules={[
                  { required: true, message: '请输入身份证号' },
                  { pattern: /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/, message: '请输入有效的身份证号' }
                ]}
              >
                <Input placeholder="请输入身份证号" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="phone"
                label="联系电话"
                rules={[
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' }
                ]}
              >
                <Input placeholder="请输入联系电话" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 1:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="certification_number"
                label="证书编号"
                rules={[{ required: true, message: '请输入证书编号' }]}
              >
                <Input placeholder="请输入证书编号" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="certification_level"
                label="证书等级"
                rules={[{ required: true, message: '请选择证书等级' }]}
              >
                <Select placeholder="请选择证书等级">
                  <Option value="初级">初级</Option>
                  <Option value="中级">中级</Option>
                  <Option value="高级">高级</Option>
                  <Option value="技师">技师</Option>
                  <Option value="高级技师">高级技师</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="certification_date"
                label="发证日期"
                rules={[{ required: true, message: '请选择发证日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="expiry_date"
                label="有效期至"
                rules={[{ required: true, message: '请选择有效期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="issuing_authority"
                label="发证机构"
                rules={[{ required: true, message: '请输入发证机构' }]}
              >
                <Input placeholder="请输入发证机构" />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 2:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Form.Item
                name="qualified_processes"
                label="资质工艺"
                rules={[{ required: true, message: '请选择资质工艺' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="请选择资质工艺"
                  style={{ width: '100%' }}
                >
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
                  <Option value="6G">6G (全位置)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="base_material"
                label="母材"
                rules={[{ required: true, message: '请输入母材' }]}
              >
                <Input placeholder="例如: Q235" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="thickness_range"
                label="厚度范围"
                rules={[{ required: true, message: '请输入厚度范围' }]}
              >
                <Input placeholder="例如: 3-20mm" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="special_skills" label="特殊技能">
                <Input.TextArea
                  rows={2}
                  placeholder="请输入特殊技能"
                />
              </Form.Item>
            </Col>
          </Row>
        )
      
      case 3:
        return (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Form.Item
                name="attachments"
                label="附件上传"
              >
                <Upload.Dragger
                  name="files"
                  multiple
                  action="/api/upload"
                  onChange={handleUploadChange}
                >
                  <p className="ant-upload-drag-icon">
                    <UploadOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                  <p className="ant-upload-hint">
                    支持单个或批量上传。严格禁止上传公司数据或其他敏感信息。
                  </p>
                </Upload.Dragger>
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="notes" label="备注">
                <Input.TextArea
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
        <Title level={2}>添加焊工</Title>
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
            certification_date: dayjs(),
            expiry_date: dayjs().add(3, 'year'),
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
              {currentStep === steps.length - 1 ? '添加焊工' : '下一步'}
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default WeldersCreate