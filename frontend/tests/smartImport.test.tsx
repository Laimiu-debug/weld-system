import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { message } from 'antd'
import api from '../src/services/api'
import service from '../src/services/smartImport'
import SmartImportPage from '../src/pages/SmartImport'
import { parseManualValue } from '../src/pages/SmartImport/helpers'
import { unwrapApiData } from '../src/services/response'

vi.mock('../src/services/api', () => ({ default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() } }))

beforeEach(() => {
  vi.mocked(api.get).mockImplementation(async url => ({ success: true, data:
    String(url).endsWith('/batches') || String(url).endsWith('/ai-provider-configs') ? [] : null,
    timestamp: '' }))
  vi.mocked(api.post).mockReset()
})

describe('API response boundaries', () => {
  it('accepts raw bodies and success envelopes, preserving false/zero values and blobs', () => {
    expect(unwrapApiData({ count: 0 })).toEqual({ count: 0 })
    expect(unwrapApiData({ success: true, data: false })).toBe(false)
    const blob = new Blob(['file'])
    expect(unwrapApiData(blob)).toBe(blob)
  })
  it('rejects HTTP 200 business failures with their reason', async () => {
    vi.mocked(api.post).mockResolvedValue({ success: true, data: { success: false, message: '没有编辑权限' }, timestamp: '' })
    await expect(service.createBatch({ name: 'test', target_entity_type: 'pqr' })).rejects.toThrow('没有编辑权限')
  })
  it('unwraps envelopes returned by a migrated endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({ success: true, data: { success: true, data: [{ id: 'b1' }] }, timestamp: '' })
    expect(await service.listBatches()).toEqual([{ id: 'b1' }])
  })
  it.each(['', 'Infinity', 'NaN', '1.5'])('rejects invalid manual integers: %s', value => {
    expect(() => parseManualValue('integer', value)).toThrow('请输入有效数值')
  })
})

describe('smart import business interactions', () => {
  it('keeps the actual creation form after a business failure and supports retry', async () => {
    const success = vi.spyOn(message, 'success').mockImplementation(() => (() => {}) as never)
    const failure = vi.spyOn(message, 'error').mockImplementation(() => (() => {}) as never)
    vi.mocked(api.post).mockResolvedValueOnce({ success: true, data: { success: false, message: '暂时不可创建' }, timestamp: '' })
    render(<MemoryRouter><SmartImportPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /新建导入任务/ }))
    const input = screen.getByPlaceholderText('例如：历史 PQR 第一批导入') as HTMLInputElement
    fireEvent.change(input, { target: { value: '我的 PQR 批次' } })
    fireEvent.click(screen.getByRole('button', { name: /^创\s*建$/ }))
    await waitFor(() => expect(failure).toHaveBeenCalledWith('暂时不可创建'))
    expect(input.value).toBe('我的 PQR 批次')
    expect(success).not.toHaveBeenCalled()
    vi.mocked(api.post).mockResolvedValueOnce({ success: true, data: { id: 'b1' }, timestamp: '' })
    vi.mocked(api.get).mockImplementation(async url => ({ success: true, data:
      String(url).endsWith('/batches/b1') ? { id: 'b1', documents: [], target_entity_type: 'pqr' } : [], timestamp: '' }))
    fireEvent.click(screen.getByRole('button', { name: /^创\s*建$/ }))
    await waitFor(() => expect(success).toHaveBeenCalledWith('导入任务已创建'))
    expect(api.post).toHaveBeenCalledTimes(2)
  })
  it('blocks duplicate clicks while creating', async () => {
    vi.mocked(api.post).mockReturnValue(new Promise(() => {}))
    render(<MemoryRouter><SmartImportPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /新建导入任务/ }))
    fireEvent.change(screen.getByPlaceholderText('例如：历史 PQR 第一批导入'), { target: { value: 'PQR' } })
    const create = screen.getByRole('button', { name: /^创\s*建$/ })
    fireEvent.click(create); fireEvent.click(create)
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1))
  })
  it('shows a load error and retries instead of presenting failure as empty success', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('加载失败'))
    render(<MemoryRouter><SmartImportPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: '重试加载' }))
    await waitFor(() => expect(screen.queryByRole('button', { name: '重试加载' })).toBeNull())
    expect(api.get).toHaveBeenCalledWith('/smart-import/batches')
  })
})
