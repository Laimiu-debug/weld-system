import { apiService } from './api'

export interface UserFeedbackItem {
  id: number
  title: string
  content: string
  contact?: string | null
  is_read: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface FeedbackListResponse {
  items: UserFeedbackItem[]
  total: number
  page: number
  page_size: number
}

export async function submitFeedback(data: {
  title: string
  content: string
  contact?: string
}): Promise<UserFeedbackItem> {
  const response = await apiService.post<{ data: UserFeedbackItem } | UserFeedbackItem>(
    '/feedback',
    data
  )
  const payload = response.data as any
  return (payload?.data || payload) as UserFeedbackItem
}

export async function listMyFeedback(params?: {
  page?: number
  page_size?: number
}): Promise<FeedbackListResponse> {
  const response = await apiService.get('/feedback/mine', { params })
  const payload = (response.data as any)?.data || response.data
  return {
    items: payload?.items || [],
    total: payload?.total || 0,
    page: payload?.page || 1,
    page_size: payload?.page_size || 20,
  }
}
