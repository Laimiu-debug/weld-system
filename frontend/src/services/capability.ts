import apiService from './api'

export interface CapabilityFilters {
  factory_id?: number
  process?: string
  material_group?: string
  position?: string
  search?: string
}

export interface CapabilityOverview {
  generated_at: string
  workspace: { type: string; company_id?: number; factory_id?: number }
  filters: CapabilityFilters
  summary: Record<string, number>
  health: {
    score: number
    status: 'healthy' | 'attention' | 'risk'
    blocking_issue_count: number
    warning_count: number
    unsupported_wps_count: number
    expiring_welder_count: number
    valid_relation_count: number
  }
  dimensions: {
    processes: string[]
    material_groups: string[]
    positions: string[]
    thickness_ranges: Array<Record<string, unknown>>
    diameter_ranges: Array<Record<string, unknown>>
    pwht_conditions: boolean[]
    impact_conditions: boolean[]
  }
  wps_records: Array<Record<string, any>>
  pqr_records: Array<Record<string, any>>
  welders: Array<Record<string, any>>
  process_capabilities: Array<Record<string, any>>
  materials: Array<Record<string, any>>
  equipment: Array<Record<string, any>>
  issues: Array<Record<string, any>>
}

export interface CapabilityCheckRequest {
  factory_id?: number
  welding_process: string
  material_group: string
  thickness_mm: number
  diameter_mm?: number
  welding_position: string
  pwht_required: boolean
  impact_required: boolean
  impact_temperature_c?: number
}

export interface CapabilityCheckResult {
  decision: 'capable' | 'needs_resources' | 'not_capable'
  process_capable: boolean
  personnel_capable: boolean
  resource_ready: boolean
  requirement: CapabilityCheckRequest
  matched_capabilities: Array<Record<string, any>>
  matched_welders: Array<Record<string, any>>
  matched_materials: Array<Record<string, any>>
  matched_equipment: Array<Record<string, any>>
  gaps: Array<Record<string, any>>
  explanation: string[]
}

class CapabilityService {
  async getOverview(filters: CapabilityFilters = {}): Promise<CapabilityOverview> {
    const response = await apiService.get<CapabilityOverview>(
      '/qualification/capabilities/overview',
      { params: filters }
    )
    return response.data
  }

  async check(request: CapabilityCheckRequest): Promise<CapabilityCheckResult> {
    const response = await apiService.post<CapabilityCheckResult>(
      '/qualification/capabilities/check',
      request
    )
    return response.data
  }
}

export const capabilityService = new CapabilityService()
