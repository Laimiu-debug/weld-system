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
  Divider,
  Popconfirm,
  Badge,
  Tooltip,
  Progress,
  Tabs,
  Upload,
  Switch,
  InputNumber,
  Descriptions,
  Alert,
  Checkbox,
} from 'antd'
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  CrownOutlined,
  SafetyOutlined,
  MailOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  UploadOutlined,
  EyeOutlined,
  StopOutlined,
  HomeOutlined,
  BankOutlined,
  ApartmentOutlined,
  UsergroupAddOutlined,
  SettingOutlined,
  SendOutlined,
  NumberOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import type { TabsProps } from 'antd'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 接口定义
interface CompanyEmployee {
  id: string
  user_id: string
  employee_number: string
  name: string
  email: string
  phone: string
  role: 'admin' | 'employee'
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

interface Factory {
  id: string
  name: string
  code: string
  address: string
  city: string
  contact_person: string
  contact_phone: string
  employee_count: number
  is_headquarters: boolean
  is_active: boolean
  created_at: string
}

interface Department {
  id: string
  company_id: string
  factory_id?: string
  department_code: string
  department_name: string
  description: string
  manager_id?: string
  manager_name?: string
  employee_count: number
  created_at: string
}

interface EmployeeInvitation {
  id: string
  email: string
  invitation_code: string
  role: 'admin' | 'employee'
  factory_id?: string
  factory_name?: string
  department_id?: string
  department_name?: string
  status: 'pending' | 'accepted' | 'expired' | 'cancelled'
  permissions: Record<string, boolean>
  expires_at: string
  accepted_at?: string
  created_at: string
}

interface EmployeeQuota {
  current: number
  max: number
  percentage: number
  tier: string
}

const EmployeeManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('employees')
  const [employees, setEmployees] = useState<CompanyEmployee[]>([])
  const [factories, setFactories] = useState<Factory[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [invitations, setInvitations] = useState<EmployeeInvitation[]>([])
  const [quota, setQuota] = useState<EmployeeQuota | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'invite' | 'factory' | 'department'>('invite')
  const [selectedEmployee, setSelectedEmployee] = useState<CompanyEmployee | null>(null)
  const [selectedFactory, setSelectedFactory] = useState<Factory | null>(null)
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterRole, setFilterRole] = useState<string>('')
  const [filterFactory, setFilterFactory] = useState<string>('')

