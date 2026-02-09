/**
 * 焊工管理服务
 */
import api from './api'
import { workspaceService } from './workspace'

// ==================== 类型定义 ====================

export interface Welder {
  id: number
  welder_code: string
  full_name: string
  english_name?: string
  gender?: string
  date_of_birth?: string
  
  // 身份信息
  id_type?: string
  id_number?: string
  nationality: string
  
  // 联系信息
  phone?: string
  email?: string
  address?: string
  emergency_contact?: string
  emergency_phone?: string
  
  // 雇佣信息
  employment_date?: string
  employment_type?: string
  department?: string
  position?: string
  
  // 技能等级
  skill_level?: string
  specialization?: string
  qualified_processes?: string
  qualified_positions?: string
  qualified_materials?: string
  
  // 主要证书信息
  primary_certification_number?: string
  primary_certification_level?: string
  primary_certification_date?: string
  primary_expiry_date?: string
  primary_issuing_authority?: string
  
  // 状态信息
  status: string
  certification_status: string
  
  // 绩效统计
  total_tasks_completed: number
  total_weld_length: number
  total_work_hours: number
  quality_score?: number
  efficiency_score?: number
  safety_score?: number
  
  // 培训信息
  last_training_date?: string
  next_training_date?: string
  training_hours: number
  
  // 健康信息
  last_health_check_date?: string
  next_health_check_date?: string
  health_status?: string
  medical_restrictions?: string
  
  // 附加信息
  photo_url?: string
  description?: string
  notes?: string
  documents?: string
  tags?: string
  
  // 工作区字段
  workspace_type: string
  user_id?: number
  company_id?: number
  factory_id?: number
  access_level: string
  
  // 审计字段
  created_by: number
  updated_by?: number
  created_at: string
  updated_at?: string
  is_active: boolean
}

export interface WelderCreate {
  welder_code: string
  full_name: string
  english_name?: string
  gender?: string
  date_of_birth?: string
  id_type?: string
  id_number?: string
  nationality?: string
  phone?: string
  email?: string
  address?: string
  emergency_contact?: string
  emergency_phone?: string
  employment_date?: string
  employment_type?: string
  department?: string
  position?: string
  skill_level?: string
  specialization?: string
  qualified_processes?: string
  qualified_positions?: string
  qualified_materials?: string
  primary_certification_number?: string
  primary_certification_level?: string
  primary_certification_date?: string
  primary_expiry_date?: string
  primary_issuing_authority?: string
  status?: string
  certification_status?: string
  photo_url?: string
  description?: string
  notes?: string
  tags?: string
}

export interface WelderUpdate extends Partial<WelderCreate> {}

export interface WelderListParams {
  skip?: number
  limit?: number
  search?: string
  skill_level?: string
  status?: string
  certification_status?: string
}

export interface WelderListResponse {
  success: boolean
  data: {
    items: Welder[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
  message: string
}

export interface WelderDetailResponse {
  success: boolean
  data: Welder
  message: string
}

// ==================== API服务 ====================

class WeldersService {
  /**
   * 获取焊工列表
   */
  async getList(params: WelderListParams = {}): Promise<WelderListResponse> {
    const workspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!workspace) {
      throw new Error('未找到工作区信息')
    }

    const queryParams: any = {
      workspace_type: workspace.type,
      skip: params.skip || 0,
      limit: params.limit || 100,
    }

    if (workspace.type === 'enterprise') {
      queryParams.company_id = workspace.company_id
      if (workspace.factory_id) {
        queryParams.factory_id = workspace.factory_id
      }
    }

    if (params.search) queryParams.search = params.search
    if (params.skill_level) queryParams.skill_level = params.skill_level
    if (params.status) queryParams.status = params.status
    if (params.certification_status) queryParams.certification_status = params.certification_status

    const response = await api.get<WelderListResponse>('/welders/', { params: queryParams })
    return response.data
  }

  /**
   * 创建焊工
   */
  async create(data: WelderCreate): Promise<WelderDetailResponse> {
    const workspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!workspace) {
      throw new Error('未找到工作区信息')
    }

    const queryParams: any = {
      workspace_type: workspace.type,
    }

    if (workspace.type === 'enterprise') {
      queryParams.company_id = workspace.company_id
      if (workspace.factory_id) {
        queryParams.factory_id = workspace.factory_id
      }
    }

    const response = await api.post<WelderDetailResponse>('/welders/', data, { params: queryParams })
    return response.data
  }

  /**
   * 获取焊工详情
   */
  async getDetail(welderId: number): Promise<WelderDetailResponse> {
    const workspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!workspace) {
      throw new Error('未找到工作区信息')
    }

    const queryParams: any = {
      workspace_type: workspace.type,
    }

    if (workspace.type === 'enterprise') {
      queryParams.company_id = workspace.company_id
      if (workspace.factory_id) {
        queryParams.factory_id = workspace.factory_id
      }
    }

    const response = await api.get<WelderDetailResponse>(`/welders/${welderId}`, { params: queryParams })
    return response.data
  }

  /**
   * 更新焊工
   */
  async update(welderId: number, data: WelderUpdate): Promise<WelderDetailResponse> {
    const workspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!workspace) {
      throw new Error('未找到工作区信息')
    }

    const queryParams: any = {
      workspace_type: workspace.type,
    }

    if (workspace.type === 'enterprise') {
      queryParams.company_id = workspace.company_id
      if (workspace.factory_id) {
        queryParams.factory_id = workspace.factory_id
      }
    }

    const response = await api.put<WelderDetailResponse>(`/welders/${welderId}`, data, { params: queryParams })
    return response.data
  }

  /**
   * 删除焊工
   */
  async delete(welderId: number): Promise<{ success: boolean; message: string }> {
    const workspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!workspace) {
      throw new Error('未找到工作区信息')
    }

    const queryParams: any = {
      workspace_type: workspace.type,
    }

    if (workspace.type === 'enterprise') {
      queryParams.company_id = workspace.company_id
      if (workspace.factory_id) {
        queryParams.factory_id = workspace.factory_id
      }
    }

    const response = await api.delete<{ success: boolean; message: string }>(`/welders/${welderId}`, { params: queryParams })
    return response.data
  }
}

export default new WeldersService()

