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

export interface ConsumableUsageResponse {
  items: ConsumableUsageItem[]
  total: number
  skip: number
  limit: number
}

export const consumablesService = {
  async listUsage(params: {
    event_type?: ConsumableUsageType
    skip?: number
    limit?: number
  } = {}): Promise<ConsumableUsageResponse> {
    const response = await apiService.get<ConsumableUsageResponse>(
      '/consumables/usage',
      { params },
    )
    return response.data
  },
}
