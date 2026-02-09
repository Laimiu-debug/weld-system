/**
 * 模块数据转TipTap HTML工具函数
 * 将模块化数据转换为TipTap编辑器可用的HTML格式
 */
import { ModuleInstance } from '@/types/wpsModules'
import { getModuleByIdAndType } from '@/constants/wpsModules'
import dayjs from 'dayjs'

/**
 * 将模块化数据转换为TipTap兼容的HTML
 * 支持多列布局，完全按照模板的rowIndex和columnIndex排列
 */
export const convertModulesToTipTapHTML = (
  modules: ModuleInstance[],
  modulesData: Record<string, any>,
  documentInfo: {
    title: string
    number: string
    revision: string
  },
  moduleType: 'wps' | 'pqr' | 'ppqr' = 'wps'
): string => {
  let html = ''

  // 文档标题
  html += `<h1 style="text-align: center;">${documentInfo.title}</h1>`
  html += `<p style="text-align: center; font-size: 14px; color: #666;">文档编号: ${documentInfo.number} | 版本: ${documentInfo.revision}</p>`
  html += `<hr />`

  // 按行分组模块
  const rowGroups = new Map<number, ModuleInstance[]>()
  modules.forEach(instance => {
    const rowIndex = instance.rowIndex ?? 0
    if (!rowGroups.has(rowIndex)) {
      rowGroups.set(rowIndex, [])
    }
    rowGroups.get(rowIndex)!.push(instance)
  })

  // 按行索引排序
  const sortedRows = Array.from(rowGroups.entries()).sort((a, b) => a[0] - b[0])

  // 遍历每一行
  sortedRows.forEach(([rowIndex, rowModules]) => {
    // 按列索引排序
    const sortedModules = rowModules.sort((a, b) => (a.columnIndex ?? 0) - (b.columnIndex ?? 0))

    const columnCount = sortedModules.length

    if (columnCount === 1) {
      // 单列：全宽显示
      const instance = sortedModules[0]
      html += generateModuleHTML(instance, modulesData, moduleType, '100%')
    } else {
      // 多列：使用表格布局
      const columnWidth = `${Math.floor(100 / columnCount)}%`

      html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 16px; border: none;">`
      html += `<tbody><tr style="vertical-align: top;">`

      sortedModules.forEach((instance, index) => {
        html += `<td style="width: ${columnWidth}; padding: 0 ${index < sortedModules.length - 1 ? '8px' : '0'} 0 0; border: none; ${index < sortedModules.length - 1 ? 'border-right: 2px solid #e0e0e0;' : ''}">`
        html += generateModuleHTML(instance, modulesData, moduleType, '100%', false)
        html += `</td>`
      })

      html += `</tr></tbody>`
      html += `</table>`
    }
  })

  return html
}

/**
 * 生成单个模块的HTML
 */
