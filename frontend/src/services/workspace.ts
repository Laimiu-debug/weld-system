import { apiService } from './api'
import { ApiResponse } from '@/types'

// 工作区相关类型定义
export interface Workspace {
  type: WorkspaceType
  id: string
  name: string
  description: string
  user_id?: number
  company_id?: number
  factory_id?: number
  factory_name?: string
  is_default?: boolean
  role?: string
  department?: string
  company_role_id?: number
  membership_tier: string
  quota_info: QuotaInfo
  status?: 'active' | 'inactive'
  member_count?: number
  created_at?: string
}

export type WorkspaceType = 'personal' | 'enterprise'

export interface QuotaInfo {
  wps?: {
    used: number
    limit: number
    percentage: number
  }
  pqr?: {
    used: number
    limit: number
    percentage: number
  }
  ppqr?: {
    used: number
    limit: number
    percentage: number
  }
  equipment?: {
    used: number
    limit: number
    percentage: number
  }
  storage?: {
    used: number
    limit: number
    percentage: number
  }
  employees?: {
    used: number
    limit: number
    percentage: number
  }
  factories?: {
    used: number
    limit: number
    percentage: number
  }
}

export interface WorkspaceSwitchRequest {
  workspace_id: string
}

export interface WorkspaceSwitchResponse {
  success: boolean
  message: string
  workspace: Workspace
}

// 工作区服务类
class WorkspaceService {
  // ==================== 工作区基础管理 ====================

  /**
   * 获取用户所有可用的工作区
   */
  async getUserWorkspaces(): Promise<ApiResponse<Workspace[]>> {
    const response = await apiService.get<Workspace[]>('/workspace/workspaces')
    return response
  }

  /**
   * 获取用户的默认工作区
   */
  async getDefaultWorkspace(): Promise<ApiResponse<Workspace>> {
    const response = await apiService.get<Workspace>('/workspace/workspaces/default')
    return response
  }

  /**
   * 切换工作区
   */
  async switchWorkspace(request: WorkspaceSwitchRequest): Promise<ApiResponse<WorkspaceSwitchResponse>> {
    const response = await apiService.post<WorkspaceSwitchResponse>('/workspace/workspaces/switch', request)
    return response
  }

  /**
   * 获取当前工作区信息
   */
  async getCurrentWorkspace(): Promise<ApiResponse<Workspace>> {
    const response = await apiService.get<Workspace>('/workspace/workspaces/current')
    return response
  }

  // ==================== 工作区状态管理 ====================

  /**
   * 从本地存储获取当前工作区
   */
  getCurrentWorkspaceFromStorage(): Workspace | null {
    try {
      const workspaceData = localStorage.getItem('current_workspace')
      return workspaceData ? JSON.parse(workspaceData) : null
    } catch (error) {
      console.error('获取当前工作区失败:', error)
      return null
    }
  }

  /**
   * 保存当前工作区到本地存储
   */
  saveCurrentWorkspaceToStorage(workspace: Workspace): void {
    try {
      localStorage.setItem('current_workspace', JSON.stringify(workspace))
    } catch (error) {
      console.error('保存当前工作区失败:', error)
    }
  }

  /**
   * 清除本地存储的工作区信息
   */
  clearCurrentWorkspaceFromStorage(): void {
    try {
      localStorage.removeItem('current_workspace')
    } catch (error) {
      console.error('清除当前工作区失败:', error)
    }
  }

  // ==================== 工作区工具方法 ====================

  /**
   * 格式化工作区类型显示
   */
  formatWorkspaceType(type: WorkspaceType): { text: string, color: string, icon: string } {
    const typeMap = {
      personal: { text: '个人工作区', color: 'blue', icon: 'user' },
      enterprise: { text: '企业工作区', color: 'green', icon: 'team' }
    }
    return typeMap[type] || { text: type, color: 'default', icon: 'home' }
  }

  /**
   * 格式化会员等级显示
   */
  formatMembershipTier(tier: string): { text: string, color: string } {
    const tierMap = {
      'personal_free': { text: '个人免费版', color: 'default' },
      'personal_pro': { text: '个人专业版', color: 'blue' },
      'personal_advanced': { text: '个人高级版', color: 'purple' },
      'personal_flagship': { text: '个人旗舰版', color: 'gold' },
      'enterprise': { text: '企业版', color: 'green' },
      'enterprise_pro': { text: '企业版PRO', color: 'cyan' },
      'enterprise_pro_max': { text: '企业版PRO MAX', color: 'red' }
    }
    return tierMap[tier as keyof typeof tierMap] || { text: tier, color: 'default' }
  }

