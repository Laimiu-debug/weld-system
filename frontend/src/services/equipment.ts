import { apiService } from './api'
import { ApiResponse, PaginatedResponse } from '@/types'

// 设备相关类型定义
export interface Equipment {
  id: string
  user_id: string
  company_id?: string
  factory_id?: string
  equipment_code: string
  equipment_name: string
  equipment_type: EquipmentType
  category?: string
  manufacturer?: string
  brand?: string
  model?: string
  serial_number?: string
  specifications?: string
  rated_power?: number
  rated_voltage?: number
  rated_current?: number
  max_capacity?: number
  working_range?: string
  purchase_date?: string
  purchase_price?: number
  currency: string
  supplier?: string
  warranty_period?: number
  warranty_expiry_date?: string
  location?: string
  workshop?: string
  area?: string
  status: EquipmentStatus
  is_active: boolean
  is_critical: boolean
  installation_date?: string
  commissioning_date?: string
  total_operating_hours?: number
  total_maintenance_hours?: number
  last_used_date?: string
  usage_count?: number
  last_maintenance_date?: string
  next_maintenance_date?: string
  maintenance_interval_days?: number
  maintenance_count?: number
  last_inspection_date?: string
  next_inspection_date?: string
  inspection_interval_days?: number
  calibration_date?: string
  calibration_due_date?: string
  responsible_person_id?: number
  operator_ids?: string
  availability_rate?: number
  utilization_rate?: number
  failure_rate?: number
  mtbf?: number
  mttr?: number
  description?: string
  notes?: string
  manual_url?: string
  images?: string
  documents?: string
  tags?: string
  access_level: string
  created_at: string
  updated_at: string
}

export type EquipmentType =
  | 'welding_machine'      // 焊接设备
  | 'cutting_machine'      // 切割设备
  | 'grinding_machine'     // 打磨设备
  | 'testing_equipment'    // 检测设备
  | 'auxiliary_equipment'  // 辅助设备
  | 'other'               // 其他

export type EquipmentStatus =
  | 'operational'  // 运行中
  | 'idle'         // 空闲
  | 'maintenance'  // 维护中
  | 'repair'       // 维修中
  | 'broken'       // 故障
  | 'retired'      // 报废

export type AccessLevel =
  | 'private'  // 仅创建者可见
  | 'factory'  // 同工厂成员可见
  | 'company'  // 全公司成员可见
  | 'public'   // 公开

// 设备创建数据
export interface CreateEquipmentData {
  equipment_code: string
  equipment_name: string
  equipment_type: EquipmentType
  category?: string
  manufacturer?: string
  brand?: string
  model?: string
  serial_number?: string
  specifications?: string
  rated_power?: number
  rated_voltage?: number
  rated_current?: number
  max_capacity?: number
  working_range?: string
  purchase_date?: string
  purchase_price?: number
  currency?: string
  supplier?: string
  warranty_period?: number
  warranty_expiry_date?: string
  location?: string
  workshop?: string
  area?: string
  status?: EquipmentStatus
  is_active?: boolean
  is_critical?: boolean
  installation_date?: string
  commissioning_date?: string
  maintenance_interval_days?: number
  inspection_interval_days?: number
  responsible_person_id?: number
  description?: string
  notes?: string
  manual_url?: string
  images?: string
  documents?: string
  tags?: string
  access_level?: AccessLevel
}

// 设备更新数据
export interface UpdateEquipmentData {
  equipment_name?: string
  equipment_type?: EquipmentType
  category?: string
  manufacturer?: string
  brand?: string
  model?: string
  specifications?: string
  rated_power?: number
  rated_voltage?: number
  rated_current?: number
  max_capacity?: number
  working_range?: string
  purchase_price?: number
  supplier?: string
  location?: string
  workshop?: string
  area?: string
  status?: EquipmentStatus
  is_active?: boolean
  is_critical?: boolean
  description?: string
  notes?: string
  manual_url?: string
  images?: string
  documents?: string
  tags?: string
  access_level?: AccessLevel
}

// 设备状态更新数据
export interface StatusUpdateData {
  status: EquipmentStatus
  notes?: string
}

