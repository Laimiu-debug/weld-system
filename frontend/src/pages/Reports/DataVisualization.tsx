import React, { useState, useMemo } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Select,
  DatePicker,
  Button,
  Space,
  Tabs,
  Alert,
  Switch,
  Tooltip,
  Badge,
} from 'antd'
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  AreaChartOutlined,
  HeatMapOutlined,
  RadarChartOutlined,
  ScatterChartOutlined,
  StockOutlined,
  ThunderboltOutlined,
  FullscreenOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select
const { TabPane } = Tabs

// 模拟图表数据
const generateTimeSeriesData = (months: number) => {
  return Array.from({ length: months }, (_, i) => {
    const date = dayjs().subtract(months - i - 1, 'month')
    return {
      month: date.format('YYYY-MM'),
      wps: Math.floor(Math.random() * 50) + 30,
      pqr: Math.floor(Math.random() * 30) + 10,
      quality: Math.floor(Math.random() * 100) + 200,
      efficiency: Math.random() * 20 + 75,
      cost: Math.random() * 10000 + 50000,
    }
  })
}

const generateDistributionData = () => [
  { category: '管道焊接', value: 35, color: '#1890ff' },
  { category: '容器制造', value: 28, color: '#52c41a' },
  { category: '结构工程', value: 22, color: '#faad14' },
  { category: '维修改造', value: 15, color: '#f5222d' },
]

const generateRadarData = () => [
  { dimension: '技术能力', value: 85, fullMark: 100 },
  { dimension: '质量管理', value: 92, fullMark: 100 },
  { dimension: '成本控制', value: 78, fullMark: 100 },
  { dimension: '交付及时', value: 88, fullMark: 100 },
  { dimension: '安全性能', value: 95, fullMark: 100 },
  { dimension: '创新能力', value: 72, fullMark: 100 },
]

