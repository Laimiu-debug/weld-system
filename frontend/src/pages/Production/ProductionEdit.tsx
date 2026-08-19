import React, { useEffect, useState } from 'react'
import { Button, Card, DatePicker, Form, Input, InputNumber, Select, Space, Spin, Typography, message } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { getProductionTaskById, updateProductionTask } from '@/services/production'
import workspaceService from '@/services/workspace'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const ProductionEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const workspace = () => {
    const current = workspaceService.getCurrentWorkspaceFromStorage()
    return {
      type: current?.type === 'enterprise' ? 'enterprise' : 'personal',
      companyId: current?.type === 'enterprise' ? current.company_id : undefined,
      factoryId: current?.factory_id,
    }
  }

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const ws = workspace()
        const response = await getProductionTaskById(Number(id), ws.type, ws.companyId, ws.factoryId)
        const data = response.data || response
        form.setFieldsValue({
          task_name: data.task_name,
          task_type: data.task_type,
          status: data.status,
          priority: data.priority,
          progress_percentage: data.progress_percentage,
          description: data.description,
          planned_start_date: data.planned_start_date ? dayjs(data.planned_start_date) : undefined,
          planned_end_date: data.planned_end_date ? dayjs(data.planned_end_date) : undefined,
        })
      } catch {
        message.error('加载生产任务失败')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [id, form])

  const handleSubmit = async (values: Record<string, any>) => {
    if (!id) return
    setSaving(true)
    try {
      const ws = workspace()
      await updateProductionTask(
        Number(id),
        {
          task_name: values.task_name,
          task_type: values.task_type,
          status: values.status,
          priority: values.priority,
          progress_percentage: values.progress_percentage,
          description: values.description,
          planned_start_date: values.planned_start_date ? values.planned_start_date.format('YYYY-MM-DD') : undefined,
          planned_end_date: values.planned_end_date ? values.planned_end_date.format('YYYY-MM-DD') : undefined,
        },
        ws.type,
        ws.companyId,
        ws.factoryId,
      )
      message.success('生产任务已更新')
      navigate('/production')
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
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/production')}>返回列表</Button>
          <Title level={2}>编辑生产任务</Title>
        </Space>
      </div>
      <Card>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="task_name" label="任务名称" rules={[{ required: true, message: '请输入任务名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="task_type" label="任务类型">
            <Input />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select>
              <Option value="planning">计划中</Option>
              <Option value="in_progress">进行中</Option>
              <Option value="paused">已暂停</Option>
              <Option value="completed">已完成</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select>
              <Option value="low">低</Option>
              <Option value="medium">中</Option>
              <Option value="high">高</Option>
              <Option value="urgent">紧急</Option>
            </Select>
          </Form.Item>
          <Form.Item name="progress_percentage" label="进度 (%)">
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="planned_start_date" label="计划开始">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="planned_end_date" label="计划结束">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>保存</Button>
        </Form>
      </Card>
    </div>
  )
}

export default ProductionEdit
