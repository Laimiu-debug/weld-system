import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Typography, Button, Space, Form, Spin, message, Alert, Radio } from 'antd'
import { ArrowLeftOutlined, SaveOutlined, FormOutlined, FileWordOutlined } from '@ant-design/icons'
import wpsService from '@/services/wps'
import ModuleFormRenderer from '@/components/WPS/ModuleFormRenderer'
import WPSDocumentEditor from '@/components/DocumentEditor/WPSDocumentEditor'
import { WPSTemplate } from '@/services/wpsTemplates'
import wpsTemplateService from '@/services/wpsTemplates'
import { getModuleById } from '@/constants/wpsModules'
import { convertModulesToTipTapHTML } from '@/utils/moduleToTipTapHTML'
import dayjs from 'dayjs'

const { Title } = Typography

interface WPSEditData {
  id: number
  title: string
  wps_number: string
  revision: string
  status: string
  template_id?: string
  modules_data?: Record<string, any>
  document_html?: string
  [key: string]: any
}

const WPSEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [wpsData, setWpsData] = useState<WPSEditData | null>(null)
  const [template, setTemplate] = useState<WPSTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editMode, setEditMode] = useState<'form' | 'document'>('form')
  const [documentHTML, setDocumentHTML] = useState<string>('')

  // 处理编辑模式切换
  const handleEditModeChange = (mode: 'form' | 'document') => {
    setEditMode(mode)

    // 如果切换到文档模式，从当前表单数据生成HTML
    if (mode === 'document' && template && wpsData) {
      const formValues = form.getFieldsValue()

      // 重新构建modules_data从表单值
      const modulesData: Record<string, any> = {}

      template.module_instances.forEach(instance => {
        const moduleData: Record<string, any> = {
          moduleId: instance.moduleId,
          customName: instance.customName,
          data: {}
        }

        const module = getModuleById(instance.moduleId)
        if (module) {
          Object.keys(module.fields).forEach(fieldKey => {
            const formFieldName = `${instance.instanceId}_${fieldKey}`
            const fieldDef = module.fields[fieldKey]
            let fieldValue = formValues[formFieldName]

            // 跳过空值（但保留 false 和 0）
            if (fieldValue === undefined || fieldValue === null || fieldValue === '') {
              return
            }

            // 跳过空数组（图片字段）
            if (Array.isArray(fieldValue) && fieldValue.length === 0) {
              return
            }

            // 如果是日期字段且值是 dayjs 对象，转换为字符串
            if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
              fieldValue = fieldValue.format('YYYY-MM-DD')
            }
            // 如果是图片字段，只保留必要的属性，移除 originFileObj
            else if (fieldDef?.type === 'image' && Array.isArray(fieldValue)) {
              fieldValue = fieldValue.map((img: any) => ({
                uid: img.uid,
                name: img.name,
                status: img.status,
                url: img.url,
                thumbUrl: img.thumbUrl
                // 不保存 originFileObj，避免序列化问题
              }))
            }

            moduleData.data[fieldKey] = fieldValue
          })
        }

        modulesData[instance.instanceId] = moduleData
      })

      // 生成HTML
      const html = convertModulesToTipTapHTML(
        template.module_instances,
        modulesData,
        {
          title: wpsData.title || '',
          number: wpsData.wps_number || '',
          revision: wpsData.revision || 'A'
        },
        'wps'
      )

      setDocumentHTML(html)
    }
  }

  // 获取 WPS 详情和模板
  useEffect(() => {
    const fetchData = async () => {
      if (!id) return

      try {
        setLoading(true)

        // 获取 WPS 详情
        const wpsResponse = await wpsService.getWPS(parseInt(id))
        if (!wpsResponse.success || !wpsResponse.data) {
          message.error('获取WPS详情失败')
          return
        }

        const wps = wpsResponse.data
        console.log('[WPSEdit] 加载的WPS数据:', {
          id: wps.id,
          wps_number: wps.wps_number,
          template_id: wps.template_id,
          has_modules_data: !!wps.modules_data,
          has_document_html: !!wps.document_html,
          document_html_length: wps.document_html?.length || 0
        })
        setWpsData(wps)

        // 如果有 template_id，尝试获取模板
        if (wps.template_id) {
          try {
            const templateResponse = await wpsTemplateService.getTemplate(wps.template_id)
            if (templateResponse.success && templateResponse.data) {
              console.log('[WPSEdit] 加载的模板:', {
                id: templateResponse.data.id,
                name: templateResponse.data.name,
                module_instances_count: templateResponse.data.module_instances?.length || 0
              })
              setTemplate(templateResponse.data)
            }
          } catch (error) {
            console.warn('获取模板失败（模板可能已被删除）:', error)
            // 模板不存在时不显示错误，因为文档数据仍然完整
          }
        }

        // 初始化表单数据
        const formValues: Record<string, any> = {
          title: wps.title,
          wps_number: wps.wps_number,
          revision: wps.revision,
        }

        // 从 modules_data 中恢复表单值
        if (wps.modules_data) {
          Object.entries(wps.modules_data).forEach(([moduleId, moduleContent]: [string, any]) => {
            if (moduleContent && moduleContent.data) {
              Object.entries(moduleContent.data).forEach(([fieldKey, fieldValue]: [string, any]) => {
                const formFieldName = `${moduleId}_${fieldKey}`

                // 获取字段定义以检查字段类型
                const module = getModuleById(moduleContent.moduleId)
                const fieldDef = module?.fields?.[fieldKey]

                // 如果是日期字段且值是字符串，转换为 dayjs 对象
                if (fieldDef?.type === 'date' && fieldValue && typeof fieldValue === 'string') {
                  formValues[formFieldName] = dayjs(fieldValue)
                }
                // 如果是图片字段，确保格式正确
                else if (fieldDef?.type === 'image' && Array.isArray(fieldValue)) {
                  console.log(`[WPSEdit] 恢复图片字段 ${formFieldName}:`, JSON.stringify(fieldValue).substring(0, 200))
                  // 确保每个图片对象都有必要的属性，并过滤掉无效的 blob URL
                  formValues[formFieldName] = fieldValue
                    .map((img: any, index: number) => {
                      const url = img.url || img.thumbUrl || ''

                      // 检测并过滤掉失效的 blob URL - blob URL 在页面刷新后会失效
                      if (url.startsWith('blob:')) {
                        console.warn(`[WPSEdit] 图片 ${index} 包含失效的 blob URL，已跳过:`, img.name, url.substring(0, 50))
                        return null  // 标记为无效
                      }

                      // 如果已经是正确的 UploadFile 格式且 URL 有效，直接使用
                      if (img.uid && img.name && url.startsWith('data:image')) {
                        console.log(`[WPSEdit] 图片 ${index} 已是正确格式:`, img.name, url.substring(0, 50))
                        return img
                      }

                      // 如果 URL 有效，构造一个标准的 UploadFile 对象
                      if (url.startsWith('data:image')) {
                        const uploadFile = {
                          uid: img.uid || `-${Date.now()}-${index}`,
                          name: img.name || `image_${index}.png`,
                          status: 'done',
                          url: url,
                          thumbUrl: url
                          // 不包含 originFileObj
                        }
                        console.log(`[WPSEdit] 构造图片 ${index} UploadFile:`, uploadFile.name, uploadFile.url?.substring(0, 50))
                        return uploadFile
                      }

                      // URL 无效或格式不正确
                      console.warn(`[WPSEdit] 图片 ${index} URL 无效，已跳过:`, img.name, url.substring(0, 50))
                      return null
                    })
                    .filter((img: any) => img !== null)  // 移除无效图片

                  // 验证图片数据
                  const validImages = formValues[formFieldName].filter((img: any) => {
                    const url = img.url || img.thumbUrl
                    return url && url.startsWith('data:image')
                  })
                  console.log(`[WPSEdit] 字段 ${formFieldName} 有效图片数量:`, validImages.length, '/', formValues[formFieldName].length)

                  // 如果所有图片都无效，显示警告
                  if (fieldValue.length > 0 && validImages.length === 0) {
                    console.error(`[WPSEdit] 字段 ${formFieldName} 的所有图片数据已损坏，请重新生成或上传图片`)
                  }
                } else {
                  formValues[formFieldName] = fieldValue
                }
              })
            }
          })
        }

        form.setFieldsValue(formValues)

        // 设置文档HTML（如果存在）
        if (wps.document_html) {
          console.log('[WPSEdit] 设置已有的document_html，长度:', wps.document_html.length)
          setDocumentHTML(wps.document_html)
        } else {
          console.log('[WPSEdit] document_html为空，等待模板加载后生成')
        }
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
    console.log('[WPSEdit] 检查是否需要生成HTML:', {
      hasTemplate: !!template,
      hasWpsData: !!wpsData,
      hasModulesData: !!wpsData?.modules_data,
      documentHTMLLength: documentHTML?.length || 0,
      templateInstances: template?.module_instances?.length || 0,
      loading: loading
    })

    // 只有在数据加载完成后才尝试生成HTML
    if (!loading && wpsData && wpsData.modules_data && !documentHTML) {
      console.log('[WPSEdit] 从表单数据生成HTML...')

      // 如果有模板，使用模板的module_instances
      // 如果没有模板，从modules_data重建module_instances
      let moduleInstances = template?.module_instances

      if (!moduleInstances) {
        console.log('[WPSEdit] 模板不存在，从modules_data重建module_instances')
        moduleInstances = Object.entries(wpsData.modules_data).map(([instanceId, content]: [string, any]) => ({
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
        wpsData.modules_data,
        {
          title: wpsData.title || '',
          number: wpsData.wps_number || '',
          revision: wpsData.revision || 'A'
        },
        'wps'
      )
      console.log('[WPSEdit] 生成的HTML长度:', html?.length || 0)
      console.log('[WPSEdit] 生成的HTML内容:', html?.substring(0, 200))
      setDocumentHTML(html)
    }
  }, [template, wpsData, documentHTML, loading])

  // 处理文档模式保存
  const handleSaveDocument = async (htmlContent: string) => {
    try {
      setSaving(true)

      const updateData: any = {
        document_html: htmlContent
      }

      const response = await wpsService.updateWPS(parseInt(id!), updateData)
      if (response.success) {
        message.success('保存成功')
        setDocumentHTML(htmlContent)
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

  // 处理Word导出
  const handleExportWord = async (style: string = 'blue_white') => {
    try {
      message.loading('正在生成Word文档...', 0)

      const response = await fetch(`/api/v1/wps/${id}/export/word?style=${style}`, {
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
      link.download = `WPS_${wpsData?.wps_number}_${new Date().toISOString().split('T')[0]}.docx`
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

  // 处理PDF导出 - 使用浏览器打印功能
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
          <title>WPS-${wpsData?.wps_number}</title>
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

  // 处理表单模式保存
  const handleSave = async () => {
    try {
      setSaving(true)

      // 验证表单
      const values = await form.validateFields()

      // 重新构建 modules_data
      let wpsNumber = ''
      let wpsTitle = ''
      let wpsRevision = 'A'
      const modulesData: Record<string, any> = {}

      // 如果有模板，使用模板结构
      if (template && template.module_instances) {
        template.module_instances.forEach(instance => {
          const moduleData: Record<string, any> = {}
          const module = getModuleById(instance.moduleId)

          if (module) {
            Object.keys(module.fields).forEach(fieldKey => {
              const formFieldName = `${instance.instanceId}_${fieldKey}`
              const fieldDef = module.fields[fieldKey]
              let fieldValue = values[formFieldName]

              // 跳过空值（但保留 false 和 0）
              if (fieldValue === undefined || fieldValue === null || fieldValue === '') {
                return
              }

              // 跳过空数组（图片字段）
              if (Array.isArray(fieldValue) && fieldValue.length === 0) {
                return
              }

              // 如果是日期字段且值是 dayjs 对象，转换为字符串
              if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
                fieldValue = fieldValue.format('YYYY-MM-DD')
              }
              // 如果是图片字段，只保留必要的属性，移除 originFileObj
              else if (fieldDef?.type === 'image' && Array.isArray(fieldValue)) {
                console.log(`[WPSEdit] 处理图片字段 ${fieldKey}，原始数据:`, fieldValue.map(img => ({
                  name: img.name,
                  hasUrl: !!img.url,
                  hasThumbUrl: !!img.thumbUrl,
                  urlType: img.url?.startsWith('data:image') ? 'base64' : img.url?.startsWith('blob:') ? 'blob' : 'unknown'
                })))

                fieldValue = fieldValue.map((img: any) => {
                  const cleanedImg = {
                    uid: img.uid,
                    name: img.name,
                    status: img.status,
                    url: img.url,
                    thumbUrl: img.thumbUrl
                    // 不保存 originFileObj，避免序列化问题
                  }
                  console.log(`[WPSEdit] 保存图片字段 ${fieldKey}:`, {
                    name: cleanedImg.name,
                    urlType: cleanedImg.url?.startsWith('data:image') ? 'base64' : cleanedImg.url?.startsWith('blob:') ? 'blob' : 'unknown',
                    urlPreview: cleanedImg.url?.substring(0, 50)
                  })
                  return cleanedImg
                })
              }

              moduleData[fieldKey] = fieldValue

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
      } else if (wpsData?.modules_data) {
        // 没有模板时，保留原有的 modules_data 结构，只更新表单值
        Object.entries(wpsData.modules_data).forEach(([instanceId, moduleContent]: [string, any]) => {
          if (moduleContent && moduleContent.data) {
            const moduleData: Record<string, any> = {}
            const module = getModuleById(moduleContent.moduleId)

            if (module) {
              Object.keys(module.fields).forEach(fieldKey => {
                const formFieldName = `${instanceId}_${fieldKey}`
                const fieldDef = module.fields[fieldKey]
                let fieldValue = values[formFieldName]

                // 跳过空值（但保留 false 和 0）
                if (fieldValue === undefined || fieldValue === null || fieldValue === '') {
                  return
                }

                // 跳过空数组（图片字段）
                if (Array.isArray(fieldValue) && fieldValue.length === 0) {
                  return
                }

                // 如果是日期字段且值是 dayjs 对象，转换为字符串
                if (fieldDef?.type === 'date' && dayjs.isDayjs(fieldValue)) {
                  fieldValue = fieldValue.format('YYYY-MM-DD')
                }
                // 如果是图片字段，只保留必要的属性，移除 originFileObj
                else if (fieldDef?.type === 'image' && Array.isArray(fieldValue)) {
                  fieldValue = fieldValue.map((img: any) => {
                    const cleanedImg = {
                      uid: img.uid,
                      name: img.name,
                      status: img.status,
                      url: img.url,
                      thumbUrl: img.thumbUrl
                      // 不保存 originFileObj，避免序列化问题
                    }
                    console.log(`[WPSEdit] 保存图片字段 ${fieldKey}:`, {
                      name: cleanedImg.name,
                      urlType: cleanedImg.url?.startsWith('data:image') ? 'base64' : cleanedImg.url?.startsWith('blob:') ? 'blob' : 'unknown',
                      urlPreview: cleanedImg.url?.substring(0, 50)
                    })
                    return cleanedImg
                  })
                }

                moduleData[fieldKey] = fieldValue
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
        title: wpsTitle || values.title,
        wps_number: wpsNumber || values.wps_number,
        revision: wpsRevision || values.revision,
      }

      if (Object.keys(modulesData).length > 0) {
        updateData.modules_data = modulesData
      }

      // 调试：打印即将发送的数据
      console.log('[WPSEdit] 即将保存的 updateData:', JSON.stringify(updateData).substring(0, 500))

      // 调用 API 更新
      const response = await wpsService.updateWPS(parseInt(id!), updateData)
      if (response.success) {
        message.success('保存成功')
        navigate('/wps')
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

  if (loading) {
    return (
      <div className="page-container">
        <Spin size="large" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }} />
      </div>
    )
  }

  if (!wpsData) {
    return (
      <div className="page-container">
        <div className="page-header">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/wps')}
          >
            返回列表
          </Button>
          <Title level={2}>编辑WPS</Title>
        </div>
        <Card>
          <Alert message="未找到WPS数据" type="error" />
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
            onClick={() => navigate('/wps')}
          >
            返回列表
          </Button>
          <Title level={2}>编辑WPS</Title>
        </Space>
      </div>

      <Card>
        {/* 如果模板被删除，显示警告信息 */}
        {!template && wpsData?.modules_data && (
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
        {wpsData?.modules_data ? (
          <>
            {editMode === 'form' ? (
              <Form
                form={form}
                layout="vertical"
              >
                {/* 基本信息 */}
                <Form.Item
                  label="WPS编号"
                  name="wps_number"
                  rules={[{ required: true, message: '请输入WPS编号' }]}
                >
                  <input type="text" />
                </Form.Item>

                <Form.Item
                  label="标题"
                  name="title"
                  rules={[{ required: true, message: '请输入标题' }]}
                >
                  <input type="text" />
                </Form.Item>

                <Form.Item
                  label="版本"
                  name="revision"
                >
                  <input type="text" />
                </Form.Item>

                {/* 模块表单 - 使用模板或从 modules_data 重建 */}
                {template && template.module_instances ? (
                  <ModuleFormRenderer
                    modules={template.module_instances || []}
                    form={form}
                  />
                ) : (
                  <ModuleFormRenderer
                    modules={Object.entries(wpsData.modules_data).map(([instanceId, content]: [string, any]) => ({
                      instanceId,
                      moduleId: content.moduleId,
                      customName: content.customName || '',
                      rowIndex: content.rowIndex,
                      columnIndex: content.columnIndex,
                      order: 0,
                    }))}
                    form={form}
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
                <Button onClick={() => navigate('/wps')}>
                  取消
                </Button>
              </Space>
            )}
          </>
        ) : (
          <Alert
            message="无法编辑此WPS"
            description="此WPS没有模块数据，无法编辑"
            type="error"
            showIcon
          />
        )}
      </Card>
    </div>
  )
}

export default WPSEdit