/**
 * Quality Management API Service
 * 质量管理API服务
 */
import api from './api'
import { ApiResponse } from '@/types'

// ==================== 类型定义 ====================

export interface QualityInspection {
  id: number
  inspection_number: string
  inspection_type: string
  inspection_date: string

  // 关联信息
  production_task_id?: number
  production_record_id?: number
  wps_id?: number
  pqr_id?: number

  // 检验人员
  inspector_id: number
  inspector_name?: string
  inspector_certification?: string
  witness_id?: number
  witness_name?: string

  // 检验对象
  welder_id?: number
  welder_name?: string
  equipment_id?: number
  joint_number?: string
  weld_location?: string

  // 检验标准
  inspection_standard?: string
  acceptance_criteria?: string
  quality_level?: string

  // 检验方法
  inspection_method?: string
  ndt_method?: string
  equipment_used?: string

  // 检验结果
  result: string
  is_qualified: boolean
  defects_found: number
  defect_details?: string

  // 缺陷详细计数
  crack_count?: number
  porosity_count?: number
  inclusion_count?: number
  undercut_count?: number
  incomplete_penetration_count?: number
  incomplete_fusion_count?: number
  other_defect_count?: number
  other_defect_description?: string

  // 处理措施
  corrective_action_required?: boolean
  corrective_actions?: string
  rework_required: boolean
  repair_required?: boolean
  repair_description?: string
  follow_up_required: boolean

  // 复检信息
  reinspection_required?: boolean
  reinspection_date?: string
  reinspection_result?: string
  reinspection_inspector_id?: number
  reinspection_notes?: string

  // 环境条件
  ambient_temperature?: number
  weather_conditions?: string

  // 附加信息
  photos?: string
  reports?: string
  tags?: string

  // 数据隔离字段
  workspace_type: string
  user_id: number
  company_id?: number
  factory_id?: number
  access_level: string

  // 审计字段
  created_by: number
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface QualityInspectionCreate {
  inspection_number: string
  inspection_type: string
  inspection_date: string
  production_task_id?: number
  production_record_id?: number
  wps_id?: number
  pqr_id?: number
  inspector_id: number
  inspector_name?: string
  inspector_certification?: string
  witness_id?: number
  witness_name?: string
  welder_id?: number
  welder_name?: string
  equipment_id?: number
  joint_number?: string
  weld_location?: string
  inspection_standard?: string
  acceptance_criteria?: string
  quality_level?: string
  inspection_method?: string
  ndt_method?: string
  equipment_used?: string
  result?: string
  is_qualified?: boolean
  defects_found?: number
  defect_details?: string
  crack_count?: number
  porosity_count?: number
  inclusion_count?: number
  undercut_count?: number
  incomplete_penetration_count?: number
  incomplete_fusion_count?: number
  other_defect_count?: number
  other_defect_description?: string
  corrective_action_required?: boolean
  corrective_actions?: string
  rework_required?: boolean
  repair_required?: boolean
  repair_description?: string
  follow_up_required?: boolean
  reinspection_required?: boolean
  reinspection_date?: string
  reinspection_result?: string
  reinspection_inspector_id?: number
  reinspection_notes?: string
  ambient_temperature?: number
  weather_conditions?: string
  photos?: string
  reports?: string
  tags?: string
}

export interface QualityInspectionUpdate {
  inspection_type?: string
  inspection_date?: string
  inspector_id?: number
  inspector_name?: string
  inspector_certification?: string
  witness_id?: number
  witness_name?: string
  welder_id?: number
  welder_name?: string
  equipment_id?: number
  joint_number?: string
  weld_location?: string
  inspection_standard?: string
  acceptance_criteria?: string
  quality_level?: string
  inspection_method?: string
  ndt_method?: string
  equipment_used?: string
  result?: string
  is_qualified?: boolean
  defects_found?: number
  defect_details?: string
  crack_count?: number
  porosity_count?: number
  inclusion_count?: number
  undercut_count?: number
  incomplete_penetration_count?: number
  incomplete_fusion_count?: number
  other_defect_count?: number
  other_defect_description?: string
  corrective_action_required?: boolean
  corrective_actions?: string
  rework_required?: boolean
  repair_required?: boolean
  repair_description?: string
  follow_up_required?: boolean
  reinspection_required?: boolean
  reinspection_date?: string
  reinspection_result?: string
  reinspection_inspector_id?: number
  reinspection_notes?: string
  ambient_temperature?: number
  weather_conditions?: string
  photos?: string
  reports?: string
  tags?: string
}

export interface QualityInspectionListParams {
  workspace_type: string
  company_id?: number
  factory_id?: number
  skip?: number
  limit?: number
  search?: string
  result?: string
  inspection_type?: string
  inspector_id?: number
}

export interface QualityInspectionListResponse {
  success: boolean
  data: {
    items: QualityInspection[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
  message: string
}

// ==================== API服务类 ====================

class QualityService {
  private baseUrl = '/quality/inspections'

  /**
   * 获取质量检验列表
   */
  async getQualityInspectionList(params: QualityInspectionListParams): Promise<QualityInspectionListResponse> {
    const queryParams: any = {
      workspace_type: params.workspace_type,
      skip: params.skip || 0,
      limit: params.limit || 100,
    }

    if (params.company_id) {
      queryParams.company_id = params.company_id
    }

    if (params.factory_id) {
      queryParams.factory_id = params.factory_id
    }

    if (params.search) {
      queryParams.search = params.search
    }

    if (params.inspection_type) {
      queryParams.inspection_type = params.inspection_type
    }

    if (params.result) {
      queryParams.result = params.result
    }

    if (params.inspector_id) {
      queryParams.inspector_id = params.inspector_id
    }

    const response = await api.get(this.baseUrl, { params: queryParams })
    return response
  }

  /**
   * 获取质量检验详情
   */
  async getQualityInspectionById(
    inspectionId: number,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<ApiResponse<QualityInspection>> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.get(`${this.baseUrl}/${inspectionId}`, { params })
    return response
  }

  /**
   * 创建质量检验
   */
  async createQualityInspection(
    data: QualityInspectionCreate,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<ApiResponse<QualityInspection>> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.post(this.baseUrl, data, { params })
    return response
  }

  /**
   * 更新质量检验
   */
  async updateQualityInspection(
    inspectionId: number,
    data: QualityInspectionUpdate,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<ApiResponse<QualityInspection>> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.put(`${this.baseUrl}/${inspectionId}`, data, { params })
    return response
  }

  /**
   * 删除质量检验
   */
  async deleteQualityInspection(
    inspectionId: number,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<ApiResponse<void>> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.delete(`${this.baseUrl}/${inspectionId}`, { params })
    return response
  }

  /**
   * 批量删除质量检验
   */
  async batchDeleteQualityInspections(
    inspectionIds: number[],
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<ApiResponse<void>> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.post(`${this.baseUrl}/batch-delete`, { ids: inspectionIds }, { params })
    return response
  }

  async getStatistics(
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ) {
    const params: Record<string, unknown> = { workspace_type: workspaceType }
    if (companyId) params.company_id = companyId
    if (factoryId) params.factory_id = factoryId
    return api.get('/quality/statistics/overview', { params })
  }
}

// 导出服务实例
const qualityService = new QualityService()
export default qualityService

