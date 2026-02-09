import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  message,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Select,
  InputNumber,
  Descriptions,
  Progress,
  Tabs,
  Divider,
  Tree,
  Badge,
  Switch,
  Upload,
  Timeline,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  ApartmentOutlined,
  SafetyOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select
const { TextArea } = Input

interface QualityStandard {
  id: string
  standardCode: string
  standardName: string
  category: string
  subCategory: string
  version: string
  status: 'draft' | 'active' | 'deprecated' | 'under_review'
  level: 'company' | 'industry' | 'national' | 'international'
  scope: string
  description: string
  applicableProducts: string[]
  testMethods: TestMethod[]
  acceptanceCriteria: AcceptanceCriterion[]
  documentUrl?: string
  effectiveDate: string
  expiryDate?: string
  createdBy: string
  approvedBy?: string
  createdAt: string
  updatedAt: string
}

interface TestMethod {
  id: string
  name: string
  code: string
  description: string
  equipment: string[]
  procedure: string
  sampleRequirement: string
  frequency: string
  tolerance: string
}

interface AcceptanceCriterion {
  id: string
  parameter: string
  requirement: string
  minValue?: number
  maxValue?: number
  unit: string
  testMethod: string
  criticalLevel: 'critical' | 'major' | 'minor'
}

interface QualityInspection {
  id: string
  inspectionCode: string
  batchNumber: string
  productId: string
  productName: string
  standardId: string
  standardName: string
  inspectionDate: string
  inspector: string
  results: InspectionResult[]
  overallResult: 'pass' | 'fail' | 'conditional'
  nonConformities: NonConformity[]
  documents: string[]
  status: 'pending' | 'in_progress' | 'completed' | 'rejected'
  createdAt: string
  updatedAt: string
}

interface InspectionResult {
  parameter: string
  measuredValue: number
  unit: string
  requirement: string
  result: 'pass' | 'fail'
  deviation?: number
}

interface NonConformity {
  id: string
  description: string
  severity: 'critical' | 'major' | 'minor'
  quantity: number
  action: string
  status: 'open' | 'closed'
}

interface QualityStats {
  totalStandards: number
  activeStandards: number
  totalInspections: number
  passRate: number
  criticalNC: number
  majorNC: number
  minorNC: number
}

const QualityStandardManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [standards, setStandards] = useState<QualityStandard[]>([])
  const [inspections, setInspections] = useState<QualityInspection[]>([])
  const [filteredStandards, setFilteredStandards] = useState<QualityStandard[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view' | 'inspection'>('create')
  const [currentStandard, setCurrentStandard] = useState<QualityStandard | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('standards')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterLevel, setFilterLevel] = useState<string>('all')

  // 模拟数据
  useEffect(() => {
    generateMockData()
  }, [])

  const generateMockData = () => {
    const mockStandards: QualityStandard[] = [
      {
        id: '1',
        standardCode: 'QS-WELD-001',
        standardName: '焊接质量检验标准',
        category: '焊接质量',
        subCategory: '外观检验',
        version: 'V2.1',
        status: 'active',
        level: 'company',
        scope: '所有焊接产品的外观质量检验',
        description: '规定了焊接接头外观质量的检验方法和验收标准',
        applicableProducts: ['压力容器', '管道', '钢结构'],
        testMethods: [
          {
            id: '1',
            name: '外观检验',
            code: 'VT-001',
            description: '目视检验焊接接头外观质量',
            equipment: ['放大镜', '照相机'],
            procedure: '在良好光照条件下进行目视检查',
            sampleRequirement: '100%检验',
            frequency: '每道焊缝',
            tolerance: '±0.1mm',
          },
        ],
        acceptanceCriteria: [
          {
            id: '1',
            parameter: '焊缝余高',
            requirement: '0-3mm',
            minValue: 0,
            maxValue: 3,
            unit: 'mm',
            testMethod: '外观检验',
            criticalLevel: 'major',
          },
          {
            id: '2',
            parameter: '咬边深度',
            requirement: '≤0.5mm',
            maxValue: 0.5,
            unit: 'mm',
            testMethod: '外观检验',
            criticalLevel: 'major',
          },
        ],
        effectiveDate: '2023-01-01',
        createdBy: '质量部',
        approvedBy: '张总工',
        createdAt: '2022-12-01',
        updatedAt: '2023-01-01',
      },
      {
        id: '2',
        standardCode: 'QS-NDT-002',
        standardName: '无损检测标准',
        category: '无损检测',
        subCategory: '超声波检测',
        version: 'V1.5',
        status: 'active',
        level: 'industry',
        scope: '焊缝内部缺陷检测',
        description: '规定了焊缝超声波检测的方法和验收标准',
        applicableProducts: ['压力容器', '重要管道'],
        testMethods: [
          {
            id: '2',
            name: '超声波检测',
            code: 'UT-002',
            description: '使用超声波检测焊缝内部缺陷',
            equipment: ['超声波探伤仪', '探头'],
            procedure: '按照标准程序进行扫查',
            sampleRequirement: '按比例抽检',
            frequency: '按批次',
            tolerance: 'φ2mm',
          },
        ],
        acceptanceCriteria: [
          {
            id: '3',
            parameter: '缺陷长度',
            requirement: '≤10mm',
            maxValue: 10,
            unit: 'mm',
            testMethod: '超声波检测',
            criticalLevel: 'critical',
          },
          {
            id: '4',
            parameter: '缺陷深度',
            requirement: '≤2mm',
            maxValue: 2,
            unit: 'mm',
            testMethod: '超声波检测',
            criticalLevel: 'major',
          },
        ],
        effectiveDate: '2023-06-01',
        createdBy: '质量部',
        approvedBy: '李总工',
        createdAt: '2023-05-01',
        updatedAt: '2023-06-01',
      },
      {
        id: '3',
        standardCode: 'QS-RD-003',
        standardName: '破坏性试验标准',
        category: '力学性能',
        subCategory: '拉伸试验',
        version: 'V1.0',
        status: 'under_review',
        level: 'company',
        scope: '焊接接头力学性能试验',
        description: '规定了焊接接头拉伸试验的方法和要求',
        applicableProducts: ['压力容器', '承重结构'],
        testMethods: [
          {
            id: '3',
            name: '拉伸试验',
            code: 'TT-003',
            description: '测试焊接接头的抗拉强度',
            equipment: ['万能试验机'],
            procedure: '制备试样，进行拉伸试验',
            sampleRequirement: '按标准制备试样',
            frequency: '每批次',
            tolerance: '±5%',
          },
        ],
        acceptanceCriteria: [
          {
            id: '5',
            parameter: '抗拉强度',
            requirement: '≥母材标准值',
            unit: 'MPa',
            testMethod: '拉伸试验',
            criticalLevel: 'critical',
          },
        ],
        effectiveDate: '2024-01-01',
        createdBy: '质量部',
        createdAt: '2023-11-01',
        updatedAt: '2023-12-01',
      },
    ]

    const mockInspections: QualityInspection[] = [
      {
        id: '1',
        inspectionCode: 'QI-2024-001',
        batchNumber: 'B202402001',
        productId: 'P001',
        productName: '压力容器A',
        standardId: '1',
        standardName: '焊接质量检验标准',
        inspectionDate: '2024-02-15',
        inspector: '王检验员',
        results: [
          {
            parameter: '焊缝余高',
            measuredValue: 2.5,
            unit: 'mm',
            requirement: '0-3mm',
            result: 'pass',
          },
          {
            parameter: '咬边深度',
            measuredValue: 0.6,
            unit: 'mm',
            requirement: '≤0.5mm',
            result: 'fail',
            deviation: 0.1,
          },
        ],
        overallResult: 'fail',
        nonConformities: [
          {
            id: '1',
            description: '咬边深度超标',
            severity: 'major',
            quantity: 1,
            action: '返修处理',
            status: 'open',
          },
        ],
        documents: ['检验报告.pdf', '照片.jpg'],
        status: 'completed',
        createdAt: '2024-02-15',
        updatedAt: '2024-02-15',
      },
    ]

    setStandards(mockStandards)
    setFilteredStandards(mockStandards)
    setInspections(mockInspections)
  }

  // 获取统计数据
  const getQualityStats = (): QualityStats => {
    const activeStandards = standards.filter(std => std.status === 'active').length
    const completedInspections = inspections.filter(insp => insp.status === 'completed')
    const passCount = completedInspections.filter(insp => insp.overallResult === 'pass').length
    const passRate = completedInspections.length > 0 ? Math.round((passCount / completedInspections.length) * 100) : 0

    const criticalNC = inspections.reduce((sum, insp) =>
      sum + insp.nonConformities.filter(nc => nc.severity === 'critical').length, 0)
    const majorNC = inspections.reduce((sum, insp) =>
      sum + insp.nonConformities.filter(nc => nc.severity === 'major').length, 0)
    const minorNC = inspections.reduce((sum, insp) =>
      sum + insp.nonConformities.filter(nc => nc.severity === 'minor').length, 0)

    return {
      totalStandards: standards.length,
      activeStandards,
      totalInspections: inspections.length,
      passRate,
      criticalNC,
      majorNC,
      minorNC,
    }
  }

  const stats = getQualityStats()

  // 搜索过滤
  const handleSearch = (value: string) => {
    const filtered = standards.filter(
      std =>
        std.standardName.toLowerCase().includes(value.toLowerCase()) ||
        std.standardCode.toLowerCase().includes(value.toLowerCase()) ||
        std.description.toLowerCase().includes(value.toLowerCase())
    )
    setFilteredStandards(filtered)
  }

  // 状态过滤
  const handleStatusFilter = (status: string) => {
    setFilterStatus(status)
    applyFilters(status, filterLevel)
  }

  // 级别过滤
  const handleLevelFilter = (level: string) => {
    setFilterLevel(level)
    applyFilters(filterStatus, level)
  }

  const applyFilters = (status: string, level: string) => {
    let filtered = standards

    if (status !== 'all') {
      filtered = filtered.filter(std => std.status === status)
    }

    if (level !== 'all') {
      filtered = filtered.filter(std => std.level === level)
    }

    setFilteredStandards(filtered)
  }

  // 查看详情
  const handleView = (record: QualityStandard) => {
    setCurrentStandard(record)
    setModalType('view')
    setIsModalVisible(true)
    form.setFieldsValue(record)
  }

  // 编辑
  const handleEdit = (record: QualityStandard) => {
    setCurrentStandard(record)
    setModalType('edit')
    setIsModalVisible(true)
    form.setFieldsValue({
      ...record,
      effectiveDate: dayjs(record.effectiveDate),
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : undefined,
    })
  }

  // 删除
  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个质量标准吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        const newStandards = standards.filter(std => std.id !== id)
        setStandards(newStandards)
        setFilteredStandards(newStandards)
        message.success('删除成功')
      },
    })
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusMap = {
      draft: { color: 'default', text: '草稿' },
      active: { color: 'success', text: '生效' },
      deprecated: { color: 'warning', text: '已废弃' },
      under_review: { color: 'processing', text: '审核中' },
    }
    return statusMap[status as keyof typeof statusMap] || { color: 'default', text: status }
  }

  // 获取级别配置
  const getLevelConfig = (level: string) => {
    const levelMap = {
      company: { color: 'blue', text: '企业标准' },
      industry: { color: 'green', text: '行业标准' },
      national: { color: 'orange', text: '国家标准' },
      international: { color: 'purple', text: '国际标准' },
    }
    return levelMap[level as keyof typeof levelMap] || { color: 'default', text: level }
  }

  // 表格列定义
  const columns: ColumnsType<QualityStandard> = [
    {
      title: '标准信息',
      key: 'standard',
      width: 200,
      render: (_, record) => (
        <div>
          <div className="font-medium text-gray-900">{record.standardName}</div>
          <div className="text-sm text-gray-500">{record.standardCode}</div>
          <div className="text-xs text-gray-400">版本: {record.version}</div>
        </div>
      ),
    },
    {
      title: '分类',
      key: 'category',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="text-sm">{record.category}</div>
          <div className="text-xs text-gray-500">{record.subCategory}</div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = getStatusConfig(status)
        return (
          <Tag color={config.color}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => {
        const config = getLevelConfig(level)
        return (
          <Tag color={config.color}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '适用产品',
      key: 'products',
      width: 200,
      render: (_, record) => (
        <div>
          {record.applicableProducts.slice(0, 2).map((product, index) => (
            <Tag key={index} size="small" className="mb-1">{product}</Tag>
          ))}
          {record.applicableProducts.length > 2 && (
            <div className="text-xs text-gray-500">
              +{record.applicableProducts.length - 2} 更多
            </div>
          )}
        </div>
      ),
    },
    {
      title: '生效日期',
      dataIndex: 'effectiveDate',
      key: 'effectiveDate',
      width: 120,
      render: (date: string, record) => {
        const isExpired = record.expiryDate && dayjs().isAfter(record.expiryDate)
        return (
          <div className={isExpired ? 'text-red-600' : 'text-gray-600'}>
            <div>{dayjs(date).format('YYYY-MM-DD')}</div>
            {record.expiryDate && (
              <div className="text-xs">
                {isExpired ? '已过期' : `至${record.expiryDate}`}
              </div>
            )}
          </div>
        )
      },
    },
    {
      title: '检验项目',
      key: 'tests',
      width: 100,
      render: (_, record) => (
        <Badge count={record.testMethods.length} color="#1890ff" />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              danger
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      if (modalType === 'create') {
        const newStandard: QualityStandard = {
          ...values,
          id: Date.now().toString(),
          status: 'draft',
          testMethods: [],
          acceptanceCriteria: [],
          effectiveDate: values.effectiveDate.format('YYYY-MM-DD'),
          expiryDate: values.expiryDate ? values.expiryDate.format('YYYY-MM-DD') : undefined,
          createdBy: '当前用户',
          createdAt: dayjs().format('YYYY-MM-DD'),
          updatedAt: dayjs().format('YYYY-MM-DD'),
        }
        setStandards([...standards, newStandard])
        setFilteredStandards([...standards, newStandard])
        message.success('创建成功')
      } else if (modalType === 'edit' && currentStandard) {
        const updatedStandard = standards.map(std =>
          std.id === currentStandard.id
            ? {
                ...std,
                ...values,
                effectiveDate: values.effectiveDate.format('YYYY-MM-DD'),
                expiryDate: values.expiryDate ? values.expiryDate.format('YYYY-MM-DD') : undefined,
                updatedAt: dayjs().format('YYYY-MM-DD'),
              }
            : std
        )
        setStandards(updatedStandard)
        setFilteredStandards(updatedStandard)
        message.success('更新成功')
      }

      setIsModalVisible(false)
      form.resetFields()
    } catch (error) {
      message.error('操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      {/* 页面标题和统计 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">质量标准管理</h1>

        {/* 统计卡片 */}
        <Row gutter={16} className="mb-6">
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="标准总数"
                value={stats.totalStandards}
                valueStyle={{ color: '#1890ff' }}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="生效标准"
                value={stats.activeStandards}
                valueStyle={{ color: '#52c41a' }}
                prefix={<SafetyOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="检验次数"
                value={stats.totalInspections}
                valueStyle={{ color: '#722ed1' }}
                prefix={<SettingOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="合格率"
                value={stats.passRate}
                suffix="%"
                valueStyle={{ color: '#13c2c2' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="严重不合格"
                value={stats.criticalNC}
                valueStyle={{ color: '#f5222d' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="主要不合格"
                value={stats.majorNC}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'standards',
            label: '质量标准',
            children: (
              <>
                {/* 工具栏 */}
                <Card className="mb-4">
                  <div className="flex justify-between items-center">
                    <Space size="middle">
                      <Search
                        placeholder="搜索标准名称、编号、描述"
                        allowClear
                        enterButton={<SearchOutlined />}
                        style={{ width: 300 }}
                        onSearch={handleSearch}
                        onChange={(e) => !e.target.value && handleSearch('')}
                      />
                      <Select
                        placeholder="状态筛选"
                        style={{ width: 120 }}
                        value={filterStatus}
                        onChange={handleStatusFilter}
                      >
                        <Option value="all">全部状态</Option>
                        <Option value="draft">草稿</Option>
                        <Option value="active">生效</Option>
                        <Option value="deprecated">已废弃</Option>
                        <Option value="under_review">审核中</Option>
                      </Select>
                      <Select
                        placeholder="级别筛选"
                        style={{ width: 120 }}
                        value={filterLevel}
                        onChange={handleLevelFilter}
                      >
                        <Option value="all">全部级别</Option>
                        <Option value="company">企业标准</Option>
                        <Option value="industry">行业标准</Option>
                        <Option value="national">国家标准</Option>
                        <Option value="international">国际标准</Option>
                      </Select>
                    </Space>

                    <Space>
                      <Button icon={<DownloadOutlined />}>导出标准</Button>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => {
                          setModalType('create')
                          setIsModalVisible(true)
                          form.resetFields()
                        }}
                      >
                        新建标准
                      </Button>
                    </Space>
                  </div>
                </Card>

                {/* 标准列表表格 */}
                <Card>
                  <Table
                    columns={columns}
                    dataSource={filteredStandards}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                      total: filteredStandards.length,
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                    }}
                    rowSelection={{
                      selectedRowKeys,
                      onChange: setSelectedRowKeys,
                    }}
                    scroll={{ x: 1200 }}
                  />
                </Card>
              </>
            ),
          },
          {
            key: 'inspections',
            label: '检验记录',
            children: (
              <Card>
                <div className="text-center py-8 text-gray-500">
                  <SettingOutlined className="text-4xl mb-4" />
                  <div>检验记录管理</div>
                  <div className="text-sm">可在此查看和管理质量检验记录</div>
                </div>
              </Card>
            ),
          },
          {
            key: 'nonconformities',
            label: '不合格品管理',
            children: (
              <Card>
                <div className="text-center py-8 text-gray-500">
                  <ExclamationCircleOutlined className="text-4xl mb-4" />
                  <div>不合格品管理</div>
                  <div className="text-sm">可在此跟踪处理不合格品</div>
                </div>
              </Card>
            ),
          },
        ]}
      />

      {/* 标准详情/编辑模态框 */}
      <Modal
        title={
          modalType === 'view' ? '标准详情' :
          modalType === 'edit' ? '编辑标准' :
          '新建标准'
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={
          modalType === 'view' ? [
            <Button key="close" onClick={() => setIsModalVisible(false)}>
              关闭
            </Button>,
          ] : [
            <Button key="cancel" onClick={() => setIsModalVisible(false)}>
              取消
            </Button>,
            <Button
              key="submit"
              type="primary"
              loading={loading}
              onClick={handleSubmit}
            >
              {modalType === 'edit' ? '更新' : '创建'}
            </Button>,
          ]
        }
        width={1000}
      >
        {modalType === 'view' && currentStandard && (
          <div>
            <Descriptions title="基本信息" column={2} bordered>
              <Descriptions.Item label="标准编号">{currentStandard.standardCode}</Descriptions.Item>
              <Descriptions.Item label="标准名称">{currentStandard.standardName}</Descriptions.Item>
              <Descriptions.Item label="版本">{currentStandard.version}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusConfig(currentStandard.status).color}>
                  {getStatusConfig(currentStandard.status).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="级别">
                <Tag color={getLevelConfig(currentStandard.level).color}>
                  {getLevelConfig(currentStandard.level).text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="分类">{currentStandard.category}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="适用范围" column={1} bordered>
              <Descriptions.Item label="范围">{currentStandard.scope}</Descriptions.Item>
              <Descriptions.Item label="描述">{currentStandard.description}</Descriptions.Item>
              <Descriptions.Item label="适用产品">
                {currentStandard.applicableProducts.map((product, index) => (
                  <Tag key={index} color="blue">{product}</Tag>
                ))}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="检验方法" column={1} bordered>
              {currentStandard.testMethods.map((method, index) => (
                <div key={method.id} className="mb-4">
                  <Descriptions title={`方法 ${index + 1}: ${method.name}`} column={2} bordered>
                    <Descriptions.Item label="方法编码">{method.code}</Descriptions.Item>
                    <Descriptions.Item label="设备">{method.equipment.join(', ')}</Descriptions.Item>
                    <Descriptions.Item label="检验频率">{method.frequency}</Descriptions.Item>
                    <Descriptions.Item label="公差">{method.tolerance}</Descriptions.Item>
                    <Descriptions.Item label="程序" span={2}>{method.procedure}</Descriptions.Item>
                  </Descriptions>
                </div>
              ))}
            </Descriptions>

            <Divider />

            <Descriptions title="验收标准" column={1} bordered>
              {currentStandard.acceptanceCriteria.map((criterion, index) => (
                <div key={criterion.id} className="mb-4">
                  <Descriptions title={`标准 ${index + 1}`} column={3} bordered>
                    <Descriptions.Item label="参数">{criterion.parameter}</Descriptions.Item>
                    <Descriptions.Item label="要求">{criterion.requirement}</Descriptions.Item>
                    <Descriptions.Item label="关键程度">
                      <Tag color={
                        criterion.criticalLevel === 'critical' ? 'red' :
                        criterion.criticalLevel === 'major' ? 'orange' : 'blue'
                      }>
                        {criterion.criticalLevel === 'critical' ? '关键' :
                         criterion.criticalLevel === 'major' ? '主要' : '次要'}
                      </Tag>
                    </Descriptions.Item>
                  </Descriptions>
                </div>
              ))}
            </Descriptions>
          </div>
        )}

        {(modalType === 'create' || modalType === 'edit') && (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="standardCode"
                  label="标准编号"
                  rules={[{ required: true, message: '请输入标准编号' }]}
                >
                  <Input placeholder="请输入标准编号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="standardName"
                  label="标准名称"
                  rules={[{ required: true, message: '请输入标准名称' }]}
                >
                  <Input placeholder="请输入标准名称" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="version"
                  label="版本"
                  rules={[{ required: true, message: '请输入版本' }]}
                >
                  <Input placeholder="请输入版本，如: V1.0" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="level"
                  label="级别"
                  rules={[{ required: true, message: '请选择级别' }]}
                >
                  <Select placeholder="请选择级别">
                    <Option value="company">企业标准</Option>
                    <Option value="industry">行业标准</Option>
                    <Option value="national">国家标准</Option>
                    <Option value="international">国际标准</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  name="status"
                  label="状态"
                  rules={[{ required: true, message: '请选择状态' }]}
                >
                  <Select placeholder="请选择状态">
                    <Option value="draft">草稿</Option>
                    <Option value="active">生效</Option>
                    <Option value="deprecated">已废弃</Option>
                    <Option value="under_review">审核中</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="category"
                  label="分类"
                  rules={[{ required: true, message: '请输入分类' }]}
                >
                  <Input placeholder="请输入分类" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="subCategory"
                  label="子分类"
                >
                  <Input placeholder="请输入子分类" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="scope"
              label="适用范围"
              rules={[{ required: true, message: '请输入适用范围' }]}
            >
              <TextArea rows={2} placeholder="请输入适用范围" />
            </Form.Item>

            <Form.Item
              name="description"
              label="描述"
              rules={[{ required: true, message: '请输入描述' }]}
            >
              <TextArea rows={3} placeholder="请输入标准描述" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="effectiveDate"
                  label="生效日期"
                  rules={[{ required: true, message: '请选择生效日期' }]}
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="expiryDate"
                  label="失效日期"
                >
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              name="applicableProducts"
              label="适用产品"
            >
              <Select
                mode="tags"
                placeholder="请输入适用产品，按回车添加"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default QualityStandardManagement