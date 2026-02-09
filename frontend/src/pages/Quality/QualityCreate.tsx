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
  Table,
  Tag,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined, UploadOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

interface DefectRecord {
  id: string
  type: string
  description: string
  severity: 'minor' | 'major' | 'critical'
  location: string
  size: string
  quantity: number
}

const QualityCreate: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [defects, setDefects] = useState<DefectRecord[]>([])

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      message.success('质量检验记录创建成功')
      navigate('/quality')
    } catch (error) {
      message.error('创建失败')
    } finally {
      setLoading(false)
    }
  }

  const addDefect = () => {
    const newDefect: DefectRecord = {
      id: Date.now().toString(),
      type: '',
      description: '',
      severity: 'minor',
      location: '',
      size: '',
      quantity: 1,
    }
    setDefects([...defects, newDefect])
  }

  const removeDefect = (id: string) => {
    setDefects(defects.filter(d => d.id !== id))
  }

  const updateDefect = (id: string, field: keyof DefectRecord, value: any) => {
    setDefects(defects.map(d => d.id === id ? { ...d, [field]: value } : d))
  }

  const defectColumns = [
    {
      title: '缺陷类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string, record: DefectRecord) => (
        <Select
          value={type}
          onChange={(value) => updateDefect(record.id, 'type', value)}
          style={{ width: '100%' }}
          placeholder="选择缺陷类型"
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
      title: '位置',
      dataIndex: 'location',
      key: 'location',
      render: (location: string, record: DefectRecord) => (
        <Input
          value={location}
          onChange={(e) => updateDefect(record.id, 'location', e.target.value)}
          placeholder="缺陷位置"
        />
      ),
    },
    {
      title: '尺寸',
      dataIndex: 'size',
      key: 'size',
      render: (size: string, record: DefectRecord) => (
        <Input
          value={size}
          onChange={(e) => updateDefect(record.id, 'size', e.target.value)}
          placeholder="缺陷尺寸"
        />
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
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
      title: '操作',
      key: 'actions',
      render: (_, record: DefectRecord) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => removeDefect(record.id)}
        />
      ),
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/quality')}
          >
            返回质量管理
          </Button>
          <Title level={2}>创建质量检验</Title>
        </Space>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            inspectionDate: dayjs(),
            inspectionType: 'routine',
            inspector: '质量检验员',
            status: 'in_progress',
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="inspectionNumber"
                label="检验编号"
                rules={[{ required: true, message: '请输入检验编号' }]}
              >
                <Input placeholder="例如: QI-2024-001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="projectName"
                label="项目名称"
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input placeholder="例如: 压力容器制造项目" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="inspectionType"
                label="检验类型"
                rules={[{ required: true, message: '请选择检验类型' }]}
              >
                <Select placeholder="选择检验类型">
                  <Option value="routine">例行检验</Option>
                  <Option value="acceptance">验收检验</Option>
                  <Option value="process">过程检验</Option>
                  <Option value="final">最终检验</Option>
                  <Option value="rework">返修检验</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="weldingMethod"
                label="焊接方法"
                rules={[{ required: true, message: '请选择焊接方法' }]}
              >
                <Select placeholder="选择焊接方法">
                  <Option value="SMAW">焊条电弧焊</Option>
                  <Option value="GMAW">熔化极气体保护焊</Option>
                  <Option value="GTAW">钨极氩弧焊</Option>
                  <Option value="FCAW">药芯焊丝电弧焊</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="inspector"
                label="检验员"
                rules={[{ required: true, message: '请输入检验员姓名' }]}
              >
                <Input placeholder="检验员姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
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
            <Col span={12}>
              <Form.Item
                name="welder"
                label="焊工"
                rules={[{ required: true, message: '请输入焊工姓名' }]}
              >
                <Input placeholder="焊工姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
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
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="materialSpec"
                label="材料规格"
                rules={[{ required: true, message: '请输入材料规格' }]}
              >
                <Input placeholder="例如: Q345R δ=12mm" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="jointType"
                label="接头类型"
                rules={[{ required: true, message: '请选择接头类型' }]}
              >
                <Select placeholder="选择接头类型">
                  <Option value="butt">对接接头</Option>
                  <Option value="lap">搭接接头</Option>
                  <Option value="corner">角接接头</Option>
                  <Option value="T">T型接头</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="inspectionResult"
            label="检验结果"
            rules={[{ required: true, message: '请选择检验结果' }]}
          >
            <Select placeholder="选择检验结果">
              <Option value="qualified">合格</Option>
              <Option value="conditional_qualified">有条件合格</Option>
              <Option value="unqualified">不合格</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="inspectionDescription"
            label="检验描述"
            rules={[{ required: true, message: '请输入检验描述' }]}
          >
            <TextArea
              rows={4}
              placeholder="请详细描述检验过程、方法、标准等..."
            />
          </Form.Item>

          <Divider />

          <Title level={4}>缺陷记录</Title>

          <div className="mb-4">
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={addDefect}
              block
            >
              添加缺陷记录
            </Button>
          </div>

          {defects.length > 0 && (
            <Table
              columns={defectColumns}
              dataSource={defects}
              rowKey="id"
              pagination={false}
              size="small"
            />
          )}

          <Divider />

          <Form.Item
            name="conclusion"
            label="检验结论"
            rules={[{ required: true, message: '请输入检验结论' }]}
          >
            <TextArea
              rows={3}
              placeholder="根据检验结果，给出最终检验结论..."
            />
          </Form.Item>

          <Form.Item
            name="recommendations"
            label="改进建议"
          >
            <TextArea
              rows={3}
              placeholder="针对发现的问题，提出改进建议..."
            />
          </Form.Item>

          <Form.Item
            name="attachments"
            label="检验报告附件"
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
                支持检验报告、照片、检测数据等文件
              </p>
            </Upload.Dragger>
          </Form.Item>

          <Divider />

          <div className="text-right">
            <Space>
              <Button onClick={() => navigate('/quality')}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
              >
                保存检验记录
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default QualityCreate