import React, { useEffect, useState, useRef } from 'react'
import {
  Alert,
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
  const [overdue, setOverdue] = useState<boolean | undefined>()
  const [taskPlan, setTaskPlan] = useState<any>(null)
  const [taskOptions, setTaskOptions] = useState<any[]>([])
  const [taskIds, setTaskIds] = useState<number[]>([])
  const [taskLoading, setTaskLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)
  const [form] = Form.useForm()
  const ws = readWorkspaceQuery()
  const requestVersion = useRef(0)

  const load = async () => {
    const version = ++requestVersion.current
    try {
      setLoading(true)
      const data = await productionPlanApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        status,
        overdue,
      })
      if (version !== requestVersion.current) return
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      if (version !== requestVersion.current) return
      setItems([])
      setTotal(0)
      message.error(err instanceof Error ? err.message : '加载生产计划失败')
    } finally {
      if (version === requestVersion.current) setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    return () => { requestVersion.current += 1 }
  }, [page, pageSize, status, search, overdue])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ status: 'draft', priority: 'normal' })
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
    const { progress_percentage, tasks, ...writable } = values
    const payload = {
      ...writable,
      plan_start_date: values.plan_start_date?.format('YYYY-MM-DD'),
      plan_end_date: values.plan_end_date?.format('YYYY-MM-DD'),
    }
    setSaving(true)
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
    } finally { setSaving(false) }
  }

  const openTasks = async (record: any) => {
    setTaskLoading(true)
    try {
      const options = await productionPlanApi.taskOptions(ws, record.id)
      setTaskOptions(options)
      setTaskIds(options.filter(t => t.plan_id === record.id).map(t => t.id))
      setTaskPlan(record)
    } catch (err) { message.error(err instanceof Error ? err.message : '加载任务失败') }
    finally { setTaskLoading(false) }
  }
  const saveTasks = async () => {
    setSaving(true)
    try { await productionPlanApi.setTasks(ws, taskPlan.id, taskIds); setTaskPlan(null); void load() }
    catch (err) { message.error(err instanceof Error ? err.message : '关联失败') }
    finally { setSaving(false) }
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
              const value = v.trim()
              if (value === search && page === 1) void load()
              else { setSearch(value); setPage(1) }
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
          <Select placeholder="逾期筛选" allowClear style={{ width: 140 }} options={[{ value: true, label: '仅逾期' }, { value: false, label: '未逾期' }]} onChange={v => { setOverdue(v); setPage(1) }} />
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
          { title: '有效任务', dataIndex: 'task_count' },
          { title: '逾期', dataIndex: 'overdue', render: (v: boolean) => v ? <Tag color="red">已逾期</Tag> : '—' },
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
                <Button size="small" disabled={['completed', 'cancelled'].includes(record.status)} icon={<EditOutlined />} onClick={() => openEdit(record)} />
                <Button size="small" loading={taskLoading} disabled={['completed', 'cancelled'].includes(record.status)} onClick={() => void openTasks(record)}>关联任务</Button>
                <Popconfirm title="确认删除？" onConfirm={() => void remove(record.id)}>
                  <Button size="small" disabled={record.status !== 'draft' || record.task_count > 0} danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? '编辑生产计划' : '新建生产计划'}
        open={open}
        confirmLoading={saving}
        cancelButtonProps={{ disabled: saving }}
        onCancel={() => { if (!saving) setOpen(false) }}
        onOk={() => void submit()}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical" disabled={saving}>
          <Alert type="info" message="计划进度按未取消任务的进度平均值自动汇总；已完成任务计 100%。草稿→已批准→进行中→已完成，结束前可取消。" style={{ marginBottom: 16 }} />
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
              <Select style={{ width: 160 }} options={statusOptions.filter(o => editing ? o.value === editing.status || editing.allowed_statuses?.includes(o.value) : o.value === 'draft')} />
            </Form.Item>
          </Space>
          <Space size="large" wrap>
            <Form.Item name="plan_start_date" label="开始日期" rules={[{ required: true }]}>
              <DatePicker />
            </Form.Item>
            <Form.Item name="plan_end_date" label="结束日期" dependencies={['plan_start_date']} rules={[{ required: true }, ({ getFieldValue }) => ({ validator(_, value) { return !value || !getFieldValue('plan_start_date') || !value.isBefore(getFieldValue('plan_start_date'), 'day') ? Promise.resolve() : Promise.reject(new Error('结束日期不能早于开始日期')) } })]}>
              <DatePicker />
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
      <Modal title={`关联任务：${taskPlan?.plan_name || ''}`} open={!!taskPlan} confirmLoading={saving} onCancel={() => { if (!saving) setTaskPlan(null) }} onOk={() => void saveTasks()}>
        <Alert message="只能关联当前工作区及同一工厂的任务；取消勾选将解除关联。" type="info" style={{ marginBottom: 16 }} />
        <Select aria-label="计划关联任务" mode="multiple" showSearch optionFilterProp="label" style={{ width: '100%' }} value={taskIds} onChange={setTaskIds} options={taskOptions.map(t => ({ value: t.id, label: `${t.task_number} · ${t.task_name}` }))} />
      </Modal>
    </Card>
  )
}

export default ProductionPlanManagement
