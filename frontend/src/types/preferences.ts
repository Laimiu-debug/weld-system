export type ThemeMode = 'light' | 'dark' | 'auto'

export interface UserSystemPreferences {
  language: string
  timezone: string
  dateFormat: string
  timeFormat: string
  theme: ThemeMode
  primaryColor: string
  compactMode: boolean
  sidebarCollapsed: boolean
  workDays: string[]
  workStartTime: string
  workEndTime: string
  autoSave: boolean
  autoSaveInterval: number
  notificationSound: boolean
  desktopNotifications: boolean
  pageSize: number
  decimalPlaces: number
  currency: string
  measurementUnit: string
}

export const DEFAULT_SYSTEM_PREFERENCES: UserSystemPreferences = {
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  dateFormat: 'YYYY-MM-DD',
  timeFormat: 'HH:mm:ss',
  theme: 'light',
  primaryColor: '#1F5EFF',
  compactMode: false,
  sidebarCollapsed: false,
  workDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
  workStartTime: '09:00',
  workEndTime: '18:00',
  autoSave: true,
  autoSaveInterval: 30,
  notificationSound: true,
  desktopNotifications: true,
  pageSize: 20,
  decimalPlaces: 2,
  currency: 'CNY',
  measurementUnit: 'metric',
}
