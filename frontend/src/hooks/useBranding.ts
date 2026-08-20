import { useEffect, useState } from 'react'
import { apiService } from '@/services/api'

export interface BrandingInfo {
  brand_name: string
  brand_subtitle: string
  org_name: string
  display_subtitle: string
  collapsed_label: string
}

const DEFAULT_BRANDING: BrandingInfo = {
  brand_name: import.meta.env.VITE_APP_TITLE || '焊序',
  brand_subtitle: import.meta.env.VITE_APP_SUBTITLE || 'Hanxu',
  org_name: import.meta.env.VITE_ORG_NAME || '',
  display_subtitle:
    import.meta.env.VITE_ORG_NAME ||
    import.meta.env.VITE_APP_SUBTITLE ||
    'Hanxu',
  collapsed_label: (import.meta.env.VITE_APP_TITLE || '焊序').slice(0, 2),
}

let cached: BrandingInfo | null = null
let inflight: Promise<BrandingInfo> | null = null

async function fetchBranding(): Promise<BrandingInfo> {
  try {
    const resp = await apiService.get<BrandingInfo>('/system/branding')
    const data = (resp as any)?.data?.data || (resp as any)?.data || resp
    if (data && typeof data.brand_name === 'string') {
      return {
        brand_name: data.brand_name || DEFAULT_BRANDING.brand_name,
        brand_subtitle: data.brand_subtitle || DEFAULT_BRANDING.brand_subtitle,
        org_name: data.org_name || '',
        display_subtitle:
          data.display_subtitle ||
          data.org_name ||
          data.brand_subtitle ||
          DEFAULT_BRANDING.display_subtitle,
        collapsed_label:
          data.collapsed_label ||
          (data.brand_name || DEFAULT_BRANDING.brand_name).slice(0, 2),
      }
    }
  } catch (error) {
    console.warn('加载品牌配置失败，使用默认值', error)
  }
  return DEFAULT_BRANDING
}

export function loadBranding(force = false): Promise<BrandingInfo> {
  if (!force && cached) return Promise.resolve(cached)
  if (!force && inflight) return inflight
  inflight = fetchBranding().then((info) => {
    cached = info
    inflight = null
    if (typeof document !== 'undefined' && info.brand_name) {
      const org = info.org_name ? ` · ${info.org_name}` : ''
      document.title = `${info.brand_name}${org} - 专业的焊接工艺管理平台`
    }
    return info
  })
  return inflight
}

export async function updateBranding(payload: {
  brand_name?: string
  brand_subtitle?: string
  org_name?: string
}): Promise<BrandingInfo> {
  const resp = await apiService.put<BrandingInfo>('/system/branding', payload)
  const data = (resp as any)?.data?.data || (resp as any)?.data || resp
  cached = null
  return loadBranding(true).then((info) => {
    if (data && typeof data.brand_name === 'string') {
      // prefer server merge already applied by loadBranding
    }
    return info
  })
}

export function useBranding(): BrandingInfo {
  const [branding, setBranding] = useState<BrandingInfo>(
    cached || DEFAULT_BRANDING
  )

  useEffect(() => {
    let cancelled = false
    void loadBranding().then((info) => {
      if (!cancelled) setBranding(info)
    })
    return () => {
      cancelled = true
    }
  }, [])

  return branding
}
