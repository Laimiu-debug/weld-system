import api from './api'

// pPQR相关的TypeScript类型定义
export interface PPQRBase {
  title: string
  ppqr_number: string
  revision?: string
  status?: string
  template_id?: string
  
  // 基本信息
  test_date?: string
  test_purpose?: string
  reference_standard?: string
  welding_process?: string
  welder_name?: string
  project_name?: string
  
  // 试验方案
  test_variables?: string
  number_of_specimens?: number
  test_matrix?: string
  expected_outcome?: string
  risk_assessment?: string
  
  // 材料信息
  base_material_spec?: string
  base_material_grade?: string
  thickness?: number
  filler_metal_spec?: string
  filler_metal_classification?: string
  diameter?: number
  shielding_gas?: string
  batch_number?: string
  
  // 参数对比分析
  best_group?: string
  best_group_reason?: string
  heat_input_analysis?: string
  quality_comparison?: string
  efficiency_analysis?: string
  recommended_parameters?: string
  
  // 试验评价
  test_conclusion?: string
  objectives_achieved?: string
  lessons_learned?: string
  next_steps?: string
  convert_to_pqr?: string
  target_pqr_number?: string
  evaluated_by?: string
  evaluation_date?: string
  
  // 备注
  notes?: string
  remarks?: string
  
  // JSONB字段 - 模块化数据
  module_data?: Record<string, any>
  
  // 参数组数据（可能有多组）
  parameter_groups?: ParameterGroup[]
  
  // 关联
  related_pqr_id?: number
}

// 参数对比组
export interface ParameterGroup {
  group_number: string
  group_description?: string
  current?: number
  voltage?: number
  travel_speed?: number
  heat_input?: number
  preheat_temp?: number
  interpass_temp?: number
  wire_feed_speed?: number
  gas_flow_rate?: number
  visual_rating?: string
  mechanical_test_result?: string
  remarks?: string
}

export interface PPQRCreate extends PPQRBase {}

export interface PPQRUpdate extends Partial<PPQRBase> {
  reviewed_by?: number
  approved_by?: number
}

export interface PPQRResponse extends PPQRBase {
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

export interface PPQRSummary {
  id: number
  title: string
  ppqr_number: string
  revision: string
  status: string
  test_date?: string
  test_conclusion?: string
  convert_to_pqr?: string
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

export interface PPQRListQuery {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  reference_standard?: string
  welding_process?: string
  test_conclusion?: string
  convert_to_pqr?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PPQRListResponse {
  items: PPQRSummary[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 参数对比数据
export interface ParameterComparisonData {
  groups: ParameterGroup[]
  comparison_chart_data: any
  best_group_analysis: any
}

// pPQR服务类
class PPQRService {
  // 获取pPQR列表
  async list(query: PPQRListQuery = {}): Promise<PPQRListResponse> {
    const params: Record<string, any> = {}

    if (query.page) params.page = query.page
    if (query.page_size) params.page_size = query.page_size
    if (query.keyword) params.keyword = query.keyword
    if (query.status) params.status = query.status
    if (query.reference_standard) params.reference_standard = query.reference_standard
    if (query.welding_process) params.welding_process = query.welding_process
    if (query.test_conclusion) params.test_conclusion = query.test_conclusion
    if (query.convert_to_pqr) params.convert_to_pqr = query.convert_to_pqr
    if (query.sort_by) params.sort_by = query.sort_by
    if (query.sort_order) params.sort_order = query.sort_order

    const response = await api.get('/ppqr/', { params })
    // API拦截器会将响应包装成 {success: true, data: ...}
    // 所以我们需要访问 response.data
    return response.data as PPQRListResponse
  }

  // 获取单个pPQR
  async get(id: number): Promise<PPQRResponse> {
    const response = await api.get(`/ppqr/${id}`)
    return response.data as PPQRResponse
  }

  // 创建pPQR
  async create(data: PPQRCreate): Promise<PPQRResponse> {
    console.log('[PPQRService] 发送创建请求:', data)
    const response = await api.post('/ppqr/', data)
    console.log('[PPQRService] 收到响应:', response)
    // API拦截器会将响应包装成 {success: true, data: ...}
    // 所以我们需要访问 response.data
    return response.data as PPQRResponse
  }

  // 更新pPQR
  async update(id: number, data: PPQRUpdate): Promise<PPQRResponse> {
    const response = await api.put(`/ppqr/${id}`, data)
    return response.data as PPQRResponse
  }

  // 删除pPQR
  async delete(id: number): Promise<void> {
    await api.delete(`/ppqr/${id}`)
  }

  // 批量删除pPQR
  async batchDelete(ids: number[]): Promise<void> {
    await api.post('/ppqr/batch-delete', { ids })
  }

  // 更新pPQR状态
  async updateStatus(id: number, status: string): Promise<PPQRResponse> {
    const response = await api.patch(`/ppqr/${id}/status`, { status })
    return response.data as PPQRResponse
  }

  // 复制pPQR
  async duplicate(id: number): Promise<PPQRResponse> {
    const response = await api.post(`/ppqr/${id}/duplicate`)
    return response.data as PPQRResponse
  }

  // 转换pPQR为PQR
  async convertToPQR(id: number, pqrData?: Partial<any>): Promise<any> {
    const response = await api.post(`/ppqr/${id}/convert-to-pqr`, pqrData || {})
    return response.data
  }

  // 获取参数对比数据
  async getParameterComparison(id: number): Promise<ParameterComparisonData> {
    const response = await api.get(`/ppqr/${id}/parameter-comparison`)
    return response.data as ParameterComparisonData
  }

  // 导出pPQR为PDF
  async exportPDF(id: number): Promise<Blob> {
    const response = await api.get(`/ppqr/${id}/export/pdf`, {
      responseType: 'blob'
    })
    return response.data as Blob
  }

  // 导出pPQR为Excel
  async exportExcel(id: number): Promise<Blob> {
    const response = await api.get(`/ppqr/${id}/export/excel`, {
      responseType: 'blob'
    })
    return response.data as Blob
  }

  // 导出参数对比报告
  async exportComparisonReport(id: number): Promise<Blob> {
    const response = await api.get(`/ppqr/${id}/export/comparison-report`, {
      responseType: 'blob'
    })
    return response.data as Blob
  }

  // 获取pPQR统计信息
  async getStatistics(): Promise<any> {
    const response = await api.get('/ppqr/statistics')
    return response.data
  }
}

// 导出单例
const ppqrService = new PPQRService()
export default ppqrService

