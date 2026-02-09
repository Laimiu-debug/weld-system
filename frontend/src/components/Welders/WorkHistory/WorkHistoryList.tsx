/**
 * 焊工工作履历列表组件
 * 记录焊工在不同公司的工作经历
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Timeline, Empty, Space, Tag, Descriptions, Popconfirm, message } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, EnvironmentOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import WorkHistoryModal from './WorkHistoryModal';
import { workHistoryService, type WelderWorkHistory } from '../../../services/welderRecords';
import { workspaceService } from '../../../services/workspace';

interface WorkHistoryListProps {
  welderId: number;
}

const WorkHistoryList: React.FC<WorkHistoryListProps> = ({ welderId }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [loading, setLoading] = useState(false);
  const [histories, setHistories] = useState<WelderWorkHistory[]>([]);
  const [modalVisible, setModalVisible] = useState(false);

  // 加载工作履历
  const loadHistories = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      const data = await workHistoryService.getList(welderId, params);
      setHistories(data.items || []);
    } catch (error: any) {
      console.error('加载工作履历失败:', error);
      // API 还未实现，暂时使用空数组
      setHistories([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (welderId && currentWorkspace) {
      loadHistories();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [welderId]);

  const handleAddSuccess = () => {
    setModalVisible(false);
    loadHistories();
  };

  const handleDelete = async (id: number) => {
    if (!currentWorkspace) return;

    try {
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      await workHistoryService.delete(welderId, id, params);
      message.success('删除成功');
      loadHistories();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // 计算工作时长
  const calculateDuration = (startDate: string, endDate?: string) => {
    const start = dayjs(startDate);
    const end = endDate ? dayjs(endDate) : dayjs();
    const months = end.diff(start, 'month');
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    
    if (years > 0) {
      return `${years}年${remainingMonths > 0 ? remainingMonths + '个月' : ''}`;
    }
    return `${months}个月`;
  };

  return (
    <Card
      title="工作履历"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加工作履历
        </Button>
      }
    >
      {histories.length === 0 && !loading ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无工作履历记录"
        >
          <Button type="primary" onClick={() => setModalVisible(true)}>
            点击上方按钮添加焊工的工作履历信息
          </Button>
        </Empty>
      ) : (
        <Timeline mode="left">
          {histories.map((history) => (
            <Timeline.Item
              key={history.id}
              label={
                <Space direction="vertical" size={0}>
                  <span style={{ fontWeight: 'bold' }}>
                    {dayjs(history.start_date).format('YYYY-MM')}
                  </span>
                  <span style={{ fontSize: '12px', color: '#999' }}>至</span>
                  <span style={{ fontWeight: 'bold' }}>
                    {history.end_date ? dayjs(history.end_date).format('YYYY-MM') : '至今'}
                  </span>
                  <Tag color="blue" style={{ marginTop: 4 }}>
                    {calculateDuration(history.start_date, history.end_date)}
                  </Tag>
                </Space>
              }
            >
              <Card
                size="small"
                title={
                  <Space>
                    <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {history.company_name}
                    </span>
                    <Tag color="green">{history.position}</Tag>
                  </Space>
                }
                extra={
                  <Space>
                    <Popconfirm
                      title="确定要删除这条工作履历吗？"
                      onConfirm={() => handleDelete(history.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button type="link" danger icon={<DeleteOutlined />} size="small">
                        删除
                      </Button>
                    </Popconfirm>
                  </Space>
                }
              >
                <Descriptions column={1} size="small">
                  {history.department && (
                    <Descriptions.Item label="部门">
                      {history.department}
                    </Descriptions.Item>
                  )}
                  {history.location && (
                    <Descriptions.Item label="工作地点">
                      <EnvironmentOutlined /> {history.location}
                    </Descriptions.Item>
                  )}
                  {history.job_description && (
                    <Descriptions.Item label="工作内容">
                      {history.job_description}
                    </Descriptions.Item>
                  )}
                  {history.achievements && (
                    <Descriptions.Item label="主要成就">
                      {history.achievements}
                    </Descriptions.Item>
                  )}
                  {history.leaving_reason && (
                    <Descriptions.Item label="离职原因">
                      {history.leaving_reason}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Timeline.Item>
          ))}
        </Timeline>
      )}

      <WorkHistoryModal
        visible={modalVisible}
        welderId={welderId}
        onSuccess={handleAddSuccess}
        onCancel={() => setModalVisible(false)}
      />
    </Card>
  );
};

export default WorkHistoryList;

