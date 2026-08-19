import React, { useEffect, useState } from 'react'
import { Button, Card, Form, Input, Select, Space, Spin, Switch, Typography, message } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import equipmentService, { EquipmentType } from '@/services/equipment'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const EquipmentEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const response = await equipmentService.getEquipmentDetail(id)
        const data = (response as any).data || response
        form.setFieldsValue({
          equipment_code: data.equipment_code,
          equipment_name: data.equipment_name,
          equipment_type: data.equipment_type,
          status: data.status,
          location: data.location,
          workshop: data.workshop,
          is_active: data.is_active,
          is_critical: data.is_critical,
          description: data.description,
          notes: data.notes,
        })
      } catch {
        message.error('加载设备失败')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [id, form])

  const handleSubmit = async (values: Record<string, unknown>) => {
    if (!id) return
    setSaving(true)
    try {
      await equipmentService.updateEquipment(id, values as never)
      message.success('设备已更新')
      navigate('/equipment')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="page-container flex justify-center items-center" style={{ minHeight: 320 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/equipment')}>返回列表</Button>
          <Title level={2}>编辑设备</Title>
        </Space>
      </div>
      <Card>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="equipment_code" label="设备编号" rules={[{ required: true, message: '请输入设备编号' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="equipment_name" label="设备名称" rules={[{ required: true, message: '请输入设备名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="equipment_type" label="设备类型" rules={[{ required: true, message: '请选择设备类型' }]}>
            <Select>
              {equipmentService.getEquipmentTypeOptions().map((item: { label: string; value: EquipmentType }) => (
                <Option key={item.value} value={item.value}>{item.label}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select>
              <Option value="operational">运行中</Option>
              <Option value="idle">空闲</Option>
              <Option value="maintenance">维护中</Option>
              <Option value="fault">故障</Option>
            </Select>
          </Form.Item>
          <Form.Item name="location" label="位置">
            <Input />
          </Form.Item>
          <Form.Item name="workshop" label="车间">
            <Input />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_critical" label="关键设备" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={3} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>保存</Button>
        </Form>
      </Card>
    </div>
  )
}

export default EquipmentEdit
