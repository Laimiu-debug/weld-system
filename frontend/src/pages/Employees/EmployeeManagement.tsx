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
  Alert,
  Switch,
  InputNumber,
} from 'antd'
import { enterpriseService, CompanyEmployee } from '@/services/enterprise'
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
  EyeOutlined,
  StopOutlined,
  HomeOutlined,
  BankOutlined,
  SendOutlined,
  UsergroupAddOutlined,
  SettingOutlined,
  ApartmentOutlined,
  ShopOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import type { TabsProps } from 'antd'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 接口定义
interface Employee {
  id: string
  employee_number: string
  name: string
  email: string
  phone: string
  position: string
  department: string
  status: 'active' | 'inactive' | 'pending'
  role: string
  location: string
  joinDate: string
  lastLogin?: string
  avatar?: string
  permissions: string[]
  workSchedule: string
  emergencyContact: string
  performance: number
}

interface EmployeeInvitation {
  id: string
  email: string
  invitation_code: string
  role: string
  factory_name?: string
  department_name?: string
  status: 'pending' | 'accepted' | 'expired' | 'cancelled'
  expires_at: string
  created_at: string
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
}

interface Department {
  id: string
  factory_id?: string
  department_code: string
  department_name: string
  description: string
  manager_name?: string
  employee_count: number
}

interface EmployeeQuota {
  current: number
  max: number
  percentage: number
  tier: string
}

