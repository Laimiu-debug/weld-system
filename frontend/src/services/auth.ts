import { apiService } from './api'
import { User, ApiResponse } from '@/types'

export interface LoginCredentials {
  email: string  // Keep as email for compatibility with existing code
  password: string
}

export interface LoginRequest {
  account: string  // Can be email or phone
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name: string
  phone?: string
  invite_token?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface PasswordResetData {
  email: string
}

export interface PasswordResetConfirmData {
  token: string
  new_password: string
  confirm_password: string
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface VerificationCodeLoginRequest {
  account: string
  verification_code: string
  account_type: 'email' | 'phone'
}

class AuthService {
  private readonly TOKEN_KEY = 'token'
  private readonly REFRESH_TOKEN_KEY = 'refresh_token'
  private readonly USER_KEY = 'user'

  // 登录（兼容旧接口）
  async login(credentials: LoginCredentials): Promise<boolean> {
    return this.loginWithAccount({
      account: credentials.email,
      password: credentials.password,
    })
  }

  // 支持邮箱/手机号的新登录方法
  async loginWithAccount(loginData: LoginRequest): Promise<boolean> {
    try {
      console.log('🔐 开始登录流程，账号:', loginData.account)

      console.log('🌐 调用真实API登录')
      // 调用真实的API
      const response = await apiService.post<AuthResponse>('/auth/login-json', loginData)

      console.log('📦 API响应:', response)

      // API响应被拦截器包装成 {success: true, data: {...}}
      // 需要从 response.data 中提取实际数据
      let authData: AuthResponse | null = null

      if (response.success && response.data) {
        // 如果data中包含access_token，说明data就是AuthResponse
        if ((response.data as any).access_token) {
          authData = response.data as AuthResponse
        }
      } else if ((response as any).access_token) {
        // 如果response直接包含access_token
        authData = response as any as AuthResponse
      }

      if (authData && authData.access_token) {
        console.log('✅ API登录成功，保存认证信息')
        const { access_token, refresh_token, user } = authData

        // 存储token和用户信息
        localStorage.setItem(this.TOKEN_KEY, access_token)
        localStorage.setItem(this.REFRESH_TOKEN_KEY, refresh_token)
        localStorage.setItem(this.USER_KEY, JSON.stringify(user))

        console.log('✅ 认证信息已保存到localStorage')
        return true
      }

      console.error('❌ 登录失败：响应数据格式不正确', response)
      return false
    } catch (error) {
      console.error('❌ 登录异常:', error)
      return false
    }
  }

  // 验证码登录
  async loginWithVerificationCode(loginData: VerificationCodeLoginRequest): Promise<boolean> {
    try {
      console.log('🔐 开始验证码登录流程，账号:', loginData.account)

      // 调用验证码登录API
      const response = await apiService.post<AuthResponse>('/auth/login-with-verification-code', loginData)

      console.log('📦 验证码登录API响应:', response)

      // 提取认证数据
      let authData: AuthResponse | null = null

      if (response.success && response.data) {
        if ((response.data as any).access_token) {
          authData = response.data as AuthResponse
        }
      } else if ((response as any).access_token) {
        authData = response as any as AuthResponse
      }

      if (authData && authData.access_token) {
        console.log('✅ 验证码登录成功，保存认证信息')
        const { access_token, refresh_token, user } = authData

        // 存储token和用户信息
        localStorage.setItem(this.TOKEN_KEY, access_token)
        localStorage.setItem(this.REFRESH_TOKEN_KEY, refresh_token)
        localStorage.setItem(this.USER_KEY, JSON.stringify(user))

        console.log('✅ 认证信息已保存到localStorage')
        return true
      }

      console.error('❌ 验证码登录失败：响应数据格式不正确', response)
      return false
    } catch (error) {
      console.error('❌ 验证码登录异常:', error)
      return false
    }
  }

