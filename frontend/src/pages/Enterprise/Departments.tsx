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
} from 'antd'
import {
  BankOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ExportOutlined,
  TeamOutlined,
  HomeOutlined,
  UserOutlined,
  EyeOutlined,
  SettingOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import enterpriseService from '@/services/enterprise'
import { useEnterpriseDepartments, useEnterpriseFactories } from '@/hooks/useEnterprise'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

// 接口定义
interface SimpleEmployee {
  id: string
  user_id: string
  employee_number: string
  name: string
  email: string
  phone: string
  role: 'admin' | 'manager' | 'employee'
  position: string
  joined_at: string
}

interface Department {
  id: string
  company_id: string
  factory_id?: string
  factory_name?: string
  department_code: string
  department_name: string
  description: string
  manager_id?: string
  manager_name?: string
  employee_count: number
  employees: SimpleEmployee[]  // 添加员工列表
  created_at: string
}

const Departments: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit'>('create')
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null)
  const [form] = Form.useForm()
  const [searchText, setSearchText] = useState('')
  const [filterFactory, setFilterFactory] = useState<string>('')

  // 使用部门管理Hook
  const {
    departments,
    loading,
    total,
    loadDepartments,
    createDepartment,
    updateDepartment,
    deleteDepartment,
  } = useEnterpriseDepartments({
    factory_id: filterFactory || undefined,
  })

  // 使用工厂管理Hook获取工厂数据
  const { factories } = useEnterpriseFactories({
    is_active: true, // 只获取活跃的工厂
  })

  // 统计数据
  const getStatistics = () => {
    const total = departments.length
    const totalEmployees = departments.reduce((sum, dept) => sum + dept.employee_count, 0)
    const withManager = departments.filter(dept => dept.manager_name).length

    return { total, totalEmployees, withManager }
  }

  const stats = getStatistics()

  // 过滤数据
  const filteredDepartments = departments.filter(department => {
    const matchSearch = !searchText ||
      department.department_name.toLowerCase().includes(searchText.toLowerCase()) ||
      department.department_code.toLowerCase().includes(searchText.toLowerCase()) ||
      department.description.toLowerCase().includes(searchText.toLowerCase())
    const matchFactory = !filterFactory || department.factory_id === filterFactory
    return matchSearch && matchFactory
  })

  // 部门列表列配置
  const columns: ColumnsType<Department> = [
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
      key: 'manager',
      render: (_, record) => (
        record.manager_name ? (
          <Space>
            <Avatar size="small" icon={<UserOutlined />} />
            <Text>{record.manager_name}</Text>
          </Space>
        ) : (
          <Text type="secondary">未设置</Text>
        )
      ),
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
      title: '所属工厂',
      key: 'factory',
      render: (_, record) => {
        const factory = factories.find(f => f.id === record.factory_id)
        return factory ? (
          <Space>
            <HomeOutlined />
            <Text>{factory.name}</Text>
          </Space>
        ) : (
          <Text type="secondary">未分配</Text>
        )
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
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedDepartment(record)
              setDetailModalVisible(true)
            }}
          >
            查看
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedDepartment(record)
              form.setFieldsValue(record)
              setModalType('edit')
              setModalVisible(true)
            }}
          >
            编辑
          </Button>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => {
              setSelectedDepartment(record)
              setDetailModalVisible(true)
            }}
          >
            设置
          </Button>
          <Popconfirm
            title="确定要删除这个部门吗？"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => deleteDepartment(record.id)}
            okText="确定"
            cancelText="取消"
            okType="danger"
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

  // 创建部门
  const handleCreateDepartment = () => {
    form.validateFields().then(values => {
      createDepartment(values).then((success) => {
        if (success) {
          setModalVisible(false)
          form.resetFields()
          loadDepartments()
        }
      })
    })
  }

  // 更新部门
  const handleUpdateDepartment = () => {
    if (selectedDepartment) {
      form.validateFields().then(values => {
        updateDepartment(selectedDepartment.id, values).then((success) => {
          if (success) {
            setModalVisible(false)
            form.resetFields()
            setSelectedDepartment(null)
          }
        })
      })
    }
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>部门管理</Title>
        <Text type="secondary">管理企业组织架构和部门设置</Text>
      </div>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="部门总数"
              value={stats.total}
              prefix={<BankOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="员工总数"
              value={stats.totalEmployees}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="已设负责人"
              value={stats.withManager}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="搜索部门名称、编码或描述"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
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
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="部门类型"
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="tech">技术部门</Option>
              <Option value="prod">生产部门</Option>
              <Option value="quality">质量部门</Option>
              <Option value="admin">行政部门</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                disabled={factories.length === 0}
                onClick={() => {
                  setModalType('create')
                  setSelectedDepartment(null)
                  form.resetFields()
                  setModalVisible(true)
                }}
              >
                创建部门
              </Button>
              <Button icon={<ExportOutlined />}>
                导出数据
              </Button>
              {factories.length === 0 && (
                <Text type="warning">
                  请先创建工厂后再创建部门
                </Text>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 部门列表 */}
      <Card title="部门列表">
        <Table
          columns={columns}
          dataSource={filteredDepartments}
          rowKey={(record) => `${record.id}_${record.department_code}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 创建/编辑部门弹窗 */}
      <Modal
        title={modalType === 'create' ? '创建部门' : '编辑部门'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setSelectedDepartment(null)
        }}
        onOk={modalType === 'create' ? handleCreateDepartment : handleUpdateDepartment}
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
            <Select
              placeholder="请选择所属工厂"
              notFoundContent={
                <div style={{ textAlign: 'center', padding: '10px' }}>
                  <Text type="secondary">暂无可用工厂</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: '12px' }}>请先在工厂管理中创建工厂</Text>
                </div>
              }
            >
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

          <Form.Item
            name="manager_name"
            label="部门负责人"
          >
            <Input placeholder="请输入部门负责人姓名" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 部门详情弹窗 */}
      <Modal
        title="部门详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedDepartment && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={6}>
                <div className="text-center">
                  <Avatar size={80} icon={<BankOutlined />} />
                  <div className="mt-2">
                    <Title level={4}>{selectedDepartment.department_name}</Title>
                    <Tag color="blue">{selectedDepartment.department_code}</Tag>
                  </div>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>员工数量：</Text> {selectedDepartment.employee_count} 人
                  </Col>
                  <Col span={12}>
                    <Text strong>负责人：</Text> {selectedDepartment.manager_name || '未设置'}
                  </Col>
                  <Col span={12}>
                    <Text strong>创建时间：</Text> {dayjs(selectedDepartment.created_at).format('YYYY-MM-DD')}
                  </Col>
                  <Col span={12}>
                    <Text strong>所属工厂：</Text>
                    {(() => {
                      const factory = factories.find(f => f.id === selectedDepartment.factory_id)
                      return factory ? factory.name : '未分配'
                    })()}
                  </Col>
                </Row>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="基本信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>部门编码：</Text>
                      <Tag color="blue" className="ml-2">{selectedDepartment.department_code}</Tag>
                    </div>
                    <div>
                      <Text strong>部门描述：</Text>
                      <Text className="ml-2">{selectedDepartment.description}</Text>
                    </div>
                    <div>
                      <Text strong>员工总数：</Text>
                      <Badge count={selectedDepartment.employee_count} className="ml-2" />
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="管理信息" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>负责人：</Text>
                      <Text className="ml-2">
                        {selectedDepartment.manager_name ? (
                          <Space>
                            <Avatar size="small" icon={<UserOutlined />} />
                            {selectedDepartment.manager_name}
                          </Space>
                        ) : (
                          <Text type="secondary">未设置</Text>
                        )}
                      </Text>
                    </div>
                    <div>
                      <Text strong>所属工厂：</Text>
                      <Text className="ml-2">
                        {(() => {
                          const factory = factories.find(f => f.id === selectedDepartment.factory_id)
                          return factory ? (
                            <Space>
                              <HomeOutlined />
                              {factory.name}
                            </Space>
                          ) : (
                            <Text type="secondary">未分配</Text>
                          )
                        })()}
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Card title="部门设置" size="small" className="mt-4">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <div>
                    <Text strong>部门类型：</Text>
                    <Tag color="blue" className="ml-2">
                      {selectedDepartment.department_code.startsWith('TECH') ? '技术部门' :
                       selectedDepartment.department_code.startsWith('PROD') ? '生产部门' :
                       selectedDepartment.department_code.startsWith('QUAL') ? '质量部门' :
                       '其他部门'}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div>
                    <Text strong>管理状态：</Text>
                    <Badge
                      status={selectedDepartment.manager_name ? 'success' : 'warning'}
                      text={selectedDepartment.manager_name ? '正常管理' : '未设置负责人'}
                      className="ml-2"
                    />
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 员工列表 */}
            <Card title={<><TeamOutlined /> 部门员工列表</>} size="small" className="mt-4">
              {selectedDepartment.employees && selectedDepartment.employees.length > 0 ? (
                <Table
                  dataSource={selectedDepartment.employees}
                  rowKey={(record) => `${record.id}_${record.employee_number}`}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: '员工',
                      dataIndex: 'name',
                      key: 'name',
                      render: (text, record) => (
                        <Space>
                          <Avatar size="small" icon={<UserOutlined />} />
                          <div>
                            <div>{text}</div>
                            <Text type="secondary" style={{ fontSize: 12 }}>{record.email}</Text>
                          </div>
                        </Space>
                      ),
                    },
                    {
                      title: '工号',
                      dataIndex: 'employee_number',
                      key: 'employee_number',
                    },
                    {
                      title: '职位',
                      dataIndex: 'position',
                      key: 'position',
                    },
                    {
                      title: '角色',
                      dataIndex: 'role',
                      key: 'role',
                      render: (role) => (
                        <Tag color={role === 'admin' ? 'red' : role === 'manager' ? 'orange' : 'blue'}>
                          {role === 'admin' ? '管理员' : role === 'manager' ? '经理' : '员工'}
                        </Tag>
                      ),
                    },
                    {
                      title: '入职时间',
                      dataIndex: 'joined_at',
                      key: 'joined_at',
                      render: (text) => dayjs(text).format('YYYY-MM-DD'),
                    },
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Text type="secondary">该部门暂无员工</Text>
                </div>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Departments