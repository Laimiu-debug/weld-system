import api from './api'

export type ImportEntityType = 'wps' | 'pqr' | 'ppqr' | 'welder'

export interface ImportBatch {
  id: string
  name: string
  source_type: 'upload' | 'manual' | 'migration'
  target_entity_type: ImportEntityType
  status: 'draft' | 'queued' | 'processing' | 'review' | 'completed' | 'failed' | 'cancelled'
  progress: number
  total_documents: number
  processed_documents: number
  workspace_type: 'personal' | 'enterprise'
  company_id?: number
  factory_id?: number
  access_level: 'private' | 'factory' | 'company'
  created_at: string
  updated_at: string
}

export interface SourceDocument {
  id: string
  batch_id: string
  original_filename: string
  sha256: string
  mime_type?: string
  size_bytes: number
  document_type: ImportEntityType | 'unknown'
  document_version?: string
  page_count?: number
  status: string
  metadata_json: Record<string, unknown>
  created_at: string
}

export interface DocumentPage {
  id: string
  document_id: string
  page_number: number
  text_content?: string
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed' | 'not_required'
  page_metadata: Record<string, unknown>
  created_at: string
}

export interface AIExtractionJob {
  id: string
  document_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled'
  mode: 'platform' | 'byok'
  provider?: string
  model?: string
  provider_config_id?: string
  retry_of_job_id?: string
  progress: number
  input_tokens: number
  output_tokens: number
  total_tokens: number
  error_code?: string
  error_message?: string
}

export interface FieldEvidence {
  id: string
  page_number: number
  evidence_type: 'text' | 'ocr' | 'table' | 'visual' | 'manual'
  text_excerpt: string
  bbox?: [number, number, number, number]
}

export interface ExtractedField {
  id: string
  module_id?: string
  instance_id?: string
  field_id?: string
  field_key: string
  canonical_field_key?: string
  raw_value: unknown
  normalized_value: unknown
  confidence?: number
  review_status: 'pending' | 'accepted' | 'corrected' | 'rejected' | 'not_required'
  schema_version: string
  evidence: FieldEvidence[]
}

export interface ExtractedEntity {
  id: string
  document_id: string
  job_id?: string
  entity_type: ImportEntityType
  source_mode: 'ai' | 'manual' | 'mixed'
  status: 'draft' | 'review' | 'approved' | 'published' | 'rejected'
  draft_data: Record<string, unknown>
  version: number
  created_at: string
  fields: ExtractedField[]
}

export interface AIQuotaStatus {
  tier_key: string
  workspace_type: 'personal' | 'enterprise'
  monthly_points: number
  used_points: number
  reserved_or_used_points: number
  remaining_points: number
  max_points_per_task: number
  max_pages_per_task: number
  period_start: string
  platform_enabled: boolean
  estimated_points?: number
  can_run_estimate?: boolean
}

export interface AIProviderConfig {
  id: string
  scope_type: 'personal' | 'enterprise'
  name: string
  provider: 'openai_responses' | 'openai_compatible_chat'
  base_url: string
  model: string
  masked_api_key: string
  key_version: number
  is_active: boolean
  is_default: boolean
  last_test_status: 'untested' | 'success' | 'failed'
  last_tested_at?: string
  last_error?: string
}

export interface EnterpriseAIPolicy {
  company_id: number
  allow_ai: boolean
  allow_external_providers: boolean
  allow_personal_keys: boolean
  require_enterprise_key: boolean
  allowed_hosts: string[]
  updated_at?: string
}

export interface EntityPublishResult {
  entity_id: string
  target_entity_type: 'wps' | 'pqr'
  target_entity_id: string
  status: 'published'
  detail_url: string
}

export interface ImportBatchDetail extends ImportBatch {
  documents: SourceDocument[]
}