  // 注册
  async register(data: RegisterData): Promise<boolean> {
    try {
      console.log('🚀 开始注册流程，数据:', data)

      // 修复字段映射，使用正确的API格式
      const registerData = {
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        phone: data.phone,
        username: data.username,
        invite_token: data.invite_token,
      }

      console.log('📤 发送注册请求:', registerData)
      const response = await apiService.post<any>('/auth/register', registerData)
      console.log('📥 注册响应:', response)

      // API服务已经将响应包装成 {success: true, data: {...}}
      // 后端实际返回：{message: '注册成功'}
      // 经过拦截器后：{success: true, data: {message: '注册成功'}}
      if (response.success && String(response.data?.message || '').includes('注册成功')) {
        console.log('✅ 注册成功')
        return true
      }

      console.warn('⚠️ 注册响应格式不符合预期:', response)
      return false
    } catch (error: any) {
      console.error('❌ 注册异常:', error)

      // 显示具体的错误信息
      if (error.response?.data?.detail) {
        const errorMsg = error.response.data.detail
        console.log('注册失败的具体原因:', errorMsg)

        // 这里可以返回错误信息让注册页面显示
        throw new Error(errorMsg)
      } else if (error.response?.data) {
        console.log('注册失败响应数据:', error.response.data)
        throw new Error('注册失败，请检查输入信息')
      } else {
        throw new Error('网络错误，请检查网络连接')
      }
    }
  }

  // 登出
  async logout(): Promise<void> {
    try {
      await apiService.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 无论API调用是否成功，都清除本地存储
      this.clearAuthData()
    }
  }

  // 刷新token
  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY)
      if (!refreshToken) {
        return false
      }

      const response = await apiService.post<{ access_token: string }>('/auth/refresh', {
        refresh_token: refreshToken,
      })

      if (response.success && response.data) {
        localStorage.setItem(this.TOKEN_KEY, response.data.access_token)
        return true
      }