  // 模拟数据
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      await Promise.all([
        loadEmployees(),
        loadFactories(),
        loadDepartments(),
        loadInvitations(),
        loadQuota(),
      ])
    } catch (error) {
      message.error('数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadEmployees = () => {
    const mockEmployees: CompanyEmployee[] = [
      {
        id: '1',
        user_id: 'u1',
        employee_number: 'EMP001',
        name: '张三',
        email: 'zhangsan@company.com',
        phone: '13800138001',
        role: 'admin',
        status: 'active',
        factory_id: 'f1',
        factory_name: '北京工厂',
        department_id: 'd1',
        department_name: '技术部',
        position: '技术总监',
        permissions: {
          can_create_wps: true,
          can_approve_wps: true,
          can_manage_employees: true,
        },
        data_access_scope: 'company',
        joined_at: '2023-01-15',
        last_active_at: '2024-10-18T09:30:00Z',
        total_wps_created: 25,
        total_tasks_completed: 45,
      },
      {
        id: '2',
        user_id: 'u2',
        employee_number: 'EMP002',
        name: '李四',
        email: 'lisi@company.com',
        phone: '13800138002',
        role: 'employee',
        status: 'active',
        factory_id: 'f1',
        factory_name: '北京工厂',
        department_id: 'd1',
        department_name: '技术部',
        position: '焊接工程师',
        permissions: {
          can_create_wps: true,
          can_approve_wps: false,
          can_manage_employees: false,
        },
        data_access_scope: 'factory',
        joined_at: '2023-03-20',
        last_active_at: '2024-10-18T08:15:00Z',
        total_wps_created: 18,
        total_tasks_completed: 32,
      },
    ]
    setEmployees(mockEmployees)
  }

  const loadFactories = () => {
    const mockFactories: Factory[] = [
      {
        id: 'f1',
        name: '北京工厂',
        code: 'BJ001',
        address: '北京市朝阳区',
        city: '北京',
        contact_person: '张三',
        contact_phone: '13800138001',
        employee_count: 15,
        is_headquarters: true,
        is_active: true,
        created_at: '2023-01-01',
      },
      {
        id: 'f2',
        name: '上海工厂',
        code: 'SH001',
        address: '上海市浦东新区',
        city: '上海',
        contact_person: '王五',
        contact_phone: '13800138003',
        employee_count: 8,
        is_headquarters: false,
        is_active: true,
        created_at: '2023-06-01',
      },
    ]
    setFactories(mockFactories)
  }

  const loadDepartments = () => {
    const mockDepartments: Department[] = [
      {
        id: 'd1',
        company_id: 'c1',
        factory_id: 'f1',
        department_code: 'TECH',
        department_name: '技术部',
        description: '负责技术研发和工艺设计',
        manager_id: 'u1',
        manager_name: '张三',
        employee_count: 8,
        created_at: '2023-01-01',
      },
      {
        id: 'd2',
        company_id: 'c1',
        factory_id: 'f1',
        department_code: 'PROD',
        department_name: '生产部',
        description: '负责生产制造',
        manager_id: 'u3',
        manager_name: '赵六',
        employee_count: 12,
        created_at: '2023-01-01',
      },
    ]
    setDepartments(mockDepartments)
  }

  const loadInvitations = () => {
    const mockInvitations: EmployeeInvitation[] = [
      {
        id: 'inv1',
        email: 'newemployee@example.com',
        invitation_code: 'INV-2025-ABC123',
        role: 'employee',
        factory_id: 'f1',
        factory_name: '北京工厂',
        department_id: 'd1',
        department_name: '技术部',
        status: 'pending',
        permissions: {
          can_create_wps: true,
          can_approve_wps: false,
        },
        expires_at: '2025-10-25T10:00:00Z',
        created_at: '2025-10-18T10:00:00Z',
      },
    ]
    setInvitations(mockInvitations)
  }

  const loadQuota = () => {
    setQuota({
      current: 15,
      max: 20,
      percentage: 75,
      tier: 'enterprise',
    })
  }

  // 邀请员工
  const handleInviteEmployee = () => {
    form.validateFields().then(values => {
      const newInvitation: EmployeeInvitation = {
        id: Date.now().toString(),
        invitation_code: `INV-${Date.now().toString(36).toUpperCase()}`,
        status: 'pending',
        expires_at: dayjs().add(7, 'day').toISOString(),
        created_at: new Date().toISOString(),
        ...values,
      }
      setInvitations([...invitations, newInvitation])
      setModalVisible(false)
      form.resetFields()
      message.success('邀请已发送')
    })
  }

  // 创建工厂
  const handleCreateFactory = () => {
    form.validateFields().then(values => {
      const newFactory: Factory = {
        id: Date.now().toString(),
        employee_count: 0,
        is_headquarters: false,
        is_active: true,
        created_at: new Date().toISOString(),
        ...values,
      }
      setFactories([...factories, newFactory])
      setModalVisible(false)
      form.resetFields()
      message.success('工厂创建成功')
    })
  }

  // 创建部门
  const handleCreateDepartment = () => {
    form.validateFields().then(values => {
      const newDepartment: Department = {
        id: Date.now().toString(),
        company_id: 'c1',
        employee_count: 0,
        created_at: new Date().toISOString(),
        ...values,
      }
      setDepartments([...departments, newDepartment])
      setModalVisible(false)
      form.resetFields()
      message.success('部门创建成功')
    })
  }

  // 停用员工
  const handleDeactivateEmployee = (id: string) => {
    setEmployees(employees.map(emp =>
      emp.id === id ? { ...emp, status: 'inactive' } : emp
    ))
    message.success('员工已停用')
  }

  // 删除员工
  const handleDeleteEmployee = (id: string) => {
    setEmployees(employees.filter(emp => emp.id !== id))
    message.success('员工已删除')
  }

  // 取消邀请
  const handleCancelInvitation = (id: string) => {
    setInvitations(invitations.map(inv =>
      inv.id === id ? { ...inv, status: 'cancelled' } : inv
    ))
    message.success('邀请已取消')
  }

  // 获取角色配置
  const getRoleConfig = (role: string) => {
    const roleMap = {
      admin: { color: 'red', text: '管理员', icon: <CrownOutlined /> },
      employee: { color: 'blue', text: '员工', icon: <UserOutlined /> },
    }
    return roleMap[role] || { color: 'default', text: role, icon: null }
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      active: { color: 'success', text: '在职' },
      inactive: { color: 'error', text: '离职' },
      pending: { color: 'warning', text: '待入职' },
      accepted: { color: 'success', text: '已接受' },
      expired: { color: 'error', text: '已过期' },
      cancelled: { color: 'default', text: '已取消' },
    }
    return statusMap[status] || { color: 'default', text: status }
  }

  // 过滤员工数据
  const filteredEmployees = employees.filter(employee => {
    const matchSearch = !searchText ||
      employee.name.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.employee_number.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !filterStatus || employee.status === filterStatus
    const matchRole = !filterRole || employee.role === filterRole
    const matchFactory = !filterFactory || employee.factory_id === filterFactory
    return matchSearch && matchStatus && matchRole && matchFactory
  })

  // 员工列表列配置
  const employeeColumns: ColumnsType<CompanyEmployee> = [
    {
      title: '员工信息',
      key: 'employee',
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
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const config = getRoleConfig(role)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
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
      render: (scope) => (
        <Tag color={scope === 'company' ? 'red' : 'blue'}>
          {scope === 'company' ? '全公司' : '当前工厂'}
        </Tag>
      ),
    },
    {
      title: '工作量',
      key: 'workload',
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
      render: (date) => date ? dayjs(date).format('MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedEmployee(record)
              setModalType('invite')
              setModalVisible(true)
            }}
          >
            查看
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedEmployee(record)
              setModalType('invite')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
          {record.status === 'active' && (
            <Button
              type="text"
              danger
              onClick={() => handleDeactivateEmployee(record.id)}
            >
              停用
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个员工吗？"
            onConfirm={() => handleDeleteEmployee(record.id)}
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

  // 邀请列表列配置
  const invitationColumns: ColumnsType<EmployeeInvitation> = [
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '邀请码',
      dataIndex: 'invitation_code',
      key: 'invitation_code',
      render: (code) => <Text copyable>{code}</Text>,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const config = getRoleConfig(role)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '工厂/部门',
      key: 'organization',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>{record.factory_name}</div>
          <div>{record.department_name}</div>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = getStatusConfig(status)
        return (
          <Badge
            status={status === 'accepted' ? 'success' : status === 'pending' ? 'warning' : 'default'}
            text={config.text}
          />
        )
      },
    },
    {
      title: '过期时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个邀请吗？"
              onConfirm={() => handleCancelInvitation(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
              >
                取消邀请
              </Button>
            </Popconfirm>
          )}
          <Button
            type="text"
            icon={<SendOutlined />}
          >
            重新发送
          </Button>
        </Space>
      ),
    },
  ]

  // 工厂列表列配置
  const factoryColumns: ColumnsType<Factory> = [
    {
      title: '工厂信息',
      key: 'factory',
      render: (_, record) => (
        <Space>
          <Avatar icon={<HomeOutlined />} />
          <div>
            <div>
              <Text strong>{record.name}</Text>
              {record.is_headquarters && <Tag color="red" className="ml-2">总部</Tag>}
            </div>
            <div>
              <Text type="secondary" className="text-xs">{record.code}</Text>
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '地址',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: '联系人',
      key: 'contact',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <Text strong>{record.contact_person}</Text>
          </div>
          <div>
            <Text className="text-xs">{record.contact_phone}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '员工数量',
      dataIndex: 'employee_count',
      key: 'employee_count',
      render: (count) => <Badge count={count} showZero />,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => (
        <Badge
          status={active ? 'success' : 'error'}
          text={active ? '正常' : '停用'}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedFactory(record)
              setModalType('factory')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  // 部门列表列配置
  const departmentColumns: ColumnsType<Department> = [
    {
      title: '部门信息',
      key: 'department',
      render: (_, record) => (
        <Space>
          <Avatar icon={<BankOutlined />} />
          <div>
            <div>
              <Text strong>{record.department_name}</Text>
              <Tag color="blue" className="ml-2">{record.department_code}</Tag>
            </div>
            <div>
              <Text type="secondary" className="text-xs">{record.description}</Text>
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'manager_name',
      key: 'manager_name',
      render: (name) => name || '-',
    },
    {
      title: '员工数量',
      dataIndex: 'employee_count',
      key: 'employee_count',
      render: (count) => <Badge count={count} showZero />,
    },
    {
      title: '所属工厂',
      key: 'factory',
      render: (_, record) => {
        const factory = factories.find(f => f.id === record.factory_id)
        return factory ? factory.name : '-'
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedDepartment(record)
              setModalType('department')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  // 标签页配置
  const tabItems: TabsProps['items'] = [
    {
      key: 'employees',
      label: (
        <span>
          <TeamOutlined />
          员工管理
        </span>
      ),
      children: (
        <div>
          {/* 配额显示 */}
          {quota && (
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

          {/* 搜索和筛选 */}
          <Card className="mb-4">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={12} md={6}>
                <Input
                  placeholder="搜索员工姓名、邮箱或工号"
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                />
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Select
                  placeholder="状态筛选"
                  value={filterStatus}
                  onChange={setFilterStatus}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="active">在职</Option>
                  <Option value="inactive">离职</Option>
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Select
                  placeholder="角色筛选"
                  value={filterRole}
                  onChange={setFilterRole}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="admin">管理员</Option>
                  <Option value="employee">员工</Option>
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <Select
                  placeholder="工厂筛选"
                  value={filterFactory}
                  onChange={setFilterFactory}
                  allowClear
                  style={{ width: '100%' }}
                >
                  {factories.map(factory => (
                    <Option key={factory.id} value={factory.id}>
                      {factory.name}
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Space>
                  <Button
                    type="primary"
                    icon={<UsergroupAddOutlined />}
                    onClick={() => {
                      setModalType('invite')
                      setSelectedEmployee(null)
                      form.resetFields()
                      setModalVisible(true)
                    }}
                    disabled={quota ? quota.current >= quota.max : false}
                  >
                    邀请员工
                  </Button>
                  <Button icon={<ExportOutlined />}>
                    导出数据
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 员工列表 */}
          <Card title="员工列表">
            <Table
              columns={employeeColumns}
              dataSource={filteredEmployees}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'invitations',
      label: (
        <span>
          <SendOutlined />
          邀请管理
        </span>
      ),
      children: (
        <Card title="邀请记录">
          <div className="mb-4">
            <Button
              type="primary"
              icon={<UsergroupAddOutlined />}
              onClick={() => {
                setModalType('invite')
                setSelectedEmployee(null)
                form.resetFields()
                setModalVisible(true)
              }}
              disabled={quota ? quota.current >= quota.max : false}
            >
              发送新邀请
            </Button>
          </div>
          <Table
            columns={invitationColumns}
            dataSource={invitations}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </Card>
      ),
    },
    {
      key: 'factories',
      label: (
        <span>
          <HomeOutlined />
          工厂管理
        </span>
      ),
      children: (
        <Card title="工厂列表">
          <div className="mb-4">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setModalType('factory')
                setSelectedFactory(null)
                form.resetFields()
                setModalVisible(true)
              }}
            >
              创建工厂
            </Button>
          </div>
          <Table
            columns={factoryColumns}
            dataSource={factories}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </Card>
      ),
    },
    {
      key: 'departments',
      label: (
        <span>
          <BankOutlined />
          部门管理
        </span>
      ),
      children: (
        <Card title="部门列表">
          <div className="mb-4">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setModalType('department')
                setSelectedDepartment(null)
                form.resetFields()
                setModalVisible(true)
              }}
            >
              创建部门
            </Button>
          </div>
          <Table
            columns={departmentColumns}
            dataSource={departments}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </Card>
      ),
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>企业员工管理</Title>
        <Text type="secondary">管理企业员工、工厂和部门，设置权限和配额</Text>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="员工总数"
              value={employees.length}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="在职员工"
              value={employees.filter(emp => emp.status === 'active').length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="工厂数量"
              value={factories.length}
              prefix={<HomeOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="部门数量"
              value={departments.length}
              prefix={<BankOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 标签页 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />

      {/* 邀请员工弹窗 */}
      <Modal
        title={selectedEmployee ? '编辑员工' : '邀请员工'}
        open={modalVisible && modalType === 'invite'}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={selectedEmployee ? undefined : handleInviteEmployee}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            role: 'employee',
            data_access_scope: 'factory',
            permissions: {},
          }}
        >
          <Form.Item
            name="email"
            label="邮箱地址"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="请输入员工邮箱地址" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="请选择角色">
                  <Option value="admin">管理员</Option>
                  <Option value="employee">普通员工</Option>
                </Select>
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
                <Select placeholder="请选择工厂">
                  {factories.map(factory => (
                    <Option key={factory.id} value={factory.id}>
                      {factory.name}
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
                <Select placeholder="请选择部门">
                  {departments.map(department => (
                    <Option key={department.id} value={department.id}>
                      {department.department_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="permissions"
            label="权限设置"
          >
            <Row gutter={[8, 8]}>
              <Col span={12}>
                <Checkbox checked>创建WPS</Checkbox>
              </Col>
              <Col span={12}>
                <Checkbox>审批WPS</Checkbox>
              </Col>
              <Col span={12}>
                <Checkbox>创建PQR</Checkbox>
              </Col>
              <Col span={12}>
                <Checkbox>管理焊工</Checkbox>
              </Col>
              <Col span={12}>
                <Checkbox>管理焊材</Checkbox>
              </Col>
              <Col span={12}>
                <Checkbox>管理设备</Checkbox>
              </Col>
            </Row>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建工厂弹窗 */}
      <Modal
        title="创建工厂"
        open={modalVisible && modalType === 'factory'}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleCreateFactory}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="工厂名称"
                rules={[{ required: true, message: '请输入工厂名称' }]}
              >
                <Input placeholder="请输入工厂名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="工厂编码"
                rules={[{ required: true, message: '请输入工厂编码' }]}
              >
                <Input placeholder="请输入工厂编码" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="address"
            label="详细地址"
            rules={[{ required: true, message: '请输入详细地址' }]}
          >
            <TextArea placeholder="请输入详细地址" rows={2} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="city"
                label="城市"
                rules={[{ required: true, message: '请输入城市' }]}
              >
                <Input placeholder="请输入城市" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contact_person"
                label="联系人"
                rules={[{ required: true, message: '请输入联系人' }]}
              >
                <Input placeholder="请输入联系人" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="contact_phone"
            label="联系电话"
            rules={[{ required: true, message: '请输入联系电话' }]}
          >
            <Input placeholder="请输入联系电话" />
          </Form.Item>

          <Form.Item
            name="is_headquarters"
            label="设为总部"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建部门弹窗 */}
      <Modal
        title="创建部门"
        open={modalVisible && modalType === 'department'}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleCreateDepartment}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="department_name"
                label="部门名称"
                rules={[{ required: true, message: '请输入部门名称' }]}
              >
                <Input placeholder="请输入部门名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="department_code"
                label="部门编码"
                rules={[{ required: true, message: '请输入部门编码' }]}
              >
                <Input placeholder="请输入部门编码" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="factory_id"
            label="所属工厂"
            rules={[{ required: true, message: '请选择所属工厂' }]}
          >
            <Select placeholder="请选择所属工厂">
              {factories.map(factory => (
                <Option key={factory.id} value={factory.id}>
                  {factory.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="部门描述"
          >
            <TextArea placeholder="请输入部门描述" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default EmployeeManagement