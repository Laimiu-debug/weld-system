import api from './api'

// PQR相关的TypeScript类型定义
export interface PQRBase {
  title: string
  pqr_number: string
  revision?: string
  status?: string
  template_id?: string
  
  // 基本信息
  test_date?: string
  standard?: string
  welding_process?: string
  welder_name?: string
  welder_certificate?: string
  
  // 母材信息
  base_material_spec?: string
  base_material_grade?: string
  thickness?: number
  p_number?: string
  group_number?: string
  
  // 填充金属
  filler_metal_spec?: string
  filler_metal_classification?: string
  diameter?: number
  f_number?: string
  a_number?: string
  batch_number?: string
  
  // 保护气体
  shielding_gas_type?: string
  gas_composition?: string
  flow_rate?: number
  backing_gas?: string
  backing_gas_flow_rate?: number
  
  // 焊接参数
  current?: number
  voltage?: number
  travel_speed?: number
  heat_input?: number
  polarity?: string
  
  // 温度控制
  preheat_temp_min?: number
  preheat_temp_actual?: number
  interpass_temp_max?: number
  interpass_temp_actual?: number
  pwht_required?: string
  pwht_temperature?: number
  pwht_holding_time?: number
  
  // 合格判定
  qualification_result?: string
  qualification_date?: string
  qualified_by?: string
  qualified_by_title?: string
  approved_by?: string | number
  document_html?: string
  approved_date?: string
  failure_reason?: string
  corrective_action?: string
  applicable_wps?: string
  validity_period?: string
  
  // 备注
  notes?: string
  remarks?: string
  
  // JSONB字段 - 模块化数据
  module_data?: Record<string, any>
  
  // 关联
  related_wps_id?: number
  related_ppqr_id?: number
}

export interface PQRCreate extends PQRBase {}

export interface PQRUpdate extends Partial<PQRBase> {
  reviewed_by?: number
  approved_by?: number
}

export interface PQRResponse extends PQRBase {
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

export interface PQRSummary {
  id: number
  title: string
  pqr_number: string
  revision: string
  status: string
  test_date?: string
  qualification_result?: string
  base_material_spec?: string
  welding_process?: string
  wps_number?: string
  approval_instance_id?: number
  approval_status?: string
  workflow_name?: string
  can_submit_approval?: boolean
  can_approve?: boolean
  submitter_id?: string
  created_at: string
  updated_at: string
}

export interface PQRListQuery {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  standard?: string
  welding_process?: string
  qualification_result?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PQRListResponse {
  items: PQRSummary[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// PQR服务类
class PQRService {
  // 获取PQR列表
  async list(query: PQRListQuery = {}): Promise<PQRListResponse> {
    const params: Record<string, any> = {}

    if (query.page) params.page = query.page
    if (query.page_size) params.page_size = query.page_size
    if (query.keyword) params.keyword = query.keyword
    if (query.status) params.status = query.status
    if (query.standard) params.standard = query.standard
    if (query.welding_process) params.welding_process = query.welding_process
    if (query.qualification_result) params.qualification_result = query.qualification_result
    if (query.sort_by) params.sort_by = query.sort_by
    if (query.sort_order) params.sort_order = query.sort_order

    const response = await api.get('/pqr/', { params })
    return response.data
  }

  // 获取单个PQR
  async get(id: number): Promise<any> {
    const response = await api.get(`/pqr/${id}`)
    return response
  }

  // 创建PQR
  async create(data: PQRCreate): Promise<any> {
    const response = await api.post('/pqr/', data)
    return response
  }

  // 更新PQR
  async update(id: number, data: PQRUpdate): Promise<any> {
    const response = await api.put(`/pqr/${id}`, data)
    return response
  }

  // 删除PQR
  async delete(id: number): Promise<void> {
    await api.delete(`/pqr/${id}`)
  }

  // 批量删除PQR
  async batchDelete(ids: number[]): Promise<void> {
    await api.post('/pqr/batch-delete', { ids })
  }

  // 更新PQR状态
  async updateStatus(id: number, status: string): Promise<PQRResponse> {
    const response = await api.patch(`/pqr/${id}/status`, { status })
    return response.data
  }

  // 复制PQR
  async duplicate(id: number): Promise<PQRResponse> {
    const response = await api.post(`/pqr/${id}/duplicate`)
    return response.data
  }

  // 导出PQR为PDF
  async exportPDF(id: number): Promise<Blob> {
    const response = await api.get(`/pqr/${id}/export/pdf`, {
      responseType: 'blob'
    })
    return response.data
  }

  // 导出PQR为Excel
  async exportExcel(id: number): Promise<Blob> {
    const response = await api.get(`/pqr/${id}/export/excel`, {
      responseType: 'blob'
    })
    return response.data
  }

  // 获取PQR统计信息
  async getStatistics(): Promise<any> {
    const response = await api.get('/pqr/statistics')
    return response.data
  }
}

// 导出单例
const pqrService = new PQRService()
export default pqrService

