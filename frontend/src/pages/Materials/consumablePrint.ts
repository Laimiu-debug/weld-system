import type { Joint } from './consumableCalc'
import { geometry, operationResult, sumResults } from './consumableCalc'
import type { CostParams, ProjectCostSummary } from './consumableCost'
import { operationCostBreakdown } from './consumableCost'

const escapeHtml = (value: unknown) => String(value ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#039;')

const money = (value: number) => `¥${value.toFixed(2)}`

const printDocument = (title: string, body: string) => {
  const frame = document.createElement('iframe')
  frame.style.position = 'fixed'
  frame.style.right = '0'
  frame.style.bottom = '0'
  frame.style.width = '0'
  frame.style.height = '0'
  frame.style.border = '0'
  frame.setAttribute('title', 'PDF 打印预览')
  document.body.appendChild(frame)
  const doc = frame.contentDocument
  if (!doc) {
    frame.remove()
    throw new Error('无法创建打印文档')
  }
  doc.open()
  doc.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>
    @page{size:A4;margin:14mm}*{box-sizing:border-box}body{font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;color:#172033;font-size:11px;margin:0}
    h1{font-size:20px;text-align:center;margin:0 0 5mm}.meta{display:flex;justify-content:space-between;color:#536174;margin-bottom:5mm}
    table{border-collapse:collapse;width:100%;page-break-inside:auto}thead{display:table-header-group}tr{page-break-inside:avoid}th,td{border:1px solid #aeb8c5;padding:5px 6px;text-align:right}th{background:#315b8a;color:white}th:first-child,td:first-child,td.text{text-align:left}
    .summary{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:5mm 0}.summary div{border:1px solid #ccd4df;padding:8px}.summary b{display:block;font-size:15px;margin-top:3px}.total{font-size:18px;color:#c75508;text-align:right;margin-top:5mm}.note{color:#66758a;margin-top:5mm}
  </style></head><body>${body}</body></html>`)
  doc.close()
  window.setTimeout(() => {
    frame.contentWindow?.focus()
    frame.contentWindow?.print()
    window.setTimeout(() => frame.remove(), 1000)
  }, 250)
}

export const printUsageReport = (joints: Joint[], projectName = '项目') => {
  const rows = joints.flatMap(joint => joint.operations.map(operation => ({
    joint,
    operation,
    result: operationResult(joint, operation),
  })))
  const totals = sumResults(rows.map(row => row.result))
  const htmlRows = rows.map(({ joint, operation, result }) => `<tr>
    <td>${escapeHtml(joint.name || '未命名焊缝')}</td><td class="text">${escapeHtml(operation.name)}</td><td class="text">${escapeHtml(operation.material)}</td>
    <td>${geometry(joint).total.toFixed(2)}</td><td>${joint.length.toFixed(1)}</td><td>${result.deposit.toFixed(3)}</td><td>${result.suggested.toFixed(3)}</td><td>${result.enterpriseFlux.toFixed(3)}</td><td>${(result.gasVolumeL ?? 0).toFixed(1)}</td>
  </tr>`).join('')
  printDocument(`${projectName}-焊材用量`, `
    <h1>${escapeHtml(projectName)} · 焊材用量计算表</h1>
    <div class="meta"><span>计算口径：weldmoney / P6</span><span>日期：${new Date().toLocaleDateString('zh-CN')}</span></div>
    <div class="summary"><div>熔敷金属<b>${totals.deposit.toFixed(3)} kg</b></div><div>理论消耗<b>${totals.primary.toFixed(3)} kg</b></div><div>建议领用<b>${totals.suggested.toFixed(3)} kg</b></div><div>焊剂<b>${totals.enterpriseFlux.toFixed(3)} kg</b></div></div>
    <table><thead><tr><th>焊缝</th><th>工序</th><th>焊材</th><th>面积 mm²</th><th>长度 mm</th><th>熔敷 kg</th><th>领用 kg</th><th>焊剂 kg</th><th>气体 L</th></tr></thead><tbody>${htmlRows}</tbody></table>
    <div class="note">说明：在系统打印窗口中选择“另存为 PDF”即可生成 PDF 文件。</div>`)
}

export const printQuoteReport = (
  joints: Joint[], cost: CostParams, summary: ProjectCostSummary,
  projectName = '项目', customer = '',
) => {
  const htmlRows = joints.flatMap(joint => joint.operations.map(operation => {
    const row = operationCostBreakdown(joint, operation, cost)
    const usage = operationResult(joint, operation)
    return `<tr><td>${escapeHtml(joint.name || '未命名焊缝')}</td><td class="text">${escapeHtml(operation.name)}</td><td>${usage.suggested.toFixed(3)}</td><td>${money(row.materialCost)}</td><td>${money(row.laborCost)}</td><td>${money(row.auxCost)}</td><td>${money(row.equipmentCost)}</td><td>${money(row.subtotal)}</td></tr>`
  })).join('')
  printDocument(`${projectName}-焊接成本报价单`, `
    <h1>${escapeHtml(projectName)} · 焊接成本报价单</h1>
    <div class="meta"><span>客户：${escapeHtml(customer || '—')}</span><span>日期：${new Date().toLocaleDateString('zh-CN')}</span></div>
    <table><thead><tr><th>焊缝</th><th>工序</th><th>领用 kg</th><th>材料费</th><th>人工费</th><th>辅助费</th><th>设备费</th><th>小计</th></tr></thead><tbody>${htmlRows}</tbody></table>
    <div class="summary"><div>材料费<b>${money(summary.materialCost)}</b></div><div>人工费<b>${money(summary.laborCost)}</b></div><div>辅助费<b>${money(summary.auxCost)}</b></div><div>设备费<b>${money(summary.equipmentCost)}</b></div></div>
    <div class="total">含税报价：<b>${money(summary.quotedPrice)}</b></div>
    <div class="note">成本合计 ${money(summary.directCost)}；税前报价 ${money(summary.priceBeforeTax)}。在系统打印窗口中选择“另存为 PDF”即可生成 PDF 文件。</div>`)
}