export interface ManualDraftField {
  field_key: string
  value: unknown
  module_id?: string
  instance_id?: string
  field_id?: string
  canonical_field_key?: string
  evidence?: Array<{
    page_number: number
    text: string
    bbox?: [number, number, number, number]
  }>
}

class SmartImportService {
  async listAIProviderConfigs(): Promise<AIProviderConfig[]> {
    const response = await api.get('/smart-import/ai-provider-configs')
    return response.data
  }

  async createAIProviderConfig(data: {
    scope_type: 'personal' | 'enterprise'
    name: string
    provider: 'openai_responses' | 'openai_compatible_chat'
    base_url?: string
    model: string
    api_key: string
    is_default?: boolean
  }): Promise<AIProviderConfig> {
    const response = await api.post('/smart-import/ai-provider-configs', data)
    return response.data
  }

  async testAIProviderConfig(id: string): Promise<AIProviderConfig> {
    const response = await api.post(`/smart-import/ai-provider-configs/${id}/test`)
    return response.data
  }

  async rotateAIProviderKey(id: string, apiKey: string): Promise<AIProviderConfig> {
    const response = await api.post(`/smart-import/ai-provider-configs/${id}/rotate`, { api_key: apiKey })
    return response.data
  }

  async disableAIProviderConfig(id: string): Promise<void> {
    await api.delete(`/smart-import/ai-provider-configs/${id}`)
  }

  async getEnterpriseAIPolicy(): Promise<EnterpriseAIPolicy> {
    const response = await api.get('/smart-import/enterprise-ai-policy')
    return response.data
  }

  async updateEnterpriseAIPolicy(data: Omit<EnterpriseAIPolicy, 'company_id' | 'updated_at'>): Promise<EnterpriseAIPolicy> {
    const response = await api.put('/smart-import/enterprise-ai-policy', data)
    return response.data
  }

  async getAICapabilities(): Promise<{
    platform_available: boolean
    platform_provider: string
    platform_model?: string
    byok_providers: Array<'openai_responses' | 'openai_compatible_chat'>
    byok_allowed_hosts: string[]
    max_document_pages: number
    max_input_chars: number
  }> {
    const response = await api.get('/smart-import/ai-capabilities')
    return response.data
  }

  async getAIQuota(estimatedPages?: number): Promise<AIQuotaStatus> {
    const response = await api.get('/smart-import/ai-quota', {
      params: estimatedPages ? { estimated_pages: estimatedPages } : undefined,
    })
    return response.data
  }

  async createBatch(data: {
    name: string
    target_entity_type: ImportEntityType
    source_type?: 'upload' | 'manual' | 'migration'
    access_level?: 'private' | 'factory' | 'company'
  }): Promise<ImportBatch> {
    const response = await api.post('/smart-import/batches', data)
    return response.data
  }

  async listBatches(): Promise<ImportBatch[]> {
    const response = await api.get('/smart-import/batches')
    return response.data
  }

  async getBatch(id: string): Promise<ImportBatchDetail> {
    const response = await api.get(`/smart-import/batches/${id}`)
    return response.data
  }

  async registerDocument(
    batchId: string,
    data: {
      original_filename: string
      sha256: string
      document_type: ImportEntityType | 'unknown'
      mime_type?: string
      size_bytes?: number
      document_version?: string
      storage_key?: string
      metadata?: Record<string, unknown>
    }
  ): Promise<SourceDocument> {
    const response = await api.post(`/smart-import/batches/${batchId}/documents`, data)
    return response.data
  }

  async uploadDocument(
    batchId: string,
    file: File,
    documentType?: ImportEntityType | 'unknown',
    documentVersion?: string
  ): Promise<SourceDocument> {
    const form = new FormData()
    form.append('file', file)
    if (documentType) form.append('document_type', documentType)
    if (documentVersion) form.append('document_version', documentVersion)
    const response = await api.post(`/smart-import/batches/${batchId}/upload`, form)
    return response.data
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await api.get(
      `/smart-import/documents/${documentId}/content`,
      { responseType: 'blob' }
    )
    return response.data
  }

