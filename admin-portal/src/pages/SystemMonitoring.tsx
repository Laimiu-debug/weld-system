import React, { useCallback, useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, Button, Space, Alert } from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DatabaseOutlined,
  UserOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';

const SystemMonitoring: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusResp, logsResp] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getErrorLogs({ page: 1, page_size: 20 }),
      ]);
      setStatus(statusResp);
      const items = (logsResp as any)?.items || (logsResp as any)?.data?.items || [];
      setLogs(Array.isArray(items) ? items : []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '加载系统监控数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const health = status?.status || 'unknown';
  const healthColor = health === 'healthy' ? '#52c41a' : health === 'unhealthy' ? '#ff4d4f' : '#faad14';

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统监控</h1>
        <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
          刷新
        </Button>
      </div>

      {error && (
        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={health === 'healthy' ? '正常' : health === 'unhealthy' ? '异常' : '未知'}
              valueStyle={{ color: healthColor }}
              prefix={health === 'healthy' ? <CheckCircleOutlined /> : <WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="CPU" value={status?.cpu_usage || 0} suffix="%" prefix={<ApiOutlined />} />
            <Progress percent={Number(status?.cpu_usage || 0)} showInfo={false} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="内存" value={status?.memory_usage || 0} suffix="%" />
            <Progress percent={Number(status?.memory_usage || 0)} showInfo={false} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="磁盘" value={status?.disk_usage || 0} suffix="%" prefix={<DatabaseOutlined />} />
            <Progress percent={Number(status?.disk_usage || 0)} showInfo={false} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="总用户" value={status?.total_users || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="今日活跃" value={status?.active_users_today || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="数据库" value={status?.database_status === 'connected' ? '已连接' : '未连接'} />
          </Card>
        </Col>
      </Row>

      <Card title="最近错误日志" loading={loading}>
        <Table
          rowKey={(record) => String(record.id || record.created_at)}
          dataSource={logs}
          pagination={false}
          columns={[
            { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
            {
              title: '级别',
              dataIndex: 'log_level',
              key: 'log_level',
              width: 100,
              render: (level: string) => <Tag color={level === 'critical' ? 'red' : 'orange'}>{level || '-'}</Tag>,
            },
            { title: '类型', dataIndex: 'log_type', key: 'log_type', width: 100 },
            { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
            { title: '路径', dataIndex: 'request_path', key: 'request_path', ellipsis: true },
          ]}
          locale={{ emptyText: '暂无错误日志' }}
        />
      </Card>
    </div>
  );
};

export default SystemMonitoring;
