import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { message } from 'antd'
import DrawingReview from '../src/pages/Engineering/DrawingReview'
import { engineeringService } from '../src/services/engineering'
import smartImport from '../src/services/smartImport'

vi.mock('../src/services/engineering', () => ({ engineeringService: {
  detail: vi.fn(), history: vi.fn(), preview: vi.fn(), parseJobs: vi.fn(), parse: vi.fn(),
} }))
vi.mock('../src/services/smartImport', () => ({ default: { getAICapabilities: vi.fn() } }))

beforeEach(() => {
  vi.mocked(engineeringService.detail).mockResolvedValue({ revision: { id: 'rev', drawing_document_id: 'doc', status: 'draft', drawing_page_count: 1 }, parts: [], weld_joints: [], requirements: [], validation: { risks: [], can_approve: false }, preview_url: '' })
  vi.mocked(engineeringService.history).mockResolvedValue([])
  vi.mocked(engineeringService.preview).mockResolvedValue(new Blob())
  vi.mocked(smartImport.getAICapabilities).mockResolvedValue({ platform_available: false, platform_host: '', platform_provider: 'test', byok_providers: [], byok_allowed_hosts: [], max_document_pages: 50, max_input_chars: 1000 })
  URL.createObjectURL = vi.fn(() => 'blob:preview')
  URL.revokeObjectURL = vi.fn()
})

function show() {
  render(<MemoryRouter initialEntries={['/review/rev']}><Routes><Route path="/review/:id" element={<DrawingReview />} /></Routes></MemoryRouter>)
}

it('restores a queued job after reload and shows a later failure without success', async () => {
  const success = vi.spyOn(message, 'success')
  vi.mocked(engineeringService.parseJobs).mockResolvedValueOnce([{ id: 'job', status: 'queued', progress: 0 }])
    .mockResolvedValue([{ id: 'job', status: 'failed', error_message: '模型响应超时，请重试' }])
  show()
  await screen.findByText(/后台识别中/)
  await waitFor(() => expect(screen.getByText('模型响应超时，请重试')).toBeTruthy(), { timeout: 5000 })
  expect(engineeringService.parse).not.toHaveBeenCalled()
  expect(success).not.toHaveBeenCalled()
})

it('shows persistent completion with a human review reminder', async () => {
  vi.mocked(engineeringService.parseJobs).mockResolvedValue([{ id: 'job', status: 'completed', progress: 100 }])
  show()
  await screen.findByText('识别完成，结果须人工核对')
  expect(engineeringService.parse).not.toHaveBeenCalled()
})
