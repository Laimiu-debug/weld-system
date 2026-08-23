import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Progress,
  Radio,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import {
  CloudUploadOutlined,
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  EyeOutlined,
  FileSearchOutlined,
  PlusOutlined,
  ReloadOutlined,
  RobotOutlined,
  SendOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import smartImportService, {
  AIExtractionJob,
  AIQuotaStatus,
  DocumentPage,
  ExtractedEntity,
  ExtractedField,
  ImportBatch,
  ImportBatchDetail,
  ImportEntityType,
  SourceDocument,
} from '@/services/smartImport'
import { useNavigate } from 'react-router-dom'
import customModuleService, { CustomModuleSummary } from '@/services/customModules'
import wpsTemplateService, { WPSTemplateSummary } from '@/services/wpsTemplates'
import './smartImport.css'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

type AICapabilities = Awaited<ReturnType<typeof smartImportService.getAICapabilities>>

interface ExtractionResult {
  job: AIExtractionJob
  entity: ExtractedEntity
  pages: DocumentPage[]
}

const entityLabels: Record<ImportEntityType, string> = {
  wps: 'WPS',
  pqr: 'PQR',
  ppqr: 'pPQR',
  welder: '焊工资质',
}

const statusLabels: Record<string, string> = {
  draft: '待上传',
  queued: '排队中',
  processing: '处理中',
  review: '待审核',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
  registered: '已登记',
  stored: '已上传',
  parsing: '解析中',
  ready: '可提取',
}

const statusColors: Record<string, string> = {
  draft: 'default',
  queued: 'processing',
  processing: 'processing',
  review: 'warning',
  completed: 'success',
  ready: 'success',
  failed: 'error',
  cancelled: 'default',
}

function errorMessage(error: unknown, fallback: string): string {
  const detail = (error as any)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (typeof detail?.message === 'string') return detail.message
  return fallback
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

function parseEditedValue(original: unknown, value: string): unknown {
  if (typeof original === 'number') {
    const parsed = Number(value)
    if (!Number.isNaN(parsed)) return parsed
  }
  if (typeof original === 'boolean') {
    if (value === 'true' || value === '是') return true
    if (value === 'false' || value === '否') return false
  }
  if (original && typeof original === 'object') {
    try {
      return JSON.parse(value)
    } catch {
      return value
    }
  }
  return value
}

const SmartImportPage: React.FC = () => {
  const navigate = useNavigate()
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [batch, setBatch] = useState<ImportBatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [extractOpen, setExtractOpen] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [activeDocument, setActiveDocument] = useState<SourceDocument | null>(null)
  const [capabilities, setCapabilities] = useState<AICapabilities | null>(null)
  const [quota, setQuota] = useState<AIQuotaStatus | null>(null)
  const [templates, setTemplates] = useState<WPSTemplateSummary[]>([])
  const [modules, setModules] = useState<CustomModuleSummary[]>([])
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [reviewField, setReviewField] = useState<ExtractedField | null>(null)
  const [reviewing, setReviewing] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [createForm] = Form.useForm()
  const [extractForm] = Form.useForm()
  const [reviewForm] = Form.useForm()
  const extractionMode = Form.useWatch('mode', extractForm)
  const provider = Form.useWatch('provider', extractForm)

  const loadBatches = useCallback(async (preferredId?: string) => {
    setLoading(true)
    try {
      const list = await smartImportService.listBatches()
      setBatches(list)
      const nextId = preferredId || batch?.id || list[0]?.id
      if (nextId) setBatch(await smartImportService.getBatch(nextId))
      else setBatch(null)
    } catch (error) {
      message.error(errorMessage(error, '加载导入任务失败'))
    } finally {
      setLoading(false)
    }
  }, [batch?.id])

  useEffect(() => {
    void loadBatches()
    smartImportService.getAICapabilities().then(setCapabilities).catch(() => undefined)
    smartImportService.getAIQuota().then(setQuota).catch(() => undefined)
  }, [])

  const selectBatch = async (id: string) => {
    setLoading(true)
    try {
      setBatch(await smartImportService.getBatch(id))
    } finally {
      setLoading(false)
    }
  }

  const createBatch = async () => {
    const values = await createForm.validateFields()
    try {
      const created = await smartImportService.createBatch(values)
      setCreateOpen(false)
      createForm.resetFields()
      await loadBatches(created.id)
      message.success('导入任务已创建')
    } catch (error) {
      message.error(errorMessage(error, '创建导入任务失败'))
    }
  }

  const uploadFile = async (options: any) => {
    if (!batch) return options.onError?.(new Error('请先创建导入任务'))
    setUploading(true)
    try {
      const document = await smartImportService.uploadDocument(
        batch.id,
        options.file as File,
        batch.target_entity_type
      )
      await smartImportService.parseDocument(document.id)
      await loadBatches(batch.id)
      options.onSuccess?.(document)
      message.success('文件已上传并完成分页解析')
    } catch (error) {
      options.onError?.(error)
      message.error(errorMessage(error, '文件上传或解析失败'))
    } finally {
      setUploading(false)
    }
  }

  const prepareExtraction = async (document: SourceDocument) => {
    if (!batch) return
    setActiveDocument(document)
    setExtractOpen(true)
    smartImportService.getAIQuota(document.page_count || 1).then(setQuota).catch(() => undefined)
    extractForm.resetFields()
    extractForm.setFieldsValue({
      mode: capabilities?.platform_available ? 'platform' : 'byok',
      provider: 'openai_responses',
      run_ocr: true,
    })
    try {
      const [templateResponse, moduleList] = await Promise.all([
        batch.target_entity_type === 'welder'
          ? Promise.resolve(null)
          : wpsTemplateService.getTemplates({
              module_type: batch.target_entity_type,
              limit: 100,
            }),
        customModuleService.getCustomModules({ limit: 100 }),
      ])
      setTemplates(templateResponse?.data?.items || [])
      setModules(
        moduleList.filter(
          item => item.module_type === batch.target_entity_type || item.module_type === 'common'
        )
      )
    } catch (error) {
      message.error(errorMessage(error, '加载模板和模块失败'))
    }
  }

  const viewDraft = async (document: SourceDocument) => {
    try {
      const entity = await smartImportService.getCurrentDocumentEntity(document.id)
      const pages = await smartImportService.listDocumentPages(document.id)
      setResult({
        entity,
        pages,
        job: {
          id: entity.job_id || '',
          status: 'completed',
          mode: entity.source_mode === 'ai' ? 'platform' : 'byok',
          input_tokens: 0,
          output_tokens: 0,
          total_tokens: 0,
        },
      })
    } catch (error) {
      message.error(errorMessage(error, '该文件还没有可审核的提取草稿'))
    }
  }

  const applyFieldReview = async () => {
    if (!result || !reviewField) return
    const values = await reviewForm.validateFields()
    setReviewing(true)
    try {
      const data = values.action === 'correct'
        ? { ...values, value: parseEditedValue(reviewField.normalized_value, values.value) }
        : values
      const entity = await smartImportService.reviewField(
        result.entity.id,
        reviewField.id,
        data
      )
      setResult({ ...result, entity })
      setReviewField(null)
      reviewForm.resetFields()
      message.success(values.action === 'correct' ? '字段已修正' : '字段审核状态已更新')
    } catch (error) {
      message.error(errorMessage(error, '字段审核失败'))
    } finally {
      setReviewing(false)
    }
  }

  const bulkAccept = async () => {
    if (!result) return
    try {
      const entity = await smartImportService.bulkAcceptFields(result.entity.id, {
        minimum_confidence: 0.85,
      })
      setResult({ ...result, entity })
      message.success('已接受置信度不低于 85% 的待审核字段')
    } catch (error) {
      message.error(errorMessage(error, '批量接受失败'))
    }
  }

  const publishEntity = async () => {
    if (!result) return
    setPublishing(true)
    try {
      const published = await smartImportService.publishEntity(result.entity.id)
      setResult({
        ...result,
        entity: { ...result.entity, status: 'published' },
      })
      await loadBatches(batch?.id)
      Modal.success({
        title: '已发布到正式业务模块',
        content: '正式记录仍保持草稿状态，需要继续执行现有审批流程。',
        okText: '查看正式记录',
        onOk: () => navigate(published.detail_url),
      })
    } catch (error) {
      message.error(errorMessage(error, '发布失败'))
    } finally {
      setPublishing(false)
    }
  }

  const runExtraction = async () => {
    if (!activeDocument) return
    const values = await extractForm.validateFields()
    const [sourceType, sourceId] = String(values.schema_source).split(':', 2)
    setExtracting(true)
    try {
      const response = await smartImportService.extractDocument(activeDocument.id, {
        mode: values.mode,
        provider: values.provider,
        model: values.mode === 'byok' ? values.model?.trim() : undefined,
        base_url: values.mode === 'byok' ? values.base_url?.trim() || undefined : undefined,
        api_key: values.mode === 'byok' ? values.api_key : undefined,
        template_id: sourceType === 'template' ? sourceId : undefined,
        module_id: sourceType === 'module' ? sourceId : undefined,
        run_ocr: values.run_ocr,
      })
      setResult(response)
      setExtractOpen(false)
      extractForm.setFieldValue('api_key', undefined)
      await loadBatches(batch?.id)
      message.success('AI 提取完成，结果已进入待审核草稿')
    } catch (error) {
      message.error(errorMessage(error, 'AI 提取失败'))
    } finally {
      setExtracting(false)
    }
  }

  const columns: ColumnsType<SourceDocument> = useMemo(() => [
    {
      title: '文件',
      dataIndex: 'original_filename',
      ellipsis: true,
      render: (name: string, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          <Text type="secondary">{row.page_count || 0} 页 · {(row.size_bytes / 1024 / 1024).toFixed(2)} MB</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 110,
      render: (status: string) => <Tag color={statusColors[status]}>{statusLabels[status] || status}</Tag>,
    },
    {
      title: '操作',
      width: 280,
      render: (_, row) => (
        <Space>
          {row.status !== 'ready' && (
            <Button
              size="small"
              onClick={async () => {
                await smartImportService.parseDocument(row.id)
                await loadBatches(batch?.id)
              }}
            >
              重新解析
            </Button>
          )}
          <Button
            type="primary"
            size="small"
            icon={<RobotOutlined />}
            disabled={row.status !== 'ready'}
            onClick={() => void prepareExtraction(row)}
          >
            AI 提取
          </Button>
          <Button size="small" icon={<EyeOutlined />} onClick={() => void viewDraft(row)}>
            查看草稿
          </Button>
        </Space>
      ),
    },
  ], [batch?.id, loadBatches])

  const fieldColumns: ColumnsType<ExtractedField> = [
    {
      title: '字段',
      dataIndex: 'field_key',
      width: 180,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value}</Text>
          {row.canonical_field_key && <Text type="secondary">{row.canonical_field_key}</Text>}
        </Space>
      ),
    },
    {
      title: '识别值',
      dataIndex: 'normalized_value',
      render: value => <pre className="smart-import__value">{displayValue(value)}</pre>,
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      width: 110,
      render: value => {
        const percent = Math.round((value || 0) * 100)
        const color = percent >= 85 ? 'success' : percent >= 60 ? 'warning' : 'error'
        return <Tag color={color}>{percent}%</Tag>
      },
    },
    {
      title: '审核状态',
      dataIndex: 'review_status',
      width: 110,
      render: status => {
        const labels: Record<string, string> = {
          pending: '待审核', accepted: '已接受', corrected: '已修正', rejected: '已拒绝', not_required: '无需处理',
        }
        const colors: Record<string, string> = {
          pending: 'warning', accepted: 'success', corrected: 'processing', rejected: 'error', not_required: 'default',
        }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
      },
    },
    {
      title: '证据',
      dataIndex: 'evidence',
      width: 320,
      render: evidence => evidence?.length ? (
        <Space direction="vertical" size={4}>
          {evidence.map((item: any) => (
            <Text key={item.id} className="smart-import__evidence">
              第 {item.page_number} 页：{item.text_excerpt}
            </Text>
          ))}
        </Space>
      ) : <Text type="secondary">无证据片段</Text>,
    },
    {
      title: '操作',
      width: 190,
      fixed: 'right',
      render: (_, field) => result?.entity.status === 'published' ? null : (
        <Space size={4}>
          <Button
            type="text"
            size="small"
            icon={<CheckOutlined />}
            title="接受"
            onClick={() => {
              setReviewField(field)
              reviewForm.setFieldsValue({ action: 'accept', value: field.normalized_value })
            }}
          />
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            title="修正"
            onClick={() => {
              setReviewField(field)
              reviewForm.setFieldsValue({ action: 'correct', value: displayValue(field.normalized_value), reason: '' })
            }}
          />
          <Button
            type="text"
            danger
            size="small"
            icon={<CloseOutlined />}
            title="拒绝"
            onClick={() => {
              setReviewField(field)
              reviewForm.setFieldsValue({ action: 'reject', reason: '' })
            }}
          />
        </Space>
      ),
    },
  ]

  const pendingFieldCount = result?.entity.fields.filter(field => field.review_status === 'pending').length || 0

  return (
    <div className="smart-import">
      <div className="smart-import__header">
        <div>
          <Title level={2}>企业能力建库 · 智能导入</Title>
          <Paragraph type="secondary">上传已有 WPS、PQR 或焊工资质文件，AI 只生成带证据的待审核草稿，不会直接写入正式数据。</Paragraph>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建导入任务</Button>
      </div>

      <Alert
        showIcon
        type="info"
        message="AI 是可选输入方式"
        description="可使用平台额度或临时填写自己的 API Key。自己的 Key 只用于本次请求，不会保存；也可以继续使用原有手工新建功能。"
      />

      {quota && (
        <Card size="small" className="smart-import__quota">
          <Space wrap>
            <WalletOutlined />
            <Text strong>本月平台 AI 点数</Text>
            <Text>{quota.remaining_points} / {quota.monthly_points} 点可用</Text>
            {quota.estimated_points !== undefined && (
              <Tag color={quota.can_run_estimate ? 'success' : 'error'}>
                当前文件预计 {quota.estimated_points} 点
              </Tag>
            )}
            <Text type="secondary">BYOK 不扣平台点数</Text>
          </Space>
        </Card>
      )}

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} className="smart-import__workspace">
          <Col xs={24} lg={7}>
            <Card
              title="导入任务"
              extra={<Button type="text" icon={<ReloadOutlined />} onClick={() => void loadBatches()} />}
            >
              <List
                dataSource={batches}
                locale={{ emptyText: <Empty description="暂无导入任务" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
                renderItem={item => (
                  <List.Item
                    className={item.id === batch?.id ? 'smart-import__batch smart-import__batch--active' : 'smart-import__batch'}
                    onClick={() => void selectBatch(item.id)}
                  >
                    <List.Item.Meta
                      title={<Space><Text>{item.name}</Text><Tag>{entityLabels[item.target_entity_type]}</Tag></Space>}
                      description={
                        <Space direction="vertical" size={3} className="smart-import__batch-meta">
                          <Text type="secondary">{statusLabels[item.status] || item.status} · {item.processed_documents}/{item.total_documents} 个文件</Text>
                          <Progress percent={item.progress} size="small" showInfo={false} />
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>

          <Col xs={24} lg={17}>
            {!batch ? (
              <Card><Empty description="请先新建一个导入任务" /></Card>
            ) : (
              <Space direction="vertical" size={16} className="smart-import__main">
                <Card>
                  <Descriptions title={batch.name} size="small" column={{ xs: 1, sm: 3 }}>
                    <Descriptions.Item label="目标类型">{entityLabels[batch.target_entity_type]}</Descriptions.Item>
                    <Descriptions.Item label="状态"><Tag color={statusColors[batch.status]}>{statusLabels[batch.status] || batch.status}</Tag></Descriptions.Item>
                    <Descriptions.Item label="处理进度">{batch.progress}%</Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card title="上传已有工艺文件">
                  <Dragger
                    accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.docx"
                    multiple={false}
                    showUploadList={false}
                    customRequest={uploadFile}
                    disabled={uploading}
                  >
                    <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                    <p className="ant-upload-text">点击或拖入一个文件</p>
                    <p className="ant-upload-hint">支持 PDF、扫描图片、TIFF 和 DOCX；上传后自动进行安全分页解析。</p>
                  </Dragger>
                </Card>

                <Card title="待处理文件">
                  <Table rowKey="id" columns={columns} dataSource={batch.documents} pagination={false} scroll={{ x: 680 }} />
                </Card>
              </Space>
            )}
          </Col>
        </Row>
      </Spin>

      <Modal
        title="新建导入任务"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => void createBatch()}
        okText="创建"
      >
        <Form form={createForm} layout="vertical" initialValues={{ target_entity_type: 'pqr', access_level: 'private' }}>
          <Form.Item name="name" label="任务名称" rules={[{ required: true, message: '请输入任务名称' }]}>
            <Input maxLength={200} placeholder="例如：历史 PQR 第一批导入" />
          </Form.Item>
          <Form.Item name="target_entity_type" label="导入内容" rules={[{ required: true }]}>
            <Select options={Object.entries(entityLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="access_level" label="可见范围">
            <Radio.Group options={[{ value: 'private', label: '仅自己' }, { value: 'factory', label: '当前工厂' }, { value: 'company', label: '全企业' }]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={<Space><RobotOutlined />AI 结构化提取</Space>}
        open={extractOpen}
        onCancel={() => !extracting && setExtractOpen(false)}
        onOk={() => void runExtraction()}
        confirmLoading={extracting}
        okText="开始提取"
        width={680}
        destroyOnClose
      >
        <Alert
          type="warning"
          showIcon
          message="结果必须由焊接工程师确认"
          description="模型只负责读取文件和填充草稿，不负责确定资格范围，也不会自动发布。"
          className="smart-import__modal-alert"
        />
        <Form form={extractForm} layout="vertical">
          <Form.Item name="schema_source" label="提取模板或模块" rules={[{ required: true, message: '请选择提取字段来源' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="选择与文件相符的模板或模块"
              options={[
                ...templates.map(item => ({ value: `template:${item.id}`, label: `模板 · ${item.name}` })),
                ...modules.map(item => ({ value: `module:${item.id}`, label: `模块 · ${item.name}` })),
              ]}
              notFoundContent="当前类型尚无可用模板或模块"
            />
          </Form.Item>
          <Form.Item name="mode" label="费用来源" rules={[{ required: true }]}>
            <Radio.Group>
              <Radio value="platform" disabled={!capabilities?.platform_available}>使用平台额度{!capabilities?.platform_available && '（管理员未配置）'}</Radio>
              <Radio value="byok">使用自己的 API Key</Radio>
            </Radio.Group>
          </Form.Item>
          {extractionMode === 'platform' && quota && (
            <Alert
              type={quota.can_run_estimate === false ? 'error' : 'success'}
              showIcon
              message={`预计使用 ${quota.estimated_points || 1} 点，剩余 ${quota.remaining_points} 点`}
              description="任务提交时预占，成功后结算；调用失败会自动退回。"
              className="smart-import__modal-alert"
            />
          )}
          {extractionMode === 'byok' && (
            <>
              <Form.Item name="provider" label="接口协议" rules={[{ required: true }]}>
                <Select options={[
                  { value: 'openai_responses', label: 'OpenAI Responses' },
                  { value: 'openai_compatible_chat', label: 'OpenAI 兼容 Chat Completions' },
                ]} />
              </Form.Item>
              <Form.Item name="model" label="模型名称" rules={[{ required: true, message: '请输入模型名称' }]}>
                <Input placeholder="例如：gpt-5.4" maxLength={120} />
              </Form.Item>
              <Form.Item name="api_key" label="临时 API Key" rules={[{ required: true, message: '请输入 API Key' }]} extra="只在本次请求中使用，不会保存到数据库。">
                <Input.Password autoComplete="new-password" maxLength={500} />
              </Form.Item>
              {provider === 'openai_compatible_chat' && (
                <Form.Item name="base_url" label="兼容接口地址（可选）" extra={`管理员允许的域名：${capabilities?.byok_allowed_hosts.join('、') || '无'}`}>
                  <Input placeholder="https://api.openai.com/v1" maxLength={500} />
                </Form.Item>
              )}
            </>
          )}
          <Form.Item name="run_ocr" label="扫描页处理">
            <Radio.Group options={[{ value: true, label: '自动 OCR' }, { value: false, label: '只使用已有文本' }]} />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={<Space><FileSearchOutlined />提取结果与原文证据</Space>}
        open={Boolean(result)}
        onClose={() => setResult(null)}
        width="min(1100px, 96vw)"
        extra={result && (
          <Space>
            <Tag color={result.entity.status === 'published' ? 'success' : 'warning'}>
              {result.entity.status === 'published' ? '已发布' : `待审核 ${pendingFieldCount} 项`}
            </Tag>
            {result.entity.status !== 'published' && (
              <>
                <Button onClick={() => void bulkAccept()}>接受高置信度字段</Button>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={publishing}
                  disabled={pendingFieldCount > 0 || !['wps', 'pqr'].includes(result.entity.entity_type)}
                  onClick={() => void publishEntity()}
                >
                  发布到正式模块
                </Button>
              </>
            )}
          </Space>
        )}
      >
        {result && (
          <Space direction="vertical" size={16} className="smart-import__main">
            <Descriptions bordered size="small" column={{ xs: 1, sm: 3 }}>
              <Descriptions.Item label="字段数">{result.entity.fields.length}</Descriptions.Item>
              <Descriptions.Item label="总 Token">{result.job.total_tokens}</Descriptions.Item>
              <Descriptions.Item label="草稿版本">V{result.entity.version}</Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="id"
              columns={fieldColumns}
              dataSource={result.entity.fields}
              pagination={{ pageSize: 20 }}
              scroll={{ x: 900 }}
              locale={{ emptyText: <Empty description="未识别到可映射字段" /> }}
            />
            <Card title={<Space><EyeOutlined />分页文本</Space>} size="small">
              {result.pages.map(page => (
                <Card key={page.id} type="inner" size="small" title={`第 ${page.page_number} 页`} className="smart-import__page">
                  <pre>{page.text_content || '本页没有可用文本'}</pre>
                </Card>
              ))}
            </Card>
          </Space>
        )}
      </Drawer>

      <Modal
        title="审核识别字段"
        open={Boolean(reviewField)}
        onCancel={() => {
          setReviewField(null)
          reviewForm.resetFields()
        }}
        onOk={() => void applyFieldReview()}
        confirmLoading={reviewing}
        okText="确认"
      >
        <Form form={reviewForm} layout="vertical">
          <Form.Item name="action" label="处理方式" rules={[{ required: true }]}>
            <Radio.Group options={[
              { value: 'accept', label: '接受识别值' },
              { value: 'correct', label: '修正' },
              { value: 'reject', label: '拒绝该字段' },
            ]} />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(previous, current) => previous.action !== current.action}>
            {({ getFieldValue }) => getFieldValue('action') === 'correct' ? (
              <Form.Item name="value" label="修正后的值" rules={[{ required: true, message: '请输入修正后的值' }]}>
                <Input.TextArea rows={4} />
              </Form.Item>
            ) : null}
          </Form.Item>
          <Form.Item name="reason" label="审核说明（可选）">
            <Input.TextArea rows={3} maxLength={1000} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SmartImportPage
