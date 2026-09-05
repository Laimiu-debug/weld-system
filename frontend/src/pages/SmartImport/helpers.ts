import type { FormInstance } from 'antd'
import type { ImportEntityType } from '@/services/smartImport'

export const entityLabels: Record<ImportEntityType, string> = {
  wps: 'WPS',
  pqr: 'PQR',
  ppqr: 'pPQR',
  welder: '焊工资质',
}

export const statusLabels: Record<string, string> = {
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

export const sha256Hex = async (value: string) => {
  const bytes = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('')
}

export const statusColors: Record<string, string> = {
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

export function errorMessage(error: unknown, fallback: string): string {
  const detail = (error as any)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (typeof detail?.message === 'string') return detail.message
  return error instanceof Error ? error.message : fallback
}

export function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

export function parseEditedValue(original: unknown, value: string): unknown {
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

export const providerPresets = [
  { value: 'openai', label: 'OpenAI', provider: 'openai_responses', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { value: 'deepseek', label: 'DeepSeek', provider: 'openai_compatible_chat', baseUrl: 'https://api.deepseek.com', model: 'deepseek-v4-flash' },
  { value: 'qwen', label: '阿里云百炼 / 通义千问', provider: 'openai_compatible_chat', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { value: 'kimi', label: 'Moonshot / Kimi', provider: 'openai_compatible_chat', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { value: 'zhipu', label: '智谱 GLM', provider: 'openai_compatible_chat', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { value: 'siliconflow', label: '硅基流动', provider: 'openai_compatible_chat', baseUrl: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-72B-Instruct' },
  { value: 'custom', label: '自定义兼容接口', provider: 'openai_compatible_chat', baseUrl: '', model: '' },
] as const

type ProviderPreset = typeof providerPresets[number]

export function applyProviderPreset(form: FormInstance, value: string) {
  const preset = providerPresets.find(item => item.value === value) as ProviderPreset | undefined
  if (!preset) return
  form.setFieldsValue({
    provider: preset.provider,
    base_url: preset.baseUrl,
    model: preset.model,
  })
}

export function parseManualValue(fieldType: string, value: string): unknown {
  if (['number', 'integer'].includes(fieldType)) {
    const parsed = Number(value)
    if (value.trim() && Number.isFinite(parsed) && (fieldType !== 'integer' || Number.isInteger(parsed))) return parsed
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
