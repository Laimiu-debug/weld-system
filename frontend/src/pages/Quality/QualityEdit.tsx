import React, { useEffect, useState } from 'react'
import { Button, Card, Col, DatePicker, Form, Input, Row, Select, Space, Spin, Typography, message } from 'antd'
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
          project_name: data.project_name || data.weld_location,
          vessel_no: data.vessel_no,
          work_order_no: data.work_order_no,
          weld_joint_number: data.weld_joint_number || data.joint_number,
          result: data.result,
          notes: data.notes,
          defect_details: data.defect_details || data.defects,
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
          inspection_date: values.inspection_date
            ? dayjs(values.inspection_date as dayjs.Dayjs).format('YYYY-MM-DD')
            : undefined,
          inspector_name: values.inspector_name as string,
          project_name: values.project_name as string,
          vessel_no: values.vessel_no as string,
          work_order_no: values.work_order_no as string,
          weld_joint_number: values.weld_joint_number as string,
          result: values.result as string,
          notes: values.notes as string,
          defect_details: values.defect_details as string,
        },
        ws.type,
        ws.companyId,
        ws.factoryId,
      )
      message.success('质量检验已更新')
      navigate(`/quality/${id}`)
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
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/quality')}>
            返回列表
          </Button>
          <Title level={2}>编辑质量检验</Title>
        </Space>
      </div>
      <Card>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目' }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="vessel_no" label="容器号" rules={[{ required: true, message: '请输入容器号' }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="work_order_no" label="工令号">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="weld_joint_number"
                label="焊缝编号"
                rules={[{ required: true, message: '请输入焊缝编号' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="inspection_type" label="检验方法" rules={[{ required: true, message: '请选择' }]}>
                <Select>
                  <Option value="visual">外观 (VT)</Option>
                  <Option value="radiographic">射线 (RT)</Option>
                  <Option value="ultrasonic">超声 (UT)</Option>
                  <Option value="magnetic">磁粉 (MT)</Option>
                  <Option value="penetrant">渗透 (PT)</Option>
                  <Option value="other">其他</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="inspection_date" label="检验日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="inspector_name" label="检验员">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="result" label="检验结果">
                <Select>
                  <Option value="pass">合格</Option>
                  <Option value="conditional">有条件合格</Option>
                  <Option value="fail">不合格</Option>
                  <Option value="pending">待定</Option>
                  <Option value="retest">需复检</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="notes" label="备注">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item
            name="defect_details"
            label="片子缺陷 JSON"
            extra='格式示例：[{"film_no":"RT-01","type":"气孔","severity":"minor","location":"...","size":"3mm","quantity":2}]'
          >
            <TextArea rows={5} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
            保存
          </Button>
        </Form>
      </Card>
    </div>
  )
}

export default QualityEdit
