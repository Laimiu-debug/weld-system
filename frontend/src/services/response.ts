/** Normalize the documented raw/enveloped API bodies at a service boundary. */
export class ApiBusinessError extends Error {
  constructor(message: string, public requestId?: string) {
    super(message)
    this.name = 'ApiBusinessError'
  }
}

export function unwrapApiData<T>(body: unknown): T {
  if (body && typeof body === 'object' && 'success' in body) {
    const envelope = body as { success: unknown; data?: unknown; message?: string; error?: { message?: string }; request_id?: string }
    if (envelope.success === false) {
      throw new ApiBusinessError(envelope.message || envelope.error?.message || '操作失败，请重试', envelope.request_id)
    }
    if (envelope.success === true && 'data' in envelope) return envelope.data as T
  }
  return body as T
}
