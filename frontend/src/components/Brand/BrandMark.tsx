import React from 'react'

export interface BrandMarkProps extends Omit<React.SVGProps<SVGSVGElement>, 'width' | 'height'> {
  size?: number
  title?: string
}

/**
 * 焊序品牌标识：两侧坡口代表待焊母材，中间折线代表连续焊缝，
 * 顶部三束电弧强调“焊接 + 数字化序列”。
 */
export const BrandMark: React.FC<BrandMarkProps> = ({
  size = 32,
  title = '焊序',
  className,
  ...props
}) => (
  <svg
    viewBox="0 0 40 40"
    width={size}
    height={size}
    className={className}
    role="img"
    aria-label={title}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <rect width="40" height="40" rx="11" fill="url(#weld-sequence-bg)" />
    <path d="M10 10V30H14.5" stroke="white" strokeWidth="2.4" strokeLinecap="round" />
    <path d="M30 10V30H25.5" stroke="white" strokeWidth="2.4" strokeLinecap="round" />
    <path
      d="M18 10.5L22 14.5L18 18.5L22 22.5L18 26.5L21.5 30"
      stroke="url(#weld-sequence-arc)"
      strokeWidth="2.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M20 7V4.5M15.8 8.2L14 6.4M24.2 8.2L26 6.4" stroke="#67E8F9" strokeWidth="1.8" strokeLinecap="round" />
    <defs>
      <linearGradient id="weld-sequence-bg" x1="5" y1="3" x2="35" y2="37" gradientUnits="userSpaceOnUse">
        <stop stopColor="#172554" />
        <stop offset="0.55" stopColor="#0B2F55" />
        <stop offset="1" stopColor="#07111F" />
      </linearGradient>
      <linearGradient id="weld-sequence-arc" x1="18" y1="10" x2="23" y2="30" gradientUnits="userSpaceOnUse">
        <stop stopColor="#67E8F9" />
        <stop offset="0.48" stopColor="#38BDF8" />
        <stop offset="1" stopColor="#2563EB" />
      </linearGradient>
    </defs>
  </svg>
)

export default BrandMark
