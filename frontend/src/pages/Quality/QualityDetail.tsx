import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Descriptions,
  Row,
  Col,
  Divider,
  Tabs,
  Table,
  Avatar,
  Modal,
  message,
  Alert,
  Image,
  Upload,
  Spin,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DownloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  FileImageOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { unwrapApiData } from '@/services/response'
import type { QualityInspection } from '@/services/quality'
import qualityService from '@/services/quality'
import { StandardSnapshot } from '@/components/QualityStandardField'
import workspaceService from '@/services/workspace'
import { apiService } from '@/services/api'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography

interface InspectionPhoto {
  file_id: string
  filename: string
  url?: string
}

const unwrapInspection = (response: unknown): QualityInspection | null => {
  const body = response as { data?: { data?: QualityInspection } & QualityInspection }
  return body?.data?.data || body?.data || null
}

const parsePhotos = (raw?: string): InspectionPhoto[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.map((item, index) => {
      if (typeof item === 'string') {
        return { file_id: item, filename: item, url: `/api/v1/files/${item}` }
      }
      const fileId = item.file_id || item.id || String(index)
      return {
        file_id: String(fileId),
        filename: item.filename || item.name || '检验图片',
        url: item.url || `/api/v1/files/${fileId}`,
      }
    })
  } catch {
    return []
  }
}

const parseDefects = (raw?: string) => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return parsed.map((item, index) => ({
        id: String(item.id ?? index),
        film_no: item.film_no || item.filmNo || '-',
        location: item.location || '-',
        type: item.type || item.defect_type || '缺陷',
        severity: item.severity || '-',
        size: item.size || '-',
        quantity: item.quantity ?? 1,
        description: item.description || item.notes || '',
      }))
    }
  } catch {
    return raw
      ? [{ id: '1', film_no: '-', location: '-', type: '记录', severity: '-', size: '-', quantity: 1, description: raw }]
      : []
  }
  return [{ id: '1', film_no: '-', location: '-', type: '记录', severity: '-', size: '-', quantity: 1, description: raw }]
}

