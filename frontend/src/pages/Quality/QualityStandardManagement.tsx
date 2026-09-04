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
import {
  DeleteOutlined,
  EditOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { qualityStandardApi, readWorkspaceQuery } from '@/services/businessExtensions'

const toTextItems = (value: unknown): string[] => {
  if (!value) return []
  if (Array.isArray(value)) return value.map(item => typeof item === 'string' ? item : JSON.stringify(item))
  if (typeof value !== 'string') return [String(value)]
  try {
    const parsed = JSON.parse(value)
    if (Array.isArray(parsed)) return parsed.map(item => typeof item === 'string' ? item : JSON.stringify(item))
  } catch {
    // 兼容历史纯文本数据。
  }
  return value.split(/\r?\n/).map(item => item.trim()).filter(Boolean)
}

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
    form.setFieldsValue({ status: 'active', version: '1.0', test_methods: [], acceptance_criteria: [] })
    setOpen(true)
  }

  const openEdit = (record: any) => {
    setEditing(record)
    form.setFieldsValue({
      ...record,
      test_methods: toTextItems(record.test_methods),
      acceptance_criteria: toTextItems(record.acceptance_criteria),
      effective_date: record.effective_date ? dayjs(record.effective_date) : undefined,
      expiry_date: record.expiry_date ? dayjs(record.expiry_date) : undefined,
    })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    const payload = {
      ...values,
      test_methods: JSON.stringify(values.test_methods || []),
      acceptance_criteria: JSON.stringify(values.acceptance_criteria || []),
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
        destroyOnHidden
        forceRender
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
          <Form.Item label="检验方法" extra="逐条填写，例如：外观检查、射线检测（RT）">
            <Form.List name="test_methods">
              {(fields, { add, remove }) => (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {fields.map(field => (
                    <Space.Compact key={field.key} block>
                      <Form.Item {...field} noStyle rules={[{ required: true, message: '请填写检验方法' }]}>
                        <Input placeholder="输入一项检验方法" />
                      </Form.Item>
                      <Button danger icon={<MinusCircleOutlined />} onClick={() => remove(field.name)} aria-label="删除检验方法" />
                    </Space.Compact>
                  ))}
                  <Button type="dashed" icon={<PlusOutlined />} onClick={() => add()} block>添加检验方法</Button>
                </Space>
              )}
            </Form.List>
          </Form.Item>
          <Form.Item label="验收准则" extra="每行一条可直接执行的合格要求">
            <Form.List name="acceptance_criteria">
              {(fields, { add, remove }) => (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {fields.map(field => (
                    <Space.Compact key={field.key} block>
                      <Form.Item {...field} noStyle rules={[{ required: true, message: '请填写验收准则' }]}>
                        <Input placeholder="例如：焊缝表面不得有裂纹" />
                      </Form.Item>
                      <Button danger icon={<MinusCircleOutlined />} onClick={() => remove(field.name)} aria-label="删除验收准则" />
                    </Space.Compact>
                  ))}
                  <Button type="dashed" icon={<PlusOutlined />} onClick={() => add()} block>添加验收准则</Button>
                </Space>
              )}
            </Form.List>
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
