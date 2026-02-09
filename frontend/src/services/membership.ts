import { apiService } from './api'

// 订阅计划类型
export interface SubscriptionPlan {
  id: string
  name: string
  description?: string
  monthly_price: number
  quarterly_price: number
  yearly_price: number
  currency: string
  max_wps_files: number
  max_pqr_files: number
  max_ppqr_files: number
  max_materials: number
  max_welders: number
  max_equipment: number
  max_factories: number
  max_employees: number
  features: string[]
  is_recommended: boolean
  sort_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 用户订阅信息
export interface UserSubscription {
  id: number
  user_id: string
  plan_id: string
  status: string
  billing_cycle: string
  price: number
  currency: string
  start_date: string
  end_date: string
  trial_end_date?: string
  auto_renew: boolean
  payment_method: string
  last_payment_date?: string
  next_billing_date?: string
  created_at: string
  updated_at: string
}

// 会员升级请求
export interface MembershipUpgradeRequest {
  plan_id: string
  billing_cycle: 'monthly' | 'quarterly' | 'yearly'
  auto_renew: boolean
  payment_method: string
}

// 会员升级响应
export interface MembershipUpgradeResponse {
  success: boolean
  subscription_id: number
  message: string
  new_plan: string
  next_billing_date: string
  amount_paid: number
}

// 用户会员信息
export interface UserMembershipInfo {
  user_id: string
  email: string
  membership_tier: string
  membership_type: string
  subscription_status: string
  subscription_start_date?: string
  subscription_end_date?: string
  auto_renewal: boolean
  is_inherited_from_company?: boolean  // 是否通过企业继承会员权限
  company_name?: string  // 所属企业名称（如果是继承的）
  features: string[]
  quotas: {
    wps: { used: number; limit: number }
    pqr: { used: number; limit: number }
    ppqr: { used: number; limit: number }
    storage: { used: number; limit: number }
  }
}

// 会员使用统计
export interface MembershipUsage {
  wps: number
  pqr: number
  ppqr: number
  materials: number
  welders: number
  equipment: number
  storage: number
}

class MembershipService {
  // 获取所有订阅计划
  async getSubscriptionPlans(): Promise<SubscriptionPlan[]> {
    const response = await apiService.get<SubscriptionPlan[]>('/members/plans')
    return response.data || []
  }

  // 获取当前用户订阅
  async getCurrentSubscription(): Promise<UserSubscription | null> {
    const response = await apiService.get<UserSubscription>('/members/current')
    return response.data || null
  }

  // 升级会员
  async upgradeMembership(data: MembershipUpgradeRequest): Promise<MembershipUpgradeResponse> {
    const response = await apiService.post<MembershipUpgradeResponse>('/members/upgrade', data)
    return response.data || {
      success: false,
      subscription_id: 0,
      message: "升级失败",
      new_plan: "",
      next_billing_date: "",
      amount_paid: 0
    }
  }

  // 获取订阅历史
  async getSubscriptionHistory(): Promise<UserSubscription[]> {
    const response = await apiService.get<UserSubscription[]>('/members/history')
    return response.data || []
  }

  // 取消订阅
  async cancelSubscription(subscriptionId: number): Promise<{ message: string }> {
    const response = await apiService.post<{ message: string }>(`/members/${subscriptionId}/cancel`)
    return response.data || { message: "取消失败" }
  }

  // 续费订阅
  async renewSubscription(subscriptionId: number): Promise<{
    message: string
    new_end_date: string
    amount_paid: number
  }> {
    const response = await apiService.post<{
      message: string
      new_end_date: string
      amount_paid: number
    }>(`/members/${subscriptionId}/renew`)
    return response.data || {
      message: "续费失败",
      new_end_date: "",
      amount_paid: 0
    }
  }

  // 获取用户会员信息（包含配额使用情况）
  async getUserMembershipInfo(): Promise<UserMembershipInfo | null> {
    const response = await apiService.get<UserMembershipInfo>('/users/me-membership')
    return response.data || null
  }

  // 获取用户使用统计
  async getUserUsageStats(): Promise<MembershipUsage> {
    const response = await apiService.get<MembershipUsage>('/users/me-usage')
    return response.data || {
      wps: 0,
      pqr: 0,
      ppqr: 0,
      materials: 0,
      welders: 0,
      equipment: 0,
      storage: 0
    }
  }

  // 根据工作区确定实际会员等级
  determineWorkspaceMembership(userMembershipType: string, workspaceType: string, workspaceMembershipTier?: string): string {
    // 如果是企业工作区，使用工作区的会员等级
    if (workspaceType === 'enterprise') {
      if (userMembershipType === 'enterprise') {
        // 企业用户在企业工作区：至少企业基础版
        return workspaceMembershipTier || 'enterprise_basic'
      }
      // 非企业用户不应该能访问企业工作区，但为了兼容性返回基础等级
      return 'personal_free'
    }

    // 个人工作区的等级确定
    if (userMembershipType === 'enterprise') {
      // 企业用户在个人工作区：享受个人高级版
      return 'personal_advanced'
    } else if (userMembershipType === 'pro') {
      return 'personal_pro'
    } else if (userMembershipType === 'basic') {
      return 'personal_basic'
    } else {
      return 'personal_free'
    }
  }

  // 获取会员等级显示名称
  getMembershipDisplayName(tier: string): string {
    const tierNames: Record<string, string> = {
      'personal_free': '免费版',
      'personal_basic': '基础版',
      'personal_pro': '专业版',
      'personal_advanced': '高级版',
      'enterprise_basic': '企业基础版',
      'enterprise_pro': '企业专业版',
      'enterprise_advanced': '企业高级版'
    }
    return tierNames[tier] || '未知等级'
  }

  // 获取会员等级颜色
  getMembershipColor(tier: string): string {
    const tierColors: Record<string, string> = {
      'personal_free': '#gray',
      'personal_basic': '#blue',
      'personal_pro': '#purple',
      'personal_advanced': '#gold',
      'enterprise_basic': '#green',
      'enterprise_pro': '#orange',
      'enterprise_advanced': '#red'
    }
    return tierColors[tier] || '#gray'
  }
}

export const membershipService = new MembershipService()
export default membershipService