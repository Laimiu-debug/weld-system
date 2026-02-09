import React, { useState, useEffect } from 'react'
import {
  Card,
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
  Popconfirm,
  Switch,
  Checkbox,
  Divider,
  Row,
  Col,
  Descriptions,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SafetyOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService, { CompanyRole, CreateRoleData, UpdateRoleData, PermissionConfig } from '@/services/enterprise'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select

// 权限模块配置
const PERMISSION_MODULES = [
  { key: 'wps_management', name: 'WPS管理', description: '焊接工艺规程管理' },
  { key: 'pqr_management', name: 'PQR管理', description: '焊接工艺评定管理' },
  { key: 'ppqr_management', name: 'pPQR管理', description: '预焊接工艺评定管理' },
  { key: 'equipment_management', name: '设备管理', description: '焊接设备管理' },
  { key: 'materials_management', name: '材料管理', description: '焊接材料管理' },
  { key: 'welders_management', name: '焊工管理', description: '焊工资质管理' },
  { key: 'employee_management', name: '员工管理', description: '企业员工管理' },
  { key: 'factory_management', name: '工厂管理', description: '工厂信息管理' },
  { key: 'department_management', name: '部门管理', description: '部门信息管理' },
  { key: 'role_management', name: '角色管理', description: '角色权限管理' },
  { key: 'reports_management', name: '报表管理', description: '数据报表管理' },
]

const PERMISSION_ACTIONS = [
  { key: 'view', name: '查看', color: 'blue' },
  { key: 'create', name: '创建', color: 'green' },
  { key: 'edit', name: '编辑', color: 'orange' },
  { key: 'delete', name: '删除', color: 'red' },
  { key: 'approve', name: '审批', color: 'purple' },
]

const RolesNew: React.FC = () => {
  const [roles, setRoles] = useState<CompanyRole[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit'>('create')
  const [selectedRole, setSelectedRole] = useState<CompanyRole | null>(null)
  const [form] = Form.useForm()

  // 加载角色列表
  const loadRoles = async () => {
    setLoading(true)
    try {
      const response = await enterpriseService.getRoles()
      if (response.data.success) {
        setRoles(response.data.data.items)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载角色列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRoles()
  }, [])

  // 打开创建/编辑模态框
  const handleOpenModal = (type: 'create' | 'edit', role?: CompanyRole) => {
    setModalType(type)
    setSelectedRole(role || null)
    
    if (type === 'edit' && role) {
      form.setFieldsValue({
        name: role.name,
        code: role.code,
        description: role.description,
        data_access_scope: role.data_access_scope,
        permissions: role.permissions,
      })
    } else {
      form.resetFields()
      // 设置默认权限（所有权限都为false）
      const defaultPermissions: any = {}
      PERMISSION_MODULES.forEach(module => {
        defaultPermissions[module.key] = {
          view: false,
          create: false,
          edit: false,
          delete: false,
          approve: false,
        }
      })
      form.setFieldsValue({ permissions: defaultPermissions })
    }
    
    setModalVisible(true)
  }

  // 关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false)
    setSelectedRole(null)
    form.resetFields()
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (modalType === 'create') {
        const createData: CreateRoleData = {
          name: values.name,
          code: values.code,
          description: values.description,
          permissions: values.permissions,
          data_access_scope: values.data_access_scope,
        }
        
        await enterpriseService.createRole(createData)
        message.success('角色创建成功')
      } else {
        const updateData: UpdateRoleData = {
          name: values.name,
          code: values.code,
          description: values.description,
          permissions: values.permissions,
          data_access_scope: values.data_access_scope,
        }
        
        await enterpriseService.updateRole(selectedRole!.id, updateData)
        message.success('角色更新成功')
      }
      
      handleCloseModal()
      loadRoles()
    } catch (error: any) {
      if (error.response) {
        message.error(error.response.data?.detail || '操作失败')
      }
    }
  }

  // 删除角色
  const handleDelete = async (roleId: string) => {
    try {
      await enterpriseService.deleteRole(roleId)
      message.success('角色删除成功')
      loadRoles()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  // 查看角色详情
  const handleViewDetail = (role: CompanyRole) => {
    setSelectedRole(role)
    setDetailModalVisible(true)
  }

  // 表格列定义
  const columns: ColumnsType<CompanyRole> = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <SafetyOutlined style={{ color: record.is_system ? '#1890ff' : '#52c41a' }} />
          <span>{text}</span>
          {record.is_system && <Tag color="blue">系统</Tag>}
        </Space>
      ),
    },
    {
      title: '角色代码',
      dataIndex: 'code',
      key: 'code',
      render: (text) => <Text code>{text}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '数据范围',
      dataIndex: 'data_access_scope',
      key: 'data_access_scope',
      render: (scope) => (
        <Tag color={scope === 'company' ? 'purple' : 'cyan'}>
          {scope === 'company' ? '全公司' : '工厂级'}
        </Tag>
      ),
    },
    {
      title: '员工数',
      dataIndex: 'employee_count',
      key: 'employee_count',
      render: (count) => (
        <Space>
          <TeamOutlined />
          <span>{count}</span>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Badge status={isActive ? 'success' : 'default'} text={isActive ? '启用' : '禁用'} />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal('edit', record)}
            disabled={record.is_system}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个角色吗？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            disabled={record.is_system || record.employee_count > 0}
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_system || record.employee_count > 0}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <SafetyOutlined />
            <span>角色管理</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal('create')}
          >
            创建角色
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={roles}
          rowKey={(record) => `${record.id}_${record.code}`}
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个角色`,
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={modalType === 'create' ? '创建角色' : '编辑角色'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={900}
        okText="确定"
        cancelText="取消"
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
                <Input placeholder="例如：质检员、生产主管" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="角色代码"
                rules={[{ required: true, message: '请输入角色代码' }]}
              >
                <Input placeholder="例如：QC_INSPECTOR" disabled={modalType === 'edit' && selectedRole?.is_system} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="角色描述"
          >
            <TextArea rows={3} placeholder="描述这个角色的职责和用途" />
          </Form.Item>

          <Form.Item
            name="data_access_scope"
            label="数据访问范围"
            rules={[{ required: true, message: '请选择数据访问范围' }]}
          >
            <Select>
              <Option value="factory">工厂级（只能访问所属工厂的数据）</Option>
              <Option value="company">公司级（可以访问全公司的数据）</Option>
            </Select>
          </Form.Item>

          <Divider>权限配置</Divider>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {PERMISSION_MODULES.map((module) => (
              <Card key={module.key} size="small" style={{ marginBottom: 16 }}>
                <Row align="middle">
                  <Col span={8}>
                    <Text strong>{module.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>{module.description}</Text>
                  </Col>
                  <Col span={16}>
                    <Space size="large">
                      {PERMISSION_ACTIONS.map((action) => (
                        <Form.Item
                          key={`${module.key}.${action.key}`}
                          name={['permissions', module.key, action.key]}
                          valuePropName="checked"
                          noStyle
                        >
                          <Checkbox>
                            <Tag color={action.color}>{action.name}</Tag>
                          </Checkbox>
                        </Form.Item>
                      ))}
                    </Space>
                  </Col>
                </Row>
              </Card>
            ))}
          </div>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="角色详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          selectedRole && !selectedRole.is_system && (
            <Button
              key="edit"
              type="primary"
              icon={<EditOutlined />}
              onClick={() => {
                setDetailModalVisible(false)
                handleOpenModal('edit', selectedRole)
              }}
            >
              编辑
            </Button>
          ),
        ]}
        width={800}
      >
        {selectedRole && (
          <>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="角色名称">{selectedRole.name}</Descriptions.Item>
              <Descriptions.Item label="角色代码">
                <Text code>{selectedRole.code}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="数据范围" span={2}>
                <Tag color={selectedRole.data_access_scope === 'company' ? 'purple' : 'cyan'}>
                  {selectedRole.data_access_scope === 'company' ? '全公司' : '工厂级'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="员工数" span={2}>
                <Space>
                  <TeamOutlined />
                  <span>{selectedRole.employee_count} 人</span>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="状态" span={2}>
                <Badge status={selectedRole.is_active ? 'success' : 'default'} text={selectedRole.is_active ? '启用' : '禁用'} />
                {selectedRole.is_system && <Tag color="blue" style={{ marginLeft: 8 }}>系统角色</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedRole.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedRole.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {dayjs(selectedRole.updated_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <Divider>权限详情</Divider>

            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {PERMISSION_MODULES.map((module) => {
                const modulePerms = selectedRole.permissions[module.key as keyof typeof selectedRole.permissions] as PermissionConfig | undefined
                if (!modulePerms) return null

                const hasAnyPermission = modulePerms.view || modulePerms.create || modulePerms.edit || modulePerms.delete

                return (
                  <Card key={module.key} size="small" style={{ marginBottom: 12 }}>
                    <Row align="middle">
                      <Col span={8}>
                        <Text strong>{module.name}</Text>
                      </Col>
                      <Col span={16}>
                        {hasAnyPermission ? (
                          <Space>
                            {modulePerms.view && <Tag color="blue">查看</Tag>}
                            {modulePerms.create && <Tag color="green">创建</Tag>}
                            {modulePerms.edit && <Tag color="orange">编辑</Tag>}
                            {modulePerms.delete && <Tag color="red">删除</Tag>}
                          </Space>
                        ) : (
                          <Text type="secondary">无权限</Text>
                        )}
                      </Col>
                    </Row>
                  </Card>
                )
              })}
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}

export default RolesNew

