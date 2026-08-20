import React, { useEffect, useState } from 'react'
import { Button, Card, DatePicker, Form, Input, Select, Space, Spin, Typography, message } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import qualityService from '@/services/quality'
import workspaceService from '@/services/workspace'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const QualityEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const workspace = () => {
    const current = workspaceService.getCurrentWorkspaceFromStorage()
    return {
      type: (current?.type === 'enterprise' ? 'enterprise' : 'personal') as 'personal' | 'enterprise',
      companyId: current?.type === 'enterprise' ? current.company_id : undefined,
      factoryId: current?.factory_id,
    }
  }

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const ws = workspace()
        const response = await qualityService.getQualityInspectionById(Number(id), ws.type, ws.companyId, ws.factoryId)
        const data = (response as any).data?.data || (response as any).data
        form.setFieldsValue({
          inspection_type: data.inspection_type,
          inspection_date: data.inspection_date ? dayjs(data.inspection_date) : undefined,
          inspector_name: data.inspector_name,
          welder_name: data.welder_name,
          weld_location: data.weld_location,
          result: data.result,
          is_qualified: data.is_qualified,
          defect_details: data.defect_details,
        })
      } catch {
        message.error('加载检验记录失败')
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
      const ws = workspace()
      await qualityService.updateQualityInspection(
        Number(id),
        {
          inspection_type: values.inspection_type as string,
          inspection_date: values.inspection_date ? dayjs(values.inspection_date as dayjs.Dayjs).format('YYYY-MM-DD') : undefined,
          inspector_name: values.inspector_name as string,
          welder_name: values.welder_name as string,
          weld_location: values.weld_location as string,
          result: values.result as string,
          is_qualified: Boolean(values.is_qualified),
          defect_details: values.defect_details as string,
        },
        ws.type,
        ws.companyId,
        ws.factoryId,
      )
      message.success('质量检验已更新')
      navigate('/quality')
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
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/quality')}>返回列表</Button>
          <Title level={2}>编辑质量检验</Title>
        </Space>
      </div>
      <Card>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="inspection_type" label="检验类型" rules={[{ required: true, message: '请选择检验类型' }]}>
            <Select>
              <Option value="routine">例行检验</Option>
              <Option value="acceptance">验收检验</Option>
              <Option value="process">过程检验</Option>
              <Option value="final">最终检验</Option>
              <Option value="rework">返修检验</Option>
            </Select>
          </Form.Item>
          <Form.Item name="inspection_date" label="检验日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="inspector_name" label="检验员">
            <Input />
          </Form.Item>
          <Form.Item name="welder_name" label="焊工">
            <Input />
          </Form.Item>
          <Form.Item name="weld_location" label="焊缝位置">
            <Input />
          </Form.Item>
          <Form.Item name="result" label="检验结果">
            <Select>
              <Option value="pass">合格</Option>
              <Option value="conditional">有条件合格</Option>
              <Option value="fail">不合格</Option>
              <Option value="pending">待定</Option>
              <Option value="retest">需复检</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_qualified" label="是否合格">
            <Select>
              <Option value={true}>合格</Option>
              <Option value={false}>不合格</Option>
            </Select>
          </Form.Item>
          <Form.Item name="defect_details" label="缺陷说明">
            <TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>保存</Button>
        </Form>
      </Card>
    </div>
  )
}

export default QualityEdit
