import React, { useEffect, useState, useRef } from 'react'
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  message,
} from 'antd'
import {
  DeleteOutlined,
  EditOutlined,
  MinusCircleOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { downloadCsv } from '@/utils/csv'
import { readWorkspaceQuery, reportTemplateApi } from '@/services/businessExtensions'

const sourceOptions = [
  { value: 'wps', label: 'WPS' },
  { value: 'pqr', label: 'PQR' },
  { value: 'quality', label: '质量检验' },
  { value: 'production', label: '生产任务' },
]

const metricOptions = [
  { value: 'count', label: '记录数量' },
]

const parseJsonArray = <T,>(value: unknown, fallback: T[] = []): T[] => {
  if (Array.isArray(value)) return value as T[]
  if (typeof value !== 'string' || !value.trim()) return fallback
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed as T[] : fallback
  } catch {
    return fallback
  }
}

const CustomReportBuilder: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [catalog, setCatalog] = useState<any[]>([])
  const [catalogError, setCatalogError] = useState(false)
  const [saving, setSaving] = useState(false)
  const [open, setOpen] = useState(false)
  const [runOpen, setRunOpen] = useState(false)
  const [runResult, setRunResult] = useState<any>(null)
  const [editing, setEditing] = useState<any | null>(null)
  const [form] = Form.useForm()
  const sources = Form.useWatch('data_sources', form) || []
  const groupFields = catalog.filter(c => sources.includes(c.source)).reduce((common: string[] | null, c: any) => common === null ? c.fields.map((f: any) => f.field) : common.filter(k => c.fields.some((f: any) => f.field === k)), null) || []
  const ws = readWorkspaceQuery()
  const requestVersion = useRef(0)

  const load = async () => {
    const version = ++requestVersion.current
    try {
      setLoading(true)
      const data = await reportTemplateApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      })
      if (version !== requestVersion.current) return
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      if (version !== requestVersion.current) return
      setItems([])
      setTotal(0)
      message.error(err instanceof Error ? err.message : '加载报表模板失败')
    } finally {
      if (version === requestVersion.current) setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    return () => { requestVersion.current += 1 }
  }, [page, pageSize, search])

  const loadCatalog = async () => {
    try { setCatalog(await reportTemplateApi.catalog()); setCatalogError(false) }
    catch { setCatalogError(true) }
  }
  useEffect(() => { void loadCatalog() }, [])
  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ chart_type: 'table', data_sources: ['wps'], metrics: ['count'], filters: [] })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.setFieldsValue({
      ...record,
      data_sources: parseJsonArray<string>(record.data_sources),
      metrics: parseJsonArray<string>(record.metrics, ['count']),
      filters: parseJsonArray<{ field?: string; operator?: string; value?: string }>(record.filters),
    })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      ...values,
      data_sources: JSON.stringify(values.data_sources || []),
      metrics: JSON.stringify(values.metrics || []),
      group_by: values.group_by || null,
      filters: JSON.stringify(values.filters || []),
    }
    setSaving(true)
    try {
      if (editing) {
        await reportTemplateApi.update(ws, editing.id, payload)
        message.success('已更新')
      } else {
        await reportTemplateApi.create(ws, payload)
        message.success('已创建')
      }
      setOpen(false)
      void load()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '保存失败')
    } finally { setSaving(false) }
  }

  const remove = async (id: number) => {
    try {
      await reportTemplateApi.remove(ws, id)
      message.success('已删除')
      void load()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除失败')
    }
  }

  const run = async (id: number) => {
    setRunResult(null); setRunOpen(false)
    try {
      const result = await reportTemplateApi.run(ws, id)
      setRunResult(result)
      setRunOpen(true)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '运行失败')
    }
  }

  return (
    <Card
      title="自定义报表"
      extra={
        <Space>
          <Input.Search
            placeholder="搜索模板名称"
            allowClear
            onSearch={(v) => {
              const value = v.trim()
              if (value === search && page === 1) void load()
              else { setSearch(value); setPage(1) }
            }}
            style={{ width: 220 }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => void load()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建模板
          </Button>
        </Space>
      }
    >
      <Table
        rowKey="id"
        loading={loading}
        dataSource={items}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p, ps) => {
            setPage(p)
            setPageSize(ps)
          },
        }}
        columns={[
          { title: '名称', dataIndex: 'name' },
          { title: '描述', dataIndex: 'description', ellipsis: true },
          {
            title: '图表',
            dataIndex: 'chart_type',
            render: (v: string) => <Tag>{v}</Tag>,
          },
          {
            title: '数据源',
            dataIndex: 'data_sources',
            render: (v: string) => {
              try {
                return JSON.parse(v || '[]').join(', ')
              } catch {
                return v
              }
            },
          },
          {
            title: '操作',
            render: (_: unknown, record: any) => (
              <Space>
                <Button
                  size="small"
                  icon={<PlayCircleOutlined />}
                  onClick={() => void run(record.id)}
                >
                  运行
                </Button>
                <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
                <Popconfirm title="确认删除？" onConfirm={() => void remove(record.id)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? '编辑报表模板' : '新建报表模板'}
        open={open}
        confirmLoading={saving}
        onCancel={() => { if (!saving) setOpen(false) }}
        onOk={() => void submit()}
        width={640}
        destroyOnHidden
        forceRender
      >
        <Form form={form} layout="vertical" disabled={saving}>
          {catalogError && <Alert type="error" message="报表字段加载失败" action={<Button onClick={() => void loadCatalog()}>重试</Button>} />}
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="data_sources" label="数据源" extra="切换数据源会清空旧筛选和分组，请重新选择。" rules={[{ required: true }]}>
            <Select mode="multiple" options={sourceOptions} onChange={() => form.setFieldsValue({ filters: [], group_by: undefined })} />
          </Form.Item>
          <Form.Item name="chart_type" label="图表类型">
            <Select
              options={[
                { value: 'table', label: '表格' },
                { value: 'bar', label: '柱状图' },
                { value: 'line', label: '折线图' },
                { value: 'pie', label: '饼图' },
              ]}
            />
          </Form.Item>
          <Form.Item name="metrics" label="统计指标" rules={[{ required: true, message: '请选择统计指标' }]}>
            <Select mode="multiple" options={metricOptions} placeholder="选择要统计的指标" />
          </Form.Item>
          <Form.Item name="group_by" label="分组字段" extra="仅显示所选数据源共同支持的字段；不选则汇总总数。"><Select allowClear options={groupFields.map((field: string) => ({ value: field, label: field }))} /></Form.Item>
          <Form.Item label="筛选条件" extra="不填写则统计所选数据源的全部记录">
            <Form.List name="filters">
              {(fields, { add, remove }) => (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {fields.map(field => (
                    <Space key={field.key} align="baseline" wrap>
                      <Form.Item name={[field.name, 'source']} rules={[{ required: true, message: '请选择数据源' }]}>
                        <Select placeholder="数据源" style={{ width: 130 }} options={sourceOptions.filter(s => sources.includes(s.value))} onChange={() => { form.setFieldValue(['filters', field.name, 'field'], undefined); form.setFieldValue(['filters', field.name, 'operator'], 'eq') }} />
                      </Form.Item>
                      <Form.Item noStyle shouldUpdate>
                        {({ getFieldValue }) => {
                          const source = catalog.find(c => c.source === getFieldValue(['filters', field.name, 'source']))
                          const spec = source?.fields.find((f: any) => f.field === getFieldValue(['filters', field.name, 'field']))
                          return <>
                            <Form.Item name={[field.name, 'field']} rules={[{ required: true, message: '请选择字段' }]}>
                              <Select placeholder="筛选字段" style={{ width: 160 }} options={(source?.fields || []).map((f: any) => ({ value: f.field, label: `${f.field} (${f.type})` }))} onChange={() => form.setFieldValue(['filters', field.name, 'operator'], 'eq')} />
                            </Form.Item>
                            <Form.Item name={[field.name, 'operator']} initialValue="eq"><Select style={{ width: 110 }} options={(spec?.operators || ['eq']).map((op: string) => ({ value: op, label: ({ eq: '等于', contains: '包含', gte: '大于等于', lte: '小于等于' } as Record<string, string>)[op] }))} /></Form.Item>
                          </>
                        }}
                      </Form.Item>
                      <Form.Item name={[field.name, 'value']} rules={[{ required: true, message: '请输入值' }]}>
                        <Input placeholder="筛选值" style={{ width: 160 }} />
                      </Form.Item>
                      <Button type="text" danger icon={<MinusCircleOutlined />} onClick={() => remove(field.name)} aria-label="删除筛选条件" />
                    </Space>
                  ))}
                  <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ source: sources[0], operator: 'eq' })} block>添加筛选条件</Button>
                </Space>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="运行结果"
        open={runOpen}
        onCancel={() => setRunOpen(false)}
        footer={<Space><Button disabled={!runResult} onClick={() => downloadCsv(runResult.name || '自定义报表', ['数据源', '分组', '记录数', '说明', '生成时间', '统计范围'], (runResult.results || []).map((r: any) => [r.source, r.group, r.total, r.note, runResult.generated_at, JSON.stringify(runResult.scope)]))}>导出 CSV</Button><Button onClick={() => setRunOpen(false)}>关闭</Button></Space>}
      >
        {runResult ? (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert type="info" message={runResult.definition} />
            <div><b>{runResult.name || '自定义报表'}</b></div>
            <Table<{ source: string; total: number; note?: string }>
              rowKey={(record: any) => `${record.source}-${record.group}`}
              size="small"
              pagination={false}
              dataSource={(runResult.results || []) as { source: string; total: number; note?: string }[]}
              columns={[
                { title: '数据源', dataIndex: 'source', render: (v: string) => sourceOptions.find(item => item.value === v)?.label || v },
                { title: '分组', dataIndex: 'group' },
                { title: '记录数量', dataIndex: 'total' },
                { title: '说明', dataIndex: 'note', render: (v?: string) => v === 'unsupported' ? '暂不支持' : (v || '—') },
              ]}
            />
            <span style={{ color: '#64748b' }}>生成时间：{runResult.generated_at ? new Date(runResult.generated_at).toLocaleString() : '—'}</span>
          </Space>
        ) : '暂无结果'}
      </Modal>
    </Card>
  )
}

export default CustomReportBuilder
