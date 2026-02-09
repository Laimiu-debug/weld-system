import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Descriptions,
  Spin,
  message,
  Divider,
  Empty,
  Tabs,
  Row,
  Col,
  Image,
  Table,
  Badge
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DownloadOutlined,
  CopyOutlined,
  FileTextOutlined,
  ToolOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  SettingOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  HistoryOutlined,
  FileWordOutlined,
  FilePdfOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import wpsService from '@/services/wps'
import { getModuleById } from '@/constants/wpsModules'
import customModuleService from '@/services/customModules'
import dayjs from 'dayjs'
import { ApprovalButton } from '@/components/Approval/ApprovalButton'
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory'
import { useAuthStore } from '@/store/authStore'
import TableFieldRenderer from '@/components/WPS/TableFieldRenderer'

const { Title, Text } = Typography

interface WPSDetailData {
  id: number
  title: string
  wps_number: string
  revision: string
  status: string
  company?: string
  project_name?: string
  welding_process?: string
  base_material_spec?: string
  filler_material_classification?: string
  template_id?: string
  modules_data?: Record<string, any>
  created_at: string
  updated_at: string
  // 审批相关字段
  approval_instance_id?: number
  approval_status?: string
  workflow_name?: string
  [key: string]: any
}

const WPSDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [wpsData, setWpsData] = useState<WPSDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [customModulesCache, setCustomModulesCache] = useState<Record<string, any>>({})

  // 获取分类图标
  const getCategoryIcon = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      basic: <FileTextOutlined style={{ color: '#1890ff' }} />,
      material: <ToolOutlined style={{ color: '#52c41a' }} />,
      gas: <ExperimentOutlined style={{ color: '#faad14' }} />,
      electrical: <ThunderboltOutlined style={{ color: '#f5222d' }} />,
      motion: <DashboardOutlined style={{ color: '#722ed1' }} />,
      equipment: <SettingOutlined style={{ color: '#13c2c2' }} />,
      calculation: <CalculatorOutlined style={{ color: '#eb2f96' }} />
    }
    return iconMap[category] || <FileTextOutlined />
  }

  // 获取分类名称
  const getCategoryName = (category: string) => {
    const categoryMap: Record<string, string> = {
      basic: '基本信息',
      material: '材料信息',
      gas: '气体信息',
      electrical: '电气参数',
      motion: '运动参数',
      equipment: '设备信息',
      calculation: '计算结果'
    }
    return categoryMap[category] || category
  }

  // 从 modules_data 中提取所有字段
  const extractAllFieldsFromModules = (modulesData: any) => {
    const extracted: Record<string, any> = {}

    if (!modulesData) return extracted

    Object.values(modulesData).forEach((module: any) => {
      if (module && module.data) {
        Object.assign(extracted, module.data)
      }
    })

    return extracted
  }

  // 获取 WPS 详情和自定义模块
  useEffect(() => {
    const fetchWPSDetail = async () => {
      if (!id) return

      try {
        setLoading(true)

        // 获取 WPS 数据
        const response = await wpsService.getWPS(parseInt(id))
        if (response.success && response.data) {
          setWpsData(response.data)

          // 获取自定义模块定义
          if (response.data.modules_data) {
            const customModuleIds = new Set<string>()
            Object.values(response.data.modules_data).forEach((module: any) => {
              if (module.moduleId && !getModuleById(module.moduleId)) {
                customModuleIds.add(module.moduleId)
              }
            })

            // 加载自定义模块定义
            const customModules: Record<string, any> = {}
            for (const moduleId of customModuleIds) {
              try {
                const moduleData = await customModuleService.getCustomModule(moduleId)
                customModules[moduleId] = moduleData
              } catch (error) {
                console.error(`加载自定义模块 ${moduleId} 失败:`, error)
              }
            }
            setCustomModulesCache(customModules)
          }
        } else {
          message.error(response.message || '获取WPS详情失败')
        }
      } catch (error: any) {
        console.error('获取WPS详情失败:', error)
        message.error(error.response?.data?.detail || '获取WPS详情失败')
      } finally {
        setLoading(false)
      }
    }

    fetchWPSDetail()
  }, [id])

  // 处理编辑
  const handleEdit = () => {
    navigate(`/wps/${id}/edit`)
  }

  // 处理复制
  const handleCopy = async () => {
    if (!wpsData) return
    try {
      // 创建新的 WPS 数据，去掉 id 和时间戳
      const copyData = {
        ...wpsData,
        title: `${wpsData.title} (副本)`,
        wps_number: `${wpsData.wps_number}-COPY-${Date.now()}`,
        status: 'draft',
      }
      delete (copyData as any).id
      delete (copyData as any).created_at
      delete (copyData as any).updated_at

      // 创建新 WPS
      const response = await wpsService.createWPS(copyData)
      if (response.success) {
        message.success('复制成功')
        navigate('/wps')
      } else {
        message.error(response.message || '复制失败')
      }
    } catch (error: any) {
      console.error('复制WPS失败:', error)
      message.error(error.response?.data?.detail || '复制失败')
    }
  }

  // 处理导出Word
  const handleExportWord = async () => {
    try {
      message.loading('正在生成Word文档...', 0)

      const apiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const response = await fetch(`${apiBaseURL}/wps/${id}/export/word`, {
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

  // 处理导出PDF
  const handleExportPDF = async () => {
    try {
      message.loading('正在生成PDF文档...', 0)

      const apiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const response = await fetch(`${apiBaseURL}/wps/${id}/export/pdf`, {
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
      link.download = `WPS_${wpsData?.wps_number}_${new Date().toISOString().split('T')[0]}.pdf`
      link.click()
      URL.revokeObjectURL(url)

      message.destroy()
      message.success('导出成功')
    } catch (error) {
      message.destroy()
      message.error('导出失败，请稍后重试')
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
          <Title level={2}>WPS详情</Title>
        </div>
        <Card>
          <Empty description="未找到WPS数据" />
        </Card>
      </div>
    )
  }

  // 提取模块数据
  const moduleFields = extractAllFieldsFromModules(wpsData.modules_data)

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const configMap: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      draft: { color: 'default', icon: <EditOutlined />, text: '草稿' },
      review: { color: 'processing', icon: <SyncOutlined spin />, text: '审核中' },
      approved: { color: 'success', icon: <CheckCircleOutlined />, text: '已批准' },
      rejected: { color: 'error', icon: <CloseCircleOutlined />, text: '已拒绝' },
    }
    return configMap[status] || { color: 'default', icon: <ClockCircleOutlined />, text: status }
  }

  // 渲染字段值
  const renderFieldValue = (fieldKey: string, value: any, fieldDef?: any) => {
    if (value === null || value === undefined || value === '') {
      return <Text type="secondary">-</Text>
    }

    // 如果是文件上传字段
    if (fieldDef?.type === 'file' || fieldDef?.type === 'image') {
      if (Array.isArray(value)) {
        return (
          <Space wrap>
            {value.map((file: any, index: number) => (
              <a key={index} href={file.url} target="_blank" rel="noopener noreferrer">
                {file.name || `文件${index + 1}`}
              </a>
            ))}
          </Space>
        )
      }
    }

    // 如果是图片字段
    if (fieldDef?.type === 'image' && Array.isArray(value)) {
      return (
        <Image.PreviewGroup>
          <Space wrap>
            {value.map((img: any, index: number) => (
              <Image
                key={index}
                width={100}
                src={img.url || img.thumbUrl}
                alt={img.name || `图片${index + 1}`}
              />
            ))}
          </Space>
        </Image.PreviewGroup>
      )
    }

    // 如果是表格字段
    if (fieldDef?.type === 'table' && fieldDef?.tableDefinition) {
      return (
        <TableFieldRenderer
          tableDefinition={fieldDef.tableDefinition}
          value={value || {}}
          readonly={true}
        />
      )
    }

    // 如果是对象
    if (typeof value === 'object') {
      return <Text code>{JSON.stringify(value, null, 2)}</Text>
    }

    // 如果是布尔值
    if (typeof value === 'boolean') {
      return value ? <Tag color="success">是</Tag> : <Tag color="default">否</Tag>
    }

    // 普通值
    return <Text>{String(value)}</Text>
  }

  const statusConfig = getStatusConfig(wpsData.status)

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/wps')}
            >
              返回列表
            </Button>
            <Divider type="vertical" />
            <Space direction="vertical" size={0}>
              <Title level={3} style={{ margin: 0 }}>
                {wpsData.title}
              </Title>
              <Space size="small">
                <Text type="secondary">WPS编号: {wpsData.wps_number}</Text>
                <Divider type="vertical" />
                <Text type="secondary">版本: {wpsData.revision || 'A'}</Text>
              </Space>
            </Space>
          </Space>
          <Space>
            <Tag color={statusConfig.color} icon={statusConfig.icon}>
              {statusConfig.text}
            </Tag>
          </Space>
        </Space>
      </div>

      {/* 基本信息卡片 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <Text strong>基本信息</Text>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Descriptions bordered column={2} size="small">
          <Descriptions.Item label="WPS编号">
            <Text strong>{wpsData.wps_number}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="标题">
            {wpsData.title}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Badge
              status={statusConfig.color === 'success' ? 'success' : statusConfig.color === 'error' ? 'error' : 'processing'}
              text={statusConfig.text}
            />
          </Descriptions.Item>
          <Descriptions.Item label="版本">
            <Tag>{wpsData.revision || 'A'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="公司">
            {wpsData.company || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="项目">
            {wpsData.project_name || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="焊接方法">
            {wpsData.welding_process || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="母材规格">
            {wpsData.base_material_spec || '-'}
          </Descriptions.Item>
          {wpsData.workflow_name && (
            <Descriptions.Item label="审批工作流" span={2}>
              <Space>
                <Tag color="blue">{wpsData.workflow_name}</Tag>
                {wpsData.approval_status && (
                  <Tag
                    color={
                      wpsData.approval_status === 'approved'
                        ? 'success'
                        : wpsData.approval_status === 'rejected'
                        ? 'error'
                        : wpsData.approval_status === 'pending' || wpsData.approval_status === 'in_progress'
                        ? 'processing'
                        : 'default'
                    }
                  >
                    {wpsData.approval_status === 'approved'
                      ? '已批准'
                      : wpsData.approval_status === 'rejected'
                      ? '已拒绝'
                      : wpsData.approval_status === 'pending'
                      ? '待审批'
                      : wpsData.approval_status === 'in_progress'
                      ? '审批中'
                      : wpsData.approval_status}
                  </Tag>
                )}
              </Space>
            </Descriptions.Item>
          )}
          <Descriptions.Item label="填充金属">
            {wpsData.filler_material_classification || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(wpsData.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(wpsData.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 模块数据卡片 */}
      {wpsData.modules_data && Object.keys(wpsData.modules_data).length > 0 && (
        <Card
          title={
            <Space>
              <SettingOutlined />
              <Text strong>模块数据详情</Text>
              <Tag color="blue">{Object.keys(wpsData.modules_data).length} 个模块</Tag>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Tabs
            items={Object.entries(wpsData.modules_data).map(([instanceId, moduleContent]: [string, any]) => {
              // 获取模块定义
              const moduleId = moduleContent.moduleId
              const presetModule = getModuleById(moduleId)
              const customModule = customModulesCache[moduleId]
              const module = presetModule || customModule

              // 模块名称和分类
              const moduleName = moduleContent.customName || module?.name || moduleId
              const moduleCategory = module?.category || 'basic'

              return {
                key: instanceId,
                label: (
                  <Space>
                    {getCategoryIcon(moduleCategory)}
                    <Text>{moduleName}</Text>
                    {module && (
                      <Tag color="blue" style={{ fontSize: 11 }}>
                        {getCategoryName(moduleCategory)}
                      </Tag>
                    )}
                  </Space>
                ),
                children: (
                  <Card size="small" styles={{ body: { padding: '16px' } }}>
                    {moduleContent.data && Object.keys(moduleContent.data).length > 0 ? (
                      <Row gutter={[16, 16]}>
                        {Object.entries(moduleContent.data).map(([fieldKey, value]: [string, any]) => {
                          // 获取字段定义
                          const fieldDef = module?.fields?.[fieldKey]
                          const fieldLabel = fieldDef?.label || fieldKey

                          return (
                            <Col key={fieldKey} xs={24} sm={12} md={8}>
                              <div style={{ marginBottom: 8 }}>
                                <Text strong style={{ fontSize: 13 }}>
                                  {fieldLabel}
                                  {fieldDef?.required && <Text type="danger"> *</Text>}
                                  {fieldDef?.unit && (
                                    <Text type="secondary" style={{ fontSize: 11, marginLeft: 4 }}>
                                      ({fieldDef.unit})
                                    </Text>
                                  )}
                                </Text>
                              </div>
                              <div>
                                {renderFieldValue(fieldKey, value, fieldDef)}
                              </div>
                            </Col>
                          )
                        })}
                      </Row>
                    ) : (
                      <Empty description="该模块暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                    )}
                  </Card>
                ),
              }
            })}
          />
        </Card>
      )}

      {/* 审批历史 */}
      {wpsData.approval_instance_id && (
        <Card
          title={
            <Space>
              <HistoryOutlined />
              <Text strong>审批历史</Text>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <ApprovalHistory instanceId={wpsData.approval_instance_id} />
        </Card>
      )}

      {/* 操作按钮 */}
      <Card>
        <Space size="middle">
          <Button type="primary" icon={<EditOutlined />} onClick={handleEdit} size="large">
            编辑 WPS
          </Button>
          <Button icon={<CopyOutlined />} onClick={handleCopy} size="large">
            复制 WPS
          </Button>
          <Button icon={<FileWordOutlined />} onClick={handleExportWord} size="large">
            导出 Word
          </Button>
          <Button icon={<FilePdfOutlined />} onClick={handleExportPDF} size="large">
            导出 PDF
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default WPSDetail