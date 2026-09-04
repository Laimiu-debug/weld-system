import React, { useEffect, useState } from 'react'
import {
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
  const [open, setOpen] = useState(false)
  const [runOpen, setRunOpen] = useState(false)
  const [runResult, setRunResult] = useState<any>(null)
  const [editing, setEditing] = useState<any | null>(null)
  const [form] = Form.useForm()
  const ws = readWorkspaceQuery()

  const load = async () => {
    try {
      setLoading(true)
      const data = await reportTemplateApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '加载报表模板失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [page, pageSize])

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
      filters: JSON.stringify(values.filters || []),
    }
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
    }
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
              setSearch(v)
              setPage(1)
              void load()
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
        onCancel={() => setOpen(false)}
        onOk={() => void submit()}
        width={640}
        destroyOnHidden
        forceRender
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="data_sources" label="数据源" rules={[{ required: true }]}>
            <Select mode="multiple" options={sourceOptions} />
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
          <Form.Item label="筛选条件" extra="不填写则统计所选数据源的全部记录">
            <Form.List name="filters">
              {(fields, { add, remove }) => (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {fields.map(field => (
                    <Space key={field.key} align="baseline" wrap>
                      <Form.Item name={[field.name, 'field']} rules={[{ required: true, message: '请输入字段' }]}>
                        <Input placeholder="字段，如 status" style={{ width: 150 }} />
                      </Form.Item>
                      <Form.Item name={[field.name, 'operator']} initialValue="eq">
                        <Select style={{ width: 110 }} options={[
                          { value: 'eq', label: '等于' },
                          { value: 'contains', label: '包含' },
                          { value: 'gte', label: '大于等于' },
                          { value: 'lte', label: '小于等于' },
                        ]} />
                      </Form.Item>
                      <Form.Item name={[field.name, 'value']} rules={[{ required: true, message: '请输入值' }]}>
                        <Input placeholder="筛选值" style={{ width: 160 }} />
                      </Form.Item>
                      <Button type="text" danger icon={<MinusCircleOutlined />} onClick={() => remove(field.name)} aria-label="删除筛选条件" />
                    </Space>
                  ))}
                  <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ operator: 'eq' })} block>添加筛选条件</Button>
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
        footer={<Button onClick={() => setRunOpen(false)}>关闭</Button>}
      >
        {runResult ? (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div><b>{runResult.name || '自定义报表'}</b></div>
            <Table<{ source: string; total: number; note?: string }>
              rowKey={(record) => record.source}
              size="small"
              pagination={false}
              dataSource={(runResult.results || []) as { source: string; total: number; note?: string }[]}
              columns={[
                { title: '数据源', dataIndex: 'source', render: (v: string) => sourceOptions.find(item => item.value === v)?.label || v },
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
