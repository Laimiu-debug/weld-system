/**
 * 表格字段编辑器
 * 用于创建复杂的多行多列表格模块
 */
import React, { useState } from 'react'
import {
  Modal,
  Button,
  Table,
  Input,
  Select,
  InputNumber,
  Space,
  Popconfirm,
  message,
  Card,
  Row,
  Col,
  Divider
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  MergeCellsOutlined
} from '@ant-design/icons'
import { TableDefinition, TableRowDefinition, TableCellDefinition } from '@/types/wpsModules'

const { Option } = Select

interface TableFieldEditorProps {
  value?: TableDefinition
  onChange?: (value: TableDefinition) => void
}

interface CellEditorProps {
  cell: TableCellDefinition
  onChange: (cell: TableCellDefinition) => void
  onClose: () => void
}

const CellEditor: React.FC<CellEditorProps> = ({ cell, onChange, onClose }) => {
  return (
    <Modal
      title="编辑单元格"
      open={true}
      onOk={onClose}
      onCancel={onClose}
      width={700}
      okText="完成"
      cancelText="取消"
    >
      <Row gutter={16}>
        <Col span={12}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>标签:</label>
            <Input
              value={cell.label}
              onChange={(e) => onChange({ ...cell, label: e.target.value })}
              placeholder="单元格标签"
              size="large"
            />
          </div>
        </Col>
        <Col span={12}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>类型:</label>
            <Select
              value={cell.type}
              onChange={(value) => onChange({ ...cell, type: value })}
              style={{ width: '100%' }}
              size="large"
            >
              <Option value="text">文本</Option>
              <Option value="number">数字</Option>
              <Option value="select">下拉选择</Option>
              <Option value="date">日期</Option>
              <Option value="textarea">多行文本</Option>
            </Select>
          </div>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>单位:</label>
            <Input
              value={cell.unit}
              onChange={(e) => onChange({ ...cell, unit: e.target.value })}
              placeholder="如: mm, °C"
              size="large"
            />
          </div>
        </Col>
        <Col span={8}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>跨行:</label>
            <InputNumber
              value={cell.rowspan || 1}
              onChange={(value) => onChange({ ...cell, rowspan: value || 1 })}
              min={1}
              max={10}
              style={{ width: '100%' }}
              size="large"
            />
          </div>
        </Col>
        <Col span={8}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>跨列:</label>
            <InputNumber
              value={cell.colspan || 1}
              onChange={(value) => onChange({ ...cell, colspan: value || 1 })}
              min={1}
              max={10}
              style={{ width: '100%' }}
              size="large"
            />
          </div>
        </Col>
      </Row>

      {cell.type === 'select' && (
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>选项 (逗号分隔):</label>
          <Input
            value={cell.options?.join(', ')}
            onChange={(e) =>
              onChange({
                ...cell,
                options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean)
              })
            }
            placeholder="选项1, 选项2, 选项3"
            size="large"
          />
        </div>
      )}
    </Modal>
  )
}

