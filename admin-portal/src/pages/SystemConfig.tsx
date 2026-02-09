import React, { useState } from 'react';
import { Card, Form, Switch, InputNumber, Button, Space, message, Row, Col } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';

const SystemConfig: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  // 模拟系统配置数据
  const initialConfig = {
    maintenance_mode: false,
    registration_enabled: true,
    max_upload_size_mb: 100,
    session_timeout_minutes: 60,
    email_service_enabled: true,
    storage_service_enabled: true,
    backup_enabled: true,
    auto_backup_interval_hours: 24,
    log_retention_days: 30,
  };

  const handleSubmit = async (_values: any) => {
    try {
      setLoading(true);
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));

      message.success('系统配置保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue(initialConfig);
    message.info('配置已重置');
  };

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统配置</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </Space>
      </div>

      <Form
        form={form}
        layout="vertical"
        initialValues={initialConfig}
        onFinish={handleSubmit}
        style={{ maxWidth: 800 }}
      >
        {/* 基础配置 */}
        <Card title={<span><SettingOutlined /> 基础配置</span>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="maintenance_mode"
                label="维护模式"
                valuePropName="checked"
                extra="启用后用户将无法访问系统"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="registration_enabled"
                label="用户注册"
                valuePropName="checked"
                extra="控制新用户是否可以注册"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="max_upload_size_mb"
                label="最大上传大小 (MB)"
                extra="单个文件的最大大小限制"
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="session_timeout_minutes"
                label="会话超时时间 (分钟)"
                extra="用户无操作后自动退出登录的时间"
              >
                <InputNumber min={5} max={1440} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 服务配置 */}
        <Card title="服务配置" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="email_service_enabled"
                label="邮件服务"
                valuePropName="checked"
                extra="系统邮件发送功能"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="storage_service_enabled"
                label="存储服务"
                valuePropName="checked"
                extra="文件存储和备份服务"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="backup_enabled"
                label="自动备份"
                valuePropName="checked"
                extra="是否启用数据库自动备份"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="auto_backup_interval_hours"
                label="备份间隔 (小时)"
                extra="自动备份的执行间隔"
              >
                <InputNumber min={1} max={168} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="log_retention_days"
                label="日志保留天数"
                extra="系统日志的保留时间"
              >
                <InputNumber min={1} max={365} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
              保存配置
            </Button>
            <Button onClick={handleReset}>
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
};

export default SystemConfig;
