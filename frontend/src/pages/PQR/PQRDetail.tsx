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
import pqrService from '@/services/pqr'
import { getPQRModuleById } from '@/constants/pqrModules'
import customModuleService from '@/services/customModules'
import dayjs from 'dayjs'
import { ApprovalButton } from '@/components/Approval/ApprovalButton'
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory'
import { useAuthStore } from '@/store/authStore'
import TableFieldRenderer from '@/components/WPS/TableFieldRenderer'

const { Title, Text } = Typography

interface PQRDetailData {
  id: number
  title: string
  pqr_number: string
  revision: string
  status: string
  test_date?: string
  test_organization?: string
  qualification_result?: string
  template_id?: string
  modules_data?: Record<string, any>
  created_at: string
  updated_at: string
  [key: string]: any
}

const PQRDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [pqrData, setPqrData] = useState<PQRDetailData | null>(null)
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

  // 获取 PQR 详情和自定义模块
  useEffect(() => {
    const fetchPQRDetail = async () => {
      if (!id) return

      try {
        setLoading(true)

        // 获取 PQR 数据
        const response = await pqrService.get(parseInt(id))
        if (response.success && response.data) {
          setPqrData(response.data)

          // 获取自定义模块定义
          if (response.data.modules_data) {
            const customModuleIds = new Set<string>()
            Object.values(response.data.modules_data).forEach((module: any) => {
              if (module.moduleId && !getPQRModuleById(module.moduleId)) {
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
          message.error(response.message || '获取PQR详情失败')
        }
      } catch (error: any) {
        console.error('获取PQR详情失败:', error)
        message.error(error.response?.data?.detail || '获取PQR详情失败')
      } finally {
        setLoading(false)
      }
    }

    fetchPQRDetail()
  }, [id])

  // 处理编辑
  const handleEdit = () => {
    navigate(`/pqr/${id}/edit`)
  }

  // 处理复制
  const handleCopy = async () => {
    if (!pqrData) return
    try {
      // 创建新的 PQR 数据，去掉 id 和时间戳
      const copyData = {
        ...pqrData,
        title: `${pqrData.title} (副本)`,
        pqr_number: `${pqrData.pqr_number}-COPY-${Date.now()}`,
        status: 'draft',
      }
      delete (copyData as any).id
      delete (copyData as any).created_at
      delete (copyData as any).updated_at

      // 创建新 PQR
      const response = await pqrService.create(copyData)
      if (response.success) {
        message.success('复制成功')
        navigate('/pqr')
      } else {
        message.error(response.message || '复制失败')
      }
    } catch (error: any) {
      console.error('复制PQR失败:', error)
      message.error(error.response?.data?.detail || '复制失败')
    }
  }

  // 处理导出Word
  const handleExportWord = async () => {
    try {
      message.loading('正在生成Word文档...', 0)

      const apiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const response = await fetch(`${apiBaseURL}/pqr/${id}/export/word`, {
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

  // 处理导出PDF
  const handleExportPDF = async () => {
    try {
      message.loading('正在生成PDF文档...', 0)

      const apiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const response = await fetch(`${apiBaseURL}/pqr/${id}/export/pdf`, {
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
      link.download = `PQR_${pqrData?.pqr_number}_${new Date().toISOString().split('T')[0]}.pdf`
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
    if (fieldDef?.type === 'table') {
      if (fieldDef?.tableDefinition) {
        return (
          <TableFieldRenderer
            tableDefinition={fieldDef.tableDefinition}
            value={value || {}}
            readonly={true}
          />
        )
      } else {
        // 表格字段但没有定义
        console.error('表格字段缺少 tableDefinition:', fieldKey, fieldDef)
        return (
          <div style={{ padding: '12px', background: '#fff2e8', border: '1px solid #ffbb96', borderRadius: '4px' }}>
            <Text type="warning">⚠️ 表格未定义</Text>
            <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
              字段: {fieldKey}
            </div>
          </div>
        )
      }
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
          <Title level={2}>PQR详情</Title>
        </div>
        <Card>
          <Empty description="未找到PQR数据" />
        </Card>
      </div>
    )
  }

  // 提取模块数据
  const moduleFields = extractAllFieldsFromModules(pqrData.modules_data)

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const configMap: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      draft: { color: 'default', icon: <EditOutlined />, text: '草稿' },
      review: { color: 'processing', icon: <SyncOutlined spin />, text: '审核中' },
      qualified: { color: 'success', icon: <CheckCircleOutlined />, text: '合格' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '不合格' },
    }
    return configMap[status] || { color: 'default', icon: <ClockCircleOutlined />, text: status }
  }

  const statusConfig = getStatusConfig(pqrData.status)

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/pqr')}
            >
              返回列表
            </Button>
            <Divider type="vertical" />
            <Space direction="vertical" size={0}>
              <Title level={3} style={{ margin: 0 }}>
                {pqrData.title}
              </Title>
              <Space size="small">
                <Text type="secondary">PQR编号: {pqrData.pqr_number}</Text>
                <Divider type="vertical" />
                <Text type="secondary">版本: {pqrData.revision || 'A'}</Text>
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
          <Descriptions.Item label="PQR编号">
            <Text strong>{pqrData.pqr_number}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="标题">
            {pqrData.title}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Badge
              status={statusConfig.color === 'success' ? 'success' : statusConfig.color === 'error' ? 'error' : 'processing'}
              text={statusConfig.text}
            />
          </Descriptions.Item>
          <Descriptions.Item label="版本">
            <Tag>{pqrData.revision || 'A'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="试验日期">
            {pqrData.test_date ? dayjs(pqrData.test_date).format('YYYY-MM-DD') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="试验机构">
            {pqrData.test_organization || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="评定结果">
            {pqrData.qualification_result || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(pqrData.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(pqrData.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 模块数据卡片 */}
      {pqrData.modules_data && Object.keys(pqrData.modules_data).length > 0 && (
        <Card
          title={
            <Space>
              <SettingOutlined />
              <Text strong>模块数据详情</Text>
              <Tag color="blue">{Object.keys(pqrData.modules_data).length} 个模块</Tag>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Tabs
            items={Object.entries(pqrData.modules_data).map(([instanceId, moduleContent]: [string, any]) => {
              // 获取模块定义
              const moduleId = moduleContent.moduleId
              const presetModule = getPQRModuleById(moduleId)
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

                          // 调试信息
                          if (fieldDef?.type === 'table' && !fieldDef?.tableDefinition) {
                            console.warn('表格字段缺少 tableDefinition:', {
                              fieldKey,
                              fieldDef,
                              moduleId,
                              module,
                              customModule
                            })
                          }

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
      {pqrData.approval_instance_id && (
        <Card
          title={
            <Space>
              <HistoryOutlined />
              <Text strong>审批历史</Text>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <ApprovalHistory instanceId={pqrData.approval_instance_id} />
        </Card>
      )}

      {/* 操作按钮 */}
      <Card>
        <Space size="middle">
          <Button type="primary" icon={<EditOutlined />} onClick={handleEdit} size="large">
            编辑 PQR
          </Button>
          <Button icon={<CopyOutlined />} onClick={handleCopy} size="large">
            复制 PQR
          </Button>
          <Button icon={<FileWordOutlined />} onClick={handleExportWord} size="large">
            导出 Word
          </Button>
          <Button icon={<FilePdfOutlined />} onClick={handleExportPDF} size="large">
            导出 PDF
          </Button>

          {/* 审批按钮 */}
          <ApprovalButton
            documentType="pqr"
            documentId={parseInt(id || '0')}
            documentNumber={pqrData.pqr_number}
            documentTitle={pqrData.title}
            instanceId={pqrData.approval_instance_id}
            status={pqrData.approval_status || pqrData.status}
            canSubmit={!pqrData.approval_instance_id}
            canApprove={false}
            canCancel={false}
            onSuccess={() => {
              // 刷新PQR数据
              window.location.reload()
            }}
            size="large"
          />
        </Space>
      </Card>
    </div>
  )
}

export default PQRDetail