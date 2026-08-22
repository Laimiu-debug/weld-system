import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthContext } from '@/contexts/AuthContext';
import BrandMark from '@/components/BrandMark';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuthContext();

  const handleSubmit = async (values: LoginForm) => {
    setLoading(true);
    setError('');

    try {
      const result = await login(values.username, values.password);
      if (!result) {
        setError('登录失败，请检查用户名和密码');
      }
    } catch (error: any) {
      setError(error.message || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page">
      <Card className="admin-login-card">
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <BrandMark size={54} />
          <Title level={2} style={{ color: '#0f172a', marginTop: 12, marginBottom: 8, letterSpacing: '0.06em' }}>
            焊序
          </Title>
          <Title level={4} type="secondary" style={{ marginBottom: 0, fontWeight: 500 }}>
            管理员门户
          </Title>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          name="login"
          onFinish={handleSubmit}
          size="large"
          autoComplete="off"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名 / 邮箱"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              style={{ width: '100%', height: 48 }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            请使用管理员账号登录 · 如遇问题请联系系统管理员
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Login;
