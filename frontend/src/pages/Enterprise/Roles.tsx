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
  Tooltip,
  Switch,
  Checkbox,
  Divider,
} from 'antd'
import {
  CrownOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  SettingOutlined,
  EyeOutlined,
  UserOutlined,
  SafetyOutlined,
  FileTextOutlined,
  ToolOutlined,
  DatabaseOutlined,
  ApartmentOutlined,
  BarChartOutlined,
  ShopOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService from '@/services/enterprise'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 接口定义
interface Role {
  id: string
  name: string
  code: string
  description: string
  permissions: Record<string, boolean>
  employee_count: number
  is_system: boolean
  created_at: string
  updated_at: string
}

interface PermissionGroup {
  key: string
  name: string
  icon: React.ReactNode
  permissions: {
    key: string
    name: string
    description: string
  }[]
}

const Roles: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit'>('create')
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(false)

  // 权限组配置
  const permissionGroups: PermissionGroup[] = [
    {
      key: 'wps',
      name: 'WPS管理',
      icon: <FileTextOutlined />,
      permissions: [
        { key: 'wps_read', name: '查看WPS', description: '查看WPS列表和详情' },
        { key: 'wps_create', name: '创建WPS', description: '创建新的WPS文件' },
        { key: 'wps_update', name: '编辑WPS', description: '修改现有WPS文件' },
        { key: 'wps_delete', name: '删除WPS', description: '删除WPS文件' },
        { key: 'wps_approve', name: '审批WPS', description: '审批WPS文件' },
        { key: 'wps_export', name: '导出WPS', description: '导出WPS文件' },
      ],
    },
    {
      key: 'pqr',
      name: 'PQR管理',
      icon: <FileTextOutlined />,
      permissions: [
        { key: 'pqr_read', name: '查看PQR', description: '查看PQR列表和详情' },
        { key: 'pqr_create', name: '创建PQR', description: '创建新的PQR文件' },
        { key: 'pqr_update', name: '编辑PQR', description: '修改现有PQR文件' },
        { key: 'pqr_delete', name: '删除PQR', description: '删除PQR文件' },
        { key: 'pqr_approve', name: '审批PQR', description: '审批PQR文件' },
        { key: 'pqr_export', name: '导出PQR', description: '导出PQR文件' },
      ],
    },
    {
      key: 'materials',
      name: '焊材管理',
      icon: <DatabaseOutlined />,
      permissions: [
        { key: 'materials_read', name: '查看焊材', description: '查看焊材库存信息' },
        { key: 'materials_create', name: '添加焊材', description: '添加新的焊材' },
        { key: 'materials_update', name: '编辑焊材', description: '修改焊材信息' },
        { key: 'materials_delete', name: '删除焊材', description: '删除焊材' },
        { key: 'materials_inventory', name: '库存管理', description: '管理焊材库存' },
      ],
    },
    {
      key: 'welders',
      name: '焊工管理',
      icon: <TeamOutlined />,
      permissions: [
        { key: 'welders_read', name: '查看焊工', description: '查看焊工信息' },
        { key: 'welders_create', name: '添加焊工', description: '添加新焊工' },
        { key: 'welders_update', name: '编辑焊工', description: '修改焊工信息' },
        { key: 'welders_delete', name: '删除焊工', description: '删除焊工' },
        { key: 'welders_cert', name: '资质管理', description: '管理焊工资质证书' },
      ],
    },
    {
      key: 'equipment',
      name: '设备管理',
      icon: <ToolOutlined />,
      permissions: [
        { key: 'equipment_read', name: '查看设备', description: '查看设备信息' },
        { key: 'equipment_create', name: '添加设备', description: '添加新设备' },
        { key: 'equipment_update', name: '编辑设备', description: '修改设备信息' },
        { key: 'equipment_delete', name: '删除设备', description: '删除设备' },
        { key: 'equipment_maintain', name: '维护管理', description: '设备维护管理' },
      ],
    },
    {
      key: 'production',
      name: '生产管理',
      icon: <ApartmentOutlined />,
      permissions: [
        { key: 'production_read', name: '查看生产', description: '查看生产任务' },
        { key: 'production_create', name: '创建生产', description: '创建生产任务' },
        { key: 'production_update', name: '编辑生产', description: '修改生产任务' },
        { key: 'production_delete', name: '删除生产', description: '删除生产任务' },
        { key: 'production_schedule', name: '排程管理', description: '生产排程管理' },
      ],
    },
    {
      key: 'quality',
      name: '质量管理',
      icon: <SafetyOutlined />,
      permissions: [
        { key: 'quality_read', name: '查看质检', description: '查看质检记录' },
        { key: 'quality_create', name: '创建质检', description: '创建质检任务' },
        { key: 'quality_update', name: '编辑质检', description: '修改质检记录' },
        { key: 'quality_delete', name: '删除质检', description: '删除质检记录' },
        { key: 'quality_approve', name: '质检审批', description: '审批质检结果' },
      ],
    },
    {
      key: 'reports',
      name: '报表管理',
      icon: <BarChartOutlined />,
      permissions: [
        { key: 'reports_read', name: '查看报表', description: '查看各类报表' },
        { key: 'reports_create', name: '创建报表', description: '创建自定义报表' },
        { key: 'reports_update', name: '编辑报表', description: '修改报表' },
        { key: 'reports_delete', name: '删除报表', description: '删除报表' },
        { key: 'reports_export', name: '导出报表', description: '导出报表数据' },
      ],
    },
    {
      key: 'enterprise',
      name: '企业管理',
      icon: <ShopOutlined />,
      permissions: [
        { key: 'enterprise_employees', name: '员工管理', description: '管理企业员工' },
        { key: 'enterprise_factories', name: '工厂管理', description: '管理工厂' },
        { key: 'enterprise_departments', name: '部门管理', description: '管理部门' },
        { key: 'enterprise_roles', name: '角色管理', description: '管理角色权限' },
        { key: 'enterprise_invitations', name: '邀请管理', description: '管理员工邀请' },
      ],
    },
  ]

  // 加载角色数据
  useEffect(() => {
    loadRoles()
  }, [])

  const loadRoles = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      const mockRoles: Role[] = [
        {
          id: '1',
          name: '系统管理员',
          code: 'ADMIN',
          description: '拥有所有权限的系统管理员',
          permissions: permissionGroups.reduce((acc, group) => {
            group.permissions.forEach(perm => {
              acc[perm.key] = true
            })
            return acc
          }, {} as Record<string, boolean>),
          employee_count: 1,
          is_system: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: '技术主管',
          code: 'TECH_SUPERVISOR',
          description: '负责技术部门的主管角色',
          permissions: {
            wps_read: true,
            wps_create: true,
            wps_update: true,
            wps_approve: true,
            wps_export: true,
            pqr_read: true,
            pqr_create: true,
            pqr_update: true,
            pqr_approve: true,
            materials_read: true,
            quality_read: true,
            reports_read: true,
          },
          employee_count: 2,
          is_system: false,
          created_at: '2024-01-15T00:00:00Z',
          updated_at: '2024-01-15T00:00:00Z',
        },
        {
          id: '3',
          name: '生产主管',
          code: 'PROD_SUPERVISOR',
          description: '负责生产部门的主管角色',
          permissions: {
            wps_read: true,
            pqr_read: true,
            welders_read: true,
            welders_create: true,
            welders_update: true,
            equipment_read: true,
            equipment_create: true,
            equipment_update: true,
            production_read: true,
            production_create: true,
            production_update: true,
            production_schedule: true,
            quality_read: true,
            reports_read: true,
          },
          employee_count: 1,
          is_system: false,
          created_at: '2024-01-15T00:00:00Z',
          updated_at: '2024-01-15T00:00:00Z',
        },
        {
          id: '4',
          name: '普通员工',
          code: 'EMPLOYEE',
          description: '基础员工角色，拥有基本查看权限',
          permissions: {
            wps_read: true,
            pqr_read: true,
            materials_read: true,
            welders_read: true,
            equipment_read: true,
            production_read: true,
            quality_read: true,
            reports_read: true,
          },
          employee_count: 15,
          is_system: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '5',
          name: '质检员',
          code: 'QUALITY_INSPECTOR',
          description: '负责质量检查的专门角色',
          permissions: {
            wps_read: true,
            pqr_read: true,
            welders_read: true,
            equipment_read: true,
            production_read: true,
            quality_read: true,
            quality_create: true,
            quality_update: true,
            quality_approve: true,
            reports_read: true,
            reports_create: true,
          },
          employee_count: 3,
          is_system: false,
          created_at: '2024-02-01T00:00:00Z',
          updated_at: '2024-02-01T00:00:00Z',
        },
      ]
      setRoles(mockRoles)
    } catch (error) {
      message.error('加载角色数据失败')
    } finally {
      setLoading(false)
    }
  }

  // 统计数据
  const getStatistics = () => {
    const total = roles.length
    const systemRoles = roles.filter(r => r.is_system).length
    const customRoles = roles.filter(r => !r.is_system).length
    const totalEmployees = roles.reduce((sum, role) => sum + role.employee_count, 0)

    return { total, systemRoles, customRoles, totalEmployees }
  }

  const stats = getStatistics()

  // 过滤数据
  const filteredRoles = roles.filter(role => {
    const matchSearch = !searchText ||
      role.name.toLowerCase().includes(searchText.toLowerCase()) ||
      role.code.toLowerCase().includes(searchText.toLowerCase()) ||
      role.description.toLowerCase().includes(searchText.toLowerCase())
    return matchSearch
  })

  // 角色列表列配置
  const columns: ColumnsType<Role> = [
    {
      title: '角色信息',
      key: 'role',
      render: (_, record) => (
        <Space>
          <Avatar icon={<CrownOutlined />} />
          <div>
            <div>
              <Text strong>{record.name}</Text>
              {record.is_system && <Tag color="red" className="ml-2">系统角色</Tag>}
            </div>
            <div>
              <Text type="secondary" className="text-xs">{record.code}</Text>
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '权限数量',
      key: 'permissions',
      render: (_, record) => {
        const permissionCount = Object.values(record.permissions).filter(Boolean).length
        const totalPermissions = permissionGroups.reduce((sum, group) => sum + group.permissions.length, 0)
        return (
          <div>
            <Text strong>{permissionCount}</Text>
            <Text type="secondary"> / {totalPermissions}</Text>
          </div>
        )
      },
    },
    {
      title: '员工数量',
      dataIndex: 'employee_count',
      key: 'employee_count',
      render: (count) => (
        <Badge count={count} showZero style={{ backgroundColor: '#52c41a' }} />
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
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedRole(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          {!record.is_system && (
            <>
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => {
                  setSelectedRole(record)
                  form.setFieldsValue(record)
                  setModalType('edit')
                  setModalVisible(true)
                }}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定要删除这个角色吗？"
                onConfirm={() => {
                  setRoles(roles.filter(r => r.id !== record.id))
                  message.success('角色删除成功')
                }}
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
            </>
          )}
        </Space>
      ),
    },
  ]

  // 创建角色
  const handleCreateRole = () => {
    form.validateFields().then(values => {
      const newRole: Role = {
        id: Date.now().toString(),
        name: values.name,
        code: values.code,
        description: values.description,
        permissions: values.permissions || {},
        employee_count: 0,
        is_system: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setRoles([...roles, newRole])
      setModalVisible(false)
      form.resetFields()
      message.success('角色创建成功')
    })
  }

  // 更新角色
  const handleUpdateRole = () => {
    if (selectedRole) {
      form.validateFields().then(values => {
        const updatedRoles = roles.map(role =>
          role.id === selectedRole.id
            ? {
                ...role,
                ...values,
                updated_at: new Date().toISOString(),
              }
            : role
        )
        setRoles(updatedRoles)
        setModalVisible(false)
        form.resetFields()
        setSelectedRole(null)
        message.success('角色更新成功')
      })
    }
  }

  // 权限变更处理
  const handlePermissionChange = (groupKey: string, permissionKey: string, checked: boolean) => {
    const currentPermissions = form.getFieldValue('permissions') || {}
    form.setFieldsValue({
      permissions: {
        ...currentPermissions,
        [permissionKey]: checked,
      },
    })
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>角色设置</Title>
        <Text type="secondary">管理企业角色权限配置，预设员工的角色和权限</Text>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="角色总数"
              value={stats.total}
              prefix={<CrownOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统角色"
              value={stats.systemRoles}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="自定义角色"
              value={stats.customRoles}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已分配员工"
              value={stats.totalEmployees}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和操作 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="搜索角色名称、编码或描述"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="角色类型"
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="system">系统角色</Option>
              <Option value="custom">自定义角色</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="权限数量"
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="high">高权限</Option>
              <Option value="medium">中权限</Option>
              <Option value="low">低权限</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setModalType('create')
                  setSelectedRole(null)
                  form.resetFields()
                  setModalVisible(true)
                }}
              >
                创建角色
              </Button>
              <Button icon={<ExportOutlined />}>
                导出配置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 角色列表 */}
      <Card title="角色列表">
        <Table
          columns={columns}
          dataSource={filteredRoles}
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

      {/* 创建/编辑角色弹窗 */}
      <Modal
        title={modalType === 'create' ? '创建角色' : '编辑角色'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setSelectedRole(null)
        }}
        onOk={modalType === 'create' ? handleCreateRole : handleUpdateRole}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="角色名称"
                rules={[{ required: true, message: '请输入角色名称' }]}
              >
                <Input placeholder="请输入角色名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="角色编码"
                rules={[{ required: true, message: '请输入角色编码' }]}
              >
                <Input placeholder="请输入角色编码" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="角色描述"
            rules={[{ required: true, message: '请输入角色描述' }]}
          >
            <TextArea placeholder="请输入角色描述" rows={3} />
          </Form.Item>

          <Divider>权限配置</Divider>

          <Form.Item name="permissions" label="权限设置">
            {permissionGroups.map(group => (
              <Card key={group.key} size="small" style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 14 }}>
                    {group.icon} {group.name}
                  </Text>
                </div>
                <Row gutter={[16, 8]}>
                  {group.permissions.map(permission => (
                    <Col span={12} key={permission.key}>
                      <Checkbox
                        onChange={(e) => handlePermissionChange(group.key, permission.key, e.target.checked)}
                      >
                        <Text style={{ fontSize: 12 }}>{permission.name}</Text>
                      </Checkbox>
                    </Col>
                  ))}
                </Row>
              </Card>
            ))}
          </Form.Item>
        </Form>
      </Modal>

      {/* 角色详情弹窗 */}
      <Modal
        title="角色详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {selectedRole && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={6}>
                <div className="text-center">
                  <Avatar size={80} icon={<CrownOutlined />} />
                  <div className="mt-2">
                    <Title level={4}>{selectedRole.name}</Title>
                    <Tag color="blue">{selectedRole.code}</Tag>
                    {selectedRole.is_system && (
                      <Tag color="red" className="ml-2">系统角色</Tag>
                    )}
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>角色编码：</Text> {selectedRole.code}
                  </Col>
                  <Col span={12}>
                    <Text strong>员工数量：</Text> {selectedRole.employee_count} 人
                  </Col>
                  <Col span={12}>
                    <Text strong>创建时间：</Text> {dayjs(selectedRole.created_at).format('YYYY-MM-DD HH:mm')}
                  </Col>
                  <Col span={12}>
                    <Text strong>更新时间：</Text> {dayjs(selectedRole.updated_at).format('YYYY-MM-DD HH:mm')}
                  </Col>
                </Row>
              </Col>
            </Row>

            <Card title="角色描述" size="small" className="mb-4">
              <Text>{selectedRole.description}</Text>
            </Card>

            <Card title="权限详情" size="small">
              {permissionGroups.map(group => {
                const groupPermissions = group.permissions.filter(perm => selectedRole.permissions[perm.key])
                if (groupPermissions.length === 0) return null

                return (
                  <div key={group.key} style={{ marginBottom: 16 }}>
                    <Text strong style={{ marginBottom: 8, display: 'block' }}>
                      {group.icon} {group.name} ({groupPermissions.length}/{group.permissions.length})
                    </Text>
                    <Space wrap>
                      {groupPermissions.map(permission => (
                        <Tag key={permission.key} color="green">
                          {permission.name}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                )
              })}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Roles