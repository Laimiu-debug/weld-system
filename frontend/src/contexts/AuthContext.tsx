import React, { ReactNode, useEffect } from 'react'
import { User } from '@/types'
import { useAuthStore, bindAuthCrossTabSync } from '@/store/authStore'

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

export interface RegisterData {
  email: string
  password: string
  full_name: string
  phone?: string
  company?: string
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  useEffect(() => {
    bindAuthCrossTabSync()
  }, [])
  return <>{children}</>
}

export const useAuth = (): AuthContextType => {
  const { user, isAuthenticated, loading, login, logout, register, refreshToken } = useAuthStore()
  return {
    user,
    token: typeof window === 'undefined' ? null : localStorage.getItem('token'),
    isLoading: loading,
    isAuthenticated,
    login: async (email, password) => {
      await login(email, password)
    },
    logout: () => {
      void logout()
    },
    register: async (userData) => {
      await register({
        email: userData.email,
        username: userData.email.split('@')[0],
        password: userData.password,
        full_name: userData.full_name,
        phone: userData.phone,
      })
    },
    refreshToken: async () => {
      await refreshToken()
    },
  }
}

export default useAuthStore
