import React, { useEffect, useState } from 'react'
import {
  Button,
  Card,
  DatePicker,
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
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { qualityStandardApi, readWorkspaceQuery } from '@/services/businessExtensions'

const QualityStandardManagement: React.FC = () => {
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
      const data = await qualityStandardApi.list({
        ...ws,
        skip: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
      })
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '加载质量标准失败')
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
    form.setFieldsValue({ status: 'active', version: '1.0' })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.setFieldsValue({
      ...record,
      effective_date: record.effective_date ? dayjs(record.effective_date) : undefined,
      expiry_date: record.expiry_date ? dayjs(record.expiry_date) : undefined,
    })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      ...values,
      effective_date: values.effective_date?.format('YYYY-MM-DD'),
      expiry_date: values.expiry_date?.format('YYYY-MM-DD'),
    }
    try {
      if (editing) {
        await qualityStandardApi.update(ws, editing.id, payload)
        message.success('已更新')
      } else {
        await qualityStandardApi.create(ws, payload)
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
      await qualityStandardApi.remove(ws, id)
      message.success('已删除')
      void load()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '删除失败')
    }
  }

  return (
    <Card
      title="质量标准"
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
          <Button icon={<ReloadOutlined />} onClick={() => void load()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建标准
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
          { title: '编号', dataIndex: 'standard_code' },
          { title: '名称', dataIndex: 'standard_name' },
          { title: '类别', dataIndex: 'category' },
          { title: '版本', dataIndex: 'version' },
          { title: '等级', dataIndex: 'level' },
          {
            title: '状态',
            dataIndex: 'status',
            render: (v: string) => <Tag color={v === 'active' ? 'green' : 'default'}>{v}</Tag>,
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
        title={editing ? '编辑质量标准' : '新建质量标准'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => void submit()}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="standard_code" label="标准编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="standard_name" label="标准名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Space wrap size="large">
            <Form.Item name="category" label="类别">
              <Input style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="version" label="版本">
              <Input style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="level" label="等级">
              <Input style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="status" label="状态">
              <Select
                style={{ width: 140 }}
                options={[
                  { value: 'active', label: '生效' },
                  { value: 'draft', label: '草稿' },
                  { value: 'obsolete', label: '作废' },
                ]}
              />
            </Form.Item>
          </Space>
          <Space wrap>
            <Form.Item name="effective_date" label="生效日期">
              <DatePicker />
            </Form.Item>
            <Form.Item name="expiry_date" label="失效日期">
              <DatePicker />
            </Form.Item>
          </Space>
          <Form.Item name="test_methods" label="检验方法">
            <Input.TextArea rows={2} placeholder="可填文本或 JSON" />
          </Form.Item>
          <Form.Item name="acceptance_criteria" label="验收准则">
            <Input.TextArea rows={2} placeholder="可填文本或 JSON" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default QualityStandardManagement
