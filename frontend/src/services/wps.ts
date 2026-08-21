import api from './api'

// WPS相关的TypeScript类型定义
export interface WPSBase {
  title: string
  wps_number: string
  revision?: string
  status?: string
  template_id?: string
  standard?: string
  product_name?: string
  manufacturer?: string
  customer?: string
  location?: string
  order_number?: string
  part_number?: string
  drawing_number?: string
  wpqr_number?: string
  welder_qualification?: string
  pdf_link?: string
  company?: string
  project_name?: string
  welding_process?: string
  process_type?: string
  process_specification?: string
  base_material_group?: string
  base_material_spec?: string
  base_material_thickness_range?: string
  filler_material_spec?: string
  filler_material_classification?: string
  filler_material_diameter?: number
  shielding_gas?: string
  gas_flow_rate?: number
  gas_composition?: string
  current_type?: string
  current_polarity?: string
  current_range?: string
  voltage_range?: string
  wire_feed_speed?: string
  welding_speed?: string
  travel_speed?: string
  heat_input_min?: number
  heat_input_max?: number
  weld_passes?: number
  weld_layer?: number
  joint_design?: string
  groove_type?: string
  groove_angle?: string
  root_gap?: string
  root_face?: string
  preheat_temp_min?: number
  preheat_temp_max?: number
  interpass_temp_max?: number
  pwht_required?: boolean
  pwht_temperature?: number
  pwht_time?: number
  ndt_required?: boolean
  ndt_methods?: string
  mechanical_testing?: string
  critical_application?: boolean
  special_requirements?: string
  notes?: string
  supporting_documents?: string
  attachments?: string
  
  // JSONB字段
  header_info?: Record<string, any>
  summary_info?: Record<string, any>
  diagram_info?: Record<string, any>
  weld_layers?: any[]
  additional_info?: Record<string, any>
}

export interface WPSCreate extends WPSBase {}

export interface WPSUpdate extends Partial<WPSBase> {
  reviewed_by?: number
  approved_by?: number
}

export interface WPSResponse extends WPSBase {
  id: number
  owner_id: number
  created_at: string
  updated_at: string
  created_by?: number
  updated_by?: number
  reviewed_by?: number
  reviewed_date?: string
  approved_by?: number
  approved_date?: string
}

export interface WPSSummary {
  id: number
  title: string
  wps_number: string
  revision: string
  status: string
  company?: string
  project_name?: string
  welding_process?: string
  base_material_spec?: string
  filler_material_classification?: string
  template_id?: string
  modules_data?: Record<string, any>
  created_at: string
  updated_at: string
  // 审批相关字段
  approval_instance_id?: number
  approval_status?: string
  workflow_name?: string
  submitter_id?: number
  can_submit_approval?: boolean
  can_approve?: boolean
}

export interface WPSSearchParams {
  wps_number?: string
  title?: string
  status?: string
  welding_process?: string
  base_material_spec?: string
  company?: string
  project_name?: string
  date_from?: string
  date_to?: string
}

export interface WPSStatusUpdate {
  status: string
  reviewed_by?: number
  approved_by?: number
}

export interface WPSRevisionCreate {
  wps_id: number
  revision: string
  changes_description: string
  changed_by: number
}

export interface WPSRevisionResponse {
  id: number
  wps_id: number
  revision: string
  changes_description: string
  changed_by: number
  changed_at: string
}

export interface WPSStatistics {
  total: number
  by_status: Record<string, number>
  by_process: Record<string, number>
  by_material: Record<string, number>
  recent_count: number
}

class WPSService {
  /**
   * 获取WPS列表
   */
  async getWPSList(params?: {
    skip?: number
    limit?: number
    owner_id?: number
    status?: string
    search_term?: string
  }): Promise<WPSSummary[]> {
    const query: Record<string, unknown> = {
      skip: params?.skip,
      limit: params?.limit,
      owner_id: params?.owner_id,
      search_term: params?.search_term,
    }
    // 后端参数名是 status_filter，不是 status
    if (params?.status) {
      query.status_filter = params.status
    }
    const response = await api.get('/wps/', { params: query })
    const body = response?.data
    if (Array.isArray(body)) return body
    if (Array.isArray(body?.items)) return body.items
    if (Array.isArray(body?.data)) return body.data
    return []
  }

  /**
   * 获取WPS详情
   */
  async getWPS(id: number): Promise<any> {
    const response = await api.get(`/wps/${id}`)
    return response
  }

  /**
   * 创建WPS
   */
  async createWPS(data: WPSCreate): Promise<any> {
    const response = await api.post('/wps/', data)
    return response
  }

  /**
   * 更新WPS
   */
  async updateWPS(id: number, data: WPSUpdate): Promise<any> {
    const response = await api.put(`/wps/${id}`, data)
    return response
  }

  /**
   * 删除WPS
   */
  async deleteWPS(id: number): Promise<any> {
    const response = await api.delete(`/wps/${id}`)
    return response
  }

  /**
   * 更新WPS状态
   */
  async updateWPSStatus(id: number, statusUpdate: WPSStatusUpdate): Promise<WPSResponse> {
    const response = await api.put(`/wps/${id}/status/`, statusUpdate)
    return response.data
  }

  /**
   * 获取WPS版本历史
   */
  async getWPSRevisions(id: number): Promise<WPSRevisionResponse[]> {
    const response = await api.get(`/wps/${id}/revisions/`)
    return response.data
  }

  /**
   * 创建WPS版本
   */
  async createWPSRevision(data: WPSRevisionCreate): Promise<WPSRevisionResponse> {
    const response = await api.post(`/wps/${data.wps_id}/revisions/`, data)
    return response.data
  }

  /**
   * 高级搜索WPS
   */
  async searchWPS(searchParams: WPSSearchParams): Promise<WPSSummary[]> {
    const response = await api.post('/wps/search', searchParams)
    return response.data
  }

  /**
   * 获取WPS统计信息
   */
  async getWPSStatistics(): Promise<WPSStatistics> {
    const response = await api.get('/wps/statistics/overview')
    return response.data
  }

  /**
   * 批量删除WPS
   */
  async batchDeleteWPS(ids: number[]): Promise<void> {
    await api.post('/wps/batch-delete', { ids })
  }

  /**
   * 导出WPS
   */
  async exportWPS(id: number, format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await api.get(`/wps/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  }

  /**
   * 批量导出WPS
   */
  async batchExportWPS(ids: number[], format: 'pdf' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await api.post('/wps/batch-export', 
      { ids, format },
      { responseType: 'blob' }
    )
    return response.data
  }
}

// 导出单例
export const wpsService = new WPSService()
export default wpsService

