import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form,
  Button,
  Card,
  Steps,
  Typography,
  Space,
  message,
  Alert,
} from 'antd'
import {
  SaveOutlined,
  LeftOutlined,
  RightOutlined,
  CheckOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import TemplateSelector from '@/components/WPS/TemplateSelector'
import TemplatePreview from '@/components/WPS/TemplatePreview'
import ModuleFormRenderer from '@/components/WPS/ModuleFormRenderer'
import { WPSTemplate } from '@/services/wpsTemplates'
import ppqrService from '@/services/ppqr'

const { Title, Text, Link } = Typography
const { Step } = Steps

const PPQRCreate: React.FC = () => {
  const navigate = useNavigate()
  const { canCreateMore } = useAuthStore()
  const [form] = Form.useForm()
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [selectedTemplate, setSelectedTemplate] = useState<WPSTemplate | null>(null)
  const [loading, setLoading] = useState(false)

  // 处理模板选择
  const handleTemplateChange = (templateId: string, template: WPSTemplate | null) => {
    setSelectedTemplateId(templateId)
    setSelectedTemplate(template)
    
    if (template) {
      message.success(`已选择模板: ${template.name}`)
    }
  }

  // 下一步
  const handleNext = () => {
    if (currentStep === 0) {
      if (!selectedTemplateId) {
        message.warning('请先选择一个模板')
        return
      }
      setCurrentStep(1)
    }
  }

  // 上一步
  const handlePrev = () => {
    setCurrentStep(currentStep - 1)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      setLoading(true)

      // 验证表单
      const values = await form.validateFields()

      console.log('表单验证通过，表单值:', values)

      // 构建模块数据
      const modulesData: Record<string, any> = {}

      if (selectedTemplate?.module_instances) {
        selectedTemplate.module_instances.forEach(instance => {
          const instanceId = instance.instanceId
          const moduleId = instance.moduleId
          const customName = instance.customName

          // 从表单值中提取该模块的数据
          const moduleFieldData: Record<string, any> = {}
          Object.keys(values).forEach(key => {
            if (key.startsWith(`${instanceId}_`)) {
              const fieldName = key.replace(`${instanceId}_`, '')
              moduleFieldData[fieldName] = values[key]
            }
          })

          modulesData[instanceId] = {
            moduleId,
            customName,
            rowIndex: instance.rowIndex,
            columnIndex: instance.columnIndex,
            data: moduleFieldData
          }
        })
      }

      // 从ppqr_basic_info模块中提取关键字段
      let ppqrNumber = ''
      let ppqrTitle = ''
      let ppqrRevision = 'A'

      Object.values(modulesData).forEach((module: any) => {
        if (module.moduleId === 'ppqr_basic_info' && module.data) {
          ppqrNumber = module.data.ppqr_number || ''
          ppqrTitle = module.data.title || ''
        }
      })

      // 构建提交数据
      const submitData = {
        template_id: selectedTemplateId,
        title: ppqrTitle || `pPQR-${Date.now()}`,
        ppqr_number: ppqrNumber || `pPQR-${Date.now()}`,
        revision: ppqrRevision,
        status: 'draft',
        module_data: modulesData
      }

      console.log('提交数据:', submitData)

      // 调用API创建pPQR
      const response = await ppqrService.create(submitData)

      console.log('API响应:', response)

      message.success('pPQR创建成功！')
      navigate(`/ppqr/${response.id}`)
    } catch (error: any) {
      console.error('创建pPQR失败:', error)

      // 处理表单验证错误
      if (error.errorFields) {
        const errorMessages = error.errorFields.map((field: any) => {
          const fieldName = field.name.join('.')
          const errors = field.errors.join(', ')
          return `${fieldName}: ${errors}`
        }).join('\n')

        console.error('表单验证错误:', errorMessages)
        message.error({
          content: (
            <div>
              <div>请检查表单填写是否完整：</div>
              <div style={{ marginTop: 8, fontSize: 12 }}>
                {error.errorFields.map((field: any, index: number) => (
                  <div key={index}>• {field.name.join('.')}: {field.errors.join(', ')}</div>
                ))}
              </div>
            </div>
          ),
          duration: 5
        })
      } else if (error.response?.data?.detail) {
        // 处理后端返回的验证错误
        const detail = error.response.data.detail
        let errorMsg = '创建pPQR失败'

        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => {
            const field = err.loc?.join('.') || '未知字段'
            return `${field}: ${err.msg}`
          }).join('; ')
        } else if (typeof detail === 'string') {
          errorMsg = detail
        }

        message.error(errorMsg)
      } else {
        message.error(error.message || '创建pPQR失败，请重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 步骤配置
  const steps = [
    {
      title: '选择模板',
      description: '选择pPQR模板',
    },
    {
      title: '填写信息',
      description: '填写pPQR详细信息',
    },
  ]

  return (
    <div className="ppqr-create-container" style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>创建pPQR</Title>
          <Text type="secondary">
            预焊接工艺评定记录 (Preliminary Procedure Qualification Record)
          </Text>
        </div>

        {/* 步骤指示器 */}
        <Steps current={currentStep} style={{ marginBottom: 32 }}>
          {steps.map(item => (
            <Step key={item.title} title={item.title} description={item.description} />
          ))}
        </Steps>

        {/* 步骤内容 */}
        <div className="steps-content">
          {/* 第一步：选择模板 */}
          {currentStep === 0 && (
            <div>
              <Alert
                message="选择pPQR模板"
                description="请选择一个pPQR模板作为基础。模板定义了需要填写的字段和模块。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />
              
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Button
                    type="dashed"
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/templates')}
                  >
                    创建自定义模板
                  </Button>
                </Space>
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>可用模板</Text>
                  <br />
                  <Text type="secondary">
                    如果没有找到合适的模板，您可以{' '}
                    <Link onClick={() => navigate('/templates')}>创建自定义模板</Link>
                    {' '}（根据会员等级有不同的配额限制）
                  </Text>
                </div>
              </div>

              <TemplateSelector
                value={selectedTemplateId}
                onChange={handleTemplateChange}
                moduleType="ppqr"
              />
            </div>
          )}

          {/* 第二步：填写表单 */}
          {currentStep === 1 && selectedTemplate && (
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Alert
                message="填写pPQR信息"
                description="请根据模板要求填写pPQR的详细信息。标记为必填的字段必须填写。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <div style={{ marginBottom: 24 }}>
                <TemplatePreview
                  template={selectedTemplate}
                />
              </div>

              <ModuleFormRenderer
                modules={selectedTemplate.module_instances || []}
                form={form}
                moduleType="ppqr"
              />
            </Form>
          )}
        </div>

        {/* 步骤操作按钮 */}
        <div className="steps-action" style={{ marginTop: 24 }}>
          <Space>
            {currentStep > 0 && (
              <Button icon={<LeftOutlined />} onClick={handlePrev}>
                上一步
              </Button>
            )}
            {currentStep === 0 && (
              <Button type="primary" icon={<RightOutlined />} onClick={handleNext}>
                下一步
              </Button>
            )}
            {currentStep === 1 && (
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={handleSubmit}
                loading={loading}
              >
                创建pPQR
              </Button>
            )}
            <Button onClick={() => navigate('/ppqr')}>
              取消
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default PPQRCreate

