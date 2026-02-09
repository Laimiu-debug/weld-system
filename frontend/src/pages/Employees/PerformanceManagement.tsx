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
  Rate,
  message,
  Typography,
  Statistic,
  Progress,
  Tabs,
  DatePicker,
  InputNumber,
  Divider,
  Alert,
} from 'antd'
import {
  TrophyOutlined,
  StarOutlined,
  FireOutlined,
  ThunderboltOutlined,
  UserOutlined,
  CalendarOutlined,
  BarChartOutlined,
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input

interface PerformanceRecord {
  id: string
  employeeId: string
  employeeName: string
  department: string
  position: string
  reviewPeriod: string
  overallScore: number
  technicalSkills: number
  qualityWork: number
  productivity: number
  teamwork: number
  innovation: number
  safety: number
  attendance: number
  goals: Goal[]
  achievements: Achievement[]
  areasForImprovement: string[]
  reviewerComments: string
  employeeComments: string
  status: 'draft' | 'submitted' | 'reviewed' | 'approved'
  createdAt: string
  reviewedAt?: string
  reviewedBy?: string
}

interface Goal {
  id: string
  title: string
  description: string
  target: string
  progress: number
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  dueDate: string
}

interface Achievement {
  id: string
  title: string
  description: string
  date: string
  impact: 'low' | 'medium' | 'high'
}

const PerformanceManagement: React.FC = () => {
  const [performances, setPerformances] = useState<PerformanceRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedPerformance, setSelectedPerformance] = useState<PerformanceRecord | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('overview')
  const [filterDepartment, setFilterDepartment] = useState<string>('')
  const [filterPeriod, setFilterPeriod] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')

  // 模拟数据
  useEffect(() => {
    const mockData: PerformanceRecord[] = [
      {
        id: '1',
        employeeId: 'EMP001',
        employeeName: '张三',
        department: '技术部',
        position: '焊接工程师',
        reviewPeriod: '2024-Q1',
        overallScore: 92,
        technicalSkills: 95,
        qualityWork: 90,
        productivity: 88,
        teamwork: 92,
        innovation: 85,
        safety: 95,
        attendance: 98,
        goals: [
          {
            id: '1',
            title: '提升焊接技能',
            description: '参加高级焊接培训课程',
            target: '获得IWE认证',
            progress: 100,
            status: 'completed',
            dueDate: '2024-03-31',
          },
          {
            id: '2',
            title: '优化焊接工艺',
            description: '减少焊接缺陷率10%',
            target: '缺陷率 < 2%',
            progress: 80,
            status: 'in_progress',
            dueDate: '2024-06-30',
          },
        ],
        achievements: [
          {
            id: '1',
            title: '优秀项目奖',
            description: '在XX项目中表现优异，提前完成项目交付',
            date: '2024-03-15',
            impact: 'high',
          },
        ],
        areasForImprovement: [
          '提升创新思维能力',
          '加强新技术学习',
        ],
        reviewerComments: '张三在本季度表现优秀，技术能力强，工作质量高，建议继续发扬。',
        employeeComments: '感谢公司认可，会继续努力提升自己的技能。',
        status: 'approved',
        createdAt: '2024-04-01T10:00:00Z',
        reviewedAt: '2024-04-05T14:30:00Z',
        reviewedBy: '李经理',
      },
      {
        id: '2',
        employeeId: 'EMP002',
        employeeName: '李四',
        department: '质量部',
        position: '质量检验员',
        reviewPeriod: '2024-Q1',
        overallScore: 88,
        technicalSkills: 90,
        qualityWork: 92,
        productivity: 85,
        teamwork: 88,
        innovation: 78,
        safety: 90,
        attendance: 95,
        goals: [
          {
            id: '3',
            title: '提升检验技能',
            description: '学习新的无损检测技术',
            target: '获得NDT高级认证',
            progress: 60,
            status: 'in_progress',
            dueDate: '2024-06-30',
          },
        ],
        achievements: [
          {
            id: '2',
            title: '零缺陷记录',
            description: '连续3个月检验工作零缺陷',
            date: '2024-03-31',
            impact: 'medium',
          },
        ],
        areasForImprovement: [
          '提高工作效率',
          '加强团队协作',
        ],
        reviewerComments: '李四工作认真负责，质量意识强，建议提高工作效率。',
        employeeComments: '会注意改进工作方法，提高效率。',
        status: 'approved',
        createdAt: '2024-04-01T11:00:00Z',
        reviewedAt: '2024-04-04T16:20:00Z',
        reviewedBy: '王主管',
      },
      {
        id: '3',
        employeeId: 'EMP003',
        employeeName: '王五',
        department: '生产部',
        position: '生产主管',
        reviewPeriod: '2024-Q1',
        overallScore: 95,
        technicalSkills: 92,
        qualityWork: 95,
        productivity: 98,
        teamwork: 96,
        innovation: 88,
        safety: 92,
        attendance: 100,
        goals: [
          {
            id: '4',
            title: '提升生产效率',
            description: '优化生产流程，提高产出',
            target: '产能提升15%',
            progress: 90,
            status: 'in_progress',
            dueDate: '2024-03-31',
          },
        ],
        achievements: [
          {
            id: '3',
            title: '生产标兵',
            description: '连续两个月超额完成生产任务',
            date: '2024-03-31',
            impact: 'high',
          },
        ],
        areasForImprovement: [
          '加强安全管理',
          '培养新人',
        ],
        reviewerComments: '王五领导能力强，团队管理出色，是生产部的骨干力量。',
        employeeComments: '感谢认可，会继续努力带领团队创造更好业绩。',
        status: 'approved',
        createdAt: '2024-04-01T09:30:00Z',
        reviewedAt: '2024-04-03T10:15:00Z',
        reviewedBy: '赵总监',
      },
      {
        id: '4',
        employeeId: 'EMP004',
        employeeName: '赵六',
        department: '设备部',
        position: '设备维护员',
        reviewPeriod: '2024-Q1',
        overallScore: 85,
        technicalSkills: 88,
        qualityWork: 85,
        productivity: 82,
        teamwork: 85,
        innovation: 80,
        safety: 88,
        attendance: 92,
        goals: [
          {
            id: '5',
            title: '设备维护技能提升',
            description: '学习新设备维护技术',
            target: '掌握2种新设备维护',
            progress: 70,
            status: 'in_progress',
            dueDate: '2024-06-30',
          },
        ],
        achievements: [
          {
            id: '4',
            title: '设备故障率降低',
            description: '设备故障率较上季度降低20%',
            date: '2024-03-31',
            impact: 'medium',
          },
        ],
        areasForImprovement: [
          '提高响应速度',
          '加强预防性维护',
        ],
        reviewerComments: '赵六技术扎实，工作认真，建议提高应急处理能力。',
        employeeComments: '会加强应急处理训练，提高响应速度。',
        status: 'reviewed',
        createdAt: '2024-04-02T14:00:00Z',
        reviewedAt: '2024-04-05T09:45:00Z',
        reviewedBy: '钱主管',
      },
    ]
    setPerformances(mockData)
  }, [])

  // 统计数据
  const getStatistics = () => {
    const total = performances.length
    const approved = performances.filter(p => p.status === 'approved').length
    const reviewed = performances.filter(p => p.status === 'reviewed').length
    const submitted = performances.filter(p => p.status === 'submitted').length
    const draft = performances.filter(p => p.status === 'draft').length
    const avgScore = Math.round(
      performances.reduce((sum, p) => sum + p.overallScore, 0) / total || 0
    )
    const excellent = performances.filter(p => p.overallScore >= 90).length
    const good = performances.filter(p => p.overallScore >= 80 && p.overallScore < 90).length
    const average = performances.filter(p => p.overallScore >= 70 && p.overallScore < 80).length
    const poor = performances.filter(p => p.overallScore < 70).length

    return {
      total,
      approved,
      reviewed,
      submitted,
      draft,
      avgScore,
      excellent,
      good,
      average,
      poor,
    }
  }

  const stats = getStatistics()

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      draft: { color: 'default', text: '草稿', icon: <EditOutlined /> },
      submitted: { color: 'processing', text: '已提交', icon: <CalendarOutlined /> },
      reviewed: { color: 'warning', text: '审核中', icon: <EyeOutlined /> },
      approved: { color: 'success', text: '已批准', icon: <TrophyOutlined /> },
    }
    return statusMap[status] || statusMap.draft
  }

  // 获取分数等级
  const getScoreGrade = (score: number) => {
    if (score >= 90) return { color: 'success', text: '优秀' }
    if (score >= 80) return { color: 'good', text: '良好' }
    if (score >= 70) return { color: 'warning', text: '一般' }
    return { color: 'error', text: '需改进' }
  }

  // 查看详情
  const handleViewDetail = (performance: PerformanceRecord) => {
    setSelectedPerformance(performance)
    setDetailModalVisible(true)
  }

  // 创建绩效评估
  const handleCreatePerformance = () => {
    form.validateFields().then(values => {
      const newPerformance: PerformanceRecord = {
        id: Date.now().toString(),
        ...values,
        overallScore: Math.round(
          (values.technicalSkills + values.qualityWork + values.productivity +
           values.teamwork + values.innovation + values.safety + values.attendance) / 7
        ),
        goals: [],
        achievements: [],
        areasForImprovement: [],
        reviewerComments: '',
        employeeComments: '',
        status: 'draft',
        createdAt: dayjs().toISOString(),
      }
      setPerformances([...performances, newPerformance])
      setModalVisible(false)
      form.resetFields()
      message.success('绩效评估创建成功')
    })
  }

  // 过滤数据
  const filteredPerformances = performances.filter(performance => {
    const matchDepartment = !filterDepartment || performance.department === filterDepartment
    const matchPeriod = !filterPeriod || performance.reviewPeriod === filterPeriod
    const matchStatus = !filterStatus || performance.status === filterStatus
    return matchDepartment && matchPeriod && matchStatus
  })

  // 表格列
  const columns: ColumnsType<PerformanceRecord> = [
    {
      title: '员工信息',
      key: 'employee',
      render: (_, record) => (
        <div>
          <div>
            <Text strong>{record.employeeName}</Text>
            <Tag color="blue" className="ml-2">{record.employeeId}</Tag>
          </div>
          <div>
            <Text type="secondary" className="text-xs">{record.position}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '评估周期',
      dataIndex: 'reviewPeriod',
      key: 'reviewPeriod',
    },
    {
      title: '总体评分',
      dataIndex: 'overallScore',
      key: 'overallScore',
      render: (score) => {
        const grade = getScoreGrade(score)
        return (
          <div>
            <div className="flex items-center">
              <Text strong style={{ color: score >= 90 ? '#52c41a' : score >= 80 ? '#1890ff' : '#fa8c16' }}>
                {score}
              </Text>
              <Text className="ml-1">/100</Text>
            </div>
            <Tag color={grade.color} size="small">{grade.text}</Tag>
          </div>
        )
      },
      sorter: (a, b) => a.overallScore - b.overallScore,
    },
    {
      title: '各项能力',
      key: 'skills',
      render: (_, record) => (
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>技术</span>
            <span>{record.technicalSkills}</span>
          </div>
          <Progress
            percent={record.technicalSkills}
            size="small"
            showInfo={false}
            strokeColor="#1890ff"
          />
          <div className="flex justify-between text-xs">
            <span>质量</span>
            <span>{record.qualityWork}</span>
          </div>
          <Progress
            percent={record.qualityWork}
            size="small"
            showInfo={false}
            strokeColor="#52c41a"
          />
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = getStatusConfig(status)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            查看
          </Button>
          {record.status === 'draft' && (
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedPerformance(record)
                form.setFieldsValue(record)
                setModalVisible(true)
              }}
            >
              编辑
            </Button>
          )}
        </Space>
      ),
    },
  ]

  // 渲染概览页面
  const renderOverview = () => (
    <div>
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="评估总数"
              value={stats.total}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均评分"
              value={stats.avgScore}
              suffix="/ 100"
              prefix={<StarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="优秀员工"
              value={stats.excellent}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats.reviewed + stats.submitted}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={12}>
          <Card title="评分分布">
            <Space direction="vertical" className="w-full">
              <div>
                <div className="flex justify-between mb-1">
                  <Text>优秀 (90-100分)</Text>
                  <Text>{stats.excellent}人</Text>
                </div>
                <Progress
                  percent={stats.total > 0 ? (stats.excellent / stats.total) * 100 : 0}
                  strokeColor="#52c41a"
                  showInfo={false}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <Text>良好 (80-89分)</Text>
                  <Text>{stats.good}人</Text>
                </div>
                <Progress
                  percent={stats.total > 0 ? (stats.good / stats.total) * 100 : 0}
                  strokeColor="#1890ff"
                  showInfo={false}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <Text>一般 (70-79分)</Text>
                  <Text>{stats.average}人</Text>
                </div>
                <Progress
                  percent={stats.total > 0 ? (stats.average / stats.total) * 100 : 0}
                  strokeColor="#fa8c16"
                  showInfo={false}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <Text>需改进 (<70分)</Text>
                  <Text>{stats.poor}人</Text>
                </div>
                <Progress
                  percent={stats.total > 0 ? (stats.poor / stats.total) * 100 : 0}
                  strokeColor="#f5222d"
                  showInfo={false}
                />
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="状态分布">
            <Space direction="vertical" className="w-full">
              <div className="flex justify-between items-center">
                <Space>
                  <TrophyOutlined style={{ color: '#52c41a' }} />
                  <Text>已批准</Text>
                </Space>
                <Tag color="success">{stats.approved}</Tag>
              </div>
              <div className="flex justify-between items-center">
                <Space>
                  <EyeOutlined style={{ color: '#fa8c16' }} />
                  <Text>审核中</Text>
                </Space>
                <Tag color="warning">{stats.reviewed}</Tag>
              </div>
              <div className="flex justify-between items-center">
                <Space>
                  <CalendarOutlined style={{ color: '#1890ff' }} />
                  <Text>已提交</Text>
                </Space>
                <Tag color="processing">{stats.submitted}</Tag>
              </div>
              <div className="flex justify-between items-center">
                <Space>
                  <EditOutlined style={{ color: '#8c8c8c' }} />
                  <Text>草稿</Text>
                </Space>
                <Tag color="default">{stats.draft}</Tag>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="高绩效员工" extra={<Button type="link">查看全部</Button>}>
        <Table
          dataSource={performances
            .filter(p => p.overallScore >= 90)
            .sort((a, b) => b.overallScore - a.overallScore)
            .slice(0, 5)}
          rowKey="id"
          pagination={false}
          size="small"
          columns={[
            {
              title: '员工',
              dataIndex: 'employeeName',
              key: 'employeeName',
              render: (text, record) => (
                <Space>
                  <UserOutlined />
                  <span>{text}</span>
                  <Tag color="blue" size="small">{record.employeeId}</Tag>
                </Space>
              ),
            },
            {
              title: '部门',
              dataIndex: 'department',
              key: 'department',
            },
            {
              title: '评分',
              dataIndex: 'overallScore',
              key: 'overallScore',
              render: (score) => (
                <Space>
                  <Text strong style={{ color: '#52c41a' }}>{score}</Text>
                  <Text>/100</Text>
                </Space>
              ),
            },
            {
              title: '状态',
              dataIndex: 'status',
              key: 'status',
              render: (status) => {
                const config = getStatusConfig(status)
                return <Tag color={config.color}>{config.text}</Tag>
              },
            },
          ]}
        />
      </Card>
    </div>
  )

  // 渲染绩效列表
  const renderList = () => (
    <div>
      {/* 筛选器 */}
      <Card className="mb-6">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="部门筛选"
              value={filterDepartment}
              onChange={setFilterDepartment}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="技术部">技术部</Option>
              <Option value="生产部">生产部</Option>
              <Option value="质量部">质量部</Option>
              <Option value="设备部">设备部</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="评估周期"
              value={filterPeriod}
              onChange={setFilterPeriod}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="2024-Q1">2024年第一季度</Option>
              <Option value="2023-Q4">2023年第四季度</Option>
              <Option value="2023-Q3">2023年第三季度</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="状态筛选"
              value={filterStatus}
              onChange={setFilterStatus}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="draft">草稿</Option>
              <Option value="submitted">已提交</Option>
              <Option value="reviewed">审核中</Option>
              <Option value="approved">已批准</Option>
            </Select>
          </Col>
          <Col xs={24} sm={24} md={6}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setSelectedPerformance(null)
                  form.resetFields()
                  setModalVisible(true)
                }}
              >
                新建评估
              </Button>
              <Button icon={<FilterOutlined />}>
                重置筛选
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 绩效列表 */}
      <Card title="绩效评估列表">
        <Table
          columns={columns}
          dataSource={filteredPerformances}
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
  )

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>绩效管理</Title>
        <Text type="secondary">员工绩效评估、目标管理和能力发展</Text>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: '绩效概览',
            children: renderOverview(),
          },
          {
            key: 'list',
            label: '评估列表',
            children: renderList(),
          },
        ]}
      />

      {/* 创建/编辑绩效评估弹窗 */}
      <Modal
        title={selectedPerformance ? '编辑绩效评估' : '新建绩效评估'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        onOk={handleCreatePerformance}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="employeeId"
                label="员工工号"
                rules={[{ required: true, message: '请输入员工工号' }]}
              >
                <Input placeholder="请输入员工工号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="employeeName"
                label="员工姓名"
                rules={[{ required: true, message: '请输入员工姓名' }]}
              >
                <Input placeholder="请输入员工姓名" />
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
                  <Option value="技术部">技术部</Option>
                  <Option value="生产部">生产部</Option>
                  <Option value="质量部">质量部</Option>
                  <Option value="设备部">设备部</Option>
                </Select>
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
                name="reviewPeriod"
                label="评估周期"
                rules={[{ required: true, message: '请选择评估周期' }]}
              >
                <Select placeholder="请选择评估周期">
                  <Option value="2024-Q1">2024年第一季度</Option>
                  <Option value="2023-Q4">2023年第四季度</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>能力评分 (0-100分)</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="technicalSkills"
                label="技术技能"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="qualityWork"
                label="工作质量"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="productivity"
                label="工作效率"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="teamwork"
                label="团队协作"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="innovation"
                label="创新能力"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="safety"
                label="安全意识"
                rules={[{ required: true, message: '请评分' }]}
              >
                <Rate style={{ fontSize: 24 }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 绩效详情弹窗 */}
      <Modal
        title="绩效评估详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={1000}
      >
        {selectedPerformance && (
          <div>
            <Row gutter={16} className="mb-4">
              <Col span={12}>
                <Card title="基本信息" size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Text strong>员工姓名：</Text> {selectedPerformance.employeeName}
                    </Col>
                    <Col span={12}>
                      <Text strong>员工工号：</Text> {selectedPerformance.employeeId}
                    </Col>
                    <Col span={12}>
                      <Text strong>部门：</Text> {selectedPerformance.department}
                    </Col>
                    <Col span={12}>
                      <Text strong>职位：</Text> {selectedPerformance.position}
                    </Col>
                    <Col span={12}>
                      <Text strong>评估周期：</Text> {selectedPerformance.reviewPeriod}
                    </Col>
                    <Col span={12}>
                      <Text strong>总体评分：</Text>
                      <Text strong style={{ color: '#52c41a', fontSize: 16 }}>
                        {selectedPerformance.overallScore}
                      </Text>
                      <Text>/100</Text>
                    </Col>
                  </Row>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="能力评分" size="small">
                  <Space direction="vertical" className="w-full">
                    <div>
                      <div className="flex justify-between">
                        <Text>技术技能</Text>
                        <Text>{selectedPerformance.technicalSkills}</Text>
                      </div>
                      <Progress percent={selectedPerformance.technicalSkills} />
                    </div>
                    <div>
                      <div className="flex justify-between">
                        <Text>工作质量</Text>
                        <Text>{selectedPerformance.qualityWork}</Text>
                      </div>
                      <Progress percent={selectedPerformance.qualityWork} />
                    </div>
                    <div>
                      <div className="flex justify-between">
                        <Text>工作效率</Text>
                        <Text>{selectedPerformance.productivity}</Text>
                      </div>
                      <Progress percent={selectedPerformance.productivity} />
                    </div>
                    <div>
                      <div className="flex justify-between">
                        <Text>团队协作</Text>
                        <Text>{selectedPerformance.teamwork}</Text>
                      </div>
                      <Progress percent={selectedPerformance.teamwork} />
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Card title="目标完成情况" size="small">
                  {selectedPerformance.goals.map((goal, index) => (
                    <div key={index} className="mb-3">
                      <div className="flex justify-between items-center mb-1">
                        <Text strong>{goal.title}</Text>
                        <Tag color={goal.status === 'completed' ? 'success' : 'processing'}>
                          {goal.progress}%
                        </Tag>
                      </div>
                      <Text type="secondary" className="text-xs">{goal.description}</Text>
                      <Progress percent={goal.progress} size="small" />
                    </div>
                  ))}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="主要成就" size="small">
                  {selectedPerformance.achievements.map((achievement, index) => (
                    <div key={index} className="mb-2">
                      <div className="flex justify-between items-center">
                        <Text strong>{achievement.title}</Text>
                        <Tag color={
                          achievement.impact === 'high' ? 'red' :
                          achievement.impact === 'medium' ? 'orange' : 'blue'
                        }>
                          {achievement.impact === 'high' ? '高影响' :
                           achievement.impact === 'medium' ? '中影响' : '低影响'}
                        </Tag>
                      </div>
                      <Text type="secondary" className="text-xs">{achievement.description}</Text>
                    </div>
                  ))}
                </Card>
              </Col>
            </Row>

            <Row gutter={16} className="mt-4">
              <Col span={12}>
                <Card title="改进建议" size="small">
                  {selectedPerformance.areasForImprovement.map((area, index) => (
                    <Tag key={index} color="warning" className="mb-1">{area}</Tag>
                  ))}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="评估状态" size="small">
                  <Space direction="vertical">
                    <div>
                      <Text strong>当前状态：</Text>
                      <Tag color={getStatusConfig(selectedPerformance.status).color}>
                        {getStatusConfig(selectedPerformance.status).text}
                      </Tag>
                    </div>
                    <div>
                      <Text strong>创建时间：</Text>
                      {dayjs(selectedPerformance.createdAt).format('YYYY-MM-DD HH:mm')}
                    </div>
                    {selectedPerformance.reviewedAt && (
                      <div>
                        <Text strong>审核时间：</Text>
                        {dayjs(selectedPerformance.reviewedAt).format('YYYY-MM-DD HH:mm')}
                      </div>
                    )}
                    {selectedPerformance.reviewedBy && (
                      <div>
                        <Text strong>审核人：</Text>
                        {selectedPerformance.reviewedBy}
                      </div>
                    )}
                  </Space>
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default PerformanceManagement