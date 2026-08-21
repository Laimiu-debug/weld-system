import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Empty, Input, Spin, Typography } from 'antd'
import {
  ExperimentOutlined,
  FileTextOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { apiService } from '@/services/api'
import { workspaceService } from '@/services/workspace'

const { Text } = Typography

type Hit = {
  key: string
  kind: 'wps' | 'pqr' | 'welder'
  title: string
  subtitle?: string
  path: string
}

function unwrapList(payload: unknown): any[] {
  if (Array.isArray(payload)) return payload
  if (!payload || typeof payload !== 'object') return []
  const obj = payload as Record<string, unknown>
  if (Array.isArray(obj.items)) return obj.items
  if (Array.isArray(obj.data)) return obj.data as any[]
  if (obj.data && typeof obj.data === 'object') {
    const nested = obj.data as Record<string, unknown>
    if (Array.isArray(nested.items)) return nested.items
    if (Array.isArray(nested.data)) return nested.data as any[]
  }
  return []
}

const GlobalSearch: React.FC = () => {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const reqIdRef = useRef(0)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  useEffect(() => {
    const q = keyword.trim()
    if (q.length < 1) {
      setHits([])
      setLoading(false)
      return
    }

    const timer = window.setTimeout(async () => {
      const reqId = ++reqIdRef.current
      setLoading(true)
      try {
        const workspace = workspaceService.getCurrentWorkspaceFromStorage()
        const welderParams: Record<string, unknown> = {
          skip: 0,
          limit: 8,
          search: q,
          workspace_type: workspace?.type || 'personal',
        }
        if (workspace?.type === 'enterprise') {
          welderParams.company_id = workspace.company_id
          if (workspace.factory_id) welderParams.factory_id = workspace.factory_id
        }

        const [wpsRes, pqrRes, welderRes] = await Promise.allSettled([
          apiService.get('/wps/', { params: { skip: 0, limit: 8, search_term: q } }),
          apiService.get('/pqr/', { params: { page: 1, page_size: 8, keyword: q } }),
          apiService.get('/welders/', { params: welderParams }),
        ])

        if (reqId !== reqIdRef.current) return

        const next: Hit[] = []

        if (wpsRes.status === 'fulfilled') {
          unwrapList(wpsRes.value.data).forEach((item: any) => {
            next.push({
              key: `wps-${item.id}`,
              kind: 'wps',
              title: item.wps_number || item.title || `WPS #${item.id}`,
              subtitle: [item.title !== item.wps_number ? item.title : null, item.status]
                .filter(Boolean)
                .join(' · '),
              path: `/wps/${item.id}`,
            })
          })
        }

        if (pqrRes.status === 'fulfilled') {
          unwrapList(pqrRes.value.data).forEach((item: any) => {
            next.push({
              key: `pqr-${item.id}`,
              kind: 'pqr',
              title: item.pqr_number || item.title || `PQR #${item.id}`,
              subtitle: [item.title !== item.pqr_number ? item.title : null, item.status]
                .filter(Boolean)
                .join(' · '),
              path: `/pqr/${item.id}`,
            })
          })
        }

        if (welderRes.status === 'fulfilled') {
          unwrapList(welderRes.value.data).forEach((item: any) => {
            next.push({
              key: `welder-${item.id}`,
              kind: 'welder',
              title: item.full_name || item.welder_code || `焊工 #${item.id}`,
              subtitle: [item.welder_code, item.department].filter(Boolean).join(' · '),
              path: `/welders/${item.id}`,
            })
          })
        }

        setHits(next)
        setOpen(true)
      } catch {
        if (reqId !== reqIdRef.current) return
        setHits([])
        setOpen(true)
      } finally {
        if (reqId === reqIdRef.current) setLoading(false)
      }
    }, 250)

    return () => window.clearTimeout(timer)
  }, [keyword])

  const goResultsPage = () => {
    const q = keyword.trim()
    if (!q) return
    setOpen(false)
    navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  const goHit = (path: string) => {
    setOpen(false)
    setKeyword('')
    navigate(path)
  }

  const kindMeta = {
    wps: { icon: <FileTextOutlined />, label: 'WPS' },
    pqr: { icon: <ExperimentOutlined />, label: 'PQR' },
    welder: { icon: <TeamOutlined />, label: '焊工' },
  } as const

  const grouped = {
    wps: hits.filter((h) => h.kind === 'wps'),
    pqr: hits.filter((h) => h.kind === 'pqr'),
    welder: hits.filter((h) => h.kind === 'welder'),
  }

  const showPanel = open && keyword.trim().length > 0

  return (
    <div className="global-search" ref={rootRef}>
      <Input
        allowClear
        value={keyword}
        placeholder="搜索 WPS、PQR、焊工…"
        prefix={<SearchOutlined />}
        className="search-input"
        onFocus={() => keyword.trim() && setOpen(true)}
        onChange={(e) => {
          setKeyword(e.target.value)
          if (e.target.value.trim()) setOpen(true)
        }}
        onPressEnter={goResultsPage}
      />

      {showPanel && (
        <div className="global-search__dropdown">
          {loading ? (
            <div className="global-search__state">
              <Spin size="small" /> 正在搜索…
            </div>
          ) : hits.length === 0 ? (
            <div className="global-search__state">
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={`未找到与 “${keyword.trim()}” 匹配的记录`}
              />
              <button type="button" className="global-search__more" onClick={goResultsPage}>
                打开完整搜索页
              </button>
            </div>
          ) : (
            <>
              {(['wps', 'pqr', 'welder'] as const).map((kind) =>
                grouped[kind].length ? (
                  <div key={kind} className="global-search__group">
                    <div className="global-search__group-title">{kindMeta[kind].label}</div>
                    {grouped[kind].map((hit) => (
                      <button
                        key={hit.key}
                        type="button"
                        className="global-search__item"
                        onClick={() => goHit(hit.path)}
                      >
                        <span className="global-search__item-icon">{kindMeta[kind].icon}</span>
                        <span className="global-search__item-text">
                          <strong>{hit.title}</strong>
                          {hit.subtitle ? <Text type="secondary">{hit.subtitle}</Text> : null}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null
              )}
              <Link
                className="global-search__more"
                to={`/search?q=${encodeURIComponent(keyword.trim())}`}
                onClick={() => setOpen(false)}
              >
                查看全部结果
              </Link>
            </>
          )}
        </div>
      )}

      <style>{`
        .global-search {
          position: relative;
          width: 100%;
          max-width: 420px;
        }
        .global-search__dropdown {
          position: absolute;
          top: calc(100% + 6px);
          left: 0;
          right: 0;
          z-index: 1050;
          max-height: 420px;
          overflow: auto;
          background: #fff;
          border: 1px solid rgba(20, 24, 31, 0.1);
          border-radius: 10px;
          box-shadow: 0 16px 40px -24px rgba(20, 24, 31, 0.45);
          padding: 8px 0;
        }
        .global-search__state {
          padding: 16px;
          text-align: center;
          color: #6b7385;
          font-size: 13px;
        }
        .global-search__group-title {
          padding: 6px 14px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #6b7385;
        }
        .global-search__item {
          width: 100%;
          display: flex;
          gap: 10px;
          align-items: flex-start;
          border: 0;
          background: transparent;
          text-align: left;
          padding: 8px 14px;
          cursor: pointer;
        }
        .global-search__item:hover {
          background: #f3f6ff;
        }
        .global-search__item-icon {
          color: #1f5eff;
          margin-top: 2px;
        }
        .global-search__item-text {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }
        .global-search__item-text strong {
          font-size: 13px;
          color: #14181f;
        }
        .global-search__more {
          display: block;
          width: calc(100% - 16px);
          margin: 8px 8px 4px;
          padding: 8px 10px;
          border: 0;
          border-radius: 6px;
          background: #f5f7fa;
          color: #1f5eff;
          font-size: 13px;
          font-weight: 600;
          text-align: center;
          text-decoration: none;
          cursor: pointer;
        }
        .global-search__more:hover {
          background: #eef3ff;
        }
      `}</style>
    </div>
  )
}

export default GlobalSearch
