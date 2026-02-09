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
  Upload,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined, UploadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const ProductionCreate: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
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
                name="assignedWelder"
                label="指定焊工"
                rules={[{ required: true, message: '请选择焊工' }]}
              >
                <Select placeholder="选择焊工">
                  <Option value="张师傅">张师傅</Option>
                  <Option value="李师傅">李师傅</Option>
                  <Option value="王师傅">王师傅</Option>
                  <Option value="刘师傅">刘师傅</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="equipment"
                label="使用设备"
                rules={[{ required: true, message: '请选择设备' }]}
              >
                <Select placeholder="选择设备">
                  <Option value="EQP-2024-001">数字化逆变焊机</Option>
                  <Option value="EQP-2024-002">等离子切割机</Option>
                  <Option value="EQP-2024-003">超声波探伤仪</Option>
                  <Option value="EQP-2024-004">CO2焊机</Option>
                </Select>
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
            name="wpsStandard"
            label="WPS标准"
            rules={[{ required: true, message: '请选择WPS标准' }]}
          >
            <Select placeholder="选择WPS标准">
              <Option value="WPS-001">碳钢焊接工艺规程</Option>
              <Option value="WPS-002">不锈钢焊接工艺规程</Option>
              <Option value="WPS-003">铝合金焊接工艺规程</Option>
            </Select>
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