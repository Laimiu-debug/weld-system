/**
 * 表格字段渲染器
 * 用于在模板预览和填写时显示表格
 */
import React from 'react'
import { Input, InputNumber, Select, DatePicker, Table as AntTable } from 'antd'
import { TableDefinition, TableCellDefinition } from '@/types/wpsModules'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

interface TableFieldRendererProps {
  tableDefinition: TableDefinition
  value?: Record<string, any>
  onChange?: (value: Record<string, any>) => void
  readonly?: boolean
}

interface CellRendererProps {
  cell: TableCellDefinition
  rowIndex: number
  cellIndex: number
  value?: any
  onChange?: (value: any) => void
  readonly?: boolean
}

const CellRenderer: React.FC<CellRendererProps> = ({
  cell,
  rowIndex,
  cellIndex,
  value,
  onChange,
  readonly
}) => {
  const cellKey = `cell_${rowIndex}_${cellIndex}`

  if (readonly && !value) {
    return <span style={{ color: '#ccc' }}>-</span>
  }

  switch (cell.type) {
    case 'number':
      return (
        <InputNumber
          value={value}
          onChange={onChange}
          disabled={readonly || cell.readonly}
          placeholder={cell.placeholder}
          min={cell.min}
          max={cell.max}
          style={{ width: '100%' }}
          size="small"
          addonAfter={cell.unit}
        />
      )

    case 'select':
      return (
        <Select
          value={value}
          onChange={onChange}
          disabled={readonly || cell.readonly}
          placeholder={cell.placeholder}
          style={{ width: '100%' }}
          size="small"
        >
          {cell.options?.map((option) => (
            <Option key={option} value={option}>
              {option}
            </Option>
          ))}
        </Select>
      )

    case 'date':
      return (
        <DatePicker
          value={value ? dayjs(value) : undefined}
          onChange={(date) => onChange?.(date?.format('YYYY-MM-DD'))}
          disabled={readonly || cell.readonly}
          placeholder={cell.placeholder}
          style={{ width: '100%' }}
          size="small"
        />
      )

    case 'textarea':
      return (
        <TextArea
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={readonly || cell.readonly}
          placeholder={cell.placeholder}
          rows={2}
          size="small"
        />
      )

    case 'text':
    default:
      return (
        <Input
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={readonly || cell.readonly}
          placeholder={cell.placeholder}
          size="small"
          suffix={cell.unit}
        />
      )
  }
}

const TableFieldRenderer: React.FC<TableFieldRendererProps> = ({
  tableDefinition,
  value = {},
  onChange,
  readonly = false
}) => {
  const handleCellChange = (rowIndex: number, cellIndex: number, cellValue: any) => {
    const cellKey = `cell_${rowIndex}_${cellIndex}`
    const newValue = { ...value, [cellKey]: cellValue }
    onChange?.(newValue)
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          border: tableDefinition.bordered ? '1px solid #d9d9d9' : 'none'
        }}
      >
        <tbody>
          {tableDefinition.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.cells.map((cell, cellIndex) => {
                const cellKey = `cell_${rowIndex}_${cellIndex}`
                const cellValue = value[cellKey]

                return (
                  <td
                    key={cellIndex}
                    rowSpan={cell.rowspan || 1}
                    colSpan={cell.colspan || 1}
                    style={{
                      border: tableDefinition.bordered ? '1px solid #d9d9d9' : 'none',
                      padding: tableDefinition.size === 'small' ? '4px 8px' : '8px 12px',
                      backgroundColor: row.isHeader ? '#fafafa' : '#fff',
                      fontWeight: row.isHeader ? 'bold' : 'normal',
                      verticalAlign: 'middle'
                    }}
                  >
                    {row.isHeader ? (
                      <div style={{ textAlign: 'center' }}>
                        {cell.label}
                        {cell.unit && <span style={{ color: '#999', marginLeft: 4 }}>({cell.unit})</span>}
                        {cell.required && <span style={{ color: 'red' }}>*</span>}
                      </div>
                    ) : (
                      <CellRenderer
                        cell={cell}
                        rowIndex={rowIndex}
                        cellIndex={cellIndex}
                        value={cellValue}
                        onChange={(newValue) => handleCellChange(rowIndex, cellIndex, newValue)}
                        readonly={readonly}
                      />
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TableFieldRenderer

