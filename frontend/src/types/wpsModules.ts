/**
 * WPS字段模块类型定义
 * 用于模块化拖拽创建模板
 */

/**
 * 表格单元格定义
 */
export interface TableCellDefinition {
  label: string
  type: 'text' | 'number' | 'select' | 'date' | 'textarea'
  unit?: string
  options?: string[]
  default?: any
  required?: boolean
  readonly?: boolean
  placeholder?: string
  min?: number
  max?: number
  rowspan?: number  // 跨行
  colspan?: number  // 跨列
}

/**
 * 表格行定义
 */
export interface TableRowDefinition {
  cells: TableCellDefinition[]
  isHeader?: boolean  // 是否为表头行
}

/**
 * 表格定义
 */
export interface TableDefinition {
  rows: TableRowDefinition[]
  bordered?: boolean
  size?: 'small' | 'middle' | 'large'
}

/**
 * 选项定义
 */
export interface OptionDefinition {
  label: string
  value: string | number | boolean
}

/**
 * 字段定义
 */
export interface FieldDefinition {
  label: string
  type: 'text' | 'number' | 'select' | 'date' | 'textarea' | 'file' | 'table' | 'image' | 'checkbox'
  unit?: string
  options?: string[] | OptionDefinition[]  // 支持字符串数组或对象数组
  default?: any
  defaultValue?: any  // 别名，与 default 相同
  required?: boolean
  readonly?: boolean
  placeholder?: string
  min?: number
  max?: number
  step?: number  // 数字输入步长
  multiple?: boolean
  tableDefinition?: TableDefinition  // 当 type='table' 时使用
  accept?: string  // 当 type='file' 或 'image' 时使用，如 'image/*' 或 '.png,.jpg'
  maxSize?: number  // 最大文件大小（字节）
  description?: string  // 字段描述
  field_id?: string  // 稳定字段ID，字段改名时保持不变
  aliases?: string[]  // 文档中可能出现的别名
  examples?: any[]  // 识别示例
  ai_extract_mode?: 'auto' | 'manual' | 'derived' | 'disabled'
  canonical_field_key?: string  // 平台稳定语义字段
  confidence_threshold?: number
  use_in_rules?: boolean
  condition?: {  // 条件显示
    field: string
    value: any
  }
}

/**
 * 字段模块定义
 */
export interface FieldModule {
  id: string
  name: string
  description: string
  icon: string
  category: 'basic' | 'material' | 'materials' | 'gas' | 'electrical' | 'motion' | 'equipment' | 'calculation' | 'parameters' | 'tests' | 'analysis' | 'evaluation' | 'approval' | 'results' | 'attachments' | 'notes'
  repeatable: boolean  // 是否可重复（用于多层多道焊）
  fields: Record<string, FieldDefinition>
  module_type?: 'wps' | 'pqr' | 'ppqr' | 'common'
  schema_version?: number
}

/**
 * 模块实例（用户拖拽到画布上的模块）
 */
export interface ModuleInstance {
  instanceId: string  // 实例唯一ID
  moduleId: string    // 模块定义ID
  order: number       // 排序
  customName?: string // 自定义名称（用于区分重复的模块，如"第1层"、"第2层"）
  rowIndex?: number   // 所在行索引
  columnIndex?: number // 所在列索引
}

/**
 * 模板配置（基于模块）
 */
export interface ModuleBasedTemplate {
  templateId?: string
  name: string
  description: string
  weldingProcess: string
  standard: string
  
  // 表头字段（用户自定义）
  headerFields: Record<string, FieldDefinition>
  
  // 模块实例列表
  modules: ModuleInstance[]
}

/**
 * 模块分类
 */
export const MODULE_CATEGORIES = {
  basic: { label: '基本信息', color: '#1890ff' },
  material: { label: '材料信息', color: '#52c41a' },
  gas: { label: '气体信息', color: '#13c2c2' },
  electrical: { label: '电气参数', color: '#faad14' },
  motion: { label: '运动参数', color: '#722ed1' },
  equipment: { label: '设备信息', color: '#eb2f96' },
  calculation: { label: '计算结果', color: '#fa8c16' },
} as const
