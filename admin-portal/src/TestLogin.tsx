import React from 'react';
import { Button, Card, Typography, Space, Alert } from 'antd';

const { Text } = Typography;

const TestLogin: React.FC = () => {
  const handleTestLogin = async () => {
    console.log('=== STARTING TEST LOGIN ===');

    try {
      const loginUrl = '/api/v1/admin/auth/login';
      const username = 'Laimiu';
      const password = 'ghzzz123';

      console.log('Sending request to:', loginUrl);
      console.log('Credentials:', { username, password });

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Login failed:', errorText);
        return;
      }

      const authData = await response.json();
      console.log('=== LOGIN RESPONSE ===');
      console.log('Raw response:', authData);
      console.log('Keys:', Object.keys(authData));
      console.log('Has access_token:', 'access_token' in authData);
      console.log('access_token value:', authData.access_token);
      console.log('Has admin:', 'admin' in authData);

      if (authData.access_token && authData.admin) {
        console.log('=== STORING DATA ===');

        // 存储 token
        localStorage.setItem('admin_token', authData.access_token);
        console.log('Token stored. Verification:', localStorage.getItem('admin_token'));

        // 存储用户信息
        const user = {
          id: authData.admin.id?.toString() || '',
          username: authData.admin.username || '',
          email: authData.admin.email || '',
          full_name: authData.admin.full_name || '',
          is_admin: true,
          admin_level: authData.admin.admin_level || (authData.admin.is_super_admin ? 'super_admin' : 'admin'),
          permissions: authData.admin.is_super_admin ? [
            'user_management', 'enterprise_management', 'subscription_management',
            'system_monitoring', 'data_statistics', 'announcement_management',
            'system_config', 'security_management'
          ] : ['user_management', 'data_statistics']
        };

        localStorage.setItem('admin_user', JSON.stringify(user));
        console.log('User stored. Verification:', localStorage.getItem('admin_user'));

        console.log('=== LOGIN TEST COMPLETE ===');
        window.location.href = '/dashboard';
      } else {
        console.error('=== LOGIN TEST FAILED ===');
        console.error('Missing required data:', {
          hasToken: !!authData.access_token,
          hasAdmin: !!authData.admin
        });
      }

    } catch (error) {
      console.error('Test login error:', error);
    }
  };

  const checkStorage = () => {
    console.log('=== CURRENT STORAGE ===');
    console.log('Token:', localStorage.getItem('admin_token'));
    console.log('User:', localStorage.getItem('admin_user'));
  };

  const clearStorage = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    console.log('Storage cleared');
    window.location.reload();
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <Card title="登录测试工具" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button type="primary" onClick={handleTestLogin} block>
            执行测试登录
          </Button>
          <Button onClick={checkStorage} block>
            检查当前存储
          </Button>
          <Button onClick={clearStorage} danger block>
            清除存储数据
          </Button>
        </Space>
      </Card>

      <Alert
        message="测试说明"
        description="点击'执行测试登录'按钮，将使用凭据 Laimiu/ghzzz123 进行登录测试。查看控制台输出了解详细过程。"
        type="info"
        showIcon
      />
    </div>
  );
};

export default TestLogin;