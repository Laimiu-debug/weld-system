import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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
  Modal,
  Descriptions,
  Spin,
} from 'antd'
import {
  SaveOutlined,
  EyeOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import weldersService from '@/services/welders'
import type { Welder } from '@/services/welders'
import dayjs from 'dayjs'

const { Title } = Typography
const { Option } = Select
const { Step } = Steps

interface WeldersEditForm {
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

const WeldersEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)
  const [currentStep, setCurrentStep] = useState(0)
  const [initialData, setInitialData] = useState<Welder | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)

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

  useEffect(() => {
    const fetchWelderDetail = async () => {
      if (!id) return
      setPageLoading(true)
      try {
        const response = await weldersService.getDetail(Number(id))
        const data = ((response as any)?.data || response) as Welder
        if (!data?.id) {
          message.error('未找到焊工信息')
          return
        }
        setInitialData(data)
        const processes = data.qualified_processes
          ? String(data.qualified_processes).split(',').map((item) => item.trim()).filter(Boolean)
          : []
        form.setFieldsValue({
          welder_code: data.welder_code,
          full_name: data.full_name,
          id_number: data.id_number,
          phone: data.phone,
          email: data.email,
          certification_number: data.primary_certification_number,
          certification_level: data.primary_certification_level,
          certification_date: data.primary_certification_date ? dayjs(data.primary_certification_date) : undefined,
          expiry_date: data.primary_expiry_date ? dayjs(data.primary_expiry_date) : undefined,
          issuing_authority: data.primary_issuing_authority,
          qualified_processes: processes,
          welding_position: data.qualified_positions,
          base_material: data.qualified_materials,
          notes: data.notes,
        })
      } catch {
        message.error('获取焊工信息失败')
      } finally {
        setPageLoading(false)
      }
    }
    void fetchWelderDetail()
  }, [id, form])

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
    if (!id) return
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      await weldersService.update(Number(id), {
        welder_code: values.welder_code,
        full_name: values.full_name,
        id_number: values.id_number,
        phone: values.phone,
        email: values.email,
        primary_certification_number: values.certification_number,
        primary_certification_level: values.certification_level,
        primary_certification_date: values.certification_date ? dayjs(values.certification_date).format('YYYY-MM-DD') : undefined,
        primary_expiry_date: values.expiry_date ? dayjs(values.expiry_date).format('YYYY-MM-DD') : undefined,
        primary_issuing_authority: values.issuing_authority,
        qualified_processes: Array.isArray(values.qualified_processes) ? values.qualified_processes.join(',') : values.qualified_processes,
        qualified_positions: values.welding_position,
        qualified_materials: values.base_material,
        notes: values.notes,
      })
      message.success('焊工信息更新成功')
      navigate(`/welders/${id}`)
    } catch {
      message.error('更新失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = () => {
    setPreviewOpen(true)
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

  if (pageLoading) {
    return (
      <div className="edit-welder-container flex justify-center items-center" style={{ minHeight: 320 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!initialData) {
    return <div>未找到焊工信息</div>
  }

  const previewValues = form.getFieldsValue()

  return (
    <div className="edit-welder-container">
      <div className="page-header">
        <Title level={2}>编辑焊工</Title>
      </div>

      <Card>
        {/* 步骤指示器 */}
        <Steps current={currentStep} className="steps-container">
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
            certification_date: initialData.primary_certification_date
              ? dayjs(initialData.primary_certification_date)
              : undefined,
            expiry_date: initialData.primary_expiry_date
              ? dayjs(initialData.primary_expiry_date)
              : undefined,
          }}
        >
          {renderStepForm()}
        </Form>

        {/* 操作按钮 */}
        <div className="form-actions">
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
              icon={<RightOutlined />}
              onClick={handleNext}
              loading={loading}
            >
              保存修改
            </Button>
          </Space>
        </div>
      </Card>

      <Modal
        title="焊工信息预览"
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={<Button onClick={() => setPreviewOpen(false)}>关闭</Button>}
      >
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="焊工编号">{previewValues.welder_code || '-'}</Descriptions.Item>
          <Descriptions.Item label="姓名">{previewValues.full_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="证件号">{previewValues.id_number || '-'}</Descriptions.Item>
          <Descriptions.Item label="电话">{previewValues.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="证书编号">{previewValues.certification_number || '-'}</Descriptions.Item>
          <Descriptions.Item label="资质等级">{previewValues.certification_level || '-'}</Descriptions.Item>
          <Descriptions.Item label="发证机构">{previewValues.issuing_authority || '-'}</Descriptions.Item>
          <Descriptions.Item label="合格工艺">
            {Array.isArray(previewValues.qualified_processes)
              ? previewValues.qualified_processes.join('、')
              : previewValues.qualified_processes || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Modal>
    </div>
  )
}

export default WeldersEdit