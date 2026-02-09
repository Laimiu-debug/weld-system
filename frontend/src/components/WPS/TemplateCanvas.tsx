/**
 * 模板画布组件
 * 接收拖拽的模块并显示
 * 支持智能分列：拖拽时显示左中右放置区域
 */
import React, { useState } from 'react'
import { Card, Empty, Button, Space, Input, Modal, Typography, Row, Col } from 'antd'
import {
  DeleteOutlined,
  CopyOutlined,
  EditOutlined,
  DragOutlined
} from '@ant-design/icons'
import { useDroppable } from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { ModuleInstance } from '@/types/wpsModules'
import { getModuleById, getModuleByIdAndType } from '@/constants/wpsModules'

const { Text } = Typography

// 拖放区域组件
interface DropZoneProps {
  rowIndex: number
  position: 'left' | 'center' | 'right'
  columnIndex?: number
  isOver: boolean
}

const DropZone: React.FC<DropZoneProps> = ({ rowIndex, position, columnIndex, isOver }) => {
  const dropId = columnIndex !== undefined
    ? `drop-${rowIndex}-${position}-${columnIndex}`
    : `drop-${rowIndex}-${position}`

  const { setNodeRef } = useDroppable({
    id: dropId,
    data: { rowIndex, position, columnIndex }
  })

  return (
    <div
      ref={setNodeRef}
      style={{
        width: '100%',
        height: position === 'center' ? '60px' : '100%',
        minHeight: position === 'center' ? '60px' : '100px',
        border: isOver ? '3px solid #1890ff' : '2px dashed #d9d9d9',
        backgroundColor: isOver ? '#e6f7ff' : '#fafafa',
        borderRadius: '4px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.2s',
        fontSize: '12px',
        color: isOver ? '#1890ff' : '#999',
        cursor: 'copy',
        fontWeight: isOver ? 'bold' : 'normal'
      }}
    >
      <div style={{ fontSize: isOver ? '20px' : '16px', marginBottom: '4px' }}>
        {position === 'left' && '←'}
        {position === 'right' && '→'}
        {position === 'center' && '↓'}
      </div>
      <Text type="secondary" style={{ fontSize: 11, color: isOver ? '#1890ff' : '#999', fontWeight: isOver ? 'bold' : 'normal' }}>
        {position === 'left' && '左侧'}
        {position === 'right' && '右侧'}
        {position === 'center' && '新行'}
      </Text>
    </div>
  )
}

interface SortableModuleInstanceProps {
  instance: ModuleInstance
  rowIndex: number
  columnIndex: number
  columnsInRow: number
  onRemove: (instanceId: string) => void
  onCopy: (instanceId: string) => void
  onRename: (instanceId: string, newName: string) => void
  isDragging: boolean
  moduleType: 'wps' | 'pqr' | 'ppqr'
}

const SortableModuleInstance: React.FC<SortableModuleInstanceProps> = ({
  instance,
  rowIndex,
  columnIndex,
  columnsInRow,
  onRemove,
  onCopy,
  onRename,
  isDragging: parentIsDragging,
  moduleType
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({
      id: instance.instanceId
    })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1
  }

  const module = getModuleByIdAndType(instance.moduleId, moduleType)
  const displayName = instance.customName || module?.name || instance.moduleId

  const [renameModalVisible, setRenameModalVisible] = useState(false)
  const [newName, setNewName] = useState(instance.customName || '')

  const handleRename = () => {
    onRename(instance.instanceId, newName)
    setRenameModalVisible(false)
  }

  // 如果找不到模块定义，显示错误卡片
  if (!module) {
    return (
      <div ref={setNodeRef} style={style}>
        <Card
          size="small"
          style={{
            marginBottom: 8,
            cursor: 'move',
            borderLeft: '3px solid #ff4d4f',
            backgroundColor: '#fff2f0'
          }}
          styles={{ body: { padding: '12px' } }}
        >
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space {...listeners} {...attributes} style={{ flex: 1, cursor: 'grab' }}>
              <DragOutlined style={{ fontSize: 16, color: '#999' }} />
              <Text strong type="danger">模块未找到: {instance.moduleId}</Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                (类型: {moduleType})
              </Text>
            </Space>

            <Space size="small">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => onRemove(instance.instanceId)}
                title="删除"
              />
            </Space>
          </Space>
        </Card>
      </div>
    )
  }

  return (
    <>
      <div ref={setNodeRef} style={style}>
        <Card
          size="small"
          style={{
            marginBottom: 8,
            cursor: 'move',
            borderLeft: '3px solid #1890ff'
          }}
          styles={{ body: { padding: '12px' } }}
        >
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space {...listeners} {...attributes} style={{ flex: 1, cursor: 'grab' }}>
              <DragOutlined style={{ fontSize: 16, color: '#999' }} />
              <Text strong>{displayName}</Text>
              {instance.customName && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ({module.name})
                </Text>
              )}
              <Text type="secondary" style={{ fontSize: 11 }}>
                ({columnsInRow} 列)
              </Text>
            </Space>

            <Space size="small">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => setRenameModalVisible(true)}
                title="重命名"
              />
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => onCopy(instance.instanceId)}
                title="复制"
              />
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => onRemove(instance.instanceId)}
                title="删除"
              />
            </Space>
          </Space>
        </Card>
      </div>

      <Modal
        title="重命名模块实例"
        open={renameModalVisible}
        onOk={handleRename}
        onCancel={() => setRenameModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">
            为此模块实例设置一个自定义名称（如"第1层"、"第2层"）
          </Text>
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={module?.name || '输入自定义名称'}
            onPressEnter={handleRename}
          />
        </Space>
      </Modal>
    </>
  )
}

