import React from 'react'
import {
  Joint,
  geometry,
  grooveOptions,
  isTubePlateGroove,
} from './consumableCalc'

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

/**
 * 与 weldmoney 的 GroovePreviewWidget 使用同一几何语义：板顶开口、向根部收窄，
 * X 形的 h 表示上半坡口高度，清根从板背向内。这里只把 QPainter 图元换成 SVG。
 */
const GroovePreview: React.FC<{ value: Joint }> = ({ value }) => {
  const area = geometry(value).total
  const label = grooveOptions.find(item => item.value === value.groove)?.label || value.groove
  const top = 48
  const bottom = 180
  const cx = 240
  const t = Math.max(value.thickness, 0.1)
  const scale = 132 / t
  const gap = clamp(value.gap * scale, 4, 34)
  const halfGap = gap / 2
  const root = clamp(value.rootFace * scale, 0, 110)
  const bevel = Math.max(132 - root, 0)
  const tan = Math.tan((clamp(value.angle, 0, 170) * Math.PI) / 360)
  const openHalf = clamp(halfGap + bevel * tan, halfGap, 105)
  const extra = clamp(value.faceExtra * scale, 0, 18)
  const reinf = clamp(value.reinforcement * scale, 0, 20)
  const gouge = clamp(value.backGougeDepth * scale, 0, 80)
  const steel = '#858b92'
  const steelEdge = '#3f4852'
  const weld = '#dca023'
  const weldEdge = '#96640f'

  const buttSteel = (leftInner: string, rightInner: string) => (
    <>
      <path d={`M35 ${top} H${cx - openHalf} ${leftInner} H35 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M445 ${top} H${cx + openHalf} ${rightInner} H445 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
    </>
  )

  let drawing: React.ReactNode
  if (value.groove === 'FILLET') {
    const k = clamp(value.legSize * 8, 34, 80)
    drawing = <>
      <rect x="55" y="156" width="370" height="38" fill={steel} stroke={steelEdge} strokeWidth="2" />
      <rect x="190" y="48" width="42" height="108" fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M232 156 L232 ${156 - k} L${232 + k} 156 Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
      <text x={246 + k / 2} y="145" fill="#1769aa" fontSize="14">K={value.legSize}</text>
    </>
  } else if (value.groove === 'LAP') {
    const k = clamp(value.legSize * 7, 30, 65)
    drawing = <>
      <rect x="65" y="62" width="255" height="44" fill={steel} stroke={steelEdge} strokeWidth="2" />
      <rect x="175" y="112" width="250" height="44" fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M175 106 L${175 - k} 106 L175 ${106 + k} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
      <text x="105" y="138" fill="#1769aa" fontSize="14">K={value.legSize}</text>
    </>
  } else if (isTubePlateGroove(value.groove)) {
    const wall = clamp(value.thickness * 3.2, 24, 48)
    const left = cx - 54
    const right = cx + 54
    const plateY = 158
    drawing = <>
      <rect x="35" y={plateY} width="410" height="38" fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M${left - wall} 42 H${left} V${plateY - 10} L${left - (value.groove === 'TP_X' ? wall / 2 : 0)} ${plateY} H${left - wall} Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M${right} 42 H${right + wall} V${plateY} H${right + (value.groove === 'TP_X' ? wall / 2 : 0)} L${right} ${plateY - 10} Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M${left} ${plateY - 28} L${left} ${plateY} L${left + 42} ${plateY} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
      <path d={`M${right} ${plateY - 28} L${right - 42} ${plateY} L${right} ${plateY} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
      {value.groove === 'TP_X' && <>
        <path d={`M${left - wall / 2} ${plateY} L${left} ${plateY} L${left - wall / 2} ${plateY + 22} Z`} fill={weld} stroke={weldEdge} strokeWidth="2" />
        <path d={`M${right + wall / 2} ${plateY} L${right} ${plateY} L${right + wall / 2} ${plateY + 22} Z`} fill={weld} stroke={weldEdge} strokeWidth="2" />
      </>}
      <line x1={left} y1="32" x2={right} y2="32" stroke="#1769aa" />
      <text x={cx} y="26" fill="#1769aa" fontSize="14" textAnchor="middle">接管 Φ{value.tubeDiameter}</text>
      <text x="356" y="145" fill="#1769aa" fontSize="14">t={value.thickness}</text>
    </>
  } else if (value.groove === 'X') {
    const usable = Math.max(t - value.rootFace, 0)
    const upperMm = value.upperHeight > 0 ? Math.min(value.upperHeight, usable) : usable / 2
    const upper = clamp(upperMm * scale, 0, 132 - root)
    const rootTop = top + upper
    const rootBottom = rootTop + root
    const lower = Math.max(bottom - rootBottom, 0)
    const upperOpen = clamp(halfGap + upper * tan, halfGap, 105)
    const lowerOpen = clamp(halfGap + lower * tan, halfGap, 105)
    drawing = <>
      <path d={`M35 ${top} H${cx - upperOpen} L${cx - halfGap} ${rootTop} V${rootBottom} L${cx - lowerOpen} ${bottom} H35 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M445 ${top} H${cx + upperOpen} L${cx + halfGap} ${rootTop} V${rootBottom} L${cx + lowerOpen} ${bottom} H445 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M${cx - upperOpen - extra} ${top} Q${cx} ${top - reinf} ${cx + upperOpen + extra} ${top} L${cx + halfGap} ${rootTop} V${rootBottom} L${cx + lowerOpen + extra} ${bottom} Q${cx} ${bottom + reinf} ${cx - lowerOpen - extra} ${bottom} L${cx - halfGap} ${rootBottom} V${rootTop} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
    </>
  } else if (value.groove === 'U') {
    const radius = clamp(value.radius * scale, 4, bevel * .75)
    const straight = Math.max(bevel - radius, 0)
    const shoulder = clamp(halfGap + radius + straight * tan, halfGap + radius, 105)
    const arcY = top + straight
    drawing = <>
      <path d={`M35 ${top} H${cx - shoulder} L${cx - halfGap - radius} ${arcY} Q${cx - halfGap} ${arcY} ${cx - halfGap} ${arcY + radius} V${bottom} H35 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M445 ${top} H${cx + shoulder} L${cx + halfGap + radius} ${arcY} Q${cx + halfGap} ${arcY} ${cx + halfGap} ${arcY + radius} V${bottom} H445 Z`} fill={steel} stroke={steelEdge} strokeWidth="2" />
      <path d={`M${cx - shoulder - extra} ${top} Q${cx} ${top - reinf} ${cx + shoulder + extra} ${top} L${cx + halfGap + radius} ${arcY} Q${cx + halfGap} ${arcY} ${cx + halfGap} ${arcY + radius} V${bottom} H${cx - halfGap} V${arcY + radius} Q${cx - halfGap} ${arcY} ${cx - halfGap - radius} ${arcY} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
    </>
  } else if (value.groove === 'I') {
    drawing = <>
      {buttSteel(`V${bottom}`, `V${bottom}`)}
      <path d={`M${cx - halfGap - extra} ${top} Q${cx} ${top - reinf} ${cx + halfGap + extra} ${top} L${cx + halfGap} ${bottom} H${cx - halfGap} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
    </>
  } else {
    const rootY = top + bevel
    drawing = <>
      {buttSteel(`L${cx - halfGap} ${rootY} V${bottom}`, `L${cx + halfGap} ${rootY} V${bottom}`)}
      <path d={`M${cx - openHalf - extra} ${top} Q${cx} ${top - reinf} ${cx + openHalf + extra} ${top} L${cx + halfGap} ${rootY} V${bottom} H${cx - halfGap} V${rootY} Z`} fill={weld} stroke={weldEdge} strokeWidth="2.5" />
    </>
  }

  return (
    <div className="cc-preview" role="img" aria-label={`${label}截面预览`}>
      <div className="cc-preview__title">{label}　A = {area.toFixed(1)} mm²</div>
      <svg viewBox="0 0 480 225" aria-hidden="true">
        {drawing}
        {!['FILLET', 'LAP', 'X', 'TP_X', 'TP_V'].includes(value.groove) && gouge > 0 && (
          <path
            d={`M${cx - halfGap - gouge / 2} ${bottom} Q${cx} ${bottom - gouge} ${cx + halfGap + gouge / 2} ${bottom} Z`}
            fill="#ee8b2c"
            stroke="#b84b13"
            strokeWidth="2"
          />
        )}
        {!['FILLET', 'LAP'].includes(value.groove) && !isTubePlateGroove(value.groove) && <>
          <line x1="422" y1={top} x2="422" y2={bottom} stroke="#1769aa" strokeWidth="1.5" />
          <line x1="416" y1={top} x2="428" y2={top} stroke="#1769aa" />
          <line x1="416" y1={bottom} x2="428" y2={bottom} stroke="#1769aa" />
          <text x="430" y="119" fill="#1769aa" fontSize="14">t={value.thickness}</text>
          <text x="42" y="215" fill="#64748b" fontSize="12">α={value.angle}°　b={value.gap}　p={value.rootFace}</text>
        </>}
      </svg>
    </div>
  )
}

export default GroovePreview
