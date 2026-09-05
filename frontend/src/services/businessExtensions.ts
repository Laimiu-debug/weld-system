/**
 * MVP business extensions API (plans / standards / performances / report templates)
 */
import { apiService } from './api'

export type WorkspaceQuery = {
  workspace_type: string
  company_id?: number
  factory_id?: number
  skip?: number
  limit?: number
  search?: string
  status?: string
  overdue?: boolean
}

function qs(params: Record<string, unknown>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  })
  const s = search.toString()
  return s ? `?${s}` : ''
}

function unwrap<T>(response: any): T {
  // apiService interceptor wraps axios body as { success, data: body }
  let body = response
  if (response?.success === false) throw new Error(response.message || '操作失败')
  if (response?.success !== undefined && response?.data !== undefined) {
    body = response.data
    if (body?.success === false) throw new Error(body.message || '操作失败')
  }
  if (body?.success !== undefined && body?.data !== undefined) {
    return body.data as T
  }
  return body as T
}

async function listResource<T>(path: string, params: WorkspaceQuery) {
  const response = await apiService.get(`${path}${qs(params as Record<string, unknown>)}`)
  return unwrap<{ items: T[]; total: number; page: number; page_size: number }>(response)
}

async function createResource<T>(path: string, params: WorkspaceQuery, payload: Record<string, unknown>) {
  const { skip, limit, search, status, ...ws } = params
  const response = await apiService.post(`${path}${qs(ws as Record<string, unknown>)}`, payload)
  return unwrap<T>(response)
}

async function updateResource<T>(
  path: string,
  id: number,
  params: WorkspaceQuery,
  payload: Record<string, unknown>
) {
  const { skip, limit, search, status, ...ws } = params
  const response = await apiService.put(`${path}/${id}${qs(ws as Record<string, unknown>)}`, payload)
  return unwrap<T>(response)
}

async function deleteResource(path: string, id: number, params: WorkspaceQuery) {
  const { skip, limit, search, status, ...ws } = params
  await apiService.delete(`${path}/${id}${qs(ws as Record<string, unknown>)}`)
}

export const productionPlanApi = {
  taskOptions: async (p: WorkspaceQuery, planId: number, search?: string) => unwrap<any[]>(await apiService.get(`/production/plan-task-options${qs({ ...p, plan_id: planId, search })}`)),
  setTasks: async (p: WorkspaceQuery, id: number, task_ids: number[]) => unwrap<any>(await apiService.put(`/production/plans/${id}/tasks${qs(p)}`, { task_ids })),
  list: (p: WorkspaceQuery) => listResource<any>('/production/plans', p),
  create: (p: WorkspaceQuery, body: Record<string, unknown>) =>
    createResource<any>('/production/plans', p, body),
  update: (p: WorkspaceQuery, id: number, body: Record<string, unknown>) =>
    updateResource<any>('/production/plans', id, p, body),
  remove: (p: WorkspaceQuery, id: number) => deleteResource('/production/plans', id, p),
}

export const qualityStandardApi = {
  list: (p: WorkspaceQuery) => listResource<any>('/quality/standards', p),
  create: (p: WorkspaceQuery, body: Record<string, unknown>) =>
    createResource<any>('/quality/standards', p, body),
  update: (p: WorkspaceQuery, id: number, body: Record<string, unknown>) =>
    updateResource<any>('/quality/standards', id, p, body),
  remove: (p: WorkspaceQuery, id: number) => deleteResource('/quality/standards', id, p),
}

export const performanceApi = {
  employees: async (p: WorkspaceQuery) => unwrap<any[]>(await apiService.get(`/employees/performance-options${qs(p)}`)),
  list: (p: WorkspaceQuery) => listResource<any>('/employees/performances', p),
  create: (p: WorkspaceQuery, body: Record<string, unknown>) =>
    createResource<any>('/employees/performances', p, body),
  update: (p: WorkspaceQuery, id: number, body: Record<string, unknown>) =>
    updateResource<any>('/employees/performances', id, p, body),
  remove: (p: WorkspaceQuery, id: number) => deleteResource('/employees/performances', id, p),
}

export const reportTemplateApi = {
  catalog: async () => unwrap<any[]>(await apiService.get('/reports/field-catalog')),
  list: (p: WorkspaceQuery) => listResource<any>('/reports/templates', p),
  create: (p: WorkspaceQuery, body: Record<string, unknown>) =>
    createResource<any>('/reports/templates', p, body),
  update: (p: WorkspaceQuery, id: number, body: Record<string, unknown>) =>
    updateResource<any>('/reports/templates', id, p, body),
  remove: (p: WorkspaceQuery, id: number) => deleteResource('/reports/templates', id, p),
  run: async (p: WorkspaceQuery, id: number) => {
    const { skip, limit, search, status, ...ws } = p
    const response = await apiService.post(
      `/reports/templates/${id}/run${qs(ws as Record<string, unknown>)}`,
      {}
    )
    return unwrap<any>(response)
  },
}

export function readWorkspaceQuery(): WorkspaceQuery {
  try {
    const raw = localStorage.getItem('current_workspace')
    const ws = raw ? JSON.parse(raw) : null
    const type = ws?.type === 'enterprise' || ws?.type === 'company' ? 'enterprise' : 'personal'
    return {
      workspace_type: type,
      company_id: ws?.company_id ? Number(ws.company_id) : undefined,
      factory_id: ws?.factory_id ? Number(ws.factory_id) : undefined,
    }
  } catch {
    return { workspace_type: 'personal' }
  }
}