  /**
   * 格式化角色显示
   */
  formatRole(role?: string): { text: string, color: string } {
    if (!role) return { text: '普通员工', color: 'default' }

    const roleMap = {
      'admin': { text: '管理员', color: 'red' },
      'manager': { text: '经理', color: 'orange' },
      'employee': { text: '员工', color: 'blue' }
    }
    return roleMap[role as keyof typeof roleMap] || { text: role, color: 'default' }
  }

  /**
   * 检查工作区是否支持指定功能
   */
  isFeatureSupported(workspace: Workspace, feature: string): boolean {
    // 个人工作区免费版不支持的功能
    if (workspace.type === 'personal' && workspace.membership_tier === 'personal_free') {
      const restrictedFeatures = ['equipment', 'enterprise', 'multi_factory']
      return !restrictedFeatures.includes(feature)
    }

    // 企业工作区支持所有功能
    if (workspace.type === 'enterprise') {
      return true
    }

    // 个人工作区付费版支持的功能
    const paidFeatures = ['wps', 'pqr', 'ppqr', 'storage']
    return paidFeatures.includes(feature)
  }

  /**
   * 检查配额使用情况
   */
  checkQuotaUsage(workspace: Workspace, quotaType: string): {
    used: number
    limit: number
    percentage: number
    isNearLimit: boolean
    isOverLimit: boolean
    status: 'available' | 'warning' | 'full' | 'over'
  } {
    const quota = workspace.quota_info[quotaType as keyof QuotaInfo]

    if (!quota) {
      return {
        used: 0,
        limit: 0,
        percentage: 0,
        isNearLimit: false,
        isOverLimit: false,
        status: 'available' as const
      }
    }

    const isNearLimit = quota.percentage >= 80
    const isOverLimit = quota.percentage >= 100

    let status: 'available' | 'warning' | 'full' | 'over' = 'available'
    if (isOverLimit) status = 'over'
    else if (quota.percentage >= 95) status = 'full'
    else if (isNearLimit) status = 'warning'

    return {
      used: quota.used,
      limit: quota.limit,
      percentage: quota.percentage,
      isNearLimit,
      isOverLimit,
      status
    }
  }

  /**
   * 获取工作区显示名称
   */
  getWorkspaceDisplayName(workspace: Workspace): string {
    if (workspace.type === 'personal') {
      return '个人工作区'
    }

    if (workspace.factory_name) {
      return `${workspace.name} - ${workspace.factory_name}`
    }

    return workspace.name
  }

  /**
   * 获取工作区完整描述
   */
  getWorkspaceDescription(workspace: Workspace): string {
    const typeInfo = this.formatWorkspaceType(workspace.type)
    const tierInfo = this.formatMembershipTier(workspace.membership_tier)

    let description = `${typeInfo.text} | ${tierInfo.text}`

    if (workspace.type === 'enterprise' && workspace.factory_name) {
      description += ` | ${workspace.factory_name}`
    }

    if (workspace.role) {
      const roleInfo = this.formatRole(workspace.role)
      description += ` | ${roleInfo.text}`
    }

    return description
  }

  /**
   * 验证工作区切换权限
   */
  canSwitchToWorkspace(workspace: Workspace): { allowed: boolean, reason?: string } {
    // 检查工作区是否激活
    if (workspace.status && workspace.status !== 'active') {
      return { allowed: false, reason: '工作区未激活' }
    }

    // 检查用户是否有权限访问该工作区
    if (workspace.type === 'enterprise' && !workspace.role) {
      return { allowed: false, reason: '您没有权限访问此企业工作区' }
    }

    return { allowed: true }
  }

  /**
   * 生成工作区切换提示
   */
  getSwitchWorkspaceMessage(fromWorkspace: Workspace, toWorkspace: Workspace): string {
    const fromName = this.getWorkspaceDisplayName(fromWorkspace)
    const toName = this.getWorkspaceDisplayName(toWorkspace)

    return `确定要从 ${fromName} 切换到 ${toName} 吗？切换后您将看到不同工作区的数据。`
  }
}

// 导出单例
export const workspaceService = new WorkspaceService()
export default workspaceService
