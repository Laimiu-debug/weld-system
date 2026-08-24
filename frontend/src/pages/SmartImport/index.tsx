import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Divider,
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
  Tooltip,
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
  HistoryOutlined,
  LinkOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { FormInstance } from 'antd'
import smartImportService, {
  AIExtractionJob,
  AIQuotaStatus,
  AIUsageReport,
  AIProviderConfig,
  EnterpriseAIPolicy,
  DocumentPage,
  ExtractedEntity,
  ExtractedField,
  ImportBatch,
  ImportBatchDetail,
  ImportEntityType,
  SourceDocument,
  TemplateRecommendationResult,
  WelderImportReview,
  WorkbenchValidation,
  ImportReviewHistory,
} from '@/services/smartImport'
import { useNavigate, useSearchParams } from 'react-router-dom'
import customModuleService, { CustomModuleSummary } from '@/services/customModules'
import wpsTemplateService, { WPSTemplateSummary } from '@/services/wpsTemplates'
import { workspaceService } from '@/services/workspace'
import { usePreferencesStore } from '@/store/preferencesStore'
import {
  AI_DATA_OUTBOUND_NOTICE_VERSION,
  aiDataOutboundNotice,
  hasPersistentAIDataAuthorization,
} from '@/utils/aiPrivacy'
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

