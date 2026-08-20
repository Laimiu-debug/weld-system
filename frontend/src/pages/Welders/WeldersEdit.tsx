import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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
  Spin,
  Alert,
} from 'antd'
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import weldersService from '@/services/welders'
import type { Welder } from '@/services/welders'
import ListPageHeader from '@/components/ListPageHeader'

const { Option } = Select
const { TextArea } = Input

const WeldersEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [pageLoading, setPageLoading] = useState(true)

  useEffect(() => {
    const fetchWelderDetail = async () => {
      if (!id) return
      setPageLoading(true)
      try {
        const response = await weldersService.getDetail(Number(id))
        const data = ((response as any)?.data || response) as Welder
        if (!data?.id) {
          message.error('未找到焊工信息')
          return
        }
        form.setFieldsValue({
          welder_code: data.welder_code,
          full_name: data.full_name,
          gender: data.gender,
          date_of_birth: data.date_of_birth ? dayjs(data.date_of_birth) : undefined,
          id_type: data.id_type || '身份证',
          id_number: data.id_number,
          nationality: data.nationality || '中国',
          phone: data.phone,
          email: data.email,
          address: data.address,
          department: data.department,
          position: data.position,
          hire_date: data.hire_date ? dayjs(data.hire_date) : undefined,
          skill_level: data.skill_level,
          specialization: data.specialization,
          status: data.status,
          notes: data.notes,
        })
      } catch {
        message.error('获取焊工信息失败')
      } finally {
        setPageLoading(false)
      }
    }
    void fetchWelderDetail()
  }, [id, form])

  const handleSubmit = async () => {
    if (!id) return
    try {
      const values = await form.validateFields()
      setLoading(true)
      await weldersService.update(Number(id), {
        welder_code: values.welder_code,
        full_name: values.full_name,
        gender: values.gender,
        date_of_birth: values.date_of_birth
          ? dayjs(values.date_of_birth).format('YYYY-MM-DD')
          : undefined,
        id_type: values.id_type,
        id_number: values.id_number,
        nationality: values.nationality,
        phone: values.phone,
        email: values.email,
        address: values.address,
        department: values.department,
        position: values.position,
        hire_date: values.hire_date
          ? dayjs(values.hire_date).format('YYYY-MM-DD')
          : undefined,
        skill_level: values.skill_level,
        specialization: values.specialization,
        status: values.status,
        notes: values.notes,
      })
      message.success('人员信息已保存')
      navigate(`/welders/${id}`)
    } catch (error: any) {
      if (error?.errorFields) return
      message.error(error.response?.data?.detail || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  if (pageLoading) {
    return (
      <div className="list-page" style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title="编辑焊工"
        description="仅维护人员档案；持证项目请在详情页按体系管理"
        extra={
          <Space>
            <Button onClick={() => navigate(`/welders/${id}`)}>查看详情</Button>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/welders')}>
              返回列表
            </Button>
          </Space>
        }
      />

      <Alert
        type="info"
        showIcon
        className="mb-4"
        message="持证信息不在此页编辑"
        description="体系、持证项目、到期与审证请到焊工详情「持证项目」区域管理。"
        action={
          <Button size="small" type="link" onClick={() => navigate(`/welders/${id}`)}>
            去管理持证
          </Button>
        }
      />

      <Card className="list-page-card">
        <Form form={form} layout="vertical">
          <Row gutter={[16, 0]}>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="welder_code"
                label="焊工编号"
                rules={[{ required: true, message: '请输入焊工编号' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item
                name="full_name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="gender" label="性别">
                <Select allowClear>
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
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="phone" label="联系电话">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="email" label="邮箱">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="status" label="在职状态">
                <Select>
                  <Option value="active">在职</Option>
                  <Option value="inactive">离职</Option>
                  <Option value="on_leave">休假</Option>
                  <Option value="suspended">停职</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="department" label="部门">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="position" label="岗位">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="hire_date" label="入职日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Form.Item name="skill_level" label="技能等级">
                <Select allowClear>
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
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="address" label="住址">
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="notes" label="备注">
                <TextArea rows={3} />
              </Form.Item>
            </Col>
          </Row>

          <Space>
            <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={handleSubmit}>
              保存人员信息
            </Button>
            <Button onClick={() => navigate(`/welders/${id}`)}>取消</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}

export default WeldersEdit
