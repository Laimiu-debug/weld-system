/**
 * 模板构建器组件
 * 主容器组件，整合模块库、画布和预览
 */
import React, { useState } from 'react'
import {
  Modal,
  Row,
  Col,
  Form,
  Input,
  Select,
  Button,
  message,
  Space,
  Divider,
  Collapse,
  Card,
  Typography
} from 'antd'
import { DndContext, DragEndEvent, DragOverlay } from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import { ModuleInstance, FieldModule } from '@/types/wpsModules'
import ModuleLibrary from './ModuleLibrary'
import TemplateCanvas from './TemplateCanvas'
import TemplatePreview from './TemplatePreview'
import ModuleCard from './ModuleCard'
import { v4 as uuidv4 } from 'uuid'
import { getModuleById, getModuleByIdAndType } from '@/constants/wpsModules'

const { TextArea } = Input
const { Option } = Select
const { Text } = Typography

interface TemplateBuilderProps {
  visible: boolean
  onClose: () => void
  onSave: (template: any) => Promise<void>
  editingTemplate?: any  // 编辑模式下的模板数据
}

const TemplateBuilder: React.FC<TemplateBuilderProps> = ({
  visible,
  onClose,
  onSave,
  editingTemplate
}) => {
  const [form] = Form.useForm()
  const [modules, setModules] = useState<ModuleInstance[]>([])
  const [loading, setLoading] = useState(false)
  const [activeModule, setActiveModule] = useState<FieldModule | null>(null)
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null)
  const [overDropZone, setOverDropZone] = useState<{
    rowIndex: number
    position: 'left' | 'center' | 'right'
    columnIndex?: number
  } | null>(null)
  const [selectedModuleType, setSelectedModuleType] = useState<'wps' | 'pqr' | 'ppqr'>('wps')

  // 当编辑模板时，初始化表单和模块
  React.useEffect(() => {
    if (visible && editingTemplate) {
      const moduleType = editingTemplate.module_type || 'wps'
      form.setFieldsValue({
        name: editingTemplate.name,
        description: editingTemplate.description,
        welding_process: editingTemplate.welding_process,
        standard: editingTemplate.standard,
        module_type: moduleType
      })
      setSelectedModuleType(moduleType as 'wps' | 'pqr' | 'ppqr')
      setModules(editingTemplate.module_instances || [])
    } else if (visible) {
      form.resetFields()
      setSelectedModuleType('wps')
      setModules([])
    }
  }, [visible, editingTemplate, form])

  // 监听模板类型变化
  const handleModuleTypeChange = (value: 'wps' | 'pqr' | 'ppqr') => {
    setSelectedModuleType(value)
    // 切换模板类型时，清空已添加的模块（因为不同类型的模块ID不兼容）
    if (modules.length > 0) {
      Modal.confirm({
        title: '切换模板类型',
        content: '切换模板类型将清空已添加的模块，确定要继续吗？',
        okText: '确定',
        cancelText: '取消',
        onOk: () => {
          setModules([])
        },
        onCancel: () => {
          // 恢复原来的值
          form.setFieldValue('module_type', selectedModuleType)
        }
      })
    }
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    setActiveModule(null)
    setActiveModuleId(null)
    setOverDropZone(null)

    if (!over) {
      return
    }

    const overId = over.id as string
    const isFromLibrary = active.data.current && (active.data.current as any).id
    const isToDropZone = overId.startsWith('drop-')

    // 从模块库拖拽到画布
    if (isFromLibrary) {
      const moduleData = active.data.current as FieldModule

      // 检查是否拖到了放置区
      if (isToDropZone) {
        const dropData = over.data.current as {
          rowIndex: number
          position: 'left' | 'center' | 'right'
          columnIndex?: number
        }

        const { rowIndex, position, columnIndex } = dropData

        if (position === 'center') {
          // 添加到新行
          const newInstance: ModuleInstance = {
            instanceId: uuidv4(),
            moduleId: moduleData.id,
            order: modules.length + 1,
            rowIndex: rowIndex,
            columnIndex: 0
          }
          setModules([...modules, newInstance])
          message.success(`已添加模块: ${moduleData.name}`)
        } else {
          // 添加到现有行的左侧或右侧
          const rowModules = modules.filter(m => m.rowIndex === rowIndex)

          if (rowModules.length >= 4) {
            message.warning('每行最多支持4列')
            return
          }

          const newInstance: ModuleInstance = {
            instanceId: uuidv4(),
            moduleId: moduleData.id,
            order: modules.length + 1,
            rowIndex: rowIndex,
            columnIndex: position === 'left' ? columnIndex! : columnIndex! + 1
          }

          // 更新该行其他模块的列索引
          const updatedModules = modules.map((m) => {
            if (m.rowIndex === rowIndex) {
              if (position === 'left' && m.columnIndex! >= columnIndex!) {
                return { ...m, columnIndex: m.columnIndex! + 1 }
              } else if (position === 'right' && m.columnIndex! > columnIndex!) {
                return { ...m, columnIndex: m.columnIndex! + 1 }
              }
            }
            return m
          })

          setModules([...updatedModules, newInstance])
          message.success(`已添加模块: ${moduleData.name}`)
        }
      } else if (overId === 'template-canvas') {
        // 拖到画布空白区域，添加到新行
        const maxRowIndex = modules.reduce((max, m) => Math.max(max, m.rowIndex ?? 0), -1)

        const newInstance: ModuleInstance = {
          instanceId: uuidv4(),
          moduleId: moduleData.id,
          order: modules.length + 1,
          rowIndex: maxRowIndex + 1,
          columnIndex: 0
        }
        setModules([...modules, newInstance])
        message.success(`已添加模块: ${moduleData.name}`)
      }
    }
    // 画布内部拖拽 (已存在的模块)
    else {
      const draggedModule = modules.find(m => m.instanceId === active.id)
      if (!draggedModule) return

      // 拖到放置区 - 移动到指定位置
      if (isToDropZone) {
        const dropData = over.data.current as {
          rowIndex: number
          position: 'left' | 'center' | 'right'
          columnIndex?: number
        }

        const { rowIndex, position, columnIndex } = dropData

        // 从原位置移除
        let updatedModules = modules.filter(m => m.instanceId !== draggedModule.instanceId)

        // 重新计算原行的列索引
        const oldRowModules = updatedModules.filter(m => m.rowIndex === draggedModule.rowIndex)
        oldRowModules.forEach((m, idx) => {
          m.columnIndex = idx
        })

        if (position === 'center') {
          // 移动到新行
          draggedModule.rowIndex = rowIndex
          draggedModule.columnIndex = 0
          updatedModules.push(draggedModule)
        } else {
          // 移动到现有行的左侧或右侧
          const targetRowModules = updatedModules.filter(m => m.rowIndex === rowIndex)

          if (targetRowModules.length >= 4) {
            message.warning('每行最多支持4列')
            return
          }

          const newColIndex = position === 'left' ? columnIndex! : columnIndex! + 1

          // 更新目标行其他模块的列索引
          updatedModules = updatedModules.map((m) => {
            if (m.rowIndex === rowIndex && m.columnIndex! >= newColIndex) {
              return { ...m, columnIndex: m.columnIndex! + 1 }
            }
            return m
          })

          draggedModule.rowIndex = rowIndex
          draggedModule.columnIndex = newColIndex
          updatedModules.push(draggedModule)
        }

        setModules(updatedModules)
        message.success('模块位置已更新')
      }
      // 拖到另一个模块上 - 交换位置
      else {
        const oldIndex = modules.findIndex((m) => m.instanceId === active.id)
        const newIndex = modules.findIndex((m) => m.instanceId === over.id)

        if (oldIndex !== -1 && newIndex !== -1 && oldIndex !== newIndex) {
          const newModules = arrayMove(modules, oldIndex, newIndex)

          // 重新计算所有模块的 rowIndex 和 columnIndex
          const rowsMap = new Map<number, ModuleInstance[]>()
          newModules.forEach((module) => {
            const rowIdx = module.rowIndex ?? 0
            if (!rowsMap.has(rowIdx)) {
              rowsMap.set(rowIdx, [])
            }
            rowsMap.get(rowIdx)!.push(module)
          })

          // 重新分配索引
          let currentOrder = 1
          const sortedRowIndices = Array.from(rowsMap.keys()).sort((a, b) => a - b)
          sortedRowIndices.forEach((rowIdx, newRowIdx) => {
            const rowModules = rowsMap.get(rowIdx)!
            rowModules.forEach((module, colIdx) => {
              module.rowIndex = newRowIdx
              module.columnIndex = colIdx
              module.order = currentOrder++
            })
          })

          setModules(newModules)
        }
      }
    }
  }

  const handleDragStart = (event: any) => {
    const activeId = event.active.id as string
    setActiveModuleId(activeId)

    // 从模块库拖拽
    if (event.active.data.current && (event.active.data.current as any).id) {
      const moduleData = event.active.data.current as FieldModule
      setActiveModule(moduleData)
    }
    // 从画布拖拽已存在的模块
    else {
      const draggedModule = modules.find(m => m.instanceId === activeId)
      if (draggedModule) {
        const moduleData = getModuleByIdAndType(draggedModule.moduleId, selectedModuleType)
        if (moduleData) {
          setActiveModule(moduleData)
        }
      }
    }
  }

  const handleDragOver = (event: any) => {
    const { over } = event

    if (over && typeof over.id === 'string' && over.id.startsWith('drop-')) {
      const dropData = over.data.current as {
        rowIndex: number
        position: 'left' | 'center' | 'right'
        columnIndex?: number
      }
      setOverDropZone(dropData)
    } else {
      setOverDropZone(null)
    }
  }

  const handleRemoveModule = (instanceId: string) => {
    const removedModule = modules.find((m) => m.instanceId === instanceId)
    if (!removedModule) return

    const newModules = modules.filter((m) => m.instanceId !== instanceId)

    // 重新计算该行的列索引
    const affectedRowModules = newModules.filter(
      (m) => m.rowIndex === removedModule.rowIndex
    )

    // 如果该行还有其他模块，重新分配列索引
    if (affectedRowModules.length > 0) {
      affectedRowModules.forEach((m, idx) => {
        m.columnIndex = idx
      })
    }

    setModules(newModules)
    message.success('模块已删除')
  }

  const handleCopyModule = (instanceId: string) => {
    const module = modules.find((m) => m.instanceId === instanceId)
    if (module) {
      // 找到最大的行索引
      const maxRowIndex = modules.reduce((max, m) => Math.max(max, m.rowIndex ?? 0), -1)

      const newInstance: ModuleInstance = {
        ...module,
        instanceId: uuidv4(),
        order: modules.length + 1,
        customName: module.customName ? `${module.customName} (副本)` : undefined,
        rowIndex: maxRowIndex + 1, // 复制的模块添加到新行
        columnIndex: 0
      }
      setModules([...modules, newInstance])
      message.success('模块已复制')
    }
  }

  const handleRenameModule = (instanceId: string, newName: string) => {
    setModules(
      modules.map((m) =>
        m.instanceId === instanceId ? { ...m, customName: newName || undefined } : m
      )
    )
    message.success('重命名成功')
  }

  const handleReorderModules = (newModules: ModuleInstance[]) => {
    setModules(newModules)
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()

      if (modules.length === 0) {
        message.error('请至少添加一个模块')
        return
      }

      // 获取当前工作区信息，确定 workspace_type
      const currentWorkspaceStr = localStorage.getItem('current_workspace')
      let workspaceType = 'personal'

      if (currentWorkspaceStr) {
        try {
          const currentWorkspace = JSON.parse(currentWorkspaceStr)
          // 根据工作区 ID 格式判断工作区类型
          if (currentWorkspace.id && currentWorkspace.id.startsWith('enterprise_')) {
            workspaceType = 'enterprise'
          }
        } catch (e) {
          console.warn('解析工作区信息失败，使用默认值 personal')
        }
      }

      const template = {
        name: values.name,
        description: values.description,
        welding_process: values.welding_process,
        standard: values.standard,
        module_type: values.module_type || 'wps',
        workspace_type: workspaceType,
        module_instances: modules,
        templateId: editingTemplate?.id  // 编辑模式下传递模板ID
      }

      setLoading(true)
      console.log('提交模板数据:', template)
      console.log('工作区类型:', workspaceType)
      await onSave(template)
      console.log('模板保存成功')
      // 不在这里显示成功消息，让父组件处理
      form.resetFields()
      setModules([])
      onClose()
    } catch (error: any) {
      console.error('保存失败:', error)
      if (error.errorFields) {
        message.error('请填写必填字段')
      } else {
        const errorMsg = error?.response?.data?.detail || error?.message || '保存模板失败'
        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    Modal.confirm({
      title: '确认关闭',
      content: '关闭后未保存的内容将丢失，确定要关闭吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        form.resetFields()
        setModules([])
        onClose()
      }
    })
  }

  return (
    <Modal
      title={editingTemplate ? `编辑模板 - ${editingTemplate.name}` : "创建模板 - 模块化拖拽"}
      open={visible}
      onCancel={handleCancel}
      width={1400}
      style={{ top: 20 }}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button key="save" type="primary" loading={loading} onClick={handleSave}>
          保存模板
        </Button>
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 基本信息表单 */}
        <Form form={form} layout="vertical" initialValues={{ module_type: 'wps' }}>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                label="模板名称"
                name="name"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input placeholder="如: 手工电弧焊模板" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="模板类型"
                name="module_type"
                rules={[{ required: true, message: '请选择模板类型' }]}
              >
                <Select
                  placeholder="选择模板类型"
                  onChange={handleModuleTypeChange}
                >
                  <Option value="wps">WPS - 焊接工艺规程</Option>
                  <Option value="pqr">PQR - 工艺评定记录</Option>
                  <Option value="ppqr">pPQR - 预评定记录</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="焊接工艺"
                name="welding_process"
              >
                <Select placeholder="选择焊接工艺(可选)" allowClear>
                  <Option value="111">111 - 手工电弧焊</Option>
                  <Option value="114">114 - 自保护药芯焊丝电弧焊</Option>
                  <Option value="121">121 - 埋弧焊</Option>
                  <Option value="135">135 - 活性气体保护焊</Option>
                  <Option value="141">141 - TIG焊</Option>
                  <Option value="15">15 - 等离子弧焊</Option>
                  <Option value="311">311 - 氧乙炔焊</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="标准"
                name="standard"
              >
                <Select placeholder="选择标准(可选)" allowClear>
                  <Option value="GB/T 15169">GB/T 15169</Option>
                  <Option value="AWS D1.1">AWS D1.1</Option>
                  <Option value="ASME IX">ASME IX</Option>
                  <Option value="EN ISO 15609">EN ISO 15609</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="模板描述" name="description">
            <TextArea rows={2} placeholder="简要描述模板的用途和适用场景" />
          </Form.Item>
        </Form>

        <Divider style={{ margin: '12px 0' }} />

        {/* 拖拽区域 */}
        <DndContext
          onDragEnd={handleDragEnd}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
        >
          <Row gutter={16}>
            <Col span={10}>
              <ModuleLibrary moduleType={selectedModuleType} />
            </Col>
            <Col span={14}>
              <TemplateCanvas
                modules={modules}
                onRemove={handleRemoveModule}
                onCopy={handleCopyModule}
                onRename={handleRenameModule}
                onReorder={handleReorderModules}
                activeModuleId={activeModuleId}
                overDropZone={overDropZone}
                moduleType={selectedModuleType}
              />
            </Col>
          </Row>

          <DragOverlay dropAnimation={null}>
            {activeModule ? (
              <div style={{
                width: '200px',
                opacity: 0.9,
                pointerEvents: 'none'
              }}>
                <Card
                  size="small"
                  style={{
                    border: '2px solid #1890ff',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                  }}
                >
                  <Space direction="vertical" size={0} style={{ width: '100%' }}>
                    <Text strong style={{ fontSize: '12px' }}>{activeModule.name}</Text>
                    <Text type="secondary" style={{ fontSize: '10px' }}>
                      {activeModule.description}
                    </Text>
                  </Space>
                </Card>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

        {/* 预览区域 */}
        {modules.length > 0 && (
          <Collapse
            defaultActiveKey={['preview']}
            ghost
            items={[
              {
                key: 'preview',
                label: '预览生成的表单',
                children: <TemplatePreview template={{ module_instances: modules } as any} moduleType={selectedModuleType} />
              }
            ]}
          />
        )}
      </Space>
    </Modal>
  )
}

export default TemplateBuilder

