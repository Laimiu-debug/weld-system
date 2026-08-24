export type ThemeMode = 'light' | 'dark' | 'auto'
export type EmailDigestFrequency = 'immediate' | 'daily' | 'weekly' | 'never'

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
  loginNotifications: boolean
  sessionTimeout: boolean
  autoLogout: boolean
  autoLogoutMinutes: number
  emailNotifications: boolean
  pushNotifications: boolean
  smsNotifications: boolean
  quietHoursEnabled: boolean
  quietHoursStart: string
  quietHoursEnd: string
  systemUpdates: boolean
  securityAlerts: boolean
  maintenance: boolean
  wpsUpdates: boolean
  pqrApprovals: boolean
  qualityAlerts: boolean
  equipmentMaintenance: boolean
  materialAlerts: boolean
  welderCertifications: boolean
  productionDeadlines: boolean
  emailDigestFrequency: EmailDigestFrequency
  aiDataOutboundAuthorized: boolean
  aiDataOutboundNoticeVersion: string
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
  loginNotifications: true,
  sessionTimeout: true,
  autoLogout: false,
  autoLogoutMinutes: 30,
  emailNotifications: true,
  pushNotifications: true,
  smsNotifications: false,
  quietHoursEnabled: false,
  quietHoursStart: '22:00',
  quietHoursEnd: '08:00',
  systemUpdates: true,
  securityAlerts: true,
  maintenance: true,
  wpsUpdates: true,
  pqrApprovals: true,
  qualityAlerts: true,
  equipmentMaintenance: true,
  materialAlerts: true,
  welderCertifications: true,
  productionDeadlines: true,
  emailDigestFrequency: 'immediate',
  aiDataOutboundAuthorized: false,
  aiDataOutboundNoticeVersion: '',
}
