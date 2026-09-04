/** weldmoney 风格成本参数与客户端报价汇总（与服务端 /calculator/quote 对齐） */

import { Joint, Operation, operationResult, sumResults } from './consumableCalc'

export type CostParams = {
  laborRatePerHour: number
  overheadRate: number
  gasPricePerL: number
  machinePowerKw: number
  electricityPrice: number
  dailyDepreciation: number
  dailyWorkHours: number
  profitMargin: number
  taxRate: number
  fluxUnitPrice: number
}

export const defaultCostParams = (): CostParams => ({
  laborRatePerHour: 80,
  overheadRate: 0.15,
  gasPricePerL: 0.02,
  machinePowerKw: 15,
  electricityPrice: 1.0,
  dailyDepreciation: 200,
  dailyWorkHours: 8,
  profitMargin: 0.12,
  taxRate: 0.13,
  fluxUnitPrice: 5,
})

const COST_STORAGE_KEY = 'consumable-cost-params-v1'

export const loadCostParams = (): CostParams => {
  try {
    const raw = localStorage.getItem(COST_STORAGE_KEY)
    if (!raw) return defaultCostParams()
    const saved = JSON.parse(raw)
    if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return defaultCostParams()
    const defaults = defaultCostParams()
    return Object.fromEntries(
      Object.entries(defaults).map(([key, fallback]) => {
        const value = Number((saved as Record<string, unknown>)[key])
        return [key, Number.isFinite(value) ? value : fallback]
      }),
    ) as CostParams
  } catch {
    return defaultCostParams()
  }
}

export const saveCostParams = (params: CostParams) => {
  localStorage.setItem(COST_STORAGE_KEY, JSON.stringify(params))
}

export type OperationCostBreakdown = {
  materialCost: number
  auxCost: number
  laborCost: number
  equipmentCost: number
  subtotal: number
}

export const operationCostBreakdown = (
  joint: Joint,
  operation: Operation,
  cost: CostParams,
): OperationCostBreakdown => {
  const result = operationResult(joint, operation)
  const arcTime = result.arcTimeH ?? 0
  const totalTime = result.totalTimeH ?? 0
  const gasL = result.gasVolumeL ?? 0

  let materialCost = result.suggested * operation.unitPrice
  if (result.enterpriseFlux > 0) {
    materialCost +=
      result.enterpriseFlux *
      (operation.fluxRatio > 0 && cost.fluxUnitPrice > 0
        ? cost.fluxUnitPrice
        : operation.unitPrice)
  }

  const auxCost = gasL * cost.gasPricePerL
  const laborCost = totalTime * cost.laborRatePerHour * (1 + cost.overheadRate)
  const powerCost = cost.machinePowerKw * arcTime * cost.electricityPrice
  const depreciation =
    cost.dailyWorkHours > 0
      ? cost.dailyDepreciation * (arcTime / cost.dailyWorkHours)
      : 0
  const equipmentCost = powerCost + depreciation
  const subtotal = materialCost + auxCost + laborCost + equipmentCost

  return { materialCost, auxCost, laborCost, equipmentCost, subtotal }
}

export type ProjectCostSummary = {
  deposit: number
  suggested: number
  flux: number
  gasVolumeL: number
  materialCost: number
  auxCost: number
  laborCost: number
  equipmentCost: number
  directCost: number
  priceBeforeTax: number
  quotedPrice: number
}

export const summarizeProjectCosts = (
  joints: Joint[],
  cost: CostParams,
): ProjectCostSummary => {
  const usage = sumResults(
    joints.flatMap(j =>
      j.operations.map(op => {
        const r = operationResult(j, op)
        return {
          ...r,
          cost: 0,
        }
      }),
    ),
  )

  let materialCost = 0
  let auxCost = 0
  let laborCost = 0
  let equipmentCost = 0

  joints.forEach(joint => {
    joint.operations.forEach(operation => {
      const row = operationCostBreakdown(joint, operation, cost)
      materialCost += row.materialCost
      auxCost += row.auxCost
      laborCost += row.laborCost
      equipmentCost += row.equipmentCost
    })
  })

  const directCost = materialCost + auxCost + laborCost + equipmentCost
  const priceBeforeTax = directCost * (1 + cost.profitMargin)
  const quotedPrice = priceBeforeTax * (1 + cost.taxRate)

  return {
    deposit: usage.deposit,
    suggested: usage.suggested,
    flux: usage.enterpriseFlux,
    gasVolumeL: usage.gasVolumeL,
    materialCost,
    auxCost,
    laborCost,
    equipmentCost,
    directCost,
    priceBeforeTax,
    quotedPrice,
  }
}