  async parseDocument(
    documentId: string
  ): Promise<{ document: SourceDocument; pages: DocumentPage[] }> {
    const response = await api.post(`/smart-import/documents/${documentId}/parse`)
    return response.data
  }

  async listDocumentPages(documentId: string): Promise<DocumentPage[]> {
    const response = await api.get(`/smart-import/documents/${documentId}/pages`)
    return response.data
  }

  async extractDocument(
    documentId: string,
    data: {
      mode?: 'platform' | 'byok'
      provider?: 'openai_responses' | 'openai_compatible_chat'
      model?: string
      base_url?: string
      api_key?: string
      provider_config_id?: string
      template_id?: string
      module_id?: string
      run_ocr?: boolean
    }
  ): Promise<{
    job: AIExtractionJob
    entity: ExtractedEntity
    pages: DocumentPage[]
  }> {
    const response = await api.post(
      `/smart-import/documents/${documentId}/extract`,
      data
    )
    return response.data
  }

  async queueExtraction(
    documentId: string,
    data: {
      mode?: 'platform' | 'byok'
      provider_config_id?: string
      template_id?: string
      module_id?: string
      run_ocr?: boolean
    }
  ): Promise<{ job: AIExtractionJob; message: string }> {
    const response = await api.post(`/smart-import/documents/${documentId}/extract-async`, data)
    return response.data
  }

  async getExtractionJob(jobId: string): Promise<AIExtractionJob> {
    const response = await api.get(`/smart-import/extraction-jobs/${jobId}`)
    return response.data
  }

  async listDocumentExtractionJobs(documentId: string): Promise<AIExtractionJob[]> {
    const response = await api.get(`/smart-import/documents/${documentId}/extraction-jobs`)
    return response.data
  }

  async cancelExtractionJob(jobId: string): Promise<AIExtractionJob> {
    const response = await api.post(`/smart-import/extraction-jobs/${jobId}/cancel`)
    return response.data
  }

  async retryExtractionJob(jobId: string): Promise<{ job: AIExtractionJob; message: string }> {
    const response = await api.post(`/smart-import/extraction-jobs/${jobId}/retry`)
    return response.data
  }

  async getExtractedEntity(entityId: string): Promise<ExtractedEntity> {
    const response = await api.get(`/smart-import/entities/${entityId}`)
    return response.data
  }

  async getCurrentDocumentEntity(documentId: string): Promise<ExtractedEntity> {
    const response = await api.get(
      `/smart-import/documents/${documentId}/current-entity`
    )
    return response.data
  }

  async reviewField(
    entityId: string,
    fieldId: string,
    data: {
      action: 'accept' | 'correct' | 'reject'
      value?: unknown
      reason?: string
    }
  ): Promise<ExtractedEntity> {
    const response = await api.post(
      `/smart-import/entities/${entityId}/fields/${fieldId}/review`,
      data
    )
    return response.data
  }

  async bulkAcceptFields(
    entityId: string,
    data: { field_ids?: string[]; minimum_confidence?: number }
  ): Promise<ExtractedEntity> {
    const response = await api.post(
      `/smart-import/entities/${entityId}/fields/bulk-accept`,
      data
    )
    return response.data
  }

  async publishEntity(entityId: string): Promise<EntityPublishResult> {
    const response = await api.post(`/smart-import/entities/${entityId}/publish`)
    return response.data
  }

  async createManualDraft(
    documentId: string,
    data: {
      entity_type: ImportEntityType
      schema_version: string
      schema_snapshot?: Record<string, unknown>
      draft_data?: Record<string, unknown>
      fields?: ManualDraftField[]
    }
  ): Promise<{ id: string; status: string; version: number }> {
    const response = await api.post(
      `/smart-import/documents/${documentId}/manual-drafts`,
      data
    )
    return response.data
  }
}

export default new SmartImportService()