const TableFieldEditor: React.FC<TableFieldEditorProps> = ({ value, onChange }) => {
  const [tableData, setTableData] = useState<TableDefinition>(
    value || {
      rows: [
        {
          isHeader: true,
          cells: [
            { label: '列1', type: 'text' },
            { label: '列2', type: 'text' }
          ]
        },
        {
          cells: [
            { label: '', type: 'text' },
            { label: '', type: 'text' }
          ]
        }
      ],
      bordered: true,
      size: 'small'
    }
  )

  const [editingCell, setEditingCell] = useState<{
    rowIndex: number
    cellIndex: number
  } | null>(null)

  const handleTableChange = (newTableData: TableDefinition) => {
    setTableData(newTableData)
    onChange?.(newTableData)
  }

  const handleAddRow = () => {
    const colCount = tableData.rows[0]?.cells.length || 2
    const newRow: TableRowDefinition = {
      cells: Array(colCount).fill(null).map(() => ({ label: '', type: 'text' }))
    }
    handleTableChange({
      ...tableData,
      rows: [...tableData.rows, newRow]
    })
  }

  const handleAddColumn = () => {
    const newRows: TableRowDefinition[] = tableData.rows.map((row) => ({
      ...row,
      cells: [...row.cells, { label: '', type: 'text' as const }]
    }))
    handleTableChange({
      ...tableData,
      rows: newRows
    })
  }

  const handleDeleteRow = (rowIndex: number) => {
    if (tableData.rows.length <= 1) {
      message.warning('至少保留一行')
      return
    }
    const newRows = tableData.rows.filter((_, i) => i !== rowIndex)
    handleTableChange({
      ...tableData,
      rows: newRows
    })
  }

  const handleDeleteColumn = (cellIndex: number) => {
    if (tableData.rows[0]?.cells.length <= 1) {
      message.warning('至少保留一列')
      return
    }
    const newRows = tableData.rows.map((row) => ({
      ...row,
      cells: row.cells.filter((_, i) => i !== cellIndex)
    }))
    handleTableChange({
      ...tableData,
      rows: newRows
    })
  }

  const handleCellChange = (rowIndex: number, cellIndex: number, cell: TableCellDefinition) => {
    const newRows = [...tableData.rows]
    newRows[rowIndex].cells[cellIndex] = cell
    handleTableChange({
      ...tableData,
      rows: newRows
    })
  }

  const handleToggleHeader = (rowIndex: number) => {
    const newRows = [...tableData.rows]
    newRows[rowIndex].isHeader = !newRows[rowIndex].isHeader
    handleTableChange({
      ...tableData,
      rows: newRows
    })
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<PlusOutlined />} onClick={handleAddRow} size="small">
          添加行
        </Button>
        <Button icon={<PlusOutlined />} onClick={handleAddColumn} size="small">
          添加列
        </Button>
      </Space>

      <div style={{ border: '1px solid #d9d9d9', borderRadius: 4, padding: 16, backgroundColor: '#fafafa' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {tableData.rows.map((row, rowIndex) => {
              // 计算哪些列位置被之前行的跨行单元格占用
              const occupiedColumns = new Set<number>()

              // 检查之前的行是否有跨行到当前行的单元格
              for (let prevRowIndex = 0; prevRowIndex < rowIndex; prevRowIndex++) {
                const prevRow = tableData.rows[prevRowIndex]
                let currentCol = 0

                prevRow.cells.forEach((prevCell) => {
                  const rowspan = prevCell.rowspan || 1
                  const colspan = prevCell.colspan || 1

                  // 如果这个单元格跨行到当前行
                  if (prevRowIndex + rowspan > rowIndex) {
                    // 标记被占用的列位置
                    for (let i = 0; i < colspan; i++) {
                      occupiedColumns.add(currentCol + i)
                    }
                  }

                  currentCol += colspan
                })
              }

              // 渲染当前行的单元格
              const renderedCells: React.ReactNode[] = []
              let currentCol = 0

              row.cells.forEach((cell, cellIndex) => {
                const colspan = cell.colspan || 1
                const rowspan = cell.rowspan || 1

                // 跳过被占用的列位置
                while (occupiedColumns.has(currentCol)) {
                  currentCol++
                }

                const isEditing = editingCell?.rowIndex === rowIndex && editingCell?.cellIndex === cellIndex

                renderedCells.push(
                  <td
                    key={cellIndex}
                    rowSpan={rowspan}
                    colSpan={colspan}
                    style={{
                      border: '1px solid #d9d9d9',
                      padding: '8px',
                      backgroundColor: row.isHeader ? '#fafafa' : '#fff',
                      fontWeight: row.isHeader ? 'bold' : 'normal',
                      position: 'relative',
                      minWidth: 100,
                      minHeight: 40
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ flex: 1 }}>
                        {cell.label || <span style={{ color: '#ccc' }}>(空)</span>}
                        {cell.unit && <span style={{ color: '#999', marginLeft: 4 }}>({cell.unit})</span>}
                        <div style={{ fontSize: 11, color: '#999' }}>
                          {cell.type}
                          {(cell.rowspan && cell.rowspan > 1) && ` | 跨${cell.rowspan}行`}
                          {(cell.colspan && cell.colspan > 1) && ` | 跨${cell.colspan}列`}
                        </div>
                      </div>
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => setEditingCell({ rowIndex, cellIndex })}
                      />
                    </div>

                    {isEditing && (
                      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, backgroundColor: '#fff', border: '2px solid #1890ff', padding: 8 }}>
                        <CellEditor
                          cell={cell}
                          onChange={(newCell) => handleCellChange(rowIndex, cellIndex, newCell)}
                          onClose={() => setEditingCell(null)}
                        />
                      </div>
                    )}
                  </td>
                )

                currentCol += colspan
              })

              return (
                <tr key={rowIndex}>
                  {renderedCells}
                  <td style={{ border: 'none', padding: '0 8px' }}>
                    <Space size="small">
                      <Button
                        type="text"
                        size="small"
                        onClick={() => handleToggleHeader(rowIndex)}
                        title={row.isHeader ? '取消表头' : '设为表头'}
                      >
                        {row.isHeader ? '表头' : '数据'}
                      </Button>
                      <Popconfirm
                        title="确定删除此行?"
                        onConfirm={() => handleDeleteRow(rowIndex)}
                      >
                        <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                      </Popconfirm>
                    </Space>
                  </td>
                </tr>
              )
            })}
            <tr>
              {tableData.rows[0]?.cells.map((_, cellIndex) => (
                <td key={cellIndex} style={{ border: 'none', padding: '8px 0', textAlign: 'center' }}>
                  <Popconfirm
                    title="确定删除此列?"
                    onConfirm={() => handleDeleteColumn(cellIndex)}
                  >
                    <Button type="text" danger size="small" icon={<DeleteOutlined />}>
                      删除列
                    </Button>
                  </Popconfirm>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 16, fontSize: 12, color: '#999' }}>
        提示: 点击单元格右侧的编辑按钮可以设置单元格属性,包括跨行跨列
      </div>
    </div>
  )
}

export default TableFieldEditor

