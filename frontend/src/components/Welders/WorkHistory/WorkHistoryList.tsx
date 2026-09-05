/**
 * 焊工工作履历列表组件
 * 记录焊工在不同公司的工作经历
 */
import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Timeline, Empty, Space, Tag, Descriptions, Popconfirm, message, Alert, Spin } from 'antd';
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
  const workspaceKey = JSON.stringify(currentWorkspace)
  const requestVersion = useRef(0)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false);
  const [histories, setHistories] = useState<WelderWorkHistory[]>([]);
  const [modalVisible, setModalVisible] = useState(false)
  const [editing, setEditing] = useState<WelderWorkHistory | null>(null);

  // 加载工作履历
  const loadHistories = async () => {
    const version = ++requestVersion.current;
    setError('');
    if (!currentWorkspace) { setHistories([]); setError('请先选择工作区'); setLoading(false); return; }

    try {
      setLoading(true);
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      const data = await workHistoryService.getList(welderId, params);
      if (version === requestVersion.current) setHistories(data.items || []);
    } catch (error: any) {
      if (version !== requestVersion.current) return;
      setError('工作履历加载失败，请重试');
      setHistories([]);
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  };

  useEffect(() => {
    setHistories([]); setEditing(null); setModalVisible(false)
    void loadHistories()
    return () => { requestVersion.current += 1 }
  }, [welderId, workspaceKey]);

  const handleAddSuccess = () => {
    setModalVisible(false)
    setEditing(null)
    loadHistories()
  }

  const openCreate = () => {
    setEditing(null)
    setModalVisible(true)
  }

  const openEdit = (history: WelderWorkHistory) => {
    setEditing(history)
    setModalVisible(true)
  }

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
  const calculateDuration = (startDate: string, endDate?: string | null) => {
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
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          添加工作履历
        </Button>
      }
    >
      {error ? <Alert type="error" showIcon message={error} action={<Button onClick={() => void loadHistories()}>重试</Button>} /> : loading ? <Spin /> : histories.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无工作履历记录"
        >
          <Button type="primary" onClick={openCreate}>
            添加工作履历
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
                    <Button
                      type="link"
                      icon={<EditOutlined />}
                      size="small"
                      onClick={() => openEdit(history)}
                    >
                      编辑
                    </Button>
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
        editing={editing}
        onSuccess={handleAddSuccess}
        onCancel={() => {
          setModalVisible(false)
          setEditing(null)
        }}
      />
    </Card>
  );
};

export default WorkHistoryList;

