import React, { useEffect, useState, useRef } from 'react'
import {
  Alert,
  Button,
  Card,
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
import { performanceApi, readWorkspaceQuery } from '@/services/businessExtensions'

const PerformanceManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [employees, setEmployees] = useState<any[]>([])
  const [employeeError, setEmployeeError] = useState(false)
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
      const data = await performanceApi.list({
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
      message.error(err instanceof Error ? err.message : '加载绩效记录失败')
    } finally {
      if (version === requestVersion.current) setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    return () => { requestVersion.current += 1 }
  }, [page, pageSize, search])

  const loadEmployees = async () => {
    try { setEmployees(await performanceApi.employees(ws)); setEmployeeError(false) }
    catch { setEmployees([]); setEmployeeError(true) }
  }
  useEffect(() => { void loadEmployees() }, [ws.workspace_type, ws.company_id, ws.factory_id])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ status: 'draft', overall_score: 0 })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.resetFields()
    form.setFieldsValue({ ...record, adjustment_reason: undefined })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editing) {
        await performanceApi.update(ws, editing.id, values)
        message.success('已更新')
      } else {
        await performanceApi.create(ws, values)
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
      await performanceApi.remove(ws, id)
      message.success('已删除')
      void load()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <Card
      title="员工绩效"
      extra={
        <Space>
          <Input.Search
            placeholder="搜索姓名/部门/周期"
            allowClear
            onSearch={(v) => {
              const value = v.trim()
              if (value === search && page === 1) void load()
              else { setSearch(value); setPage(1) }
            }}
            style={{ width: 240 }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => void load()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建评估
          </Button>
        </Space>
      }
    >
      <Table
        expandable={{ expandedRowRender: record => <Space direction="vertical">
          <div>周期：{record.period_start} 至 {record.period_end}</div>
          <div>业务参考：组长完工任务 {record.evidence_snapshot?.completed_tasks ?? '—'}；检验 {record.evidence_snapshot?.inspections ?? '—'}；合格检验 {record.evidence_snapshot?.passed_inspections ?? '—'}</div>
          <div>{record.evidence_snapshot?.source_note}</div>
          <div>人工调整理由：{record.adjustment_reason || '无调整'}</div>
          <div>评审意见：{record.reviewer_comment || '未填写'}</div>
          {(record.evidence_snapshot?.adjustments || []).map((a: any, i: number) => <div key={i}>{a.at} · {a.reason} · 总分 {a.before.overall_score} → {a.after.overall_score}</div>)}
        </Space> }}
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
          { title: '员工', dataIndex: 'employee_name' },
          { title: '部门', dataIndex: 'department' },
          { title: '岗位', dataIndex: 'position' },
          { title: '周期', dataIndex: 'review_period' },
          { title: '总分', dataIndex: 'overall_score' },
          {
            title: '状态',
            dataIndex: 'status',
            render: (v: string) => <Tag>{v}</Tag>,
          },
          {
            title: '操作',
            render: (_: unknown, record: any) => (
              <Space>
                <Button size="small" disabled={record.status === 'finalized'} icon={<EditOutlined />} onClick={() => openEdit(record)} />
                <Popconfirm title="确认删除？" onConfirm={() => void remove(record.id)}>
                  <Button size="small" disabled={record.status !== 'draft'} danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? '编辑绩效' : '新建绩效'}
        open={open}
        confirmLoading={saving}
        onCancel={() => { if (!saving) setOpen(false) }}
        onOk={() => void submit()}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical" disabled={saving}>
          <Alert type="info" message="评分范围 0–100；草稿→提交→评审→确认。确认后锁定，评分由人工评审，业务记录作为参考。" style={{ marginBottom: 16 }} />
          {employeeError && <Alert type="error" message="员工列表加载失败" action={<Button onClick={() => void loadEmployees()}>重试</Button>} />}
          <Form.Item name="employee_user_id" label="员工" rules={[{ required: true, message: '请选择员工' }]}>
            <Select showSearch optionFilterProp="label" disabled={employeeError} options={employees.map(e => ({ value: e.id, label: `${e.name}${e.department ? ' · ' + e.department : ''}` }))} />
          </Form.Item>
          <Space wrap size="large">
            <Form.Item name="review_period" label="考核周期" rules={[{ required: true }, { pattern: /^\d{4}-(0[1-9]|1[0-2]|Q[1-4])$/, message: '请输入 YYYY-MM 或 YYYY-Q1 至 YYYY-Q4' }]}>
              <Input placeholder="如 2026-Q1" style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select
                style={{ width: 140 }}
                options={[
                  { value: 'draft', label: '草稿' },
                  { value: 'submitted', label: '已提交' },
                  { value: 'reviewed', label: '已评审' },
                  { value: 'finalized', label: '已确认（锁定）' },
                ].filter(o => editing ? o.value === editing.status || ({ draft: ['submitted'], submitted: ['draft', 'reviewed'], reviewed: ['draft', 'finalized'] } as Record<string, string[]>)[editing.status]?.includes(o.value) : o.value === 'draft')}
              />
            </Form.Item>
          </Space>
          <Space wrap>
            <Form.Item name="overall_score" label="总分">
              <InputNumber min={0} max={100} />
            </Form.Item>
            <Form.Item name="quality_score" label="质量分">
              <InputNumber min={0} max={100} />
            </Form.Item>
            <Form.Item name="efficiency_score" label="效率分">
              <InputNumber min={0} max={100} />
            </Form.Item>
            <Form.Item name="safety_score" label="安全分">
              <InputNumber min={0} max={100} />
            </Form.Item>
            <Form.Item name="teamwork_score" label="协作分">
              <InputNumber min={0} max={100} />
            </Form.Item>
          </Space>
          <Form.Item name="adjustment_reason" label="人工调整理由" extra="修改已有评分时必填，随评审记录保存。"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="goals" label="目标">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="achievements" label="业绩">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="areas_for_improvement" label="改进项">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="reviewer_comment" label="评审意见">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default PerformanceManagement
