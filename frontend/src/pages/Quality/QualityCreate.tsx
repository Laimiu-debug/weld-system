import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Button,
  Space,
  message,
  Typography,
  Row,
  Col,
  Divider,
  Table,
  Steps,
  Alert,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import qualityService from '@/services/quality'
import QualityStandardField from '@/components/QualityStandardField'
import workspaceService from '@/services/workspace'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

interface DefectRecord {
  id: string
  film_no: string
  type: string
  severity: 'minor' | 'major' | 'critical'
  location: string
  size: string
  quantity: number
  description?: string
}

const QualityCreate: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const taskIdFromQuery = searchParams.get('taskId')
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [defects, setDefects] = useState<DefectRecord[]>([])
  const [step, setStep] = useState(0)

  const { user } = useAuthStore()

  const handleSubmit = async (values: Record<string, unknown>) => {
    if (step < 2) { await goNext(); return }
    setLoading(true)
    try {
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      const workspaceType = currentWorkspace?.type === 'enterprise' ? 'enterprise' : 'personal'
      const resultMap: Record<string, string> = {
        qualified: 'pass',
        unqualified: 'fail',
        conditional_qualified: 'conditional',
        pass: 'pass',
        fail: 'fail',
        conditional: 'conditional',
        pending: 'pending',
        retest: 'retest',
      }
      const inspectionResult = String(values.inspectionResult || '')
      const normalizedResult = resultMap[inspectionResult] || inspectionResult
      const qualified = normalizedResult === 'pass'
      const defectPayload = defects
        .filter((d) => d.film_no || d.type)
        .map(({ id: _id, ...rest }) => rest)

      await qualityService.createQualityInspection(
        {
          standard_id: values.standard_id as number | undefined,
          production_task_id:
            (values.production_task_id as number | undefined) ||
            (taskIdFromQuery ? Number(taskIdFromQuery) : undefined),
          inspection_number: (values.inspectionNumber as string) || undefined,
          inspection_type: values.inspectionType as string,
          inspection_date: values.inspectionDate
            ? (values.inspectionDate as dayjs.Dayjs).format('YYYY-MM-DD')
            : dayjs().format('YYYY-MM-DD'),
          inspector_id: Number(user?.id) || 0,
          inspector_name: (values.inspector as string) || user?.full_name || user?.username,
          project_name: values.projectName as string,
          vessel_no: values.vesselNo as string,
          work_order_no: (values.workOrderNo as string) || undefined,
          weld_joint_number: values.weldJointNumber as string,
          result: normalizedResult,
          is_qualified: qualified,
          defects_found: defectPayload.reduce((sum, d) => sum + (d.quantity || 1), 0),
          defect_details: JSON.stringify(defectPayload),
          notes: (values.notes as string) || undefined,
        },
        workspaceType,
        workspaceType === 'enterprise' ? currentWorkspace?.company_id : undefined,
        currentWorkspace?.factory_id
      )
      message.success('质量检验记录创建成功')
      if (taskIdFromQuery && searchParams.get('from') === 'production') {
        navigate(`/production/${taskIdFromQuery}?tab=quality`)
      } else {
        navigate('/quality')
      }
    } catch {
      message.error('创建失败')
    } finally {
      setLoading(false)
    }
  }

  const addDefect = () => {
    setDefects([
      ...defects,
      {
        id: Date.now().toString(),
        film_no: '',
        type: '',
        severity: 'minor',
        location: '',
        size: '',
        quantity: 1,
        description: '',
      },
    ])
  }

  const removeDefect = (id: string) => {
    setDefects(defects.filter((d) => d.id !== id))
  }

  const updateDefect = (id: string, field: keyof DefectRecord, value: string | number) => {
    setDefects(defects.map((d) => (d.id === id ? { ...d, [field]: value } : d)))
  }

  const defectColumns = [
    {
      title: '片子号',
      dataIndex: 'film_no',
      key: 'film_no',
      width: 120,
      render: (film_no: string, record: DefectRecord) => (
        <Input
          value={film_no}
          onChange={(e) => updateDefect(record.id, 'film_no', e.target.value)}
          placeholder="如 RT-01"
        />
      ),
    },
    {
      title: '缺陷类型',
      dataIndex: 'type',
      key: 'type',
      width: 130,
      render: (type: string, record: DefectRecord) => (
        <Select
          value={type || undefined}
          onChange={(value) => updateDefect(record.id, 'type', value)}
          style={{ width: '100%' }}
          placeholder="类型"
        >
          <Option value="裂纹">裂纹</Option>
          <Option value="气孔">气孔</Option>
          <Option value="夹渣">夹渣</Option>
          <Option value="未焊透">未焊透</Option>
          <Option value="未熔合">未熔合</Option>
          <Option value="咬边">咬边</Option>
          <Option value="焊瘤">焊瘤</Option>
          <Option value="其他">其他</Option>
        </Select>
      ),
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 110,
      render: (severity: string, record: DefectRecord) => (
        <Select
          value={severity}
          onChange={(value) => updateDefect(record.id, 'severity', value)}
          style={{ width: '100%' }}
        >
          <Option value="minor">轻微</Option>
          <Option value="major">严重</Option>
          <Option value="critical">致命</Option>
        </Select>
      ),
    },
    {
      title: '片上位置',
      dataIndex: 'location',
      key: 'location',
      render: (location: string, record: DefectRecord) => (
        <Input
          value={location}
          onChange={(e) => updateDefect(record.id, 'location', e.target.value)}
          placeholder="位置"
        />
      ),
    },
    {
      title: '尺寸',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size: string, record: DefectRecord) => (
        <Input
          value={size}
          onChange={(e) => updateDefect(record.id, 'size', e.target.value)}
          placeholder="如 3mm"
        />
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (quantity: number, record: DefectRecord) => (
        <InputNumber
          value={quantity}
          onChange={(value) => updateDefect(record.id, 'quantity', value || 1)}
          min={1}
          style={{ width: '100%' }}
        />
      ),
    },
    {
      title: '',
      key: 'actions',
      width: 48,
      render: (_: unknown, record: DefectRecord) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => removeDefect(record.id)}
        />
      ),
    },
  ]

  const goNext = async () => {
    if (step === 0) {
      await form.validateFields(['projectName', 'vesselNo', 'weldJointNumber'])
    } else if (step === 1) {
      await form.validateFields(['inspectionType', 'inspectionDate', 'inspector', 'inspectionResult'])
    }
    setStep((s) => Math.min(s + 1, 2))
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/quality')}>
            返回质量管理
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            新建质量检验
          </Title>
        </Space>
        <Text type="secondary" className="block mt-2">
          按 项目 → 容器/工令 → 焊缝 → 片子缺陷 定位录入，减少无关字段
        </Text>
      </div>

      <Card>
        <Steps
          current={step}
          className="mb-6"
          items={[
            { title: '定位', description: '项目 / 容器 / 焊缝' },
            { title: '检测', description: '方法与结论' },
            { title: '片子缺陷', description: '可选' },
          ]}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            inspectionDate: dayjs(),
            inspectionType: 'radiographic',
            inspector: user?.full_name || user?.username || '',
            inspectionResult: 'pass',
            production_task_id: taskIdFromQuery ? Number(taskIdFromQuery) : undefined,
          }}
        >
          <QualityStandardField form={form} />
          <div style={{ display: step === 0 ? 'block' : 'none' }}>
            <Alert
              type="info"
              showIcon
              className="mb-4"
              message="先写清「哪台容器的哪条焊缝」，再填检测结果"
            />
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="projectName"
                  label="项目名称"
                  rules={[{ required: true, message: '请输入项目名称' }]}
                >
                  <Input placeholder="例如：XX 石化装置改造" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="vesselNo"
                  label="容器号"
                  rules={[{ required: true, message: '请输入容器号' }]}
                >
                  <Input placeholder="例如：V-101 / E-201" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item name="workOrderNo" label="工令号">
                  <Input placeholder="可选，例如：WO-2026-088" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="weldJointNumber"
                  label="焊缝编号"
                  rules={[{ required: true, message: '请输入焊缝编号' }]}
                >
                  <Input placeholder="例如：W-12 / A-3" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item name="production_task_id" label="关联生产任务">
                  <InputNumber
                    style={{ width: '100%' }}
                    placeholder="可选"
                    disabled={Boolean(taskIdFromQuery)}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="inspectionNumber" label="检验编号">
                  <Input placeholder="可留空，系统按项目-容器-焊缝自动生成" />
                </Form.Item>
              </Col>
            </Row>
          </div>

          <div style={{ display: step === 1 ? 'block' : 'none' }}>
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="inspectionType"
                  label="检验方法"
                  rules={[{ required: true, message: '请选择检验方法' }]}
                >
                  <Select placeholder="选择检验方法">
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
                <Form.Item
                  name="inspectionDate"
                  label="检验日期"
                  rules={[{ required: true, message: '请选择检验日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="inspector"
                  label="检验员"
                  rules={[{ required: true, message: '请输入检验员' }]}
                >
                  <Input placeholder="检验员姓名" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name="inspectionResult"
                  label="检验结果"
                  rules={[{ required: true, message: '请选择检验结果' }]}
                >
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
              <TextArea rows={3} placeholder="可选：方法说明、标准条款等" />
            </Form.Item>
          </div>

          <div style={{ display: step === 2 ? 'block' : 'none' }}>
            <Alert
              type="info"
              showIcon
              className="mb-4"
              message="按片子号记录缺陷。无缺陷可跳过直接保存。"
            />
            <Button type="dashed" icon={<PlusOutlined />} onClick={addDefect} block className="mb-4">
              添加片子缺陷
            </Button>
            {defects.length > 0 && (
              <Table
                columns={defectColumns}
                dataSource={defects}
                rowKey="id"
                pagination={false}
                size="small"
                scroll={{ x: 720 }}
              />
            )}
          </div>

          <Divider />

          <div className="flex justify-between">
            <Button onClick={() => (step === 0 ? navigate('/quality') : setStep(step - 1))}>
              {step === 0 ? '取消' : '上一步'}
            </Button>
            <Space>
              {step < 2 ? (
                <Button key="next" htmlType="button" type="primary" onClick={() => void goNext()}>
                  下一步
                </Button>
              ) : (
                <Button
                  type="primary"
                  key="save"
                  htmlType="submit"
                  loading={loading}
                  icon={<SaveOutlined />}
                >
                  保存检验记录
                </Button>
              )}
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default QualityCreate
