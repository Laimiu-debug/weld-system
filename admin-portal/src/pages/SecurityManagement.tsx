import React, { useState } from 'react';
import { Card, Table, Button, Space, Input, Tag, Badge, Row, Col, message, Modal } from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  SafetyOutlined,
  UserOutlined,
  SecurityScanOutlined,
  LockOutlined
} from '@ant-design/icons';

const { Search } = Input;

const SecurityManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);

  // 模拟管理员数据
  const adminData = [
    {
      key: '1',
      username: 'admin',
      email: 'admin@welding-system.com',
      role: 'super_admin',
      permissions: ['all'],
      lastLogin: '2025-10-16 09:30',
      status: 'active',
      createdBy: 'system'
    },
    {
      key: '2',
      username: 'security_admin',
      email: 'security@welding-system.com',
      role: 'admin',
      permissions: ['user_management', 'security_logs'],
      lastLogin: '2025-10-16 08:15',
      status: 'active',
      createdBy: 'admin'
    }
  ];

  // 模拟安全日志数据
  const securityLogsData = [
    {
      key: '1',
      time: '2025-10-16 10:30:22',
      event: '用户登录',
      user: 'admin',
      ip: '192.168.1.100',
      location: '上海',
      status: 'success',
      details: '管理员登录成功'
    },
    {
      key: '2',
      time: '2025-10-16 10:25:15',
      event: '权限修改',
      user: 'security_admin',
      ip: '192.168.1.101',
      location: '北京',
      status: 'success',
      details: '修改用户权限配置'
    },
    {
      key: '3',
      time: '2025-10-16 10:20:08',
      event: '登录失败',
      user: 'unknown',
      ip: '192.168.1.200',
      location: '广州',
      status: 'warning',
      details: '密码错误，登录失败'
    }
  ];

  const adminColumns = [
    {
      title: '管理员信息',
      key: 'admin_info',
      render: (record: any) => (
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
          ) : (
            permissions.map((perm, index) => (
              <Tag key={index} style={{ marginBottom: 2 }}>
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
          <Button type="link" size="small" icon={<EyeOutlined />}>
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
          color: event.includes('失败') || event.includes('警告') ? '#ff4d4f' : '#1890ff',
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
      render: (status: string) => (
        <Badge
          status={status === 'success' ? 'success' : status === 'warning' ? 'warning' : 'error'}
          text={status === 'success' ? '成功' : status === 'warning' ? '警告' : '失败'}
        />
      ),
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
  ];

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      message.success('数据已刷新');
    }, 1000);
  };

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">安全管理</h1>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => message.info('添加管理员功能开发中')}
          >
            添加管理员
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 管理员列表 */}
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

      {/* 安全日志 */}
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
