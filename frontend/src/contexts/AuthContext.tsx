import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { message } from 'antd'
import axios from 'axios'

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// 用户类型定义
export interface User {
  id: number
  email: string
  full_name: string
  phone?: string
  company?: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  member_tier: string
  created_at: string
  updated_at: string
}

// 认证上下文类型定义
interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (userData: RegisterData) => Promise<void>
  refreshToken: () => Promise<void>
}

// 注册数据类型
export interface RegisterData {
  email: string
  password: string
  full_name: string
  phone?: string
  company?: string
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// 认证提供者组件
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 从localStorage恢复认证状态
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser)
        setToken(storedToken)
        setUser(userData)

        // 设置axios默认headers
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
      } catch (error) {
        console.error('Error parsing stored user data:', error)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }

    setIsLoading(false)
  }, [])

  // 登录函数
  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true)

    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await axios.post(`${API_BASE_URL}/auth/login`, formData)

      const { access_token, token_type, expires_in } = response.data

      // 获取用户信息
      const userResponse = await axios.get(`${API_BASE_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${access_token}`
        }
      })

      const userData = userResponse.data

      // 保存到状态和localStorage
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))

      // 设置axios默认headers
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      message.success('登录成功！')
    } catch (error: any) {
      console.error('Login error:', error)

      if (error.response?.data?.detail) {
        const errorMsg = error.response.data.detail
        if (errorMsg.includes('密码') || errorMsg.includes('password')) {
          message.error('密码错误，请重新输入')
        } else if (errorMsg.includes('邮箱') || errorMsg.includes('email')) {
          message.error('用户不存在，请先注册')
        } else if (errorMsg.includes('disabled') || errorMsg.includes('禁用')) {
          message.error('账户已被禁用，请联系管理员')
        } else if (errorMsg.includes('verified') || errorMsg.includes('验证')) {
          message.error('请先验证邮箱地址')
        } else {
          message.error(`登录失败: ${errorMsg}`)
        }
      } else {
        message.error('网络错误，请检查网络连接')
      }

      throw error
    } finally {
      setIsLoading(false)
    }
  }

  // 注册函数
  const register = async (userData: RegisterData): Promise<void> => {
    setIsLoading(true)

    try {
      await axios.post(`${API_BASE_URL}/auth/register`, userData)
      message.success('注册成功！请登录您的账户')
    } catch (error: any) {
      console.error('Registration error:', error)

      if (error.response?.data?.detail) {
        const errorMsg = error.response.data.detail

        if (typeof errorMsg === 'string') {
          if (errorMsg.includes('邮箱') || errorMsg.includes('email')) {
            message.error('邮箱已存在，请使用其他邮箱')
          } else if (errorMsg.includes('密码') || errorMsg.includes('password')) {
            message.error('密码格式不符合要求')
          } else if (errorMsg === 'Internal server error') {
            message.error('服务器错误，请稍后重试')
          } else {
            message.error(`注册失败: ${errorMsg}`)
          }
        } else {
          message.error('注册失败，请检查输入信息')
        }
      } else {
        message.error('网络错误，请检查网络连接')
      }

      throw error
    } finally {
      setIsLoading(false)
    }
  }

  // 登出函数
  const logout = async (): Promise<void> => {
    try {
      // 调用后端登出接口（如果存在）
      if (token) {
        try {
          await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })
        } catch (error) {
          console.log('Logout API call failed:', error)
          // 即使API调用失败，也要清除本地状态
        }
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // 清除状态和localStorage
      setUser(null)
      setToken(null)
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      // 清除axios headers
      delete axios.defaults.headers.common['Authorization']

      message.success('已成功退出登录')
    }
  }

  // 刷新token函数
  const refreshToken = async (): Promise<void> => {
    if (!token) return

    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      const { access_token } = response.data
      setToken(access_token)
      localStorage.setItem('token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      // 获取最新的用户信息
      const userResponse = await axios.get(`${API_BASE_URL}/users/me`)
      const userData = userResponse.data
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Token refresh failed:', error)
      // 如果刷新失败，清除认证状态
      logout()
    }
  }

  // 计算是否已认证
  const isAuthenticated = !!user && !!token

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    register,
    refreshToken
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext