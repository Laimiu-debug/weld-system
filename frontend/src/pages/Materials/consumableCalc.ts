/**
 * 焊材用量纯计算（对齐 weldmoney 核心公式 + 本项目 P6 分层损耗）。
 *
 * 主链路：
 *   熔敷质量 deposit = A(mm²) × L(mm) × ρ(g/cm³) / 1e6
 *   理论消耗 primary = deposit / η
 *   工艺消耗 process = primary × (1 + stub + spatter)
 *   企业修正 enterprise = process × enterpriseFactor
 *   建议领用 suggested = ceil(enterprise / package) × package（可选）
 *   焊剂 flux = primary × fluxRatio（再叠焊剂损耗与企业修正）
 *
 * 焊道数不参与质量计算（截面积已代表完整熔敷量）。
 */

export type Groove =
  | 'I'
  | 'V'
  | 'X'
  | 'U'
  | 'FILLET'
  | 'LAP'
  | 'BACK_GOUGE'
  | 'TP_V'
  | 'TP_X'
export type OperationRole = 'face' | 'gouge' | 'tack' | 'custom'
export type DiameterBasis = 'od' | 'id' | 'mean'

export type Operation = {
  id: string
  role: OperationRole
  name: string
  method: string
  material: string
  density: number
  efficiency: number
  unitPrice: number
  fluxRatio: number
  customArea: number
  /** 焊条头损耗率 0~1，焊条默认约 0.08 */
  stubLoss: number
  /** 飞溅损耗率 0~1 */
  spatterLoss: number
  /** 焊剂损耗率 0~1（埋弧焊） */
  fluxLoss: number
  /** 企业修正系数，默认 1.0 */
  enterpriseFactor: number
  /** 包装规格 kg，空则不取整 */
  packageSizeKg: number | null
  /** 熔敷速度 kg/h，用于推算电弧时间与气体 */
  depositionRateKgH: number | null
  /** 燃弧系数 0~1 */
  arcTimeRatio: number
  /** 保护气体流量 L/min */
  gasFlowLMin: number | null
}

export type Joint = {
  id: string
  name: string
  length: number
  groove: Groove
  thickness: number
  angle: number
  gap: number
  rootFace: number
  radius: number
  upperHeight: number
  legSize: number
  reinforcement: number
  backGougeDepth: number
  /** 清根槽开口宽；0 则用参考近似 gap + depth */
  gougeOpeningWidth: number
  faceExtra: number
  fillFactor: number
  /** 管板焊：接管外径 mm，用于环缝长度估算 */
  tubeDiameter: number
  operations: Operation[]
}

export type LengthDraft = {
  mode: 'circumference' | 'straight'
  diameter: number
  wallThickness: number
  diameterBasis: DiameterBasis
  angle: number
  count: number
  straight: number
}

export type GeometryResult = {
  face: number
  gouge: number
  total: number
  geometryTotal: number
  warnings: string[]
}

export type OperationCalcResult = {
  area: number
  deposit: number
  primary: number
  process: number
  enterprise: number
  suggested: number
  flux: number
  processFlux: number
  enterpriseFlux: number
  arcTimeH: number | null
  totalTimeH: number | null
  gasVolumeL: number | null
  cost: number
}

export const grooveOptions = [
  { value: 'I' as const, label: 'I形对接' },
  { value: 'V' as const, label: 'V形对接' },
  { value: 'X' as const, label: 'X形对接' },
  { value: 'U' as const, label: 'U形对接' },
  { value: 'BACK_GOUGE' as const, label: '背面开清根（单面V+清根）' },
  { value: 'TP_V' as const, label: '管板焊·单面坡口' },
  { value: 'TP_X' as const, label: '管板焊·双面坡口' },
  { value: 'FILLET' as const, label: '角焊缝' },
  { value: 'LAP' as const, label: '搭接' },
]

export const isTubePlateGroove = (groove: Groove) => groove === 'TP_V' || groove === 'TP_X'
export const isBackGougeGroove = (groove: Groove) => groove === 'BACK_GOUGE'
export const thicknessLabel = (groove: Groove) =>
  isTubePlateGroove(groove) ? '管壁厚度 t' : '板厚 t'

/** 切换坡口形式时的推荐默认参数 */
export const defaultParamsForGroove = (groove: Groove): Partial<Joint> => {
  const common = { fillFactor: 1.05, faceExtra: 1, reinforcement: 2, gap: 2 }
  switch (groove) {
    case 'BACK_GOUGE':
      return {
        ...common,
        groove,
        angle: 60,
        rootFace: 2,
        backGougeDepth: 3,
        gougeOpeningWidth: 0,
        operations: [createOperation('face'), createOperation('gouge')],
      }
    case 'TP_V':
      return {
        ...common,
        groove,
        thickness: 10,
        angle: 35,
        rootFace: 1.5,
        legSize: 6,
        backGougeDepth: 0,
        tubeDiameter: 219,
      }
    case 'TP_X':
      return {
        ...common,
        groove,
        thickness: 10,
        angle: 35,
        rootFace: 1,
        upperHeight: 0,
        legSize: 0,
        backGougeDepth: 0,
        tubeDiameter: 219,
      }
    case 'I':
      return { ...common, groove, angle: 0, rootFace: 0, backGougeDepth: 2 }
    case 'X':
      return { ...common, groove, angle: 60, rootFace: 2, backGougeDepth: 0, upperHeight: 0 }
    case 'U':
      return { ...common, groove, angle: 20, rootFace: 2, radius: 5, backGougeDepth: 2 }
    case 'FILLET':
    case 'LAP':
      return { ...common, groove, legSize: groove === 'FILLET' ? 8 : 6, backGougeDepth: 0 }
    default:
      return { ...common, groove, angle: 60, rootFace: 2, backGougeDepth: 2 }
  }
}

export const roleMeta: Record<OperationRole, { label: string; area: 'face' | 'gouge' | 'custom' }> = {
  face: { label: '正面填充', area: 'face' },
  gouge: { label: '清根填充', area: 'gouge' },
  tack: { label: '固定焊', area: 'custom' },
  custom: { label: '自定义工序', area: 'custom' },
}

/** 常用焊材预设（来自 weldmoney 标准目录，简化规格） */
export const materialPresets = [
  { label: 'ER50-6 焊丝 Φ1.2', material: 'ER50-6 焊丝 Φ1.2', density: 7.85, efficiency: 0.95, unitPrice: 12.5, depositionRateKgH: 2.0, stubLoss: 0, spatterLoss: 0.03 },
  { label: 'ER50-6 焊丝 Φ1.6', material: 'ER50-6 焊丝 Φ1.6', density: 7.85, efficiency: 0.95, unitPrice: 12.0, depositionRateKgH: 3.0, stubLoss: 0, spatterLoss: 0.03 },
  { label: 'E71T-1 药芯 Φ1.2', material: 'E71T-1 药芯焊丝 Φ1.2', density: 7.85, efficiency: 0.88, unitPrice: 14.0, depositionRateKgH: 2.5, stubLoss: 0, spatterLoss: 0.05 },
  { label: 'H08A 埋弧焊丝 Φ4.0', material: 'H08A 焊丝 Φ4.0', density: 7.85, efficiency: 0.98, unitPrice: 8.0, depositionRateKgH: 5.0, stubLoss: 0, spatterLoss: 0.01 },
  { label: 'E5015 焊条 Φ3.2', material: 'E5015 焊条 Φ3.2', density: 7.85, efficiency: 0.55, unitPrice: 10.0, depositionRateKgH: 1.0, stubLoss: 0.08, spatterLoss: 0.05 },
  { label: 'E5015 焊条 Φ4.0', material: 'E5015 焊条 Φ4.0', density: 7.85, efficiency: 0.55, unitPrice: 9.5, depositionRateKgH: 1.5, stubLoss: 0.08, spatterLoss: 0.05 },
  { label: 'ER308L 不锈钢丝 Φ1.2', material: 'ER308L 不锈钢焊丝 Φ1.2', density: 8.0, efficiency: 0.95, unitPrice: 45.0, depositionRateKgH: 2.0, stubLoss: 0, spatterLoss: 0.03 },
  { label: 'ER316L 不锈钢丝 Φ1.2', material: 'ER316L 不锈钢焊丝 Φ1.2', density: 8.0, efficiency: 0.95, unitPrice: 51.0, depositionRateKgH: 2.0, stubLoss: 0, spatterLoss: 0.03 },
]

/** 焊接方法预设：默认焊剂比 / 气体流量 */
export const methodPresets = [
  { label: 'GMAW 气保焊 (135)', method: 'GMAW(熔化极气保焊) (135)', fluxRatio: 0, gasFlowLMin: 18, arcTimeRatio: 0.4 },
  { label: 'FCAW 药芯焊 (136)', method: 'FCAW(药芯焊) (136)', fluxRatio: 0, gasFlowLMin: 18, arcTimeRatio: 0.4 },
  { label: 'SMAW 焊条电弧焊 (111)', method: 'SMAW(焊条电弧焊) (111)', fluxRatio: 0, gasFlowLMin: null, arcTimeRatio: 0.3 },
  { label: 'SAW 埋弧焊 (12)', method: 'SAW(埋弧焊) (12)', fluxRatio: 1.2, gasFlowLMin: null, arcTimeRatio: 0.6 },
  { label: 'GTAW 氩弧焊 (141)', method: 'GTAW(钨极氩弧焊) (141)', fluxRatio: 0, gasFlowLMin: 10, arcTimeRatio: 0.35 },
]

export const num = (value: unknown, fallback = 0) =>
  Number.isFinite(Number(value)) ? Number(value) : fallback

export const createOperation = (
  role: OperationRole = 'face',
  seed: Partial<Operation> = {},
): Operation => ({
  id: crypto.randomUUID(),
  role,
  name: roleMeta[role].label,
  method: 'GMAW(熔化极气保焊) (135)',
  material: 'ER50-6 焊丝 Φ1.2',
  density: 7.85,
  efficiency: 0.95,
  unitPrice: 12.5,
  fluxRatio: 0,
  customArea: role === 'tack' ? 8 : 0,
  stubLoss: 0,
  spatterLoss: 0.03,
  fluxLoss: 0,
  enterpriseFactor: 1.0,
  packageSizeKg: null,
  depositionRateKgH: 2.0,
  arcTimeRatio: 0.4,
  gasFlowLMin: 18,
  ...seed,
})

export const createJoint = (seed: Partial<Joint> = {}): Joint => ({
  id: crypto.randomUUID(),
  name: '',
  length: 0,
  groove: 'V',
  thickness: 12,
  angle: 60,
  gap: 2,
  rootFace: 2,
  radius: 5,
  upperHeight: 0,
  legSize: 8,
  reinforcement: 2,
  backGougeDepth: 2,
  gougeOpeningWidth: 0,
  faceExtra: 1,
  fillFactor: 1.05,
  tubeDiameter: 219,
  operations: [createOperation()],
  ...seed,
})

export const normalizeGroove = (value: unknown): Groove => {
  const text = String(value || '').toUpperCase()
  if (text.includes('管板') && (text.includes('双') || text.includes('X') || text.includes('TP_X'))) {
    return 'TP_X'
  }
  if (text.includes('管板') || text.includes('TP_V') || text.includes('接管')) {
    return 'TP_V'
  }
  if (
    text.includes('背面') &&
    (text.includes('清根') || text.includes('BACK_GOUGE') || text.includes('BACK'))
  ) {
    return 'BACK_GOUGE'
  }
  if (text.includes('角') || text.includes('FILLET')) return 'FILLET'
  if (text.includes('搭') || text.includes('LAP')) return 'LAP'
  if (text.startsWith('X') || text.includes('X形')) return 'X'
  if (text.startsWith('U') || text.includes('U形')) return 'U'
  if (text.startsWith('I') || text.includes('I形')) return 'I'
  return 'V'
}

const tanHalf = (angle: number) => Math.tan((angle * Math.PI) / 360)
const triangle = (width: number, height: number) =>
  (Math.max(width, 0) * Math.max(height, 0)) / 2

/**
 * 坡口截面积：对齐后端 P6 geometry + weldmoney 清根近似。
 * face = 正面熔敷（含余高），gouge = 清根槽（含背面余高，X 形除外）。
 */
