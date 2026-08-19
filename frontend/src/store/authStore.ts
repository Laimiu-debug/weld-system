import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/types'
import { authService } from '@/services/auth'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (data: {
    email: string
    username: string
    password: string
    full_name: string
    phone?: string
  }) => Promise<boolean>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  updateProfile: (data: Partial<User>) => Promise<boolean>
  checkPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  canCreateMore: (recordType: string, currentCount: number) => boolean
  setUser: (user: User) => void
  setLoading: (loading: boolean) => void
  refreshUserInfo: () => Promise<boolean>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      loading: false,

      login: async (email: string, password: string) => {
        console.log('🔐 authStore.login 开始')
        set({ loading: true })
        try {
          const success = await authService.loginWithAccount({
            account: email,
            password: password
          })
          console.log('📊 authService.loginWithAccount 返回:', success)

          if (success) {
            const user = authService.getCurrentUserFromStorage()
            console.log('👤 获取到用户信息:', user)

            // 立即更新状态
            set({ user, isAuthenticated: true, loading: false })
            console.log('✅ authStore 状态已更新: isAuthenticated=true')

            // 登录成功后立即初始化个人工作区
            try {
              const { workspaceService } = await import('@/services/workspace')
              console.log('🏢 开始获取默认工作区（个人工作区）')
              const workspaceResponse = await workspaceService.getDefaultWorkspace()

              if (workspaceResponse && workspaceResponse.data) {
                console.log('✅ 获取到默认工作区:', workspaceResponse.data)
                workspaceService.saveCurrentWorkspaceToStorage(workspaceResponse.data)
                console.log('💾 已保存默认工作区到本地存储')
              } else {
                console.warn('⚠️ 未获取到默认工作区数据')
              }
            } catch (workspaceError) {
              console.error('❌ 获取默认工作区失败:', workspaceError)
              // 工作区初始化失败不影响登录流程
            }

            return true
          }

          console.log('❌ 登录失败')
          set({ loading: false })
          return false
        } catch (error) {
          console.error('❌ Login error:', error)
          set({ loading: false })
          return false
        }
      },

      register: async (data) => {
        set({ loading: true })
        try {
          const success = await authService.register(data)
          // 注册成功后不自动登录，用户需要手动登录
          return success
        } catch (error) {
          console.error('Register error:', error)
          return false
        } finally {
          set({ loading: false })
        }
      },

      logout: async () => {
        set({ loading: true })
        try {
          await authService.logout()
          set({ user: null, isAuthenticated: false })
        } catch (error) {
          console.error('Logout error:', error)
          // 即使API调用失败，也要清除本地状态
          set({ user: null, isAuthenticated: false })
        } finally {
          set({ loading: false })
        }
      },

      refreshToken: async () => {
        try {
          const success = await authService.refreshToken()
          if (!success) {
            set({ user: null, isAuthenticated: false })
            return false
          }

          // 刷新token成功后，重新获取用户信息以更新权限和会员等级
          const updatedUser = await authService.getCurrentUser()
          if (updatedUser) {
            set({ user: updatedUser })
          }

          return success
        } catch (error) {
          console.error('Token refresh error:', error)
          set({ user: null, isAuthenticated: false })
          return false
        }
      },

      updateProfile: async (data) => {
        try {
          const success = await authService.updateProfile(data)
          if (success) {
            const user = authService.getCurrentUserFromStorage()
            set({ user })
          }
          return success
        } catch (error) {
          console.error('Update profile error:', error)
          return false
        }
      },

      checkPermission: (permission: string) => {
        const { user } = get()
        if (!user) return false
        return authService.hasPermission(permission)
      },

      hasAnyPermission: (permissions: string[]) => {
        const { user } = get()
        if (!user) return false
        return authService.hasAnyPermission(permissions)
      },

      canCreateMore: (recordType: string, currentCount: number) => {
        const { user } = get()
        if (!user) return false
        return authService.canCreateMore(recordType, currentCount)
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true })
      },

      setLoading: (loading: boolean) => {
        set({ loading })
      },

      refreshUserInfo: async () => {
        try {
          const updatedUser = await authService.getCurrentUser()
          if (updatedUser) {
            set({ user: updatedUser })
            return true
          }
          return false
        } catch (error) {
          console.error('Refresh user info error:', error)
          return false
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // 添加恢复后的验证逻辑
      onRehydrateStorage: () => (state) => {
        console.log('🔄 Zustand persist 恢复状态')
        if (state) {
          // 验证 localStorage 中是否真的有 token 和 user
          const token = localStorage.getItem('token')
          const userStr = localStorage.getItem('user')

          if (!token || !userStr) {
            console.log('❌ localStorage 中没有 token 或 user，清除认证状态')
            state.user = null
            state.isAuthenticated = false
            // 清除 auth-storage 避免再次恢复错误状态
            localStorage.removeItem('auth-storage')
          } else {
            // 验证 user 数据是否有效
            try {
              const user = JSON.parse(userStr)
              if (!user || !user.id) {
                console.log('❌ user 数据无效，清除认证状态')
                state.user = null
                state.isAuthenticated = false
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                localStorage.removeItem('auth-storage')
              } else {
                console.log('✅ localStorage 验证通过，保持认证状态')
                // 确保 state.user 与 localStorage 中的 user 一致
                state.user = user
                state.isAuthenticated = true
              }
            } catch (error) {
              console.error('❌ 解析 user 数据失败:', error)
              state.user = null
              state.isAuthenticated = false
              localStorage.removeItem('token')
              localStorage.removeItem('user')
              localStorage.removeItem('auth-storage')
            }
          }
        }
      },
    }
  )
)

let authCrossTabBound = false

export function bindAuthCrossTabSync(): void {
  if (authCrossTabBound || typeof window === 'undefined') {
    return
  }
  authCrossTabBound = true
  window.addEventListener('storage', (event: StorageEvent) => {
    if (event.key !== 'token' && event.key !== 'user' && event.key !== 'auth-storage') {
      return
    }
    const token = localStorage.getItem('token')
    const stored = authService.getCurrentUserFromStorage()
    if (!token || !stored) {
      useAuthStore.setState({ user: null, isAuthenticated: false })
      return
    }
    useAuthStore.setState({ user: stored, isAuthenticated: true })
  })
}