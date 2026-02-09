/**
 * 审批列表页面
 * 显示待审批和已提交的审批列表
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tabs,
  Tag,
  Space,
  Button,
  Modal,
  Input,
  message,
  Badge,
  Tooltip,
} from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { approvalApi, ApprovalInstance } from '@/services/approval';
import { ApprovalHistory } from '@/components/Approval/ApprovalHistory';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { TextArea } = Input;

interface ApprovalListProps {
  workspaceType: string;
  workspaceId?: string;
}

export const ApprovalList: React.FC<ApprovalListProps> = ({
  workspaceType,
  workspaceId,
}) => {
  const [activeTab, setActiveTab] = useState('pending');
  const [loading, setLoading] = useState(false);
  const [pendingList, setPendingList] = useState<ApprovalInstance[]>([]);
  const [submittedList, setSubmittedList] = useState<ApprovalInstance[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<number | null>(null);
  const [actionModalVisible, setActionModalVisible] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve');
  const [comment, setComment] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab, pagination.current, workspaceType, workspaceId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        workspace_type: workspaceType,
        workspace_id: workspaceId,
        page: pagination.current,
        page_size: pagination.pageSize,
      };

      if (activeTab === 'pending') {
        const response = await approvalApi.getPendingApprovals(params);
        setPendingList(response.data.items);
        setPagination((prev) => ({ ...prev, total: response.data.total }));
      } else {
        const response = await approvalApi.getMySubmissions(params);
        setSubmittedList(response.data.items);
        setPagination((prev) => ({ ...prev, total: response.data.total }));
      }
    } catch (error: any) {
      message.error(error.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchAction = async (type: 'approve' | 'reject') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要操作的审批');
      return;
    }
    setActionType(type);
    setActionModalVisible(true);
  };

  const handleActionConfirm = async () => {
    if (!comment.trim()) {
      message.warning('请输入审批意见');
      return;
    }

    setLoading(true);
    try {
      if (selectedRowKeys.length > 1) {
        // 批量操作
        const apiMethod =
          actionType === 'approve'
            ? approvalApi.batchApprove
            : approvalApi.batchReject;
        await apiMethod({
          instance_ids: selectedRowKeys,
          comment,
        });
        message.success(`批量${actionType === 'approve' ? '批准' : '拒绝'}成功`);
      } else {
        // 单个操作
        const apiMethod =
          actionType === 'approve' ? approvalApi.approve : approvalApi.reject;
        await apiMethod(selectedRowKeys[0], { comment });
        message.success(`${actionType === 'approve' ? '批准' : '拒绝'}成功`);
      }

      setActionModalVisible(false);
      setComment('');
      setSelectedRowKeys([]);
      fetchData();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '待审批' },
      in_progress: { color: 'processing', text: '审批中' },
      approved: { color: 'success', text: '已批准' },
      rejected: { color: 'error', text: '已拒绝' },
      returned: { color: 'warning', text: '已退回' },
      cancelled: { color: 'default', text: '已取消' },
    };
    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getPriorityTag = (priority: string) => {
    const priorityMap: Record<string, { color: string; text: string }> = {
      low: { color: 'default', text: '低' },
      normal: { color: 'blue', text: '普通' },
      high: { color: 'orange', text: '高' },
      urgent: { color: 'red', text: '紧急' },
    };
    const config = priorityMap[priority] || { color: 'default', text: priority };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '文档编号',
      dataIndex: 'document_number',
      key: 'document_number',
      width: 150,
    },
    {
      title: '文档标题',
      dataIndex: 'document_title',
      key: 'document_title',
      ellipsis: true,
    },
    {
      title: '文档类型',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 100,
      render: (type: string) => type.toUpperCase(),
    },
    {
      title: '当前步骤',
      dataIndex: 'current_step_name',
      key: 'current_step_name',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => getPriorityTag(priority),
    },
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ApprovalInstance) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedInstance(record.id);
                setDetailVisible(true);
              }}
            />
          </Tooltip>
          {activeTab === 'pending' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => {
                  setSelectedRowKeys([record.id]);
                  handleBatchAction('approve');
                }}
              >
                批准
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<CloseOutlined />}
                onClick={() => {
                  setSelectedRowKeys([record.id]);
                  handleBatchAction('reject');
                }}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as number[]),
    getCheckboxProps: (record: ApprovalInstance) => ({
      disabled: activeTab !== 'pending' || record.status !== 'pending',
    }),
  };

  return (
    <Card
      title="审批管理"
      extra={
        <Button icon={<ReloadOutlined />} onClick={fetchData}>
          刷新
        </Button>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <Badge count={pagination.total} offset={[10, 0]}>
              待我审批
            </Badge>
          }
          key="pending"
        >
          {selectedRowKeys.length > 0 && (
            <Space style={{ marginBottom: 16 }}>
              <span>已选择 {selectedRowKeys.length} 项</span>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={() => handleBatchAction('approve')}
              >
                批量批准
              </Button>
              <Button
                danger
                icon={<CloseOutlined />}
                onClick={() => handleBatchAction('reject')}
              >
                批量拒绝
              </Button>
            </Space>
          )}
          <Table
            rowSelection={rowSelection}
            columns={columns}
            dataSource={pendingList}
            loading={loading}
            rowKey="id"
            pagination={{
              ...pagination,
              onChange: (page) => setPagination((prev) => ({ ...prev, current: page })),
            }}
          />
        </TabPane>
        <TabPane tab="我提交的" key="submitted">
          <Table
            columns={columns}
            dataSource={submittedList}
            loading={loading}
            rowKey="id"
            pagination={{
              ...pagination,
              onChange: (page) => setPagination((prev) => ({ ...prev, current: page })),
            }}
          />
        </TabPane>
      </Tabs>

      {/* 审批详情弹窗 */}
      <Modal
        title="审批详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedInstance && <ApprovalHistory instanceId={selectedInstance} showCard={false} />}
      </Modal>

      {/* 审批操作弹窗 */}
      <Modal
        title={actionType === 'approve' ? '批准审批' : '拒绝审批'}
        open={actionModalVisible}
        onOk={handleActionConfirm}
        onCancel={() => {
          setActionModalVisible(false);
          setComment('');
        }}
        confirmLoading={loading}
      >
        <TextArea
          rows={4}
          placeholder="请输入审批意见"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </Modal>
    </Card>
  );
};

export default ApprovalList;