// 设备查询参数
export interface EquipmentListParams {
  skip?: number
  limit?: number
  search?: string
  equipment_type?: EquipmentType
  status?: EquipmentStatus
  factory_id?: number
  workspace_type?: 'personal' | 'company'
}

// 设备统计信息
export interface EquipmentStatistics {
  total_equipment: number
  operational: number
  idle: number
  maintenance: number
  repair: number
  broken: number
  upcoming_maintenance: number
  overdue_inspection: number
  status_counts: Record<string, number>
  type_counts: Record<string, number>
}

// 维护提醒
export interface MaintenanceAlert {
  id: string
  equipment_code: string
  equipment_name: string
  equipment_type: EquipmentType
  next_maintenance_date: string
  days_until_maintenance: number
  urgency: 'urgent' | 'normal' | 'low'
  location?: string
  status: EquipmentStatus
}

export interface MaintenanceRecordItem {
  id: number
  equipment_id: number
  equipment_code: string
  equipment_name: string
  maintenance_code?: string
  maintenance_type: string
  start_date?: string
  end_date?: string
  duration_hours?: number
  technician_name?: string
  work_description?: string
  result?: string
  status?: string
  notes?: string
  created_at?: string
}

export interface UsageRecordItem {
  id: number
  equipment_id: number
  equipment_code: string
  equipment_name: string
  usage_date?: string
  start_time?: string
  end_time?: string
  duration_hours?: number
  operator_id?: number
  work_type?: string
  work_description?: string
  output_quantity?: number
  output_unit?: string
  issues_occurred?: boolean
  issue_description?: string
  notes?: string
  created_at?: string
}

export interface CreateMaintenanceRecordData {
  equipment_id: number
  maintenance_type: string
  start_date: string
  end_date?: string
  duration_hours?: number
  technician_name?: string
  work_description?: string
  result?: string
  notes?: string
}

export interface CreateUsageRecordData {
  equipment_id: number
  usage_date: string
  start_time?: string
  end_time?: string
  duration_hours?: number
  work_type?: string
  work_description?: string
  output_quantity?: number
  output_unit?: string
  issues_occurred?: boolean
  issue_description?: string
  notes?: string
}

// 设备服务类
class EquipmentService {
  // ==================== 设备基础管理 ====================

  /**
   * 获取设备列表
   */
  async getEquipmentList(params?: EquipmentListParams): Promise<PaginatedResponse<Equipment>> {
    const queryParams = new URLSearchParams()

    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    if (params?.search) queryParams.append('search', params.search)
    if (params?.equipment_type) queryParams.append('equipment_type', params.equipment_type)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.factory_id) queryParams.append('factory_id', params.factory_id.toString())
    if (params?.workspace_type) queryParams.append('workspace_type', params.workspace_type)

