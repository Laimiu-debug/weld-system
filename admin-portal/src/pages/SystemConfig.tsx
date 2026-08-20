import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Switch,
  InputNumber,
  Button,
  Space,
  message,
  Row,
  Col,
  Alert,
} from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import { apiService } from '@/services/api';

interface SystemConfigForm {
  maintenance_mode: boolean;
  registration_enabled: boolean;
  max_upload_size_mb: number;
  session_timeout_minutes: number;
}

const SystemConfig: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm<SystemConfigForm>();

  const loadConfig = async () => {
    setLoading(true);
    try {
      const resp = await apiService.get<any>('/system/config');
      const data = resp?.data?.data || resp?.data || resp;
      if (data) {
        form.setFieldsValue({
          maintenance_mode: !!data.maintenance_mode,
          registration_enabled: data.registration_enabled !== false,
          max_upload_size_mb: data.max_upload_size_mb ?? 100,
          session_timeout_minutes: data.session_timeout_minutes ?? 60,
        });
      }
    } catch (error) {
      console.error(error);
      message.error('加载系统配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadConfig();
  }, []);

  const handleSubmit = async (values: SystemConfigForm) => {
    try {
      setSaving(true);
      await apiService.put('/system/config', values);
      message.success('系统配置已保存并生效');
      await loadConfig();
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统配置</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void loadConfig()} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="配置会持久化并立即影响用户端"
        description="维护模式会拦截用户 API；关闭注册后无法新注册；会话超时影响新签发的登录令牌；上传上限影响通用附件上传。"
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        style={{ maxWidth: 800 }}
        disabled={loading}
      >
        <Card
          title={
            <span>
              <SettingOutlined /> 基础配置
            </span>
          }
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="maintenance_mode"
                label="维护模式"
                valuePropName="checked"
                extra="开启后用户端接口返回 503；管理门户不受影响"
              >
                <Switch checkedChildren="开" unCheckedChildren="关" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="registration_enabled"
                label="用户注册"
                valuePropName="checked"
                extra="关闭后注册接口拒绝新用户"
              >
                <Switch checkedChildren="允许" unCheckedChildren="关闭" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_upload_size_mb"
                label="最大上传 (MB)"
                extra="通用附件上传上限（头像另有 5MB 封顶）"
              >
                <InputNumber min={1} max={1024} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="session_timeout_minutes"
                label="会话超时 (分钟)"
                extra="影响此后新登录签发的访问令牌有效期"
              >
                <InputNumber min={5} max={1440} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
            保存配置
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default SystemConfig;
