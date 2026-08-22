import React from 'react'

export type ProductIconKind =
  | 'dashboard'
  | 'library'
  | 'wps'
  | 'pqr'
  | 'ppqr'
  | 'materials'
  | 'welder'
  | 'equipment'
  | 'production'
  | 'quality'
  | 'reports'
  | 'enterprise'
  | 'membership'
  | 'profile'

interface ProductIconProps extends Omit<React.SVGProps<SVGSVGElement>, 'children'> {
  kind: ProductIconKind
  size?: number
}

const paths: Record<ProductIconKind, React.ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="2" /><rect x="14" y="3" width="7" height="7" rx="2" /><rect x="3" y="14" width="7" height="7" rx="2" /><path d="M14 17.5h7M17.5 14v7" /></>,
  library: <><path d="m12 3 8 4-8 4-8-4 8-4Z" /><path d="m4 12 8 4 8-4M4 17l8 4 8-4" /></>,
  wps: <><path d="M6 2.8h8l4 4V21H6z" /><path d="M14 3v4h4M9 11h2.2l1.6 2-1.6 2H9l1.6 2H15" /></>,
  pqr: <><path d="M9 3h6M10 3v5l-4.7 8.1A3.2 3.2 0 0 0 8.1 21h7.8a3.2 3.2 0 0 0 2.8-4.9L14 8V3" /><path d="M8.2 15h7.6M10 18l1.4 1.4L15 16" /></>,
  ppqr: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H18v16H6.5A2.5 2.5 0 0 0 4 21.5z" /><path d="M4 5.5v16M9 8h5M9 12h3M15.5 14.5v5M13 17h5" /></>,
  materials: <><path d="M4 7h12l4 5-4 5H4z" /><path d="M8 7v10M12 7v10M16 7v10" /></>,
  welder: <><path d="M5 11a7 7 0 0 1 14 0v5H5z" /><path d="M8 16v2a4 4 0 0 0 8 0v-2M12 6v4M9 8l1 2M15 8l-1 2" /></>,
  equipment: <><rect x="3" y="5" width="14" height="13" rx="2" /><path d="M17 9h2a2 2 0 0 1 2 2v6M7 18v3M14 18v3M7 10h6M8 14h4" /><circle cx="19" cy="19" r="2" /></>,
  production: <><path d="M3 7h5v5H3zM16 12h5v5h-5z" /><path d="M8 9.5h5a3 3 0 0 1 3 3v2M5.5 12v5a2 2 0 0 0 2 2H16" /></>,
  quality: <><path d="M12 3 20 6v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6z" /><path d="m8.5 12 2.2 2.2 4.8-5" /></>,
  reports: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /><path d="m4 7 6-4 6 6 5-5" /></>,
  enterprise: <><path d="M3 21V9l6 3V7l6 3V3h6v18z" /><path d="M7 16h2M13 16h2M17 7h2M17 11h2M17 15h2" /></>,
  membership: <><path d="m12 3 2.5 5.1 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8z" /><circle cx="12" cy="12" r="2.2" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" /></>,
}

/** 24px 行业图标。统一 1.75px 线宽，适配侧栏、页头和业务卡片。 */
export const ProductIcon: React.FC<ProductIconProps> = ({ kind, size = 18, className, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    className={className}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    focusable="false"
    {...props}
  >
    {paths[kind]}
  </svg>
)

export default ProductIcon