interface TemplateCanvasProps {
  modules: ModuleInstance[]
  onRemove: (instanceId: string) => void
  onCopy: (instanceId: string) => void
  onRename: (instanceId: string, newName: string) => void
  onReorder: (newModules: ModuleInstance[]) => void
  activeModuleId: string | null
  overDropZone: { rowIndex: number; position: 'left' | 'center' | 'right'; columnIndex?: number } | null
  moduleType?: 'wps' | 'pqr' | 'ppqr'
}

const TemplateCanvas: React.FC<TemplateCanvasProps> = ({
  modules,
  onRemove,
  onCopy,
  onRename,
  onReorder,
  activeModuleId,
  overDropZone,
  moduleType = 'wps'
}) => {
  const { setNodeRef } = useDroppable({
    id: 'template-canvas'
  })

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

  const isDraggingFromLibrary = activeModuleId && !modules.find(m => m.instanceId === activeModuleId)
  const isDraggingFromCanvas = activeModuleId && modules.find(m => m.instanceId === activeModuleId)
  const shouldShowDropZones = isDraggingFromLibrary || isDraggingFromCanvas

  return (
    <Card
      title={
        <Space>
          <span>模板画布</span>
          <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
            ({modules.length} 个模块, {rows.length} 行)
          </Text>
        </Space>
      }
      size="small"
      styles={{ body: { padding: '12px' } }}
      style={{ height: '100%' }}
    >
      <div ref={setNodeRef} style={{ minHeight: 400 }}>
        {modules.length === 0 ? (
          <Empty
            description="从左侧拖拽模块到这里"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 100 }}
          />
        ) : (
          <SortableContext
            items={modules.map((m) => m.instanceId)}
            strategy={verticalListSortingStrategy}
          >
            <div style={{ maxHeight: 500, overflow: 'auto', paddingRight: 8 }}>
              {/* 按行显示模块 */}
              {rows.map((row, rowIndex) => {
                const columnsInRow = row.length
                const columnSpan = Math.floor(24 / columnsInRow)
                const canAddColumn = columnsInRow < 4

                return (
                  <div key={rowIndex} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'stretch', gap: '8px' }}>
                      {row.map((instance, columnIndex) => {
                        // 如果正在拖拽这个模块，不显示它的放置区
                        const isDraggingThis = activeModuleId === instance.instanceId
                        const showLeftDropZone = shouldShowDropZones && !isDraggingThis && canAddColumn && columnIndex === 0
                        const showRightDropZone = shouldShowDropZones && !isDraggingThis && canAddColumn

                        return (
                          <React.Fragment key={instance.instanceId}>
                            {/* 左侧放置区 */}
                            {showLeftDropZone && (
                              <div style={{ width: '80px', flexShrink: 0 }}>
                                <DropZone
                                  rowIndex={rowIndex}
                                  position="left"
                                  columnIndex={columnIndex}
                                  isOver={
                                    overDropZone?.rowIndex === rowIndex &&
                                    overDropZone?.position === 'left' &&
                                    overDropZone?.columnIndex === columnIndex
                                  }
                                />
                              </div>
                            )}

                            {/* 模块本身 */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <SortableModuleInstance
                                instance={instance}
                                rowIndex={rowIndex}
                                columnIndex={columnIndex}
                                columnsInRow={columnsInRow}
                                onRemove={onRemove}
                                onCopy={onCopy}
                                onRename={onRename}
                                isDragging={isDraggingThis}
                                moduleType={moduleType}
                              />
                            </div>

                            {/* 右侧放置区 */}
                            {showRightDropZone && (
                              <div style={{ width: '80px', flexShrink: 0 }}>
                                <DropZone
                                  rowIndex={rowIndex}
                                  position="right"
                                  columnIndex={columnIndex}
                                  isOver={
                                    overDropZone?.rowIndex === rowIndex &&
                                    overDropZone?.position === 'right' &&
                                    overDropZone?.columnIndex === columnIndex
                                  }
                                />
                              </div>
                            )}
                          </React.Fragment>
                        )
                      })}
                    </div>
                  </div>
                )
              })}

              {/* 底部新行放置区 */}
              {shouldShowDropZones && (
                <div style={{ marginTop: 8 }}>
                  <DropZone
                    rowIndex={rows.length}
                    position="center"
                    isOver={
                      overDropZone?.rowIndex === rows.length &&
                      overDropZone?.position === 'center'
                    }
                  />
                </div>
              )}
            </div>
          </SortableContext>
        )}
      </div>

      {modules.length > 0 && (
        <div style={{ marginTop: 12, fontSize: 12, color: '#999', textAlign: 'center' }}>
          拖拽模块卡片可自由移动位置，拖拽到左右两侧可添加到同一行
        </div>
      )}
    </Card>
  )
}

export default TemplateCanvas