const sha256Hex = async (value: string) => {
  const bytes = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('')
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

const providerPresets = [
  { value: 'openai', label: 'OpenAI', provider: 'openai_responses', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { value: 'deepseek', label: 'DeepSeek', provider: 'openai_compatible_chat', baseUrl: 'https://api.deepseek.com', model: 'deepseek-v4-flash' },
  { value: 'qwen', label: '阿里云百炼 / 通义千问', provider: 'openai_compatible_chat', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { value: 'kimi', label: 'Moonshot / Kimi', provider: 'openai_compatible_chat', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { value: 'zhipu', label: '智谱 GLM', provider: 'openai_compatible_chat', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { value: 'siliconflow', label: '硅基流动', provider: 'openai_compatible_chat', baseUrl: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-72B-Instruct' },
  { value: 'custom', label: '自定义兼容接口', provider: 'openai_compatible_chat', baseUrl: '', model: '' },
] as const

type ProviderPreset = typeof providerPresets[number]

function applyProviderPreset(form: FormInstance, value: string) {
  const preset = providerPresets.find(item => item.value === value) as ProviderPreset | undefined
  if (!preset) return
  form.setFieldsValue({
    provider: preset.provider,
    base_url: preset.baseUrl,
    model: preset.model,
  })
}

function parseManualValue(fieldType: string, value: string): unknown {
  if (['number', 'integer'].includes(fieldType)) {
    const parsed = Number(value)
    if (!Number.isNaN(parsed)) return fieldType === 'integer' ? Math.trunc(parsed) : parsed
    throw new Error('请输入有效数值')
  }
  if (fieldType === 'checkbox') {
    if (['true', '是', '1'].includes(value)) return true
    if (['false', '否', '0'].includes(value)) return false
  }
  if (['table', 'object', 'array'].includes(fieldType)) {
    try { return JSON.parse(value) } catch { throw new Error('请输入合法 JSON') }
  }
  return value
}

const SmartImportPage: React.FC = () => {
  const navigate = useNavigate()
  const workspace = workspaceService.getCurrentWorkspaceFromStorage()
  const isEnterpriseWorkspace = workspace?.type === 'enterprise'
  const workspaceLabel = isEnterpriseWorkspace ? '企业' : '个人'
  const batchExtractionPreferenceKey = `smart-import:batch-ai:${workspace?.id || 'personal'}`
  const pageStateKey = `smart-import:page-state:${workspace?.id || 'personal'}`
  const preferences = usePreferencesStore(state => state.preferences)
  const persistentOutboundAuthorization = hasPersistentAIDataAuthorization(preferences)
  const [searchParams, setSearchParams] = useSearchParams()
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [batch, setBatch] = useState<ImportBatchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState<UploadResultItem[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteRelatedData, setDeleteRelatedData] = useState(false)
  const [deletingBatch, setDeletingBatch] = useState(false)
  const [extractOpen, setExtractOpen] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [activeDocument, setActiveDocument] = useState<SourceDocument | null>(null)
  const [capabilities, setCapabilities] = useState<AICapabilities | null>(null)
  const [quota, setQuota] = useState<AIQuotaStatus | null>(null)
  const [aiUsage, setAIUsage] = useState<AIUsageReport | null>(null)
  const [templates, setTemplates] = useState<WPSTemplateSummary[]>([])
  const [templateRecommendation, setTemplateRecommendation] = useState<TemplateRecommendationResult | null>(null)
  const [modules, setModules] = useState<CustomModuleSummary[]>([])
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [reviewField, setReviewField] = useState<ExtractedField | null>(null)
  const [reviewing, setReviewing] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [welderReview, setWelderReview] = useState<WelderImportReview | null>(null)
  const [welderChoices, setWelderChoices] = useState<Record<string, number | 'new'>>({})
  const [workbenchValidation, setWorkbenchValidation] = useState<WorkbenchValidation | null>(null)
  const [reviewHistory, setReviewHistory] = useState<ImportReviewHistory[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [activePageNumber, setActivePageNumber] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(pageStateKey) || '{}')
      return Number(saved.pageNumber) > 0 ? Number(saved.pageNumber) : 1
    } catch {
      return 1
    }
  })
  const [activeEvidence, setActiveEvidence] = useState<ExtractedField['evidence'][number] | null>(null)
  const [pagePreviewUrl, setPagePreviewUrl] = useState<string | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [bindField, setBindField] = useState<ExtractedField | null>(null)
  const [manualFieldOpen, setManualFieldOpen] = useState(false)
  const [manualFieldSaving, setManualFieldSaving] = useState(false)
  const [binding, setBinding] = useState(false)
  const [providerOpen, setProviderOpen] = useState(false)
  const [providerConfigs, setProviderConfigs] = useState<AIProviderConfig[]>([])
  const [enterprisePolicy, setEnterprisePolicy] = useState<EnterpriseAIPolicy | null>(null)
  const [providerSaving, setProviderSaving] = useState(false)
  const [providerTesting, setProviderTesting] = useState(false)
  const [editConfig, setEditConfig] = useState<AIProviderConfig | null>(null)
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
  const [editProviderForm] = Form.useForm()
  const [bindForm] = Form.useForm()
  const [manualFieldForm] = Form.useForm()
  const uploadQueueRef = useRef<Promise<void>>(Promise.resolve())
  const pendingUploadCountRef = useRef(0)
  const extractionMode = Form.useWatch('mode', extractForm)
  const extractionProviderPreset = Form.useWatch('provider_preset', extractForm)
  const extractionProviderConfigId = Form.useWatch('provider_config_id', extractForm)
  const extractionBaseUrl = Form.useWatch('base_url', extractForm)
  const savedProviderPreset = Form.useWatch('provider_preset', providerForm)
  const bindAction = Form.useWatch('action', bindForm)
  const manualFieldTarget = Form.useWatch('target', manualFieldForm)
  const extractionProviderHost = useMemo(() => {
    if (extractionMode === 'saved') {
      const config = providerConfigs.find(item => item.id === extractionProviderConfigId)
      if (!config) return ''
      try { return new URL(config.base_url).hostname }
      catch { return '' }
    }
    if (extractionMode === 'byok') {
      try { return new URL(extractionBaseUrl || '').hostname }
      catch { return '' }
    }
    return capabilities?.platform_host || ''
  }, [extractionMode, extractionProviderConfigId, extractionBaseUrl, providerConfigs, capabilities?.platform_host])
  const loadProviderSettings = useCallback(async () => {
    const configs = await smartImportService.listAIProviderConfigs()
    setProviderConfigs(configs)
    if (!isEnterpriseWorkspace) {
      setEnterprisePolicy(null)
      return
    }
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
  }, [isEnterpriseWorkspace, policyForm])

  const loadBatches = useCallback(async (preferredId?: string) => {
    setLoading(true)
    try {
      const list = await smartImportService.listBatches()
      setBatches(list)
      let persisted: { batchId?: string; documentId?: string } = {}
      try { persisted = JSON.parse(localStorage.getItem(pageStateKey) || '{}') }
      catch { persisted = {} }
      const persistedBatchExists = list.some(item => item.id === persisted.batchId)
      const nextId = preferredId || batch?.id || (persistedBatchExists ? persisted.batchId : undefined) || list[0]?.id
      if (nextId) {
        const detail = await smartImportService.getBatch(nextId)
        setBatch(detail)
        localStorage.setItem(pageStateKey, JSON.stringify({
          ...persisted,
          batchId: detail.id,
          documentId: detail.documents.some(item => item.id === persisted.documentId)
            ? persisted.documentId
            : undefined,
        }))
        setActiveDocument(
          detail.documents.find(item => item.id === persisted.documentId) || null
        )
        const jobsByDocument = await Promise.all(
          detail.documents.map(item => smartImportService.listDocumentExtractionJobs(item.id))
        )
        setDocumentJobs(Object.fromEntries(
          detail.documents.flatMap((item, index) => {
            const latestExtraction = jobsByDocument[index].find(
              job => job.progress_detail?.job_kind !== 'parse'
            )
            return latestExtraction ? [[item.id, latestExtraction]] : []
          })
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
  }, [batch?.id, pageStateKey])

  useEffect(() => {
    if (!batch) return
    try {
      const current = JSON.parse(localStorage.getItem(pageStateKey) || '{}')
      localStorage.setItem(pageStateKey, JSON.stringify({
        ...current,
        batchId: batch?.id,
        documentId: activeDocument?.id,
        pageNumber: activePageNumber,
      }))
    } catch {
      // Ignore malformed legacy state; the next interaction will replace it.
    }
  }, [pageStateKey, batch, activeDocument?.id, activePageNumber])

  useEffect(() => {
    void loadBatches()
    smartImportService.getAICapabilities().then(setCapabilities).catch(() => undefined)
    smartImportService.getAIQuota().then(setQuota).catch(() => undefined)
    smartImportService.getAIUsage().then(setAIUsage).catch(() => undefined)
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
        if (job.status === 'completed' && job.progress_detail?.job_kind === 'parse') {
          await loadBatches(batch?.id)
          message.success('后台文件解析完成，可以开始 AI 提取或手工录入')
        } else if (job.status === 'completed') {
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

  const refreshWorkbench = useCallback(async (entityId: string) => {
    const [validation, history] = await Promise.all([
      smartImportService.getWorkbenchValidation(entityId),
      smartImportService.getReviewHistory(entityId),
    ])
    setWorkbenchValidation(validation)
    setReviewHistory(history)
  }, [])

  useEffect(() => {
    if (!result) {
      setWorkbenchValidation(null)
      setReviewHistory([])
      setActiveEvidence(null)
      return
    }
    setActivePageNumber(result.pages[0]?.page_number || 1)
    void refreshWorkbench(result.entity.id).catch(error => {
      message.error(errorMessage(error, '加载发布前检查失败'))
    })
  }, [result?.entity.id, refreshWorkbench])

  useEffect(() => {
    if (!result) return
    const document = batch?.documents.find(item => item.id === result.entity.document_id) || activeDocument
    const visual = document?.mime_type === 'application/pdf' || document?.mime_type?.startsWith('image/')
    if (!visual) {
      setPagePreviewUrl(null)
      return
    }
    let disposed = false
    let objectUrl: string | null = null
    setPreviewLoading(true)
    smartImportService.getDocumentPagePreview(result.entity.document_id, activePageNumber)
      .then(blob => {
        if (disposed) return
        objectUrl = URL.createObjectURL(blob)
        setPagePreviewUrl(objectUrl)
      })
      .catch(() => setPagePreviewUrl(null))
      .finally(() => !disposed && setPreviewLoading(false))
    return () => {
      disposed = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [result?.entity.document_id, activePageNumber, batch?.documents, activeDocument])

  const focusEvidence = (evidence: ExtractedField['evidence'][number]) => {
    setActiveEvidence(evidence)
    setActivePageNumber(evidence.page_number)
  }

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
      setActiveDocument(null)
      localStorage.setItem(pageStateKey, JSON.stringify({ batchId: id, pageNumber: 1 }))
      const jobsByDocument = await Promise.all(
        detail.documents.map(item => smartImportService.listDocumentExtractionJobs(item.id))
      )
      setDocumentJobs(Object.fromEntries(
        detail.documents.flatMap((item, index) => {
          const latestExtraction = jobsByDocument[index].find(
            job => job.progress_detail?.job_kind !== 'parse'
          )
          return latestExtraction ? [[item.id, latestExtraction]] : []
        })
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
        const queued = await smartImportService.queueDocumentParse(document.id)
        setQueuedJob(queued.job)
        options.onSuccess?.(document)
        setUploadResults(items => items.map(item =>
          item.id === itemId
            ? { ...item, status: 'completed', message: '已进入后台解析队列' }
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

  const deleteCurrentBatch = async () => {
    if (!batch) return
    setDeletingBatch(true)
    try {
      const result = await smartImportService.deleteBatch(batch.id, deleteRelatedData)
      setDeleteOpen(false)
      setDeleteRelatedData(false)
      setBatch(null)
      setQueuedJob(null)
      setResult(null)
      await loadBatches()
      message.success(
        deleteRelatedData
          ? `导入任务已删除，并停用 ${result.related_records_deleted} 条关联业务数据`
          : '导入任务已删除，已发布的业务数据已保留'
      )
    } catch (error) {
      message.error(errorMessage(error, '删除导入任务失败'))
    } finally {
      setDeletingBatch(false)
    }
  }

  const prepareExtraction = async (document: SourceDocument) => {
    if (!batch) return
    setActiveDocument(document)
    setBatchExtractionMode(false)
    setTemplateRecommendation(null)
    setExtractOpen(true)
    smartImportService.getAIQuota(document.page_count || 1).then(setQuota).catch(() => undefined)
    extractForm.resetFields()
    extractForm.setFieldsValue({
      mode: capabilities?.platform_available ? 'platform' : 'byok',
      provider_preset: 'openai',
      provider: 'openai_responses',
      base_url: 'https://api.openai.com/v1',
      model: 'gpt-4o-mini',
      schema_source: ['wps', 'pqr', 'welder'].includes(batch.target_entity_type)
        ? 'builtin:auto'
        : undefined,
      run_ocr: true,
      outbound_privacy_consent: false,
    })
    try {
      const [templateResponse, moduleList, recommendation] = await Promise.all([
        batch.target_entity_type === 'welder'
          ? Promise.resolve(null)
          : wpsTemplateService.getTemplates({
              module_type: batch.target_entity_type,
              limit: 100,
            }),
        customModuleService.getCustomModules({ limit: 100 }),
        smartImportService.recommendTemplates(document.id),
      ])
      setTemplates(templateResponse?.data?.items || [])
      setModules(
        moduleList.filter(
          item => item.module_type === batch.target_entity_type || item.module_type === 'common'
        )
      )
      setTemplateRecommendation(recommendation)
      const recommended = recommendation.recommendations[0]
      if (recommended && recommended.score >= 55) {
        extractForm.setFieldValue('schema_source', `template:${recommended.template_id}`)
      }
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
    let remembered: { mode?: 'platform' | 'saved'; provider_config_id?: string; run_ocr?: boolean } = {}
    try {
      remembered = JSON.parse(localStorage.getItem(batchExtractionPreferenceKey) || '{}')
    } catch {
      remembered = {}
    }
    const rememberedConfigExists = providerConfigs.some(item => item.id === remembered.provider_config_id)
    const mode = remembered.mode === 'saved' && rememberedConfigExists
      ? 'saved'
      : remembered.mode === 'platform' && capabilities?.platform_available
        ? 'platform'
        : capabilities?.platform_available
          ? 'platform'
          : providerConfigs.length
            ? 'saved'
            : undefined
    extractForm.setFieldsValue({
      mode,
      provider_config_id: mode === 'saved'
        ? (rememberedConfigExists ? remembered.provider_config_id : providerConfigs[0]?.id)
        : undefined,
      run_ocr: remembered.run_ocr ?? true,
      outbound_privacy_consent: false,
    })
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
          progress_detail: {
            job_kind: 'extraction',
            phase: 'completed',
            fields: { completed: entity.fields.length, total: entity.fields.length },
          },
        },
      })
    } catch (error) {
      message.error(errorMessage(error, '该文件还没有可审核的提取草稿'))
    }
  }

  const applyFieldReview = async () => {
    if (!result || !reviewField) return
    const values = await reviewForm.validateFields()
    const previousResult = result
    const nextStatus: ExtractedField['review_status'] = values.action === 'accept'
      ? 'accepted'
      : values.action === 'correct'
        ? 'corrected'
        : 'rejected'
    setReviewing(true)
    // Reflect the confirmed action immediately. The subsequent GET is the
    // authoritative reconciliation and also avoids stale nested table rows.
    setResult(current => current?.entity.id === result.entity.id ? {
      ...current,
      entity: {
        ...current.entity,
        fields: current.entity.fields.map(field => field.id === reviewField.id
          ? { ...field, review_status: nextStatus }
          : field),
      },
    } : current)
    try {
      const data = values.action === 'correct'
        ? { ...values, value: parseEditedValue(reviewField.normalized_value, values.value) }
        : values
      const entity = await smartImportService.reviewField(
        result.entity.id,
        reviewField.id,
        data
      )
      const refreshedEntity = await smartImportService.getExtractedEntity(entity.id)
      setResult(current => current ? { ...current, entity: refreshedEntity } : current)
      await refreshWorkbench(entity.id)
      setReviewField(null)
      reviewForm.resetFields()
      message.success(values.action === 'correct' ? '字段已修正' : '字段审核状态已更新')
    } catch (error) {
      setResult(previousResult)
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
      await refreshWorkbench(entity.id)
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

  const applyUnmappedBinding = async () => {
    if (!result || !bindField) return
    const values = await bindForm.validateFields()
    setBinding(true)
    try {
      const option = workbenchValidation?.binding_options.find(item =>
        `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}` === values.target
      )
      const entity = await smartImportService.bindUnmappedField(result.entity.id, bindField.id, {
        ...values,
        target: undefined,
        target_field_id: option?.field_id,
        target_module_id: option?.module_id,
        target_instance_id: option?.instance_id,
        target_field_key: option?.field_key,
      })
      setResult({ ...result, entity })
      await refreshWorkbench(entity.id)
      setBindField(null)
      bindForm.resetFields()
      message.success(values.action === 'create_custom' ? '已创建企业字段并完成绑定' : '未映射内容已绑定')
    } catch (error) {
      message.error(errorMessage(error, '字段绑定失败'))
    } finally {
      setBinding(false)
    }
  }

  const addManualField = async () => {
    if (!result || !workbenchValidation) return
    const values = await manualFieldForm.validateFields()
    const option = workbenchValidation.binding_options.find(item =>
      `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}` === values.target
    )
    if (!option) return
    setManualFieldSaving(true)
    try {
      const entity = await smartImportService.addManualWorkbenchField(result.entity.id, {
        target_field_id: option.field_id,
        target_module_id: option.module_id,
        target_instance_id: option.instance_id,
        target_field_key: option.field_key,
        value: parseManualValue(option.field_type, values.value),
        reason: values.reason,
      })
      setResult({ ...result, entity })
      await refreshWorkbench(entity.id)
      manualFieldForm.resetFields()
      setManualFieldOpen(false)
      message.success('字段已手工录入并记入审核历史')
    } catch (error) {
      message.error(errorMessage(error, '手工录入字段失败'))
    } finally {
      setManualFieldSaving(false)
    }
  }

  const openWelderReview = async () => {
    if (!result) return
    try {
      const review = await smartImportService.getWelderImportReview(result.entity.id)
      setWelderReview(review)
      setWelderChoices(review.records.reduce<Record<string, number | 'new'>>((choices, item) => {
        if (item.identity_status === 'matched' && item.candidates[0]) {
          choices[item.record_key] = item.candidates[0].id
        } else if (item.identity_status === 'new') {
          choices[item.record_key] = 'new'
        }
        return choices
      }, {}))
    } catch (error) {
      message.error(errorMessage(error, '加载焊工资质审核失败'))
    }
  }

  const publishWelderReview = async () => {
    if (!result || !welderReview) return
    const unresolved = welderReview.records.filter(item =>
      item.identity_status === 'ambiguous' && !welderChoices[item.record_key]
    )
    if (unresolved.length) {
      message.warning(`还有 ${unresolved.length} 条重名记录需要确认`)
      return
    }
    setPublishing(true)
    try {
      const published = await smartImportService.publishWelderImport(
        result.entity.id,
        welderReview.records.map(item => ({
          record_key: item.record_key,
          existing_welder_id: typeof welderChoices[item.record_key] === 'number'
            ? welderChoices[item.record_key] as number
            : undefined,
          create_new: welderChoices[item.record_key] === 'new',
          skip_duplicate: item.certificate_status === 'duplicate',
        }))
      )
      setWelderReview(null)
      setResult({ ...result, entity: { ...result.entity, status: 'published' } })
      await loadBatches(batch?.id)
      Modal.success({
        title: '焊工与资质已导入',
        content: '已写入现有焊工、证书和持证项目，重复证书已跳过，续证已更新。',
        okText: '查看焊工',
        onOk: () => navigate(published.detail_url),
      })
    } catch (error) {
      message.error(errorMessage(error, '焊工资质发布失败'))
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
      let outboundConsentId: string | undefined
      let outboundConsentIds: Record<string, string> | undefined
      if (batch.target_entity_type === 'pqr') {
        if (!extractionProviderHost) throw new Error('无法识别外部模型服务域名，请检查模型配置')
        const notice = aiDataOutboundNotice(extractionProviderHost)
        const privacyNoticeHash = await sha256Hex(notice)
        const documents = batchExtractionMode ? batch.documents : [activeDocument!]
        const consents = await Promise.all(documents.map(document => smartImportService.createOutboundConsent({
          document_id: document.id,
          provider_host: extractionProviderHost,
          purpose: `提取 ${document.original_filename} 的 PQR 结构化字段`,
          privacy_notice_version: AI_DATA_OUTBOUND_NOTICE_VERSION,
          privacy_notice_hash: privacyNoticeHash,
          authorized: true,
        })))
        if (batchExtractionMode) {
          outboundConsentIds = Object.fromEntries(documents.map((document, index) => [document.id, consents[index].id]))
        } else {
          outboundConsentId = consents[0].id
        }
      }
      const payload = {
        mode: (values.mode === 'platform' ? 'platform' : 'byok') as 'platform' | 'byok',
        provider: values.mode === 'byok' ? values.provider : undefined,
        model: values.mode === 'byok' ? values.model?.trim() : undefined,
        base_url: values.mode === 'byok' ? values.base_url?.trim() || undefined : undefined,
        api_key: values.mode === 'byok' ? values.api_key : undefined,
        provider_config_id: values.mode === 'saved' ? values.provider_config_id : undefined,
        outbound_consent_id: outboundConsentId,
        outbound_consent_ids: outboundConsentIds,
        template_id: sourceType === 'template' ? sourceId : undefined,
        module_id: sourceType === 'module' ? sourceId : undefined,
        run_ocr: values.run_ocr,
      }
      if (batchExtractionMode) {
        const response = await smartImportService.queueBatchExtraction(batch.id, payload)
        localStorage.setItem(batchExtractionPreferenceKey, JSON.stringify({
          mode: values.mode,
          provider_config_id: values.mode === 'saved' ? values.provider_config_id : undefined,
          run_ocr: values.run_ocr,
        }))
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
      const { provider_preset: _preset, ...payload } = values
      await smartImportService.createAIProviderConfig(payload)
      providerForm.resetFields()
      await loadProviderSettings()
      message.success('模型配置已加密保存')
    } catch (error) {
      message.error(errorMessage(error, '保存模型配置失败'))
    } finally {
      setProviderSaving(false)
    }
  }

  const testDraftProviderConfig = async () => {
    const values = await providerForm.validateFields(['provider', 'base_url', 'model', 'api_key'])
    setProviderTesting(true)
    try {
      const result = await smartImportService.testAIProviderConnection({
        provider: values.provider,
        base_url: values.base_url.trim(),
        model: values.model.trim(),
        api_key: values.api_key,
      })
      result.success ? message.success(result.message) : message.error(result.message)
    } catch (error) {
      message.error(errorMessage(error, '连接测试失败'))
    } finally {
      setProviderTesting(false)
    }
  }

  const openEditProviderConfig = (item: AIProviderConfig) => {
    setEditConfig(item)
    editProviderForm.setFieldsValue({
      name: item.name,
      provider: item.provider,
      base_url: item.base_url,
      model: item.model,
      is_default: item.is_default,
    })
  }

  const updateProviderConfig = async () => {
    if (!editConfig) return
    const values = await editProviderForm.validateFields()
    setProviderSaving(true)
    try {
      await smartImportService.updateAIProviderConfig(editConfig.id, values)
      setEditConfig(null)
      await loadProviderSettings()
      message.success('模型配置已更新；建议重新测试连接')
    } catch (error) {
      message.error(errorMessage(error, '更新模型配置失败'))
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
            {job?.progress_detail?.fields && job.progress_detail.fields.total > 0 && (
              <Text type="secondary">字段 {job.progress_detail.fields.completed}/{job.progress_detail.fields.total}</Text>
            )}
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
                const response = await smartImportService.queueDocumentParse(row.id)
                setQueuedJob(response.job)
                await loadBatches(batch?.id)
              }}
            >
              后台重新解析
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
          <Button
            size="small"
            icon={<EyeOutlined />}
            disabled={documentJobs[row.id]?.status !== 'completed'}
            title={documentJobs[row.id]?.status === 'completed' ? '查看当前提取草稿' : '完成 AI 提取后可查看草稿'}
            onClick={() => void viewDraft(row)}
          >
            查看草稿
          </Button>
        </Space>
      ),
    },
  ], [batch?.id, loadBatches, documentJobs])

  const fieldColumns: ColumnsType<ExtractedField> = [
    {
      title: '业务字段',
      dataIndex: 'field_key',
      width: 180,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Space size={6}>
            {row.evidence?.length ? (
              <Button
                type="link"
                className="smart-import__field-link"
                onClick={() => focusEvidence(row.evidence[0])}
              >
                {workbenchValidation?.field_states[row.id]?.label || value}
              </Button>
            ) : (
              <Text strong>{workbenchValidation?.field_states[row.id]?.label || value}</Text>
            )}
            {workbenchValidation?.field_states[row.id]?.is_unmapped && (
              <Tooltip title={['accepted', 'corrected'].includes(row.review_status) ? '已作为扩展字段保留，不影响发布' : '平台尚未找到对应的标准字段，请确认或归类'}>
                <Tag color="orange">{['accepted', 'corrected'].includes(row.review_status) ? '扩展字段' : '待归类'}</Tag>
              </Tooltip>
            )}
          </Space>
          <Tooltip title={`技术字段：${row.field_key}${row.canonical_field_key ? `；平台语义：${row.canonical_field_key}` : ''}`}>
            <Text type="secondary" className="smart-import__technical-field">查看技术字段</Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '识别值',
      dataIndex: 'normalized_value',
      render: value => <Tooltip title={displayValue(value)}><pre className="smart-import__value">{displayValue(value)}</pre></Tooltip>,
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      width: 110,
      render: value => {
        const percent = Math.round((value || 0) * 100)
        const color = percent >= 85 ? 'success' : percent >= 60 ? 'warning' : 'error'
        const level = percent >= 85 ? '高' : percent >= 60 ? '中' : '低'
        return <Tag color={color}>{level} · {percent}%</Tag>
      },
    },
    {
      title: '冲突',
      width: 150,
      render: (_, field) => {
        const conflicts = workbenchValidation?.field_states[field.id]?.conflicts || []
        const labels: Record<string, string> = {
          unconfirmed: '未确认', unmapped: '未映射', duplicate_field: '重复',
          existing_record_duplicate: '正式库已存在',
          semantic_conflict: '关联值冲突', range_violation: '超出范围', option_violation: '选项不合法',
          type_violation: '值类型不正确',
        }
        return conflicts.length
          ? <Space size={[4, 4]} wrap>{conflicts.map(item => <Tag key={item} color="error">{labels[item] || item}</Tag>)}</Space>
          : <Tag color="success">无冲突</Tag>
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
            <Tooltip key={item.id} title={item.text_excerpt} placement="topLeft">
              <Button type="link" className="smart-import__evidence" onClick={() => focusEvidence(item)}>
                第 {item.page_number} 页：{item.text_excerpt}
              </Button>
            </Tooltip>
          ))}
        </Space>
      ) : <Text type="secondary">无证据片段</Text>,
    },
    {
      title: '操作',
      width: 230,
      fixed: 'right',
      render: (_, field) => result?.entity.status === 'published' ? null : (
        <Space size={4} wrap>
          {workbenchValidation?.field_states[field.id]?.is_unmapped && (
            <Tooltip title="绑定已有字段或创建企业自定义字段">
              <Button
                type="text"
                size="small"
                icon={<LinkOutlined />}
                title="绑定字段"
                onClick={() => {
                  setBindField(field)
                  bindForm.setFieldsValue({ action: 'bind_existing' })
                }}
              />
            </Tooltip>
          )}
          {field.review_status !== 'accepted' && field.review_status !== 'rejected' && (
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
          )}
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
          {field.review_status !== 'rejected' && (
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
          )}
        </Space>
      ),
    },
  ]

  const pendingFieldCount = result?.entity.fields.filter(field => field.review_status === 'pending').length || 0
  const confirmedFieldCount = result?.entity.fields.filter(field => ['accepted', 'corrected'].includes(field.review_status)).length || 0
  const existingFieldKeys = new Set(
    (result?.entity.fields || [])
      .filter(field => field.review_status !== 'rejected')
      .map(field => `${field.field_id || ''}|${field.module_id || ''}|${field.instance_id || ''}|${field.field_key}`)
  )
  const manualFieldOptions = (workbenchValidation?.binding_options || []).filter(item =>
    !existingFieldKeys.has(`${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}`)
  )
  const selectedManualField = (workbenchValidation?.binding_options || []).find(item =>
    `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}` === manualFieldTarget
  )
  const activePage = result?.pages.find(page => page.page_number === activePageNumber)
  const reviewGroups = (result?.entity.fields || []).reduce<Record<string, ExtractedField[]>>((groups, field) => {
    const key = field.module_id || 'core'
    groups[key] = [...(groups[key] || []), field]
    return groups
  }, {})
  const evidenceBoxStyle = (() => {
    const bbox = activeEvidence?.bbox
    if (!bbox || bbox.length !== 4 || !activePage) return undefined
    const metadata = activePage.page_metadata || {}
    const width = Number(metadata.width_pixels || metadata.width_points || 1)
    const height = Number(metadata.height_pixels || metadata.height_points || 1)
    const normalized = bbox.every(value => value >= 0 && value <= 1)
    const [x, y, boxWidth, boxHeight] = bbox
    return {
      left: `${normalized ? x * 100 : x * 100 / width}%`,
      top: `${normalized ? y * 100 : y * 100 / height}%`,
      width: `${normalized ? boxWidth * 100 : boxWidth * 100 / width}%`,
      height: `${normalized ? boxHeight * 100 : boxHeight * 100 / height}%`,
    }
  })()

  return (
    <div className="smart-import">
      <div className="smart-import__header">
        <div>
          <Title level={2}>{workspaceLabel}能力建库 · 智能导入</Title>
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
        description="可使用平台额度、临时 API Key 或当前工作区已保存的配置；也可以继续使用原有手工新建功能。"
      />

      {quota && (
        <Card size="small" className="smart-import__quota">
          <Space wrap>
            <WalletOutlined />
            <Text strong>本月平台 AI 点数</Text>
            <Text>{quota.remaining_points} / {quota.monthly_points} 点可用</Text>
            {typeof quota.estimated_points === 'number' && (
              <Tag color={quota.can_run_estimate ? 'success' : 'error'}>
                当前文件预计 {quota.estimated_points} 点
              </Tag>
            )}
            <Text type="secondary">BYOK 不扣平台点数</Text>
          </Space>
          {aiUsage && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <Space wrap size={[16, 8]}>
                <Text type="secondary">近 30 天</Text>
                <Text>任务 {aiUsage.totals.tasks}</Text>
                <Text>输入 Token {aiUsage.totals.input_tokens.toLocaleString()}</Text>
                <Text>输出 Token {aiUsage.totals.output_tokens.toLocaleString()}</Text>
                <Text>总 Token {aiUsage.totals.total_tokens.toLocaleString()}</Text>
                <Text>已扣 {aiUsage.totals.points} 点</Text>
                {aiUsage.by_model.slice(0, 3).map(item => (
                  <Tag key={`${item.provider}:${item.model}`}>{item.model} · {item.total_tokens.toLocaleString()} Token</Tag>
                ))}
              </Space>
            </>
          )}
        </Card>
      )}

      {queuedJob && (
        <Card size="small" className="smart-import__quota">
          <Space wrap>
            <RobotOutlined />
            <Text strong>{queuedJob.progress_detail?.job_kind === 'parse' ? '后台解析任务' : '后台提取任务'}</Text>
            <Tag color={queuedJob.status === 'completed' ? 'success' : queuedJob.status === 'failed' ? 'error' : queuedJob.status === 'cancelled' ? 'default' : 'processing'}>
              {statusLabels[queuedJob.status] || queuedJob.status}
            </Tag>
            <Progress percent={queuedJob.progress || 0} size="small" style={{ width: 180 }} />
            {queuedJob.progress_detail?.pages && queuedJob.progress_detail.pages.total > 0 && (
              <Text type="secondary">页面 {queuedJob.progress_detail.pages.completed}/{queuedJob.progress_detail.pages.total}</Text>
            )}
            {queuedJob.progress_detail?.fields && queuedJob.progress_detail.fields.total > 0 && (
              <Text type="secondary">字段 {queuedJob.progress_detail.fields.completed}/{queuedJob.progress_detail.fields.total}</Text>
            )}
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
                <Card
                  extra={<Button danger icon={<DeleteOutlined />} onClick={() => setDeleteOpen(true)}>删除任务</Button>}
                >
                  <Descriptions title={batch.name} size="small" column={{ xs: 1, sm: 3 }}>
                    <Descriptions.Item label="目标类型">{entityLabels[batch.target_entity_type]}</Descriptions.Item>
                    <Descriptions.Item label="状态"><Tag color={statusColors[batch.status]}>{statusLabels[batch.status] || batch.status}</Tag></Descriptions.Item>
                    <Descriptions.Item label="处理进度">{batch.progress}%</Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card title="上传已有工艺文件">
                  <Dragger
                    accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.doc,.docx,.xlsx"
                    multiple
                    maxCount={50}
                    showUploadList={false}
                    customRequest={uploadFile}
                    disabled={uploading}
                  >
                    <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                    <p className="ant-upload-text">点击或拖入一个或多个文件</p>
                    <p className="ant-upload-hint">支持 PDF、扫描图片、TIFF、DOC、DOCX 和 XLSX 名册；文件会依次上传，单个失败不影响其他文件。</p>
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
                            {item.status === 'queued' ? '等待上传' : item.status === 'uploading' ? '上传中' : item.status === 'completed' ? '已提交解析' : '失败'}
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
        <Form
          form={extractForm}
          layout="vertical"
          onValuesChange={(_, values) => {
            if (!batchExtractionMode || !['platform', 'saved'].includes(values.mode)) return
            localStorage.setItem(batchExtractionPreferenceKey, JSON.stringify({
              mode: values.mode,
              provider_config_id: values.mode === 'saved' ? values.provider_config_id : undefined,
              run_ocr: values.run_ocr,
            }))
          }}
        >
          {templateRecommendation && (
            <Alert
              type={templateRecommendation.classification.requires_confirmation ? 'warning' : 'info'}
              showIcon
              message={`内容分类：${entityLabels[templateRecommendation.classification.document_type as ImportEntityType] || '未知'}（${Math.round(templateRecommendation.classification.confidence * 100)}%）`}
              description={templateRecommendation.recommendations[0]
                ? `已推荐“${templateRecommendation.recommendations[0].name}”：${templateRecommendation.recommendations[0].reasons.join('、')}`
                : '未找到明显匹配的企业模板，可继续使用内置核心字段或手工指定模板。'}
              className="smart-import__modal-alert"
            />
          )}
          <Form.Item name="schema_source" label="提取字段来源" rules={[{ required: true, message: '请选择提取字段来源' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="选择自动核心字段、企业模板或模块"
              options={[
                ...(['wps', 'pqr', 'welder'].includes(batch?.target_entity_type || '')
                  ? [{ value: 'builtin:auto', label: `自动 · ${entityLabels[batch!.target_entity_type]} 核心字段（推荐）` }]
                  : []),
                ...templates.map(item => {
                  const recommended = templateRecommendation?.recommendations.find(value => value.template_id === item.id)
                  return {
                    value: `template:${item.id}`,
                    label: recommended ? `推荐 ${recommended.score}% · ${item.name}` : `模板 · ${item.name}`,
                  }
                }),
                ...modules.map(item => ({ value: `module:${item.id}`, label: `模块 · ${item.name}` })),
              ]}
              notFoundContent="当前类型尚无可用字段来源"
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
              <Form.Item name="provider_preset" label="模型服务商" rules={[{ required: true, message: '请选择模型服务商' }]}>
                <Select
                  options={providerPresets.map(({ value, label }) => ({ value, label }))}
                  onChange={(value) => applyProviderPreset(extractForm, value)}
                />
              </Form.Item>
              {extractionProviderPreset === 'custom' ? (
                <Form.Item name="provider" label="接口协议" rules={[{ required: true }]}>
                  <Select options={[
                    { value: 'openai_responses', label: 'OpenAI Responses' },
                    { value: 'openai_compatible_chat', label: 'OpenAI 兼容 Chat Completions' },
                  ]} />
                </Form.Item>
              ) : <Form.Item name="provider" hidden><Input /></Form.Item>}
              <Form.Item name="model" label="模型名称" rules={[{ required: true, message: '请输入模型名称' }]}>
                <Input placeholder="例如：gpt-5.4" maxLength={120} />
              </Form.Item>
              <Form.Item name="api_key" label="临时 API Key" rules={[{ required: true, message: '请输入 API Key' }]} extra="只在本次请求中使用，不会保存到数据库。">
                <Input.Password autoComplete="new-password" maxLength={500} />
              </Form.Item>
              <Form.Item name="base_url" label="接口地址" extra={`已预填，可按服务商文档调整。允许的域名：${capabilities?.byok_allowed_hosts.join('、') || '无'}`}>
                <Input placeholder="https://api.openai.com/v1" maxLength={500} />
              </Form.Item>
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
          {batch?.target_entity_type === 'pqr' && (
            <>
              <Alert
                type={persistentOutboundAuthorization ? 'success' : 'warning'}
                showIcon
                message={persistentOutboundAuthorization
                  ? '已按“我的设置”完成数据外发授权'
                  : '向外部模型发送前需要隐私确认'}
                description={extractionProviderHost
                  ? aiDataOutboundNotice(extractionProviderHost)
                  : '请先选择可用模型配置，以显示数据接收方。'}
                className="smart-import__modal-alert"
              />
              {!persistentOutboundAuthorization && (
                <Form.Item
                  name="outbound_privacy_consent"
                  valuePropName="checked"
                  rules={[{
                    validator: (_, checked) => checked
                      ? Promise.resolve()
                      : Promise.reject(new Error('请确认隐私说明后再开始提取，或前往“我的设置”保存长期授权')),
                  }]}
                >
                  <Checkbox disabled={!extractionProviderHost}>
                    本次允许将这些 PQR 文件发送至 {extractionProviderHost || '所选外部服务'}
                  </Checkbox>
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
                <Button key="edit" size="small" icon={<EditOutlined />} onClick={() => openEditProviderConfig(item)}>编辑</Button>,
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
          <Form form={providerForm} layout="vertical" initialValues={{ scope_type: isEnterpriseWorkspace ? 'enterprise' : 'personal', provider_preset: 'openai', provider: 'openai_responses', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' }}>
            <Row gutter={12}>
              <Col span={12}><Form.Item name="scope_type" label="使用范围" rules={[{ required: true }]}><Select options={isEnterpriseWorkspace ? [{ value: 'personal', label: '仅自己' }, { value: 'enterprise', label: '当前企业工作区（需管理员）' }] : [{ value: 'personal', label: '当前个人工作区' }]} /></Form.Item></Col>
              <Col span={12}><Form.Item name="name" label="配置名称" rules={[{ required: true }]}><Input maxLength={100} /></Form.Item></Col>
            </Row>
            <Form.Item name="provider_preset" label="模型服务商" rules={[{ required: true }]}>
              <Select
                options={providerPresets.map(({ value, label }) => ({ value, label }))}
                onChange={(value) => applyProviderPreset(providerForm, value)}
              />
            </Form.Item>
            <Row gutter={12}>
              <Col span={12}>{savedProviderPreset === 'custom' ? <Form.Item name="provider" label="接口协议" rules={[{ required: true }]}><Select options={[{ value: 'openai_responses', label: 'OpenAI Responses' }, { value: 'openai_compatible_chat', label: '兼容 Chat Completions' }]} /></Form.Item> : <Form.Item name="provider" hidden><Input /></Form.Item>}</Col>
              <Col span={12}><Form.Item name="model" label="模型名称" rules={[{ required: true }]}><Input maxLength={120} /></Form.Item></Col>
            </Row>
            <Form.Item name="base_url" label="接口地址" rules={[{ required: true }]}><Input maxLength={500} /></Form.Item>
            <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}><Input.Password autoComplete="new-password" maxLength={500} /></Form.Item>
            <Space>
              <Button loading={providerTesting} onClick={() => void testDraftProviderConfig()}>测试连接</Button>
              <Button type="primary" loading={providerSaving} onClick={() => void createProviderConfig()}>加密保存</Button>
            </Space>
            {savedProviderPreset === 'deepseek' && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">已按新版 DeepSeek Chat Completions 配置：基础地址不含 /v1，默认模型 deepseek-v4-flash。</Text>
              </div>
            )}
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

      <Modal
        title={`编辑模型配置 · ${editConfig?.name || ''}`}
        open={Boolean(editConfig)}
        onCancel={() => setEditConfig(null)}
        onOk={() => void updateProviderConfig()}
        confirmLoading={providerSaving}
        okText="保存修改"
      >
        <Alert type="info" showIcon message="API Key 不会回显；如需更换，请使用“轮换 Key”。" style={{ marginBottom: 16 }} />
        <Form form={editProviderForm} layout="vertical">
          <Form.Item name="name" label="配置名称" rules={[{ required: true }]}><Input maxLength={100} /></Form.Item>
          <Form.Item name="provider" label="接口协议" rules={[{ required: true }]}>
            <Select options={[{ value: 'openai_responses', label: 'OpenAI Responses' }, { value: 'openai_compatible_chat', label: '兼容 Chat Completions' }]} />
          </Form.Item>
          <Form.Item name="model" label="模型名称" rules={[{ required: true }]}><Input maxLength={120} /></Form.Item>
          <Form.Item name="base_url" label="接口地址" rules={[{ required: true }]}><Input maxLength={500} /></Form.Item>
          <Form.Item name="is_default" label="设为默认配置" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>

      <Modal
        title="删除导入任务"
        open={deleteOpen}
        okText="确认删除"
        okButtonProps={{ danger: true, loading: deletingBatch }}
        cancelText="取消"
        onCancel={() => {
          if (!deletingBatch) {
            setDeleteOpen(false)
            setDeleteRelatedData(false)
          }
        }}
        onOk={() => void deleteCurrentBatch()}
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Alert
            type="warning"
            showIcon
            message={`将删除导入任务“${batch?.name || ''}”及原始文件、解析页、提取草稿和审核记录`}
            description="此操作不可恢复。正在排队或处理中的后台任务会同时取消。"
          />
          <Space align="start">
            <Switch checked={deleteRelatedData} onChange={setDeleteRelatedData} />
            <div>
              <Text strong>同时删除关联业务数据</Text>
              <div><Text type="secondary">开启后会停用由本任务发布的 WPS/PQR/pPQR 或焊工资质；焊工主档不会被误删。</Text></div>
            </div>
          </Space>
        </Space>
      </Modal>

      <Modal title={`轮换 ${rotateConfig?.name || ''} 的 API Key`} open={Boolean(rotateConfig)} onCancel={() => setRotateConfig(null)} onOk={() => void rotateProviderKey()} okText="确认轮换">
        <Form form={rotateForm} layout="vertical">
          <Form.Item name="api_key" label="新 API Key" rules={[{ required: true }]} extra="保存后旧密钥立即从本系统失效。"><Input.Password autoComplete="new-password" maxLength={500} /></Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={<Space><FileSearchOutlined />提取结果与原文证据</Space>}
        open={Boolean(result)}
        onClose={() => setResult(null)}
        width="min(1600px, 98vw)"
        extra={result && (
          <Space>
            <Button icon={<HistoryOutlined />} onClick={() => setHistoryOpen(true)}>审核记录</Button>
            <Tag color={result.entity.status === 'published' ? 'success' : 'warning'}>
              {result.entity.status === 'published' ? '已发布' : `待审核 ${pendingFieldCount} 项`}
            </Tag>
            {result.entity.status !== 'published' && <Tag color="success">已确认 {confirmedFieldCount} 项</Tag>}
            {result.entity.status !== 'published' && (
              <>
                <Button onClick={() => void bulkAccept()}>接受高置信度字段</Button>
                <Button icon={<PlusOutlined />} onClick={() => setManualFieldOpen(true)}>手工录入字段</Button>
                {['wps', 'pqr'].includes(result.entity.entity_type) && (
                  <Button
                    icon={<EditOutlined />}
                    onClick={() => navigate(`/${result.entity.entity_type}/create?import_entity_id=${result.entity.id}`)}
                  >
                    使用现有表单校核
                  </Button>
                )}
                {result.entity.entity_type === 'pqr' && (
                  <Tooltip title={!workbenchValidation?.can_publish ? (workbenchValidation?.issues.find(item => item.severity === 'error')?.message || '发布前检查尚未完成') : '仅使用已接受和已修正字段创建正式 PQR 草稿'}>
                    <span>
                      <Button
                        type="primary"
                        icon={<SendOutlined />}
                        loading={publishing}
                        disabled={!workbenchValidation?.can_publish}
                        onClick={() => void publishEntity()}
                      >
                        按已审核字段发布
                      </Button>
                    </span>
                  </Tooltip>
                )}
                {result.entity.entity_type === 'welder' && (
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={publishing}
                    onClick={() => void openWelderReview()}
                  >
                    审核焊工与资质
                  </Button>
                )}
              </>
            )}
          </Space>
        )}
      >
        {result && (
          <div className="smart-import__review-workbench">
            <Card
              className="smart-import__source-pane"
              title={<Space><EyeOutlined />原文定位</Space>}
              extra={
                <Select
                  aria-label="选择原文页码"
                  value={activePageNumber}
                  onChange={value => { setActivePageNumber(value); setActiveEvidence(null) }}
                  options={result.pages.map(page => ({ value: page.page_number, label: `第 ${page.page_number} 页` }))}
                  style={{ width: 120 }}
                />
              }
            >
              <Spin spinning={previewLoading}>
                {pagePreviewUrl ? (
                  <div className="smart-import__page-preview">
                    <img src={pagePreviewUrl} alt={`原始文件第 ${activePageNumber} 页`} />
                    {evidenceBoxStyle && <div className="smart-import__evidence-box" style={evidenceBoxStyle} />}
                  </div>
                ) : (
                  <pre className="smart-import__source-text">{activePage?.text_content || '本页没有可用文本或视觉预览'}</pre>
                )}
              </Spin>
              {activeEvidence && (
                <Alert
                  type="warning"
                  showIcon
                  message={`当前证据 · 第 ${activeEvidence.page_number} 页${activeEvidence.bbox ? ' · 已定位区域' : ''}`}
                  description={activeEvidence.text_excerpt}
                  className="smart-import__active-evidence"
                />
              )}
            </Card>

            <div className="smart-import__form-pane">
              <Card size="small" className="smart-import__validation-card">
                <Descriptions size="small" column={{ xs: 2, md: 5 }}>
                  <Descriptions.Item label="缺少必填">{workbenchValidation?.counts.required_missing || 0}</Descriptions.Item>
                  <Descriptions.Item label="重复项">{workbenchValidation?.counts.duplicates || 0}</Descriptions.Item>
                  <Descriptions.Item label="规则冲突">{workbenchValidation?.counts.rule_conflicts || 0}</Descriptions.Item>
                  <Descriptions.Item label="未确认">{workbenchValidation?.counts.unconfirmed || 0}</Descriptions.Item>
                  <Descriptions.Item label="未映射">{workbenchValidation?.counts.unmapped || 0}</Descriptions.Item>
                </Descriptions>
                {(workbenchValidation?.issues.length || 0) > 0 && (
                  <>
                    <Divider />
                    <List
                      size="small"
                      dataSource={workbenchValidation?.issues || []}
                      renderItem={item => (
                        <List.Item>
                          <Space><WarningOutlined className="smart-import__issue-icon" /><Text>{item.message}</Text></Space>
                        </List.Item>
                      )}
                    />
                  </>
                )}
              </Card>

              <Descriptions bordered size="small" column={{ xs: 1, sm: 3 }}>
                <Descriptions.Item label="字段数">{result.entity.fields.length}</Descriptions.Item>
                <Descriptions.Item label="总 Token">{result.job.total_tokens}</Descriptions.Item>
                <Descriptions.Item label="草稿版本">V{result.entity.version}</Descriptions.Item>
              </Descriptions>

              {Object.entries(reviewGroups).map(([moduleId, fields]) => (
                <Card
                  key={moduleId}
                  size="small"
                  className="smart-import__module-card"
                  title={<Space><Text strong>{moduleId === 'unmapped' ? '未映射字段' : moduleId}</Text><Tag>{fields.length} 项</Tag></Space>}
                >
                  <Table
                    rowKey="id"
                    columns={fieldColumns}
                    dataSource={fields}
                    pagination={false}
                    scroll={{ x: 1100 }}
                    locale={{ emptyText: <Empty description="暂无字段" /> }}
                  />
                </Card>
              ))}
            </div>
          </div>
        )}
      </Drawer>

      <Modal
        title="焊工、证书与持证项目审核"
        open={Boolean(welderReview)}
        onCancel={() => !publishing && setWelderReview(null)}
        onOk={() => void publishWelderReview()}
        confirmLoading={publishing}
        okText="确认导入现有焊工库"
        width="min(1200px, 96vw)"
      >
        <Alert
          type="info"
          showIcon
          message="编号或身份证件优先匹配；只有姓名相同的记录必须人工确认"
          description="重复证书默认跳过；有效期更晚的同号证书按续证更新。每个持证项目会单独保存到期状态。"
          style={{ marginBottom: 16 }}
        />
        <Table
          rowKey="record_key"
          dataSource={welderReview?.records || []}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1050 }}
          columns={[
            { title: '姓名 / 编号', width: 180, render: (_, item) => <><Text strong>{item.full_name || '未识别姓名'}</Text><br /><Text type="secondary">{item.welder_code || item.id_number || '无身份编号'}</Text></> },
            { title: '身份处理', width: 250, render: (_, item) => (
              <Select
                value={welderChoices[item.record_key]}
                placeholder="请选择对应焊工"
                style={{ width: '100%' }}
                onChange={value => setWelderChoices(current => ({ ...current, [item.record_key]: value }))}
                options={[
                  ...item.candidates.map(candidate => ({ value: candidate.id, label: `${candidate.full_name} · ${candidate.welder_code}` })),
                  { value: 'new', label: '确认新建焊工' },
                ]}
              />
            ) },
            { title: '证书号', dataIndex: 'certification_number', width: 170, render: value => value || '未识别' },
            { title: '证书判断', width: 120, render: (_, item) => {
              const config = { new: ['blue', '新证书'], duplicate: ['default', '重复·跳过'], renewal: ['green', '续证更新'], conflict: ['red', '归属冲突'] }[item.certificate_status]
              return <Tag color={config[0]}>{config[1]}</Tag>
            } },
            { title: '有效期', width: 110, render: (_, item) => {
              const config = { valid: ['success', '有效'], expiring_soon: ['warning', '即将到期'], expired: ['error', '已过期'] }[item.expiry_status]
              return <Tag color={config[0]}>{config[1]}</Tag>
            } },
            { title: '持证项目', width: 100, render: (_, item) => `${item.qualified_projects.length} 项` },
          ]}
        />
      </Modal>

      <Modal
        title="手工录入模块字段"
        open={manualFieldOpen}
        onCancel={() => { setManualFieldOpen(false); manualFieldForm.resetFields() }}
        onOk={() => void addManualField()}
        confirmLoading={manualFieldSaving}
        okText="保存并确认"
      >
        <Alert
          type="info"
          showIcon
          message="用于补录未识别或禁止自动提取的模块字段"
          description="本操作不会调用模型或扣减额度；保存后字段直接标记为人工确认，并进入审核历史。"
          className="smart-import__modal-alert"
        />
        <Form form={manualFieldForm} layout="vertical">
          <Form.Item name="target" label="模块字段" rules={[{ required: true, message: '请选择字段' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={manualFieldOptions.map(item => ({
                value: `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}`,
                label: `${item.label} · ${item.extractable ? '支持自动提取' : item.ai_extract_mode === 'disabled' ? '已禁用自动提取' : '仅手工录入'}`,
              }))}
              placeholder={manualFieldOptions.length ? '选择需要补录的字段' : '没有可补录字段'}
            />
          </Form.Item>
          {selectedManualField && (
            <Tag color={selectedManualField.extractable ? 'blue' : 'orange'}>
              {selectedManualField.extractable ? 'AI 未识别，可人工补录' : '该字段不支持自动提取'}
            </Tag>
          )}
          <Form.Item
            name="value"
            label="字段值"
            rules={[{ required: true, message: '请输入字段值' }]}
            extra={selectedManualField?.field_type === 'table' ? '表格字段请输入合法 JSON 数组。' : undefined}
          >
            {selectedManualField?.field_type === 'checkbox' ? (
              <Select options={[{ value: 'true', label: '是' }, { value: 'false', label: '否' }]} />
            ) : (
              <Input.TextArea rows={4} maxLength={10000} />
            )}
          </Form.Item>
          <Form.Item name="reason" label="录入说明（可选）">
            <Input.TextArea rows={2} maxLength={1000} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="绑定未映射字段"
        open={Boolean(bindField)}
        onCancel={() => { setBindField(null); bindForm.resetFields() }}
        onOk={() => void applyUnmappedBinding()}
        confirmLoading={binding}
        okText="确认绑定"
      >
        <Alert
          type="info"
          showIcon
          message={`识别内容：${bindField ? displayValue(bindField.normalized_value) : ''}`}
          description="绑定只更新当前草稿的字段关系并运行局部校验，不会重新调用模型或重复扣费。"
          className="smart-import__modal-alert"
        />
        <Form form={bindForm} layout="vertical" initialValues={{ action: 'bind_existing', field_type: 'text' }}>
          <Form.Item name="action" label="处理方式" rules={[{ required: true }]}>
            <Radio.Group options={[
              { value: 'bind_existing', label: '绑定已有字段' },
              { value: 'create_custom', label: '创建企业自定义字段' },
            ]} />
          </Form.Item>
          {bindAction === 'bind_existing' ? (
            <Form.Item name="target" label="目标字段" rules={[{ required: true, message: '请选择目标字段' }]}>
              <Select
                showSearch
                optionFilterProp="label"
                options={(workbenchValidation?.binding_options || []).map(item => ({
                  value: `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}`,
                  label: `${item.label} · ${item.module_id || '核心字段'}`,
                }))}
              />
            </Form.Item>
          ) : (
            <>
              <Form.Item name="field_label" label="字段名称" initialValue={bindField ? (workbenchValidation?.field_states[bindField.id]?.label || '其他识别字段') : undefined} rules={[{ required: true }]}>
                <Input maxLength={200} />
              </Form.Item>
              <Form.Item name="field_key" label="字段键名" extra="可留空，由系统根据字段名称生成">
                <Input maxLength={150} placeholder="例如：impact_test_temperature" />
              </Form.Item>
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item name="field_type" label="字段类型" rules={[{ required: true }]}>
                    <Select options={[
                      { value: 'text', label: '单行文本' }, { value: 'textarea', label: '多行文本' },
                      { value: 'number', label: '数值' }, { value: 'date', label: '日期' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="module_name" label="新模块名称" initialValue="导入发现字段">
                    <Input maxLength={200} />
                  </Form.Item>
                </Col>
              </Row>
            </>
          )}
        </Form>
      </Modal>

      <Modal
        title="字段审核与修改记录"
        open={historyOpen}
        onCancel={() => setHistoryOpen(false)}
        footer={<Button onClick={() => setHistoryOpen(false)}>关闭</Button>}
        width="min(900px, 94vw)"
      >
        <Table
          rowKey="id"
          dataSource={reviewHistory}
          pagination={{ pageSize: 10 }}
          columns={[
            { title: '时间', dataIndex: 'created_at', width: 180, render: value => new Date(value).toLocaleString() },
            { title: '操作', dataIndex: 'action', width: 100, render: value => ({ accept: '接受', correct: '修正', reject: '拒绝', submit: '提交', approve: '发布' }[value as string] || value) },
            { title: '原值', dataIndex: 'previous_value', render: value => <Text ellipsis={{ tooltip: displayValue(value) }}>{displayValue(value)}</Text> },
            { title: '新值', dataIndex: 'new_value', render: value => <Text ellipsis={{ tooltip: displayValue(value) }}>{displayValue(value)}</Text> },
            { title: '原因', dataIndex: 'reason', render: value => value || '—' },
          ]}
          locale={{ emptyText: '尚无人工审核记录' }}
        />
      </Modal>

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
