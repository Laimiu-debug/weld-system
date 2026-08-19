import React, { useEffect, useState } from 'react'
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
  Upload,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined, UploadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { createProductionTask } from '@/services/production'
import workspaceService from '@/services/workspace'
import weldersService from '@/services/welders'
import equipmentService from '@/services/equipment'
import wpsService from '@/services/wps'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const ProductionCreate: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [welders, setWelders] = useState<Array<{ id: number; full_name?: string; welder_code?: string }>>([])
  const [equipments, setEquipments] = useState<Array<{ id: number | string; equipment_name?: string; equipment_code?: string }>>([])
  const [wpsList, setWpsList] = useState<Array<{ id: number; wps_number?: string; title?: string }>>([])

  const unwrapItems = (response: any): any[] => {
    const data = response?.data ?? response
    if (Array.isArray(data)) return data
    if (Array.isArray(data?.items)) return data.items
    if (Array.isArray(data?.data?.items)) return data.data.items
    if (Array.isArray(data?.data)) return data.data
    return []
  }

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
        const apiWorkspaceType = currentWorkspace?.type === 'enterprise' ? 'company' : 'personal'
        const [welderRes, equipmentRes, wpsRes] = await Promise.all([
          weldersService.getList({ skip: 0, limit: 200 }),
          equipmentService.getEquipmentList({ skip: 0, limit: 200, workspace_type: apiWorkspaceType }),
          wpsService.getWPSList({ skip: 0, limit: 200 }),
        ])
        setWelders(unwrapItems(welderRes))
        setEquipments(unwrapItems(equipmentRes))
        setWpsList(unwrapItems(wpsRes))
      } catch (error) {
        console.error('加载追溯选项失败', error)
      }
    }
    void loadOptions()
  }, [])

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      const workspaceType = currentWorkspace?.type === 'enterprise' ? 'enterprise' : 'personal'
      const priority = values.priority === 'medium' ? 'normal' : values.priority
      await createProductionTask(
        {
          task_number: `TASK-${dayjs().format('YYYYMMDDHHmmss')}`,
          task_name: values.taskName,
          task_type: values.taskType,
          project_name: values.projectName,
          wps_id: values.wps_id,
          assigned_welder_id: values.assigned_welder_id,
          assigned_equipment_id: values.assigned_equipment_id,
          description: values.description,
          work_description: values.description,
          technical_requirements: values.technicalRequirements,
          quality_requirements: values.wpsStandard,
          safety_requirements: values.safetyRequirements,
          base_material: values.materialSpec,
          weld_length_planned: values.workload,
          planned_start_date: values.startDate ? values.startDate.format('YYYY-MM-DD') : undefined,
          planned_end_date: values.endDate ? values.endDate.format('YYYY-MM-DD') : undefined,
          status: values.status === 'planning' ? 'pending' : (values.status || 'pending'),
          priority,
        },
        workspaceType,
        workspaceType === 'enterprise' ? currentWorkspace?.company_id : undefined,
        currentWorkspace?.factory_id
      )
      message.success('生产任务创建成功')
      navigate('/production')
    } catch (error) {
      message.error('创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/production')}
          >
            返回生产管理
          </Button>
          <Title level={2}>创建生产任务</Title>
        </Space>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            startDate: dayjs(),
            endDate: dayjs().add(7, 'day'),
            priority: 'medium',
            status: 'planning',
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="taskName"
                label="任务名称"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="例如: 压力容器焊接任务" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="projectName"
                label="项目名称"
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input placeholder="例如: 化工设备制造项目" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="taskType"
                label="任务类型"
                rules={[{ required: true, message: '请选择任务类型' }]}
              >
                <Select placeholder="选择任务类型">
                  <Option value="焊接">焊接</Option>
                  <Option value="切割">切割</Option>
                  <Option value="组装">组装</Option>
                  <Option value="检验">检验</Option>
                  <Option value="返修">返修</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select placeholder="选择优先级">
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                  <Option value="urgent">紧急</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="assigned_welder_id"
                label="指定焊工"
              >
                <Select
                  allowClear
                  showSearch
                  placeholder="选择焊工，用于工艺追溯"
                  optionFilterProp="label"
                  options={welders.map((welder) => ({
                    value: welder.id,
                    label: `${welder.full_name || '未命名'}（${welder.welder_code || '无编号'}）`,
                  }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="assigned_equipment_id"
                label="使用设备"
              >
                <Select
                  allowClear
                  showSearch
                  placeholder="选择设备，用于工艺追溯"
                  optionFilterProp="label"
                  options={equipments.map((equipment) => ({
                    value: Number(equipment.id),
                    label: `${equipment.equipment_name || '未命名'}（${equipment.equipment_code || '无编号'}）`,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="startDate"
                label="开始时间"
                rules={[{ required: true, message: '请选择开始时间' }]}
              >
                <DatePicker
                  showTime
                  style={{ width: '100%' }}
                  placeholder="选择开始时间"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="endDate"
                label="预计完成时间"
                rules={[{ required: true, message: '请选择预计完成时间' }]}
              >
                <DatePicker
                  showTime
                  style={{ width: '100%' }}
                  placeholder="选择预计完成时间"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="workload"
                label="工作量"
                rules={[{ required: true, message: '请输入工作量' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                  addonAfter="米"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="materialSpec"
                label="材料规格"
                rules={[{ required: true, message: '请输入材料规格' }]}
              >
                <Input placeholder="例如: Q345R δ=12mm" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="wps_id"
            label="执行 WPS"
          >
            <Select
              allowClear
              showSearch
              placeholder="选择本任务使用的 WPS"
              optionFilterProp="label"
              options={wpsList.map((item) => ({
                value: item.id,
                label: `${item.wps_number || item.id} ${item.title ? `- ${item.title}` : ''}`,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <TextArea
              rows={4}
              placeholder="请详细描述生产任务要求、技术要点等..."
            />
          </Form.Item>

          <Form.Item
            name="technicalRequirements"
            label="技术要求"
          >
            <TextArea
              rows={3}
              placeholder="焊接质量要求、检验标准、验收条件等..."
            />
          </Form.Item>

          <Form.Item
            name="safetyRequirements"
            label="安全要求"
          >
            <TextArea
              rows={3}
              placeholder="安全防护措施、操作规程、应急预案等..."
            />
          </Form.Item>

          <Form.Item
            name="attachments"
            label="相关文档"
          >
            <Upload.Dragger
              multiple
              action="/api/upload"
              showUploadList={true}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持技术图纸、工艺文件、检验标准等文档
              </p>
            </Upload.Dragger>
          </Form.Item>

          <Divider />

          <div className="text-right">
            <Space>
              <Button onClick={() => navigate('/production')}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
              >
                创建任务
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default ProductionCreate