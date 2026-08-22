import React, { useEffect, useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Table,
  Tag,
  Space,
  message,
  Empty,
  Alert,
} from 'antd'
import { MessageOutlined, SendOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { listMyFeedback, submitFeedback, UserFeedbackItem } from '@/services/feedback'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

const FeedbackBoard: React.FC = () => {
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState<UserFeedbackItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const loadMine = async (nextPage = page, nextSize = pageSize) => {
    setLoading(true)
    try {
      const data = await listMyFeedback({ page: nextPage, page_size: nextSize })
      setItems(data.items)
      setTotal(data.total)
      setPage(data.page)
      setPageSize(data.page_size)
    } catch (error) {
      console.error(error)
      message.error('加载反馈列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadMine(1, pageSize)
  }, [])

  const handleSubmit = async (values: { title: string; content: string; contact?: string }) => {
    setSubmitting(true)
    try {
      await submitFeedback({
        title: values.title.trim(),
        content: values.content.trim(),
        contact: values.contact?.trim() || undefined,
      })
      message.success('反馈已提交，感谢您的建议')
      form.resetFields()
      await loadMine(1, pageSize)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || error?.message || '提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  const columns: ColumnsType<UserFeedbackItem> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'is_read',
      key: 'is_read',
      width: 100,
      render: (isRead: boolean) =>
        isRead ? <Tag color="green">已读</Tag> : <Tag color="orange">待处理</Tag>,
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (value?: string | null) =>
        value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2} className="mb-2">
          <MessageOutlined className="mr-2" />
          意见反馈
        </Title>
        <Text type="secondary">告诉我们哪里可以改进，您的留言仅管理员可见</Text>
      </div>

      <Alert
        className="mb-4"
        type="info"
        showIcon
        message="欢迎提出产品改进建议、使用问题或功能需求。我们会认真阅读每一条反馈。"
      />

      <Card title="提交反馈" className="mb-6">
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="title"
            label="标题"
            rules={[
              { required: true, message: '请填写标题' },
              { max: 200, message: '标题不超过 200 字' },
            ]}
          >
            <Input placeholder="例如：希望增加某某功能" maxLength={200} />
          </Form.Item>
          <Form.Item
            name="content"
            label="详细说明"
            rules={[
              { required: true, message: '请填写内容' },
              { max: 5000, message: '内容不超过 5000 字' },
            ]}
          >
            <TextArea rows={6} placeholder="描述问题场景、期望改进或建议" maxLength={5000} showCount />
          </Form.Item>
          <Form.Item
            name="contact"
            label="联系方式（可选）"
            rules={[{ max: 200, message: '不超过 200 字' }]}
          >
            <Input placeholder="邮箱 / 微信 / 手机，方便我们回访" maxLength={200} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SendOutlined />} loading={submitting}>
              提交反馈
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="我的反馈">
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          locale={{ emptyText: <Empty description="暂无反馈记录" /> }}
          expandable={{
            expandedRowRender: (record) => (
              <Space direction="vertical" className="w-full">
                <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                  {record.content}
                </Paragraph>
                {record.contact ? <Text type="secondary">联系方式：{record.contact}</Text> : null}
              </Space>
            ),
          }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (p, ps) => {
              void loadMine(p, ps)
            },
          }}
        />
      </Card>
    </div>
  )
}

export default FeedbackBoard
