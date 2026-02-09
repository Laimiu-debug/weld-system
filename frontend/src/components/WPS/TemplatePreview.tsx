/**
 * 模板预览组件
 * 实时预览基于模块生成的表单
 */
import React, { useState } from 'react'
import { Card, Descriptions, Tag, Empty, Space, Typography, Row, Col, Table, FormInstance, Button } from 'antd'
import { EyeOutlined, EyeInvisibleOutlined } from '@ant-design/icons'
import { ModuleInstance, FieldDefinition } from '@/types/wpsModules'
import { getModuleById, getModuleByIdAndType } from '@/constants/wpsModules'
import { WPSTemplate } from '@/services/wpsTemplates'

const { Text } = Typography

interface TemplatePreviewProps {
  template: WPSTemplate
  form?: FormInstance
  defaultCollapsed?: boolean  // 默认是否折叠
  moduleType?: 'wps' | 'pqr' | 'ppqr'  // 模块类型
}

const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  template,
  form,
  defaultCollapsed = false,
  moduleType = 'wps'
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)
  // 切换折叠状态
  const toggleCollapsed = () => {
    setCollapsed(!collapsed)
  }

  // 渲染标题栏
  const renderTitle = () => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Space>
        <EyeOutlined />
        <span>模板预览</span>
      </Space>
      <Button
        type="text"
        size="small"
        icon={collapsed ? <EyeOutlined /> : <EyeInvisibleOutlined />}
        onClick={toggleCollapsed}
      >
        {collapsed ? '展开' : '折叠'}
      </Button>
    </div>
  )

  // 添加 null 检查
  if (!template) {
    return (
      <Card
        title={renderTitle()}
        size="small"
      >
        <Empty description="未选择模板" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    )
  }

  const modules = template.module_instances || []

  if (!modules || modules.length === 0) {
    return (
      <Card
        title={renderTitle()}
        size="small"
      >
        <Empty description="添加模块后可预览表单" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    )
  }

  const getFieldTypeName = (type: string) => {
    const typeMap: Record<string, string> = {
      text: '文本',
      number: '数字',
      select: '下拉选择',
      date: '日期',
      textarea: '多行文本',
      file: '文件',
      table: '表格'
    }
    return typeMap[type] || type
  }

  // 渲染表格字段
  const renderTableField = (field: FieldDefinition) => {
    if (!field.tableDefinition || !field.tableDefinition.rows) {
      return <Text type="secondary">表格未定义</Text>
    }

    const { rows } = field.tableDefinition

    // 计算表格的列数
    let maxCols = 0
    rows.forEach(row => {
      let colCount = 0
      row.cells.forEach(cell => {
        colCount += (cell.colspan || 1)
      })
      maxCols = Math.max(maxCols, colCount)
    })

    return (
      <div style={{ marginTop: 8 }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            border: '1px solid #d9d9d9',
            fontSize: 12
          }}
        >
          <tbody>
            {rows.map((row, rowIndex) => {
              // 计算哪些列位置被之前行的跨行单元格占用
              const occupiedColumns = new Set<number>()

              for (let prevRowIndex = 0; prevRowIndex < rowIndex; prevRowIndex++) {
                const prevRow = rows[prevRowIndex]
                let currentCol = 0

                prevRow.cells.forEach((prevCell) => {
                  const rowspan = prevCell.rowspan || 1
                  const colspan = prevCell.colspan || 1

                  if (prevRowIndex + rowspan > rowIndex) {
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

                renderedCells.push(
                  <td
                    key={cellIndex}
                    rowSpan={rowspan}
                    colSpan={colspan}
                    style={{
                      border: '1px solid #d9d9d9',
                      padding: '6px 8px',
                      backgroundColor: row.isHeader ? '#fafafa' : '#fff',
                      fontWeight: row.isHeader ? 500 : 'normal',
                      textAlign: 'center'
                    }}
                  >
                    <div>
                      <div style={{ marginBottom: 2 }}>{cell.label || '-'}</div>
                      {!row.isHeader && (
                        <Tag color="blue" style={{ fontSize: 10, margin: 0 }}>
                          {getFieldTypeName(cell.type)}
                        </Tag>
                      )}
                    </div>
                  </td>
                )

                currentCol += colspan
              })

              return <tr key={rowIndex}>{renderedCells}</tr>
            })}
          </tbody>
        </table>
      </div>
    )
  }

  // 将模块按行分组（根据 rowIndex）
  const groupModulesIntoRows = () => {
    const rowsMap = new Map<number, ModuleInstance[]>()

    modules.forEach((module) => {
      const rowIdx = module.rowIndex ?? 0
      if (!rowsMap.has(rowIdx)) {
        rowsMap.set(rowIdx, [])
      }
      rowsMap.get(rowIdx)!.push(module)
    })

    // 按行索引排序，并在每行内按列索引排序
    const rows: ModuleInstance[][] = []
    const sortedRowIndices = Array.from(rowsMap.keys()).sort((a, b) => a - b)

    sortedRowIndices.forEach((rowIdx) => {
      const rowModules = rowsMap.get(rowIdx)!
      rowModules.sort((a, b) => (a.columnIndex ?? 0) - (b.columnIndex ?? 0))
      rows.push(rowModules)
    })

    return rows
  }

  const rows = groupModulesIntoRows()

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <EyeOutlined />
            <span>模板预览</span>
            <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
              (共 {modules.length} 个模块)
            </Text>
          </Space>
          <Button
            type="text"
            size="small"
            icon={collapsed ? <EyeOutlined /> : <EyeInvisibleOutlined />}
            onClick={toggleCollapsed}
          >
            {collapsed ? '展开' : '折叠'}
          </Button>
        </div>
      }
      size="small"
      styles={{ body: { padding: collapsed ? '0' : '12px' } }}
    >
      {!collapsed && (
        <>
          {/* 按行显示模块预览 */}
          {rows.map((row, rowIndex) => {
        const columnsInRow = row.length
        const columnSpan = Math.floor(24 / columnsInRow)

        return (
          <Row key={rowIndex} gutter={8} style={{ marginBottom: 8 }}>
            {row.map((instance) => {
              const module = getModuleByIdAndType(instance.moduleId, moduleType)
              if (!module) return null

              const displayName = instance.customName || module.name
              const fieldCount = Object.keys(module.fields).length

              return (
                <Col key={instance.instanceId} span={columnSpan}>
                  <Card
                    size="small"
                    title={
                      <Space>
                        <Text strong style={{ fontSize: 13 }}>{displayName}</Text>
                        <Tag color="blue" style={{ fontSize: 11 }}>
                          {fieldCount} 个字段
                        </Tag>
                      </Space>
                    }
                    style={{ marginBottom: 8 }}
                    styles={{ body: { padding: '8px' } }}
                  >
                    {Object.entries(module.fields).map(([key, field]) => {
                      // 如果是表格类型,使用特殊渲染
                      if (field.type === 'table') {
                        return (
                          <div key={key} style={{ marginBottom: 12 }}>
                            <div style={{ marginBottom: 8, fontWeight: 500, fontSize: 13 }}>
                              {field.label}
                              {field.required && <Text type="danger"> *</Text>}
                            </div>
                            {renderTableField(field)}
                          </div>
                        )
                      }

                      // 普通字段使用 Descriptions 渲染
                      return null
                    })}

                    {/* 普通字段使用 Descriptions 渲染 */}
                    {Object.values(module.fields).some(f => f.type !== 'table') && (
                      <Descriptions
                        size="small"
                        column={1}
                        bordered
                        labelStyle={{ width: 120, backgroundColor: '#fafafa', fontSize: 12 }}
                        contentStyle={{ fontSize: 12 }}
                      >
                        {Object.entries(module.fields)
                          .filter(([_, field]) => field.type !== 'table')
                          .map(([key, field]) => (
                            <Descriptions.Item
                              key={key}
                              label={
                                <Space size={4}>
                                  <span>{field.label}</span>
                                  {field.required && <Text type="danger">*</Text>}
                                </Space>
                              }
                            >
                              <Space wrap size={4}>
                                <Tag color="blue" style={{ fontSize: 11 }}>{getFieldTypeName(field.type)}</Tag>
                                {field.unit && <Tag color="green" style={{ fontSize: 11 }}>单位: {field.unit}</Tag>}
                                {field.readonly && <Tag color="orange" style={{ fontSize: 11 }}>只读</Tag>}
                              </Space>
                            </Descriptions.Item>
                          ))}
                      </Descriptions>
                    )}
                  </Card>
                </Col>
              )
            })}
          </Row>
        )
      })}

      <div style={{ marginTop: 12, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text strong style={{ fontSize: 12 }}>
            统计信息
          </Text>
          <Space wrap>
            <Tag color="blue">模块数: {modules.length}</Tag>
            <Tag color="green">
              总字段数:{' '}
              {modules.reduce((sum, instance) => {
                const module = getModuleByIdAndType(instance.moduleId, moduleType)
                return sum + (module ? Object.keys(module.fields).length : 0)
              }, 0)}
            </Tag>
            <Tag color="orange">
              必填字段:{' '}
              {modules.reduce((sum, instance) => {
                const module = getModuleByIdAndType(instance.moduleId, moduleType)
                if (!module) return sum
                return (
                  sum +
                  Object.values(module.fields).filter((f) => f.required).length
                )
              }, 0)}
            </Tag>
          </Space>
        </Space>
      </div>
        </>
      )}
    </Card>
  )
}

export default TemplatePreview