export const jointsToQuotePayload = (
  joints: Joint[],
  cost: CostParams,
  meta: { projectName?: string; customer?: string } = {},
) => ({
  project_name: meta.projectName,
  customer: meta.customer,
  cost_params: {
    labor_rate_per_hour: cost.laborRatePerHour,
    overhead_rate: cost.overheadRate,
    gas_price_per_l: cost.gasPricePerL,
    machine_power_kw: cost.machinePowerKw,
    electricity_price: cost.electricityPrice,
    daily_depreciation: cost.dailyDepreciation,
    daily_work_hours: cost.dailyWorkHours,
    profit_margin: cost.profitMargin,
    tax_rate: cost.taxRate,
  },
  joints: joints.map(joint => ({
    name: joint.name,
    groove: joint.groove,
    thickness_mm: joint.thickness,
    included_angle_deg: joint.angle,
    root_gap_mm: joint.gap,
    root_face_mm: joint.rootFace,
    radius_mm: joint.radius,
    upper_bevel_height_mm: joint.upperHeight,
    leg_size_mm: joint.legSize,
    reinforcement_mm: joint.reinforcement,
    back_gouge_depth_mm: joint.backGougeDepth,
    gouge_opening_width_mm: joint.gougeOpeningWidth,
    face_extra_each_side_mm: joint.faceExtra,
    fill_factor: joint.fillFactor,
    length_mm: joint.length,
    operations: joint.operations.map(op => ({
      role: op.role,
      name: op.name,
      method: op.method,
      material: op.material,
      density_g_cm3: op.density,
      deposition_efficiency: op.efficiency,
      unit_price: op.unitPrice,
      flux_wire_ratio: op.fluxRatio,
      flux_unit_price: cost.fluxUnitPrice,
      custom_area_mm2: op.customArea,
      stub_loss_ratio: op.stubLoss,
      spatter_loss_ratio: op.spatterLoss,
      flux_loss_ratio: op.fluxLoss,
      enterprise_correction_factor: op.enterpriseFactor,
      package_size_kg: op.packageSizeKg,
      deposition_rate_kg_h: op.depositionRateKgH,
      arc_time_ratio: op.arcTimeRatio,
      gas_flow_l_min: op.gasFlowLMin,
    })),
  })),
})

export const exportQuoteCsv = (
  joints: Joint[],
  cost: CostParams,
  summary: ProjectCostSummary,
  projectName = '项目',
) => {
  const lines = [
    ['项目', projectName],
    ['材料费', summary.materialCost.toFixed(2)],
    ['气体辅助费', summary.auxCost.toFixed(2)],
    ['人工费', summary.laborCost.toFixed(2)],
    ['设备/电费', summary.equipmentCost.toFixed(2)],
    ['直接成本', summary.directCost.toFixed(2)],
    ['含税报价', summary.quotedPrice.toFixed(2)],
    [],
    [
      '焊缝',
      '工序',
      '焊材',
      '建议领用kg',
      '材料费',
      '人工费',
      '设备费',
      '气体费',
      '小计',
    ],
  ]

  joints.forEach(joint => {
    joint.operations.forEach(operation => {
      const row = operationCostBreakdown(joint, operation, cost)
      const usage = operationResult(joint, operation)
      lines.push([
        joint.name,
        operation.name,
        operation.material,
        usage.suggested.toFixed(3),
        row.materialCost.toFixed(2),
        row.laborCost.toFixed(2),
        row.equipmentCost.toFixed(2),
        row.auxCost.toFixed(2),
        row.subtotal.toFixed(2),
      ])
    })
  })

  const blob = new Blob([`\uFEFF${lines.map(line => line.join(',')).join('\n')}`], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${projectName}-焊接成本报价.csv`
  link.click()
  URL.revokeObjectURL(url)
}
