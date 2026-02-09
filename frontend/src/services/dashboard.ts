/**
 * 仪表盘数据服务
 */
import api from './api'
import { DashboardStats } from '@/types'

export interface RecentActivity {
  type: string
  id: number
  wps_number?: string
  pqr_number?: string
  title: string
  description: string
  status: string
  qualification_date?: string
  created_at: string
  updated_at?: string
}

export interface DashboardStatsResponse {
  success: boolean
  data: DashboardStats
}

export interface RecentActivitiesResponse {
  success: boolean
  data: RecentActivity[]
}

class DashboardService {
  /**
   * 获取仪表盘统计数据
   */
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStatsResponse>('/dashboard/stats')
    // API拦截器已经包装了响应，所以response.data是后端返回的完整响应
    // 后端返回格式: {success: true, data: DashboardStats}
    // 经过拦截器后: {success: true, data: {success: true, data: DashboardStats}}
    // 所以我们需要访问 response.data.data
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      return (response.data as any).data
    }
    return response.data as DashboardStats
  }

  /**
   * 获取最近活动记录
   */
  async getRecentActivities(limit: number = 10): Promise<RecentActivity[]> {
    const response = await api.get<RecentActivitiesResponse>(
      `/dashboard/recent-activities?limit=${limit}`
    )
    // 同样的处理逻辑
    if (response.data && typeof response.data === 'object' && 'data' in response.data) {
      return (response.data as any).data
    }
    return response.data as RecentActivity[]
  }
}

export const dashboardService = new DashboardService()
export default dashboardService

