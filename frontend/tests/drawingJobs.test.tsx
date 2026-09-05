import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { message } from 'antd'
import DrawingReview from '../src/pages/Engineering/DrawingReview'
import { engineeringService } from '../src/services/engineering'
import smartImport from '../src/services/smartImport'

vi.mock('../src/services/engineering', () => ({ engineeringService: {
  detail: vi.fn(), history: vi.fn(), preview: vi.fn(), parseJobs: vi.fn(), parse: vi.fn(),
} }))
vi.mock('../src/services/smartImport', () => ({ default: { getAICapabilities: vi.fn(), cancelExtractionJob: vi.fn(), createOutboundConsent: vi.fn() } }))

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


it('cancels a restored running job without submitting another extraction', async () => {
  vi.mocked(engineeringService.parseJobs).mockResolvedValue([{ id: 'job', status: 'queued' }])
  vi.mocked(smartImport.cancelExtractionJob).mockResolvedValue({ id: 'job', status: 'cancelled' } as any)
  show()
  fireEvent.click(await screen.findByRole('button', { name: '取消识别' }))
  await waitFor(() => expect(smartImport.cancelExtractionJob).toHaveBeenCalledWith('job'))
  expect(engineeringService.parse).not.toHaveBeenCalled()
})

it('shows uncovered pages and keeps localized suggestions visibly separate', async () => {
  vi.mocked(engineeringService.detail).mockResolvedValue({ revision: { id:'rev', status:'review', data_version:3, drawing_page_count:2 }, parts:[], weld_joints:[], requirements:[], preview_url:'', validation: {can_approve:false, risks:[], completeness: {recognized_pages:[1],total_pages:2,unrecognized_pages:[2],part_count:0,weld_count:0,duplicate_weld_numbers:[],unresolved_connections:['W1'],unknown_quantities:['Plate'],missing_evidence:[{}],unresolved_regions:[],notice:'识别数量不是实际总数'}} })
  vi.mocked(engineeringService.parseJobs).mockResolvedValue([{ id:'job', status:'completed', progress_detail:{ proposal_only:true, source_data_version:3, proposal:{ parts:[{name:'局部零件',quantity:2}],weld_joints:[] } } }])
  show()
  await screen.findByText('识别完整性报告')
  expect(screen.getByText(/未覆盖页：2/)).toBeTruthy()
  expect(screen.getByText('局部识别建议（尚未写入审核数据）')).toBeTruthy()
  expect(screen.getByText('局部零件')).toBeTruthy()
  expect(engineeringService.parse).not.toHaveBeenCalled()
})

it('validates region bounds before an outbound call', async () => {
  vi.mocked(engineeringService.parseJobs).mockResolvedValue([])
  const error = vi.spyOn(message, 'error')
  show()
  fireEvent.click(await screen.findByRole('button', { name: '单页 / 区域识别' }))
  fireEvent.click(screen.getByLabelText('仅识别指定区域'))
  fireEvent.change(screen.getByLabelText('左 (%)'), { target:{ value:'100' } })
  fireEvent.click(screen.getByRole('button', { name:'识别所选范围' }))
  await waitFor(() => expect(error).toHaveBeenCalledWith('区域右下角必须大于左上角'))
  expect(engineeringService.parse).not.toHaveBeenCalled()
})
