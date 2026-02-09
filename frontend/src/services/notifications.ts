import api from './api'

export interface Notification {
  id: number
  title: string
  content: string
  type: 'info' | 'warning' | 'error' | 'success' | 'maintenance'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  is_read: boolean
  is_pinned: boolean
  publish_at: string | null
  expire_at: string | null
  read_at: string | null
  created_at: string | null
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  page: number
  page_size: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
  total_count: number
}

/**
 * 获取通知列表
 */
export const getNotifications = async (params?: {
  unread_only?: boolean
  page?: number
  page_size?: number
}): Promise<NotificationListResponse> => {
  const response = await api.get('/notifications/', { params })
  return response.data.data
}

/**
 * 获取未读通知数量
 */
export const getUnreadCount = async (): Promise<UnreadCountResponse> => {
  const response = await api.get('/notifications/unread-count')
  return response.data.data
}

/**
 * 标记通知为已读
 */
export const markAsRead = async (notificationId: number): Promise<void> => {
  await api.post(`/notifications/${notificationId}/mark-read`)
}

/**
 * 标记所有通知为已读
 */
export const markAllAsRead = async (): Promise<void> => {
  await api.post('/notifications/mark-all-read')
}

/**
 * 删除通知
 */
export const deleteNotification = async (notificationId: number): Promise<void> => {
  await api.delete(`/notifications/${notificationId}`)
}

export default {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
}

