import React from 'react';
import { Card, Button, Space, Typography } from 'antd';
import { useAuthContext } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const { Title, Text, Paragraph } = Typography;

const AuthTest: React.FC = () => {
  const { isAuthenticated, loading, user, login, logout } = useAuthContext();
  const navigate = useNavigate();

  console.log('=== AUTH TEST PAGE ===');
  console.log('AuthTest - isAuthenticated:', isAuthenticated);
  console.log('AuthTest - loading:', loading);
  console.log('AuthTest - user:', user);
  console.log('AuthTest - localStorage token:', localStorage.getItem('admin_token'));
  console.log('AuthTest - localStorage user:', localStorage.getItem('admin_user'));

  const handleLogout = async () => {
    console.log('AuthTest: Manual logout triggered');
    await logout();
  };

  const handleNavigateToDashboard = () => {
    console.log('AuthTest: Navigate to dashboard');
    navigate('/dashboard');
  };

  const handleTestAPI = async () => {
    console.log('AuthTest: Testing API call...');

    // 详细检查token
    const token = localStorage.getItem('admin_token');
    console.log('=== TOKEN DEBUG ===');
    console.log('Token exists:', !!token);
    console.log('Token length:', token?.length || 0);
    console.log('Token starts with Bearer:', token?.startsWith('Bearer '));
    console.log('Token content:', token);

    try {
      const response = await fetch('/api/v1/admin/system/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      console.log('AuthTest: API response status:', response.status);
      console.log('AuthTest: API response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log('AuthTest: API response data:', data);
      } else {
        const errorText = await response.text();
        console.log('AuthTest: API error response:', errorText);
      }
    } catch (error) {
      console.error('AuthTest: API call failed:', error);
    }
  };

  const handleTestLogin = async () => {
    console.log('=== TEST LOGIN ===');
    try {
      const response = await fetch('/api/v1/admin/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=Laimiu&password=ghzzz123'
      });
      console.log('Test login response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Test login response data:', data);

        if (data.access_token) {
          console.log('Test login - received token:', data.access_token);
        }
      } else {
        const errorText = await response.text();
        console.log('Test login error:', errorText);
      }
    } catch (error) {
      console.error('Test login failed:', error);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>认证状态测试页面</Title>
      
      <Card title="认证状态信息" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Loading: </Text>
            <Text>{loading ? '是' : '否'}</Text>
          </div>
          <div>
            <Text strong>已认证: </Text>
            <Text>{isAuthenticated ? '是' : '否'}</Text>
          </div>
          <div>
            <Text strong>用户信息: </Text>
            <Text>{user ? JSON.stringify(user, null, 2) : '无'}</Text>
          </div>
          <div>
            <Text strong>LocalStorage Token: </Text>
            <Text>{localStorage.getItem('admin_token') ? '存在' : '不存在'}</Text>
          </div>
          <div>
            <Text strong>LocalStorage User: </Text>
            <Text>{localStorage.getItem('admin_user') ? '存在' : '不存在'}</Text>
          </div>
        </Space>
      </Card>

      <Card title="测试操作" style={{ marginBottom: '16px' }}>
        <Space wrap>
          <Button type="primary" onClick={handleNavigateToDashboard}>
            导航到仪表盘
          </Button>
          <Button onClick={handleTestAPI}>
            测试API调用
          </Button>
          <Button onClick={handleTestLogin} style={{ backgroundColor: '#52c41a', borderColor: '#52c411', color: 'white' }}>
            测试直接登录
          </Button>
          <Button danger onClick={handleLogout}>
            退出登录
          </Button>
        </Space>
      </Card>

      <Card title="浏览器控制台日志">
        <Paragraph>
          请打开浏览器控制台查看详细的认证流程日志。搜索以下关键词：
        </Paragraph>
        <ul>
          <li><code>=== AUTH PROVIDER</code> - 认证提供者初始化</li>
          <li><code>=== APP CONTENT</code> - 应用路由检查</li>
          <li><code>=== API INTERCEPTOR</code> - API拦截器</li>
          <li><code>=== DASHBOARD</code> - 仪表盘加载</li>
          <li><code>=== AUTH TEST</code> - 认证测试页面</li>
        </ul>
      </Card>
    </div>
  );
};

export default AuthTest;