const AuthImage: React.FC<{ fileId: string; alt: string }> = ({ fileId, alt }) => {
  const [src, setSrc] = useState('')

  useEffect(() => {
    let objectUrl = ''
    const load = async () => {
      const blob = await apiService.downloadFile(fileId)
      objectUrl = URL.createObjectURL(blob)
      setSrc(objectUrl)
    }
    void load().catch(() => {
      setSrc('')
    })
    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [fileId])

  if (!src) {
    return (
      <div className="flex items-center justify-center" style={{ height: 180 }}>
        <Spin />
      </div>
    )
  }
  return <Image src={src} alt={alt} />
}

const QualityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [inspectionData, setInspectionData] = useState<QualityInspection | null>(null)

  const workspace = () => {
    const current = workspaceService.getCurrentWorkspaceFromStorage()
    return {
      type: (current?.type === 'enterprise' ? 'enterprise' : 'personal') as 'personal' | 'enterprise',
      companyId: current?.type === 'enterprise' ? current.company_id : undefined,
      factoryId: current?.factory_id,
    }
  }

  const loadInspection = async () => {
    if (!id) return
    setLoading(true)
    try {
      const ws = workspace()
      const response = await qualityService.getQualityInspectionById(
        Number(id),
        ws.type,
        ws.companyId,
        ws.factoryId,
      )
      const data = unwrapInspection(response)
      if (!data) {
        message.error('未找到检验记录')
        return
      }
      setInspectionData(data)
    } catch {
      message.error('加载检验记录失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadInspection()
  }, [id])

  const inspectionImages = parsePhotos(inspectionData?.photos)
  const defectRecords = parseDefects(inspectionData?.defect_details || inspectionData?.defects)
  const inspectionItems = [
    {
      id: 'standard',
      name: '检验标准',
      standard: inspectionData?.standard_snapshot ? `${inspectionData.standard_snapshot.standard_code} / ${inspectionData.standard_snapshot.version}: ${inspectionData.standard_snapshot.acceptance_criteria}` : inspectionData?.inspection_standard || inspectionData?.acceptance_criteria || '-',
      result: inspectionData?.is_qualified ? '合格' : '待确认',
      notes: inspectionData?.inspection_method || inspectionData?.ndt_method || '',
    },
  ]

  const getInspectionTypeName = (type: string) => {
    const typeNames: Record<string, { color: string; text: string }> = {
      visual: { color: 'blue', text: '外观检验' },
      radiographic: { color: 'green', text: '射线检验' },
      ultrasonic: { color: 'orange', text: '超声波检验' },
      magnetic: { color: 'purple', text: '磁粉检验' },
      magnetic_particle: { color: 'purple', text: '磁粉检验' },
      penetrant: { color: 'cyan', text: '渗透检验' },
      liquid_penetrant: { color: 'cyan', text: '渗透检验' },
      destructive: { color: 'red', text: '破坏性检验' },
      other: { color: 'default', text: '其他' },
    }
    return typeNames[type] || { color: 'default', text: type || '未知' }
  }

  const getInspectionResultName = (result: string) => {
    const resultNames: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      pass: { color: 'success', text: '合格', icon: <CheckCircleOutlined /> },
      qualified: { color: 'success', text: '合格', icon: <CheckCircleOutlined /> },
      fail: { color: 'error', text: '不合格', icon: <ExclamationCircleOutlined /> },
      unqualified: { color: 'error', text: '不合格', icon: <ExclamationCircleOutlined /> },
      conditional: { color: 'warning', text: '有条件合格', icon: <WarningOutlined /> },
      conditional_qualified: { color: 'warning', text: '有条件合格', icon: <WarningOutlined /> },
      pending: { color: 'default', text: '待定', icon: <ClockCircleOutlined /> },
      retest: { color: 'processing', text: '需复检', icon: <ClockCircleOutlined /> },
    }
    return resultNames[result] || resultNames.pass
  }

  const handleEdit = () => {
    navigate(`/quality/${id}/edit`)
  }

  const handleDelete = () => {
    Modal.confirm({
      title: '确定要删除这个检验记录吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      async onOk() {
        if (!id) return
        const ws = workspace()
        await qualityService.deleteQualityInspection(Number(id), ws.type, ws.companyId, ws.factoryId)
        message.success('删除成功')
        navigate('/quality')
      },
    })
  }

  const persistPhotos = async (photos: InspectionPhoto[]) => {
    if (!id) return
    const ws = workspace()
    const response = await qualityService.updateQualityInspection(
      Number(id),
      { photos: JSON.stringify(photos) },
      ws.type,
      ws.companyId,
      ws.factoryId,
    )
    unwrapApiData(response.data)
    await loadInspection()
  }

  const handleUploadImage = async (file: File) => {
    if (!id) return false
    setUploading(true)
    let uploadedId: string | undefined
    try {
      const uploadResp = await apiService.uploadFile(file, {
        resource_type: 'quality',
        resource_id: String(id),
        description: '质量检验图片',
      })
      const payload = unwrapApiData<{ file_id: string; filename: string; url: string }>(uploadResp.data)
      const fileId = payload?.file_id
      if (!fileId) {
        throw new Error('上传未返回文件编号')
      }
      uploadedId = fileId
      const nextPhotos = [
        ...inspectionImages,
        {
          file_id: fileId,
          filename: payload.filename || file.name,
          url: payload.url || `/api/v1/files/${fileId}`,
        },
      ]
      await persistPhotos(nextPhotos)
      message.success('图片已上传')
    } catch {
      if (uploadedId) {
        try { await apiService.delete(`/files/${uploadedId}`) }
        catch { message.warning('附件清理失败，请稍后重试') }
      }
      message.error('上传图片失败')
    } finally {
      setUploading(false)
    }
    return false
  }

  const inspectionColumns = [
    { title: '检验项目', dataIndex: 'name', key: 'name' },
    { title: '标准要求', dataIndex: 'standard', key: 'standard', ellipsis: true },
    {
      title: '检验结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => (
        <Tag color={result === '合格' ? 'success' : 'warning'}>{result}</Tag>
      ),
    },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
  ]

  const defectColumns = [
    { title: '片子号', dataIndex: 'film_no', key: 'film_no', width: 100 },
    { title: '片上位置', dataIndex: 'location', key: 'location' },
    {
      title: '缺陷类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="red">{type}</Tag>,
    },
    { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 90 },
    { title: '尺寸', dataIndex: 'size', key: 'size', width: 80 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 70 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ]

  if (loading) {
    return (
      <div className="page-container flex justify-center items-center" style={{ minHeight: 320 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!inspectionData) {
    return (
      <div className="page-container">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/quality')}>返回列表</Button>
        <Alert className="mt-4" type="warning" message="未找到检验记录" />
      </div>
    )
  }

  const inspectionType = getInspectionTypeName(inspectionData.inspection_type)
  const inspectionResult = getInspectionResultName(inspectionData.result)

  return (
    <div className="page-container">
      <StandardSnapshot snapshot={inspectionData?.standard_snapshot} />
      <div className="page-header">
        <div className="flex justify-between items-center">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/quality')}>
              返回
            </Button>
            <Title level={2} className="!mb-0">质量检验详情</Title>
            <Tag color={inspectionType.color}>{inspectionType.text}</Tag>
            <Tag color={inspectionResult.color} icon={inspectionResult.icon}>
              {inspectionResult.text}
            </Tag>
          </Space>
          <Space>
            <Button icon={<EditOutlined />} onClick={handleEdit}>编辑</Button>
            <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>删除</Button>
          </Space>
        </div>
      </div>

      <Row gutter={24}>
        <Col xs={24} lg={16}>
          <Card>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                {
                  key: 'info',
                  label: '基本信息',
                  children: (
                    <Descriptions column={2} bordered>
                      <Descriptions.Item label="检验编号">{inspectionData.inspection_number}</Descriptions.Item>
                      <Descriptions.Item label="检验日期">
                        {inspectionData.inspection_date ? dayjs(inspectionData.inspection_date).format('YYYY-MM-DD') : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="项目名称">{inspectionData.project_name || inspectionData.weld_location || '-'}</Descriptions.Item>
                      <Descriptions.Item label="容器号">{inspectionData.vessel_no || '-'}</Descriptions.Item>
                      <Descriptions.Item label="工令号">{inspectionData.work_order_no || '-'}</Descriptions.Item>
                      <Descriptions.Item label="焊缝编号">{inspectionData.weld_joint_number || inspectionData.joint_number || '-'}</Descriptions.Item>
                      <Descriptions.Item label="关联生产任务" span={2}>
                        {inspectionData.production_task_id ? (
                          <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/production/${inspectionData.production_task_id}?tab=quality`)}>
                            任务 #{inspectionData.production_task_id}（查看生产质检）
                          </Button>
                        ) : (
                          '-'
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="检验员">{inspectionData.inspector_name || '-'}</Descriptions.Item>
                      <Descriptions.Item label="缺陷数量">{inspectionData.defects_found ?? 0}</Descriptions.Item>
                      <Descriptions.Item label="是否合格">
                        {inspectionData.is_qualified ? <Tag color="success">合格</Tag> : <Tag color="warning">待确认</Tag>}
                      </Descriptions.Item>
                      <Descriptions.Item label="备注" span={2}>
                        {inspectionData.notes || inspectionData.corrective_actions || '无'}
                      </Descriptions.Item>
                    </Descriptions>
                  ),
                },
                {
                  key: 'items',
                  label: '检验项目',
                  children: (
                    <Table
                      dataSource={inspectionItems}
                      columns={inspectionColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  ),
                },
                {
                  key: 'defects',
                  label: '缺陷记录',
                  children: Array.isArray(defectRecords) ? (
                    <Table
                      dataSource={defectRecords}
                      columns={defectColumns}
                      rowKey="id"
                      pagination={false}
                      locale={{ emptyText: '暂无缺陷记录' }}
                    />
                  ) : (
                    <Paragraph>{String(defectRecords)}</Paragraph>
                  ),
                },
                {
                  key: 'images',
                  label: '检验图片',
                  children: (
                    <div className="p-4">
                      <Row gutter={[16, 16]}>
                        {inspectionImages.map((image) => (
                          <Col xs={24} sm={12} md={8} key={image.file_id}>
                            <Card hoverable cover={<AuthImage fileId={image.file_id} alt={image.filename} />}>
                              <Card.Meta title={image.filename} />
                            </Card>
                          </Col>
                        ))}
                      </Row>
                      {inspectionImages.length === 0 && (
                        <Alert type="info" message="还没有检验图片" className="mb-4" />
                      )}
                      <div className="mt-4 text-center">
                        <Upload
                          accept="image/*"
                          showUploadList={false}
                          beforeUpload={handleUploadImage}
                        >
                          <Button icon={<UploadOutlined />} loading={uploading}>
                            上传图片
                          </Button>
                        </Upload>
                      </div>
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="检验结果">
            <div className="text-center p-4">
              <div className="mb-4">
                <Avatar size={64} icon={inspectionResult.icon} className="mb-3" />
                <Title level={4}>{inspectionResult.text}</Title>
                <Tag color={inspectionResult.color} icon={inspectionResult.icon}>
                  {inspectionResult.text}
                </Tag>
              </div>
              <Divider />
              <div className="mb-4">
                <Text>检验编号: {inspectionData.inspection_number}</Text>
              </div>
              <div className="mb-4">
                <Text>检验类型: </Text>
                <Tag color={inspectionType.color}>{inspectionType.text}</Tag>
              </div>
            </div>
          </Card>

          <Card title="检验信息" className="mt-6">
            <div className="p-4">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>检验日期:</Text>
                  <Text>
                    {inspectionData.inspection_date ? dayjs(inspectionData.inspection_date).format('YYYY-MM-DD') : '-'}
                  </Text>
                </div>
                <div className="flex justify-between">
                  <Text>项目:</Text>
                  <Text>{inspectionData.project_name || inspectionData.weld_location || '-'}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>容器号:</Text>
                  <Text>{inspectionData.vessel_no || '-'}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>工令号:</Text>
                  <Text>{inspectionData.work_order_no || '-'}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>焊缝:</Text>
                  <Text>{inspectionData.weld_joint_number || inspectionData.joint_number || '-'}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>检验员:</Text>
                  <Text>{inspectionData.inspector_name || '-'}</Text>
                </div>
              </Space>
            </div>
          </Card>

          <Card title="缺陷统计" className="mt-6">
            <div className="p-4">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>缺陷总数:</Text>
                  <Text strong>{inspectionData.defects_found ?? (Array.isArray(defectRecords) ? defectRecords.length : 0)}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>气孔:</Text>
                  <Text>{inspectionData.porosity_count ?? 0}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>裂纹:</Text>
                  <Text>{inspectionData.crack_count ?? 0}</Text>
                </div>
              </Space>
            </div>
          </Card>

          <Card title="操作" className="mt-6">
            <Space direction="vertical" className="w-full">
              <Button type="primary" icon={<EditOutlined />} block onClick={handleEdit}>
                编辑检验
              </Button>
              <Button icon={<FileImageOutlined />} block onClick={() => setActiveTab('images')}>
                添加图片
              </Button>
              <Button icon={<PlusOutlined />} block disabled>
                添加检验项目
              </Button>
              <Button icon={<DownloadOutlined />} block disabled>
                导出报告
              </Button>
              <Button icon={<DeleteOutlined />} block danger onClick={handleDelete}>
                删除检验
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default QualityDetail
