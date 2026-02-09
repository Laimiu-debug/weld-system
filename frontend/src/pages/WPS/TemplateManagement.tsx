/**
 * WPS模板管理页面
 * 用于管理用户自定义的WPS模板
 */
import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Typography,
  Tooltip,
  Popconfirm
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CopyOutlined,
  FileTextOutlined,
  BlockOutlined,
  ArrowLeftOutlined,
  ShareAltOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import wpsTemplateService, { WPSTemplateSummary, WPSTemplate } from '@/services/wpsTemplates'
import { SharedLibraryService } from '@/services/sharedLibrary'
import { useAuthStore } from '@/store/authStore'
import TemplateBuilder from '@/components/WPS/TemplateBuilder'

const { Title, Text } = Typography

const TemplateManagement: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const [templates, setTemplates] = useState<WPSTemplateSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<WPSTemplateSummary | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [builderVisible, setBuilderVisible] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<WPSTemplate | null>(null)

  // 加载模板列表
  useEffect(() => {
    console.log('TemplateManagement 组件已挂载，开始加载模板')
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      console.log('开始加载模板列表...')
      const response = await wpsTemplateService.getTemplates()
      console.log('模板列表响应:', response)
      if (response.success && response.data) {
        console.log('模板数据:', response.data.items)
        setTemplates(response.data.items)
      } else {
        console.warn('响应不成功或没有数据:', response)
        message.warning('没有获取到模板数据')
      }
    } catch (error: any) {
      console.error('加载模板列表失败:', error)
      message.error('加载模板列表失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  // 删除模板
  const handleDelete = async (templateId: string) => {
    try {
      await wpsTemplateService.deleteTemplate(templateId)
      message.success('模板删除成功')
      loadTemplates()
    } catch (error) {
      message.error('删除模板失败')
    }
  }

  // 查看模板详情
  const handleView = async (template: WPSTemplateSummary) => {
    try {
      const response = await wpsTemplateService.getTemplate(template.id)
      if (response.success && response.data) {
        setSelectedTemplate(template)
        setPreviewVisible(true)
      }
    } catch (error) {
      message.error('加载模板详情失败')
    }
  }

  // 编辑模板
  const handleEdit = async (template: WPSTemplateSummary) => {
    try {
      const response = await wpsTemplateService.getTemplate(template.id)
      if (response.success && response.data) {
        setEditingTemplate(response.data)
        setBuilderVisible(true)
      }
    } catch (error) {
      message.error('加载模板详情失败')
    }
  }

  // 复制模板
  const handleCopy = async (template: WPSTemplateSummary) => {
    try {
      const response = await wpsTemplateService.getTemplate(template.id)
      if (response.success && response.data) {
        const copiedTemplate = {
          ...response.data,
          name: `${response.data.name} (副本)`,
          id: undefined  // 清除ID以创建新模板
        }
        setEditingTemplate(copiedTemplate)
        setBuilderVisible(true)
      }
    } catch (error) {
      message.error('加载模板详情失败')
    }
  }

  // 分享到共享库
  const handleShareToLibrary = async (template: WPSTemplateSummary) => {
    try {
      // 先获取模板详情
      const detailResponse = await wpsTemplateService.getTemplate(template.id)
      if (detailResponse.success && detailResponse.data) {
        const templateData = detailResponse.data

        // 显示分享确认对话框
        Modal.confirm({
          title: '分享到共享库',
          content: (
            <div>
              <p>确定要将模板 "{template.name}" 分享到共享库吗？</p>
              <p style={{ color: '#666', fontSize: '12px' }}>
                分享后，其他用户可以浏览和下载您的模板。
              </p>
            </div>
          ),
          okText: '确认分享',
          cancelText: '取消',
          onOk: async () => {
            try {
              // 创建共享模板数据
              const sharedTemplateData = {
                original_template_id: template.id,
                name: templateData.name,
                description: templateData.description || '',
                welding_process: templateData.welding_process,
                welding_process_name: templateData.welding_process_name,
                standard: templateData.standard,
                module_instances: templateData.module_instances,
                tags: ['WPS', '焊接工艺'],
                difficulty_level: 'beginner',
                changelog: '初始分享版本'
              }

              const response = await SharedLibraryService.shareTemplate(sharedTemplateData)
              if (response.id) {
                message.success('分享成功！模板已提交到共享库等待审核。')

                // 可以选择跳转到共享库页面
                setTimeout(() => {
                  Modal.info({
                    title: '分享成功',
                    content: (
                      <div>
                        <p>您的模板已成功分享到共享库！</p>
                        <p>管理员审核通过后，其他用户就可以看到并使用您的模板了。</p>
                        <p style={{ marginTop: '16px' }}>
                          <Button
                            type="primary"
                            onClick={() => navigate('/shared-library')}
                          >
                            前往共享库
                          </Button>
                        </p>
                      </div>
                    ),
                    okText: '知道了'
                  })
                }, 1000)
              }
            } catch (shareError: any) {
              message.error(shareError.response?.data?.detail || '分享失败，请稍后重试')
            }
          }
        })
      } else {
        message.error('无法获取模板详情')
      }
    } catch (error) {
      message.error('分享失败，请稍后重试')
    }
  }

  // 表格列定义
  const columns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: WPSTemplateSummary) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: '焊接工艺',
      dataIndex: 'welding_process',
      key: 'welding_process',
      render: (code: string, record: WPSTemplateSummary) => (
        <Space>
          <Tag color="blue">{code}</Tag>
          <Text type="secondary">{record.welding_process_name}</Text>
        </Space>
      )
    },
    {
      title: '标准',
      dataIndex: 'standard',
      key: 'standard',
      render: (text: string) => text || '-'
    },
    {
      title: '模板类型',
      dataIndex: 'module_type',
      key: 'module_type',
      render: (moduleType: string) => {
        if (moduleType === 'wps') {
          return <Tag color="cyan">WPS</Tag>
        }
        if (moduleType === 'pqr') {
          return <Tag color="orange">PQR</Tag>
        }
        if (moduleType === 'ppqr') {
          return <Tag color="magenta">pPQR</Tag>
        }
        return <Tag color="cyan">WPS</Tag>
      }
    },
    {
      title: '来源',
      dataIndex: 'template_source',
      key: 'template_source',
      render: (source: string, record: WPSTemplateSummary) => {
        if (record.is_system) {
          return <Tag color="green">系统</Tag>
        }
        if (source === 'user') {
          return <Tag color="blue">个人</Tag>
        }
        if (source === 'enterprise') {
          return <Tag color="purple">企业</Tag>
        }
        return <Tag>{source}</Tag>
      }
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
      render: (count: number) => count || 0
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: WPSTemplateSummary) => (
        <Space>
          <Tooltip title="查看">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>

          {!record.is_system && (
            <>
              <Tooltip title="编辑">
                <Button
                  type="link"
                  icon={<EditOutlined />}
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>

              <Tooltip title="复制">
                <Button
                  type="link"
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(record)}
                />
              </Tooltip>

              <Tooltip title="分享到共享库">
                <Button
                  type="link"
                  icon={<ShareAltOutlined />}
                  onClick={() => handleShareToLibrary(record)}
                  style={{ color: '#1890ff' }}
                />
              </Tooltip>

              <Tooltip title="删除">
                <Popconfirm
                  title="确定要删除这个模板吗？"
                  onConfirm={() => handleDelete(record.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button
                    type="link"
                    danger
                    icon={<DeleteOutlined />}
                  />
                </Popconfirm>
              </Tooltip>
            </>
          )}
        </Space>
      )
    }
  ]

  const handleSaveTemplate = async (templateData: any) => {
    try {
      // 获取当前工作区信息
      const currentWorkspace = localStorage.getItem('current_workspace')
      console.log('当前工作区:', currentWorkspace)
      console.log('保存模板:', templateData)

      let response
      if (templateData.templateId) {
        // 编辑模式
        const { templateId, ...updateData } = templateData
        response = await wpsTemplateService.updateTemplate(templateId, updateData)
        console.log('模板更新响应:', response)
      } else {
        // 创建模式
        response = await wpsTemplateService.createTemplate(templateData)
        console.log('模板创建响应:', response)
      }

      if (response.success) {
        message.success(templateData.templateId ? '模板更新成功！' : '模板创建成功！')
        // 刷新模板列表
        await loadTemplates()
        // 清除编辑状态
        setEditingTemplate(null)
      } else {
        message.error(response.data?.detail || '保存模板失败')
        throw new Error(response.data?.detail || '保存模板失败')
      }
    } catch (error: any) {
      console.error('保存模板失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '保存模板失败'
      message.error(errorMsg)
      throw error
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 页面标题和操作 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={2}>模板管理</Title>
            <Space>
              <Button
                icon={<BlockOutlined />}
                onClick={() => navigate('/modules')}
              >
                模块管理
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setBuilderVisible(true)}
              >
                使用模块创建模板
              </Button>
            </Space>
          </div>

          {/* 模板列表 */}
          <Table
            columns={columns}
            dataSource={templates}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个模板`
            }}
          />
        </Space>
      </Card>

      {/* 预览模态框 */}
      <Modal
        title="模板详情"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedTemplate && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Text strong>模板名称：</Text>
              <Text>{selectedTemplate.name}</Text>
            </div>
            <div>
              <Text strong>焊接工艺：</Text>
              <Tag color="blue">{selectedTemplate.welding_process}</Tag>
              <Text>{selectedTemplate.welding_process_name}</Text>
            </div>
            {selectedTemplate.standard && (
              <div>
                <Text strong>标准：</Text>
                <Text>{selectedTemplate.standard}</Text>
              </div>
            )}
            <div>
              <Text strong>使用次数：</Text>
              <Text>{selectedTemplate.usage_count || 0}</Text>
            </div>
          </Space>
        )}
      </Modal>

      {/* 模板构建器 */}
      <TemplateBuilder
        visible={builderVisible}
        onClose={() => {
          setBuilderVisible(false)
          setEditingTemplate(null)
        }}
        onSave={handleSaveTemplate}
        editingTemplate={editingTemplate}
      />
    </div>
  )
}

export default TemplateManagement

