import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Typography,
  Statistic,
  Avatar,
  Popconfirm,
  Badge,
  Progress,
  Alert,
  Tabs,
} from 'antd'
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  MailOutlined,
  PhoneOutlined,
  EyeOutlined,
  StopOutlined,
  HomeOutlined,
  BankOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService, { CompanyRole } from '@/services/enterprise'
import { useEnterpriseEmployees, useEmployeeQuota } from '@/hooks/useEnterprise'
import EnterpriseWorkspaceGate from '@/components/EnterpriseWorkspaceGate'
import { useNavigate } from 'react-router-dom'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { Option } = Select
const { Search } = Input

// 接口定义
interface EnterpriseEmployee {
  id: string
  user_id: string
  employee_number: string
  name: string
  email: string
  phone: string
  role: 'admin' | 'employee'
  company_role_id?: string
  company_role_name?: string
  status: 'active' | 'inactive'
  factory_id?: string
  factory_name?: string
  department_id?: string
  department_name?: string
  position?: string
  permissions: Record<string, boolean>
  data_access_scope: 'factory' | 'company'
  joined_at: string
  last_active_at?: string
  total_wps_created: number
  total_tasks_completed: number
}

const EnterpriseEmployees: React.FC = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('active')
  const [modalVisible, setModalVisible] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<EnterpriseEmployee | null>(null)
  const [form] = Form.useForm()
  const [createForm] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterRole, setFilterRole] = useState<string>('')
  const [filterFactory, setFilterFactory] = useState<string>('')
  const [roles, setRoles] = useState<CompanyRole[]>([])
  const [rolesLoading, setRolesLoading] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [factories, setFactories] = useState<any[]>([])
  const [factoriesLoading, setFactoriesLoading] = useState(false)
  const [departments, setDepartments] = useState<any[]>([])
  const [departmentsLoading, setDepartmentsLoading] = useState(false)

  // 使用企业员工管理Hook
  const {
    employees,
    loading,
    loadEmployees,
    updateEmployeePermissions,
    deactivateEmployee,
    activateEmployee,
    deleteEmployee,
  } = useEnterpriseEmployees({
    search: searchText,
    status: filterStatus,
    role: filterRole,
    factory_id: filterFactory,
  })

  const { quota, loading: quotaLoading } = useEmployeeQuota()

  // 加载角色列表
  const loadRoles = async () => {
    setRolesLoading(true)
    try {
      const response = await enterpriseService.getRoles({ is_active: true })
      if (response.data.success) {
        setRoles(response.data.data.items)
      }
    } catch (error: any) {
      console.error('加载角色列表失败:', error)
    } finally {
      setRolesLoading(false)
    }
  }

  // 加载工厂列表
  const loadFactories = async () => {
    setFactoriesLoading(true)
    try {
      const response = await enterpriseService.getFactories()
      if (response.data.success) {
        setFactories(response.data.data.items)
      }
    } catch (error: any) {
      console.error('加载工厂列表失败:', error)
    } finally {
      setFactoriesLoading(false)
    }
  }

  // 加载部门列表
  const loadDepartments = async () => {
    setDepartmentsLoading(true)
    try {
      const response = await enterpriseService.getDepartments()
      if (response.data.success) {
        setDepartments(response.data.data.items)
      }
    } catch (error: any) {
      console.error('加载部门列表失败:', error)
    } finally {
      setDepartmentsLoading(false)
    }
  }

  useEffect(() => {
    loadRoles()
    loadFactories()
    loadDepartments()
  }, [])

  // 统计数据
  const getStatistics = () => {
    const total = employees.length
    const active = employees.filter(emp => emp.status === 'active').length
    const inactive = employees.filter(emp => emp.status === 'inactive').length
    const admins = employees.filter(emp => emp.role === 'admin').length

    return { total, active, inactive, admins }
  }

  const stats = getStatistics()

  // 获取角色配置
  const getRoleConfig = (role: string) => {
    const roleMap: Record<string, any> = {
      admin: { color: 'red', text: '管理员', icon: <UserOutlined /> },
      employee: { color: 'blue', text: '员工', icon: <TeamOutlined /> },
    }
    return roleMap[role] || { color: 'default', text: role, icon: null }
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap: Record<string, any> = {
      active: { color: 'success', text: '在职' },
      inactive: { color: 'error', text: '离职' },
    }
    return statusMap[status] || { color: 'default', text: status }
  }

  // 过滤数据
  const filteredEmployees = employees.filter(employee => {
    const matchSearch = !searchText ||
      employee.name.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.employee_number.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !filterStatus || employee.status === filterStatus
    const matchRole = !filterRole || employee.role === filterRole
    const matchFactory = !filterFactory || employee.factory_id === filterFactory
    const matchTab = activeTab === 'active' ? employee.status === 'active' :
                   activeTab === 'inactive' ? employee.status === 'inactive' : true
    return matchSearch && matchStatus && matchRole && matchFactory && matchTab
  })

  // 员工列表列配置
  const columns: ColumnsType<EnterpriseEmployee> = [
    {
      title: '员工信息',
      key: 'employee',
      width: 220,
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>
              <Text strong>{record.name}</Text>
              <Tag color="blue" className="ml-2">{record.employee_number}</Tag>
            </div>
            <div>
              <Text type="secondary" className="text-xs">{record.position}</Text>
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '联系方式',
      key: 'contact',
      width: 200,
      ellipsis: true,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <MailOutlined className="mr-1" />
            <Text className="text-xs">{record.email}</Text>
          </div>
          <div>
            <PhoneOutlined className="mr-1" />
            <Text className="text-xs">{record.phone}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '工厂/部门',
      key: 'organization',
      width: 160,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <HomeOutlined className="mr-1" />
            <Text className="text-xs">{record.factory_name}</Text>
          </div>
          <div>
            <BankOutlined className="mr-1" />
            <Text className="text-xs">{record.department_name}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      key: 'roles',
      width: 160,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>系统：</Text>
            <Tag color={getRoleConfig(record.role).color} icon={getRoleConfig(record.role).icon}>
              {getRoleConfig(record.role).text}
            </Tag>
          </div>
          {record.company_role_name && (
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>企业：</Text>
              <Tag color="green">
                {record.company_role_name}
              </Tag>
            </div>
          )}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => {
        const config = getStatusConfig(status)
        return (
          <Badge
            status={status === 'active' ? 'success' : 'error'}
            text={config.text}
          />
        )
      },
    },
    {
      title: '数据权限',
      dataIndex: 'data_access_scope',
      key: 'data_access_scope',
      width: 110,
      render: (scope) => (
        <Tag color={scope === 'company' ? 'red' : 'blue'}>
          {scope === 'company' ? '全公司' : '当前工厂'}
        </Tag>
      ),
    },
    {
      title: '工作量',
      key: 'workload',
      width: 110,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <Text>WPS: </Text>
            <Text strong>{record.total_wps_created}</Text>
          </div>
          <div>
            <Text>任务: </Text>
            <Text strong>{record.total_tasks_completed}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '最后活跃',
      dataIndex: 'last_active_at',
      key: 'last_active_at',
      width: 110,
      render: (date) => date ? dayjs(date).format('MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space wrap size={0}>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedEmployee(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedEmployee(record)
              form.setFieldsValue({
                role: record.role,
                data_access_scope: record.data_access_scope,
                factory_id: record.factory_id,
                department_id: record.department_id,
              })
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
          {record.status === 'active' ? (
            <Button
              type="text"
              danger
              onClick={() => deactivateEmployee(record.id)}
            >
              停用
            </Button>
          ) : (
            <Button
              type="text"
              onClick={() => activateEmployee(record.id)}
            >
              激活
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个员工吗？"
            onConfirm={() => deleteEmployee(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 更新员工权限
  const handleUpdateEmployee = () => {
    form.validateFields().then(values => {
      if (selectedEmployee) {
        updateEmployeePermissions(selectedEmployee.id, values).then((success) => {
          if (success) {
            setModalVisible(false)
            form.resetFields()
            setSelectedEmployee(null)
          }
        })
      }
    })
  }

  // 创建员工
  const handleCreateEmployee = async () => {
    try {
      const values = await createForm.validateFields()
      setCreateLoading(true)

      // 调用创建员工API
      const response = await enterpriseService.createEmployee({
        email: values.email,
        name: values.name,
        phone: values.phone,
        password: values.password,
        employee_number: values.employee_number,
        position: values.position,
        department: values.department,
        factory_id: values.factory_id,
        role: values.role,
        company_role_id: values.company_role_id,
        data_access_scope: values.data_access_scope,
      })

      if (response.data.success) {
        message.success('员工创建成功')
        console.log('✅ 员工创建成功，准备刷新列表...')
        setCreateModalVisible(false)
        createForm.resetFields()
        console.log('📋 调用 loadEmployees()...')
        await loadEmployees()
        console.log('✅ loadEmployees() 完成')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建员工失败')
    } finally {
      setCreateLoading(false)
    }
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title="员工管理"
        description="管理企业员工信息、权限和状态"
      />

      <Button type="primary" icon={<MailOutlined />} onClick={() => navigate('/enterprise/invitations')} style={{ marginBottom: 16 }}>邀请员工 / 查看邀请</Button>
      {/* 配额显示 */}
      {!quotaLoading && quota && (
        <Alert
          message="员工配额"
          description={
            <div className="mt-2">
              <Progress
                percent={quota.percentage}
                status={quota.percentage >= 90 ? 'exception' : 'normal'}
                format={() => `${quota.current}/${quota.max}`}
              />
              <Text type="secondary" className="text-xs">
                当前等级：{quota.tier} | 已使用 {quota.percentage}%
              </Text>
            </div>
          }
          type={quota.percentage >= 90 ? 'warning' : 'info'}
          showIcon
          className="mb-4"
        />
      )}

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="list-stats-row">
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic
              title="员工总数"
              value={stats.total}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic
              title="在职员工"
              value={stats.active}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic
              title="离职员工"
              value={stats.inactive}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic
              title="管理员"
              value={stats.admins}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="list-page-card">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'active',
              label: `在职员工 (${stats.active})`,
              children: null,
            },
            {
              key: 'inactive',
              label: `离职员工 (${stats.inactive})`,
              children: null,
            },
          ]}
          style={{ marginBottom: 8 }}
        />

        <div className="doc-list-toolbar">
          <div className="toolbar-search">
            <Search
              placeholder="搜索员工姓名、邮箱或工号"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={setSearchText}
            />
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="状态筛选"
              value={filterStatus || undefined}
              onChange={(v) => setFilterStatus(v || '')}
              allowClear
              size="large"
              style={{ width: '100%' }}
            >
              <Option value="active">在职</Option>
              <Option value="inactive">离职</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="角色筛选"
              value={filterRole || undefined}
              onChange={(v) => setFilterRole(v || '')}
              allowClear
              size="large"
              style={{ width: '100%' }}
            >
              <Option value="admin">管理员</Option>
              <Option value="employee">员工</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="工厂筛选"
              value={filterFactory || undefined}
              onChange={(v) => setFilterFactory(v || '')}
              allowClear
              size="large"
              style={{ width: '100%' }}
            >
              {factories.map((factory: any) => (
                <Option key={factory.id} value={factory.id}>{factory.name}</Option>
              ))}
            </Select>
          </div>
          <div className="toolbar-actions">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="large"
              onClick={() => {
                createForm.resetFields()
                setCreateModalVisible(true)
              }}
              disabled={quota ? quota.current >= quota.max : false}
            >
              创建员工
            </Button>
            <Button icon={<ExportOutlined />} size="large">
              导出数据
            </Button>
          </div>
        </div>

        <div className="list-table-wrap">
          <Table
            columns={columns}
            dataSource={filteredEmployees}
            rowKey={(record) => `${record.id}_${record.user_id}`}
            loading={loading}
            scroll={{ x: 1400 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </div>
      </Card>

      {/* 创建员工弹窗 */}
      <Modal
        title="创建员工"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          createForm.resetFields()
        }}
        onOk={handleCreateEmployee}
        confirmLoading={createLoading}
        width={800}
        okText="创建"
        cancelText="取消"
      >
        <Form
          form={createForm}
          layout="vertical"
        >
          <Alert
            message="创建员工账户"
            description="系统将创建一个新的用户账户并自动关联到企业。请妥善保管初始密码并分发给员工。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="员工姓名"
                rules={[{ required: true, message: '请输入员工姓名' }]}
              >
                <Input placeholder="请输入员工姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="employee@example.com" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[{ required: true, message: '请输入手机号' }]}
              >
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="employee_number"
                label="工号"
                rules={[{ required: true, message: '请输入工号' }]}
              >
                <Input placeholder="例如：EMP001" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="password"
                label="初始密码"
                rules={[
                  { required: true, message: '请输入初始密码' },
                  { min: 6, message: '密码至少6位' }
                ]}
              >
                <Input.Password placeholder="请设置初始密码（至少6位）" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="position"
                label="职位"
                rules={[{ required: true, message: '请输入职位' }]}
              >
                <Input placeholder="例如：质检员、生产主管" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="department"
                label="部门"
                rules={[{ required: true, message: '请选择部门' }]}
              >
                <Select
                  placeholder="请选择部门"
                  loading={departmentsLoading}
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {departments.map(dept => (
                    <Option key={dept.id} value={dept.department_name}>
                      <Space>
                        <BankOutlined />
                        <span>{dept.department_name}</span>
                        {dept.department_code && <Text type="secondary" style={{ fontSize: 12 }}>({dept.department_code})</Text>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="factory_id"
                label="所属工厂"
                rules={[{ required: true, message: '请选择工厂' }]}
              >
                <Select
                  placeholder="请选择工厂"
                  loading={factoriesLoading}
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {factories.map(factory => (
                    <Option key={factory.id} value={factory.id}>
                      <Space>
                        <HomeOutlined />
                        <span>{factory.name}</span>
                        {factory.code && <Text type="secondary" style={{ fontSize: 12 }}>({factory.code})</Text>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="系统角色"
                rules={[{ required: true, message: '请选择系统角色' }]}
                tooltip="系统角色决定基本权限级别"
              >
                <Select placeholder="请选择系统角色">
                  <Option value="admin">管理员</Option>
                  <Option value="employee">员工</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="company_role_id"
                label="企业角色"
                tooltip="企业角色定义具体的权限配置"
              >
                <Select
                  placeholder="请选择企业角色（可选）"
                  loading={rolesLoading}
                  allowClear
                >
                  {roles.map(role => (
                    <Option key={role.id} value={role.id}>
                      <Space>
                        <span>{role.name}</span>
                        <Tag color={role.data_access_scope === 'company' ? 'purple' : 'cyan'} style={{ fontSize: 12 }}>
                          {role.data_access_scope === 'company' ? '全公司' : '工厂级'}
                        </Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="data_access_scope"
            label="数据权限范围"
            rules={[{ required: true, message: '请选择数据权限范围' }]}
          >
            <Select placeholder="请选择数据权限范围">
              <Option value="factory">工厂级（只能访问所属工厂的数据）</Option>
              <Option value="company">公司级（可以访问全公司的数据）</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑员工弹窗 */}
      <Modal
        title="编辑员工"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setSelectedEmployee(null)
        }}
        onOk={handleUpdateEmployee}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="系统角色"
                rules={[{ required: true, message: '请选择系统角色' }]}
                tooltip="系统角色决定基本权限级别"
              >
                <Select placeholder="请选择系统角色">
                  <Option value="admin">管理员</Option>
                  <Option value="employee">员工</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="company_role_id"
                label="企业角色"
                tooltip="企业角色定义具体的权限配置"
              >
                <Select
                  placeholder="请选择企业角色（可选）"
                  loading={rolesLoading}
                  allowClear
                >
                  {roles.map(role => (
                    <Option key={role.id} value={role.id}>
                      <Space>
                        <span>{role.name}</span>
                        <Tag color={role.data_access_scope === 'company' ? 'purple' : 'cyan'} style={{ fontSize: 12 }}>
                          {role.data_access_scope === 'company' ? '全公司' : '工厂级'}
                        </Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="position"
                label="职位"
              >
                <Input placeholder="例如：质检员、生产主管" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="data_access_scope"
                label="数据权限范围"
                rules={[{ required: true, message: '请选择数据权限范围' }]}
              >
                <Select placeholder="请选择数据权限范围">
                  <Option value="factory">当前工厂</Option>
                  <Option value="company">全公司</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="factory_id"
                label="分配工厂"
                rules={[{ required: true, message: '请选择工厂' }]}
              >
                <Select
                  placeholder="请选择工厂"
                  loading={factoriesLoading}
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {factories.map(factory => (
                    <Option key={factory.id} value={factory.id}>
                      <Space>
                        <HomeOutlined />
                        <span>{factory.name}</span>
                        {factory.code && <Text type="secondary" style={{ fontSize: 12 }}>({factory.code})</Text>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="department_id"
                label="分配部门"
              >
                <Select
                  placeholder="请选择部门"
                  loading={departmentsLoading}
                  showSearch
                  optionFilterProp="children"
                  allowClear
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {departments.map(dept => (
                    <Option key={dept.id} value={dept.department_name}>
                      <Space>
                        <BankOutlined />
                        <span>{dept.department_name}</span>
                        {dept.department_code && <Text type="secondary" style={{ fontSize: 12 }}>({dept.department_code})</Text>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 员工详情弹窗 */}
      <Modal
        title="员工详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedEmployee && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={6}>
                <div className="text-center">
                  <Avatar size={80} icon={<UserOutlined />} />
                  <div className="mt-2">
                    <Title level={4}>{selectedEmployee.name}</Title>
                    <Tag color="blue">{selectedEmployee.employee_number}</Tag>
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>职位：</Text> {selectedEmployee.position}
                  </Col>
                  <Col span={12}>
                    <Text strong>角色：</Text>
                    <Tag color={getRoleConfig(selectedEmployee.role).color} className="ml-2">
                      {getRoleConfig(selectedEmployee.role).text}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>状态：</Text>
                    <Badge
                      status={selectedEmployee.status === 'active' ? 'success' : 'error'}
                      text={getStatusConfig(selectedEmployee.status).text}
                      className="ml-2"
                    />
                  </Col>
                  <Col span={12}>
                    <Text strong>数据权限：</Text>
                    <Tag color={selectedEmployee.data_access_scope === 'company' ? 'red' : 'blue'} className="ml-2">
                      {selectedEmployee.data_access_scope === 'company' ? '全公司' : '当前工厂'}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>入职时间：</Text> {dayjs(selectedEmployee.joined_at).format('YYYY-MM-DD')}
                  </Col>
                  <Col span={12}>
                    <Text strong>最后活跃：</Text> {selectedEmployee.last_active_at ? dayjs(selectedEmployee.last_active_at).format('YYYY-MM-DD HH:mm') : '从未活跃'}
                  </Col>
                </Row>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="联系信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div><MailOutlined className="mr-2" />{selectedEmployee.email}</div>
                    <div><PhoneOutlined className="mr-2" />{selectedEmployee.phone}</div>
                    <div><HomeOutlined className="mr-2" />{selectedEmployee.factory_name}</div>
                    <div><BankOutlined className="mr-2" />{selectedEmployee.department_name}</div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="工作统计" size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic title="创建WPS" value={selectedEmployee.total_wps_created} />
                    </Col>
                    <Col span={12}>
                      <Statistic title="完成任务" value={selectedEmployee.total_tasks_completed} />
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>

            <Card title="权限详情" size="small" className="mt-4">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>功能权限：</Text>
                  <div className="mt-2">
                    <Space wrap>
                      {Object.entries(selectedEmployee.permissions).map(([key, value]) => (
                        <Tag key={key} color={value ? 'green' : 'default'}>
                          {key}: {value ? '开启' : '关闭'}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>数据权限：</Text>
                  <div className="mt-2">
                    <Tag color={selectedEmployee.data_access_scope === 'company' ? 'red' : 'blue'}>
                      {selectedEmployee.data_access_scope === 'company' ? '全公司数据访问' : '当前工厂数据访问'}
                    </Tag>
                  </div>
                </Col>
              </Row>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default function EnterpriseEntry() { return <EnterpriseWorkspaceGate><EnterpriseEmployees /></EnterpriseWorkspaceGate> }