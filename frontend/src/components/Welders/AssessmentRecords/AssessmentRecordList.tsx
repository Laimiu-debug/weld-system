/**
 * 焊工考核记录列表组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Empty, Table, Space, Tag, Popconfirm, message } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { assessmentRecordService, type WelderAssessmentRecord } from '../../../services/welderRecords';
import AssessmentRecordModal from './AssessmentRecordModal';
import { workspaceService } from '../../../services/workspace';
import dayjs from 'dayjs';

interface AssessmentRecordListProps {
  welderId: number;
}

const AssessmentRecordList: React.FC<AssessmentRecordListProps> = ({ welderId }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<WelderAssessmentRecord[]>([]);
  const [modalVisible, setModalVisible] = useState(false);

  // 加载考核记录
  const loadRecords = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      const data = await assessmentRecordService.getList(welderId, params);
      setRecords(data.items || []);
    } catch (error: any) {
      console.error('加载考核记录失败:', error);
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

  // 添加记录成功
  const handleAddSuccess = () => {
    setModalVisible(false);
    loadRecords();
  };

  // 删除记录
  const handleDelete = async (recordId: number) => {
    if (!currentWorkspace) return;

    try {
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      await assessmentRecordService.delete(welderId, recordId, params);
      message.success('删除成功');
      loadRecords();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const columns = [
    {
      title: '考核名称',
      dataIndex: 'assessment_name',
      key: 'assessment_name',
    },
    {
      title: '考核类型',
      dataIndex: 'assessment_type',
      key: 'assessment_type',
    },
    {
      title: '考核日期',
      dataIndex: 'assessment_date',
      key: 'assessment_date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '理论成绩',
      dataIndex: 'theory_score',
      key: 'theory_score',
    },
    {
      title: '实操成绩',
      dataIndex: 'practical_score',
      key: 'practical_score',
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
    },
    {
      title: '考核结果',
      dataIndex: 'assessment_result',
      key: 'assessment_result',
      render: (result: string) => {
        const color = result === '合格' ? 'success' : result === '优秀' ? 'blue' : 'error';
        return <Tag color={color}>{result}</Tag>;
      },
    },
    {
      title: '是否通过',
      dataIndex: 'pass_status',
      key: 'pass_status',
      render: (pass: boolean) => (
        <Tag color={pass ? 'success' : 'error'}>{pass ? '通过' : '未通过'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: WelderAssessmentRecord) => (
        <Space>
          <Popconfirm
            title="确定要删除这条考核记录吗？"
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
      title="考核记录"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加考核记录
        </Button>
      }
    >
      {records.length === 0 && !loading ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无考核记录"
        >
          <Button type="primary" onClick={() => setModalVisible(true)}>
            点击上方按钮添加考核记录信息
          </Button>
        </Empty>
      ) : (
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      )}

      <AssessmentRecordModal
        visible={modalVisible}
        welderId={welderId}
        onSuccess={handleAddSuccess}
        onCancel={() => setModalVisible(false)}
      />
    </Card>
  );
};

export default AssessmentRecordList;

