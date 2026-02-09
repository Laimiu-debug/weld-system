/**
 * WPS模板API服务
 */
import apiService from './api'
import { ApiResponse, PaginatedResponse } from '@/types'

// ==================== 类型定义 ====================
// 注：已移除 FieldDefinition, TabDefinition, TopInfoDefinition, FieldSchema, UILayout
// 这些类型在新的模块化系统中不再需要

/**
 * 模块实例
 */
export interface ModuleInstance {
  instanceId: string
  moduleId: string
  order: number
  customName?: string
}

/**
 * WPS模板
 */
export interface WPSTemplate {
  id: string
  name: string
  description?: string
  welding_process: string
  welding_process_name?: string
  standard?: string
  module_type?: 'wps' | 'pqr' | 'ppqr'  // 模板类型
  // 注：已移除 field_schema, ui_layout, validation_rules, default_values
  // 现在仅使用 module_instances 基于模块的模板方式
  module_instances: ModuleInstance[]  // 基于模块的模板

  // 数据隔离
  user_id?: number
  workspace_type: 'system' | 'personal' | 'enterprise'
  company_id?: number
  factory_id?: number
  is_shared?: boolean
  access_level?: 'private' | 'factory' | 'company' | 'public'
  template_source: 'system' | 'user' | 'enterprise'

  // 元数据
  version?: string
  is_active: boolean
  is_system: boolean
  usage_count?: number

  // 审计
  created_by?: number
  updated_by?: number
  created_at?: string
  updated_at?: string
}

/**
 * 模板摘要（列表用）
 */
export interface WPSTemplateSummary {
  id: string
  name: string
  description?: string
  welding_process?: string
  welding_process_name?: string
  standard?: string
  module_type?: 'wps' | 'pqr' | 'ppqr'  // 模板类型
  template_source: 'system' | 'user' | 'enterprise'
  is_system: boolean
  is_shared: boolean
  usage_count: number
  created_at: string
}

/**
 * 模板列表响应
 */
export interface WPSTemplateListResponse {
  total: number
  items: WPSTemplateSummary[]
}

/**
 * 创建模板请求
 */
export interface CreateWPSTemplateRequest {
  name: string
  description?: string
  welding_process: string
  welding_process_name?: string
  standard?: string
  field_schema?: FieldSchema  // 传统方式（可选）
  ui_layout?: UILayout  // 传统方式（可选）
  validation_rules?: Record<string, any>
  default_values?: Record<string, any>
  module_instances?: ModuleInstance[]  // 新方式：基于模块的模板
  workspace_type?: 'personal' | 'enterprise'
  is_shared?: boolean
  access_level?: 'private' | 'factory' | 'company'
}

/**
 * 更新模板请求
 */
export interface UpdateWPSTemplateRequest {
  name?: string
  description?: string
  field_schema?: FieldSchema
  ui_layout?: UILayout
  validation_rules?: Record<string, any>
  default_values?: Record<string, any>
  module_instances?: ModuleInstance[]  // 新方式：基于模块的模板
  is_shared?: boolean
  access_level?: 'private' | 'factory' | 'company'
  is_active?: boolean
}

/**
 * 焊接工艺
 */
export interface WeldingProcess {
  code: string
  name: string
  name_en: string
}

/**
 * 焊接标准
 */
export interface WeldingStandard {
  code: string
  name: string
}

// ==================== API服务 ====================

class WPSTemplateService {
  /**
   * 获取模板列表
   */
  async getTemplates(params?: {
    welding_process?: string
    standard?: string
    module_type?: 'wps' | 'pqr' | 'ppqr'
    skip?: number
    limit?: number
  }): Promise<ApiResponse<WPSTemplateListResponse>> {
    return apiService.get('/wps-templates/', { params })
  }

  /**
   * 获取模板详情
   */
  async getTemplate(templateId: string): Promise<ApiResponse<WPSTemplate>> {
    return apiService.get(`/wps-templates/${templateId}`)
  }

  /**
   * 创建模板
   */
  async createTemplate(data: CreateWPSTemplateRequest): Promise<ApiResponse<WPSTemplate>> {
    return apiService.post('/wps-templates/', data)
  }

  /**
   * 更新模板
   */
  async updateTemplate(
    templateId: string,
    data: UpdateWPSTemplateRequest
  ): Promise<ApiResponse<WPSTemplate>> {
    return apiService.put(`/wps-templates/${templateId}`, data)
  }

  /**
   * 删除模板
   */
  async deleteTemplate(templateId: string): Promise<ApiResponse<void>> {
    return apiService.delete(`/wps-templates/${templateId}`)
  }

  /**
   * 获取焊接工艺列表
   */
  async getWeldingProcesses(): Promise<ApiResponse<WeldingProcess[]>> {
    return apiService.get('/wps-templates/welding-processes/list')
  }

  /**
   * 获取焊接标准列表
   */
  async getWeldingStandards(): Promise<ApiResponse<WeldingStandard[]>> {
    return apiService.get('/wps-templates/standards/list')
  }

  /**
   * 根据焊接工艺和标准获取模板
   */
  async getTemplatesByProcessAndStandard(
    weldingProcess: string,
    standard?: string
  ): Promise<ApiResponse<WPSTemplateListResponse>> {
    return this.getTemplates({
      welding_process: weldingProcess,
      standard,
      limit: 100
    })
  }
}

// 导出单例
const wpsTemplateService = new WPSTemplateService()
export default wpsTemplateService

