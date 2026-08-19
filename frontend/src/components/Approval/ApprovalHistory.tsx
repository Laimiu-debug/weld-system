/**
 * 审批历史时间线组件
 * 显示文档的审批流程和历史记录
 */
import React, { useEffect, useState } from 'react';
import { Timeline, Card, Tag, Spin, Empty, Space } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  RollbackOutlined,
  SendOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { approvalApi } from '@/services/approval';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

interface ApprovalHistoryProps {
  instanceId: number;
  showCard?: boolean;
}

interface HistoryItem {
  id: number;
  step_number: number;
  step_name: string;
  action: string;
  operator_id: number;
  operator_name: string;
  comment: string;
  result?: string;
  created_at: string;
  attachments?: string[];
}

const getActionIcon = (action: string) => {
  switch (action) {
    case 'submit':
      return <SendOutlined style={{ color: '#1890ff' }} />;
    case 'approve':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    case 'reject':
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    case 'return':
      return <RollbackOutlined style={{ color: '#faad14' }} />;
    case 'cancel':
      return <StopOutlined style={{ color: '#8c8c8c' }} />;
    default:
      return <ClockCircleOutlined />;
  }
};

const getActionText = (action: string) => {
  switch (action) {
    case 'submit':
      return '提交审批';
    case 'approve':
      return '批准';
    case 'reject':
      return '拒绝';
    case 'return':
      return '退回';
    case 'cancel':
      return '取消';
    default:
      return action;
  }
};

const getActionColor = (action: string) => {
  switch (action) {
    case 'submit':
      return 'blue';
    case 'approve':
      return 'green';
    case 'reject':
      return 'red';
    case 'return':
      return 'orange';
    case 'cancel':
      return 'default';
    default:
      return 'default';
  }
};

export const ApprovalHistory: React.FC<ApprovalHistoryProps> = ({
  instanceId,
  showCard = true,
}) => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    fetchHistory();
  }, [instanceId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await approvalApi.getHistory(instanceId);
      // 后端返回格式: { success: true, data: [...] }
      // response.data 是整个响应对象，response.data.data 才是历史记录数组
      const historyData = response.data || [];
      console.log('审批历史数据:', historyData);
      setHistory(Array.isArray(historyData) ? historyData : []);
    } catch (error) {
      console.error('获取审批历史失败:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const renderTimeline = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin />
        </div>
      );
    }

    if (!history || history.length === 0) {
      return <Empty description="暂无审批记录" />;
    }

    return (
      <Timeline>
        {history.map((item, index) => (
          <Timeline.Item
            key={item.id}
            dot={getActionIcon(item.action)}
            color={getActionColor(item.action)}
          >
            <div style={{ marginBottom: 16 }}>
              <Space direction="vertical" size={4} style={{ width: '100%' }}>
                <Space>
                  <Tag color={getActionColor(item.action)}>
                    {getActionText(item.action)}
                  </Tag>
                  <span style={{ fontWeight: 500 }}>{item.step_name}</span>
                </Space>

                <div style={{ color: '#8c8c8c', fontSize: 12 }}>
                  <Space split="|">
                    <span>{item.operator_name}</span>
                    <span>{dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}</span>
                    <span>{dayjs(item.created_at).fromNow()}</span>
                  </Space>
                </div>

                {item.comment && (
                  <div
                    style={{
                      marginTop: 8,
                      padding: '8px 12px',
                      background: '#f5f5f5',
                      borderRadius: 4,
                      fontSize: 14,
                    }}
                  >
                    {item.comment}
                  </div>
                )}

                {item.attachments && item.attachments.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <Space>
                      {item.attachments.map((attachment, idx) => (
                        <a key={idx} href={attachment} target="_blank" rel="noopener noreferrer">
                          附件{idx + 1}
                        </a>
                      ))}
                    </Space>
                  </div>
                )}
              </Space>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
    );
  };

  if (showCard) {
    return (
      <Card title="审批历史" variant="borderless">
        {renderTimeline()}
      </Card>
    );
  }

  return renderTimeline();
};

export default ApprovalHistory;

