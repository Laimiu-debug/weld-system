/**
 * 焊材出库弹窗组件
 */

import React, { useState } from 'react'
import { Modal, Form, InputNumber, Input, Select, message } from 'antd'
import type { Material, StockOutRequest } from '../../services/materials'
import materialsService from '../../services/materials'
import { workspaceService } from '../../services/workspace'

interface StockOutModalProps {
  visible: boolean
  material: Material | null
  onCancel: () => void
  onSuccess: () => void
}

const StockOutModal: React.FC<StockOutModalProps> = ({
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

      const data: StockOutRequest = {
        material_id: material.id,
        quantity: values.quantity,
        destination: values.destination,
        reference_type: values.reference_type,
        reference_number: values.reference_number,
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

      await materialsService.stockOut(workspaceType, companyId, factoryId, data)

      message.success('出库成功')
      form.resetFields()
      onSuccess()
    } catch (error: any) {
      console.error('出库失败:', error)
      message.error(error.response?.data?.detail || '出库失败')
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
      title="焊材出库"
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
          {material.min_stock_level && material.current_stock < material.min_stock_level && (
            <div style={{ color: '#ff4d4f', marginTop: 8 }}>
              ⚠️ 当前库存低于最低库存水平（{material.min_stock_level} {material.unit}）
            </div>
          )}
        </div>
      )}

      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          label="出库数量"
          name="quantity"
          rules={[
            { required: true, message: '请输入出库数量' },
            { type: 'number', min: 0.01, message: '数量必须大于0' },
            {
              validator: (_, value) => {
                if (material && value > material.current_stock) {
                  return Promise.reject(new Error(`出库数量不能超过当前库存（${material.current_stock} ${material.unit}）`))
                }
                return Promise.resolve()
              },
            },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入出库数量"
            addonAfter={material?.unit || 'kg'}
            precision={2}
          />
        </Form.Item>

        <Form.Item
          label="去向"
          name="destination"
          rules={[{ required: true, message: '请输入去向' }]}
        >
          <Input placeholder="请输入去向（如：生产车间、项目名称等）" />
        </Form.Item>

        <Form.Item
          label="关联单据类型"
          name="reference_type"
        >
          <Select
            placeholder="请选择关联单据类型"
            allowClear
            options={[
              { label: '生产任务', value: '生产任务' },
              { label: '项目', value: '项目' },
              { label: '维修', value: '维修' },
              { label: '测试', value: '测试' },
              { label: '其他', value: '其他' },
            ]}
          />
        </Form.Item>

        <Form.Item
          label="关联单据号"
          name="reference_number"
        >
          <Input placeholder="请输入关联单据号" />
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

export default StockOutModal

