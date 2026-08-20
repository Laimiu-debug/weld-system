import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form,
  Input,
  Button,
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Space,
  message,
  Alert,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import weldersService from '@/services/welders'
import ListPageHeader from '@/components/ListPageHeader'

const { Option } = Select
const { TextArea } = Input

const WeldersCreate: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      const apiData = {
        welder_code: values.welder_code,
        full_name: values.full_name,
        gender: values.gender,
        date_of_birth: values.date_of_birth
          ? dayjs(values.date_of_birth).format('YYYY-MM-DD')
          : undefined,
        id_type: values.id_type || '身份证',
        id_number: values.id_number,
        nationality: values.nationality || '中国',
        phone: values.phone,
        email: values.email,
        emergency_contact: values.emergency_contact,
        emergency_phone: values.emergency_phone,
        address: values.address,
        employee_number: values.employee_number,
        department: values.department,
        position: values.position,
        hire_date: values.hire_date
          ? dayjs(values.hire_date).format('YYYY-MM-DD')
          : undefined,
        skill_level: values.skill_level,
        specialization: values.specialization,
        status: 'active',
        certification_status: 'valid',
        notes: values.notes,
      }

      const response = await weldersService.create(apiData)
      const created = (response as any)?.data || response
      const welderId = created?.id || created?.data?.id

      message.success('焊工档案已创建，请继续添加持证项目')
      if (welderId) {
        navigate(`/welders/${welderId}`, { state: { highlightCerts: true } })
      } else {
        navigate('/welders')
      }
    } catch (error: any) {
      if (error?.errorFields) return
      message.error(error.response?.data?.detail || '创建失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title="新增焊工"
        description="先建立人员档案，持证项目请在详情页按体系添加"
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/welders')}>
            返回列表
          </Button>
        }
      />

      <Alert
        type="info"
        showIcon
        className="mb-4"
        message="持证与体系在详情页管理"
        description="创建成功后将进入焊工详情，可按 ASME / 国标等体系分别添加持证项目，并维护到期与审证信息。"
      />

      <Card className="list-page-card">
        <Form form={form} layout="vertical" initialValues={{ nationality: '中国', id_type: '身份证' }}>
          <Row gutter={[16, 0]}>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="welder_code"
                label="焊工编号"
                rules={[{ required: true, message: '请输入焊工编号' }]}
              >
                <Input placeholder="例如: WLD-2024-001" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="full_name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input placeholder="请输入姓名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="gender" label="性别">
                <Select allowClear placeholder="请选择">
                  <Option value="男">男</Option>
                  <Option value="女">女</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="date_of_birth" label="出生日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="id_type" label="证件类型">
                <Select>
                  <Option value="身份证">身份证</Option>
                  <Option value="护照">护照</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="id_number"
                label="证件号码"
                rules={[{ required: true, message: '请输入证件号码' }]}
              >
                <Input placeholder="请输入证件号码" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="nationality" label="国籍">
                <Input placeholder="中国" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="phone"
                label="联系电话"
                rules={[{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效手机号' }]}
              >
                <Input placeholder="手机号码" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="email" label="邮箱" rules={[{ type: 'email', message: '邮箱格式不正确' }]}>
                <Input placeholder="邮箱" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="department" label="部门">
                <Input placeholder="所属部门" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="position" label="岗位">
                <Input placeholder="岗位" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="hire_date" label="入职日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="skill_level" label="技能等级">
                <Select allowClear placeholder="请选择">
                  <Option value="junior">初级</Option>
                  <Option value="intermediate">中级</Option>
                  <Option value="senior">高级</Option>
                  <Option value="expert">专家</Option>
                  <Option value="master">大师</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="specialization" label="专业方向">
                <Input placeholder="例如：压力管道 / 结构钢" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="address" label="住址">
                <Input placeholder="联系地址" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="notes" label="备注">
                <TextArea rows={3} placeholder="其他说明" />
              </Form.Item>
            </Col>
          </Row>

          <Space>
            <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={handleSubmit}>
              创建并去添加持证项目
            </Button>
            <Button onClick={() => navigate('/welders')}>取消</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}

export default WeldersCreate