    const url = `/equipment/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiService.get<PaginatedResponse<Equipment>>(url)

    return response.data
  }

  /**
   * 获取设备详情
   */
  async getEquipmentDetail(equipmentId: string): Promise<ApiResponse<Equipment>> {
    const response = await apiService.get<Equipment>(`/equipment/${equipmentId}`)
    return response.data
  }

  /**
   * 创建新设备
   */
  async createEquipment(data: CreateEquipmentData): Promise<ApiResponse<Equipment>> {
    // 获取当前工作区类型
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'

    // 添加工作区类型参数到URL (注意URL末尾的斜杠,避免307重定向)
    const response = await apiService.post<Equipment>(
      `/equipment/?workspace_type=${workspaceType}`,
      data
    )
    return response.data
  }

  /**
   * 获取当前工作区（从本地存储）
   */
  private getCurrentWorkspace() {
    try {
      const workspaceData = localStorage.getItem('current_workspace')
      return workspaceData ? JSON.parse(workspaceData) : null
    } catch (error) {
      console.error('获取当前工作区失败:', error)
      return null
    }
  }

  /**
   * 更新设备信息
   */
  async updateEquipment(equipmentId: string, data: UpdateEquipmentData): Promise<ApiResponse<Equipment>> {
    // 获取当前工作区类型
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'

    const response = await apiService.put<Equipment>(
      `/equipment/${equipmentId}?workspace_type=${workspaceType}`,
      data
    )
    return response.data
  }

  /**
   * 删除设备
   */
  async deleteEquipment(equipmentId: string): Promise<ApiResponse<void>> {
    // 获取当前工作区类型
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'

    const response = await apiService.delete<void>(
      `/equipment/${equipmentId}?workspace_type=${workspaceType}`
    )
    return response.data
  }

  // ==================== 设备状态管理 ====================

  /**
   * 更新设备状态
   */
  async updateEquipmentStatus(equipmentId: string, data: StatusUpdateData): Promise<ApiResponse<Equipment>> {
    const response = await apiService.put<Equipment>(`/equipment/${equipmentId}/status`, data)
    return response.data
  }

  // ==================== 设备统计和提醒 ====================

  /**
   * 获取设备统计信息
   */
  async getEquipmentStatistics(): Promise<ApiResponse<EquipmentStatistics>> {
    // 获取当前工作区类型
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'

    const response = await apiService.get<EquipmentStatistics>(
      `/equipment/statistics/overview?workspace_type=${workspaceType}`
    )
    return response.data
  }

  /**
   * 获取维护提醒
   */
  async getMaintenanceAlerts(days: number = 30): Promise<ApiResponse<{ items: MaintenanceAlert[], total: number }>> {
    const response = await apiService.get<{ items: MaintenanceAlert[], total: number }>(`/equipment/maintenance/alerts?days=${days}`)
    return response.data
  }

  async getMaintenanceRecords(params?: {
    skip?: number
    limit?: number
    equipment_id?: number
  }): Promise<ApiResponse<{ items: MaintenanceRecordItem[], total: number }>> {
    const queryParams = new URLSearchParams()
    const currentWorkspace = this.getCurrentWorkspace()
    queryParams.append('workspace_type', currentWorkspace?.type === 'enterprise' ? 'company' : 'personal')
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    if (params?.equipment_id !== undefined) queryParams.append('equipment_id', params.equipment_id.toString())
    const response = await apiService.get<{ items: MaintenanceRecordItem[], total: number }>(
      `/equipment/maintenance-records?${queryParams.toString()}`
    )
    return response.data
  }

  async createMaintenanceRecord(
    data: CreateMaintenanceRecordData
  ): Promise<ApiResponse<MaintenanceRecordItem>> {
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
    const response = await apiService.post<MaintenanceRecordItem>(
      `/equipment/maintenance-records?workspace_type=${workspaceType}`,
      data
    )
    return response.data
  }

  async getUsageRecords(params?: {
    skip?: number
    limit?: number
    equipment_id?: number
  }): Promise<ApiResponse<{ items: UsageRecordItem[], total: number }>> {
    const queryParams = new URLSearchParams()
    const currentWorkspace = this.getCurrentWorkspace()
    queryParams.append('workspace_type', currentWorkspace?.type === 'enterprise' ? 'company' : 'personal')
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    if (params?.equipment_id !== undefined) queryParams.append('equipment_id', params.equipment_id.toString())
    const response = await apiService.get<{ items: UsageRecordItem[], total: number }>(
      `/equipment/usage-records?${queryParams.toString()}`
    )
    return response.data
  }

  async createUsageRecord(data: CreateUsageRecordData): Promise<ApiResponse<UsageRecordItem>> {
    const currentWorkspace = this.getCurrentWorkspace()
    const workspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
    const response = await apiService.post<UsageRecordItem>(
      `/equipment/usage-records?workspace_type=${workspaceType}`,
      data
    )
    return response.data
  }

  // ==================== 工具方法 ====================

  /**
   * 获取设备类型选项
   */
  getEquipmentTypeOptions(): Array<{ label: string, value: EquipmentType }> {
    return [
      { label: '焊接设备', value: 'welding_machine' },
      { label: '切割设备', value: 'cutting_machine' },
      { label: '打磨设备', value: 'grinding_machine' },
      { label: '检测设备', value: 'testing_equipment' },
      { label: '辅助设备', value: 'auxiliary_equipment' },
      { label: '其他', value: 'other' }
    ]
  }

  /**
   * 获取设备状态选项
   */
  getEquipmentStatusOptions(): Array<{ label: string, value: EquipmentStatus, color: string }> {
    return [
      { label: '运行中', value: 'operational', color: 'green' },
      { label: '空闲', value: 'idle', color: 'blue' },
      { label: '维护中', value: 'maintenance', color: 'orange' },
      { label: '维修中', value: 'repair', color: 'red' },
      { label: '故障', value: 'broken', color: 'red' },
      { label: '报废', value: 'retired', color: 'gray' }
    ]
  }

  /**
   * 获取访问级别选项
   */
  getAccessLevelOptions(): Array<{ label: string, value: AccessLevel, description: string }> {
    return [
      { label: '私有', value: 'private', description: '仅创建者可见' },
      { label: '工厂级', value: 'factory', description: '同工厂成员可见' },
      { label: '公司级', value: 'company', description: '全公司成员可见' },
      { label: '公开', value: 'public', description: '所有企业成员可见' }
    ]
  }

  /**
   * 格式化设备状态显示
   */
  formatEquipmentStatus(status: EquipmentStatus): { text: string, color: string } {
    const statusMap = {
      operational: { text: '运行中', color: 'green' },
      idle: { text: '空闲', color: 'blue' },
      maintenance: { text: '维护中', color: 'orange' },
      repair: { text: '维修中', color: 'red' },
      broken: { text: '故障', color: 'red' },
      retired: { text: '报废', color: 'gray' }
    }
    return statusMap[status] || { text: status, color: 'default' }
  }

  /**
   * 格式化设备类型显示
   */
  formatEquipmentType(type: EquipmentType): string {
    const typeMap = {
      welding_machine: '焊接设备',
      cutting_machine: '切割设备',
      grinding_machine: '打磨设备',
      testing_equipment: '检测设备',
      auxiliary_equipment: '辅助设备',
      other: '其他'
    }
    return typeMap[type] || type
  }

  /**
   * 生成设备编号
   */
  generateEquipmentCode(type: EquipmentType, companyId?: string): string {
    const now = new Date()
    const year = now.getFullYear().toString().slice(-2)
    const month = (now.getMonth() + 1).toString().padStart(2, '0')
    const day = now.getDate().toString().padStart(2, '0')

    const typePrefix = {
      welding_machine: 'WM',
      cutting_machine: 'CM',
      grinding_machine: 'GM',
      testing_equipment: 'TE',
      auxiliary_equipment: 'AE',
      other: 'OT'
    }

    const prefix = typePrefix[type] || 'EQ'
    const companySuffix = companyId ? `-${companyId.slice(-4)}` : ''

    return `${prefix}-${year}${month}${day}${companySuffix}`
  }

  /**
   * 验证设备数据
   */
  validateEquipmentData(data: CreateEquipmentData): { isValid: boolean, errors: string[] } {
    const errors: string[] = []

    // 必填字段验证
    if (!data.equipment_code?.trim()) {
      errors.push('设备编号不能为空')
    }
    if (!data.equipment_name?.trim()) {
      errors.push('设备名称不能为空')
    }
    if (!data.equipment_type) {
      errors.push('设备类型不能为空')
    }

    // 格式验证
    if (data.purchase_price && (data.purchase_price < 0 || isNaN(data.purchase_price))) {
      errors.push('采购价格必须是正数')
    }
    if (data.rated_power && (data.rated_power < 0 || isNaN(data.rated_power))) {
      errors.push('额定功率必须是正数')
    }
    if (data.rated_voltage && (data.rated_voltage < 0 || isNaN(data.rated_voltage))) {
      errors.push('额定电压必须是正数')
    }
    if (data.rated_current && (data.rated_current < 0 || isNaN(data.rated_current))) {
      errors.push('额定电流必须是正数')
    }

    // 日期验证
    if (data.purchase_date && !this.isValidDate(data.purchase_date)) {
      errors.push('采购日期格式不正确')
    }
    if (data.warranty_expiry_date && !this.isValidDate(data.warranty_expiry_date)) {
      errors.push('保修到期日期格式不正确')
    }
    if (data.installation_date && !this.isValidDate(data.installation_date)) {
      errors.push('安装日期格式不正确')
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }

  /**
   * 验证日期格式
   */
  private isValidDate(dateString: string): boolean {
    const date = new Date(dateString)
    return date instanceof Date && !isNaN(date.getTime())
  }
}

// 导出单例
export const equipmentService = new EquipmentService()
export default equipmentService