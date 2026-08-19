import React, { useState, useEffect } from 'react'
import {
  Table,
  Card,
  Button,
  Space,
  Typography,
  Input,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Modal,
  message,
  Row,
  Col,
  Popconfirm,
  Badge,
  Statistic,
  Divider,
  Form,
  Descriptions,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ExclamationCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  WarningOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import weldersService, { Welder, WelderCreate, WelderUpdate } from '@/services/welders'

const { Title, Text } = Typography
const { Search } = Input
const { RangePicker } = DatePicker
const { Option } = Select
const { TextArea } = Input

const WeldersList: React.FC = () => {
  const navigate = useNavigate()
  const [welders, setWelders] = useState<Welder[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [skillLevelFilter, setSkillLevelFilter] = useState<string | undefined>()
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [certStatusFilter, setCertStatusFilter] = useState<string | undefined>()

  // 模态框相关状态
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view'>('create')
  const [currentWelder, setCurrentWelder] = useState<Welder | null>(null)
  const [form] = Form.useForm()

  // 获取焊工列表
  const fetchWelders = async () => {
    setLoading(true)
    try {
      const response = await weldersService.getList({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchText || undefined,
        skill_level: skillLevelFilter,
        status: statusFilter,
        certification_status: certStatusFilter,
      })

      // weldersService.getList() 返回的是 response.data
      // 由于 API 拦截器已经包装了一层，这里的 response 就是后端的原始响应
      if (response.success && response.data) {
        const { items, total: totalCount } = response.data
        setWelders(items || [])
        setTotal(totalCount || 0)
      } else {
        message.error('获取焊工列表失败')
      }
    } catch (error: any) {
      console.error('获取焊工列表失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else {
        message.error('获取焊工列表失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWelders()
  }, [currentPage, pageSize, searchText, skillLevelFilter, statusFilter, certStatusFilter])

  // 处理创建焊工
  const handleCreate = () => {
    setModalType('create')
    setCurrentWelder(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  // 处理编辑焊工
  const handleEdit = (welder: Welder) => {
    setModalType('edit')
    setCurrentWelder(welder)
    form.setFieldsValue({
      welder_code: welder.welder_code,
      full_name: welder.full_name,
      english_name: welder.english_name,
      gender: welder.gender,
      date_of_birth: welder.date_of_birth ? dayjs(welder.date_of_birth) : undefined,
      id_type: welder.id_type,
      id_number: welder.id_number,
      nationality: welder.nationality,
      phone: welder.phone,
      email: welder.email,
      address: welder.address,
      emergency_contact: welder.emergency_contact,
      emergency_phone: welder.emergency_phone,
      hire_date: welder.hire_date ? dayjs(welder.hire_date) : undefined,
      employment_type: welder.employment_type,
      department: welder.department,
      position: welder.position,
      skill_level: welder.skill_level,
      specialization: welder.specialization,
      qualified_processes: welder.qualified_processes,
      qualified_positions: welder.qualified_positions,
      qualified_materials: welder.qualified_materials,
      primary_certification_number: welder.primary_certification_number,
      primary_certification_level: welder.primary_certification_level,
      primary_certification_date: welder.primary_certification_date ? dayjs(welder.primary_certification_date) : undefined,
      primary_expiry_date: welder.primary_expiry_date ? dayjs(welder.primary_expiry_date) : undefined,
      primary_issuing_authority: welder.primary_issuing_authority,
      status: welder.status,
      certification_status: welder.certification_status,
      description: welder.description,
      notes: welder.notes,
      tags: welder.tags,
    })
    setIsModalVisible(true)
  }

  // 处理查看焊工 - 跳转到详情页
  const handleView = (welder: Welder) => {
    navigate(`/welders/${welder.id}`)
  }

  // 处理模态框取消
  const handleModalCancel = () => {
    setIsModalVisible(false)
    form.resetFields()
    setCurrentWelder(null)
  }

  // 处理模态框确定
  const handleModalOk = async () => {
    if (modalType === 'view') {
      handleModalCancel()
      return
    }

    try {
      const values = await form.validateFields()
      setLoading(true)

      // 转换日期格式
      const formData: any = {
        ...values,
        date_of_birth: values.date_of_birth ? values.date_of_birth.format('YYYY-MM-DD') : undefined,
        hire_date: values.hire_date ? values.hire_date.format('YYYY-MM-DD') : undefined,
        primary_certification_date: values.primary_certification_date ? values.primary_certification_date.format('YYYY-MM-DD') : undefined,
        primary_expiry_date: values.primary_expiry_date ? values.primary_expiry_date.format('YYYY-MM-DD') : undefined,
      }

      if (modalType === 'create') {
        const response = await weldersService.create(formData as WelderCreate)
        if (response.success) {
          message.success('创建成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchWelders()
        } else {
          message.error('创建失败')
        }
      } else if (modalType === 'edit' && currentWelder) {
        const response = await weldersService.update(currentWelder.id, formData as WelderUpdate)
        if (response.success) {
          message.success('更新成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchWelders()
        } else {
          message.error('更新失败')
        }
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else if (error.errorFields) {
        message.error('请检查表单填写')
      } else {
        message.error('操作失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 删除焊工
  const handleDelete = (welder: Welder) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除焊工"${welder.full_name}"吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await weldersService.delete(welder.id)
          if (response.success) {
            message.success('删除焊工成功')
            fetchWelders()
          }
        } catch (error: any) {
          console.error('删除焊工失败:', error)
          message.error(error.response?.data?.detail || '删除焊工失败')
        }
      },
    })
  }

  // 状态标签颜色
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      inactive: 'default',
      on_leave: 'orange',
      resigned: 'red',
    }
    return colors[status] || 'default'
  }

  // 证书状态标签颜色
  const getCertStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      valid: 'green',
      expiring_soon: 'orange',
      expired: 'red',
      pending: 'blue',
    }
    return colors[status] || 'default'
  }

  // 技能等级标签颜色
  const getSkillLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      junior: 'blue',
      intermediate: 'cyan',
      senior: 'green',
      expert: 'gold',
      master: 'red',
    }
    return colors[level] || 'default'
  }

  
  // 表格列配置
  const columns = [
    {
      title: '焊工编号',
      dataIndex: 'welder_code',
      key: 'welder_code',
      width: 150,
      render: (text: string, record: Welder) => (
        <Button type="link" onClick={() => navigate(`/welders/${record.id}`)}>
          {text}
        </Button>
      ),
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 100,
    },
    {
      title: '身份证号',
      dataIndex: 'id_number',
      key: 'id_number',
      width: 180,
      render: (idNumber: string) => {
        // 隐藏中间部分身份证号
        if (idNumber && idNumber.length >= 10) {
          return `${idNumber.substring(0, 6)}********${idNumber.substring(idNumber.length - 4)}`
        }
        return idNumber
      },
    },
    {
      title: '联系电话',
      dataIndex: 'phone',
      key: 'phone',
      width: 120,
      render: (phone: string) => {
        // 隐藏中间部分手机号
        if (phone && phone.length >= 7) {
          return `${phone.substring(0, 3)}****${phone.substring(phone.length - 4)}`
        }
        return phone
      },
    },
    {
      title: '证书编号',
      dataIndex: 'primary_certification_number',
      key: 'primary_certification_number',
      width: 180,
    },
    {
      title: '证书等级',
      dataIndex: 'primary_certification_level',
      key: 'primary_certification_level',
      width: 100,
      render: (level: string) => {
        const levelConfig: Record<string, { color: string; text: string }> = {
          '初级': { color: 'default', text: '初级' },
          '中级': { color: 'processing', text: '中级' },
          '高级': { color: 'success', text: '高级' },
          '技师': { color: 'warning', text: '技师' },
          '高级技师': { color: 'error', text: '高级技师' },
        }
        const config = levelConfig[level] || levelConfig['初级']
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '证书有效期',
      dataIndex: 'primary_expiry_date',
      key: 'primary_expiry_date',
      width: 120,
      render: (expiryDate: string) => {
        if (!expiryDate) return '-'

        const isExpired = dayjs(expiryDate).isBefore(dayjs())
        const isExpiringSoon = dayjs(expiryDate).diff(dayjs(), 'days') <= 30

        return (
          <Space>
            <Text>{dayjs(expiryDate).format('YYYY-MM-DD')}</Text>
            {isExpired && <Tag color="error">已过期</Tag>}
            {!isExpired && isExpiringSoon && <Tag color="warning">即将过期</Tag>}
          </Space>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '在职' : '离职'}
        </Tag>
      ),
    },
    {
      title: '资质工艺',
      dataIndex: 'qualified_processes',
      key: 'qualified_processes',
      width: 150,
      render: (processes: string | string[]) => {
        if (!processes) return '-'

        let processArray: string[] = []
        if (typeof processes === 'string') {
          try {
            processArray = JSON.parse(processes)
          } catch {
            return '-'
          }
        } else {
          processArray = processes
        }

        return (
          <Space wrap>
            {processArray.slice(0, 3).map(process => (
              <Tag key={process} color="blue" style={{ fontSize: '12px' }}>
                {process}
              </Tag>
            ))}
            {processArray.length > 3 && (
              <Tag color="gray" style={{ fontSize: '12px' }}>
                +{processArray.length - 3}
              </Tag>
            )}
          </Space>
        )
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: unknown, record: Welder) => (
        <Space>
          <Tooltip title="查看">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 统计信息 */}
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="总焊工数"
                value={total}
                prefix={<UserOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="在职焊工"
                value={welders.filter(w => w.status === 'active').length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="证书有效"
                value={welders.filter(w => w.certification_status === 'valid').length}
                prefix={<SafetyCertificateOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="证书即将过期"
                value={welders.filter(w => w.certification_status === 'expiring_soon').length}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>

          <Divider />

          {/* 搜索和筛选 */}
          <Row gutter={16}>
            <Col span={8}>
              <Search
                placeholder="搜索焊工编号、姓名、电话..."
                allowClear
                enterButton={<SearchOutlined />}
                onSearch={setSearchText}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="技能等级"
                allowClear
                style={{ width: '100%' }}
                onChange={setSkillLevelFilter}
              >
                <Option value="junior">初级</Option>
                <Option value="intermediate">中级</Option>
                <Option value="senior">高级</Option>
                <Option value="expert">专家</Option>
                <Option value="master">大师</Option>
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: '100%' }}
                onChange={setStatusFilter}
              >
                <Option value="active">在职</Option>
                <Option value="inactive">离职</Option>
                <Option value="on_leave">休假</Option>
                <Option value="resigned">辞职</Option>
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="证书状态"
                allowClear
                style={{ width: '100%' }}
                onChange={setCertStatusFilter}
              >
                <Option value="valid">有效</Option>
                <Option value="expiring_soon">即将过期</Option>
                <Option value="expired">已过期</Option>
                <Option value="pending">待审核</Option>
              </Select>
            </Col>
            <Col span={4}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreate}
                >
                  新增焊工
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchWelders}
                >
                  刷新
                </Button>
              </Space>
            </Col>
          </Row>

          {/* 表格 */}
          <Table
            columns={columns}
            dataSource={welders}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1800 }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, size) => {
                setCurrentPage(page)
                setPageSize(size)
              },
            }}
          />
        </Space>
      </Card>

      {/* 焊工模态框 */}
      <Modal
        title={
          modalType === 'create'
            ? '新增焊工'
            : modalType === 'edit'
            ? '编辑焊工'
            : '查看焊工'
        }
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={1000}
        okText={modalType === 'view' ? '关闭' : '确定'}
        cancelText="取消"
        cancelButtonProps={{ style: { display: modalType === 'view' ? 'none' : 'inline-block' } }}
      >
        {modalType === 'view' && currentWelder ? (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="焊工编号">{currentWelder.welder_code}</Descriptions.Item>
            <Descriptions.Item label="姓名">{currentWelder.full_name}</Descriptions.Item>
            <Descriptions.Item label="英文名">{currentWelder.english_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="性别">{currentWelder.gender || '-'}</Descriptions.Item>
            <Descriptions.Item label="出生日期">{currentWelder.date_of_birth || '-'}</Descriptions.Item>
            <Descriptions.Item label="国籍">{currentWelder.nationality || '-'}</Descriptions.Item>
            <Descriptions.Item label="证件类型">{currentWelder.id_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="证件号码">{currentWelder.id_number || '-'}</Descriptions.Item>
            <Descriptions.Item label="联系电话">{currentWelder.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="电子邮箱">{currentWelder.email || '-'}</Descriptions.Item>
            <Descriptions.Item label="联系地址" span={2}>{currentWelder.address || '-'}</Descriptions.Item>
            <Descriptions.Item label="紧急联系人">{currentWelder.emergency_contact || '-'}</Descriptions.Item>
            <Descriptions.Item label="紧急联系电话">{currentWelder.emergency_phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="入职日期">{currentWelder.hire_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="雇佣类型">{currentWelder.employment_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="部门">{currentWelder.department || '-'}</Descriptions.Item>
            <Descriptions.Item label="职位">{currentWelder.position || '-'}</Descriptions.Item>
            <Descriptions.Item label="技能等级">{currentWelder.skill_level || '-'}</Descriptions.Item>
            <Descriptions.Item label="专业方向">{currentWelder.specialization || '-'}</Descriptions.Item>
            <Descriptions.Item label="合格工艺" span={2}>{currentWelder.qualified_processes || '-'}</Descriptions.Item>
            <Descriptions.Item label="合格位置" span={2}>{currentWelder.qualified_positions || '-'}</Descriptions.Item>
            <Descriptions.Item label="合格材料" span={2}>{currentWelder.qualified_materials || '-'}</Descriptions.Item>
            <Descriptions.Item label="主要证书编号">{currentWelder.primary_certification_number || '-'}</Descriptions.Item>
            <Descriptions.Item label="证书等级">{currentWelder.primary_certification_level || '-'}</Descriptions.Item>
            <Descriptions.Item label="证书颁发日期">{currentWelder.primary_certification_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="证书有效期">{currentWelder.primary_expiry_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="颁发机构" span={2}>{currentWelder.primary_issuing_authority || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">{currentWelder.status || '-'}</Descriptions.Item>
            <Descriptions.Item label="证书状态">{currentWelder.certification_status || '-'}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{currentWelder.description || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{currentWelder.notes || '-'}</Descriptions.Item>
            <Descriptions.Item label="标签" span={2}>{currentWelder.tags || '-'}</Descriptions.Item>
          </Descriptions>
        ) : (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="焊工编号"
                  name="welder_code"
                  rules={[{ required: true, message: '请输入焊工编号' }]}
                >
                  <Input placeholder="请输入焊工编号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="姓名"
                  name="full_name"
                  rules={[{ required: true, message: '请输入姓名' }]}
                >
                  <Input placeholder="请输入姓名" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="英文名" name="english_name">
                  <Input placeholder="请输入英文名" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="性别" name="gender">
                  <Select placeholder="请选择性别">
                    <Option value="male">男</Option>
                    <Option value="female">女</Option>
                    <Option value="other">其他</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="出生日期" name="date_of_birth">
                  <DatePicker style={{ width: '100%' }} placeholder="请选择出生日期" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="国籍"
                  name="nationality"
                  initialValue="中国"
                >
                  <Input placeholder="请输入国籍" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="证件类型" name="id_type">
                  <Select placeholder="请选择证件类型">
                    <Option value="id_card">身份证</Option>
                    <Option value="passport">护照</Option>
                    <Option value="other">其他</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="证件号码" name="id_number">
                  <Input placeholder="请输入证件号码" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="联系电话" name="phone">
                  <Input placeholder="请输入联系电话" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="电子邮箱" name="email">
                  <Input placeholder="请输入电子邮箱" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="联系地址" name="address">
                  <Input placeholder="请输入联系地址" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="紧急联系人" name="emergency_contact">
                  <Input placeholder="请输入紧急联系人" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="紧急联系电话" name="emergency_phone">
                  <Input placeholder="请输入紧急联系电话" />
                </Form.Item>
              </Col>
            </Row>

            <Divider>雇佣信息</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="入职日期" name="hire_date">
                  <DatePicker style={{ width: '100%' }} placeholder="请选择入职日期" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="雇佣类型" name="employment_type">
                  <Select placeholder="请选择雇佣类型">
                    <Option value="full_time">全职</Option>
                    <Option value="part_time">兼职</Option>
                    <Option value="contract">合同工</Option>
                    <Option value="temporary">临时工</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="部门" name="department">
                  <Input placeholder="请输入部门" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="职位" name="position">
                  <Input placeholder="请输入职位" />
                </Form.Item>
              </Col>
            </Row>

            <Divider>技能信息</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="技能等级" name="skill_level">
                  <Select placeholder="请选择技能等级">
                    <Option value="junior">初级</Option>
                    <Option value="intermediate">中级</Option>
                    <Option value="senior">高级</Option>
                    <Option value="expert">专家</Option>
                    <Option value="master">大师</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="专业方向" name="specialization">
                  <Input placeholder="请输入专业方向" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="合格工艺" name="qualified_processes">
                  <Input placeholder="请输入合格工艺，多个用逗号分隔" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="合格位置" name="qualified_positions">
                  <Input placeholder="请输入合格位置，多个用逗号分隔" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="合格材料" name="qualified_materials">
                  <Input placeholder="请输入合格材料，多个用逗号分隔" />
                </Form.Item>
              </Col>
            </Row>

            <Divider>证书信息</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="主要证书编号" name="primary_certification_number">
                  <Input placeholder="请输入主要证书编号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="证书等级" name="primary_certification_level">
                  <Input placeholder="请输入证书等级" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="证书颁发日期" name="primary_certification_date">
                  <DatePicker style={{ width: '100%' }} placeholder="请选择证书颁发日期" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="证书有效期" name="primary_expiry_date">
                  <DatePicker style={{ width: '100%' }} placeholder="请选择证书有效期" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="颁发机构" name="primary_issuing_authority">
                  <Input placeholder="请输入颁发机构" />
                </Form.Item>
              </Col>
            </Row>

            <Divider>状态信息</Divider>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="状态" name="status" initialValue="active">
                  <Select placeholder="请选择状态">
                    <Option value="active">在职</Option>
                    <Option value="inactive">离职</Option>
                    <Option value="on_leave">休假</Option>
                    <Option value="resigned">辞职</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="证书状态" name="certification_status" initialValue="valid">
                  <Select placeholder="请选择证书状态">
                    <Option value="valid">有效</Option>
                    <Option value="expiring_soon">即将过期</Option>
                    <Option value="expired">已过期</Option>
                    <Option value="pending">待审核</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Divider>其他信息</Divider>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="描述" name="description">
                  <TextArea rows={3} placeholder="请输入描述" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="备注" name="notes">
                  <TextArea rows={3} placeholder="请输入备注" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="标签" name="tags">
                  <Input placeholder="请输入标签，多个用逗号分隔" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default WeldersList
