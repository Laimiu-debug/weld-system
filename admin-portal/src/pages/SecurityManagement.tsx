import React, { useCallback, useEffect, useState } from 'react';
import { Card, Table, Button, Space, Tag, Badge, Alert } from 'antd';
import {
  ReloadOutlined,
  EyeOutlined,
  UserOutlined,
  SecurityScanOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';

interface AdminAccount {
  key: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  lastLogin: string;
  status: string;
}

interface SecurityLog {
  key: string;
  time: string;
  event: string;
  user: string;
  ip: string;
  location: string;
  status: 'success' | 'warning' | 'error';
  details: string;
}

const SecurityManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adminData, setAdminData] = useState<AdminAccount[]>([]);
  const [securityLogsData, setSecurityLogsData] = useState<SecurityLog[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [adminsResp, usersResp, logsResp] = await Promise.all([
        apiService.getAdmins(),
        apiService.getUsers({ page: 1, page_size: 20, sort_field: 'last_login_at', sort_order: 'desc' }),
        apiService.getErrorLogs({ page: 1, page_size: 20 }),
      ]);

      const adminItems = (adminsResp as any)?.items || (adminsResp as any)?.data?.items || [];
      setAdminData(
        (Array.isArray(adminItems) ? adminItems : []).map((item: any) => ({
          key: String(item.id),
          username: item.username,
          email: item.email,
          role: item.role || (item.is_super_admin ? 'super_admin' : 'admin'),
          permissions: Array.isArray(item.permissions) ? item.permissions : [],
          lastLogin: item.last_login_at || '-',
          status: item.status || (item.is_active ? 'active' : 'inactive'),
        }))
      );

      const userItems = (usersResp as any)?.items || (usersResp as any)?.data?.items || [];
      const loginLogs: SecurityLog[] = (Array.isArray(userItems) ? userItems : [])
        .filter((item: any) => item.last_login_at)
        .map((item: any) => ({
          key: `login-${item.id}`,
          time: item.last_login_at,
          event: '用户登录',
          user: item.username || item.email,
          ip: item.last_login_ip || '-',
          location: '-',
          status: 'success' as const,
          details: `${item.full_name || item.username || item.email} 最近登录`,
        }));

      const errorItems = (logsResp as any)?.items || (logsResp as any)?.data?.items || [];
      const errorLogs: SecurityLog[] = (Array.isArray(errorItems) ? errorItems : []).map((item: any, index: number) => ({
        key: `err-${item.id || index}`,
        time: item.created_at || item.time || '-',
        event: item.event || item.level || '系统错误',
        user: item.user || item.username || '-',
        ip: item.ip || '-',
        location: item.location || '-',
        status: 'error' as const,
        details: item.message || item.details || '',
      }));

      setSecurityLogsData([...errorLogs, ...loginLogs]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '加载安全管理数据失败');
      setAdminData([]);
      setSecurityLogsData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const adminColumns = [
    {
      title: '管理员信息',
      key: 'admin_info',
      render: (record: AdminAccount) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <UserOutlined style={{ marginRight: 4 }} />
            {record.username}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            {record.email}
          </div>
        </div>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const roleConfig: Record<string, { text: string; color: string }> = {
          super_admin: { text: '超级管理员', color: 'red' },
          admin: { text: '管理员', color: 'orange' },
        };
        const config = roleConfig[role] || { text: role, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <div style={{ fontSize: '12px' }}>
          {permissions.includes('all') ? (
            <Tag color="red">全部权限</Tag>
          ) : permissions.length === 0 ? (
            <Tag>未配置</Tag>
          ) : (
            permissions.map((perm) => (
              <Tag key={perm} style={{ marginBottom: 2 }}>
                {perm}
              </Tag>
            ))
          )}
        </div>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge
          status={status === 'active' ? 'success' : 'error'}
          text={status === 'active' ? '正常' : '禁用'}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: () => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} disabled>
            查看
          </Button>
        </Space>
      ),
    },
  ];

  const securityLogsColumns = [
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
      width: 180,
    },
    {
      title: '事件',
      dataIndex: 'event',
      key: 'event',
      render: (event: string) => (
        <span style={{
          color: event.includes('失败') || event.includes('错误') ? '#ff4d4f' : '#1F5EFF',
          fontWeight: 500
        }}>
          {event}
        </span>
      ),
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      render: (ip: string) => (
        <code style={{ backgroundColor: '#f5f5f5', padding: '2px 6px', borderRadius: '4px' }}>
          {ip}
        </code>
      ),
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: SecurityLog['status']) => {
        switch (status) {
          case 'success':
            return <Badge status="success" text="成功" />
          case 'warning':
            return <Badge status="warning" text="警告" />
          case 'error':
            return <Badge status="error" text="失败" />
          default: {
            const _exhaustive: never = status
            return _exhaustive
          }
        }
      },
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">安全管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {error && (
        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
      )}

      <Card
        title={
          <span>
            <UserOutlined style={{ marginRight: 8 }} />
            管理员列表
          </span>
        }
        style={{ marginBottom: 16 }}
      >
        <Table
          columns={adminColumns}
          dataSource={adminData}
          loading={loading}
          pagination={false}
        />
      </Card>

      <Card
        title={
          <span>
            <SecurityScanOutlined style={{ marginRight: 8 }} />
            安全日志
          </span>
        }
      >
        <Table
          columns={securityLogsColumns}
          dataSource={securityLogsData}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  );
};

export default SecurityManagement;
