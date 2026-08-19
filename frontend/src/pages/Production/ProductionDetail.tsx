import React, { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Descriptions,
  Row,
  Col,
  Divider,
  Tabs,
  Table,
  Progress,
  Avatar,
  Modal,
  message,
  Alert,
  Spin,
  Form,
  DatePicker,
  Input,
  InputNumber,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  getProductionTaskById,
  updateProductionTaskStatus,
  deleteProductionTask,
  getProductionRecords,
  createProductionRecord,
  type ProductionTask as APIProductionTask,
  type ProductionRecord,
} from '@/services/production'
import workspaceService from '@/services/workspace'

const { Title, Text } = Typography
const { TextArea } = Input

const STATUS_MAP: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
  pending: { color: 'default', text: '待开始', icon: <ClockCircleOutlined /> },
  in_progress: { color: 'processing', text: '进行中', icon: <PlayCircleOutlined /> },
  paused: { color: 'warning', text: '已暂停', icon: <PauseCircleOutlined /> },
  completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
  cancelled: { color: 'error', text: '已取消', icon: <ExclamationCircleOutlined /> },
  failed: { color: 'error', text: '失败', icon: <ExclamationCircleOutlined /> },
}

const PRIORITY_MAP: Record<string, { color: string; text: string }> = {
  low: { color: 'default', text: '低' },
  normal: { color: 'blue', text: '普通' },
  high: { color: 'orange', text: '高' },
  urgent: { color: 'red', text: '紧急' },
}

const formatDate = (value?: string | null) => (value ? dayjs(value).format('YYYY-MM-DD') : '-')

const ProductionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')
  const [loading, setLoading] = useState(false)
  const [taskData, setTaskData] = useState<APIProductionTask | null>(null)
  const [records, setRecords] = useState<ProductionRecord[]>([])
  const [logOpen, setLogOpen] = useState(false)
  const [form] = Form.useForm()

  const workspace = workspaceService.getCurrentWorkspaceFromStorage()
  const workspaceType = workspace?.type || 'personal'
  const companyId = workspace?.company_id
  const factoryId = workspace?.factory_id
  const taskId = Number(id)

  const loadDetail = useCallback(async () => {
    if (!taskId) return
    setLoading(true)
    try {
      const [taskResp, recordResp] = await Promise.all([
        getProductionTaskById(taskId, workspaceType, companyId, factoryId),
        getProductionRecords(taskId, workspaceType, companyId, factoryId),
      ])
      setTaskData(taskResp.data)
      setRecords(recordResp.data?.items || [])
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [taskId, workspaceType, companyId, factoryId])

  useEffect(() => {
    loadDetail()
  }, [loadDetail])

  const handleDelete = () => {
    Modal.confirm({
      title: '确定要删除这个生产任务吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      async onOk() {
        await deleteProductionTask(taskId, workspaceType, companyId, factoryId)
        navigate('/production')
      },
    })
  }

  const handleStatus = async (status: string) => {
    await updateProductionTaskStatus(taskId, status, workspaceType, companyId, factoryId)
    await loadDetail()
  }

  const handleAddLog = async () => {
    const values = await form.validateFields()
    await createProductionRecord(
      taskId,
      {
        record_date: values.record_date.format('YYYY-MM-DD'),
        work_description: values.work_description,
        duration_hours: values.duration_hours,
        weld_length: values.weld_length,
        notes: values.notes,
      },
      workspaceType,
      companyId,
      factoryId
    )
    setLogOpen(false)
    form.resetFields()
    await loadDetail()
  }

  const workLogColumns = [
    {
      title: '日期',
      dataIndex: 'record_date',
      key: 'record_date',
      render: (value: string) => formatDate(value),
    },
    {
      title: '工时(h)',
      dataIndex: 'duration_hours',
      key: 'duration_hours',
      render: (value?: number) => value ?? '-',
    },
    {
      title: '工作内容',
      dataIndex: 'work_description',
      key: 'work_description',
      ellipsis: true,
    },
    {
      title: '焊缝长度(m)',
      dataIndex: 'weld_length',
      key: 'weld_length',
      render: (value?: number) => value ?? '-',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
  ]

  if (!taskData) {
    return (
      <div className="page-container">
        <Spin spinning={loading}>
          <Card>未找到生产任务</Card>
        </Spin>
      </div>
    )
  }

  const taskStatus = STATUS_MAP[taskData.status] || STATUS_MAP.pending
  const priority = PRIORITY_MAP[taskData.priority] || PRIORITY_MAP.normal
  const startDate = taskData.planned_start_date || taskData.actual_start_date
  const endDate = taskData.planned_end_date || taskData.actual_end_date
  const remainingDays = endDate ? dayjs(endDate).diff(dayjs(), 'days') : null

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/production')}>
            返回列表
          </Button>
          <Title level={2}>生产任务详情</Title>
        </Space>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={[
                  {
                    key: 'info',
                    label: '任务信息',
                    children: (
                      <Descriptions bordered column={2}>
                        <Descriptions.Item label="任务编号">{taskData.task_number}</Descriptions.Item>
                        <Descriptions.Item label="任务名称">{taskData.task_name}</Descriptions.Item>
                        <Descriptions.Item label="状态">
                          <Tag color={taskStatus.color} icon={taskStatus.icon}>
                            {taskStatus.text}
                          </Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="优先级">
                          <Tag color={priority.color}>{priority.text}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="计划开始">{formatDate(startDate)}</Descriptions.Item>
                        <Descriptions.Item label="计划结束">{formatDate(endDate)}</Descriptions.Item>
                        <Descriptions.Item label="进度" span={2}>
                          <Progress percent={taskData.progress_percentage || 0} />
                        </Descriptions.Item>
                        <Descriptions.Item label="备注" span={2}>
                          {taskData.notes || '-'}
                        </Descriptions.Item>
                      </Descriptions>
                    ),
                  },
                  {
                    key: 'logs',
                    label: '工作日志',
                    children: (
                      <Table
                        dataSource={records}
                        columns={workLogColumns}
                        rowKey="id"
                        pagination={false}
                      />
                    ),
                  },
                ]}
              />
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="任务状态">
              <div className="text-center p-4">
                <Avatar size={64} icon={<PlayCircleOutlined />} className="mb-3" />
                <Title level={4}>{taskData.task_name}</Title>
                <Tag color={taskStatus.color} icon={taskStatus.icon}>
                  {taskStatus.text}
                </Tag>
                <Divider />
                <Progress type="circle" percent={taskData.progress_percentage || 0} width={80} />
              </div>
            </Card>

            <Card title="时间信息" className="mt-6">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>开始日期:</Text>
                  <Text>{formatDate(startDate)}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>结束日期:</Text>
                  <Text>{formatDate(endDate)}</Text>
                </div>
                {remainingDays !== null && (
                  <div className="flex justify-between">
                    <Text>剩余天数:</Text>
                    <Text>{remainingDays}天</Text>
                  </div>
                )}
              </Space>
            </Card>

            <Card title="操作" className="mt-6">
              <Space direction="vertical" className="w-full">
                <Button type="primary" icon={<EditOutlined />} block onClick={() => navigate(`/production/${id}/edit`)}>
                  编辑任务
                </Button>
                {taskData.status === 'pending' && (
                  <Button type="primary" icon={<PlayCircleOutlined />} block onClick={() => handleStatus('in_progress')}>
                    开始任务
                  </Button>
                )}
                {taskData.status === 'in_progress' && (
                  <Button icon={<PauseCircleOutlined />} block onClick={() => handleStatus('paused')}>
                    暂停任务
                  </Button>
                )}
                {taskData.status === 'paused' && (
                  <Button icon={<PlayCircleOutlined />} block onClick={() => handleStatus('in_progress')}>
                    继续任务
                  </Button>
                )}
                {taskData.status === 'in_progress' && (
                  <Button type="primary" icon={<CheckCircleOutlined />} block onClick={() => handleStatus('completed')}>
                    完成任务
                  </Button>
                )}
                <Button icon={<PlusOutlined />} block onClick={() => setLogOpen(true)}>
                  添加工作日志
                </Button>
                <Button icon={<DeleteOutlined />} block danger onClick={handleDelete}>
                  删除任务
                </Button>
              </Space>
            </Card>

            {remainingDays !== null && remainingDays <= 2 && taskData.status !== 'completed' && (
              <Alert
                message="任务即将到期"
                description={`任务计划结束日期为 ${formatDate(endDate)}，请加快进度`}
                type="warning"
                showIcon
                className="mt-6"
              />
            )}
          </Col>
        </Row>
      </Spin>

      <Modal
        title="添加工作日志"
        open={logOpen}
        onCancel={() => setLogOpen(false)}
        onOk={handleAddLog}
        okText="保存"
      >
        <Form form={form} layout="vertical" initialValues={{ record_date: dayjs() }}>
          <Form.Item name="record_date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="work_description" label="工作内容" rules={[{ required: true, message: '请填写工作内容' }]}>
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="duration_hours" label="工时(h)">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="weld_length" label="焊缝长度(m)">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProductionDetail
