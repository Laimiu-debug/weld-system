import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Form,
  Select,
  DatePicker,
  Input,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Table,
  message,
  Modal,
  Row,
  Col,
  Statistic,
  Tabs,
  Divider,
  Typography,
  Tag,
  Progress,
  Alert,
  Tooltip,
  Transfer,
  TreeSelect,
  InputNumber,
} from 'antd'
import {
  PlusOutlined,
  SaveOutlined,
  ExportOutlined,
  PreviewOutlined,
  SettingOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TableOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import dayjs from 'dayjs'

const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input
const { Title, Text } = Typography
const { TreeNode } = TreeSelect

interface ReportTemplate {
  id: string
  name: string
  description: string
  category: string
  dataSource: string[]
  metrics: MetricConfig[]
  filters: FilterConfig[]
  groupBy: string[]
  chartType: 'table' | 'bar' | 'line' | 'pie' | 'area'
  timeRange: TimeRangeConfig
  layout: LayoutConfig
  createdBy: string
  createdAt: string
  updatedAt: string
  isPublic: boolean
}

interface MetricConfig {
  id: string
  name: string
  field: string
  aggregation: 'sum' | 'avg' | 'count' | 'max' | 'min'
  format: string
  color?: string
  showTrend: boolean
}

interface FilterConfig {
  id: string
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'between'
  value: any
  label: string
}

interface TimeRangeConfig {
  type: 'fixed' | 'dynamic' | 'custom'
  startDate?: string
  endDate?: string
  dynamicRange?: 'today' | 'yesterday' | 'this_week' | 'last_week' | 'this_month' | 'last_month' | 'this_quarter' | 'last_quarter' | 'this_year' | 'last_year'
}

interface LayoutConfig {
  columns: number
  showHeader: boolean
  showFooter: boolean
  showSummary: boolean
  pagination: boolean
  pageSize: number
}

interface DataSourceField {
  name: string
  field: string
  type: 'string' | 'number' | 'date' | 'boolean'
  aggregatable: boolean
  filterable: boolean
  groupable: boolean
}

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa541c']

const CustomReportBuilder: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [currentTemplate, setCurrentTemplate] = useState<ReportTemplate | null>(null)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('builder')
  const [previewData, setPreviewData] = useState<any[]>([])
  const [isPreviewVisible, setIsPreviewVisible] = useState(false)
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [chartType, setChartType] = useState<string>('table')

  // 模拟数据源字段定义
  const availableDataSources: Record<string, DataSourceField[]> = {
    equipment: [
      { name: '设备名称', field: 'name', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '设备类型', field: 'type', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '购买价格', field: 'price', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '运行时间', field: 'runtime', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '使用率', field: 'utilization', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '状态', field: 'status', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '购买日期', field: 'purchase_date', type: 'date', aggregatable: false, filterable: true, groupable: true },
    ],
    production: [
      { name: '产品名称', field: 'product_name', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '生产数量', field: 'quantity', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '合格数量', field: 'qualified_quantity', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '生产时间', field: 'production_time', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '成本', field: 'cost', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '生产日期', field: 'production_date', type: 'date', aggregatable: false, filterable: true, groupable: true },
      { name: '负责团队', field: 'team', type: 'string', aggregatable: false, filterable: true, groupable: true },
    ],
    quality: [
      { name: '检验批次', field: 'batch_no', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '检验数量', field: 'inspection_count', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '合格数量', field: 'pass_count', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '不合格数量', field: 'fail_count', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '合格率', field: 'pass_rate', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '检验日期', field: 'inspection_date', type: 'date', aggregatable: false, filterable: true, groupable: true },
      { name: '检验员', field: 'inspector', type: 'string', aggregatable: false, filterable: true, groupable: true },
    ],
    maintenance: [
      { name: '维护编号', field: 'maintenance_no', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '设备名称', field: 'equipment_name', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '维护类型', field: 'maintenance_type', type: 'string', aggregatable: false, filterable: true, groupable: true },
      { name: '维护成本', field: 'cost', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '维护时长', field: 'duration', type: 'number', aggregatable: true, filterable: true, groupable: false },
      { name: '维护日期', field: 'maintenance_date', type: 'date', aggregatable: false, filterable: true, groupable: true },
      { name: '维护人员', field: 'technician', type: 'string', aggregatable: false, filterable: true, groupable: true },
    ],
  }

  // 模拟模板数据
  useEffect(() => {
    const mockTemplates: ReportTemplate[] = [
      {
        id: '1',
        name: '设备利用率统计报表',
        description: '统计各类设备的利用率和运行情况',
        category: '设备管理',
        dataSource: ['equipment'],
        metrics: [
          { id: '1', name: '平均利用率', field: 'utilization', aggregation: 'avg', format: '0.00%', showTrend: true },
          { id: '2', name: '总运行时间', field: 'runtime', aggregation: 'sum', format: '0小时', showTrend: false },
        ],
        filters: [],
        groupBy: ['type'],
        chartType: 'bar',
        timeRange: { type: 'dynamic', dynamicRange: 'this_month' },
        layout: { columns: 3, showHeader: true, showFooter: true, showSummary: true, pagination: false, pageSize: 10 },
        createdBy: '系统管理员',
        createdAt: '2024-01-01',
        updatedAt: '2024-02-01',
        isPublic: true,
      },
      {
        id: '2',
        name: '生产质量分析报表',
        description: '分析生产质量和合格率趋势',
        category: '质量管理',
        dataSource: ['quality'],
        metrics: [
          { id: '3', name: '合格率', field: 'pass_rate', aggregation: 'avg', format: '0.00%', showTrend: true },
          { id: '4', name: '检验总数', field: 'inspection_count', aggregation: 'sum', format: '0件', showTrend: false },
        ],
        filters: [],
        groupBy: ['inspection_date'],
        chartType: 'line',
        timeRange: { type: 'dynamic', dynamicRange: 'this_month' },
        layout: { columns: 2, showHeader: true, showFooter: false, showSummary: true, pagination: false, pageSize: 10 },
        createdBy: '质量部',
        createdAt: '2024-01-15',
        updatedAt: '2024-02-15',
        isPublic: true,
      },
    ]
    setTemplates(mockTemplates)
  }, [])

  // 生成预览数据
  const generatePreviewData = (template: ReportTemplate) => {
    const data = []
    const days = 30

    if (template.dataSource.includes('equipment')) {
      for (let i = 0; i < 5; i++) {
        data.push({
          name: ['焊机', '切割机', '检测设备', '辅助设备', '其他'][i],
          utilization: Math.random() * 100,
          runtime: Math.floor(Math.random() * 1000),
          count: Math.floor(Math.random() * 10) + 1,
        })
      }
    } else if (template.dataSource.includes('quality')) {
      for (let i = 0; i < days; i++) {
        data.push({
          date: dayjs().subtract(days - i, 'day').format('YYYY-MM-DD'),
          pass_rate: 85 + Math.random() * 15,
          inspection_count: Math.floor(Math.random() * 100) + 50,
          pass_count: Math.floor(Math.random() * 90) + 40,
        })
      }
    }

    return data
  }

  // 预览报表
  const handlePreview = () => {
    form.validateFields().then(values => {
      const template: ReportTemplate = {
        id: Date.now().toString(),
        name: values.name || '未命名报表',
        description: values.description || '',
        category: values.category || '其他',
        dataSource: values.dataSource || [],
        metrics: values.metrics || [],
        filters: values.filters || [],
        groupBy: values.groupBy || [],
        chartType: values.chartType || 'table',
        timeRange: values.timeRange || { type: 'dynamic', dynamicRange: 'this_month' },
        layout: values.layout || { columns: 3, showHeader: true, showFooter: true, showSummary: true, pagination: false, pageSize: 10 },
        createdBy: '当前用户',
        createdAt: dayjs().format('YYYY-MM-DD'),
        updatedAt: dayjs().format('YYYY-MM-DD'),
        isPublic: values.isPublic || false,
      }

      setCurrentTemplate(template)
      setPreviewData(generatePreviewData(template))
      setChartType(template.chartType)
      setIsPreviewVisible(true)
    })
  }

  // 保存模板
  const handleSave = () => {
    form.validateFields().then(values => {
      const template: ReportTemplate = {
        id: Date.now().toString(),
        name: values.name,
        description: values.description,
        category: values.category,
        dataSource: values.dataSource,
        metrics: values.metrics,
        filters: values.filters,
        groupBy: values.groupBy,
        chartType: values.chartType,
        timeRange: values.timeRange,
        layout: values.layout,
        createdBy: '当前用户',
        createdAt: dayjs().format('YYYY-MM-DD'),
        updatedAt: dayjs().format('YYYY-MM-DD'),
        isPublic: values.isPublic,
      }

      setTemplates([...templates, template])
      message.success('报表模板保存成功')
    })
  }

  // 删除模板
  const handleDeleteTemplate = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个报表模板吗？',
      onOk: () => {
        setTemplates(templates.filter(t => t.id !== id))
        message.success('删除成功')
      },
    })
  }

  // 渲染图表
  const renderChart = (data: any[], type: string) => {
    if (data.length === 0) return <div className="text-center py-8 text-gray-500">暂无数据</div>

    switch (type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Bar dataKey="utilization" fill="#1890ff" name="利用率" />
              <Bar dataKey="runtime" fill="#52c41a" name="运行时间" />
            </BarChart>
          </ResponsiveContainer>
        )
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Line type="monotone" dataKey="pass_rate" stroke="#1890ff" name="合格率" />
              <Line type="monotone" dataKey="inspection_count" stroke="#52c41a" name="检验数量" />
            </LineChart>
          </ResponsiveContainer>
        )
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
                label
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <RechartsTooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Area type="monotone" dataKey="pass_rate" stackId="1" stroke="#1890ff" fill="#1890ff" name="合格率" />
              <Area type="monotone" dataKey="inspection_count" stackId="1" stroke="#52c41a" fill="#52c41a" name="检验数量" />
            </AreaChart>
          </ResponsiveContainer>
        )
      default:
        return (
          <Table
            dataSource={data}
            columns={Object.keys(data[0] || {}).map(key => ({
              title: key,
              dataIndex: key,
              key,
            }))}
            pagination={{ pageSize: 10 }}
            size="small"
          />
        )
    }
  }

  // 数据源字段选择组件
  const DataSourceFields = ({ dataSource }: { dataSource: string[] }) => {
    const allFields = dataSource.flatMap(ds => availableDataSources[ds] || [])

    return (
      <Transfer
        dataSource={allFields.map(field => ({
          key: field.field,
          title: field.name,
          disabled: false,
        }))}
        targetKeys={selectedFields}
        onChange={setSelectedFields}
        render={item => item.title}
        oneWay
        style={{ marginBottom: 16 }}
        listStyle={{
          width: 250,
          height: 300,
        }}
      />
    )
  }

  return (
    <div className="p-6">
      <Title level={2} className="mb-6">自定义报表生成器</Title>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'builder',
            label: '报表设计器',
            children: (
              <Row gutter={16}>
                <Col span={16}>
                  <Card title="报表配置" className="mb-4">
                    <Form form={form} layout="vertical">
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            name="name"
                            label="报表名称"
                            rules={[{ required: true, message: '请输入报表名称' }]}
                          >
                            <Input placeholder="请输入报表名称" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            name="category"
                            label="报表分类"
                            rules={[{ required: true, message: '请选择报表分类' }]}
                          >
                            <Select placeholder="请选择报表分类">
                              <Option value="equipment">设备管理</Option>
                              <Option value="production">生产管理</Option>
                              <Option value="quality">质量管理</Option>
                              <Option value="maintenance">维护管理</Option>
                              <Option value="other">其他</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item
                        name="description"
                        label="报表描述"
                      >
                        <TextArea rows={2} placeholder="请输入报表描述" />
                      </Form.Item>

                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            name="dataSource"
                            label="数据源"
                            rules={[{ required: true, message: '请选择数据源' }]}
                          >
                            <Select mode="multiple" placeholder="请选择数据源">
                              <Option value="equipment">设备数据</Option>
                              <Option value="production">生产数据</Option>
                              <Option value="quality">质量数据</Option>
                              <Option value="maintenance">维护数据</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            name="chartType"
                            label="图表类型"
                            rules={[{ required: true, message: '请选择图表类型' }]}
                          >
                            <Select placeholder="请选择图表类型">
                              <Option value="table">表格</Option>
                              <Option value="bar">柱状图</Option>
                              <Option value="line">折线图</Option>
                              <Option value="pie">饼图</Option>
                              <Option value="area">面积图</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item label="时间范围">
                        <Row gutter={16}>
                          <Col span={12}>
                            <Form.Item name={['timeRange', 'type']} noStyle>
                              <Radio.Group>
                                <Radio value="dynamic">动态</Radio>
                                <Radio value="fixed">固定</Radio>
                                <Radio value="custom">自定义</Radio>
                              </Radio.Group>
                            </Form.Item>
                          </Col>
                          <Col span={12}>
                            <Form.Item name={['timeRange', 'dynamicRange']} noStyle>
                              <Select placeholder="选择时间范围">
                                <Option value="today">今天</Option>
                                <Option value="yesterday">昨天</Option>
                                <Option value="this_week">本周</Option>
                                <Option value="last_week">上周</Option>
                                <Option value="this_month">本月</Option>
                                <Option value="last_month">上月</Option>
                                <Option value="this_quarter">本季度</Option>
                                <Option value="last_quarter">上季度</Option>
                                <Option value="this_year">今年</Option>
                                <Option value="last_year">去年</Option>
                              </Select>
                            </Form.Item>
                          </Col>
                        </Row>
                      </Form.Item>

                      <Form.Item name="isPublic" valuePropName="checked">
                        <Checkbox>公开报表（其他用户可见）</Checkbox>
                      </Form.Item>

                      <Divider />

                      <Form.Item label="显示指标">
                        <Form.List name="metrics">
                          {(fields, { add, remove }) => (
                            <>
                              {fields.map(({ key, name, ...restField }) => (
                                <Row key={key} gutter={16} align="middle">
                                  <Col span={6}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'name']}
                                      label="指标名称"
                                    >
                                      <Input placeholder="指标名称" />
                                    </Form.Item>
                                  </Col>
                                  <Col span={4}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'aggregation']}
                                      label="聚合方式"
                                    >
                                      <Select>
                                        <Option value="sum">求和</Option>
                                        <Option value="avg">平均</Option>
                                        <Option value="count">计数</Option>
                                        <Option value="max">最大值</Option>
                                        <Option value="min">最小值</Option>
                                      </Select>
                                    </Form.Item>
                                  </Col>
                                  <Col span={6}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'format']}
                                      label="显示格式"
                                    >
                                      <Input placeholder="如: 0.00%" />
                                    </Form.Item>
                                  </Col>
                                  <Col span={4}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'showTrend']}
                                      valuePropName="checked"
                                      label="显示趋势"
                                    >
                                      <Switch />
                                    </Form.Item>
                                  </Col>
                                  <Col span={4}>
                                    <Button
                                      type="text"
                                      danger
                                      onClick={() => remove(name)}
                                    >
                                      删除
                                    </Button>
                                  </Col>
                                </Row>
                              ))}
                              <Form.Item>
                                <Button
                                  type="dashed"
                                  onClick={() => add()}
                                  icon={<PlusOutlined />}
                                  block
                                >
                                  添加指标
                                </Button>
                              </Form.Item>
                            </>
                          )}
                        </Form.List>
                      </Form.Item>

                      <Form.Item label="分组字段">
                        <Form.List name="groupBy">
                          {(fields, { add, remove }) => (
                            <>
                              {fields.map(({ key, name, ...restField }) => (
                                <Row key={key} gutter={16} align="middle">
                                  <Col span={20}>
                                    <Form.Item
                                      {...restField}
                                      name={name}
                                    >
                                      <Select placeholder="选择分组字段">
                                        <Option value="type">设备类型</Option>
                                        <Option value="team">团队</Option>
                                        <Option value="status">状态</Option>
                                        <Option value="date">日期</Option>
                                      </Select>
                                    </Form.Item>
                                  </Col>
                                  <Col span={4}>
                                    <Button
                                      type="text"
                                      danger
                                      onClick={() => remove(name)}
                                    >
                                      删除
                                    </Button>
                                  </Col>
                                </Row>
                              ))}
                              <Form.Item>
                                <Button
                                  type="dashed"
                                  onClick={() => add()}
                                  icon={<PlusOutlined />}
                                  block
                                >
                                  添加分组
                                </Button>
                              </Form.Item>
                            </>
                          )}
                        </Form.List>
                      </Form.Item>

                      <Form.Item>
                        <Space>
                          <Button type="primary" icon={<PreviewOutlined />} onClick={handlePreview}>
                            预览报表
                          </Button>
                          <Button icon={<SaveOutlined />} onClick={handleSave}>
                            保存模板
                          </Button>
                          <Button icon={<ExportOutlined />}>
                            导出报表
                          </Button>
                        </Space>
                      </Form.Item>
                    </Form>
                  </Card>
                </Col>

                <Col span={8}>
                  <Card title="报表模板" size="small">
                    <div className="space-y-2">
                      {templates.map(template => (
                        <div key={template.id} className="p-3 border rounded hover:bg-gray-50">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-medium">{template.name}</div>
                              <div className="text-sm text-gray-500">{template.category}</div>
                              <div className="text-xs text-gray-400 mt-1">
                                {template.dataSource.join(', ')} · {template.chartType}
                              </div>
                            </div>
                            <Space size="small">
                              {template.isPublic && <Tag color="green">公开</Tag>}
                              <Button
                                type="text"
                                size="small"
                                icon={<EyeOutlined />}
                                onClick={() => {
                                  setCurrentTemplate(template)
                                  setPreviewData(generatePreviewData(template))
                                  setChartType(template.chartType)
                                  setIsPreviewVisible(true)
                                }}
                              />
                              <Button
                                type="text"
                                size="small"
                                icon={<EditOutlined />}
                                onClick={() => form.setFieldsValue(template)}
                              />
                              <Button
                                type="text"
                                size="small"
                                icon={<DeleteOutlined />}
                                danger
                                onClick={() => handleDeleteTemplate(template.id)}
                              />
                            </Space>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card title="数据统计" size="small" className="mt-4">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Statistic
                          title="报表模板"
                          value={templates.length}
                          prefix={<BarChartOutlined />}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="公开模板"
                          value={templates.filter(t => t.isPublic).length}
                          prefix={<SettingOutlined />}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'templates',
            label: '模板管理',
            children: (
              <Card>
                <div className="mb-4">
                  <Space>
                    <Button type="primary" icon={<PlusOutlined />}>
                      新建模板
                    </Button>
                    <Button icon={<DownloadOutlined />}>
                      导入模板
                    </Button>
                    <Button icon={<ExportOutlined />}>
                      导出模板
                    </Button>
                  </Space>
                </div>

                <Table
                  dataSource={templates}
                  rowKey="id"
                  columns={[
                    {
                      title: '模板名称',
                      dataIndex: 'name',
                      key: 'name',
                    },
                    {
                      title: '分类',
                      dataIndex: 'category',
                      key: 'category',
                      render: (category) => <Tag>{category}</Tag>,
                    },
                    {
                      title: '数据源',
                      dataIndex: 'dataSource',
                      key: 'dataSource',
                      render: (sources) => sources.join(', '),
                    },
                    {
                      title: '图表类型',
                      dataIndex: 'chartType',
                      key: 'chartType',
                      render: (type) => (
                        <Tag icon={
                          type === 'bar' ? <BarChartOutlined /> :
                          type === 'line' ? <LineChartOutlined /> :
                          type === 'pie' ? <PieChartOutlined /> :
                          <TableOutlined />
                        }>
                          {type}
                        </Tag>
                      ),
                    },
                    {
                      title: '创建者',
                      dataIndex: 'createdBy',
                      key: 'createdBy',
                    },
                    {
                      title: '创建时间',
                      dataIndex: 'createdAt',
                      key: 'createdAt',
                    },
                    {
                      title: '操作',
                      key: 'actions',
                      render: (_, record) => (
                        <Space>
                          <Button
                            type="text"
                            size="small"
                            icon={<EyeOutlined />}
                            onClick={() => {
                              setCurrentTemplate(record)
                              setPreviewData(generatePreviewData(record))
                              setChartType(record.chartType)
                              setIsPreviewVisible(true)
                            }}
                          >
                            预览
                          </Button>
                          <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined />}
                          >
                            编辑
                          </Button>
                          <Button
                            type="text"
                            size="small"
                            icon={<DeleteOutlined />}
                            danger
                            onClick={() => handleDeleteTemplate(record.id)}
                          >
                            删除
                          </Button>
                        </Space>
                      ),
                    },
                  ]}
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* 预览模态框 */}
      <Modal
        title={
          <div className="flex items-center justify-between">
            <span>报表预览 - {currentTemplate?.name}</span>
            <Space>
              <Button size="small" icon={<DownloadOutlined />}>
                导出Excel
              </Button>
              <Button size="small" icon={<DownloadOutlined />}>
                导出PDF
              </Button>
            </Space>
          </div>
        }
        open={isPreviewVisible}
        onCancel={() => setIsPreviewVisible(false)}
        footer={null}
        width={1200}
      >
        {currentTemplate && (
          <div>
            <Alert
              message={`数据源: ${currentTemplate.dataSource.join(', ')} | 时间范围: ${currentTemplate.timeRange.dynamicRange || '自定义'}`}
              type="info"
              showIcon
              className="mb-4"
            />

            {currentTemplate.metrics.length > 0 && (
              <Row gutter={16} className="mb-4">
                {currentTemplate.metrics.map(metric => (
                  <Col span={6} key={metric.id}>
                    <Card size="small">
                      <Statistic
                        title={metric.name}
                        value={Math.random() * 100}
                        suffix={metric.format.includes('%') ? '%' : ''}
                        precision={metric.format.includes('.00') ? 2 : 0}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            )}

            <Card>
              {renderChart(previewData, chartType)}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default CustomReportBuilder