export const geometry = (j: Joint): GeometryResult => {
  const warnings: string[] = []
  if (j.fillFactor < 1) warnings.push('填充系数小于 1.0，计算量低于理论几何量')
  if (j.fillFactor > 1.15) warnings.push('填充系数偏大；清根/展宽/损耗建议用独立参数')
  const thicknessWord = isTubePlateGroove(j.groove) ? '管壁厚度' : '板厚'
  if (j.groove !== 'FILLET' && j.groove !== 'LAP') {
    if (j.rootFace > j.thickness) warnings.push(`钝边大于${thicknessWord}`)
    if (j.backGougeDepth >= j.thickness && j.thickness > 0) {
      warnings.push(`清根深度不应达到或超过${thicknessWord}`)
    }
  }
  if (isBackGougeGroove(j.groove) && j.backGougeDepth <= 0) {
    warnings.push('背面开清根形式应填写清根深度')
  }
  if (j.groove === 'TP_X' || j.groove === 'X') {
    const bevel = Math.max(j.thickness - j.rootFace, 0)
    const upper = j.upperHeight > 0 ? Math.min(j.upperHeight, bevel) : bevel / 2
    const lower = Math.max(bevel - upper, 0)
    if (upper + lower > bevel + 1e-6) {
      warnings.push('上下坡口高度之和超过可用管壁/板厚')
    }
  }

  if (j.groove === 'FILLET' || j.groove === 'LAP') {
    const faceWidth = Math.SQRT2 * j.legSize + 2 * j.faceExtra
    const geom = 0.5 * j.legSize ** 2 + triangle(faceWidth, j.reinforcement)
    const total = Math.max(geom * j.fillFactor, 0)
    return { face: total, gouge: 0, total, geometryTotal: geom, warnings }
  }

  const t = Math.max(j.thickness, 0)
  const gap = Math.max(j.gap, 0)
  const bevel = Math.max(t - j.rootFace, 0)
  const tan = tanHalf(j.angle)
  const extra = Math.max(j.faceExtra, 0)
  let front = t * gap
  let frontWidth = gap + 2 * extra

  if (j.groove === 'I') {
    front += triangle(frontWidth, j.reinforcement)
  } else if (j.groove === 'V' || j.groove === 'BACK_GOUGE' || j.groove === 'TP_V') {
    frontWidth = gap + 2 * bevel * tan + 2 * extra
    const cornerFillet =
      j.groove === 'TP_V' && j.legSize > 0 ? 0.5 * j.legSize ** 2 : 0
    front += bevel ** 2 * tan + cornerFillet + triangle(frontWidth, j.reinforcement)
  } else if (j.groove === 'X' || j.groove === 'TP_X') {
    const upper = j.upperHeight > 0 ? Math.min(j.upperHeight, bevel) : bevel / 2
    const lower = Math.max(bevel - upper, 0)
    frontWidth = gap + 2 * upper * tan + 2 * extra
    const backWidth = gap + 2 * lower * tan + 2 * extra
    front +=
      upper ** 2 * tan +
      lower ** 2 * tan +
      triangle(frontWidth, j.reinforcement) +
      triangle(backWidth, j.reinforcement)
  } else if (j.groove === 'U') {
    const radius = Math.min(Math.max(j.radius, 0), bevel)
    const straight = Math.max(bevel - radius, 0)
    frontWidth = gap + 2 * radius + 2 * straight * tan + 2 * extra
    front +=
      2 * radius * straight +
      straight ** 2 * tan +
      (Math.PI * radius ** 2) / 2 +
      triangle(frontWidth, j.reinforcement)
  }

  let gougeCavity = 0
  let gougeOpening = 0
  const skipBackGouge = j.groove === 'TP_X' || j.groove === 'X'
  if (j.backGougeDepth > 0 && !skipBackGouge) {
    gougeOpening =
      j.gougeOpeningWidth > 0 ? j.gougeOpeningWidth : gap + j.backGougeDepth
    gougeCavity = (j.backGougeDepth * (gap + gougeOpening)) / 2
    if (!(j.gougeOpeningWidth > 0)) {
      warnings.push('清根槽采用参考近似，生产使用前建议填写实测开口宽')
    }
  }

  const gougeReinf =
    !skipBackGouge && j.backGougeDepth > 0
      ? triangle(gougeOpening + 2 * extra, j.reinforcement)
      : 0

  const geometryTotal = front + gougeCavity + gougeReinf
  const factor = j.fillFactor
  const gouge = (gougeCavity + gougeReinf) * factor
  const total = Math.max(geometryTotal * factor, 0)
  return {
    face: Math.max(total - gouge, 0),
    gouge,
    total,
    geometryTotal,
    warnings,
  }
}

