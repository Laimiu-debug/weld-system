import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Switch,
  Input,
  InputNumber,
  Button,
  Space,
  message,
  Row,
  Col,
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
      message.success('系统配置保存成功');
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
                extra="启用后用户将无法访问系统（部分字段暂未持久化）"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="registration_enabled"
                label="用户注册"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_upload_size_mb" label="最大上传 (MB)">
                <InputNumber min={1} max={1024} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="session_timeout_minutes" label="会话超时 (分钟)">
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
