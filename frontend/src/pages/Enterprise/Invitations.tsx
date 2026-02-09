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
  Progress,
  Alert,
  Switch,
} from 'antd'
import {
  MailOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  SendOutlined,
  EyeOutlined,
  StopOutlined,
  UsergroupAddOutlined,
  HomeOutlined,
  BankOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService from '@/services/enterprise'
import { useEnterpriseInvitations, useEmployeeQuota } from '@/hooks/useEnterprise'

const { Title, Text } = Typography
const { Option } = Select

// 接口定义
interface EmployeeInvitation {
  id: string
  email: string
  invitation_code: string
  role: 'admin' | 'employee'
  factory_id?: string
  factory_name?: string
  department_id?: string
  department_name?: string
  permissions: Record<string, boolean>
  status: 'pending' | 'accepted' | 'expired' | 'cancelled'
  expires_at: string
  accepted_at?: string
  created_at: string
  invited_by?: string
  message?: string
}

interface Factory {
  id: string
  name: string
}

interface Department {
  id: string
  factory_id: string
  department_name: string
}

const Invitations: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedInvitation, setSelectedInvitation] = useState<EmployeeInvitation | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterRole, setFilterRole] = useState<string>('')
  const [filterFactory, setFilterFactory] = useState<string>('')
  const [factories, setFactories] = useState<Factory[]>([])
  const [departments, setDepartments] = useState<Department[]>([])

  // 使用邀请管理Hook
  const {
    invitations,
    loading,
    total,
    loadInvitations,
    cancelInvitation,
    resendInvitation,
  } = useEnterpriseInvitations({
    status: filterStatus || undefined,
  })

  const { quota, loading: quotaLoading } = useEmployeeQuota()

  // 加载工厂和部门数据
  useEffect(() => {
    const loadFactoryAndDepartmentData = async () => {
      try {
        // 加载工厂数据
        const factoryResponse = await enterpriseService.getFactories()
        setFactories(factoryResponse.data.items || [])

        // 加载部门数据
        const departmentResponse = await enterpriseService.getDepartments()
        setDepartments(departmentResponse.data.items || [])
      } catch (error) {
        message.error('加载基础数据失败')
      }
    }
    loadFactoryAndDepartmentData()
  }, [])

  // 统计数据
  const getStatistics = () => {
    const total = invitations.length
    const pending = invitations.filter(inv => inv.status === 'pending').length
    const accepted = invitations.filter(inv => inv.status === 'accepted').length
    const expired = invitations.filter(inv => inv.status === 'expired').length
    const cancelled = invitations.filter(inv => inv.status === 'cancelled').length

    return { total, pending, accepted, expired, cancelled }
  }

  const stats = getStatistics()

  // 过滤数据
  const filteredInvitations = invitations.filter(invitation => {
    const matchSearch = !searchText ||
      invitation.email.toLowerCase().includes(searchText.toLowerCase()) ||
      invitation.invitation_code.toLowerCase().includes(searchText.toLowerCase())
    const matchStatus = !filterStatus || invitation.status === filterStatus
    const matchRole = !filterRole || invitation.role === filterRole
    const matchFactory = !filterFactory || invitation.factory_id === filterFactory
    return matchSearch && matchStatus && matchRole && matchFactory
  })

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap: Record<string, any> = {
      pending: { color: 'warning', text: '待接受', icon: <ClockCircleOutlined /> },
      accepted: { color: 'success', text: '已接受', icon: <CheckCircleOutlined /> },
      expired: { color: 'error', text: '已过期', icon: <CloseCircleOutlined /> },
      cancelled: { color: 'default', text: '已取消', icon: <StopOutlined /> },
    }
    return statusMap[status] || { color: 'default', text: status, icon: null }
  }

  // 邀请列表列配置
  const columns: ColumnsType<EmployeeInvitation> = [
    {
      title: '邮箱地址',
      dataIndex: 'email',
      key: 'email',
      render: (email) => (
        <Space>
          <MailOutlined />
          <Text>{email}</Text>
        </Space>
      ),
    },
    {
      title: '邀请码',
      dataIndex: 'invitation_code',
      key: 'invitation_code',
      render: (code) => (
        <Space>
          <Text copyable={{ text: code }} style={{ cursor: 'pointer' }}>
            {code}
          </Text>
          <Tooltip title="点击复制邀请码">
            <Text type="secondary" style={{ cursor: 'pointer' }}>
              <CheckCircleOutlined />
            </Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const roleMap: Record<string, any> = {
          admin: { color: 'red', text: '管理员' },
          employee: { color: 'blue', text: '员工' },
        }
        const config = roleMap[role] || { color: 'default', text: role }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '分配工厂/部门',
      key: 'organization',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <HomeOutlined className="mr-1" />
            <Text className="text-xs">{record.factory_name || '未分配'}</Text>
          </div>
          <div>
            <BankOutlined className="mr-1" />
            <Text className="text-xs">{record.department_name || '未分配'}</Text>
          </div>
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
            status={status === 'pending' ? 'warning' : status === 'accepted' ? 'success' : status === 'expired' ? 'error' : 'default'}
            text={config.text}
            icon={config.icon}
          />
        )
      },
    },
    {
      title: '有效期',
      key: 'expiry',
      render: (_, record) => {
        const expiresAt = dayjs(record.expires_at)
        const now = dayjs()
        const hoursLeft = expiresAt.diff(now, 'hours')

        return (
          <div>
            <div>
              <Text className="text-xs">{expiresAt.format('MM-DD HH:mm')}</Text>
            </div>
            {record.status === 'pending' && (
              <div>
                {hoursLeft > 0 ? (
                  <Text type="secondary" className="text-xs">
                    剩余 {hoursLeft} 小时
                  </Text>
                ) : (
                  <Text type="danger" className="text-xs">
                    已过期
                  </Text>
                )}
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => dayjs(date).format('MM-DD HH:mm'),
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
              setSelectedInvitation(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          {record.status === 'pending' && (
            <Button
              type="text"
              icon={<SendOutlined />}
              onClick={() => resendInvitation(record.id)}
            >
              重新发送
            </Button>
          )}
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个邀请吗？"
              onConfirm={() => cancelInvitation(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
                icon={<StopOutlined />}
              >
                取消邀请
              </Button>
            </Popconfirm>
          )}
          {record.status === 'expired' && (
            <Button
              type="text"
              icon={<SendOutlined />}
              onClick={() => {
                // 重新创建邀请
                handleResendExpiredInvitation(record)
              }}
            >
              重新邀请
            </Button>
          )}
        </Space>
      ),
    },
  ]

  // 发送邀请
  const handleSendInvitation = () => {
    form.validateFields().then(values => {
      if (!quota || quota.current >= quota.max) {
        message.error('员工配额已满，无法发送邀请')
        return
      }

      const newInvitation: EmployeeInvitation = {
        id: Date.now().toString(),
        invitation_code: `INV-${Date.now().toString(36).toUpperCase()}`,
        status: 'pending',
        expires_at: dayjs().add(7, 'day').toISOString(),
        created_at: new Date().toISOString(),
        ...values,
      }

      invitations.unshift(newInvitation)
      setModalVisible(false)
      form.resetFields()
      message.success('邀请已发送，请查收邮件')
    })
  }

  // 重新发送过期邀请
  const handleResendExpiredInvitation = (expiredInvitation: EmployeeInvitation) => {
    if (!quota || quota.current >= quota.max) {
      message.error('员工配额已满，无法重新邀请')
      return
    }

    const newInvitation: EmployeeInvitation = {
      ...expiredInvitation,
      id: Date.now().toString(),
      invitation_code: `INV-${Date.now().toString(36).toUpperCase()}`,
      status: 'pending',
      expires_at: dayjs().add(7, 'day').toISOString(),
      created_at: new Date().toISOString(),
    }

    const updatedInvitations = invitations.map(inv =>
      inv.id === expiredInvitation.id ? { ...inv, status: 'cancelled' } : inv
    )
    updatedInvitations.unshift(newInvitation)

    setInvitations(updatedInvitations)
    message.success('邀请已重新发送')
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>邀请管理</Title>
        <Text type="secondary">管理企业员工邀请，发送邀请码并跟踪邀请状态</Text>
      </div>

      {/* 配额显示 */}
      {!quotaLoading && quota && (
        <Alert
          message="邀请配额"
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
          className="mb-6"
        />
      )}

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="邀请总数"
              value={stats.total}
              prefix={<MailOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待接受"
              value={stats.pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已接受"
              value={stats.accepted}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已过期"
              value={stats.expired}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索邮箱地址或邀请码"
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
              <Option value="pending">待接受</Option>
              <Option value="accepted">已接受</Option>
              <Option value="expired">已过期</Option>
              <Option value="cancelled">已取消</Option>
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
                  setModalVisible(true)
                  form.resetFields()
                }}
                disabled={quota ? quota.current >= quota.max : false}
              >
                发送邀请
              </Button>
              <Button icon={<ExportOutlined />}>
                导出记录
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 邀请列表 */}
      <Card title="邀请记录">
        <Table
          columns={columns}
          dataSource={filteredInvitations}
          rowKey={(record) => `${record.id}_${record.invitation_code}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 发送邀请弹窗 */}
      <Modal
        title="发送邀请"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleSendInvitation}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            role: 'employee',
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

          <Form.Item
            name="message"
            label="邀请留言（可选）"
          >
            <Input.TextArea
              placeholder="输入给员工的邀请留言..."
              rows={3}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="分配角色"
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
          </Row>

          <Form.Item
            name="department_id"
            label="分配部门"
          >
            <Select placeholder="请选择部门">
              {departments
                .filter(dept => !filterFactory || dept.factory_id === filterFactory)
                .map(department => (
                  <Option key={department.id} value={department.id}>
                    {department.department_name}
                  </Option>
                ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="expires_at"
            label="邀请有效期"
            rules={[{ required: true, message: '请选择有效期' }]}
          >
            <Select placeholder="请选择有效期">
              <Option value={dayjs().add(3, 'day').toISOString()}>3天</Option>
              <Option value={dayjs().add(7, 'day').toISOString()}>7天</Option>
              <Option value={dayjs().add(14, 'day').toISOString()}>14天</Option>
              <Option value={dayjs().add(30, 'day').toISOString()}>30天</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 邀请详情弹窗 */}
      <Modal
        title="邀请详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedInvitation && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={6}>
                <div className="text-center">
                  <Avatar size={80} icon={<MailOutlined />} />
                  <div className="mt-2">
                    <Title level={4}>邀请详情</Title>
                    <Tag color="blue">{selectedInvitation.invitation_code}</Tag>
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>邮箱地址：</Text> {selectedInvitation.email}
                  </Col>
                  <Col span={12}>
                    <Text strong>分配角色：</Text>
                    <Tag color={selectedInvitation.role === 'admin' ? 'red' : 'blue'} className="ml-2">
                      {selectedInvitation.role === 'admin' ? '管理员' : '员工'}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>邀请状态：</Text>
                    <Badge
                      status={
                        selectedInvitation.status === 'pending' ? 'warning' :
                        selectedInvitation.status === 'accepted' ? 'success' :
                        selectedInvitation.status === 'expired' ? 'error' : 'default'
                      }
                      text={getStatusConfig(selectedInvitation.status).text}
                      className="ml-2"
                    />
                  </Col>
                  <Col span={12}>
                    <Text strong>创建时间：</Text> {dayjs(selectedInvitation.created_at).format('YYYY-MM-DD HH:mm')}
                  </Col>
                  {selectedInvitation.accepted_at && (
                    <Col span={12}>
                      <Text strong>接受时间：</Text> {dayjs(selectedInvitation.accepted_at).format('YYYY-MM-DD HH:mm')}
                    </Col>
                  )}
                </Row>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="分配信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>工厂：</Text>
                      <Text className="ml-2">{selectedInvitation.factory_name || '未分配'}</Text>
                    </div>
                    <div>
                      <Text strong>部门：</Text>
                      <Text className="ml-2">{selectedInvitation.department_name || '未分配'}</Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="有效期信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>过期时间：</Text>
                      <Text className="ml-2">{dayjs(selectedInvitation.expires_at).format('YYYY-MM-DD HH:mm')}</Text>
                    </div>
                    <div>
                      <Text strong>剩余时间：</Text>
                      <Text className="ml-2">
                        {(() => {
                          const expiresAt = dayjs(selectedInvitation.expires_at)
                          const now = dayjs()
                          const hoursLeft = expiresAt.diff(now, 'hours')
                          if (hoursLeft > 0) {
                            return <Text type="success">{hoursLeft} 小时</Text>
                          } else {
                            return <Text type="danger">已过期</Text>
                          }
                        })()}
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>

            {selectedInvitation.message && (
              <Card title="邀请留言" size="small" className="mt-4">
                <Text>{selectedInvitation.message}</Text>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Invitations