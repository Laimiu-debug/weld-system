import React, { useEffect, useState } from 'react'
import {
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
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)
  const [form] = Form.useForm()
  const ws = readWorkspaceQuery()

  const load = async () => {
    try {
      setLoading(true)
      const data = await performanceApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '加载绩效记录失败')
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
    form.setFieldsValue({ status: 'draft', overall_score: 0 })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.setFieldsValue(record)
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
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
    }
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
              setSearch(v)
              setPage(1)
              void load()
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
        title={editing ? '编辑绩效' : '新建绩效'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => void submit()}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="employee_name" label="员工姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="employee_user_id" label="员工用户ID（可选）">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Space wrap size="large">
            <Form.Item name="department" label="部门">
              <Input style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="position" label="岗位">
              <Input style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="review_period" label="考核周期" rules={[{ required: true }]}>
              <Input placeholder="如 2026-Q1" style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select
                style={{ width: 140 }}
                options={[
                  { value: 'draft', label: '草稿' },
                  { value: 'submitted', label: '已提交' },
                  { value: 'reviewed', label: '已评审' },
                  { value: 'finalized', label: '已定稿' },
                ]}
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
