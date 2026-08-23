import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
  Switch,
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
  SettingOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import smartImportService, {
  AIExtractionJob,
  AIQuotaStatus,
  AIProviderConfig,
  EnterpriseAIPolicy,
  DocumentPage,
  ExtractedEntity,
  ExtractedField,
  ImportBatch,
  ImportBatchDetail,
  ImportEntityType,
  SourceDocument,
} from '@/services/smartImport'
import { useNavigate, useSearchParams } from 'react-router-dom'
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

interface UploadResultItem {
  id: string
  filename: string
  status: 'queued' | 'uploading' | 'completed' | 'failed'
  message?: string
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
  partial_success: '部分成功',
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
  partial_success: 'warning',
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
  const [searchParams, setSearchParams] = useSearchParams()
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [batch, setBatch] = useState<ImportBatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState<UploadResultItem[]>([])
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
  const [providerOpen, setProviderOpen] = useState(false)
  const [providerConfigs, setProviderConfigs] = useState<AIProviderConfig[]>([])
  const [enterprisePolicy, setEnterprisePolicy] = useState<EnterpriseAIPolicy | null>(null)
  const [providerSaving, setProviderSaving] = useState(false)
  const [queuedJob, setQueuedJob] = useState<AIExtractionJob | null>(null)
  const [documentJobs, setDocumentJobs] = useState<Record<string, AIExtractionJob>>({})
  const [batchExtractionMode, setBatchExtractionMode] = useState(false)
  const [rotateConfig, setRotateConfig] = useState<AIProviderConfig | null>(null)
  const [createForm] = Form.useForm()
  const [extractForm] = Form.useForm()
  const [reviewForm] = Form.useForm()
  const [providerForm] = Form.useForm()
  const [policyForm] = Form.useForm()
  const [rotateForm] = Form.useForm()
  const uploadQueueRef = useRef<Promise<void>>(Promise.resolve())
  const pendingUploadCountRef = useRef(0)
  const extractionMode = Form.useWatch('mode', extractForm)
  const provider = Form.useWatch('provider', extractForm)
  const loadProviderSettings = useCallback(async () => {
    const configs = await smartImportService.listAIProviderConfigs()
    setProviderConfigs(configs)
    try {
      const policy = await smartImportService.getEnterpriseAIPolicy()
      setEnterprisePolicy(policy)
      policyForm.setFieldsValue({
        ...policy,
        allowed_hosts_text: policy.allowed_hosts.join(', '),
      })
    } catch {
      setEnterprisePolicy(null)
    }
  }, [policyForm])

