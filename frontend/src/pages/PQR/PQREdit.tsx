import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Button, Space, Form, Spin, message, Alert, Input, Radio } from 'antd'
import { ArrowLeftOutlined, SaveOutlined, FormOutlined, FileWordOutlined } from '@ant-design/icons'
import pqrService from '@/services/pqr'
import ModuleFormRenderer from '@/components/WPS/ModuleFormRenderer'
import WPSDocumentEditor from '@/components/DocumentEditor/WPSDocumentEditor'
import { WPSTemplate } from '@/services/wpsTemplates'
import wpsTemplateService from '@/services/wpsTemplates'
import { getPQRModuleById } from '@/constants/pqrModules'
import { convertModulesToTipTapHTML } from '@/utils/moduleToTipTapHTML'
import dayjs from 'dayjs'

const { Title } = Typography

interface PQREditData {
  id: number
  title: string
  pqr_number: string
  revision: string
  status: string
  template_id?: string
  modules_data?: Record<string, any>
  document_html?: string
  [key: string]: any
}

const PQREdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [pqrData, setPqrData] = useState<PQREditData | null>(null)
  const [template, setTemplate] = useState<WPSTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState<'form' | 'document'>('form')
  const [documentHTML, setDocumentHTML] = useState<string>('')

  // 处理编辑模式切换
  const handleEditModeChange = (mode: 'form' | 'document') => {
    setEditMode(mode)

    // 如果切换到文档模式，从当前表单数据生成HTML
    if (mode === 'document' && template && pqrData) {
      const formValues = form.getFieldsValue()

      // 重新构建modules_data从表单值
      const modulesData: Record<string, any> = {}

      template.module_instances.forEach(instance => {
        const moduleData: Record<string, any> = {
          moduleId: instance.moduleId,
          customName: instance.customName,
          data: {}
        }

        const module = getPQRModuleById(instance.moduleId)
        if (module) {
          Object.keys(module.fields).forEach(fieldKey => {
            const formFieldName = `${instance.instanceId}_${fieldKey}`
            const fieldValue = formValues[formFieldName]

            // 包含所有字段，即使是空值
            if (fieldValue !== undefined && fieldValue !== null && fieldValue !== '') {
              const fieldDef = module.fields[fieldKey]
              let processedValue = fieldValue

              // 如果是日期字段且值是 dayjs 对象，转换为字符串
              if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
                processedValue = fieldValue.format('YYYY-MM-DD')
              }

              moduleData.data[fieldKey] = processedValue
            }
          })
        }

        modulesData[instance.instanceId] = moduleData
      })

      // 生成HTML
      const html = convertModulesToTipTapHTML(
        template.module_instances,
        modulesData,
        {
          title: pqrData.title || '',
          number: pqrData.pqr_number || '',
          revision: pqrData.revision || 'A'
        },
        'pqr'
      )

      setDocumentHTML(html)
    }
  }

  // 获取 PQR 详情和模板
  useEffect(() => {
    const fetchData = async () => {
      if (!id) return

      try {
        setLoading(true)

        // 获取 PQR 详情
        const pqrResponse = await pqrService.get(parseInt(id))
        if (!pqrResponse.success || !pqrResponse.data) {
          message.error('获取PQR详情失败')
          return
        }

        const pqr = pqrResponse.data
        setPqrData(pqr)

        // 如果有 document_html，初始化文档内容
        if (pqr.document_html) {
          setDocumentHTML(pqr.document_html)
        }

        // 如果有 template_id，尝试获取模板
        if (pqr.template_id) {
          try {
            const templateResponse = await wpsTemplateService.getTemplate(pqr.template_id)
            if (templateResponse.success && templateResponse.data) {
              setTemplate(templateResponse.data)
            }
          } catch (error) {
            console.warn('获取模板失败（模板可能已被删除）:', error)
            // 模板不存在时不显示错误，因为文档数据仍然完整
          }
        }

        // 初始化表单数据
        const formValues: Record<string, any> = {
          title: pqr.title,
          pqr_number: pqr.pqr_number,
          revision: pqr.revision,
        }

        // 从 modules_data 中恢复表单值
        if (pqr.modules_data) {
          Object.entries(pqr.modules_data).forEach(([moduleId, moduleContent]: [string, any]) => {
            if (moduleContent && moduleContent.data) {
              Object.entries(moduleContent.data).forEach(([fieldKey, fieldValue]: [string, any]) => {
                const formFieldName = `${moduleId}_${fieldKey}`

                // 获取字段定义以检查字段类型
                const module = getPQRModuleById(moduleContent.moduleId)
                const fieldDef = module?.fields?.[fieldKey]

                // 如果是日期字段且值是字符串，转换为 dayjs 对象
                if (fieldDef?.type === 'date' && fieldValue && typeof fieldValue === 'string') {
                  formValues[formFieldName] = dayjs(fieldValue)
                }
                // 如果是图片字段，确保格式正确
                else if (fieldDef?.type === 'image' && Array.isArray(fieldValue)) {
                  // 确保每个图片对象都有必要的属性
                  formValues[formFieldName] = fieldValue.map((img: any, index: number) => {
                    // 如果已经是正确的 UploadFile 格式，直接使用
                    if (img.uid && img.name && (img.url || img.thumbUrl)) {
                      return img
                    }
                    // 否则，构造一个标准的 UploadFile 对象
                    return {
                      uid: img.uid || `-${Date.now()}-${index}`,
                      name: img.name || `image_${index}.png`,
                      status: 'done',
                      url: img.url || img.thumbUrl || '',
                      thumbUrl: img.thumbUrl || img.url || '',
                      originFileObj: img.originFileObj
                    }
                  })
                } else {
                  formValues[formFieldName] = fieldValue
                }
              })
            }
          })
        }

        form.setFieldsValue(formValues)
      } catch (error: any) {
        console.error('获取数据失败:', error)
        message.error(error.response?.data?.detail || '获取数据失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id, form])

  // 当数据加载完成后，如果document_html为空，从表单数据生成HTML
  useEffect(() => {
    // 只有在数据加载完成后才尝试生成HTML
    if (!loading && pqrData && pqrData.modules_data && !documentHTML) {
      console.log('[PQREdit] 从表单数据生成HTML...')

      // 如果有模板，使用模板的module_instances
      // 如果没有模板，从modules_data重建module_instances
      let moduleInstances = template?.module_instances

      if (!moduleInstances) {
        console.log('[PQREdit] 模板不存在，从modules_data重建module_instances')
        moduleInstances = Object.entries(pqrData.modules_data).map(([instanceId, content]: [string, any]) => ({
          instanceId,
          moduleId: content.moduleId,
          customName: content.customName || '',
          rowIndex: content.rowIndex || 0,
          columnIndex: content.columnIndex || 0,
          order: 0,
        }))
      }

      const html = convertModulesToTipTapHTML(
        moduleInstances,
        pqrData.modules_data,
        {
          title: pqrData.title || '',
          number: pqrData.pqr_number || '',
          revision: pqrData.revision || 'A'
        },
        'pqr'
      )
      console.log('[PQREdit] 生成的HTML长度:', html?.length || 0)
      setDocumentHTML(html)
    }
  }, [template, pqrData, documentHTML, loading])

  // 处理保存
  const handleSave = async () => {
    try {
      setSaving(true)

      // 验证表单
      const values = await form.validateFields()

      // 重新构建 modules_data
      let pqrNumber = ''
      let pqrTitle = ''
      let pqrRevision = 'A'
      const modulesData: Record<string, any> = {}

      // 如果有模板，使用模板结构
      if (template && template.module_instances) {
        template.module_instances.forEach(instance => {
          const moduleData: Record<string, any> = {}
          const module = getPQRModuleById(instance.moduleId)

          if (module) {
            Object.keys(module.fields).forEach(fieldKey => {
              const formFieldName = `${instance.instanceId}_${fieldKey}`
              if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
                const fieldDef = module.fields[fieldKey]
                let fieldValue = values[formFieldName]

                // 如果是日期字段且值是 dayjs 对象，转换为字符串
                if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
                  fieldValue = fieldValue.format('YYYY-MM-DD')
                }

                moduleData[fieldKey] = fieldValue

                // 从 pqr_basic_info 模块中提取 pqr_number, title, revision
                if (instance.moduleId === 'pqr_basic_info') {
                  if (fieldKey === 'pqr_number') {
                    pqrNumber = values[formFieldName]
                  } else if (fieldKey === 'title') {
                    pqrTitle = values[formFieldName]
                  } else if (fieldKey === 'revision') {
                    pqrRevision = values[formFieldName]
                  }
                }
              }
            })
          }

          if (Object.keys(moduleData).length > 0) {
            modulesData[instance.instanceId] = {
              moduleId: instance.moduleId,
              customName: instance.customName,
              rowIndex: instance.rowIndex,
              columnIndex: instance.columnIndex,
              data: moduleData,
            }
          }
        })
      } else if (pqrData?.modules_data) {
        // 没有模板时，保留原有的 modules_data 结构，只更新表单值
        Object.entries(pqrData.modules_data).forEach(([instanceId, moduleContent]: [string, any]) => {
          if (moduleContent && moduleContent.data) {
            const moduleData: Record<string, any> = {}
            const module = getPQRModuleById(moduleContent.moduleId)

            if (module) {
              Object.keys(module.fields).forEach(fieldKey => {
                const formFieldName = `${instanceId}_${fieldKey}`
                if (values[formFieldName] !== undefined && values[formFieldName] !== null && values[formFieldName] !== '') {
                  const fieldDef = module.fields[fieldKey]
                  let fieldValue = values[formFieldName]

                  // 如果是日期字段且值是 dayjs 对象，转换为字符串
                  if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
                    fieldValue = fieldValue.format('YYYY-MM-DD')
                  }

                  moduleData[fieldKey] = fieldValue
                }
              })
            }

            if (Object.keys(moduleData).length > 0) {
              modulesData[instanceId] = {
                moduleId: moduleContent.moduleId,
                customName: moduleContent.customName,
                data: moduleData,
              }
            }
          }
        })
      }

      // 构建更新数据
      const updateData: any = {
        title: pqrTitle || values.title,
        pqr_number: pqrNumber || values.pqr_number,
        revision: pqrRevision || values.revision,
      }

      if (Object.keys(modulesData).length > 0) {
        updateData.modules_data = modulesData
      }

      // 调用 API 更新
      const response = await pqrService.update(parseInt(id!), updateData)
      if (response.success) {
        message.success('保存成功')
        navigate('/pqr')
      } else {
        message.error(response.message || '保存失败')
      }
    } catch (error: any) {
      console.error('保存失败:', error)
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  // 保存文档HTML
  const handleSaveDocument = async (html: string) => {
    try {
      setSaving(true)
      setDocumentHTML(html)

      // 更新数据库中的 document_html
      const updateData = {
        document_html: html
      }

      const response = await pqrService.update(parseInt(id!), updateData)
      if (response.success) {
        message.success('文档已保存')
      } else {
        message.error(response.message || '保存失败')
      }
    } catch (error: any) {
      console.error('保存文档失败:', error)
      message.error(error.response?.data?.detail || '保存文档失败')
    } finally {
      setSaving(false)
    }
  }

  // 导出为Word
  const handleExportWord = async (style: string = 'blue_white') => {
    try {
      message.loading('正在生成Word文档...', 0)

      const response = await fetch(`/api/v1/pqr/${id}/export/word?style=${style}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('导出失败')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `PQR_${pqrData?.pqr_number}_${new Date().toISOString().split('T')[0]}.docx`
      link.click()
      URL.revokeObjectURL(url)

      message.destroy()
      message.success('导出成功')
    } catch (error) {
      message.destroy()
      message.error('导出失败，请稍后重试')
      console.error('导出Word失败:', error)
    }
  }

  // 导出为PDF - 使用浏览器打印功能
  const handleExportPDF = async () => {
    try {
      // 先保存当前内容（如果在文档编辑模式）
      if (editMode === 'document' && documentHTML) {
        message.loading('正在保存文档...', 0)
        await handleSaveDocument(documentHTML)
        message.destroy()
      }

      // 打开打印预览窗口
      const printWindow = window.open('', '_blank')
      if (!printWindow) {
        message.error('无法打开打印窗口，请检查浏览器弹窗设置')
        return
      }

      // 生成打印页面HTML
      const printHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>PQR-${pqrData?.pqr_number}</title>
          <style>
            @page {
              size: A4;
              margin: 2cm;
            }
            body {
              font-family: 'Microsoft YaHei', Arial, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 21cm;
              margin: 0 auto;
              padding: 20px;
            }
            h1 {
              text-align: center;
              color: #1890ff;
              margin-bottom: 10px;
            }
            h2, h3 {
              color: #1890ff;
              margin-top: 20px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 20px 0;
              page-break-inside: avoid;
            }
            table, th, td {
              border: 1px solid #ddd;
            }
            th, td {
              padding: 8px;
              text-align: left;
            }
            th {
              background-color: #f0f0f0;
              font-weight: bold;
            }
            hr {
              border: none;
              border-top: 2px solid #ddd;
              margin: 20px 0;
            }
            .footer {
              margin-top: 40px;
              text-align: center;
              font-size: 12px;
              color: #999;
            }
            @media print {
              body {
                padding: 0;
              }
              .no-print {
                display: none;
              }
            }
          </style>
        </head>
        <body>
          ${documentHTML || '<p>文档内容为空</p>'}
          <div class="footer">
            <p>打印日期: ${new Date().toLocaleString('zh-CN')}</p>
          </div>
          <div class="no-print" style="position: fixed; top: 20px; right: 20px;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
              打印/保存为PDF
            </button>
            <button onclick="window.close()" style="padding: 10px 20px; background: #999; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-left: 10px;">
              关闭
            </button>
          </div>
        </body>
        </html>
      `

      printWindow.document.write(printHTML)
      printWindow.document.close()

      message.success('已打开打印预览窗口，请使用浏览器的"打印"功能保存为PDF')
    } catch (error) {
      message.error('打开打印预览失败')
      console.error('导出PDF失败:', error)
    }
  }


  if (loading) {
    return (
      <div className="page-container">
        <Spin size="large" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }} />
      </div>
    )
  }

  if (!pqrData) {
    return (
      <div className="page-container">
        <div className="page-header">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/pqr')}
          >
            返回列表
          </Button>
          <Title level={2}>编辑PQR</Title>
        </div>
        <Card>
          <Alert message="未找到PQR数据" type="error" />
        </Card>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/pqr')}
          >
            返回列表
          </Button>
          <Title level={2}>编辑PQR</Title>
        </Space>
      </div>

      <Card>
        {/* 如果模板被删除，显示警告信息 */}
        {!template && pqrData?.modules_data && (
          <Alert
            message="模板已被删除"
            description="此文档使用的模板已被删除，但文档数据完整，仍可正常编辑。"
            type="warning"
            showIcon
            closable
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 如果有模板，显示模板信息 */}
        {template && (
          <Alert
            message="使用模板编辑"
            description={`当前使用模板: ${template.name || template.id}`}
            type="info"
            showIcon
            closable
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 编辑模式切换 */}
        <div style={{ marginBottom: 16 }}>
          <Radio.Group
            value={editMode}
            onChange={e => handleEditModeChange(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="form">
              <FormOutlined /> 表单编辑
            </Radio.Button>
            <Radio.Button value="document">
              <FileWordOutlined /> 文档编辑
            </Radio.Button>
          </Radio.Group>
        </div>

        {/* 如果有 modules_data（无论是否有模板），都可以编辑 */}
        {pqrData?.modules_data ? (
          <>
            {editMode === 'form' ? (
              <Form
                form={form}
                layout="vertical"
              >
                {/* 基本信息 */}
                <Form.Item
                  label="PQR编号"
                  name="pqr_number"
                  rules={[{ required: true, message: '请输入PQR编号' }]}
                >
                  <Input />
                </Form.Item>

                <Form.Item
                  label="标题"
                  name="title"
                  rules={[{ required: true, message: '请输入标题' }]}
                >
                  <Input />
                </Form.Item>

                <Form.Item
                  label="版本"
                  name="revision"
                >
                  <Input />
                </Form.Item>

                {/* 模块表单 - 使用模板或从 modules_data 重建 */}
                {template && template.module_instances ? (
                  <ModuleFormRenderer
                    modules={template.module_instances || []}
                    form={form}
                    moduleType="pqr"
                  />
                ) : (
                  <ModuleFormRenderer
                    modules={Object.entries(pqrData.modules_data).map(([instanceId, content]: [string, any]) => ({
                      instanceId,
                      moduleId: content.moduleId,
                      customName: content.customName || '',
                      rowIndex: content.rowIndex,
                      columnIndex: content.columnIndex,
                      order: 0,
                    }))}
                    form={form}
                    moduleType="pqr"
                  />
                )}
              </Form>
            ) : (
              <WPSDocumentEditor
                initialContent={documentHTML}
                onSave={handleSaveDocument}
                onExportWord={handleExportWord}
                onExportPDF={handleExportPDF}
              />
            )}

            {editMode === 'form' && (
              <Space style={{ marginTop: 24 }}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={saving}
                  onClick={handleSave}
                >
                  保存
                </Button>
                <Button onClick={() => navigate('/pqr')}>
                  取消
                </Button>
              </Space>
            )}
          </>
        ) : (
          <Alert
            message="无法编辑此PQR"
            description="此PQR没有模块数据，无法编辑"
            type="error"
            showIcon
          />
        )}
      </Card>
    </div>
  )
}

export default PQREdit