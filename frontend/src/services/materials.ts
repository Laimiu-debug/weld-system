/**
 * Materials Management API Service
 * 焊材管理API服务
 */

import api from './api'

// ==================== 类型定义 ====================

export interface Material {
  id: number
  material_code: string
  material_name: string
  material_type: string
  specification?: string
  manufacturer?: string
  current_stock: number
  unit: string
  min_stock_level?: number
  reorder_point?: number
  unit_price?: number
  storage_location?: string
  warehouse?: string
  supplier?: string
  batch_number?: string
  production_date?: string
  expiry_date?: string
  quality_certificate?: string
  notes?: string
  
  // 数据隔离字段
  workspace_type: 'personal' | 'enterprise'
  user_id: number
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

export interface MaterialCreate {
  material_code: string
  material_name: string
  material_type: string
  specification?: string
  manufacturer?: string
  current_stock?: number
  unit?: string
  min_stock_level?: number
  reorder_point?: number
  unit_price?: number
  storage_location?: string
  supplier?: string
  batch_number?: string
  production_date?: string
  expiry_date?: string
  quality_certificate?: string
  notes?: string
}

export interface MaterialUpdate {
  material_code?: string
  material_name?: string
  material_type?: string
  specification?: string
  manufacturer?: string
  current_stock?: number
  unit?: string
  min_stock_level?: number
  reorder_point?: number
  unit_price?: number
  storage_location?: string
  supplier?: string
  batch_number?: string
  production_date?: string
  expiry_date?: string
  quality_certificate?: string
  notes?: string
}

// 出入库相关类型
export interface MaterialTransaction {
  id: number
  material_id: number
  transaction_type: 'in' | 'out' | 'adjust' | 'return' | 'transfer' | 'consume'
  transaction_number: string
  transaction_date: string
  quantity: number
  unit: string
  stock_before: number
  stock_after: number
  unit_price?: number
  total_price?: number
  currency?: string
  source?: string
  destination?: string
  reference_type?: string
  reference_id?: number
  reference_number?: string
  batch_number?: string
  warehouse?: string
  storage_location?: string
  operator?: string
  notes?: string
  created_at: string
  created_by: number
}

export interface StockInRequest {
  material_id: number
  quantity: number
  unit_price?: number
  source?: string
  batch_number?: string
  warehouse?: string
  storage_location?: string
  notes?: string
}

export interface StockOutRequest {
  material_id: number
  quantity: number
  destination?: string
  reference_type?: string
  reference_id?: number
  reference_number?: string
  notes?: string
}

export interface TransactionListParams {
  workspace_type: 'personal' | 'enterprise'
  company_id?: number
  factory_id?: number
  material_id?: number
  transaction_type?: string
  skip?: number
  limit?: number
}

export interface MaterialListParams {
  workspace_type: 'personal' | 'enterprise'
  company_id?: number
  factory_id?: number
  skip?: number
  limit?: number
  search?: string
  material_type?: string
  low_stock?: boolean
}

export interface MaterialListResponse {
  success: boolean
  data: {
    items: Material[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
  message?: string
}

export interface MaterialResponse {
  success: boolean
  data: Material
  message?: string
}

// ==================== API服务类 ====================

class MaterialsService {
  private baseUrl = '/materials/'

  /**
   * 获取焊材列表
   */
  async getMaterialsList(params: MaterialListParams): Promise<MaterialListResponse> {
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

    if (params.material_type) {
      queryParams.material_type = params.material_type
    }

    if (params.low_stock !== undefined) {
      queryParams.low_stock = params.low_stock
    }

    const response = await api.get(this.baseUrl, { params: queryParams })
    return response
  }

  /**
   * 获取焊材详情
   */
  async getMaterialById(
    materialId: number,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<MaterialResponse> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.get(`${this.baseUrl}/${materialId}`, { params })
    return response
  }

  /**
   * 创建焊材
   */
  async createMaterial(
    data: MaterialCreate,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<MaterialResponse> {
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
   * 更新焊材
   */
  async updateMaterial(
    materialId: number,
    data: MaterialUpdate,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<MaterialResponse> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.put(`${this.baseUrl}/${materialId}`, data, { params })
    return response
  }

  /**
   * 删除焊材
   */
  async deleteMaterial(
    materialId: number,
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<{ success: boolean; message?: string }> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.delete(`${this.baseUrl}/${materialId}`, { params })
    return response
  }

  /**
   * 批量删除焊材
   */
  async batchDeleteMaterials(
    materialIds: number[],
    workspaceType: 'personal' | 'enterprise',
    companyId?: number,
    factoryId?: number
  ): Promise<{ success: boolean; message?: string }> {
    const params: any = {
      workspace_type: workspaceType,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    const response = await api.post(`${this.baseUrl}/batch-delete`, { ids: materialIds }, { params })
    return response
  }

  /**
   * 焊材入库
   */
  async stockIn(
    workspaceType: 'personal' | 'enterprise',
    companyId: number | undefined,
    factoryId: number | undefined,
    data: StockInRequest
  ) {
    const params: any = {
      workspace_type: workspaceType,
      material_id: data.material_id,
      quantity: data.quantity,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    if (data.unit_price !== undefined) {
      params.unit_price = data.unit_price
    }

    if (data.source) {
      params.source = data.source
    }

    if (data.batch_number) {
      params.batch_number = data.batch_number
    }

    if (data.warehouse) {
      params.warehouse = data.warehouse
    }

    if (data.storage_location) {
      params.storage_location = data.storage_location
    }

    if (data.notes) {
      params.notes = data.notes
    }

    const response = await api.post(`${this.baseUrl}/stock-in`, null, { params })
    return response
  }

  /**
   * 焊材出库
   */
  async stockOut(
    workspaceType: 'personal' | 'enterprise',
    companyId: number | undefined,
    factoryId: number | undefined,
    data: StockOutRequest
  ) {
    const params: any = {
      workspace_type: workspaceType,
      material_id: data.material_id,
      quantity: data.quantity,
    }

    if (companyId) {
      params.company_id = companyId
    }

    if (factoryId) {
      params.factory_id = factoryId
    }

    if (data.destination) {
      params.destination = data.destination
    }

    if (data.reference_type) {
      params.reference_type = data.reference_type
    }

    if (data.reference_id !== undefined) {
      params.reference_id = data.reference_id
    }

    if (data.reference_number) {
      params.reference_number = data.reference_number
    }

    if (data.notes) {
      params.notes = data.notes
    }

    const response = await api.post(`${this.baseUrl}/stock-out`, null, { params })
    return response
  }

  /**
   * 获取出入库记录列表
   */
  async getTransactionList(params: TransactionListParams) {
    const queryParams: any = {
      workspace_type: params.workspace_type,
      skip: params.skip || 0,
      limit: params.limit || 20,
    }

    if (params.company_id) {
      queryParams.company_id = params.company_id
    }

    if (params.factory_id) {
      queryParams.factory_id = params.factory_id
    }

    if (params.material_id !== undefined) {
      queryParams.material_id = params.material_id
    }

    if (params.transaction_type) {
      queryParams.transaction_type = params.transaction_type
    }

    const response = await api.get(`${this.baseUrl}/transactions`, { params: queryParams })
    return response
  }
}

// 导出单例
export const materialsService = new MaterialsService()
export default materialsService

