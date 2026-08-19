/**
 * 自定义模块API服务
 */
import api from './api'
import { FieldModule } from '@/types/wpsModules'

export interface CustomModuleCreate {
  id?: string
  name: string
  description?: string
  icon?: string
  category: 'basic' | 'material' | 'gas' | 'electrical' | 'motion' | 'equipment' | 'calculation'
  repeatable: boolean
  fields: Record<string, any>
  is_shared?: boolean
  module_type?: 'wps' | 'pqr' | 'ppqr'
  access_level?: 'private' | 'shared' | 'public'
}

export interface CustomModuleUpdate {
  name?: string
  description?: string
  icon?: string
  category?: 'basic' | 'material' | 'gas' | 'electrical' | 'motion' | 'equipment' | 'calculation'
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

