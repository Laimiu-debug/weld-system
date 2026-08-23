import React, { useState, useEffect } from 'react'
import {
  Table,
  Card,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Tooltip,
  Modal,
  message,
  Row,
  Col,
  Statistic,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import weldersService, { Welder } from '@/services/welders'
import ListPageHeader from '@/components/ListPageHeader'

const { Search } = Input
const { Option } = Select

export interface CertSummary {
  cert_count: number
  systems: string[]
  nearest_expiry?: string | null
  risk_count: number
  risk_level: string
}

type WelderRow = Welder & { cert_summary?: CertSummary }

const SYSTEM_LABELS: Record<string, string> = {
  ASME: 'ASME',
  GB: '国标',
  EN: '欧标',
  AWS: 'AWS',
  API: 'API',
  DNV: 'DNV',
  OTHER: '其他',
  国标: '国标',
  欧标: '欧标',
  其他: '其他',
}

const WeldersList: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [welders, setWelders] = useState<WelderRow[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [skillLevelFilter, setSkillLevelFilter] = useState<string | undefined>()
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [certStatusFilter, setCertStatusFilter] = useState<string | undefined>()

  useEffect(() => {
    const fromQuery =
      searchParams.get('certStatus') ||
      searchParams.get('status') ||
      searchParams.get('certification_status')
    if (fromQuery === 'expiring_soon' || fromQuery === 'expired' || fromQuery === 'valid') {
      setCertStatusFilter(fromQuery)
    }
    const q = searchParams.get('q')
    if (q !== null) {
      setSearchText(q)
      setCurrentPage(1)
    }
  }, [searchParams])

  const fetchWelders = async () => {
    setLoading(true)
    try {
      const response = await weldersService.getList({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchText || undefined,
        skill_level: skillLevelFilter,
        status: statusFilter,
        certification_status: certStatusFilter,
      })
      if (response.success && response.data) {
        setWelders((response.data.items || []) as WelderRow[])
        setTotal(response.data.total || 0)
      } else {
        message.error('获取焊工列表失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取焊工列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWelders()
  }, [currentPage, pageSize, searchText, skillLevelFilter, statusFilter, certStatusFilter])

  const handleCertFilterChange = (value?: string) => {
    setCertStatusFilter(value)
    setCurrentPage(1)
    const next = new URLSearchParams(searchParams)
    if (value) {
      next.set('certStatus', value)
      next.delete('status')
    } else {
      next.delete('certStatus')
      next.delete('status')
    }
    setSearchParams(next, { replace: true })
  }

  const handleDelete = (welder: Welder) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除焊工「${welder.full_name}」吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await weldersService.delete(welder.id)
          message.success('删除成功')
          fetchWelders()
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败')
        }
      },
    })
  }

  const riskOnPage = welders.filter((w) => w.cert_summary?.risk_level === 'expiring_soon').length
  const expiredOnPage = welders.filter((w) => w.cert_summary?.risk_level === 'expired').length
  const validOnPage = welders.filter((w) => w.cert_summary?.risk_level === 'valid').length

  const columns: ColumnsType<WelderRow> = [
    {
      title: '焊工编号',
      dataIndex: 'welder_code',
      key: 'welder_code',
      width: 140,
      fixed: 'left',
      render: (text, record) => (
        <Button type="link" onClick={() => navigate(`/welders/${record.id}`)}>
          {text}
        </Button>
      ),
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      width: 100,
    },
    {
      title: '部门/岗位',
      key: 'org',
      width: 140,
      ellipsis: true,
      render: (_, r) => [r.department, r.position].filter(Boolean).join(' / ') || '-',
    },
    {
      title: '持证体系',
      key: 'systems',
      width: 160,
      render: (_, r) => {
        const systems = r.cert_summary?.systems || []
        if (!systems.length) return <Tag>暂无持证</Tag>
        return (
          <Space wrap size={[4, 4]}>
            {systems.slice(0, 3).map((s) => (
              <Tag key={s} color="blue">
                {SYSTEM_LABELS[s] || s}
              </Tag>
            ))}
            {systems.length > 3 && <Tag>+{systems.length - 3}</Tag>}
          </Space>
        )
      },
    },
    {
      title: '持证项目数',
      key: 'cert_count',
      width: 100,
      align: 'center',
      render: (_, r) => r.cert_summary?.cert_count ?? 0,
    },
    {
      title: '最近到期',
      key: 'nearest_expiry',
      width: 140,
      render: (_, r) => {
        const d = r.cert_summary?.nearest_expiry
        if (!d) return '-'
        const days = dayjs(d).diff(dayjs(), 'day')
        let color: string | undefined
        if (days < 0) color = 'error'
        else if (days <= 30) color = 'warning'
        return (
          <Space size={4}>
            <span>{dayjs(d).format('YYYY-MM-DD')}</span>
            {days < 0 && <Tag color={color}>已过期</Tag>}
            {days >= 0 && days <= 30 && <Tag color={color}>{days}天内</Tag>}
          </Space>
        )
      },
    },
    {
      title: '风险证数',
      key: 'risk',
      width: 100,
      render: (_, r) => {
        const n = r.cert_summary?.risk_count || 0
        if (!n) return <Tag color="success">0</Tag>
        return (
          <Tag color={r.cert_summary?.risk_level === 'expired' ? 'error' : 'warning'} icon={<WarningOutlined />}>
            {n}
          </Tag>
        )
      },
    },
    {
      title: '在职状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '在职' : status === 'inactive' ? '离职' : status}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      fixed: 'right',
      render: (_, record) => (
        <Space size={0}>
          <Tooltip title="详情 / 持证">
            <Button type="text" icon={<EyeOutlined />} onClick={() => navigate(`/welders/${record.id}`)} />
          </Tooltip>
          <Tooltip title="编辑人员">
            <Button type="text" icon={<EditOutlined />} onClick={() => navigate(`/welders/${record.id}/edit`)} />
          </Tooltip>
          <Tooltip title="删除">
            <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)} />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div className="list-page">
      <ListPageHeader
        title="焊工管理"
        description="一人多体系持证：先建档案，再在详情中按体系添加持证项目"
      />

      <Row gutter={[16, 16]} className="list-stats-row">
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic title="总焊工数" value={total} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small">
            <Statistic
              title="本页持证正常"
              value={validOnPage}
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small" onClick={() => handleCertFilterChange('expiring_soon')} style={{ cursor: 'pointer' }}>
            <Statistic title="本页即将到期" value={riskOnPage} valueStyle={{ color: '#d48806' }} />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card" size="small" onClick={() => handleCertFilterChange('expired')} style={{ cursor: 'pointer' }}>
            <Statistic title="本页已过期" value={expiredOnPage} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      <Card className="list-page-card">
        <div className="doc-list-toolbar">
          <div className="toolbar-search">
            <Search
              placeholder="搜索焊工编号、姓名、电话..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={(v) => {
                setSearchText(v)
                setCurrentPage(1)
              }}
            />
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="技能等级"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={skillLevelFilter}
              onChange={(v) => {
                setSkillLevelFilter(v)
                setCurrentPage(1)
              }}
            >
              <Option value="junior">初级</Option>
              <Option value="intermediate">中级</Option>
              <Option value="senior">高级</Option>
              <Option value="expert">专家</Option>
              <Option value="master">大师</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="在职状态"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={statusFilter}
              onChange={(v) => {
                setStatusFilter(v)
                setCurrentPage(1)
              }}
            >
              <Option value="active">在职</Option>
              <Option value="inactive">离职</Option>
              <Option value="on_leave">休假</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="持证风险"
              allowClear
              size="large"
              style={{ width: '100%' }}
              value={certStatusFilter}
              onChange={handleCertFilterChange}
            >
              <Option value="valid">持证正常</Option>
              <Option value="expiring_soon">30天内到期</Option>
              <Option value="expired">已过期</Option>
              <Option value="none">暂无持证</Option>
            </Select>
          </div>
          <div className="toolbar-actions">
            <Button icon={<RobotOutlined />} size="large" onClick={() => navigate('/smart-import?type=welder&new=1')}>
              AI导入
            </Button>
            <Button type="primary" icon={<PlusOutlined />} size="large" onClick={() => navigate('/welders/create')}>
              新增焊工
            </Button>
            <Button icon={<ReloadOutlined />} size="large" onClick={fetchWelders}>
              刷新
            </Button>
          </div>
        </div>

        <div className="list-table-wrap">
          <Table
            columns={columns}
            dataSource={welders}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1200 }}
            pagination={{
              current: currentPage,
              pageSize,
              total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (t) => `共 ${t} 条`,
              onChange: (page, size) => {
                setCurrentPage(page)
                setPageSize(size)
              },
            }}
          />
        </div>
      </Card>
    </div>
  )
}

export default WeldersList
