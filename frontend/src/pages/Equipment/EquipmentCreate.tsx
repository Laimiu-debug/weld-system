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
  Switch,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined, SettingOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { equipmentService, CreateEquipmentData, EquipmentType } from '@/services/equipment'
import dayjs from 'dayjs'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const EquipmentCreate: React.FC = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      // 转换表单数据为API格式
      const equipmentData: CreateEquipmentData = {
        equipment_code: values.equipment_code,
        equipment_name: values.equipment_name,
        equipment_type: values.equipment_type,
        category: values.category,
        manufacturer: values.manufacturer,
        brand: values.brand,
        model: values.model,
        serial_number: values.serial_number,
        specifications: values.specifications,
        rated_power: values.rated_power,
        rated_voltage: values.rated_voltage,
        rated_current: values.rated_current,
        max_capacity: values.max_capacity,
        working_range: values.working_range,
        purchase_date: values.purchase_date ? values.purchase_date.format('YYYY-MM-DD') : undefined,
        purchase_price: values.purchase_price,
        currency: values.currency || 'CNY',
        supplier: values.supplier,
        warranty_period: values.warranty_period,
        warranty_expiry_date: values.warranty_expiry_date ? values.warranty_expiry_date.format('YYYY-MM-DD') : undefined,
        location: values.location,
        workshop: values.workshop,
        area: values.area,
        status: values.status || 'operational',
        is_active: values.is_active !== false,
        is_critical: values.is_critical || false,
        installation_date: values.installation_date ? values.installation_date.format('YYYY-MM-DD') : undefined,
        commissioning_date: values.commissioning_date ? values.commissioning_date.format('YYYY-MM-DD') : undefined,
        maintenance_interval_days: values.maintenance_interval_days,
        inspection_interval_days: values.inspection_interval_days,
        responsible_person_id: values.responsible_person_id,
        description: values.description,
        notes: values.notes,
        manual_url: values.manual_url,
        images: values.images,
        documents: values.documents,
        tags: values.tags,
        access_level: values.access_level || 'private'
      }

      // 验证数据
      const validation = equipmentService.validateEquipmentData(equipmentData)
      if (!validation.isValid) {
        validation.errors.forEach(error => message.error(error))
        return
      }

      // 调用API创建设备
      const response = await equipmentService.createEquipment(equipmentData)

      if (response.success) {
        message.success('设备创建成功')
        navigate('/equipment')
      } else {
        message.error(response.message || '创建失败')
      }
    } catch (error: any) {
      console.error('创建设备失败:', error)
      // API拦截器已经显示了错误消息
      if (!error.response) {
        message.error('网络错误，请检查连接')
      }
    } finally {
      setLoading(false)
    }
  }

  // 生成设备编号
  const generateEquipmentCode = (type: EquipmentType) => {
    const code = equipmentService.generateEquipmentCode(type)
    form.setFieldsValue({ equipment_code: code })
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/equipment')}
          >
            返回设备列表
          </Button>
          <Title level={2}>添加新设备</Title>
        </Space>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            status: 'operational',
            is_active: true,
            is_critical: false,
            currency: 'CNY',
            access_level: 'private',
          }}
        >
          {/* 基本信息 */}
          <Title level={4}>基本信息</Title>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="equipment_type"
                label="设备类型"
                rules={[{ required: true, message: '请选择设备类型' }]}
              >
                <Select
                  placeholder="选择设备类型"
                  onChange={(value) => generateEquipmentCode(value)}
                >
                  {equipmentService.getEquipmentTypeOptions().map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="equipment_code"
                label="设备编号"
                rules={[{ required: true, message: '请输入设备编号' }]}
                extra="系统可根据设备类型自动生成编号"
              >
                <Input placeholder="例如: WM-241001" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="equipment_name"
                label="设备名称"
                rules={[{ required: true, message: '请输入设备名称' }]}
              >
                <Input placeholder="例如: 数字化逆变焊机" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category"
                label="设备类别"
              >
                <Input placeholder="例如: 手工焊设备" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 制造商信息 */}
          <Title level={4}>制造商信息</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="manufacturer"
                label="制造商"
              >
                <Input placeholder="例如: 松下" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="brand"
                label="品牌"
              >
                <Input placeholder="例如: Panasonic" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="model"
                label="型号"
              >
                <Input placeholder="例如: YD-400KR2" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="serial_number"
                label="序列号"
              >
                <Input placeholder="设备唯一序列号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="supplier"
                label="供应商"
              >
                <Input placeholder="设备供应商" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 技术参数 */}
          <Title level={4}>技术参数</Title>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                name="rated_power"
                label="额定功率 (kW)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="rated_voltage"
                label="额定电压 (V)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="rated_current"
                label="额定电流 (A)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="max_capacity"
                label="最大容量"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="working_range"
                label="工作范围"
              >
                <Input placeholder="例如: 1-12mm钢板" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="specifications"
                label="技术规格"
              >
                <TextArea
                  rows={3}
                  placeholder="详细技术规格..."
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 采购信息 */}
          <Title level={4}>采购信息</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="purchase_date"
                label="采购日期"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="purchase_price"
                label="采购价格"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  precision={2}
                  placeholder="0.00"
                  addonBefore="¥"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="currency"
                label="货币"
              >
                <Select>
                  <Option value="CNY">人民币 (¥)</Option>
                  <Option value="USD">美元 ($)</Option>
                  <Option value="EUR">欧元 (€)</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="warranty_period"
                label="保修期 (月)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  placeholder="12"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="warranty_expiry_date"
                label="保修到期日期"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="installation_date"
                label="安装日期"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 位置和状态 */}
          <Title level={4}>位置和状态</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="location"
                label="存放位置"
              >
                <Input placeholder="例如: A区-焊接工位01" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="workshop"
                label="车间"
              >
                <Input placeholder="例如: 焊接车间" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="area"
                label="区域"
              >
                <Input placeholder="例如: A区" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="status"
                label="设备状态"
              >
                <Select placeholder="选择设备状态">
                  {equipmentService.getEquipmentStatusOptions().map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="is_active"
                label="启用状态"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="is_critical"
                label="关键设备"
                valuePropName="checked"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 维护信息 */}
          <Title level={4}>维护信息</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="maintenance_interval_days"
                label="维护间隔 (天)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  placeholder="90"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="inspection_interval_days"
                label="检验间隔 (天)"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  placeholder="365"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="access_level"
                label="访问级别"
              >
                <Select>
                  {equipmentService.getAccessLevelOptions().map(option => (
                    <Option key={option.value} value={option.value} title={option.description}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 附加信息 */}
          <Title level={4}>附加信息</Title>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="description"
                label="设备描述"
              >
                <TextArea rows={3} placeholder="设备功能描述..." />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="notes"
                label="备注信息"
              >
                <TextArea rows={3} placeholder="其他需要说明的信息..." />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="manual_url"
                label="使用手册链接"
              >
                <Input placeholder="http://..." />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="tags"
                label="标签"
              >
                <Input placeholder="标签1, 标签2, 标签3" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <div className="text-right">
            <Space>
              <Button onClick={() => navigate('/equipment')}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
              >
                保存设备
              </Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default EquipmentCreate