/**
 * 审批工作流管理页面
 */
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
  Row,
  Col,
  Divider,
  InputNumber,
  Badge,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ApartmentOutlined,
  UserOutlined,
  TeamOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import approvalApi, { ApprovalWorkflowDefinition, ApprovalWorkflowStep, CreateWorkflowData } from '@/services/approval'
import enterpriseService, { CompanyRole, CompanyEmployee } from '@/services/enterprise'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select

// 文档类型选项
const DOCUMENT_TYPES = [
  { value: 'wps', label: 'WPS - 焊接工艺规程' },
  { value: 'pqr', label: 'PQR - 焊接工艺评定' },
  { value: 'ppqr', label: 'pPQR - 预焊接工艺评定' },
  { value: 'equipment', label: '设备管理' },
  { value: 'material', label: '焊材管理' },
  { value: 'welder', label: '焊工管理' },
  { value: 'product_version', label: '产品图纸版本' },
  { value: 'weld_sequence_version', label: '焊序版本' },
]

// 审批模式选项
const APPROVAL_MODES = [
  { value: 'any', label: '任一审批（任意一人通过即可）' },
  { value: 'all', label: '全部审批（所有人都需通过）' },
  { value: 'sequential', label: '顺序审批（按顺序逐个审批）' },
]

const ApprovalWorkflows: React.FC = () => {
  const [workflows, setWorkflows] = useState<ApprovalWorkflowDefinition[]>([])
  const [roles, setRoles] = useState<CompanyRole[]>([])
  const [employees, setEmployees] = useState<CompanyEmployee[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit'>('create')
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflowDefinition | null>(null)
  const [form] = Form.useForm()

  // 加载工作流列表
  const loadWorkflows = async () => {
    setLoading(true)
    try {
      const response = await approvalApi.getWorkflows()
      console.log('[审批工作流] 加载工作流响应:', response)

      setWorkflows(response.data.items || [])
    } catch (error: any) {
      console.error('[审批工作流] 加载失败:', error)
      message.error(error.response?.data?.detail || '加载工作流列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await enterpriseService.getRoles()
      if (response.data.success) {
        // 只显示有审批权限的角色
        const rolesWithApproval = response.data.data.items.filter((role: CompanyRole) => {
          const permissions = role.permissions as any
          return permissions.wps_management?.approve ||
                 permissions.pqr_management?.approve ||
                 permissions.ppqr_management?.approve
        })
        setRoles(rolesWithApproval)
      }
    } catch (error: any) {
      console.error('加载角色列表失败:', error)
    }
  }

  // 加载员工列表
  const loadEmployees = async () => {
    try {
      const response = await enterpriseService.getEmployees({ status: 'active' })
      if (response.data.success) {
        setEmployees(response.data.data.items || [])
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载角色列表失败')
    }
  }

  useEffect(() => {
    // 打印当前工作区信息
    const currentWorkspace = localStorage.getItem('current_workspace')
    if (currentWorkspace) {
      try {
        const workspace = JSON.parse(currentWorkspace)
        console.log('[审批工作流] 当前工作区:', workspace)
      } catch (error) {
        console.error('[审批工作流] 解析工作区信息失败:', error)
      }
    } else {
      console.warn('[审批工作流] 未找到工作区信息')
    }

    loadWorkflows()
    loadRoles()
    loadEmployees()
  }, [])

  // 打开创建/编辑模态框
  const handleOpenModal = (type: 'create' | 'edit', workflow?: ApprovalWorkflowDefinition) => {
    setModalType(type)
    setSelectedWorkflow(workflow || null)

    if (type === 'edit' && workflow) {
      form.setFieldsValue({
        name: workflow.name,
        code: workflow.code,
        description: workflow.description,
        document_type: workflow.document_type,
        steps: workflow.steps,
        is_active: workflow.is_active,
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        is_active: true,
        steps: [{
          step_number: 1,
          step_name: '',
          approver_type: 'role',
          approver_ids: [],
          approval_mode: 'any',
          time_limit_hours: 48,
        }],
      })
    }

    setModalVisible(true)
  }

  // 保存工作流
  const handleSaveWorkflow = async () => {
    try {
      const values = await form.validateFields()

      console.log('[审批工作流] 表单数据:', values)

      // 确保步骤编号连续
      const steps = values.steps.map((step: any, index: number) => ({
        ...step,
        step_number: index + 1,
      }))

      const data: CreateWorkflowData = {
        name: values.name,
        code: values.code,
        description: values.description,
        document_type: values.document_type,
        steps,
        is_active: values.is_active,
      }

      console.log('[审批工作流] 提交数据:', data)

      if (modalType === 'create') {
        const response = await approvalApi.createWorkflow(data)
        console.log('[审批工作流] 创建响应:', response)
        message.success('工作流创建成功')
      } else if (selectedWorkflow) {
        const response = await approvalApi.updateWorkflow(selectedWorkflow.id, data)
        console.log('[审批工作流] 更新响应:', response)
        message.success('工作流更新成功')
      }

      setModalVisible(false)
      form.resetFields()
      loadWorkflows()
    } catch (error: any) {
      console.error('[审批工作流] 保存失败:', error)
      console.error('[审批工作流] 错误详情:', error.response)

      if (error.errorFields) {
        message.error('请填写完整的表单信息')
      } else {
        const errorMsg = error.response?.data?.detail || '保存工作流失败'
        message.error(errorMsg)
        console.error('[审批工作流] 错误消息:', errorMsg)
      }
    }
  }

  // 删除工作流
  const handleDeleteWorkflow = async (id: number) => {
    try {
      console.log('[审批工作流] 删除工作流:', id)
      const response = await approvalApi.deleteWorkflow(id)
      console.log('[审批工作流] 删除响应:', response)
      message.success('工作流删除成功')
      loadWorkflows()
    } catch (error: any) {
      console.error('[审批工作流] 删除失败:', error)
      console.error('[审批工作流] 错误详情:', error.response)
      message.error(error.response?.data?.detail || '删除工作流失败')
    }
  }

  // 切换工作流状态
  const handleToggleWorkflow = async (id: number, is_active: boolean) => {
    try {
      console.log('[审批工作流] 切换状态:', id, is_active)
      const response = await approvalApi.toggleWorkflowStatus(id, is_active)
      console.log('[审批工作流] 切换响应:', response)
      message.success(is_active ? '工作流已启用' : '工作流已停用')
      loadWorkflows()
    } catch (error: any) {
      console.error('[审批工作流] 切换失败:', error)
      console.error('[审批工作流] 错误详情:', error.response)
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  // 设置为默认工作流
  const handleSetDefault = async (id: number, record: any) => {
    Modal.confirm({
      title: '设置为默认工作流',
      content: `确定要将"${record.name}"设置为默认工作流吗？设置后，同一文档类型的其他工作流将被自动禁用。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          console.log('[审批工作流] 设置默认:', id)
          const response = await approvalApi.setDefaultWorkflow(id)
          console.log('[审批工作流] 设置响应:', response)
          message.success('已设置为默认工作流，其他工作流已自动禁用')
          loadWorkflows()
        } catch (error: any) {
          console.error('[审批工作流] 设置失败:', error)
          console.error('[审批工作流] 错误详情:', error.response)
          message.error(error.response?.data?.detail || '设置失败')
        }
      }
    })
  }

  // 表格列定义
  const columns: ColumnsType<ApprovalWorkflowDefinition> = [
    {
      title: '工作流名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.code}
          </Text>
        </Space>
      ),
    },
    {
      title: '文档类型',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 150,
      render: (type) => {
        const docType = DOCUMENT_TYPES.find(t => t.value === type)
        return <Tag color="blue">{docType?.label || type}</Tag>
      },
    },
    {
      title: '审批步骤',
      dataIndex: 'steps',
      key: 'steps',
      width: 100,
      align: 'center',
      render: (steps: ApprovalWorkflowStep[]) => (
        <Badge count={steps?.length || 0} showZero color="purple" />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center',
      render: (is_active) => (
        <Tag color={is_active ? 'success' : 'default'} icon={is_active ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {is_active ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'is_default',
      key: 'is_default',
      width: 120,
      align: 'center',
      render: (is_default, record) => (
        <Space>
          {is_default ? (
            <Tag color="orange" icon={<StarFilled />}>默认</Tag>
          ) : (
            <Tag color="blue">自定义</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 240,
      fixed: 'right',
      render: (_, record) => (
        <Space wrap size={0}>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedWorkflow(record)
                setDetailModalVisible(true)
              }}
            />
          </Tooltip>

          {/* 系统默认工作流:只能查看 */}
          {record.company_id === null ? (
            <Tooltip title="系统默认工作流不可修改,请创建企业自定义工作流来覆盖">
              <Tag color="orange" icon={<StarFilled />}>系统默认</Tag>
            </Tooltip>
          ) : (
            /* 企业自定义工作流:可以编辑、设置默认、启用/停用、删除 */
            <>
              {!record.is_default && (
                <Tooltip title="设置为默认">
                  <Button
                    type="text"
                    size="small"
                    icon={<StarOutlined />}
                    onClick={() => handleSetDefault(record.id, record)}
                  />
                </Tooltip>
              )}

              <Tooltip title="编辑">
                <Button
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => handleOpenModal('edit', record)}
                />
              </Tooltip>

              <Tooltip title={record.is_active ? '停用' : '启用'}>
                <Switch
                  size="small"
                  checked={record.is_active}
                  onChange={(checked) => handleToggleWorkflow(record.id, checked)}
                />
              </Tooltip>

              {!record.is_default && (
                <Tooltip title="删除">
                  <Popconfirm
                    title="确定要删除这个工作流吗？"
                    onConfirm={() => handleDeleteWorkflow(record.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    />
                  </Popconfirm>
                </Tooltip>
              )}
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="list-page">
      <ListPageHeader
        title="审批流程"
        description="配置文档审批工作流与步骤"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal('create')}
          >
            创建工作流
          </Button>
        }
      />

      <Card className="list-page-card">
        <div className="list-table-wrap">
          <Table
            columns={columns}
            dataSource={workflows}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1100 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        </div>
      </Card>

      {/* 创建/编辑工作流模态框 */}
      <Modal
        title={modalType === 'create' ? '创建审批工作流' : '编辑审批工作流'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleSaveWorkflow}
        width={900}
        okText="保存"
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
                label="工作流名称"
                rules={[{ required: true, message: '请输入工作流名称' }]}
              >
                <Input placeholder="例如：WPS标准审批流程" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="code"
                label="工作流代码"
                rules={[{ required: true, message: '请输入工作流代码' }]}
              >
                <Input placeholder="例如：WPS_STANDARD" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="document_type"
                label="文档类型"
                rules={[{ required: true, message: '请选择文档类型' }]}
              >
                <Select placeholder="请选择文档类型">
                  {DOCUMENT_TYPES.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="状态"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="停用" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="请输入工作流描述" />
          </Form.Item>

          <Divider>审批步骤配置</Divider>

          <Form.List name="steps">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field, index) => {
                  const { key, ...restField } = field
                  return (
                    <Card
                      key={key}
                      size="small"
                      title={`步骤 ${index + 1}`}
                      extra={
                        fields.length > 1 && (
                          <Button
                            type="text"
                            danger
                            size="small"
                            onClick={() => remove(field.name)}
                          >
                            删除
                          </Button>
                        )
                      }
                      style={{ marginBottom: 16 }}
                    >
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            {...restField}
                            name={[field.name, 'step_name']}
                            label="步骤名称"
                            rules={[{ required: true, message: '请输入步骤名称' }]}
                          >
                            <Input placeholder="例如：部门经理审批" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            {...restField}
                            name={[field.name, 'approver_type']}
                            label="审批人类型"
                            rules={[{ required: true, message: '请选择审批人类型' }]}
                          >
                            <Select placeholder="请选择审批人类型">
                              <Option value="role">
                                <TeamOutlined /> 角色
                              </Option>
                              <Option value="user">
                                <UserOutlined /> 指定用户
                              </Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            noStyle
                            shouldUpdate={(prevValues, currentValues) => {
                              const prevType = prevValues.steps?.[field.name]?.approver_type
                              const currType = currentValues.steps?.[field.name]?.approver_type
                              return prevType !== currType
                            }}
                          >
                            {({ getFieldValue }) => {
                              const approverType = getFieldValue(['steps', field.name, 'approver_type'])
                              return (
                                <Form.Item
                                  {...restField}
                                  name={[field.name, 'approver_ids']}
                                  label="审批人"
                                  rules={[{ required: true, message: '请选择审批人' }]}
                                >
                                  <Select
                                    mode="multiple"
                                    placeholder={approverType === 'user' ? '请选择用户' : '请选择审批角色'}
                                    showSearch
                                    filterOption={(input, option) =>
                                      String(option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                                    }
                                  >
                                    {approverType === 'user' ? (
                                      employees.map(emp => (
                                        <Option key={emp.user_id} value={parseInt(emp.user_id)}>
                                          {emp.name || emp.email || `用户${emp.user_id}`}
                                        </Option>
                                      ))
                                    ) : (
                                      roles.map(role => (
                                        <Option key={role.id} value={parseInt(role.id)}>
                                          {role.name}
                                        </Option>
                                      ))
                                    )}
                                  </Select>
                                </Form.Item>
                              )
                            }}
                          </Form.Item>
                        </Col>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[field.name, 'approval_mode']}
                          label="审批模式"
                          rules={[{ required: true, message: '请选择审批模式' }]}
                        >
                          <Select placeholder="请选择审批模式">
                            {APPROVAL_MODES.map(mode => (
                              <Option key={mode.value} value={mode.value}>
                                {mode.label}
                              </Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>

                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[field.name, 'time_limit_hours']}
                          label="时限（小时）"
                        >
                          <InputNumber
                            min={1}
                            max={720}
                            placeholder="48"
                            style={{ width: '100%' }}
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[field.name, 'description']}
                          label="步骤说明"
                        >
                          <Input placeholder="可选" />
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                )
              })}

                <Button
                  type="dashed"
                  onClick={() => add({
                    step_number: fields.length + 1,
                    step_name: '',
                    approver_type: 'role',
                    approver_ids: [],
                    approval_mode: 'any',
                    time_limit_hours: 48,
                  })}
                  block
                  icon={<PlusOutlined />}
                >
                  添加审批步骤
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* 工作流详情模态框 */}
      <Modal
        title="工作流详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedWorkflow && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text type="secondary">工作流名称：</Text>
                <Text strong>{selectedWorkflow.name}</Text>
              </Col>
              <Col span={12}>
                <Text type="secondary">工作流代码：</Text>
                <Text strong>{selectedWorkflow.code}</Text>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text type="secondary">文档类型：</Text>
                <Tag color="blue">
                  {DOCUMENT_TYPES.find(t => t.value === selectedWorkflow.document_type)?.label}
                </Tag>
              </Col>
              <Col span={12}>
                <Text type="secondary">状态：</Text>
                <Tag color={selectedWorkflow.is_active ? 'success' : 'default'}>
                  {selectedWorkflow.is_active ? '启用' : '停用'}
                </Tag>
              </Col>
            </Row>

            {selectedWorkflow.description && (
              <Row style={{ marginBottom: 16 }}>
                <Col span={24}>
                  <Text type="secondary">描述：</Text>
                  <div>{selectedWorkflow.description}</div>
                </Col>
              </Row>
            )}

            <Divider>审批步骤</Divider>

            {selectedWorkflow.steps?.map((step, index) => (
              <Card key={index} size="small" style={{ marginBottom: 8 }}>
                <Row gutter={16}>
                  <Col span={24}>
                    <Text strong>步骤 {step.step_number}：{step.step_name}</Text>
                  </Col>
                </Row>
                <Row gutter={16} style={{ marginTop: 8 }}>
                  <Col span={8}>
                    <Text type="secondary">审批人类型：</Text>
                    <Tag>{step.approver_type === 'role' ? '角色' : '用户'}</Tag>
                  </Col>
                  <Col span={8}>
                    <Text type="secondary">审批模式：</Text>
                    <Tag color="blue">
                      {APPROVAL_MODES.find(m => m.value === step.approval_mode)?.label}
                    </Tag>
                  </Col>
                  <Col span={8}>
                    <Text type="secondary">时限：</Text>
                    <Text>{step.time_limit_hours || '-'} 小时</Text>
                  </Col>
                </Row>
                {step.description && (
                  <Row style={{ marginTop: 8 }}>
                    <Col span={24}>
                      <Text type="secondary">说明：</Text>
                      <Text>{step.description}</Text>
                    </Col>
                  </Row>
                )}
              </Card>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ApprovalWorkflows

