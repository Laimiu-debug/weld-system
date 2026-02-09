import React, { useState } from 'react'
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
  Timeline,
  Badge,
  Progress,
  Statistic,
  Avatar,
  Tooltip,
  Modal,
  message,
  Alert,
  Steps,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DownloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CalendarOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { ProductionTask, TaskStatus, TaskPriority } from '@/types'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

const ProductionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')

  // 模拟获取生产任务详情数据
  const taskData: ProductionTask = {
    id: id || '1',
    user_id: 'user1',
    task_number: 'TSK-2024-001',
    task_name: '压力容器筒体焊接',
    wps_id: '1',
    start_date: '2024-01-15',
    end_date: '2024-01-20',
    status: 'in_progress',
    priority: 'high',
    assigned_welder_id: '1',
    assigned_equipment_id: '1',
    progress_percentage: 60,
    notes: '重点监控项目',
    created_at: '2024-01-10T10:30:00Z',
    updated_at: '2024-01-15T14:20:00Z',
  }

  // 模拟任务步骤
  const taskSteps = [
    {
      title: '准备阶段',
      description: '准备焊材、设备和工艺文件',
      status: 'finish',
      date: '2024-01-15',
    },
    {
      title: '焊接阶段',
      description: '按照WPS进行焊接作业',
      status: 'process',
      date: '2024-01-16',
    },
    {
      title: '检验阶段',
      description: '进行焊缝检验',
      status: 'wait',
      date: '2024-01-19',
    },
    {
      title: '完成阶段',
      description: '整理资料，交付验收',
      status: 'wait',
      date: '2024-01-20',
    },
  ]

  // 模拟工作日志
  const workLogs = [
    {
      id: '1',
      date: '2024-01-16',
      startTime: '08:30',
      endTime: '17:30',
      workContent: '完成筒体环缝焊接，焊接长度5米',
      progress: 20,
      operator: '张三',
      notes: '焊接质量良好，无缺陷',
    },
    {
      id: '2',
      date: '2024-01-15',
      startTime: '09:00',
      endTime: '12:00',
      workContent: '准备焊接设备，调试参数',
      progress: 10,
      operator: '张三',
      notes: '设备运行正常',
    },
  ]

  // 模拟质量检验记录
  const qualityRecords = [
    {
      id: '1',
      date: '2024-01-16',
      type: '外观检验',
      result: '合格',
      inspector: '李检验员',
      notes: '焊缝成型良好，无表面缺陷',
    },
    {
      id: '2',
      date: '2024-01-15',
      type: '工艺参数检查',
      result: '合格',
      inspector: '王检验员',
      notes: '焊接参数符合WPS要求',
    },
  ]

  // 获取任务状态显示名称
  const getTaskStatusName = (status: TaskStatus) => {
    const statusNames: Record<TaskStatus, { color: string; text: string; icon: React.ReactNode }> = {
      'pending': { color: 'default', text: '待开始', icon: <ClockCircleOutlined /> },
      'in_progress': { color: 'processing', text: '进行中', icon: <PlayCircleOutlined /> },
      'completed': { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      'cancelled': { color: 'error', text: '已取消', icon: <ExclamationCircleOutlined /> },
    }
    return statusNames[status] || statusNames['pending']
  }

  // 获取优先级显示名称
  const getPriorityName = (priority: TaskPriority) => {
    const priorityNames: Record<TaskPriority, { color: string; text: string }> = {
      'low': { color: 'default', text: '低' },
      'normal': { color: 'blue', text: '普通' },
      'high': { color: 'orange', text: '高' },
      'urgent': { color: 'red', text: '紧急' },
    }
    return priorityNames[priority] || priorityNames['normal']
  }

  // 处理编辑
  const handleEdit = () => {
    navigate(`/production/${id}/edit`)
  }

  // 处理删除
  const handleDelete = () => {
    Modal.confirm({
      title: '确定要删除这个生产任务吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      onOk() {
        message.success('删除成功')
        navigate('/production')
      },
    })
  }

  // 处理开始任务
  const handleStartTask = () => {
    message.success('任务已开始')
  }

  // 处理暂停任务
  const handlePauseTask = () => {
    message.success('任务已暂停')
  }

  // 处理完成任务
  const handleCompleteTask = () => {
    Modal.confirm({
      title: '确定要完成这个任务吗？',
      icon: <CheckCircleOutlined />,
      content: '完成后将无法修改',
      okText: '确定',
      cancelText: '取消',
      onOk() {
        message.success('任务已完成')
        navigate('/production')
      },
    })
  }

  // 工作日志表格列
  const workLogColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '工作时间',
      key: 'workTime',
      render: (_: any, record: any) => `${record.startTime} - ${record.endTime}`,
    },
    {
      title: '工作内容',
      dataIndex: 'workContent',
      key: 'workContent',
      ellipsis: true,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => `${progress}%`,
    },
    {
      title: '操作员',
      dataIndex: 'operator',
      key: 'operator',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
  ]

  // 质量检验记录表格列
  const qualityColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '检验类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      ),
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => (
        <Tag color={result === '合格' ? 'success' : 'error'}>
          {result}
        </Tag>
      ),
    },
    {
      title: '检验员',
      dataIndex: 'inspector',
      key: 'inspector',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
  ]

  const taskStatus = getTaskStatusName(taskData.status)
  const priority = getPriorityName(taskData.priority)

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/production')}
          >
            返回列表
          </Button>
          <Title level={2}>生产任务详情</Title>
        </Space>
      </div>

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
                      <Descriptions.Item label="任务编号">
                        {taskData.task_number}
                      </Descriptions.Item>
                      <Descriptions.Item label="任务名称">
                        {taskData.task_name}
                      </Descriptions.Item>
                      <Descriptions.Item label="状态">
                        <Tag color={taskStatus.color} icon={taskStatus.icon}>
                          {taskStatus.text}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="优先级">
                        <Tag color={priority.color}>
                          {priority.text}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="开始日期">
                        {dayjs(taskData.start_date).format('YYYY-MM-DD')}
                      </Descriptions.Item>
                      <Descriptions.Item label="结束日期">
                        {dayjs(taskData.end_date).format('YYYY-MM-DD')}
                      </Descriptions.Item>
                      <Descriptions.Item label="指定焊工">
                        张三 (WLD-2024-001)
                      </Descriptions.Item>
                      <Descriptions.Item label="使用设备">
                        数字化逆变焊机 (EQP-2024-001)
                      </Descriptions.Item>
                      <Descriptions.Item label="进度" span={2}>
                        <Progress percent={taskData.progress_percentage} status="active" />
                      </Descriptions.Item>
                      <Descriptions.Item label="备注" span={2}>
                        {taskData.notes}
                      </Descriptions.Item>
                    </Descriptions>
                  )
                },
                {
                  key: 'steps',
                  label: '任务步骤',
                  children: (
                    <Steps current={1} direction="vertical" size="small">
                      {taskSteps.map((step, index) => (
                        <Step
                          key={index}
                          title={step.title}
                          description={
                            <div>
                              <p>{step.description}</p>
                              <Text type="secondary">{step.date}</Text>
                            </div>
                          }
                          status={step.status === 'finish' ? 'finish' : step.status === 'process' ? 'process' : 'wait'}
                        />
                      ))}
                    </Steps>
                  )
                },
                {
                  key: 'logs',
                  label: '工作日志',
                  children: (
                    <Table
                      dataSource={workLogs}
                      columns={workLogColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                },
                {
                  key: 'quality',
                  label: '质量检验',
                  children: (
                    <Table
                      dataSource={qualityRecords}
                      columns={qualityColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                }
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="任务状态">
            <div className="text-center p-4">
              <div className="mb-4">
                <Avatar size={64} icon={<PlayCircleOutlined />} className="mb-3" />
                <Title level={4}>{taskData.task_name}</Title>
                <Tag color={taskStatus.color} icon={taskStatus.icon}>
                  {taskStatus.text}
                </Tag>
              </div>
              <Divider />
              <div className="mb-4">
                <Text>任务编号: {taskData.task_number}</Text>
              </div>
              <div className="mb-4">
                <Text>优先级: </Text>
                <Tag color={priority.color}>
                  {priority.text}
                </Tag>
              </div>
              <div className="mt-4">
                <Progress
                  type="circle"
                  percent={taskData.progress_percentage}
                  width={80}
                />
              </div>
            </div>
          </Card>

          <Card title="时间信息" className="mt-6">
            <div className="p-4">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>开始日期:</Text>
                  <Text>{dayjs(taskData.start_date).format('YYYY-MM-DD')}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>结束日期:</Text>
                  <Text>{dayjs(taskData.end_date).format('YYYY-MM-DD')}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>剩余天数:</Text>
                  <Text>{dayjs(taskData.end_date).diff(dayjs(), 'days')}天</Text>
                </div>
              </Space>
            </div>
          </Card>

          <Card title="操作" className="mt-6">
            <Space direction="vertical" className="w-full">
              <Button
                type="primary"
                icon={<EditOutlined />}
                block
                onClick={handleEdit}
              >
                编辑任务
              </Button>
              {taskData.status === 'pending' && (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  block
                  onClick={handleStartTask}
                >
                  开始任务
                </Button>
              )}
              {taskData.status === 'in_progress' && (
                <Button
                  icon={<PauseCircleOutlined />}
                  block
                  onClick={handlePauseTask}
                >
                  暂停任务
                </Button>
              )}
              {taskData.status === 'in_progress' && (
                <Button
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  block
                  onClick={handleCompleteTask}
                >
                  完成任务
                </Button>
              )}
              <Button
                icon={<PlusOutlined />}
                block
              >
                添加工作日志
              </Button>
              <Button
                icon={<DownloadOutlined />}
                block
              >
                导出信息
              </Button>
              <Button
                icon={<DeleteOutlined />}
                block
                danger
                onClick={handleDelete}
              >
                删除任务
              </Button>
            </Space>
          </Card>

          {dayjs(taskData.end_date).diff(dayjs(), 'days') <= 2 && taskData.status !== 'completed' && (
            <Alert
              message="任务即将到期"
              description={`任务计划结束日期为 ${dayjs(taskData.end_date).format('YYYY-MM-DD')}，请加快进度`}
              type="warning"
              showIcon
              className="mt-6"
            />
          )}
        </Col>
      </Row>
    </div>
  )
}

export default ProductionDetail