function generateModuleHTML(
  instance: ModuleInstance,
  modulesData: Record<string, any>,
  moduleType: 'wps' | 'pqr' | 'ppqr',
  width: string = '100%',
  addBottomMargin: boolean = true
): string {
  let html = ''

  const moduleData = modulesData[instance.instanceId]

  // 获取模块定义
  const module = getModuleByIdAndType(moduleData?.moduleId || instance.moduleId, moduleType)

  // 优先使用customName，其次使用模块定义的name，最后使用默认值
  const moduleName = instance.customName || moduleData?.customName || module?.name || '模块'

  // 模块标题
  html += `<h3 style="font-size: 14px; font-weight: bold; margin: 8px 0 4px 0; padding: 4px 8px; background-color: #f5f5f5; border-left: 3px solid #1890ff;">${moduleName}</h3>`

  if (!module || !module.fields) {
    html += `<p style="color: #999; font-size: 12px; padding: 8px;">模块定义未找到</p>`
    return html
  }

  // 特殊处理：焊接接头示意图生成器 V4 - 只显示生成的图片
  if (module.id === 'weld_joint_diagram_v4') {
    const generatedDiagram = moduleData?.data?.generated_diagram
    if (generatedDiagram && Array.isArray(generatedDiagram) && generatedDiagram.length > 0) {
      html += `<div style="text-align: center; padding: 16px; ${addBottomMargin ? 'margin-bottom: 16px;' : ''}">`
      generatedDiagram.forEach((img, index) => {
        const imgSrc = img.url || img.thumbUrl || ''
        console.log(`[generateModuleHTML] V4示意图图片${index}:`, imgSrc.substring(0, 100))

        if (imgSrc) {
          // 验证base64图片数据完整性
          if (imgSrc.startsWith('data:image')) {
            const [header, base64Data] = imgSrc.split(',')
            if (!base64Data || base64Data.length === 0) {
              console.warn(`[generateModuleHTML] V4示意图${index} base64数据不完整`)
              html += `<div style="color: #999; font-size: 12px; margin: 8px 0;">示意图${index + 1}数据不完整</div>`
            } else {
              html += `<img src="${imgSrc}" style="max-width: 100%; height: auto; border: 1px solid #e0e0e0; border-radius: 4px; margin: 8px 0;" alt="${img.name || `焊接接头示意图${index + 1}`}" onerror="console.error('V4示意图图片加载失败:', this.src);" />`
            }
          } else {
            html += `<img src="${imgSrc}" style="max-width: 100%; height: auto; border: 1px solid #e0e0e0; border-radius: 4px; margin: 8px 0;" alt="${img.name || `焊接接头示意图${index + 1}`}" onerror="console.error('V4示意图图片加载失败:', this.src);" />`
          }
        } else {
          console.warn(`[generateModuleHTML] V4示意图${index}没有URL`)
          html += `<div style="color: #999; font-size: 12px; margin: 8px 0;">示意图${index + 1}缺失</div>`
        }
      })
      html += `</div>`
    } else {
      html += `<p style="color: #999; font-size: 12px; padding: 8px; text-align: center; ${addBottomMargin ? 'margin-bottom: 16px;' : ''}">暂无示意图</p>`
    }
    return html
  }

  // 创建表格 - 显示所有字段（包括未填写的）
  html += `<table style="width: ${width}; border-collapse: collapse; font-size: 12px; ${addBottomMargin ? 'margin-bottom: 16px;' : ''}">`
  html += `<tbody>`

  // 遍历模块定义中的所有字段（而不是只遍历已填写的）
  Object.entries(module.fields).forEach(([fieldKey, fieldDef]) => {
    const label = fieldDef.label || fieldKey
    const value = moduleData?.data?.[fieldKey]
    const formattedValue = formatFieldValue(value, fieldDef)

    html += `
      <tr style="border-bottom: 1px solid #f0f0f0;">
        <td style="width: 35%; padding: 6px 8px; font-weight: 500; background-color: #fafafa; border-right: 1px solid #f0f0f0;">
          ${label}${fieldDef.unit ? ` <span style="color: #999; font-size: 11px;">(${fieldDef.unit})</span>` : ''}
        </td>
        <td style="width: 65%; padding: 6px 8px;">
          ${formattedValue}
        </td>
      </tr>
    `
  })

  html += `</tbody>`
  html += `</table>`

  return html
}

/**
 * 格式化字段值
 */
