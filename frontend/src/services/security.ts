import { apiService } from './api'

export interface LoginHistoryItem {
  id: number
  time?: string | null
  ip?: string | null
  device?: string | null
  status: 'success' | 'failed' | string
  message?: string | null
}

export interface SecurityOverview {
  email?: string | null
  phone?: string | null
  is_verified: boolean
  last_login_at?: string | null
  last_login_ip?: string | null
  loginNotifications: boolean
  sessionTimeout: boolean
  autoLogout: boolean
  autoLogoutMinutes: number
  recent_logins: LoginHistoryItem[]
  security_score: number
}

export interface SecuritySettingsUpdate {
  loginNotifications?: boolean
  sessionTimeout?: boolean
  autoLogout?: boolean
  autoLogoutMinutes?: number
}

export interface PhoneBindSendCodePayload {
  phone: string
}

export interface PhoneBindConfirmPayload {
  phone: string
  verification_code: string
  current_password?: string
}

export const securityService = {
  async getOverview(): Promise<SecurityOverview> {
    const response = await apiService.get<SecurityOverview>('/users/me/security')
    return response.data
  },

  async updateSettings(payload: SecuritySettingsUpdate): Promise<SecurityOverview> {
    const response = await apiService.put<SecurityOverview>('/users/me/security', payload)
    return response.data
  },

  async sendPhoneBindCode(payload: PhoneBindSendCodePayload): Promise<{ message: string; expires_in?: number }> {
    const response = await apiService.post<{ message: string; expires_in?: number }>(
      '/users/me/phone/send-code',
      payload
    )
    return response.data
  },

  async bindPhone(payload: PhoneBindConfirmPayload): Promise<void> {
    await apiService.post('/users/me/phone/bind', payload)
  },
}
