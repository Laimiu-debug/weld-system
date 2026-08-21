import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  message,
} from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { productionPlanApi, readWorkspaceQuery } from '@/services/businessExtensions'

const statusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'approved', label: '已批准' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]

const ProductionPlanManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)
  const [form] = Form.useForm()
  const ws = readWorkspaceQuery()

  const load = async () => {
    try {
      setLoading(true)
      const data = await productionPlanApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        status,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '加载生产计划失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [page, pageSize, status])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ status: 'draft', priority: 'normal', progress_percentage: 0 })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.setFieldsValue({
      ...record,
      plan_start_date: record.plan_start_date ? dayjs(record.plan_start_date) : undefined,
      plan_end_date: record.plan_end_date ? dayjs(record.plan_end_date) : undefined,
    })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      ...values,
      plan_start_date: values.plan_start_date?.format('YYYY-MM-DD'),
      plan_end_date: values.plan_end_date?.format('YYYY-MM-DD'),
    }
    try {
      if (editing) {
        await productionPlanApi.update(ws, editing.id, payload)
        message.success('已更新')
      } else {
        await productionPlanApi.create(ws, payload)
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
      await productionPlanApi.remove(ws, id)
      message.success('已删除')
      void load()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <Card
      title="生产计划"
      bordered={false}
      styles={{ body: { paddingTop: 12 } }}
      extra={
        <Space>
          <Input.Search
            placeholder="搜索编号/名称"
            allowClear
            onSearch={(v) => {
              setSearch(v)
              setPage(1)
              void load()
            }}
            style={{ width: 220 }}
          />
          <Select
            allowClear
            placeholder="状态"
            options={statusOptions}
            style={{ width: 140 }}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => void load()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建计划
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
          { title: '编号', dataIndex: 'plan_number' },
          { title: '名称', dataIndex: 'plan_name' },
          { title: '类型', dataIndex: 'plan_type' },
          {
            title: '状态',
            dataIndex: 'status',
            render: (v: string) => <Tag>{v}</Tag>,
          },
          { title: '开始', dataIndex: 'plan_start_date' },
          { title: '结束', dataIndex: 'plan_end_date' },
          {
            title: '进度',
            dataIndex: 'progress_percentage',
            render: (v: number) => `${v ?? 0}%`,
          },
          {
            title: '操作',
            render: (_: unknown, record: any) => (
              <Space>
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
        title={editing ? '编辑生产计划' : '新建生产计划'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => void submit()}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="plan_number" label="计划编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="plan_name" label="计划名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Space size="large" style={{ display: 'flex' }} wrap>
            <Form.Item name="plan_type" label="计划类型">
              <Input style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="priority" label="优先级">
              <Select
                style={{ width: 160 }}
                options={[
                  { value: 'low', label: '低' },
                  { value: 'normal', label: '普通' },
                  { value: 'high', label: '高' },
                  { value: 'urgent', label: '紧急' },
                ]}
              />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select style={{ width: 160 }} options={statusOptions} />
            </Form.Item>
          </Space>
          <Space size="large" wrap>
            <Form.Item name="plan_start_date" label="开始日期" rules={[{ required: true }]}>
              <DatePicker />
            </Form.Item>
            <Form.Item name="plan_end_date" label="结束日期" rules={[{ required: true }]}>
              <DatePicker />
            </Form.Item>
            <Form.Item name="progress_percentage" label="进度(%)">
              <InputNumber min={0} max={100} />
            </Form.Item>
            <Form.Item name="planned_quantity" label="计划数量">
              <InputNumber min={0} />
            </Form.Item>
            <Form.Item name="unit" label="单位">
              <Input style={{ width: 120 }} />
            </Form.Item>
          </Space>
          <Form.Item name="assigned_team" label="负责团队">
            <Input />
          </Form.Item>
          <Form.Item name="quality_standards" label="质量标准">
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="objectives" label="目标">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default ProductionPlanManagement
