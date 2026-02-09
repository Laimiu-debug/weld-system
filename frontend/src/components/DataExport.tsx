import React, { useState } from 'react'
import {
  Button,
  Modal,
  Form,
  Select,
  DatePicker,
  Checkbox,
  Input,
  message,
  Space,
  Row,
  Col,
  Card,
  Typography,
  Divider,
  Progress,
  Alert,
  Tooltip,
  Upload,
  Table,
  Tag,
} from 'antd'
import {
  DownloadOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  UploadOutlined,
  SettingOutlined,
  FilterOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import * as XLSX from 'xlsx'
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import dayjs from 'dayjs'

const { Option } = Select
const { RangePicker } = DatePicker
const { TextArea } = Input
const { Title, Text } = Typography

interface ExportConfig {
  format: 'excel' | 'pdf' | 'csv' | 'json'
  dataSource: string
  fields: string[]
  filters: Record<string, any>
  dateRange: [string, string] | null
  includeHeaders: boolean
  includeSummary: boolean
  pageSize: number
  template?: string
}

interface ExportField {
  key: string
  title: string
  type: 'string' | 'number' | 'date' | 'boolean'
  width?: number
  format?: string
}

interface ExportTemplate {
  id: string
  name: string
  description: string
  dataSource: string
  fields: string[]
  config: Partial<ExportConfig>
}

const DataExport: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)
  const [form] = Form.useForm()
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'excel',
    dataSource: '',
    fields: [],
    filters: {},
    dateRange: null,
    includeHeaders: true,
    includeSummary: false,
    pageSize: 1000,
  })

  // 可用的数据源
  const dataSources = [
    { key: 'equipment', name: '设备数据', description: '包含所有设备的基本信息和运行数据' },
    { key: 'production', name: '生产数据', description: '生产计划、任务和产出数据' },
    { key: 'quality', name: '质量数据', description: '质量检验结果和不合格品记录' },
    { key: 'maintenance', name: '维护数据', description: '设备维护记录和成本数据' },
    { key: 'welders', name: '焊工数据', description: '焊工资质和培训记录' },
    { key: 'materials', name: '材料数据', description: '焊材库存和使用记录' },
    { key: 'wps', name: 'WPS数据', description: '焊接工艺规范记录' },
    { key: 'pqr', name: 'PQR数据', description: '工艺评定报告记录' },
  ]

  // 字段定义
  const fieldDefinitions: Record<string, ExportField[]> = {
    equipment: [
      { key: 'id', title: 'ID', type: 'string' },
      { key: 'name', title: '设备名称', type: 'string' },
      { key: 'code', title: '设备编号', type: 'string' },
      { key: 'type', title: '设备类型', type: 'string' },
      { key: 'manufacturer', title: '制造商', type: 'string' },
      { key: 'model', title: '型号', type: 'string' },
      { key: 'status', title: '状态', type: 'string' },
      { key: 'location', title: '位置', type: 'string' },
      { key: 'purchaseDate', title: '购买日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'purchasePrice', title: '购买价格', type: 'number' },
      { key: 'utilizationRate', title: '使用率', type: 'number', format: '0.00%' },
      { key: 'operatingHours', title: '运行时间', type: 'number' },
      { key: 'maintenanceCost', title: '维护成本', type: 'number' },
      { key: 'efficiency', title: '效率', type: 'number', format: '0.00%' },
    ],
    production: [
      { key: 'id', title: 'ID', type: 'string' },
      { key: 'planName', title: '计划名称', type: 'string' },
      { key: 'planCode', title: '计划编号', type: 'string' },
      { key: 'productName', title: '产品名称', type: 'string' },
      { key: 'quantity', title: '数量', type: 'number' },
      { key: 'unit', title: '单位', type: 'string' },
      { key: 'status', title: '状态', type: 'string' },
      { key: 'progress', title: '进度', type: 'number', format: '0.00%' },
      { key: 'startDate', title: '开始日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'endDate', title: '结束日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'team', title: '负责团队', type: 'string' },
      { key: 'estimatedCost', title: '预计成本', type: 'number' },
      { key: 'actualCost', title: '实际成本', type: 'number' },
    ],
    quality: [
      { key: 'id', title: 'ID', type: 'string' },
      { key: 'batchNumber', title: '批次号', type: 'string' },
      { key: 'productName', title: '产品名称', type: 'string' },
      { key: 'inspectionDate', title: '检验日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'inspector', title: '检验员', type: 'string' },
      { key: 'inspectionCount', title: '检验数量', type: 'number' },
      { key: 'passCount', title: '合格数量', type: 'number' },
      { key: 'failCount', title: '不合格数量', type: 'number' },
      { key: 'passRate', title: '合格率', type: 'number', format: '0.00%' },
      { key: 'result', title: '检验结果', type: 'string' },
      { key: 'nonConformities', title: '不合格项', type: 'string' },
    ],
    maintenance: [
      { key: 'id', title: 'ID', type: 'string' },
      { key: 'taskCode', title: '任务编号', type: 'string' },
      { key: 'equipmentName', title: '设备名称', type: 'string' },
      { key: 'maintenanceType', title: '维护类型', type: 'string' },
      { key: 'title', title: '任务标题', type: 'string' },
      { key: 'status', title: '状态', type: 'string' },
      { key: 'technician', title: '维护人员', type: 'string' },
      { key: 'scheduledDate', title: '计划日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'completedDate', title: '完成日期', type: 'date', format: 'YYYY-MM-DD' },
      { key: 'estimatedCost', title: '预计成本', type: 'number' },
      { key: 'actualCost', title: '实际成本', type: 'number' },
      { key: 'duration', title: '维护时长', type: 'number' },
    ],
  }

  // 导出模板
  const exportTemplates: ExportTemplate[] = [
    {
      id: '1',
      name: '设备清单报表',
      description: '完整的设备清单，包含基本信息和运行数据',
      dataSource: 'equipment',
      fields: ['name', 'code', 'type', 'manufacturer', 'model', 'status', 'location', 'purchaseDate', 'purchasePrice'],
      config: {
        format: 'excel',
        includeHeaders: true,
        includeSummary: true,
      },
    },
    {
      id: '2',
      name: '生产统计报表',
      description: '生产计划和完成情况统计',
      dataSource: 'production',
      fields: ['planName', 'planCode', 'productName', 'quantity', 'status', 'progress', 'startDate', 'endDate', 'team'],
      config: {
        format: 'excel',
        includeHeaders: true,
        includeSummary: true,
      },
    },
    {
      id: '3',
      name: '质量检验报表',
      description: '质量检验结果和合格率统计',
      dataSource: 'quality',
      fields: ['batchNumber', 'productName', 'inspectionDate', 'inspector', 'inspectionCount', 'passCount', 'passRate', 'result'],
      config: {
        format: 'pdf',
        includeHeaders: true,
        includeSummary: true,
      },
    },
  ]

  // 生成模拟数据
  const generateMockData = (dataSource: string, count: number = 100): any[] => {
    const data = []
    const fields = fieldDefinitions[dataSource] || []

    for (let i = 0; i < count; i++) {
      const item: any = {}
      fields.forEach(field => {
        switch (field.type) {
          case 'string':
            if (field.key === 'status') {
              item[field.key] = ['正常', '维护中', '故障', '已报废'][Math.floor(Math.random() * 4)]
            } else if (field.key === 'type') {
              item[field.key] = ['焊机', '切割机', '检测设备'][Math.floor(Math.random() * 3)]
            } else {
              item[field.key] = `${field.title}_${i + 1}`
            }
            break
          case 'number':
            item[field.key] = Math.floor(Math.random() * 1000)
            break
          case 'date':
            item[field.key] = dayjs().subtract(Math.floor(Math.random() * 365), 'day').format(field.format || 'YYYY-MM-DD')
            break
          case 'boolean':
            item[field.key] = Math.random() > 0.5
            break
          default:
            item[field.key] = ''
        }
      })
      data.push(item)
    }

    return data
  }

  // 处理导出
  const handleExport = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      setExportProgress(0)

      const config: ExportConfig = {
        ...exportConfig,
        ...values,
        dateRange: values.dateRange ? [
          values.dateRange[0].format('YYYY-MM-DD'),
          values.dateRange[1].format('YYYY-MM-DD')
        ] : null,
      }

      // 模拟数据生成
      const data = generateMockData(config.dataSource, 500)
      const filteredData = config.fields.length > 0
        ? data.map(item => {
            const filtered: any = {}
            config.fields.forEach(field => {
              if (item[field] !== undefined) {
                filtered[field] = item[field]
              }
            })
            return filtered
          })
        : data

      // 模拟导出进度
      for (let i = 0; i <= 100; i += 10) {
        setExportProgress(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      // 执行实际导出
      switch (config.format) {
        case 'excel':
          exportToExcel(filteredData, config)
          break
        case 'pdf':
          exportToPDF(filteredData, config)
          break
        case 'csv':
          exportToCSV(filteredData, config)
          break
        case 'json':
          exportToJSON(filteredData, config)
          break
      }

      message.success('导出成功')
      setIsModalVisible(false)
      setExportProgress(0)
    } catch (error) {
      message.error('导出失败')
    } finally {
      setLoading(false)
    }
  }

  // 导出到Excel
  const exportToExcel = (data: any[], config: ExportConfig) => {
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(data)

    if (config.includeHeaders) {
      const headers = config.fields.map(field => {
        const fieldDef = fieldDefinitions[config.dataSource]?.find(f => f.key === field)
        return fieldDef?.title || field
      })
      XLSX.utils.sheet_add_aoa(ws, [headers], { origin: 'A1' })
    }

    XLSX.utils.book_append_sheet(wb, ws, '数据')
    XLSX.writeFile(wb, `${config.dataSource}_${dayjs().format('YYYY-MM-DD')}.xlsx`)
  }

  // 导出到PDF
  const exportToPDF = (data: any[], config: ExportConfig) => {
    const doc = new jsPDF()

    // 添加标题
    doc.setFontSize(16)
    doc.text(`${config.dataSource} 数据导出`, 14, 15)

    // 添加日期
    doc.setFontSize(10)
    doc.text(`导出时间: ${dayjs().format('YYYY-MM-DD HH:mm:ss')}`, 14, 25)

    // 添加表格
    if (data.length > 0) {
      const headers = config.fields.map(field => {
        const fieldDef = fieldDefinitions[config.dataSource]?.find(f => f.key === field)
        return fieldDef?.title || field
      })

      const rows = data.slice(0, 20).map(item =>
        config.fields.map(field => String(item[field] || ''))
      )

      // @ts-ignore
      doc.autoTable({
        head: [headers],
        body: rows,
        startY: 35,
        styles: { fontSize: 8 },
      })
    }

    doc.save(`${config.dataSource}_${dayjs().format('YYYY-MM-DD')}.pdf`)
  }

  // 导出到CSV
  const exportToCSV = (data: any[], config: ExportConfig) => {
    const headers = config.fields.map(field => {
      const fieldDef = fieldDefinitions[config.dataSource]?.find(f => f.key === field)
      return fieldDef?.title || field
    })

    const csvContent = [
      headers.join(','),
      ...data.map(item =>
        config.fields.map(field => `"${item[field] || ''}"`).join(',')
      )
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `${config.dataSource}_${dayjs().format('YYYY-MM-DD')}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 导出到JSON
  const exportToJSON = (data: any[], config: ExportConfig) => {
    const jsonContent = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `${config.dataSource}_${dayjs().format('YYYY-MM-DD')}.json`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 应用模板
  const applyTemplate = (template: ExportTemplate) => {
    form.setFieldsValue({
      dataSource: template.dataSource,
      fields: template.fields,
      ...template.config,
    })
    setSelectedFields(template.fields)
    setExportConfig({
      ...exportConfig,
      dataSource: template.dataSource,
      fields: template.fields,
      ...template.config,
    } as ExportConfig)
  }

  return (
    <>
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={() => setIsModalVisible(true)}
      >
        数据导出
      </Button>

      <Modal
        title={
          <div className="flex items-center">
            <DownloadOutlined className="mr-2" />
            数据导出
          </div>
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form form={form} layout="vertical">
          <div className="mb-4">
            <Title level={4}>快速模板</Title>
            <Row gutter={16}>
              {exportTemplates.map(template => (
                <Col span={8} key={template.id}>
                  <Card
                    size="small"
                    hoverable
                    className="mb-2"
                    onClick={() => applyTemplate(template)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{template.name}</div>
                        <div className="text-xs text-gray-500">{template.description}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          <Tag size="small">{template.dataSource}</Tag>
                          <Tag size="small">{template.config.format}</Tag>
                        </div>
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>

          <Divider />

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="dataSource"
                label="数据源"
                rules={[{ required: true, message: '请选择数据源' }]}
              >
                <Select
                  placeholder="请选择数据源"
                  onChange={(value) => {
                    setSelectedFields([])
                    setExportConfig({ ...exportConfig, dataSource: value })
                  }}
                >
                  {dataSources.map(ds => (
                    <Option key={ds.key} value={ds.key}>
                      <div>
                        <div>{ds.name}</div>
                        <div className="text-xs text-gray-500">{ds.description}</div>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="format"
                label="导出格式"
                rules={[{ required: true, message: '请选择导出格式' }]}
              >
                <Select placeholder="请选择导出格式">
                  <Option value="excel">
                    <FileExcelOutlined className="mr-1" />
                    Excel (.xlsx)
                  </Option>
                  <Option value="pdf">
                    <FilePdfOutlined className="mr-1" />
                    PDF (.pdf)
                  </Option>
                  <Option value="csv">
                    <FileTextOutlined className="mr-1" />
                    CSV (.csv)
                  </Option>
                  <Option value="json">
                    <FileTextOutlined className="mr-1" />
                    JSON (.json)
                  </Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="dateRange"
                label="时间范围"
              >
                <RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="导出字段">
            <Form.Item name="fields" noStyle>
              <Select
                mode="multiple"
                placeholder="请选择要导出的字段"
                style={{ width: '100%' }}
                onChange={(fields) => {
                  setSelectedFields(fields)
                  setExportConfig({ ...exportConfig, fields })
                }}
              >
                {(fieldDefinitions[exportConfig.dataSource] || []).map(field => (
                  <Option key={field.key} value={field.key}>
                    {field.title} ({field.type})
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <div className="text-xs text-gray-500 mt-1">
              已选择 {selectedFields.length} 个字段
            </div>
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="includeHeaders"
                valuePropName="checked"
              >
                <Checkbox>包含表头</Checkbox>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="includeSummary"
                valuePropName="checked"
              >
                <Checkbox>包含汇总信息</Checkbox>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="pageSize"
                label="每页记录数"
              >
                <InputNumber min={100} max={10000} step={100} defaultValue={1000} />
              </Form.Item>
            </Col>
          </Row>

          {loading && (
            <div className="mb-4">
              <Text>正在导出数据...</Text>
              <Progress percent={exportProgress} status="active" />
            </div>
          )}

          <div className="flex justify-end">
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                取消
              </Button>
              <Button
                type="primary"
                onClick={handleExport}
                loading={loading}
                disabled={!exportConfig.dataSource || selectedFields.length === 0}
              >
                开始导出
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </>
  )
}

export default DataExport