const formatFieldValue = (value: any, fieldDef?: any): string => {
  if (value === null || value === undefined || value === '') return '-'

  // 图片字段
  if (fieldDef?.type === 'image' && Array.isArray(value)) {
    if (value.length === 0) return '-'

    console.log('[formatFieldValue] 处理图片字段:', value)

    return value.map((img, index) => {
      const imgSrc = img.url || img.thumbUrl || ''
      console.log('[formatFieldValue] 图片URL:', imgSrc.substring(0, 100))

      if (!imgSrc) {
        console.warn('[formatFieldValue] 图片没有URL:', img)
        return `<span style="color: #999;">[图片${index + 1}URL缺失]</span>`
      }

      // 验证base64图片数据完整性
      if (imgSrc.startsWith('data:image')) {
        const [header, base64Data] = imgSrc.split(',')
        if (!base64Data || base64Data.length === 0) {
          console.warn('[formatFieldValue] base64数据不完整:', img)
          return `<span style="color: #999;">[图片${index + 1}数据不完整]</span>`
        }
      }

      return `<img src="${imgSrc}" style="max-width: 100%; height: auto; margin: 8px 0; border: 1px solid #e0e0e0; border-radius: 4px;" alt="${img.name || `图片${index + 1}`}" onerror="console.error('图片加载失败:', this.src);" />`
    }).join('<br />')
  }
  
  // 表格字段（嵌套表格）
  if (fieldDef?.type === 'table' && typeof value === 'object') {
    return generateNestedTableHTML(value, fieldDef.tableDefinition)
  }
  
  // 日期字段
  if (fieldDef?.type === 'date') {
    try {
      return dayjs(value).format('YYYY-MM-DD')
    } catch {
      return String(value)
    }
  }
  
  // 复选框
  if (fieldDef?.type === 'checkbox') {
    return value ? '是' : '否'
  }
  
  // 选择框（数组）
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  
  // 对象
  if (typeof value === 'object') {
    try {
      return `<pre>${JSON.stringify(value, null, 2)}</pre>`
    } catch {
      return String(value)
    }
  }
  
  return String(value)
}

/**
 * 生成嵌套表格HTML
 */
const generateNestedTableHTML = (data: any, tableDef: any): string => {
  if (!tableDef || !tableDef.rows) return '-'
  
  let html = '<table style="width: 100%; border-collapse: collapse; margin: 5px 0;">'
  
  tableDef.rows.forEach((row: any, rowIndex: number) => {
    html += '<tr>'
    row.cells.forEach((cell: any, cellIndex: number) => {
      const cellKey = `cell_${rowIndex}_${cellIndex}`
      const cellValue = data[cellKey] || (row.isHeader ? cell.label : '-')
      const tag = row.isHeader ? 'th' : 'td'
      
      const styles = [
        'border: 1px solid #000',
        'padding: 4px 8px',
        row.isHeader ? 'background-color: #f0f0f0' : '',
        row.isHeader ? 'font-weight: bold' : '',
        'text-align: left'
      ].filter(Boolean).join('; ')
      
      html += `<${tag} 
        rowspan="${cell.rowspan || 1}" 
        colspan="${cell.colspan || 1}"
        style="${styles}"
      >`
      html += cellValue
      html += `</${tag}>`
    })
    html += '</tr>'
  })
  
  html += '</table>'
  return html
}

/**
 * 解析HTML提取模块数据（用于从文档模式切换回表单模式）
 * 注意：这个功能比较复杂，可能会丢失部分格式信息
 */
export const parseHTMLToModules = (html: string): Record<string, any> => {
  // TODO: 实现HTML解析逻辑
  // 这个功能比较复杂，暂时返回空对象
  console.warn('HTML解析功能尚未实现')
  return {}
}

/**
 * 生成默认的文档HTML模板
 */
export const generateDefaultDocumentHTML = (
  documentInfo: {
    title: string
    number: string
    revision: string
  }
): string => {
  return `
    <h1>${documentInfo.title}</h1>
    <p style="text-align: center;">文档编号: ${documentInfo.number} | 版本: ${documentInfo.revision}</p>
    <hr />
    <h2>基本信息</h2>
    <table>
      <tbody>
        <tr>
          <td style="width: 30%; font-weight: bold;">焊接工艺</td>
          <td style="width: 70%;">-</td>
        </tr>
        <tr>
          <td style="width: 30%; font-weight: bold;">标准</td>
          <td style="width: 70%;">-</td>
        </tr>
      </tbody>
    </table>
    <p></p>
    <h2>材料信息</h2>
    <table>
      <tbody>
        <tr>
          <td style="width: 30%; font-weight: bold;">母材</td>
          <td style="width: 70%;">-</td>
        </tr>
        <tr>
          <td style="width: 30%; font-weight: bold;">焊材</td>
          <td style="width: 70%;">-</td>
        </tr>
      </tbody>
    </table>
    <p></p>
  `
}

