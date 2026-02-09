/**
 * 焊工焊接操作记录列表组件
 */
import React, { useState, useEffect } from 'react';
import { Card, Button, Table, message, Popconfirm, Empty, Space, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { workRecordService, type WelderWorkRecord } from '../../../services/welderRecords';
import WorkRecordModal from './WorkRecordModal';
import { workspaceService } from '../../../services/workspace';

interface WorkRecordListProps {
  welderId: number;
}

const WorkRecordList: React.FC<WorkRecordListProps> = ({ welderId }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<WelderWorkRecord[]>([]);
  const [modalVisible, setModalVisible] = useState(false);

  // 加载焊接操作记录
  const loadRecords = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };
      const data = await workRecordService.getList(welderId, params);
      setRecords(data.items || []);
    } catch (error: any) {
      console.error('加载焊接操作记录失败:', error);
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
      await workRecordService.delete(welderId, recordId, params);
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
      title: '工作日期',
      dataIndex: 'work_date',
      key: 'work_date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '班次',
      dataIndex: 'work_shift',
      key: 'work_shift',
    },
    {
      title: '工时(h)',
      dataIndex: 'work_hours',
      key: 'work_hours',
    },
    {
      title: '焊接工艺',
      dataIndex: 'welding_process',
      key: 'welding_process',
    },
    {
      title: '焊接位置',
      dataIndex: 'welding_position',
      key: 'welding_position',
    },
    {
      title: '焊接长度(m)',
      dataIndex: 'weld_length',
      key: 'weld_length',
    },
    {
      title: '质量结果',
      dataIndex: 'quality_result',
      key: 'quality_result',
      render: (result: string) => {
        const colorMap: Record<string, string> = {
          '合格': 'success',
          '优秀': 'blue',
          '不合格': 'error',
        };
        return result ? <Tag color={colorMap[result] || 'default'}>{result}</Tag> : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: WelderWorkRecord) => (
        <Space>
          <Popconfirm
            title="确定要删除这条工作记录吗？"
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
      title="焊接操作记录"
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加操作记录
        </Button>
      }
    >
      {records.length === 0 && !loading ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无焊接操作记录"
        >
          <Button type="primary" onClick={() => setModalVisible(true)}>
            点击上方按钮添加焊工的日常焊接操作记录
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

      <WorkRecordModal
        visible={modalVisible}
        welderId={welderId}
        onSuccess={handleAddSuccess}
        onCancel={() => setModalVisible(false)}
      />
    </Card>
  );
};

export default WorkRecordList;

