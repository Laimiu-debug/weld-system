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
    form.setFieldsValue({ chart_type: 'table', data_sources: ['wps'] })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    let sources: string[] = []
    try {
      sources = JSON.parse(record.data_sources || '[]')
    } catch {
      sources = []
    }
    form.setFieldsValue({ ...record, data_sources: sources })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      ...values,
      data_sources: JSON.stringify(values.data_sources || []),
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
        destroyOnClose
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
          <Form.Item name="metrics" label="指标配置（JSON，可选）">
            <Input.TextArea rows={2} placeholder='例如 ["count"]' />
          </Form.Item>
          <Form.Item name="filters" label="筛选配置（JSON，可选）">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="运行结果"
        open={runOpen}
        onCancel={() => setRunOpen(false)}
        footer={<Button onClick={() => setRunOpen(false)}>关闭</Button>}
      >
        <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(runResult, null, 2)}</pre>
      </Modal>
    </Card>
  )
}

export default CustomReportBuilder