  const loadBatches = useCallback(async (preferredId?: string) => {
    setLoading(true)
    try {
      const list = await smartImportService.listBatches()
      setBatches(list)
      const nextId = preferredId || batch?.id || list[0]?.id
      if (nextId) {
        const detail = await smartImportService.getBatch(nextId)
        setBatch(detail)
        const jobsByDocument = await Promise.all(
          detail.documents.map(item => smartImportService.listDocumentExtractionJobs(item.id))
        )
        setDocumentJobs(Object.fromEntries(
          detail.documents.flatMap((item, index) => jobsByDocument[index][0] ? [[item.id, jobsByDocument[index][0]]] : [])
        ))
        const jobs = jobsByDocument.flat()
        const active = jobs.find(item => ['queued', 'processing'].includes(item.status))
        if (active) setQueuedJob(active)
      } else setBatch(null)
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
    void loadProviderSettings()
  }, [])

  useEffect(() => {
    const requestedType = searchParams.get('type') as ImportEntityType | null
    if (
      searchParams.get('new') === '1' &&
      requestedType &&
      Object.prototype.hasOwnProperty.call(entityLabels, requestedType)
    ) {
      createForm.setFieldsValue({
        target_entity_type: requestedType,
        access_level: 'private',
        name: `${entityLabels[requestedType]} 历史文件导入`,
      })
      setCreateOpen(true)
      const next = new URLSearchParams(searchParams)
      next.delete('new')
      setSearchParams(next, { replace: true })
    }
  }, [searchParams, setSearchParams, createForm])

  useEffect(() => {
    if (!queuedJob || !['queued', 'processing'].includes(queuedJob.status)) return
    const timer = window.setInterval(async () => {
      try {
        const job = await smartImportService.getExtractionJob(queuedJob.id)
        setQueuedJob(job)
        if (job.status === 'completed') {
          const [entity, pages] = await Promise.all([
            smartImportService.getCurrentDocumentEntity(job.document_id),
            smartImportService.listDocumentPages(job.document_id),
          ])
          setResult({ job, entity, pages })
          await loadBatches(batch?.id)
          message.success('后台 AI 提取完成，结果已进入待审核草稿')
        } else if (job.status === 'failed') {
          message.error(job.error_message || '后台 AI 提取失败')
        }
      } catch {
        // A transient polling failure does not alter the persisted task state.
      }
    }, 1500)
    return () => window.clearInterval(timer)
  }, [queuedJob?.id, queuedJob?.status, batch?.id, loadBatches])

  const selectBatch = async (id: string) => {
    if (uploading) {
      message.warning('文件队列处理完成后才能切换导入任务')
      return
    }
    setLoading(true)
    setUploadResults([])
    try {
      const detail = await smartImportService.getBatch(id)
      setBatch(detail)
      const jobsByDocument = await Promise.all(
        detail.documents.map(item => smartImportService.listDocumentExtractionJobs(item.id))
      )
      setDocumentJobs(Object.fromEntries(
        detail.documents.flatMap((item, index) => jobsByDocument[index][0] ? [[item.id, jobsByDocument[index][0]]] : [])
      ))
      const jobs = jobsByDocument.flat()
      const active = jobs.find(item => ['queued', 'processing'].includes(item.status))
      setQueuedJob(active || null)
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
      setUploadResults([])
      await loadBatches(created.id)
      message.success('导入任务已创建')
    } catch (error) {
      message.error(errorMessage(error, '创建导入任务失败'))
    }
  }

  const uploadFile = (options: any) => {
    if (!batch) return options.onError?.(new Error('请先创建导入任务'))
    const file = options.file as File & { uid?: string }
    const itemId = file.uid || `${file.name}-${Date.now()}`
    const batchId = batch.id
    const targetType = batch.target_entity_type
    pendingUploadCountRef.current += 1
    setUploading(true)
    setUploadResults(items => [
      ...items,
      { id: itemId, filename: file.name, status: 'queued' },
    ])
    uploadQueueRef.current = uploadQueueRef.current.then(async () => {
      setUploadResults(items => items.map(item =>
        item.id === itemId ? { ...item, status: 'uploading' } : item
      ))
      try {
        const document = await smartImportService.uploadDocument(
          batchId,
          file,
          targetType
        )
        await smartImportService.parseDocument(document.id)
        options.onSuccess?.(document)
        setUploadResults(items => items.map(item =>
          item.id === itemId
            ? { ...item, status: 'completed', message: `${document.page_count || 0} 页` }
            : item
        ))
      } catch (error) {
        options.onError?.(error)
        setUploadResults(items => items.map(item =>
          item.id === itemId
            ? { ...item, status: 'failed', message: errorMessage(error, '上传或解析失败') }
            : item
        ))
      } finally {
        pendingUploadCountRef.current -= 1
        if (pendingUploadCountRef.current === 0) {
          setUploading(false)
          await loadBatches(batchId)
        }
      }
    })
  }

  const prepareExtraction = async (document: SourceDocument) => {
    if (!batch) return
    setActiveDocument(document)
    setBatchExtractionMode(false)
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

  const prepareBatchExtraction = async () => {
    if (!batch?.documents.length) {
      message.warning('请先上传文件')
      return
    }
    await prepareExtraction(batch.documents[0])
    setBatchExtractionMode(true)
    extractForm.setFieldValue(
      'mode',
      capabilities?.platform_available ? 'platform' : providerConfigs.length ? 'saved' : undefined
    )
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
          document_id: document.id,
          status: 'completed',
          mode: entity.source_mode === 'ai' ? 'platform' : 'byok',
          input_tokens: 0,
          output_tokens: 0,
          total_tokens: 0,
          progress: 100,
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

  const retryFailedBatch = async () => {
    if (!batch) return
    try {
      const response = await smartImportService.retryFailedBatchJobs(batch.id)
      await loadBatches(batch.id)
      message.success(`已重新排队 ${response.succeeded} 个文件，跳过 ${response.skipped} 个`)
    } catch (error) {
      message.error(errorMessage(error, '批量重试失败'))
    }
  }

  const publishReviewedBatch = async () => {
    if (!batch) return
    setPublishing(true)
    try {
      const response = await smartImportService.publishReviewedBatch(batch.id)
      await loadBatches(batch.id)
      message.success(`已发布 ${response.succeeded} 条，跳过 ${response.skipped} 条，失败 ${response.failed} 条`)
    } catch (error) {
      message.error(errorMessage(error, '批量发布失败'))
    } finally {
      setPublishing(false)
    }
  }

  const runExtraction = async () => {
    if ((!activeDocument && !batchExtractionMode) || !batch) return
    const values = await extractForm.validateFields()
    const [sourceType, sourceId] = String(values.schema_source).split(':', 2)
    setExtracting(true)
    try {
      const payload = {
        mode: (values.mode === 'platform' ? 'platform' : 'byok') as 'platform' | 'byok',
        provider: values.mode === 'byok' ? values.provider : undefined,
        model: values.mode === 'byok' ? values.model?.trim() : undefined,
        base_url: values.mode === 'byok' ? values.base_url?.trim() || undefined : undefined,
        api_key: values.mode === 'byok' ? values.api_key : undefined,
        provider_config_id: values.mode === 'saved' ? values.provider_config_id : undefined,
        template_id: sourceType === 'template' ? sourceId : undefined,
        module_id: sourceType === 'module' ? sourceId : undefined,
        run_ocr: values.run_ocr,
      }
      if (batchExtractionMode) {
        const response = await smartImportService.queueBatchExtraction(batch.id, payload)
        message.success(`批量任务已提交：${response.succeeded} 个排队，${response.skipped} 个跳过，${response.failed} 个失败`)
      } else if (values.mode === 'byok') {
        const response = await smartImportService.extractDocument(activeDocument!.id, payload)
        setResult(response)
        message.success('AI 提取完成，结果已进入待审核草稿')
      } else {
        const response = await smartImportService.queueExtraction(activeDocument!.id, payload)
        setQueuedJob(response.job)
        message.success('任务已进入后台队列，可离开当前页面继续其他工作')
      }
      setExtractOpen(false)
      extractForm.setFieldValue('api_key', undefined)
      await loadBatches(batch?.id)
    } catch (error) {
      message.error(errorMessage(error, 'AI 提取失败'))
    } finally {
      setExtracting(false)
    }
  }

  const createProviderConfig = async () => {
    const values = await providerForm.validateFields()
    setProviderSaving(true)
    try {
      await smartImportService.createAIProviderConfig(values)
      providerForm.resetFields()
      await loadProviderSettings()
      message.success('模型配置已加密保存')
    } catch (error) {
      message.error(errorMessage(error, '保存模型配置失败'))
    } finally {
      setProviderSaving(false)
    }
  }

  const saveEnterprisePolicy = async () => {
    const values = await policyForm.validateFields()
    try {
      const policy = await smartImportService.updateEnterpriseAIPolicy({
        allow_ai: values.allow_ai,
        allow_external_providers: values.allow_external_providers,
        allow_personal_keys: values.allow_personal_keys,
        require_enterprise_key: values.require_enterprise_key,
        allowed_hosts: String(values.allowed_hosts_text || '').split(/[，,\s]+/).filter(Boolean),
      })
      setEnterprisePolicy(policy)
      message.success('企业 AI 使用策略已更新')
    } catch (error) {
      message.error(errorMessage(error, '更新企业策略失败'))
    }
  }

  const rotateProviderKey = async () => {
    if (!rotateConfig) return
    const values = await rotateForm.validateFields()
    try {
      await smartImportService.rotateAIProviderKey(rotateConfig.id, values.api_key)
      rotateForm.resetFields()
      setRotateConfig(null)
      await loadProviderSettings()
      message.success('API Key 已轮换，旧密钥立即失效')
    } catch (error) {
      message.error(errorMessage(error, '轮换 API Key 失败'))
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
      render: (status: string, row) => {
        const job = documentJobs[row.id]
        return (
          <Space direction="vertical" size={2}>
            <Tag color={statusColors[status]}>{statusLabels[status] || status}</Tag>
            {job && <Tag color={statusColors[job.status]}>{statusLabels[job.status] || job.status} {job.progress}%</Tag>}
          </Space>
        )
      },
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
  ], [batch?.id, loadBatches, documentJobs])

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
        <Space>
          <Button icon={<SettingOutlined />} onClick={() => { setProviderOpen(true); void loadProviderSettings() }}>模型配置</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建导入任务</Button>
        </Space>
      </div>

      <Alert
        showIcon
        type="info"
        message="AI 是可选输入方式"
        description="可使用平台额度、临时 API Key 或后端加密保存的个人/企业配置；也可以继续使用原有手工新建功能。"
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

      {queuedJob && (
        <Card size="small" className="smart-import__quota">
          <Space wrap>
            <RobotOutlined />
            <Text strong>后台提取任务</Text>
            <Tag color={queuedJob.status === 'completed' ? 'success' : queuedJob.status === 'failed' ? 'error' : queuedJob.status === 'cancelled' ? 'default' : 'processing'}>
              {statusLabels[queuedJob.status] || queuedJob.status}
            </Tag>
            <Progress percent={queuedJob.progress || 0} size="small" style={{ width: 180 }} />
            {['queued', 'processing'].includes(queuedJob.status) && (
              <Button size="small" danger onClick={async () => {
                try { setQueuedJob(await smartImportService.cancelExtractionJob(queuedJob.id)); message.success('任务已取消') }
                catch (error) { message.error(errorMessage(error, '取消任务失败')) }
              }}>取消</Button>
            )}
            {['failed', 'cancelled'].includes(queuedJob.status) && (
              <Button size="small" onClick={async () => {
                try { const response = await smartImportService.retryExtractionJob(queuedJob.id); setQueuedJob(response.job); message.success('重试任务已进入队列') }
                catch (error) { message.error(errorMessage(error, '重试任务失败')) }
              }}>重试</Button>
            )}
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
                    multiple
                    maxCount={50}
                    showUploadList={false}
                    customRequest={uploadFile}
                    disabled={uploading}
                  >
                    <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                    <p className="ant-upload-text">点击或拖入一个或多个文件</p>
                    <p className="ant-upload-hint">支持 PDF、扫描图片、TIFF 和 DOCX；文件会依次上传，单个失败不影响其他文件。</p>
                  </Dragger>
                  {uploadResults.length > 0 && (
                    <List
                      size="small"
                      style={{ marginTop: 12 }}
                      dataSource={uploadResults}
                      renderItem={item => (
                        <List.Item key={item.id}>
                          <List.Item.Meta title={item.filename} description={item.message} />
                          <Tag color={item.status === 'completed' ? 'success' : item.status === 'failed' ? 'error' : 'processing'}>
                            {item.status === 'queued' ? '等待上传' : item.status === 'uploading' ? '上传解析中' : item.status === 'completed' ? '已完成' : '失败'}
                          </Tag>
                        </List.Item>
                      )}
                    />
                  )}
                </Card>

                <Card
                  title="待处理文件"
                  extra={(
                    <Space>
                      <Button icon={<RobotOutlined />} onClick={() => void prepareBatchExtraction()}>批量 AI 提取</Button>
                      <Button onClick={() => void retryFailedBatch()}>重试失败项</Button>
                      <Button type="primary" loading={publishing} onClick={() => Modal.confirm({
                        title: '批量发布已审核草稿？',
                        content: '仅发布所有字段已确认的 WPS/PQR，其他文件会自动跳过。',
                        onOk: publishReviewedBatch,
                      })}>批量发布</Button>
                    </Space>
                  )}
                >
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
        title={<Space><RobotOutlined />{batchExtractionMode ? '批量 AI 结构化提取' : 'AI 结构化提取'}</Space>}
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
              <Radio value="saved" disabled={!providerConfigs.length}>使用已保存配置{!providerConfigs.length && '（暂无）'}</Radio>
              <Radio value="byok" disabled={batchExtractionMode}>使用自己的 API Key{batchExtractionMode && '（批量任务不传递临时 Key）'}</Radio>
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
          {extractionMode === 'saved' && (
            <Form.Item name="provider_config_id" label="已保存模型配置" rules={[{ required: true, message: '请选择模型配置' }]}>
              <Select
                options={providerConfigs.map(item => ({
                  value: item.id,
                  label: `${item.scope_type === 'enterprise' ? '企业' : '个人'} · ${item.name} · ${item.model} · ${item.masked_api_key}`,
                }))}
              />
            </Form.Item>
          )}
          <Form.Item name="run_ocr" label="扫描页处理">
            <Radio.Group options={[{ value: true, label: '自动 OCR' }, { value: false, label: '只使用已有文本' }]} />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={<Space><SettingOutlined />模型与 API Key 配置</Space>}
        open={providerOpen}
        onClose={() => setProviderOpen(false)}
        width="min(720px, 96vw)"
      >
        <Alert
          type="info"
          showIcon
          message="API Key 只以密文保存在后端"
          description="页面仅显示末四位。保存后可连接测试、轮换或立即停用，浏览器不会再次取得完整 Key。"
          className="smart-import__modal-alert"
        />
        <Card title="已保存配置" size="small">
          <List
            dataSource={providerConfigs}
            locale={{ emptyText: '暂无已保存配置' }}
            renderItem={item => (
              <List.Item actions={[
                <Button key="test" size="small" onClick={async () => {
                  try {
                    const tested = await smartImportService.testAIProviderConfig(item.id)
                    await loadProviderSettings()
                    tested.last_test_status === 'success' ? message.success('连接测试成功') : message.error(tested.last_error || '连接测试失败')
                  } catch (error) { message.error(errorMessage(error, '连接测试失败')) }
                }}>测试</Button>,
                <Button key="rotate" size="small" onClick={() => setRotateConfig(item)}>轮换 Key</Button>,
                <Button key="disable" size="small" danger icon={<DeleteOutlined />} onClick={() => Modal.confirm({
                  title: `停用“${item.name}”？`,
                  content: '停用后现有提取任务不能再使用该配置。',
                  onOk: async () => { await smartImportService.disableAIProviderConfig(item.id); await loadProviderSettings() },
                })}>停用</Button>,
              ]}>
                <List.Item.Meta
                  title={<Space><Text strong>{item.name}</Text><Tag>{item.scope_type === 'enterprise' ? '企业' : '个人'}</Tag><Tag color={item.last_test_status === 'success' ? 'success' : item.last_test_status === 'failed' ? 'error' : 'default'}>{item.last_test_status === 'success' ? '连接正常' : item.last_test_status === 'failed' ? '连接失败' : '未测试'}</Tag></Space>}
                  description={`${item.provider} · ${item.model} · ${item.masked_api_key}`}
                />
              </List.Item>
            )}
          />
        </Card>
        <Card title="新增配置" size="small" style={{ marginTop: 16 }}>
          <Form form={providerForm} layout="vertical" initialValues={{ scope_type: 'personal', provider: 'openai_responses', base_url: 'https://api.openai.com/v1' }}>
            <Row gutter={12}>
              <Col span={12}><Form.Item name="scope_type" label="使用范围" rules={[{ required: true }]}><Select options={[{ value: 'personal', label: '仅自己' }, { value: 'enterprise', label: '当前企业（需管理员）' }]} /></Form.Item></Col>
              <Col span={12}><Form.Item name="name" label="配置名称" rules={[{ required: true }]}><Input maxLength={100} /></Form.Item></Col>
            </Row>
            <Row gutter={12}>
              <Col span={12}><Form.Item name="provider" label="接口协议" rules={[{ required: true }]}><Select options={[{ value: 'openai_responses', label: 'OpenAI Responses' }, { value: 'openai_compatible_chat', label: '兼容 Chat Completions' }]} /></Form.Item></Col>
              <Col span={12}><Form.Item name="model" label="模型名称" rules={[{ required: true }]}><Input maxLength={120} /></Form.Item></Col>
            </Row>
            <Form.Item name="base_url" label="接口地址" rules={[{ required: true }]}><Input maxLength={500} /></Form.Item>
            <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}><Input.Password autoComplete="new-password" maxLength={500} /></Form.Item>
            <Button type="primary" loading={providerSaving} onClick={() => void createProviderConfig()}>加密保存</Button>
          </Form>
        </Card>
        {enterprisePolicy && (
          <Card title="企业 AI 使用策略" size="small" style={{ marginTop: 16 }}>
            <Form form={policyForm} layout="vertical">
              <Form.Item name="allow_ai" label="允许使用 AI" valuePropName="checked"><Switch /></Form.Item>
              <Form.Item name="allow_personal_keys" label="允许员工使用个人或临时 Key" valuePropName="checked"><Switch /></Form.Item>
              <Form.Item name="allow_external_providers" label="允许外部模型服务" valuePropName="checked"><Switch /></Form.Item>
              <Form.Item name="require_enterprise_key" label="强制使用企业统一配置" valuePropName="checked"><Switch /></Form.Item>
              <Form.Item name="allowed_hosts_text" label="额外允许域名" extra="多个域名用逗号分隔"><Input placeholder="例如：ai.example.com" /></Form.Item>
              <Button onClick={() => void saveEnterprisePolicy()}>保存企业策略</Button>
            </Form>
          </Card>
        )}
      </Drawer>

      <Modal title={`轮换 ${rotateConfig?.name || ''} 的 API Key`} open={Boolean(rotateConfig)} onCancel={() => setRotateConfig(null)} onOk={() => void rotateProviderKey()} okText="确认轮换">
        <Form form={rotateForm} layout="vertical">
          <Form.Item name="api_key" label="新 API Key" rules={[{ required: true }]} extra="保存后旧密钥立即从本系统失效。"><Input.Password autoComplete="new-password" maxLength={500} /></Form.Item>
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
