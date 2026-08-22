import React from 'react';

const BrandMark: React.FC<{ size?: number; className?: string }> = ({ size = 32, className }) => (
  <svg
    viewBox="0 0 40 40"
    width={size}
    height={size}
    className={className}
    role="img"
    aria-label="焊序"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect width="40" height="40" rx="11" fill="url(#admin-weld-bg)" />
    <path d="M10 10V30H14.5" stroke="white" strokeWidth="2.4" strokeLinecap="round" />
    <path d="M30 10V30H25.5" stroke="white" strokeWidth="2.4" strokeLinecap="round" />
    <path d="M18 10.5 22 14.5 18 18.5 22 22.5 18 26.5 21.5 30" stroke="url(#admin-weld-arc)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M20 7V4.5M15.8 8.2 14 6.4M24.2 8.2 26 6.4" stroke="#67E8F9" strokeWidth="1.8" strokeLinecap="round" />
    <defs>
      <linearGradient id="admin-weld-bg" x1="5" y1="3" x2="35" y2="37" gradientUnits="userSpaceOnUse">
        <stop stopColor="#172554" /><stop offset="0.55" stopColor="#0B2F55" /><stop offset="1" stopColor="#07111F" />
      </linearGradient>
      <linearGradient id="admin-weld-arc" x1="18" y1="10" x2="23" y2="30" gradientUnits="userSpaceOnUse">
        <stop stopColor="#67E8F9" /><stop offset="0.48" stopColor="#38BDF8" /><stop offset="1" stopColor="#2563EB" />
      </linearGradient>
    </defs>
  </svg>
);

export default BrandMark;
