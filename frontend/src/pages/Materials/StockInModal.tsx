/**
 * 焊材入库弹窗组件
 */

import React, { useState } from 'react'
import { Modal, Form, InputNumber, Input, message } from 'antd'
import type { Material, StockInRequest } from '../../services/materials'
import materialsService from '../../services/materials'
import { workspaceService } from '../../services/workspace'

interface StockInModalProps {
  visible: boolean
  material: Material | null
  onCancel: () => void
  onSuccess: () => void
}

const StockInModal: React.FC<StockInModalProps> = ({
  visible,
  material,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!material) return

    try {
      const values = await form.validateFields()
      setLoading(true)

      const data: StockInRequest = {
        material_id: material.id,
        quantity: values.quantity,
        unit_price: values.unit_price,
        source: values.source,
        batch_number: values.batch_number,
        warehouse: values.warehouse,
        storage_location: values.storage_location,
        notes: values.notes,
      }

      // 获取当前工作区
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      if (!currentWorkspace) {
        message.warning('请先选择工作区')
        setLoading(false)
        return
      }

      const workspaceType = currentWorkspace.type
      const companyId = currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined
      const factoryId = currentWorkspace.factory_id

      await materialsService.stockIn(workspaceType, companyId, factoryId, data)

      message.success('入库成功')
      form.resetFields()
      onSuccess()
    } catch (error: any) {
      console.error('入库失败:', error)
      message.error(error.response?.data?.detail || '入库失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title="焊材入库"
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={loading}
      width={600}
      destroyOnClose
    >
      {material && (
        <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
          <div><strong>焊材名称：</strong>{material.material_name}</div>
          <div><strong>焊材编号：</strong>{material.material_code}</div>
          <div><strong>当前库存：</strong>{material.current_stock} {material.unit}</div>
        </div>
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          unit_price: material?.unit_price,
          warehouse: material?.warehouse,
          storage_location: material?.storage_location,
        }}
      >
        <Form.Item
          label="入库数量"
          name="quantity"
          rules={[
            { required: true, message: '请输入入库数量' },
            { type: 'number', min: 0.01, message: '数量必须大于0' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入入库数量"
            addonAfter={material?.unit || 'kg'}
            precision={2}
          />
        </Form.Item>

        <Form.Item
          label="单价"
          name="unit_price"
          rules={[
            { type: 'number', min: 0, message: '单价不能为负数' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入单价"
            addonAfter="元"
            precision={2}
          />
        </Form.Item>

        <Form.Item
          label="供应商"
          name="source"
        >
          <Input placeholder="请输入供应商名称" />
        </Form.Item>

        <Form.Item
          label="批次号"
          name="batch_number"
        >
          <Input placeholder="请输入批次号" />
        </Form.Item>

        <Form.Item
          label="仓库"
          name="warehouse"
        >
          <Input placeholder="请输入仓库名称" />
        </Form.Item>

        <Form.Item
          label="存储位置"
          name="storage_location"
        >
          <Input placeholder="请输入存储位置（如：A区-01货架-03层）" />
        </Form.Item>

        <Form.Item
          label="备注"
          name="notes"
        >
          <Input.TextArea
            rows={3}
            placeholder="请输入备注信息"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default StockInModal

