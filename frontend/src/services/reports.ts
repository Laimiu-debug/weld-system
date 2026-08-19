import api from './api'

export interface ReportStatistics {
  wps: { total: number; approved: number; pending: number; rejected: number }
  pqr: { total: number; completed: number; in_progress: number }
  ppqr: { total: number; converted: number }
  quality: { total: number; passed: number; failed: number; pass_rate: number }
  production: { total: number; completed: number; in_progress: number; overdue: number }
  materials: { total: number; low_stock: number; out_of_stock: number }
  welders: { total: number }
  equipment: { total: number }
}

class ReportsService {
  async getCatalog() {
    return api.get('/reports/')
  }

  async getStatistics(startDate?: string, endDate?: string) {
    const params: Record<string, string> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get('/reports/statistics', { params })
  }
}

const reportsService = new ReportsService()
export default reportsService
