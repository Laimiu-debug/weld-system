/**
 * 基于模板的PQR创建页面
 * 使用动态表单根据选择的模板渲染不同的字段
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form,
  Button,
  Card,
  Space,
  message,
  Steps,
  Typography,
  Spin,
  Alert
} from 'antd'
import {
  LeftOutlined,
  CheckOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  PlusOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import TemplateSelector from '@/components/WPS/TemplateSelector'
import TemplatePreview from '@/components/WPS/TemplatePreview'
import ModuleFormRenderer from '@/components/WPS/ModuleFormRenderer'
import { WPSTemplate } from '@/services/wpsTemplates'
import { getPQRModuleById } from '@/constants/pqrModules'
import pqrService from '@/services/pqr'

const { Title, Text, Link } = Typography

const PQRCreate: React.FC = () => {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { user } = useAuthStore()

  // 状态
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>()
  const [selectedTemplate, setSelectedTemplate] = useState<WPSTemplate | null>(null)
  const [loading, setLoading] = useState(false)

  // 步骤配置
  const steps = [
    {
      title: '选择模板',
      description: '选择PQR模板',
      icon: <FileTextOutlined />
    },
    {
      title: '填写数据',
      description: '根据模板填写PQR数据',
      icon: <ExperimentOutlined />
    }
  ]

  /**
   * 处理模板选择
   */
  const handleTemplateChange = (templateId: string, template: WPSTemplate | null) => {
    setSelectedTemplateId(templateId)
    setSelectedTemplate(template)

    // 如果模板有默认值，设置到表单
    if (template?.default_values) {
      form.setFieldsValue(template.default_values)
    }
  }

  /**
   * 处理下一步
   */
  const handleNext = async () => {
    if (currentStep === 0) {
      // 第一步：验证是否选择了模板
      if (!selectedTemplateId || !selectedTemplate) {
        message.error('请先选择PQR模板')
        return
      }
      setCurrentStep(1)
    } else {
      // 第二步：提交表单
      await handleSubmit()
    }
  }

  /**
   * 处理上一步
   */
  const handlePrev = () => {
    setCurrentStep(currentStep - 1)
  }

  /**
   * 提交表单
   */
  const handleSubmit = async () => {
    try {
      setLoading(true)

      // 验证表单
      const values = await form.validateFields()

      // 新架构：直接保存所有模块数据到 module_data
      // 结构: { "module_instance_id": { "module_id": "xxx", "custom_name": "xxx", "data": {...} }, ... }
      const modulesData: Record<string, any> = {}
      let pqrNumber = ''
      let pqrTitle = ''
      let pqrRevision = 'A'

      if (selectedTemplate?.module_instances) {
        selectedTemplate.module_instances.forEach(instance => {
          const moduleData: Record<string, any> = {}
          const module = getPQRModuleById(instance.moduleId)

          if (module) {
            Object.keys(module.fields).forEach(fieldKey => {
              const formFieldName = `${instance.instanceId}_${fieldKey}`
              // 只包含有值的字段
              if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
                moduleData[fieldKey] = values[formFieldName]

                // 从 pqr_basic_info 模块中提取 pqr_number, title
                if (instance.moduleId === 'pqr_basic_info') {
                  if (fieldKey === 'pqr_number') {
                    pqrNumber = values[formFieldName]
                  } else if (fieldKey === 'title') {
                    pqrTitle = values[formFieldName]
                  }
                }
              }
            })
          }

          // 将模块数据存储到 module_data，使用 instanceId 作为 key
          if (Object.keys(moduleData).length > 0) {
            modulesData[instance.instanceId] = {
              moduleId: instance.moduleId,
              customName: instance.customName,
              rowIndex: instance.rowIndex,
              columnIndex: instance.columnIndex,
              data: moduleData
            }
          }
        })
      }

      // 构建提交数据 - 基于模块化结构
      const submitData: any = {
        template_id: selectedTemplateId,
        title: pqrTitle || `PQR-${Date.now()}`,
        pqr_number: pqrNumber || `PQR-${Date.now()}`,
        test_date: new Date().toISOString(),  // 添加默认试验日期
        qualification_result: 'pending',  // 添加默认评定结果
      }

      // 添加 modules_data 到提交数据
      if (Object.keys(modulesData).length > 0) {
        submitData.modules_data = modulesData
      }

      console.log('提交数据:', submitData)

      // 调用API创建PQR
      const response = await pqrService.create(submitData)

      message.success('PQR创建成功')
      navigate('/pqr')
    } catch (error: any) {
      console.error('创建PQR失败:', error)
      console.error('错误详情:', error.response?.data)

      if (error.errorFields) {
        message.error('请完成所有必填项')
      } else {
        // 处理后端返回的验证错误
        let errorMsg = '创建PQR失败，请稍后重试'

        if (error.response?.data?.detail) {
          const detail = error.response.data.detail
          // 如果 detail 是数组（FastAPI 验证错误）
          if (Array.isArray(detail)) {
            errorMsg = detail.map((err: any) => {
              const field = err.loc?.join('.') || '未知字段'
              return `${field}: ${err.msg}`
            }).join('; ')
          } else if (typeof detail === 'string') {
            errorMsg = detail
          } else if (typeof detail === 'object') {
            errorMsg = JSON.stringify(detail)
          }
        }

        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  /**
   * 取消创建
   */
  const handleCancel = () => {
    navigate('/pqr')
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 页面标题 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={2}>创建PQR</Title>
              <Space>
                <Button
                  icon={<QuestionCircleOutlined />}
                  onClick={() => window.open('/help/pqr-template', '_blank')}
                >
                  帮助文档
                </Button>
                <Button
                  type="dashed"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/templates')}
                >
                  创建自定义模板
                </Button>
              </Space>
            </div>
            <Alert
              message="提示"
              description={
                <div>
                  <Text>请先选择PQR模板，然后根据模板填写具体的试验数据。</Text>
                  <br />
                  <Text type="secondary">
                    如果没有找到合适的模板，您可以{' '}
                    <Link onClick={() => navigate('/templates')}>创建自定义模板</Link>
                    {' '}（根据会员等级有不同的配额限制）
                  </Text>
                </div>
              }
              type="info"
              showIcon
              closable
              style={{ marginTop: 16 }}
            />
          </div>

          {/* 步骤指示器 */}
          <Steps current={currentStep} items={steps} />

          {/* 表单内容 */}
          <Spin spinning={loading}>
            <Form
              form={form}
              layout="vertical"
              style={{ marginTop: 24 }}
            >
              {/* 第一步：选择模板 */}
              {currentStep === 0 && (
                <TemplateSelector
                  value={selectedTemplateId}
                  onChange={handleTemplateChange}
                  moduleType="pqr"
                />
              )}

              {/* 第二步：填写数据 */}
              {currentStep === 1 && selectedTemplate && (
                <>
                  <div style={{ marginBottom: 24 }}>
                    <TemplatePreview
                      template={selectedTemplate}
                      defaultCollapsed={true}
                    />
                  </div>
                  <ModuleFormRenderer
                    modules={selectedTemplate.module_instances || []}
                    form={form}
                    moduleType="pqr"
                  />
                </>
              )}
            </Form>
          </Spin>

          {/* 操作按钮 */}
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCancel}>
                取消
              </Button>

              {currentStep > 0 && (
                <Button
                  icon={<LeftOutlined />}
                  onClick={handlePrev}
                >
                  上一步
                </Button>
              )}

              {currentStep < steps.length - 1 ? (
                <Button
                  type="primary"
                  onClick={handleNext}
                  disabled={!selectedTemplateId}
                >
                  下一步
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<CheckOutlined />}
                  onClick={handleNext}
                  loading={loading}
                >
                  提交
                </Button>
              )}
            </Space>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default PQRCreate