/** 环缝有效直径：外径 / 内径 / 中径 */
export const effectiveDiameter = (
  od: number,
  wall: number,
  basis: DiameterBasis,
): number => {
  if (basis === 'id') return Math.max(od - 2 * wall, 0)
  if (basis === 'mean') return Math.max(od - wall, 0)
  return Math.max(od, 0)
}

export const calcWeldLength = (draft: LengthDraft): number => {
  if (draft.mode === 'straight') {
    return Math.max(draft.straight, 0) * Math.max(draft.count, 1)
  }
  const d = effectiveDiameter(draft.diameter, draft.wallThickness, draft.diameterBasis)
  return Math.PI * d * (Math.max(draft.angle, 0) / 360) * Math.max(draft.count, 1)
}

/**
 * 单工序用量。焊道数不乘质量（与 weldmoney / P6 一致）。
 */
export const operationResult = (j: Joint, operation: Operation): OperationCalcResult => {
  const areas = geometry(j)
  const areaKind = roleMeta[operation.role].area
  const area =
    areaKind === 'face'
      ? areas.face
      : areaKind === 'gouge'
        ? areas.gouge
        : Math.max(operation.customArea, 0)

  const deposit = (area * j.length * operation.density) / 1_000_000
  const efficiency = operation.efficiency > 0 ? operation.efficiency : 0
  const primary = efficiency > 0 ? deposit / efficiency : 0
  const stub = Math.max(0, Math.min(operation.stubLoss, 0.99))
  const spatter = Math.max(0, Math.min(operation.spatterLoss, 0.99))
  const process = primary * (1 + stub + spatter)
  const enterprise = process * Math.max(operation.enterpriseFactor, 0)
  const pkg = operation.packageSizeKg
  const suggested =
    pkg != null && pkg > 0 ? Math.ceil(enterprise / pkg) * pkg : enterprise

  const flux = primary * Math.max(operation.fluxRatio, 0)
  const fluxLoss = Math.max(0, Math.min(operation.fluxLoss, 0.99))
  const processFlux = flux * (1 + fluxLoss)
  const enterpriseFlux = processFlux * Math.max(operation.enterpriseFactor, 0)

  const rate = operation.depositionRateKgH
  const arcTimeH = rate != null && rate > 0 ? deposit / rate : null
  const ratio = operation.arcTimeRatio
  const totalTimeH =
    arcTimeH != null && ratio > 0 && ratio <= 1 ? arcTimeH / ratio : null
  const gas =
    operation.gasFlowLMin != null && operation.gasFlowLMin > 0 && arcTimeH != null
      ? operation.gasFlowLMin * arcTimeH * 60
      : null

  return {
    area,
    deposit,
    primary,
    process,
    enterprise,
    suggested,
    flux,
    processFlux,
    enterpriseFlux,
    arcTimeH,
    totalTimeH,
    gasVolumeL: gas,
    cost: suggested * Math.max(operation.unitPrice, 0),
  }
}

export const emptyTotals = () => ({
  deposit: 0,
  primary: 0,
  process: 0,
  enterprise: 0,
  suggested: 0,
  flux: 0,
  enterpriseFlux: 0,
  gasVolumeL: 0,
  cost: 0,
})

export type Totals = ReturnType<typeof emptyTotals>

export const sumResults = (
  items: Array<{
    deposit: number
    primary: number
    process: number
    enterprise: number
    suggested: number
    flux: number
    enterpriseFlux: number
    gasVolumeL: number | null
    cost: number
  }>,
): Totals =>
  items.reduce<Totals>(
    (sum, item) => ({
      deposit: sum.deposit + item.deposit,
      primary: sum.primary + item.primary,
      process: sum.process + item.process,
      enterprise: sum.enterprise + item.enterprise,
      suggested: sum.suggested + item.suggested,
      flux: sum.flux + item.flux,
      enterpriseFlux: sum.enterpriseFlux + item.enterpriseFlux,
      gasVolumeL: sum.gasVolumeL + (item.gasVolumeL ?? 0),
      cost: sum.cost + item.cost,
    }),
    emptyTotals(),
  )
