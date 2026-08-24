import apiService from './api'

export type ConsumableUsageType = 'issue' | 'return' | 'consume'

export interface ConsumableUsageItem {
  id: string
  event_type: ConsumableUsageType
  quantity: number
  unit: string
  batch_number?: string
  notes?: string
  source: string
  recorded_at: string
  material_id: number
  material_code?: string
  material_name?: string
  specification?: string
  issue_list_id: string
  document_number?: string
}

export interface ConsumableIssueListItem {
  id: string
  document_number: string
  status: string
  generated_at: string
  approved_at?: string
  issued_at?: string
  quota_run_id: string
  product_revision_id: string
  sequence_revision_id: string
  version_number: number
}

export interface ServerQuoteSummary {
  deposit_kg: number
  suggested_primary_kg: number
  enterprise_flux_kg: number
  gas_volume_l: number
  material_cost: number
  aux_cost: number
  labor_cost: number
  equipment_cost: number
  direct_cost: number
  price_before_tax: number
  quoted_price: number
}

export interface CalculatorQuoteResponse {
  summary: ServerQuoteSummary
  joints: unknown[]
  project_name?: string | null
  customer?: string | null
}

export const consumablesService = {
  async listUsage(params: {
    event_type?: ConsumableUsageType
    skip?: number
    limit?: number
  } = {}): Promise<{ items: ConsumableUsageItem[]; total: number }> {
    const response = await apiService.get<{ items: ConsumableUsageItem[]; total: number }>(
      '/consumables/usage',
      { params },
    )
    return response.data
  },

  async listIssueLists(params: {
    status?: string
    skip?: number
    limit?: number
  } = {}): Promise<{ items: ConsumableIssueListItem[]; total: number }> {
    const response = await apiService.get<{ items: ConsumableIssueListItem[]; total: number }>(
      '/consumables/issue-lists',
      { params },
    )
    return response.data
  },

  async quoteProject(payload: unknown): Promise<CalculatorQuoteResponse> {
    const response = await apiService.post<CalculatorQuoteResponse>(
      '/consumables/calculator/quote',
      payload,
    )
    return response.data
  },

  issueListExportUrl(
    issueListId: string,
    exportType: 'weld-detail' | 'product-summary' | 'formal-issue-list',
  ) {
    return `/api/v1/consumables/issue-lists/${issueListId}/export/${exportType}`
  },
}

export default consumablesService

export interface QuoteSummaryUi {
  deposit: number
  suggested: number
  flux: number
  gasVolumeL: number
  materialCost: number
  auxCost: number
  laborCost: number
  equipmentCost: number
  directCost: number
  priceBeforeTax: number
  quotedPrice: number
}

export const mapServerSummary = (summary: ServerQuoteSummary): QuoteSummaryUi => ({
  deposit: summary.deposit_kg,
  suggested: summary.suggested_primary_kg,
  flux: summary.enterprise_flux_kg,
  gasVolumeL: summary.gas_volume_l,
  materialCost: summary.material_cost,
  auxCost: summary.aux_cost,
  laborCost: summary.labor_cost,
  equipmentCost: summary.equipment_cost,
  directCost: summary.direct_cost,
  priceBeforeTax: summary.price_before_tax,
  quotedPrice: summary.quoted_price,
})