      return false
    } catch (error) {
      console.error('Token refresh error:', error)
      this.clearAuthData()
      return false
    }
  }

  // 忘记密码
  async forgotPassword(data: PasswordResetData): Promise<boolean> {
    try {
      const response = await apiService.post('/auth/forgot-password', data)
      return response.success
    } catch (error) {
      console.error('Forgot password error:', error)
      return false
    }
  }

  // 重置密码
  async resetPassword(data: PasswordResetConfirmData): Promise<boolean> {
    try {
      const response = await apiService.post('/auth/reset-password', data)
      return response.success
    } catch (error) {
      console.error('Reset password error:', error)
      return false
    }
  }

  // 修改密码
  async changePassword(data: ChangePasswordData): Promise<boolean> {
    try {
      const response = await apiService.post('/auth/change-password', data)
      return !!response.success
    } catch (error: any) {
      console.error('Change password error:', error)
      const detail = error?.response?.data?.detail
      if (detail && typeof detail === 'object' && detail.message) {
        throw new Error(detail.message)
      }
      if (typeof detail === 'string') {
        throw new Error(detail)
      }
      throw error
    }
  }

  // 验证邮箱
  async verifyEmail(token: string): Promise<boolean> {
    try {
      const response = await apiService.post('/auth/verify-email', { token })
      return response.success
    } catch (error) {
      console.error('Email verification error:', error)
      return false
    }
  }

  // 重新发送验证邮件
  async resendVerificationEmail(email: string): Promise<boolean> {
    try {
      const response = await apiService.post('/auth/resend-verification', { email })
      return response.success
    } catch (error) {
      console.error('Resend verification error:', error)
      return false
    }
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await apiService.get<User>('/users/me')

      if (response.success && response.data) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(response.data))
        return response.data
      }

      return null
    } catch (error) {
      console.error('Get current user error:', error)
      return null
    }
  }

  // 更新用户信息
  async updateProfile(data: Partial<User>): Promise<boolean> {
    try {
      const response = await apiService.put<User>('/users/me', data)

      if (response.success && response.data) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(response.data))
        return true
      }

      return false
    } catch (error) {
      console.error('Update profile error:', error)
      return false
    }
  }

  // 检查是否已认证
  isAuthenticated(): boolean {
    const token = localStorage.getItem(this.TOKEN_KEY)
    return !!token
  }

  // 获取当前用户信息（从本地存储）
  getCurrentUserFromStorage(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY)
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch (error) {
        console.error('Parse user info error:', error)
        this.clearAuthData()
      }
    }
    return null
  }

  // 获取访问token
  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY)
  }

  // 获取刷新token
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  // 清除认证数据
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
    localStorage.removeItem(this.USER_KEY)
  }

  // 检查用户权限
  hasPermission(permission: string): boolean {
    const user = this.getCurrentUserFromStorage()
    if (!user) {
      return false
    }

    // 管理员拥有所有权限
    if (user.is_admin) {
      return true
    }

    // 企业管理权限需要特殊处理
    const enterprisePermissions = [
      'enterprise.employees',
      'enterprise.factories',
      'enterprise.departments',
      'enterprise.roles',
      'enterprise.invitations',
    ]

    if (enterprisePermissions.includes(permission)) {
      // 检查是否是企业会员
      const membershipTier = (user as any).member_tier || user.membership_tier || 'personal_free'
      const isEnterpriseMember = membershipTier.startsWith('enterprise')

      if (!isEnterpriseMember) {
        return false
      }

      // 检查用户权限 - 如果有平台级别的企业管理权限，直接允许
      // 这些权限通常授予企业所有者
      if (user.permissions) {
        let permissions: any = user.permissions
        if (typeof permissions === 'string') {
          try {
            permissions = JSON.parse(permissions)
          } catch (error) {
            console.error('Failed to parse permissions:', error)
            permissions = {}
          }
        }

        // 检查平台级别的企业管理权限（企业所有者拥有）
        const platformPermissionMap: Record<string, string> = {
          'enterprise.employees': 'employee_management',
          'enterprise.factories': 'multi_factory_management',
          'enterprise.departments': 'multi_factory_management',
          'enterprise.roles': 'employee_management',
          'enterprise.invitations': 'employee_management',
        }

        const platformField = platformPermissionMap[permission]
        if (platformField && permissions[platformField] === true) {
          // 企业所有者有平台级别的权限
          return true
        }

        // 检查企业角色权限（普通员工）
        const rolePermissionMap: Record<string, string> = {
          'enterprise.employees': 'employee_management',
          'enterprise.factories': 'factory_management',
          'enterprise.departments': 'department_management',
          'enterprise.roles': 'role_management',
          'enterprise.invitations': 'employee_management',
        }

        const roleField = rolePermissionMap[permission]
        if (roleField && permissions[roleField]) {
          // 检查是否有view权限
          if (typeof permissions[roleField] === 'object' && permissions[roleField].view === true) {
            return true
          }
        }
      }

      // 没有企业管理权限
      return false
    }

    // 非企业管理权限的处理
    // 如果用户有明确的权限字段，使用权限字段（企业内部权限）
    // 注意：只有当permissions字段存在且不为空时才使用企业权限检查
    const rawPermissions = user.permissions as unknown
    if (rawPermissions && rawPermissions !== '' && rawPermissions !== '{}') {
      // 处理权限字段可能是字符串的情况
      let permissions: any = rawPermissions
      if (typeof permissions === 'string') {
        try {
          permissions = JSON.parse(permissions)
        } catch (error) {
          console.error('Failed to parse permissions:', error)
          permissions = {}
        }
      }

      // 检查解析后的permissions对象是否为空
      if (Object.keys(permissions).length === 0) {
        // 如果permissions为空对象，使用会员等级权限
        const membershipTier = (user as any).member_tier || user.membership_tier || 'personal_free'
        return this.checkMembershipPermission(membershipTier, permission)
      }

      // 将权限名称转换为对应的权限字段
      const permissionFieldMap: Record<string, string> = {
        'wps.read': 'wps_management',
        'wps.create': 'wps_management',
        'wps.update': 'wps_management',
        'wps.delete': 'wps_management',
        'pqr.read': 'pqr_management',
        'pqr.create': 'pqr_management',
        'pqr.update': 'pqr_management',
        'pqr.delete': 'pqr_management',
        'ppqr.read': 'ppqr_management',
        'ppqr.create': 'ppqr_management',
        'ppqr.update': 'ppqr_management',
        'ppqr.delete': 'ppqr_management',
        'materials.read': 'materials_management',
        'materials.create': 'materials_management',
        'materials.update': 'materials_management',
        'materials.delete': 'materials_management',
        'welders.read': 'welders_management',
        'welders.create': 'welders_management',
        'welders.update': 'welders_management',
        'welders.delete': 'welders_management',
        'equipment.read': 'equipment_management',
        'equipment.create': 'equipment_management',
        'equipment.update': 'equipment_management',
        'equipment.delete': 'equipment_management',
        'production.read': 'production_management',
        'production.create': 'production_management',
        'production.update': 'production_management',
        'production.delete': 'production_management',
        'quality.read': 'quality_management',
        'quality.create': 'quality_management',
        'quality.update': 'quality_management',
        'quality.delete': 'quality_management',
        'employees.read': 'employee_management',
        'employees.create': 'employee_management',
        'employees.update': 'employee_management',
        'employees.delete': 'employee_management',
        'factories.read': 'multi_factory_management',
        'factories.create': 'multi_factory_management',
        'factories.update': 'multi_factory_management',
        'factories.delete': 'multi_factory_management',
        'reports.read': 'reports_management',
        'reports.create': 'reports_management',
        'reports.update': 'reports_management',
        'reports.delete': 'reports_management',
        'api.access': 'api_access',
      }

      const field = permissionFieldMap[permission]
      return field ? !!permissions[field] : false
    }

    // 如果没有权限字段，根据会员等级检查权限（平台等级权限）
    // 处理字段名不匹配：API返回member_tier，但TypeScript类型使用membership_tier
    const membershipTier = (user as any).member_tier || user.membership_tier || 'personal_free'

    // 根据会员等级检查权限
    return this.checkMembershipPermission(membershipTier, permission)
  }

  // 检查是否有任一权限
  hasAnyPermission(permissions: string[]): boolean {
    return permissions.some(permission => this.hasPermission(permission))
  }

  // 检查会员权限
  private checkMembershipPermission(tier: string, permission: string): boolean {
    const permissionMap: Record<string, string[]> = {
      free: ['wps.read', 'wps.create', 'wps.update', 'wps.delete', 'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete'], // 个人免费版：WPS、PQR增删改查
      personal_pro: [
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
      ],
      personal_advanced: [
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
        'equipment.read', 'equipment.create', 'equipment.update', 'equipment.delete',
        'production.read', 'production.create', 'production.update', 'production.delete',
        'quality.read', 'quality.create', 'quality.update', 'quality.delete',
      ],
      personal_flagship: [
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
        'equipment.read', 'equipment.create', 'equipment.update', 'equipment.delete',
        'production.read', 'production.create', 'production.update', 'production.delete',
        'quality.read', 'quality.create', 'quality.update', 'quality.delete',
        'reports.read', 'reports.create', 'reports.update', 'reports.delete',
      ],
      enterprise: [
        // 企业版包含个人旗舰版所有权限
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
        'equipment.read', 'equipment.create', 'equipment.update', 'equipment.delete',
        'production.read', 'production.create', 'production.update', 'production.delete',
        'quality.read', 'quality.create', 'quality.update', 'quality.delete',
        'reports.read', 'reports.create', 'reports.update', 'reports.delete',
        'employees.read', 'employees.create', 'employees.update', 'employees.delete',
        // 注意：enterprise.* 权限由企业角色控制，不在平台会员权限中
        'factories.read', 'factories.create', 'factories.update', 'factories.delete',
      ],
      enterprise_pro: [
        // 企业PRO版 - 包含企业版所有权限
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
        'equipment.read', 'equipment.create', 'equipment.update', 'equipment.delete',
        'production.read', 'production.create', 'production.update', 'production.delete',
        'quality.read', 'quality.create', 'quality.update', 'quality.delete',
        'reports.read', 'reports.create', 'reports.update', 'reports.delete',
        'employees.read', 'employees.create', 'employees.update', 'employees.delete',
        // 注意：enterprise.* 权限由企业角色控制，不在平台会员权限中
        'factories.read', 'factories.create', 'factories.update', 'factories.delete',
      ],
      enterprise_pro_max: [
        // 企业PRO MAX版 - 包含企业PRO版所有权限
        'wps.read', 'wps.create', 'wps.update', 'wps.delete',
        'pqr.read', 'pqr.create', 'pqr.update', 'pqr.delete',
        'ppqr.read', 'ppqr.create', 'ppqr.update', 'ppqr.delete',
        'materials.read', 'materials.create', 'materials.update', 'materials.delete',
        'welders.read', 'welders.create', 'welders.update', 'welders.delete',
        'equipment.read', 'equipment.create', 'equipment.update', 'equipment.delete',
        'production.read', 'production.create', 'production.update', 'production.update', 'production.delete',
        'quality.read', 'quality.create', 'quality.update', 'quality.delete',
        'reports.read', 'reports.create', 'reports.update', 'reports.delete',
        'employees.read', 'employees.create', 'employees.update', 'employees.delete',
        // 注意：enterprise.* 权限由企业角色控制，不在平台会员权限中
        'factories.read', 'factories.create', 'factories.update', 'factories.delete',
      ],
    }

    const tierPermissions = permissionMap[tier] || []
    return tierPermissions.includes(permission)
  }

  // 检查是否可以创建更多记录
  canCreateMore(recordType: string, currentCount: number): boolean {
    const user = this.getCurrentUserFromStorage()
    if (!user) return false

    const limits: Record<string, Record<string, number>> = {
      free: {
        wps: 10,
        pqr: 10,
        ppqr: 0,
        materials: 0,
        welders: 0,
        equipment: 0,
      },
      personal_pro: {
        wps: 30,
        pqr: 30,
        ppqr: 30,
        materials: 50,
        welders: 20,
        equipment: 0,
      },
      personal_advanced: {
        wps: 50,
        pqr: 50,
        ppqr: 50,
        materials: 100,
        welders: 50,
        equipment: 20,
      },
      personal_flagship: {
        wps: 100,
        pqr: 100,
        ppqr: 100,
        materials: 200,
        welders: 100,
        equipment: 50,
      },
      enterprise: {
        wps: 200,
        pqr: 200,
        ppqr: 200,
        materials: 500,
        welders: 200,
        equipment: 100,
      },
      enterprise_pro: {
        wps: 400,
        pqr: 400,
        ppqr: 400,
        materials: 1000,
        welders: 500,
        equipment: 200,
      },
      enterprise_pro_max: {
        wps: 500,
        pqr: 500,
        ppqr: 500,
        materials: 2000,
        welders: 1000,
        equipment: 500,
      },
    }

    // 处理字段名不匹配：API返回member_tier，但TypeScript类型使用membership_tier
    const membershipTier = (user as any).member_tier || user.membership_tier || 'free'
    const userLimits = limits[membershipTier] || limits.free
    const limit = userLimits[recordType] || 0

    return limit === -1 || currentCount < limit // -1表示无限制
  }
}

export const authService = new AuthService()
export default authService