const EmployeeManagement: React.FC = () => {
  const { user, checkPermission } = useAuthStore()
  const [activeTab, setActiveTab] = useState('employees')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [invitations, setInvitations] = useState<EmployeeInvitation[]>([])
  const [factories, setFactories] = useState<Factory[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [quota, setQuota] = useState<EmployeeQuota | null>(null)
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'invite' | 'factory' | 'department'>('create')
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterRole, setFilterRole] = useState<string>('')
  const [filterFactory, setFilterFactory] = useState<string>('')

  // 判断是否为企业用户
  const isEnterpriseUser = () => {
    const userTier = user?.membership_tier || user?.member_tier || 'free'
    return ['enterprise', 'enterprise_pro', 'enterprise_pro_max'].includes(userTier)
  }

  // 数据加载
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      console.log('=== 开始加载员工数据 ===')
      // 使用真实API获取员工数据
      const response = await enterpriseService.getEmployees({
        page: 1,
        page_size: 100
      })

      console.log('员工API响应:', response)

      let employees: CompanyEmployee[] = []
      if (response?.data?.employees) {
        employees = response.data.employees
      } else if (response?.data) {
        employees = Array.isArray(response.data) ? response.data : [response.data]
      } else if (Array.isArray(response)) {
        employees = response
      }

      console.log('原始员工数据:', employees)

      // 基于user_id合并重复的员工记录
      const employeeMap = new Map<string, CompanyEmployee>()

      employees.forEach(employee => {
        const existing = employeeMap.get(employee.user_id)

        if (!existing) {
          // 如果员工不存在，直接添加
          employeeMap.set(employee.user_id, employee)
        } else {
          // 如果员工已存在，合并信息
          // 优先级：admin > manager > employee
          const getRolePriority = (role: string) => {
            switch (role) {
              case 'admin': return 3
              case 'manager': return 2
              case 'employee': return 1
              default: return 1
            }
          }

          const existingPriority = getRolePriority(existing.role)
          const newPriority = getRolePriority(employee.role)

          // 如果新记录的角色优先级更高，则更新
          if (newPriority > existingPriority) {
            const mergedEmployee = {
              ...existing,
              role: employee.role,
              position: employee.position || existing.position,
              department: employee.department || existing.department,
              factory_id: employee.factory_id || existing.factory_id,
              factory_name: employee.factory_name || existing.factory_name,
            }
            employeeMap.set(employee.user_id, mergedEmployee)
          }
        }
      })

      const uniqueEmployees = Array.from(employeeMap.values())
      console.log('合并后的员工数据:', uniqueEmployees)

      // 转换为前端需要的格式
      const formattedEmployees: Employee[] = uniqueEmployees.map(emp => ({
        id: emp.id,
        employee_number: emp.employee_number,
        name: emp.name,
        email: emp.email,
        phone: emp.phone,
        position: emp.position || '员工',
        department: emp.department || '未分配',
        status: emp.status,
        role: emp.role,
        location: emp.factory_name || '未分配',
        joinDate: emp.joined_at || new Date().toISOString().split('T')[0],
        lastLogin: new Date().toISOString().split('T')[0] + ' ' + new Date().toTimeString().split(' ')[0].substring(0,5),
        avatar: '',
        permissions: ['basic_access'],
        workSchedule: '9:00-18:00',
        emergencyContact: '-',
        performance: 0,
      }))

      setEmployees(formattedEmployees)
      console.log('格式化后的员工数据:', formattedEmployees)

      // 设置员工数量到统计信息
      setStatistics({
        total: formattedEmployees.length,
        active: formattedEmployees.filter(e => e.status === 'active').length,
        inactive: formattedEmployees.filter(e => e.status === 'inactive').length,
        pending: 0
      })

      // 加载企业功能数据（仅企业用户）
      if (isEnterpriseUser()) {
        const mockInvitations: EmployeeInvitation[] = [
          {
            id: 'inv1',
            email: 'newemployee@example.com',
            invitation_code: 'INV-2025-ABC123',
            role: 'operator',
            factory_name: '北京工厂',
            department_name: '技术部',
            status: 'pending',
            expires_at: dayjs().add(7, 'day').toISOString(),
            created_at: new Date().toISOString(),
          },
        ]

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
          },
        ]

        const mockDepartments: Department[] = [
          {
            id: 'd1',
            factory_id: 'f1',
            department_code: 'TECH',
            department_name: '技术部',
            description: '负责技术研发和工艺设计',
            manager_name: '张三',
            employee_count: 8,
          },
          {
            id: 'd2',
            factory_id: 'f1',
            department_code: 'PROD',
            department_name: '生产部',
            description: '负责生产制造',
            manager_name: '赵六',
            employee_count: 12,
          },
        ]

        const mockQuota: EmployeeQuota = {
          current: employees.length,
          max: 20,
          percentage: Math.round((employees.length / 20) * 100),
          tier: 'enterprise',
        }

        setInvitations(mockInvitations)
        setFactories(mockFactories)
        setDepartments(mockDepartments)
        setQuota(mockQuota)
      }
    } catch (error) {
      message.error('数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 统计数据
  const getStatistics = () => {
    const total = employees.length
    const active = employees.filter(emp => emp.status === 'active').length
    const pending = employees.filter(emp => emp.status === 'pending').length

    return {
      total,
      active,
      pending,
      avgPerformance: Math.round(
        employees.filter(emp => emp.performance > 0).reduce((sum, emp) => sum + emp.performance, 0) /
        employees.filter(emp => emp.performance > 0).length || 1
      ),
    }
  }

  const stats = getStatistics()

  // 处理函数
  const handleCreateEmployee = () => {
    form.validateFields().then(values => {
      const newEmployee: Employee = {
        id: Date.now().toString(),
        employee_number: `EMP${String(employees.length + 1).padStart(3, '0')}`,
        ...values,
        status: 'pending',
        location: values.location || '默认工厂',
        joinDate: dayjs().format('YYYY-MM-DD'),
        permissions: [],
        performance: 0,
        workSchedule: '9:00-18:00',
        emergencyContact: '',
      }
      setEmployees([...employees, newEmployee])
      setModalVisible(false)
      form.resetFields()
      message.success('员工创建成功')
    })
  }

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

  const handleCreateFactory = () => {
    form.validateFields().then(values => {
      const newFactory: Factory = {
        id: Date.now().toString(),
        employee_count: 0,
        is_headquarters: false,
        is_active: true,
        ...values,
      }
      setFactories([...factories, newFactory])
      setModalVisible(false)
      form.resetFields()
      message.success('工厂创建成功')
    })
  }

  const handleCreateDepartment = () => {
    form.validateFields().then(values => {
      const newDepartment: Department = {
        id: Date.now().toString(),
        employee_count: 0,
        ...values,
      }
      setDepartments([...departments, newDepartment])
      setModalVisible(false)
      form.resetFields()
      message.success('部门创建成功')
    })
  }

  // 过滤数据
  const filteredEmployees = employees.filter(employee => {
    const matchSearch = !searchText ||
      employee.name.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchText.toLowerCase()) ||
      employee.employee_number.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !filterStatus || employee.status === filterStatus
    const matchRole = !filterRole || employee.role === filterRole
    const matchFactory = !filterFactory || employee.location === filterFactory
    return matchSearch && matchStatus && matchRole && matchFactory
  })

  // 员工列表列配置
  const employeeColumns: ColumnsType<Employee> = [
    {
      title: '员工信息',
      key: 'employee',
      render: (_, record) => (
        <Space>
          <Avatar src={record.avatar} icon={<UserOutlined />} />
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
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const roleMap: Record<string, any> = {
          admin: { color: 'red', text: '管理员' },
          manager: { color: 'orange', text: '经理' },
          supervisor: { color: 'blue', text: '主管' },
          operator: { color: 'green', text: '操作员' },
          viewer: { color: 'default', text: '查看者' },
        }
        const config = roleMap[role] || { color: 'default', text: role }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap: Record<string, any> = {
          active: { color: 'success', text: '在职' },
          inactive: { color: 'error', text: '离职' },
          pending: { color: 'warning', text: '待入职' },
        }
        const config = statusMap[status] || { color: 'default', text: status }
        return (
          <Badge
            status={status === 'active' ? 'success' : status === 'pending' ? 'warning' : 'error'}
            text={config.text}
          />
        )
      },
    },
    {
      title: isEnterpriseUser() ? '工厂' : '位置',
      dataIndex: 'location',
      key: 'location',
      render: (text) => (
        <div>
          <EnvironmentOutlined className="mr-1" />
          <Text className="text-xs">{text}</Text>
        </div>
      ),
    },
    {
      title: '绩效',
      dataIndex: 'performance',
      key: 'performance',
      render: (performance) => (
        performance > 0 ? (
          <div>
            <Text strong>{performance}</Text>
            <Text type="secondary">/100</Text>
          </div>
        ) : <Text type="secondary">-</Text>
      ),
    },
    {
      title: '入职时间',
      dataIndex: 'joinDate',
      key: 'joinDate',
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
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
              form.setFieldsValue(record)
              setModalType('create')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
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
      render: (role) => <Tag>{role}</Tag>,
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
        const statusMap: Record<string, any> = {
          pending: { color: 'warning', text: '待接受' },
          accepted: { color: 'success', text: '已接受' },
          expired: { color: 'error', text: '已过期' },
          cancelled: { color: 'default', text: '已取消' },
        }
        const config = statusMap[status] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
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
            <Button
              type="text"
              danger
              onClick={() => {
                setInvitations(invitations.map(inv =>
                  inv.id === record.id ? { ...inv, status: 'cancelled' } : inv
                ))
                message.success('邀请已取消')
              }}
            >
              取消邀请
            </Button>
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
          {/* 配额显示 - 仅企业用户 */}
          {isEnterpriseUser() && quota && (
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
                  <Option value="pending">待入职</Option>
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
                  <Option value="manager">经理</Option>
                  <Option value="supervisor">主管</Option>
                  <Option value="operator">操作员</Option>
                </Select>
              </Col>
              {isEnterpriseUser() && (
                <Col xs={12} sm={6} md={4}>
                  <Select
                    placeholder="工厂筛选"
                    value={filterFactory}
                    onChange={setFilterFactory}
                    allowClear
                    style={{ width: '100%' }}
                  >
                    {factories.map(factory => (
                      <Option key={factory.id} value={factory.name}>
                        {factory.name}
                      </Option>
                    ))}
                  </Select>
                </Col>
              )}
              <Col xs={24} sm={12} md={6}>
                <Space>
                  {isEnterpriseUser() ? (
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
                  ) : (
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => {
                        setModalType('create')
                        setSelectedEmployee(null)
                        form.resetFields()
                        setModalVisible(true)
                      }}
                    >
                      添加员工
                    </Button>
                  )}
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
  ]

  // 企业功能标签页
  if (isEnterpriseUser()) {
    tabItems.push(
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
                  setSelectedEmployee(null)
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
                  setSelectedEmployee(null)
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
      }
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>
          {isEnterpriseUser() ? '企业员工管理' : '员工管理'}
        </Title>
        <Text type="secondary">
          {isEnterpriseUser()
            ? '管理企业员工、工厂和部门，设置权限和配额'
            : '管理员工信息和状态'
          }
        </Text>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="员工总数"
              value={stats.total}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="在职员工"
              value={stats.active}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待入职"
              value={stats.pending}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        {isEnterpriseUser() ? (
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
        ) : (
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="平均绩效"
                value={stats.avgPerformance}
                suffix="/ 100"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* 标签页 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
      />

      {/* 创建/编辑员工弹窗 */}
      <Modal
        title={modalType === 'invite' ? '邀请员工' : (selectedEmployee ? '编辑员工' : '添加员工')}
        open={modalVisible && modalType === 'create'}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={modalType === 'invite' ? handleInviteEmployee : handleCreateEmployee}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            role: 'operator',
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="姓名"
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
                <Input placeholder="请输入邮箱" />
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
                name="position"
                label="职位"
                rules={[{ required: true, message: '请输入职位' }]}
              >
                <Input placeholder="请输入职位" />
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
                <Select placeholder="请选择部门">
                  {departments.map(dept => (
                    <Option key={dept.id} value={dept.department_name}>
                      {dept.department_name}
                    </Option>
                  ))}
                  <Option value="技术部">技术部</Option>
                  <Option value="生产部">生产部</Option>
                  <Option value="质量部">质量部</Option>
                  <Option value="设备部">设备部</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="请选择角色">
                  <Option value="admin">管理员</Option>
                  <Option value="manager">经理</Option>
                  <Option value="supervisor">主管</Option>
                  <Option value="operator">操作员</Option>
                  <Option value="viewer">查看者</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          {isEnterpriseUser() && (
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="location"
                  label="工厂"
                  rules={[{ required: true, message: '请选择工厂' }]}
                >
                  <Select placeholder="请选择工厂">
                    {factories.map(factory => (
                      <Option key={factory.id} value={factory.name}>
                        {factory.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          )}
        </Form>
      </Modal>

      {/* 邀请员工弹窗 */}
      <Modal
        title="邀请员工"
        open={modalVisible && modalType === 'invite'}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleInviteEmployee}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            role: 'operator',
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
                  <Option value="operator">普通员工</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="factory_name"
                label="分配工厂"
                rules={[{ required: true, message: '请选择工厂' }]}
              >
                <Select placeholder="请选择工厂">
                  {factories.map(factory => (
                    <Option key={factory.id} value={factory.name}>
                      {factory.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="department_name"
            label="分配部门"
          >
            <Select placeholder="请选择部门">
              {departments.map(dept => (
                <Option key={dept.id} value={dept.department_name}>
                  {dept.department_name}
                </Option>
              ))}
            </Select>
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
                  <Avatar size={80} src={selectedEmployee.avatar} icon={<UserOutlined />} />
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
                    <Text strong>部门：</Text> {selectedEmployee.department}
                  </Col>
                  <Col span={12}>
                    <Text strong>角色：</Text> <Tag color="blue">{selectedEmployee.role}</Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>状态：</Text>
                    <Badge
                      status={selectedEmployee.status === 'active' ? 'success' : 'error'}
                      text={selectedEmployee.status === 'active' ? '在职' : '离职'}
                      className="ml-2"
                    />
                  </Col>
                  <Col span={12}>
                    <Text strong>入职时间：</Text> {dayjs(selectedEmployee.joinDate).format('YYYY-MM-DD')}
                  </Col>
                  <Col span={12}>
                    <Text strong>最后登录：</Text> {selectedEmployee.lastLogin || '从未登录'}
                  </Col>
                </Row>
              </Col>
            </Row>

            <Divider />

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="联系信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div><MailOutlined className="mr-2" />{selectedEmployee.email}</div>
                    <div><PhoneOutlined className="mr-2" />{selectedEmployee.phone}</div>
                    <div><EnvironmentOutlined className="mr-2" />{selectedEmployee.location}</div>
                    <div><CalendarOutlined className="mr-2" />{selectedEmployee.workSchedule}</div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="紧急联系人" size="small">
                  <Text>{selectedEmployee.emergencyContact}</Text>
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} className="mt-4">
              <Col span={12}>
                <Card title="权限设置" size="small">
                  <Space wrap>
                    {selectedEmployee.permissions.map((permission, index) => (
                      <Tag key={index} color="green">{permission}</Tag>
                    ))}
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="绩效评分" size="small">
                  <Statistic title="绩效评分" value={selectedEmployee.performance} suffix="/100" />
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default EmployeeManagement