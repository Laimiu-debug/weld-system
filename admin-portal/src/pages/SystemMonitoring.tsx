import React, { useCallback, useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, Button, Space, Alert, Typography } from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DatabaseOutlined,
  UserOutlined,
  ApiOutlined,
  CloudServerOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';

const { Text } = Typography;

const formatUptime = (seconds?: number) => {
  if (!seconds || seconds <= 0) return '-';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}天 ${hours}小时`;
  if (hours > 0) return `${hours}小时 ${mins}分`;
  return `${mins}分`;
};

const statusTag = (value?: string, ok = 'connected') => {
  const connected = value === ok || value === 'healthy';
  const warning = value === 'warning' || value === 'unknown';
  return (
    <Tag color={connected ? 'success' : warning ? 'warning' : 'error'}>
      {value || 'unknown'}
    </Tag>
  );
};

const SystemMonitoring: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [logSummary, setLogSummary] = useState<any>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusResp, logsResp] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getErrorLogs({ page: 1, page_size: 20 }),
      ]);
      setStatus(statusResp);
      const payload = logsResp as any;
      const items = payload?.items || payload?.data?.items || [];
      setLogs(Array.isArray(items) ? items : []);
      setLogSummary(payload?.summary || payload?.data?.summary || null);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || '加载系统监控数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const timer = window.setInterval(() => {
      void loadData();
    }, 30000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, loadData]);

  const health = status?.status || 'unknown';
  const healthColor =
    health === 'healthy' ? '#52c41a' : health === 'unhealthy' || health === 'error' ? '#ff4d4f' : '#faad14';
  const healthLabel =
    health === 'healthy' ? '正常' : health === 'unhealthy' || health === 'error' ? '异常' : health === 'warning' ? '告警' : '未知';

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统监控</h1>
        <Space>
          <Button type={autoRefresh ? 'primary' : 'default'} onClick={() => setAutoRefresh((v) => !v)}>
            {autoRefresh ? '自动刷新：开' : '自动刷新：关'}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {error && (
        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
      )}

      {status?.timestamp && (
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          最近更新：{status.timestamp.replace('T', ' ').slice(0, 19)} UTC
          {autoRefresh ? ' · 每 30 秒自动刷新' : ''}
        </Text>
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={healthLabel}
              valueStyle={{ color: healthColor }}
              prefix={health === 'healthy' ? <CheckCircleOutlined /> : <WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="CPU" value={status?.cpu_usage || 0} suffix="%" prefix={<ApiOutlined />} />
            <Progress
              percent={Number(status?.cpu_usage || 0)}
              showInfo={false}
              status={Number(status?.cpu_usage || 0) >= 90 ? 'exception' : 'normal'}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="内存" value={status?.memory_usage || 0} suffix="%" />
            <Progress
              percent={Number(status?.memory_usage || 0)}
              showInfo={false}
              status={Number(status?.memory_usage || 0) >= 90 ? 'exception' : 'normal'}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="磁盘" value={status?.disk_usage || 0} suffix="%" prefix={<DatabaseOutlined />} />
            <Progress
              percent={Number(status?.disk_usage || 0)}
              showInfo={false}
              status={Number(status?.disk_usage || 0) >= 95 ? 'exception' : 'normal'}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="总用户" value={status?.total_users || 0} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="今日活跃" value={status?.active_users_today || 0} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              近 5 分钟：{status?.active_users_5min ?? status?.active_users ?? 0}
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行时间"
              value={formatUptime(status?.uptime_seconds)}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="24h 错误"
              value={status?.errors_24h ?? logSummary?.recent_errors_24h ?? 0}
              valueStyle={{
                color: (status?.errors_24h ?? logSummary?.recent_errors_24h ?? 0) > 0 ? '#ff4d4f' : undefined,
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Space direction="vertical" size={4}>
              <Text type="secondary">数据库</Text>
              {statusTag(status?.database_status)}
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Space direction="vertical" size={4}>
              <Text type="secondary">Redis</Text>
              {statusTag(status?.redis_status)}
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="今日 API 日志"
              value={status?.api_requests_today || 0}
              prefix={<CloudServerOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              近 1 分钟：{status?.api_requests_per_minute || 0}（依赖 system_logs）
            </Text>
          </Card>
        </Col>
      </Row>

      <Card title="最近错误日志" loading={loading}>
        <Table
          rowKey={(record) => String(record.id || `${record.created_at}-${record.message}`)}
          dataSource={logs}
          pagination={false}
          columns={[
            { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
            {
              title: '级别',
              dataIndex: 'log_level',
              key: 'log_level',
              width: 100,
              render: (level: string) => (
                <Tag color={level === 'critical' ? 'red' : 'orange'}>{level || '-'}</Tag>
              ),
            },
            { title: '类型', dataIndex: 'log_type', key: 'log_type', width: 100 },
            { title: '消息', dataIndex: 'message', key: 'message', ellipsis: true },
            { title: '路径', dataIndex: 'request_path', key: 'request_path', ellipsis: true },
          ]}
          locale={{ emptyText: '暂无错误日志（仅展示 system_logs 中 error/critical）' }}
        />
      </Card>
    </div>
  );
};

export default SystemMonitoring;
