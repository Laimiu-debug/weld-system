/**
 * 自定义模块API服务
 */
import api from './api'
import { FieldModule } from '@/types/wpsModules'

export type ModuleCategory =
  | 'basic'
  | 'parameters'
  | 'materials'
  | 'tests'
  | 'results'
  | 'equipment'
  | 'attachments'
  | 'notes'

export interface SemanticFieldDefinition {
  key: string
  label: string
  data_type: string
  document_types: string[]
  unit?: string
  description: string
  aliases: string[]
  rule_input: boolean
  enum: string[]
}

export interface ExtractionSchemaResponse {
  schema_version: string
  document_type: string
  source: Record<string, unknown>
  json_schema: Record<string, unknown>
  field_bindings: Array<Record<string, unknown>>
  warnings?: Array<Record<string, unknown>>
}

export interface CustomModuleCreate {
  id?: string
  name: string
  description?: string
  icon?: string
  category: ModuleCategory
  repeatable: boolean
  fields: Record<string, any>
  is_shared?: boolean
  module_type?: 'wps' | 'pqr' | 'ppqr' | 'common'
  access_level?: 'private' | 'shared' | 'public'
}

export interface CustomModuleUpdate {
  name?: string
  description?: string
  icon?: string
  category?: ModuleCategory
  repeatable?: boolean
  fields?: Record<string, any>
  is_shared?: boolean
  access_level?: 'private' | 'shared' | 'public'
}

export interface CustomModuleResponse extends FieldModule {
  user_id?: number
  workspace_type: string
  company_id?: number
  factory_id?: number
  usage_count: number
  schema_version: number
  created_at: string
  updated_at: string
}

export interface CustomModuleSummary {
  id: string
  name: string
  description?: string
  icon: string
  module_type?: string  // 模块类型: wps, pqr, ppqr, common
  category: string
  repeatable: boolean
  field_count: number
  usage_count: number
  is_shared: boolean
  access_level: string
  created_at: string
}

class CustomModuleService {
  async getSemanticFields(
    moduleType?: 'wps' | 'pqr' | 'ppqr'
  ): Promise<SemanticFieldDefinition[]> {
    const response = await api.get('/custom-modules/semantic-fields/registry', {
      params: moduleType ? { module_type: moduleType } : undefined
    })
    return response.data
  }

  async getExtractionSchema(id: string): Promise<ExtractionSchemaResponse> {
    const response = await api.get(`/custom-modules/${id}/extraction-schema`)
    return response.data
  }

  /**
   * 获取自定义模块列表
   */
  async getCustomModules(params?: {
    category?: string
    skip?: number
    limit?: number
  }): Promise<CustomModuleSummary[]> {
    const response = await api.get('/custom-modules/', { params })
    return response.data
  }

  /**
   * 获取单个自定义模块
   */
  async getCustomModule(id: string): Promise<CustomModuleResponse> {
    const response = await api.get(`/custom-modules/${id}`)
    return response.data
  }

  /**
   * 创建自定义模块
   */
  async createCustomModule(data: CustomModuleCreate): Promise<CustomModuleResponse> {
    const response = await api.post('/custom-modules/', data)
    return response.data
  }

  /**
   * 更新自定义模块
   */
  async updateCustomModule(id: string, data: CustomModuleUpdate): Promise<CustomModuleResponse> {
    const response = await api.put(`/custom-modules/${id}`, data)
    return response.data
  }

  /**
   * 删除自定义模块
   */
  async deleteCustomModule(id: string): Promise<void> {
    await api.delete(`/custom-modules/${id}`)
  }

  /**
   * 增加模块使用次数
   */
  async incrementUsage(id: string): Promise<void> {
    await api.post(`/custom-modules/${id}/increment-usage`)
  }
}

export default new CustomModuleService()
