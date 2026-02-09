/**
 * 基于模板的WPS创建页面
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
import { getModuleById } from '@/constants/wpsModules'
import wpsService from '@/services/wps'

const { Title, Text, Link } = Typography

const WPSCreate: React.FC = () => {
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
      description: '选择焊接工艺和WPS模板',
      icon: <FileTextOutlined />
    },
    {
      title: '填写数据',
      description: '根据模板填写WPS数据',
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
        message.error('请先选择WPS模板')
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

      // 新架构：直接保存所有模块数据到 modules_data
      // 结构: { "module_instance_id": { "field_key": value, ... }, ... }
      const modulesData: Record<string, any> = {}
      let wpsNumber = ''
      let wpsTitle = ''
      let wpsRevision = 'A'

      if (selectedTemplate?.module_instances) {
        selectedTemplate.module_instances.forEach(instance => {
          const moduleData: Record<string, any> = {}
          const module = getModuleById(instance.moduleId)

          if (module) {
            Object.keys(module.fields).forEach(fieldKey => {
              const formFieldName = `${instance.instanceId}_${fieldKey}`
              // 只包含有值的字段
              if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
                moduleData[fieldKey] = values[formFieldName]

                // 从 header_data 模块中提取 wps_number, title, revision
                if (instance.moduleId === 'header_data') {
                  if (fieldKey === 'wps_number') {
                    wpsNumber = values[formFieldName]
                  } else if (fieldKey === 'title') {
                    wpsTitle = values[formFieldName]
                  } else if (fieldKey === 'revision') {
                    wpsRevision = values[formFieldName]
                  }
                }
              }
            })
          }

          // 将模块数据存储到 modules_data，使用 instanceId 作为 key
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
        title: wpsTitle || `WPS-${Date.now()}`,
        wps_number: wpsNumber || `WPS-${Date.now()}`,
        revision: wpsRevision || 'A',
        status: 'draft',
        welding_process: selectedTemplate?.welding_process,
        process_specification: selectedTemplate?.standard,
      }

      // 添加 modules_data 到提交数据
      if (Object.keys(modulesData).length > 0) {
        submitData.modules_data = modulesData
      }

      console.log('提交数据:', submitData)

      // 调用API创建WPS
      const response = await wpsService.createWPS(submitData)

      message.success('WPS创建成功')
      navigate('/wps')
    } catch (error: any) {
      console.error('创建WPS失败:', error)
      if (error.errorFields) {
        message.error('请完成所有必填项')
      } else {
        const errorMsg = error.response?.data?.detail || '创建WPS失败，请稍后重试'
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
    navigate('/wps')
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 页面标题 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={2}>创建WPS</Title>
              <Space>
                <Button
                  icon={<QuestionCircleOutlined />}
                  onClick={() => window.open('/help/wps-template', '_blank')}
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
                  <Text>请先选择焊接工艺和标准，然后选择对应的WPS模板，最后根据模板填写具体数据。</Text>
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
                />
              )}

              {/* 第二步：填写数据 */}
              {currentStep === 1 && selectedTemplate && (
                <>
                  <div style={{ marginBottom: 24 }}>
                    <TemplatePreview
                      template={selectedTemplate}
                    />
                  </div>
                  <ModuleFormRenderer
                    modules={selectedTemplate.module_instances || []}
                    form={form}
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

export default WPSCreate