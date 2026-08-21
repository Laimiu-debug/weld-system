import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Empty, Input, Spin, Tabs, Tag, Typography } from 'antd'
import {
  ExperimentOutlined,
  FileTextOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { apiService } from '@/services/api'
import { workspaceService } from '@/services/workspace'
import '@/styles/ResourceLibrary.css'

const { Text, Title } = Typography

type Hit = {
  id: number | string
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
  }
  return []
}

const SearchResultsPage: React.FC = () => {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const initialQ = params.get('q') || ''
  const [keyword, setKeyword] = useState(initialQ)
  const [loading, setLoading] = useState(false)
  const [hits, setHits] = useState<Hit[]>([])

  const runSearch = async (q: string) => {
    const query = q.trim()
    if (!query) {
      setHits([])
      return
    }
    setLoading(true)
    try {
      const workspace = workspaceService.getCurrentWorkspaceFromStorage()
      const welderParams: Record<string, unknown> = {
        skip: 0,
        limit: 50,
        search: query,
        workspace_type: workspace?.type || 'personal',
      }
      if (workspace?.type === 'enterprise') {
        welderParams.company_id = workspace.company_id
        if (workspace.factory_id) welderParams.factory_id = workspace.factory_id
      }

      const [wpsRes, pqrRes, welderRes] = await Promise.allSettled([
        apiService.get('/wps/', { params: { skip: 0, limit: 50, search_term: query } }),
        apiService.get('/pqr/', { params: { page: 1, page_size: 50, keyword: query } }),
        apiService.get('/welders/', { params: welderParams }),
      ])

      const next: Hit[] = []
      if (wpsRes.status === 'fulfilled') {
        unwrapList(wpsRes.value.data).forEach((item: any) => {
          next.push({
            id: item.id,
            kind: 'wps',
            title: item.wps_number || item.title || `WPS #${item.id}`,
            subtitle: [item.title, item.status].filter(Boolean).join(' · '),
            path: `/wps/${item.id}`,
          })
        })
      }
      if (pqrRes.status === 'fulfilled') {
        unwrapList(pqrRes.value.data).forEach((item: any) => {
          next.push({
            id: item.id,
            kind: 'pqr',
            title: item.pqr_number || item.title || `PQR #${item.id}`,
            subtitle: [item.title, item.status].filter(Boolean).join(' · '),
            path: `/pqr/${item.id}`,
          })
        })
      }
      if (welderRes.status === 'fulfilled') {
        unwrapList(welderRes.value.data).forEach((item: any) => {
          next.push({
            id: item.id,
            kind: 'welder',
            title: item.full_name || item.welder_code || `焊工 #${item.id}`,
            subtitle: [item.welder_code, item.department].filter(Boolean).join(' · '),
            path: `/welders/${item.id}`,
          })
        })
      }
      setHits(next)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const q = params.get('q') || ''
    setKeyword(q)
    void runSearch(q)
  }, [params])

  const submit = () => {
    const q = keyword.trim()
    setParams(q ? { q } : {})
  }

  const wps = hits.filter((h) => h.kind === 'wps')
  const pqr = hits.filter((h) => h.kind === 'pqr')
  const welders = hits.filter((h) => h.kind === 'welder')

  const renderList = (items: Hit[], emptyText: string) => {
    if (!items.length) {
      return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
    }
    return (
      <div className="search-results__list">
        {items.map((item) => (
          <button
            key={`${item.kind}-${item.id}`}
            type="button"
            className="search-results__row"
            onClick={() => navigate(item.path)}
          >
            <div>
              <strong>{item.title}</strong>
              {item.subtitle ? (
                <div>
                  <Text type="secondary">{item.subtitle}</Text>
                </div>
              ) : null}
            </div>
            <Tag>
              {item.kind === 'wps' ? 'WPS' : item.kind === 'pqr' ? 'PQR' : '焊工'}
            </Tag>
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="resource-page search-results">
      <div className="resource-page__header">
        <h1 className="resource-page__title">
          <SearchOutlined />
          全局搜索
        </h1>
      </div>

      <div className="resource-page__toolbar" style={{ marginBottom: 20 }}>
        <Input.Search
          allowClear
          value={keyword}
          placeholder="输入编号、标题、姓名等关键词"
          enterButton="搜索"
          style={{ maxWidth: 520 }}
          onChange={(e) => setKeyword(e.target.value)}
          onSearch={submit}
        />
        <Text type="secondary">
          当前工作区：{workspaceService.getCurrentWorkspaceFromStorage()?.name || '个人'}
        </Text>
      </div>

      {!keyword.trim() ? (
        <Empty description="输入关键词后开始搜索" />
      ) : loading ? (
        <div style={{ padding: 48, textAlign: 'center' }}>
          <Spin />
        </div>
      ) : (
        <>
          <Title level={5} style={{ marginTop: 0 }}>
            “{keyword.trim()}” 共 {hits.length} 条结果
          </Title>
          <Tabs
            items={[
              {
                key: 'all',
                label: `全部 (${hits.length})`,
                children: renderList(hits, '没有匹配结果'),
              },
              {
                key: 'wps',
                label: (
                  <span>
                    <FileTextOutlined /> WPS ({wps.length})
                  </span>
                ),
                children: renderList(wps, '没有匹配的 WPS'),
              },
              {
                key: 'pqr',
                label: (
                  <span>
                    <ExperimentOutlined /> PQR ({pqr.length})
                  </span>
                ),
                children: renderList(pqr, '没有匹配的 PQR'),
              },
              {
                key: 'welder',
                label: (
                  <span>
                    <TeamOutlined /> 焊工 ({welders.length})
                  </span>
                ),
                children: renderList(welders, '没有匹配的焊工'),
              },
            ]}
          />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">也可直接打开列表：</Text>{' '}
            <Link to={`/wps?q=${encodeURIComponent(keyword.trim())}`}>WPS 列表</Link>
            {' · '}
            <Link to={`/pqr?q=${encodeURIComponent(keyword.trim())}`}>PQR 列表</Link>
            {' · '}
            <Link to={`/welders?q=${encodeURIComponent(keyword.trim())}`}>焊工列表</Link>
          </div>
        </>
      )}

      <style>{`
        .search-results__list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .search-results__row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          width: 100%;
          text-align: left;
          border: 1px solid rgba(20,24,31,0.08);
          background: #f7f8fa;
          border-radius: 8px;
          padding: 12px 14px;
          cursor: pointer;
        }
        .search-results__row:hover {
          border-color: rgba(31,94,255,0.35);
          background: #f3f6ff;
        }
        .search-results__row strong {
          color: #14181f;
        }
      `}</style>
    </div>
  )
}

export default SearchResultsPage
