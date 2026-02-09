import React, { useEffect, useState } from 'react';
import { Card, Button, Space, Typography } from 'antd';
import { useAuthContext } from '@/contexts/AuthContext';
import authService from '@/services/auth';

const { Text, Title } = Typography;

const DebugPage: React.FC = () => {
  const { user, isAuthenticated, loading } = useAuthContext();
  const [debugInfo, setDebugInfo] = useState<any>({});

  useEffect(() => {
    const collectDebugInfo = () => {
      setDebugInfo({
        localStorage: {
          admin_token: localStorage.getItem('admin_token'),
          admin_user: localStorage.getItem('admin_user'),
        },
        authService: {
          currentUser: authService.getCurrentUser(),
          isAuthenticated: authService.isAuthenticated(),
        },
        context: {
          user,
          isAuthenticated,
          loading,
        },
        timestamp: new Date().toISOString(),
      });
    };

    collectDebugInfo();
    const interval = setInterval(collectDebugInfo, 1000);
    return () => clearInterval(interval);
  }, [user, isAuthenticated, loading]);

  const handleClearAuth = () => {
    authService.clearAuth();
    window.location.reload();
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>认证状态调试页面</Title>

      <Card title="Context 状态" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text><strong>Loading:</strong> {loading.toString()}</Text>
          <Text><strong>Is Authenticated:</strong> {isAuthenticated.toString()}</Text>
          <Text><strong>User:</strong> {JSON.stringify(user, null, 2)}</Text>
        </Space>
      </Card>

      <Card title="localStorage 内容" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text><strong>admin_token:</strong> {debugInfo.localStorage?.admin_token || 'null'}</Text>
          <Text><strong>admin_user:</strong> {debugInfo.localStorage?.admin_user || 'null'}</Text>
        </Space>
      </Card>

      <Card title="AuthService 状态" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text><strong>Current User:</strong> {JSON.stringify(debugInfo.authService?.currentUser, null, 2)}</Text>
          <Text><strong>Is Authenticated:</strong> {debugInfo.authService?.isAuthenticated?.toString()}</Text>
        </Space>
      </Card>

      <Card title="完整调试信息" style={{ marginBottom: '20px' }}>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', overflow: 'auto' }}>
          {JSON.stringify(debugInfo, null, 2)}
        </pre>
      </Card>

      <Space>
        <Button onClick={() => window.location.reload()}>刷新页面</Button>
        <Button onClick={handleClearAuth} danger>清除认证</Button>
        <Button onClick={() => window.location.href = '/login'}>跳转登录</Button>
        <Button onClick={() => window.location.href = '/dashboard'}>跳转仪表盘</Button>
      </Space>
    </div>
  );
};

export default DebugPage;