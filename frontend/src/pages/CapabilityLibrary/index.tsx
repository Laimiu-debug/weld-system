import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  CheckCircleOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  LinkOutlined,
  PlusOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  TeamOutlined,
  ToolOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import {
  capabilityService,
  CapabilityCheckRequest,
  CapabilityCheckResult,
  CapabilityFilters,
  CapabilityOverview,
} from '@/services/capability'
import './capabilityLibrary.css'

const { Title, Text, Paragraph } = Typography

type DataRow = Record<string, any>

const healthLabels = {
  healthy: { text: '健康', color: '#16a34a' },
  attention: { text: '需关注', color: '#d97706' },
  risk: { text: '有风险', color: '#dc2626' },
}

const decisionLabels = {
  capable: { text: '工艺、人员及资源均具备', status: 'success' as const },
  needs_resources: { text: '工艺与人员具备，资源待补充', status: 'warning' as const },
  not_capable: { text: '当前不具备完整能力', status: 'error' as const },
}

const CapabilityLibraryPage: React.FC = () => {
  const navigate = useNavigate()
  const [filterForm] = Form.useForm<CapabilityFilters>()
  const [checkForm] = Form.useForm<CapabilityCheckRequest>()
  const [overview, setOverview] = useState<CapabilityOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('process')
  const [detail, setDetail] = useState<DataRow | null>(null)
  const [detailType, setDetailType] = useState('process')
  const [checkOpen, setCheckOpen] = useState(false)
  const [checking, setChecking] = useState(false)
  const [checkResult, setCheckResult] = useState<CapabilityCheckResult | null>(null)

  const loadOverview = useCallback(async (filters: CapabilityFilters = {}) => {
    setLoading(true)
    try {
      setOverview(await capabilityService.getOverview(filters))
    } catch {
      message.error('加载企业焊接能力库失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  const openDetail = (type: string, row: DataRow) => {
    setDetailType(type)
    setDetail(row)
  }

  const submitCheck = async (values: CapabilityCheckRequest) => {
    setChecking(true)
    try {
      setCheckResult(await capabilityService.check(values))
    } catch {
      message.error('能力校核失败，请检查输入后重试')
    } finally {
      setChecking(false)
    }
  }

  const processColumns: ColumnsType<DataRow> = [
    {
      title: '工艺能力',
      key: 'procedure',
      width: 220,
      render: (_, row) => (
        <Button type="link" className="capability-link" onClick={() => openDetail('process', row)}>
          {row.wps_number} / {row.pqr_number}
        </Button>
      ),
    },
    {
      title: '方法',
      dataIndex: 'supported_processes',
      width: 150,
      render: (items: string[]) => tagList(items, 'blue'),
    },
    {
      title: '材料组',
      key: 'materials',
      width: 150,
      render: (_, row) => tagList(row.qualified_scope?.material_groups, 'geekblue'),
    },
    {
      title: '厚度范围',
      key: 'thickness',
      width: 150,
      render: (_, row) => formatRange(row.qualified_scope?.thickness, 'mm'),
    },
    {
      title: '位置',
      key: 'positions',
      width: 130,
      render: (_, row) => tagList(row.qualified_scope?.positions, 'cyan'),
    },
    {
      title: '资源关联',
      key: 'resources',
      width: 190,
      render: (_, row) => (
        <Space size={4} wrap>
          <Tag icon={<TeamOutlined />}>焊工 {row.resource_links?.welder_count ?? 0}</Tag>
          <Tag icon={<DatabaseOutlined />}>焊材 {row.resource_links?.material_count ?? 0}</Tag>
          <Tag icon={<ToolOutlined />}>设备 {row.resource_links?.equipment_count ?? 0}</Tag>
        </Space>
      ),
    },
    {
      title: '规则版本',
      dataIndex: 'rule_pack_version',
      width: 110,
      render: (value) => <Tag color="purple">v{value}</Tag>,
    },
  ]

  const wpsColumns: ColumnsType<DataRow> = [
    {
      title: 'WPS 编号',
      dataIndex: 'number',
      width: 180,
      render: (value, row) => (
        <Button type="link" className="capability-link" onClick={() => openDetail('wps', row)}>
          {value}
        </Button>
      ),
    },
    { title: '版本', dataIndex: 'revision', width: 80 },
    { title: '焊接方法', dataIndex: 'welding_process', width: 130 },
    { title: '材料组', dataIndex: 'material_group', width: 130 },
    {
      title: '有效 PQR 支持',
      dataIndex: 'valid_support_count',
      width: 130,
      render: (value) => <Badge count={value} showZero color={value ? '#16a34a' : '#dc2626'} />,
    },
    {
      title: '状态',
      dataIndex: 'health_status',
      width: 120,
      render: (value) => (
        <Tag color={value === 'valid' ? 'success' : value === 'unsupported' ? 'error' : 'default'}>
          {value === 'valid' ? '有效' : value === 'unsupported' ? '无有效支持' : '未启用'}
        </Tag>
      ),
    },
    {
      title: '来源文件',
      dataIndex: 'source_documents',
      width: 100,
      render: (items: any[]) => items?.length || 0,
    },
    {
      title: '操作',
      key: 'action',
      width: 90,
      render: (_, row) => <Button onClick={() => navigate(`/wps/${row.id}`)}>查看</Button>,
    },
  ]

  const pqrColumns: ColumnsType<DataRow> = [
    {
      title: 'PQR 编号',
      dataIndex: 'number',
      width: 180,
      render: (value, row) => (
        <Button type="link" className="capability-link" onClick={() => openDetail('pqr', row)}>
          {value}
        </Button>
      ),
    },
    { title: '焊接方法', dataIndex: 'welding_process', width: 130 },
    { title: '材料组', dataIndex: 'material_group', width: 130 },
    {
      title: '资格结果',
      dataIndex: 'qualification_outcome',
      width: 130,
      render: (value) => (
        <Tag color={value === 'qualified' ? 'success' : value ? 'warning' : 'default'}>
          {value === 'qualified' ? '明确合格' : value || '未计算'}
        </Tag>
      ),
    },
    { title: '规则版本', dataIndex: 'rule_pack_version', width: 110 },
    { title: '支持 WPS', dataIndex: 'supported_wps_count', width: 100 },
    {
      title: '操作',
      key: 'action',
      width: 90,
      render: (_, row) => <Button onClick={() => navigate(`/pqr/${row.id}`)}>查看</Button>,
    },
  ]

  const welderColumns: ColumnsType<DataRow> = [
    {
      title: '焊工',
      key: 'welder',
      width: 200,
      render: (_, row) => (
        <Button type="link" className="capability-link" onClick={() => openDetail('welder', row)}>
          {row.full_name} · {row.welder_code}
        </Button>
      ),
    },
    {
      title: '当前有效',
      dataIndex: 'is_currently_valid',
      width: 110,
      render: (value) => <Tag color={value ? 'success' : 'error'}>{value ? '有效' : '不可用'}</Tag>,
    },
    {
      title: '证书风险',
      dataIndex: 'expiry_risk',
      width: 120,
      render: (value) => (
        <Tag color={value === 'normal' ? 'success' : value === 'expiring_soon' ? 'warning' : 'error'}>
          {value === 'normal' ? '正常' : value === 'expiring_soon' ? '即将到期' : '已过期'}
        </Tag>
      ),
    },
    { title: '最近到期日', dataIndex: 'next_expiry_date', width: 130, render: (value) => value || '未填写' },
    {
      title: '有效项目',
      dataIndex: 'qualifications',
      render: (items: any[]) => (
        <Space size={[4, 4]} wrap>
          {(items || []).slice(0, 4).map((item, index) => (
            <Tag key={`${item.certification_number}-${index}`}>
              {[item.process, item.material_group, item.position].filter(Boolean).join(' / ') || '资料不完整'}
            </Tag>
          ))}
          {(items || []).length > 4 && <Text type="secondary">+{items.length - 4}</Text>}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 90,
      render: (_, row) => <Button onClick={() => navigate(`/welders/${row.id}`)}>查看</Button>,
    },
  ]

  const tabItems = useMemo(
    () => [
      {
        key: 'process',
        label: `工艺能力 (${overview?.process_capabilities.length || 0})`,
        children: (
          <Table
            rowKey="link_id"
            columns={processColumns}
            dataSource={overview?.process_capabilities || []}
            scroll={{ x: 1100 }}
            pagination={{ pageSize: 10, showSizeChanger: true }}
          />
        ),
      },
      {
        key: 'wps',
        label: `WPS (${overview?.wps_records.length || 0})`,
        children: <Table rowKey="id" columns={wpsColumns} dataSource={overview?.wps_records || []} scroll={{ x: 900 }} />,
      },
      {
        key: 'pqr',
        label: `PQR (${overview?.pqr_records.length || 0})`,
        children: <Table rowKey="id" columns={pqrColumns} dataSource={overview?.pqr_records || []} scroll={{ x: 800 }} />,
      },
      {
        key: 'welder',
        label: `焊工 (${overview?.welders.length || 0})`,
        children: <Table rowKey="id" columns={welderColumns} dataSource={overview?.welders || []} scroll={{ x: 900 }} />,
      },
    ],
    [overview]
  )

  const health = overview?.health
  const healthMeta = healthLabels[health?.status || 'risk']

  return (
    <div className="capability-page">
      <div className="capability-header">
        <div>
          <Space align="center" size={12}>
            <SafetyCertificateOutlined className="capability-title-icon" />
            <Title level={2}>企业焊接能力库</Title>
          </Space>
          <Paragraph type="secondary">
            仅展示已批准、未停用且具有当前有效 PQR 支持链的能力。边界与资料不足不会计为可用。
          </Paragraph>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={() => void loadOverview(filterForm.getFieldsValue())}>
            刷新
          </Button>
          <Button type="primary" icon={<SearchOutlined />} onClick={() => setCheckOpen(true)}>
            典型焊缝能力校核
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} className="capability-summary">
          <Col xs={24} md={8} xl={5}>
            <Card className="health-card">
              <Text type="secondary">数据健康度</Text>
              <div className="health-content">
                <Progress
                  type="circle"
                  size={88}
                  percent={health?.score || 0}
                  strokeColor={healthMeta.color}
                />
                <div>
                  <Title level={4} style={{ color: healthMeta.color }}>{healthMeta.text}</Title>
                  <Text type="secondary">{health?.blocking_issue_count || 0} 项阻断 · {health?.warning_count || 0} 项提醒</Text>
                </div>
              </div>
            </Card>
          </Col>
          <SummaryCard title="有效 WPS" value={overview?.summary.valid_wps || 0} hint="具有有效 PQR 支持" icon={<CheckCircleOutlined />} />
          <SummaryCard title="合格 PQR" value={overview?.summary.qualified_pqr || 0} hint="当前规则结果明确合格" icon={<FileSearchOutlined />} />
          <SummaryCard title="有效焊工" value={overview?.summary.active_welders || 0} hint="证书与人员状态均有效" icon={<TeamOutlined />} />
          <SummaryCard title="待审核关系" value={overview?.summary.pending_reviews || 0} hint="不计入当前能力" icon={<WarningOutlined />} tone="warning" />
        </Row>

        <Card className="filter-card">
          <Form
            form={filterForm}
            layout="vertical"
            onFinish={(values) => void loadOverview(values)}
          >
            <Row gutter={12} align="bottom">
              <Col xs={24} md={8} xl={5}>
                <Form.Item name="search" label="编号或名称">
                  <Input allowClear prefix={<SearchOutlined />} placeholder="WPS、PQR 或焊工" />
                </Form.Item>
              </Col>
              <Col xs={12} md={8} xl={4}>
                <Form.Item name="process" label="焊接方法">
                  <Select allowClear options={selectOptions(overview?.dimensions.processes)} />
                </Form.Item>
              </Col>
              <Col xs={12} md={8} xl={4}>
                <Form.Item name="material_group" label="材料组">
                  <Select allowClear options={selectOptions(overview?.dimensions.material_groups)} />
                </Form.Item>
              </Col>
              <Col xs={12} md={8} xl={4}>
                <Form.Item name="position" label="焊接位置">
                  <Select allowClear options={selectOptions(overview?.dimensions.positions)} />
                </Form.Item>
              </Col>
              <Col xs={12} md={8} xl={3}>
                <Form.Item name="factory_id" label="工厂 ID">
                  <InputNumber min={1} precision={0} style={{ width: '100%' }} placeholder="全部" />
                </Form.Item>
              </Col>
              <Col xs={24} md={8} xl={4}>
                <Form.Item>
                  <Space>
                    <Button type="primary" htmlType="submit">筛选</Button>
                    <Button onClick={() => { filterForm.resetFields(); void loadOverview() }}>重置</Button>
                  </Space>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Card>

        {!!overview?.issues.length && (
          <Card title="数据风险与待办" className="issue-card" extra={<Tag color="orange">{overview.issues.length} 项</Tag>}>
            <List
              dataSource={overview.issues.slice(0, 8)}
              renderItem={(issue) => (
                <List.Item
                  actions={issue.entity_id ? [
                    <Button key="view" type="link" onClick={() => navigate(`/${issue.entity_type}/${issue.entity_id}`)}>处理</Button>,
                  ] : undefined}
                >
                  <List.Item.Meta
                    avatar={issue.severity === 'blocking' ? <WarningOutlined className="issue-blocking" /> : <WarningOutlined className="issue-warning" />}
                    title={<Space><span>{issue.message}</span><Tag>{issue.label}</Tag></Space>}
                    description={issue.code}
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        <Card className="capability-table-card">
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        </Card>

        <Card title="支持资源" className="resource-card">
          <Row gutter={[16, 16]}>
            <ResourceSummary icon={<DatabaseOutlined />} title="可用焊材" ready={overview?.summary.available_materials || 0} total={overview?.materials.length || 0} />
            <ResourceSummary icon={<ToolOutlined />} title="可用设备" ready={overview?.summary.available_equipment || 0} total={overview?.equipment.length || 0} />
            <Col xs={24} md={8}>
              <div className="gap-actions">
                <Text strong>发现能力缺口？</Text>
                <Text type="secondary">导入企业已有资料，或创建新的预焊接工艺规程。</Text>
                <Space wrap>
                  <Button icon={<LinkOutlined />} onClick={() => navigate('/smart-import')}>智能导入</Button>
                  <Button icon={<PlusOutlined />} onClick={() => navigate('/ppqr/create')}>新建 pPQR</Button>
                </Space>
              </div>
            </Col>
          </Row>
        </Card>
      </Spin>

      <Drawer
        width={640}
        open={!!detail}
        onClose={() => setDetail(null)}
        title="能力详情与证据链"
      >
        {detail ? <CapabilityDetail type={detailType} record={detail} /> : <Empty />}
      </Drawer>

      <Drawer
        width={620}
        open={checkOpen}
        onClose={() => setCheckOpen(false)}
        title="典型焊缝能力校核"
        extra={<Button onClick={() => { checkForm.resetFields(); setCheckResult(null) }}>清空</Button>}
      >
        <Alert
          type="info"
          showIcon
          message="只有工艺范围、有效焊工资质和资源均明确覆盖时，系统才会判定完整具备。"
          className="check-alert"
        />
        <Form
          form={checkForm}
          layout="vertical"
          initialValues={{ pwht_required: false, impact_required: false }}
          onFinish={(values) => void submitCheck(values)}
        >
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="welding_process" label="焊接方法" rules={[{ required: true }]}>
                <Select showSearch options={selectOptions(overview?.dimensions.processes)} placeholder="例如 GTAW" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="material_group" label="材料组" rules={[{ required: true }]}>
                <Select showSearch options={selectOptions(overview?.dimensions.material_groups)} placeholder="例如 Fe-1" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="thickness_mm" label="厚度（mm）" rules={[{ required: true }]}>
                <InputNumber min={0.001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="diameter_mm" label="管径（mm，可选）">
                <InputNumber min={0.001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="welding_position" label="焊接位置" rules={[{ required: true }]}>
                <Select showSearch options={selectOptions(overview?.dimensions.positions)} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="factory_id" label="限定工厂 ID">
                <InputNumber min={1} precision={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}><Form.Item name="pwht_required" label="要求 PWHT" valuePropName="checked"><Switch /></Form.Item></Col>
            <Col span={12}><Form.Item name="impact_required" label="要求冲击试验" valuePropName="checked"><Switch /></Form.Item></Col>
            <Col span={12}>
              <Form.Item name="impact_temperature_c" label="冲击温度（℃）">
                <InputNumber min={-273.15} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Button type="primary" htmlType="submit" loading={checking} block>开始校核</Button>
        </Form>
        {checkResult && <CheckResult result={checkResult} onNavigate={navigate} />}
      </Drawer>
    </div>
  )
}

const SummaryCard: React.FC<{ title: string; value: number; hint: string; icon: React.ReactNode; tone?: 'warning' }> = ({ title, value, hint, icon, tone }) => (
  <Col xs={12} md={8} xl={4}>
    <Card className={`metric-card ${tone ? 'metric-warning' : ''}`}>
      <div className="metric-icon">{icon}</div>
      <Title level={2}>{value}</Title>
      <Text strong>{title}</Text>
      <Text type="secondary">{hint}</Text>
    </Card>
  </Col>
)

const ResourceSummary: React.FC<{ icon: React.ReactNode; title: string; ready: number; total: number }> = ({ icon, title, ready, total }) => (
  <Col xs={24} md={8}>
    <div className="resource-summary">
      <div className="resource-icon">{icon}</div>
      <div><Title level={4}>{title}</Title><Text><strong>{ready}</strong> / {total} 当前可用</Text></div>
    </div>
  </Col>
)

const CapabilityDetail: React.FC<{ type: string; record: DataRow }> = ({ type, record }) => {
  if (type === 'process') {
    const scope = record.qualified_scope || {}
    const evidence = record.evidence || {}
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="WPS">{record.wps_number} · {record.wps_revision}</Descriptions.Item>
          <Descriptions.Item label="PQR">{record.pqr_number}</Descriptions.Item>
          <Descriptions.Item label="规则版本">{record.rule_pack_version}</Descriptions.Item>
          <Descriptions.Item label="方法">{tagList(scope.welding_processes, 'blue')}</Descriptions.Item>
          <Descriptions.Item label="材料组">{tagList(scope.material_groups, 'geekblue')}</Descriptions.Item>
          <Descriptions.Item label="厚度">{formatRange(scope.thickness, 'mm')}</Descriptions.Item>
          <Descriptions.Item label="直径">{formatDiameter(scope.diameter)}</Descriptions.Item>
          <Descriptions.Item label="位置">{tagList(scope.positions, 'cyan')}</Descriptions.Item>
          <Descriptions.Item label="PWHT">{scope.pwht?.performed ? '按已试验 PWHT 条件' : '未进行 PWHT'}</Descriptions.Item>
          <Descriptions.Item label="冲击">{scope.impact?.required ? `已试验 ${scope.impact.tested_temperature_c ?? '-'}℃` : '未要求'}</Descriptions.Item>
        </Descriptions>
        <EvidenceList evidence={evidence} />
      </Space>
    )
  }
  if (type === 'welder') {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="焊工">{record.full_name} · {record.welder_code}</Descriptions.Item>
          <Descriptions.Item label="有效状态">{record.is_currently_valid ? '当前有效' : '不可用于能力判定'}</Descriptions.Item>
          <Descriptions.Item label="最近到期日">{record.next_expiry_date || '未填写'}</Descriptions.Item>
        </Descriptions>
        <List
          header={<Text strong>有效资质项目</Text>}
          dataSource={record.qualifications || []}
          locale={{ emptyText: '没有完整且当前有效的资质项目' }}
          renderItem={(item: any) => (
            <List.Item>
              <List.Item.Meta
                title={item.certification_number}
                description={[item.process, item.material_group, item.thickness_range, item.position].filter(Boolean).join(' · ')}
              />
            </List.Item>
          )}
        />
      </Space>
    )
  }
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Descriptions bordered column={1} size="small">
        <Descriptions.Item label="编号">{record.number}</Descriptions.Item>
        <Descriptions.Item label="名称">{record.title}</Descriptions.Item>
        <Descriptions.Item label="状态">{record.status}</Descriptions.Item>
        <Descriptions.Item label="焊接方法">{record.welding_process || '未填写'}</Descriptions.Item>
        <Descriptions.Item label="材料组">{record.material_group || '未填写'}</Descriptions.Item>
      </Descriptions>
      <List
        header={<Text strong>原始文档证据</Text>}
        dataSource={record.source_documents || []}
        locale={{ emptyText: '该记录由人工创建，未关联智能导入原始文档' }}
        renderItem={(item: any) => <List.Item><List.Item.Meta title={item.filename} description={`版本 ${item.document_version || '-'} · SHA-256 ${item.sha256}`} /></List.Item>}
      />
    </Space>
  )
}

const EvidenceList: React.FC<{ evidence: DataRow }> = ({ evidence }) => (
  <div>
    <Title level={4}>证据链</Title>
    <Descriptions bordered column={1} size="small">
      <Descriptions.Item label="WPS 精确版本">{evidence.wps_version_key}</Descriptions.Item>
      <Descriptions.Item label="PQR 精确版本">{evidence.pqr_version_key}</Descriptions.Item>
      <Descriptions.Item label="资格计算结果">{evidence.qualification_result_id}</Descriptions.Item>
    </Descriptions>
    <List
      header={<Text strong>规则依据</Text>}
      dataSource={evidence.basis || []}
      locale={{ emptyText: '无规则依据' }}
      renderItem={(item: any) => <List.Item><List.Item.Meta title={item.rule_id} description={`${item.standard || ''} · ${item.locator || ''}`} /></List.Item>}
    />
    <List
      header={<Text strong>原始文档</Text>}
      dataSource={evidence.source_documents || []}
      locale={{ emptyText: '人工创建记录，无智能导入原始文档' }}
      renderItem={(item: any) => <List.Item><List.Item.Meta title={item.filename} description={`版本 ${item.document_version || '-'} · ${item.sha256}`} /></List.Item>}
    />
  </div>
)

const CheckResult: React.FC<{ result: CapabilityCheckResult; onNavigate: (path: string) => void }> = ({ result, onNavigate }) => {
  const meta = decisionLabels[result.decision]
  return (
    <div className="check-result" aria-live="polite">
      <Alert type={meta.status} showIcon message={meta.text} description={result.explanation.join('；') || '请查看缺口明细'} />
      <Row gutter={8} className="check-status-row">
        <Col span={8}><StatusBlock label="工艺能力" ready={result.process_capable} /></Col>
        <Col span={8}><StatusBlock label="人员能力" ready={result.personnel_capable} /></Col>
        <Col span={8}><StatusBlock label="资源就绪" ready={result.resource_ready} /></Col>
      </Row>
      {!!result.gaps.length && (
        <List
          header={<Text strong>能力缺口</Text>}
          dataSource={result.gaps}
          renderItem={(gap) => <List.Item><List.Item.Meta avatar={<WarningOutlined className={gap.severity === 'blocking' ? 'issue-blocking' : 'issue-warning'} />} title={gap.message} description={gap.code} /></List.Item>}
        />
      )}
      <Space wrap>
        <Button onClick={() => onNavigate('/smart-import')}>导入已有资料</Button>
        <Button onClick={() => onNavigate('/ppqr/create')}>创建 pPQR</Button>
      </Space>
    </div>
  )
}

const StatusBlock: React.FC<{ label: string; ready: boolean }> = ({ label, ready }) => (
  <div className={ready ? 'status-block status-ready' : 'status-block status-missing'}>
    {ready ? <CheckCircleOutlined /> : <WarningOutlined />}
    <Text strong>{label}</Text>
    <Text>{ready ? '具备' : '缺失'}</Text>
  </div>
)

function selectOptions(items?: string[]) {
  return (items || []).map((value) => ({ label: value, value }))
}

function tagList(items?: string[], color?: string) {
  if (!items?.length) return <Text type="secondary">未填写</Text>
  return <Space size={[4, 4]} wrap>{items.map((item) => <Tag color={color} key={item}>{item}</Tag>)}</Space>
}

function formatRange(value?: Record<string, any>, unit = '') {
  if (value?.min_mm == null || value?.max_mm == null) return '未计算'
  return `${value.min_mm}–${value.max_mm} ${unit}`
}

function formatDiameter(value?: Record<string, any>) {
  if (!value) return '未计算'
  if (value.applicable === false) return '板材试件，不适用'
  if (value.min_mm == null || value.max_mm == null) return '资料不足'
  return `${value.min_mm}–${value.max_mm} mm`
}

export default CapabilityLibraryPage