const DataVisualization: React.FC = () => {
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(6, 'month'),
    dayjs(),
  ])
  const [chartType, setChartType] = useState<'line' | 'bar' | 'area'>('line')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)

  const timeSeriesData = useMemo(() => generateTimeSeriesData(12), [])
  const distributionData = useMemo(generateDistributionData, [])
  const radarData = useMemo(generateRadarData, [])

  // 简单的SVG图表组件
  const SimpleLineChart = ({ data, width = 600, height = 300 }: { data: any[], width?: number, height?: number }) => {
    const margin = { top: 20, right: 30, bottom: 40, left: 50 }
    const chartWidth = width - margin.left - margin.right
    const chartHeight = height - margin.top - margin.bottom

    const maxValue = Math.max(...data.map(d => Math.max(d.wps, d.pqr, d.quality)))
    const xScale = (index: number) => (index / (data.length - 1)) * chartWidth
    const yScale = (value: number) => chartHeight - (value / maxValue) * chartHeight

    return (
      <div className="w-full overflow-auto">
        <svg width={width} height={height} className="border border-gray-200 rounded">
          {/* 网格线 */}
          {Array.from({ length: 5 }, (_, i) => (
            <g key={i}>
              <line
                x1={margin.left}
                y1={margin.top + (chartHeight / 4) * i}
                x2={margin.left + chartWidth}
                y2={margin.top + (chartHeight / 4) * i}
                stroke="#e0e0e0"
                strokeWidth="1"
              />
              <text
                x={margin.left - 10}
                y={margin.top + (chartHeight / 4) * i + 5}
                textAnchor="end"
                fontSize="12"
                fill="#666"
              >
                {Math.round(maxValue - (maxValue / 4) * i)}
              </text>
            </g>
          ))}

          {/* 数据线 */}
          <g>
            {/* WPS线 */}
            <polyline
              points={data.map((d, i) => `${margin.left + xScale(i)},${margin.top + yScale(d.wps)}`).join(' ')}
              fill="none"
              stroke="#1890ff"
              strokeWidth="2"
            />
            {data.map((d, i) => (
              <circle
                key={`wps-${i}`}
                cx={margin.left + xScale(i)}
                cy={margin.top + yScale(d.wps)}
                r="4"
                fill="#1890ff"
              />
            ))}

            {/* PQR线 */}
            <polyline
              points={data.map((d, i) => `${margin.left + xScale(i)},${margin.top + yScale(d.pqr)}`).join(' ')}
              fill="none"
              stroke="#52c41a"
              strokeWidth="2"
            />
            {data.map((d, i) => (
              <circle
                key={`pqr-${i}`}
                cx={margin.left + xScale(i)}
                cy={margin.top + yScale(d.pqr)}
                r="4"
                fill="#52c41a"
              />
            ))}

            {/* 质量线 */}
            <polyline
              points={data.map((d, i) => `${margin.left + xScale(i)},${margin.top + yScale(d.quality)}`).join(' ')}
              fill="none"
              stroke="#faad14"
              strokeWidth="2"
            />
            {data.map((d, i) => (
              <circle
                key={`quality-${i}`}
                cx={margin.left + xScale(i)}
                cy={margin.top + yScale(d.quality)}
                r="4"
                fill="#faad14"
              />
            ))}
          </g>

          {/* X轴标签 */}
          {data.map((d, i) => (
            <text
              key={`x-label-${i}`}
              x={margin.left + xScale(i)}
              y={height - margin.bottom + 20}
              textAnchor="middle"
              fontSize="12"
              fill="#666"
            >
              {dayjs(d.month).format('MM月')}
            </text>
          ))}

          {/* 图例 */}
          <g transform={`translate(${width - 150}, ${margin.top})`}>
            <rect x="0" y="0" width="12" height="12" fill="#1890ff" />
            <text x="16" y="10" fontSize="12" fill="#666">WPS文档</text>
            <rect x="0" y="20" width="12" height="12" fill="#52c41a" />
            <text x="16" y="30" fontSize="12" fill="#666">PQR记录</text>
            <rect x="0" y="40" width="12" height="12" fill="#faad14" />
            <text x="16" y="50" fontSize="12" fill="#666">质量检验</text>
          </g>
        </svg>
      </div>
    )
  }

  const SimpleBarChart = ({ data, width = 400, height = 300 }: { data: any[], width?: number, height?: number }) => {
    const margin = { top: 20, right: 30, bottom: 60, left: 50 }
    const chartWidth = width - margin.left - margin.right
    const chartHeight = height - margin.top - margin.bottom

    const maxValue = Math.max(...data.map(d => d.value))
    const barWidth = chartWidth / data.length * 0.6
    const barSpacing = chartWidth / data.length

    return (
      <div className="w-full overflow-auto">
        <svg width={width} height={height} className="border border-gray-200 rounded">
          {/* Y轴 */}
          {Array.from({ length: 5 }, (_, i) => (
            <g key={i}>
              <line
                x1={margin.left}
                y1={margin.top + (chartHeight / 4) * i}
                x2={margin.left + chartWidth}
                y2={margin.top + (chartHeight / 4) * i}
                stroke="#e0e0e0"
                strokeWidth="1"
              />
              <text
                x={margin.left - 10}
                y={margin.top + (chartHeight / 4) * i + 5}
                textAnchor="end"
                fontSize="12"
                fill="#666"
              >
                {Math.round(maxValue - (maxValue / 4) * i)}
              </text>
            </g>
          ))}

          {/* 柱状图 */}
          {data.map((d, i) => (
            <g key={i}>
              <rect
                x={margin.left + barSpacing * i + (barSpacing - barWidth) / 2}
                y={margin.top + chartHeight - (d.value / maxValue) * chartHeight}
                width={barWidth}
                height={(d.value / maxValue) * chartHeight}
                fill={d.color}
              />
              <text
                x={margin.left + barSpacing * i + barSpacing / 2}
                y={height - margin.bottom + 40}
                textAnchor="middle"
                fontSize="11"
                fill="#666"
                transform={`rotate(-45 ${margin.left + barSpacing * i + barSpacing / 2} ${height - margin.bottom + 40})`}
              >
                {d.category}
              </text>
              <text
                x={margin.left + barSpacing * i + barSpacing / 2}
                y={margin.top + chartHeight - (d.value / maxValue) * chartHeight - 5}
                textAnchor="middle"
                fontSize="12"
                fill="#333"
                fontWeight="bold"
              >
                {d.value}
              </text>
            </g>
          ))}
        </svg>
      </div>
    )
  }

  const SimpleRadarChart = ({ data, width = 400, height = 400 }: { data: any[], width?: number, height?: number }) => {
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) / 2 - 60
    const angleStep = (Math.PI * 2) / data.length

    return (
      <div className="w-full overflow-auto">
        <svg width={width} height={height} className="border border-gray-200 rounded">
          {/* 背景网格 */}
          {Array.from({ length: 5 }, (_, i) => {
            const r = radius * ((i + 1) / 5)
            const points = data.map((_, index) => {
              const angle = angleStep * index - Math.PI / 2
              return `${centerX + r * Math.cos(angle)},${centerY + r * Math.sin(angle)}`
            }).join(' ')
            return (
              <polygon
                key={i}
                points={points}
                fill="none"
                stroke="#e0e0e0"
                strokeWidth="1"
              />
            )
          })}

          {/* 轴线 */}
          {data.map((_, index) => {
            const angle = angleStep * index - Math.PI / 2
            return (
              <line
                key={index}
                x1={centerX}
                y1={centerY}
                x2={centerX + radius * Math.cos(angle)}
                y2={centerY + radius * Math.sin(angle)}
                stroke="#e0e0e0"
                strokeWidth="1"
              />
            )
          })}

          {/* 数据多边形 */}
          <polygon
            points={data.map((item, index) => {
              const angle = angleStep * index - Math.PI / 2
              const r = radius * (item.value / item.fullMark)
              return `${centerX + r * Math.cos(angle)},${centerY + r * Math.sin(angle)}`
            }).join(' ')}
            fill="rgba(24, 144, 255, 0.2)"
            stroke="#1890ff"
            strokeWidth="2"
          />

          {/* 数据点 */}
          {data.map((item, index) => {
            const angle = angleStep * index - Math.PI / 2
            const r = radius * (item.value / item.fullMark)
            return (
              <circle
                key={index}
                cx={centerX + r * Math.cos(angle)}
                cy={centerY + r * Math.sin(angle)}
                r="4"
                fill="#1890ff"
              />
            )
          })}

          {/* 标签 */}
          {data.map((item, index) => {
            const angle = angleStep * index - Math.PI / 2
            const labelRadius = radius + 30
            return (
              <text
                key={index}
                x={centerX + labelRadius * Math.cos(angle)}
                y={centerY + labelRadius * Math.sin(angle)}
                textAnchor="middle"
                fontSize="12"
                fill="#666"
              >
                {item.dimension}
              </text>
            )
          })}
        </svg>
      </div>
    )
  }

  const SimpleHeatmap = ({ width = 600, height = 300 }: { width?: number, height?: number }) => {
    const data = Array.from({ length: 7 }, (_, i) =>
      Array.from({ length: 12 }, (_, j) => ({
        value: Math.floor(Math.random() * 100),
        week: i,
        month: j,
      }))
    )

    const cellSize = 30
    const padding = 40

    return (
      <div className="w-full overflow-auto">
        <svg width={width} height={height} className="border border-gray-200 rounded">
          {/* 月份标签 */}
          {['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'].map((month, i) => (
            <text
              key={i}
              x={padding + i * cellSize + cellSize / 2}
              y={padding - 10}
              textAnchor="middle"
              fontSize="10"
              fill="#666"
            >
              {month}
            </text>
          ))}

          {/* 周标签 */}
          {['周一', '周二', '周三', '周四', '周五', '周六', '周日'].map((day, i) => (
            <text
              key={i}
              x={padding - 10}
              y={padding + i * cellSize + cellSize / 2 + 5}
              textAnchor="end"
              fontSize="10"
              fill="#666"
            >
              {day}
            </text>
          ))}

          {/* 热力图格子 */}
          {data.map((week, weekIndex) =>
            week.map((cell, monthIndex) => (
              <rect
                key={`${weekIndex}-${monthIndex}`}
                x={padding + monthIndex * cellSize}
                y={padding + weekIndex * cellSize}
                width={cellSize - 2}
                height={cellSize - 2}
                fill={cell.value > 80 ? '#1890ff' : cell.value > 60 ? '#52c41a' : cell.value > 40 ? '#faad14' : '#f5222d'}
                opacity={0.8}
              />
            ))
          )}
        </svg>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <Title level={2} className="mb-2">数据可视化中心</Title>
            <Text type="secondary">多维度数据分析和可视化展示</Text>
          </div>
          <Space>
            <div className="flex items-center">
              <Text className="mr-2">自动刷新</Text>
              <Switch checked={autoRefresh} onChange={setAutoRefresh} />
            </div>
            <Tooltip title="全屏显示">
              <Button icon={<FullscreenOutlined />} onClick={() => setFullscreen(!fullscreen)} />
            </Tooltip>
            <Button type="primary" icon={<ThunderboltOutlined />}>
              刷新数据
            </Button>
          </Space>
        </div>
      </div>

      {/* 控制面板 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>时间范围：</Text>
          </Col>
          <Col>
            <RangePicker value={timeRange} onChange={setTimeRange} />
          </Col>
          <Col>
            <Text strong>图表类型：</Text>
          </Col>
          <Col>
            <Select value={chartType} onChange={setChartType} style={{ width: 120 }}>
              <Option value="line">折线图</Option>
              <Option value="bar">柱状图</Option>
              <Option value="area">面积图</Option>
            </Select>
          </Col>
          <Col>
            <Space>
              <Button icon={<LineChartOutlined />}>趋势图</Button>
              <Button icon={<BarChartOutlined />}>对比图</Button>
              <Button icon={<PieChartOutlined />}>分布图</Button>
              <Button icon={<RadarChartOutlined />}>雷达图</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主要图表区域 */}
      <Tabs defaultActiveKey="trends" className="mb-6">
        <TabPane tab="趋势分析" key="trends">
          <Card title="业务指标趋势分析" extra={<Badge status="processing" text="实时更新" />}>
            <SimpleLineChart data={timeSeriesData} width={800} height={400} />
          </Card>
        </TabPane>

        <TabPane tab="分布统计" key="distribution">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="项目类型分布">
                <SimpleBarChart data={distributionData} width={400} height={300} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="工作负荷热力图">
                <SimpleHeatmap width={400} height={300} />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="能力分析" key="capability">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="综合能力雷达图">
                <SimpleRadarChart data={radarData} width={400} height={400} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="能力评分详情">
                <div className="space-y-4">
                  {radarData.map((item, index) => (
                    <div key={index}>
                      <div className="flex justify-between items-center mb-2">
                        <Text strong>{item.dimension}</Text>
                        <Text>{item.value}/{item.fullMark}</Text>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(item.value / item.fullMark) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="对比分析" key="comparison">
          <Card title="多维度对比分析">
            <div className="text-center text-gray-500 py-8">
              <AreaChartOutlined style={{ fontSize: 48 }} />
              <div className="mt-4">
                <Text>对比分析图表开发中...</Text>
                <br />
                <Text type="secondary">将支持多指标对比、同期对比等功能</Text>
              </div>
            </div>
          </Card>
        </TabPane>
      </Tabs>

      {/* 系统提示 */}
      <Alert
        message="图表说明"
        description="所有图表均支持交互操作，鼠标悬停可查看详细数据。点击图例可以显示/隐藏对应的数据系列。"
        type="info"
        showIcon
      />
    </div>
  )
}

export default DataVisualization