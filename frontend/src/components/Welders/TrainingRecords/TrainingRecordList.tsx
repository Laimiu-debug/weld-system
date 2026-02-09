/**
 * 焊工培训记录列表组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Table, message, Popconfirm, Empty, Space, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { trainingRecordService, type WelderTrainingRecord } from '../../../services/welderRecords';
import TrainingRecordModal from './TrainingRecordModal';
import { workspaceService } from '../../../services/workspace';

interface TrainingRecordListProps {
  welderId: number;
}

const TrainingRecordList: React.FC<TrainingRecordListProps> = ({ welderId }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<WelderTrainingRecord[]>([]);
  const [modalVisible, setModalVisible] = useState(false);

  // 加载培训记录
  const loadRecords = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      const data = await trainingRecordService.getList(welderId, params);
      setRecords(data.items || []);
    } catch (error: any) {
      console.error('加载培训记录失败:', error);
      // 暂时忽略错误，因为 API 可能还未完全实现
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (welderId && currentWorkspace) {
      loadRecords();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [welderId]);

  // 删除记录
  const handleDelete = async (recordId: number) => {
    if (!currentWorkspace) return;

    try {
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      await trainingRecordService.delete(welderId, recordId, params);
      message.success('删除成功');
      loadRecords();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // 添加记录成功
  const handleAddSuccess = () => {
    setModalVisible(false);
    loadRecords();
  };

  const columns = [
    {
      title: '培训名称',
      dataIndex: 'training_name',
      key: 'training_name',
    },
    {
      title: '培训类型',
      dataIndex: 'training_type',
      key: 'training_type',
    },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      key: 'start_date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '培训时长(h)',
      dataIndex: 'duration_hours',
      key: 'duration_hours',
    },
    {
      title: '培训机构',
      dataIndex: 'training_organization',
      key: 'training_organization',
    },
    {
      title: '考核成绩',
      dataIndex: 'assessment_score',
      key: 'assessment_score',
    },
    {
      title: '是否通过',
      dataIndex: 'pass_status',
      key: 'pass_status',
      render: (passed: boolean) => (
        <Tag color={passed ? 'success' : 'error'}>
          {passed ? '通过' : '未通过'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: WelderTrainingRecord) => (
        <Space>
          <Popconfirm
            title="确定要删除这条培训记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="培训记录"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加培训记录
        </Button>
      }
    >
      {records.length === 0 && !loading ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无培训记录"
        >
          <Button type="primary" onClick={() => setModalVisible(true)}>
            点击上方按钮添加培训记录信息
          </Button>
        </Empty>
      ) : (
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      )}

      <TrainingRecordModal
        visible={modalVisible}
        welderId={welderId}
        onSuccess={handleAddSuccess}
        onCancel={() => setModalVisible(false)}
      />
    </Card>
  );
};

export default TrainingRecordList;

