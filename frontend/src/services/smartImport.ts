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
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled'
  mode: 'platform' | 'byok'
  provider?: string
  model?: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  error_code?: string
  error_message?: string
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
      template_id?: string
      module_id?: string
      run_ocr?: boolean
    }
  ): Promise<{
    job: AIExtractionJob
    entity: { id: string; status: string; version: number }
    pages: DocumentPage[]
  }> {
    const response = await api.post(
      `/smart-import/documents/${documentId}/extract`,
      data
    )
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
