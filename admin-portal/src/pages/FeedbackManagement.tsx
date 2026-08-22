import React, { useEffect, useState } from 'react';
import {
  Badge,
  Button,
  Card,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  AdminFeedbackItem,
  deleteFeedback,
  getFeedbackList,
  markFeedbackRead,
  updateFeedbackNote,
} from '@/services/feedback';

const { TextArea } = Input;
const { Paragraph, Text } = Typography;

const FeedbackManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<AdminFeedbackItem[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined);
  const [detailVisible, setDetailVisible] = useState(false);
  const [noteVisible, setNoteVisible] = useState(false);
  const [selected, setSelected] = useState<AdminFeedbackItem | null>(null);
  const [noteForm] = Form.useForm();

  const loadList = async () => {
    setLoading(true);
    try {
      const data = await getFeedbackList({
        page,
        page_size: pageSize,
        is_read: filterRead,
      });
      setItems(data.items || []);
      setTotal(data.total || 0);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error(error);
      message.error('加载反馈列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadList();
  }, [page, pageSize, filterRead]);

  const openDetail = async (record: AdminFeedbackItem) => {
    setSelected(record);
    setDetailVisible(true);
    if (!record.is_read) {
      try {
        const updated = await markFeedbackRead(record.id);
        setSelected(updated);
        void loadList();
      } catch (error) {
        console.error(error);
      }
    }
  };

  const openNote = (record: AdminFeedbackItem) => {
    setSelected(record);
    noteForm.setFieldsValue({ admin_note: record.admin_note || '' });
    setNoteVisible(true);
  };

  const handleSaveNote = async () => {
    if (!selected) return;
    try {
      const values = await noteForm.validateFields();
      await updateFeedbackNote(selected.id, values.admin_note || '');
      message.success('备注已保存');
      setNoteVisible(false);
      void loadList();
    } catch (error) {
      console.error(error);
      message.error('保存备注失败');
    }
  };

  const handleMarkRead = async (record: AdminFeedbackItem) => {
    try {
      await markFeedbackRead(record.id);
      message.success('已标记为已读');
      void loadList();
    } catch (error) {
      console.error(error);
      message.error('操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteFeedback(id);
      message.success('已删除');
      void loadList();
    } catch (error) {
      console.error(error);
      message.error('删除失败');
    }
  };

  const columns: ColumnsType<AdminFeedbackItem> = [
    {
      title: '状态',
      dataIndex: 'is_read',
      width: 90,
      render: (isRead: boolean) =>
        isRead ? <Tag color="default">已读</Tag> : <Badge status="processing" text="未读" />,
    },
    {
      title: '标题',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: '用户',
      key: 'user',
      width: 180,
      render: (_, record) => (
        <div>
          <div>{record.user_name || '-'}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.user_email || `ID:${record.user_id}`}
          </Text>
        </div>
      ),
    },
    {
      title: '联系方式',
      dataIndex: 'contact',
      width: 140,
      ellipsis: true,
      render: (v?: string | null) => v || '-',
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      width: 170,
      render: (v?: string | null) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => void openDetail(record)}>
            详情
          </Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => openNote(record)}>
            备注
          </Button>
          {!record.is_read && (
            <Button type="link" icon={<CheckOutlined />} onClick={() => void handleMarkRead(record)}>
              已读
            </Button>
          )}
          <Popconfirm title="确定删除这条反馈？" onConfirm={() => void handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <MessageOutlined />
            <span>用户反馈</span>
            {unreadCount > 0 ? <Badge count={unreadCount} overflowCount={99} /> : null}
          </Space>
        }
        extra={
          <Select
            allowClear
            placeholder="按状态筛选"
            style={{ width: 140 }}
            value={filterRead}
            onChange={(v) => {
              setPage(1);
              setFilterRead(v);
            }}
            options={[
              { label: '未读', value: false },
              { label: '已读', value: true },
            ]}
          />
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
        />
      </Card>

      <Modal
        title="反馈详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          selected ? (
            <Button key="note" type="primary" onClick={() => openNote(selected)}>
              编辑备注
            </Button>
          ) : null,
        ]}
        width={720}
      >
        {selected && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <Text type="secondary">标题</Text>
              <Paragraph strong style={{ marginBottom: 0 }}>
                {selected.title}
              </Paragraph>
            </div>
            <div>
              <Text type="secondary">用户</Text>
              <Paragraph style={{ marginBottom: 0 }}>
                {selected.user_name || '-'}（{selected.user_email || selected.user_id}）
              </Paragraph>
            </div>
            {selected.contact ? (
              <div>
                <Text type="secondary">联系方式</Text>
                <Paragraph style={{ marginBottom: 0 }}>{selected.contact}</Paragraph>
              </div>
            ) : null}
            <div>
              <Text type="secondary">内容</Text>
              <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                {selected.content}
              </Paragraph>
            </div>
            <div>
              <Text type="secondary">内部备注</Text>
              <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                {selected.admin_note || '暂无'}
              </Paragraph>
            </div>
            <Text type="secondary">
              提交于{' '}
              {selected.created_at
                ? dayjs(selected.created_at).format('YYYY-MM-DD HH:mm:ss')
                : '-'}
              {selected.read_at
                ? ` · 已读于 ${dayjs(selected.read_at).format('YYYY-MM-DD HH:mm:ss')}`
                : ''}
            </Text>
          </Space>
        )}
      </Modal>

      <Modal
        title="内部备注"
        open={noteVisible}
        onCancel={() => setNoteVisible(false)}
        onOk={() => void handleSaveNote()}
        okText="保存"
      >
        <Form form={noteForm} layout="vertical">
          <Form.Item name="admin_note" label="备注（仅管理员可见）">
            <TextArea rows={5} maxLength={5000} showCount placeholder="处理进展、跟进记录等" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FeedbackManagement;
