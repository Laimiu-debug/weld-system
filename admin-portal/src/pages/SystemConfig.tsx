import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Switch,
  Input,
  InputNumber,
  Select,
  Button,
  Space,
  message,
  Row,
  Col,
  Alert,
  Divider,
  Popconfirm,
  Statistic,
  Table,
  Tag,
} from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, SaveOutlined, ReloadOutlined, SettingOutlined, RobotOutlined } from '@ant-design/icons';
import { apiService } from '@/services/api';

interface SystemConfigForm {
  maintenance_mode: boolean;
  registration_enabled: boolean;
  max_upload_size_mb: number;
  session_timeout_minutes: number;
  ai_provider: 'openai_responses' | 'openai_compatible_chat';
  ai_base_url: string;
  ai_model: string;
  ai_api_key?: string;
  ai_name?: string;
  ai_task_types?: string[];
  ai_complexity_level?: 'simple' | 'standard' | 'advanced';
  ai_point_multiplier?: number;
  ai_priority?: number;
  ai_is_default?: boolean;
}

interface PlatformModel extends Record<string, any> {
  id: string;
  name: string;
  model: string;
  provider: string;
  masked_api_key: string;
  task_types: string[];
  complexity_level: string;
  point_multiplier: number;
  priority: number;
  is_default: boolean;
  last_test_status: string;
}

const providerPresets = [
  { value: 'openai', label: 'OpenAI', provider: 'openai_responses', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { value: 'deepseek', label: 'DeepSeek', provider: 'openai_compatible_chat', baseUrl: 'https://api.deepseek.com', model: 'deepseek-v4-flash' },
  { value: 'qwen', label: '阿里云百炼 / 通义千问', provider: 'openai_compatible_chat', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { value: 'kimi', label: 'Moonshot / Kimi', provider: 'openai_compatible_chat', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { value: 'zhipu', label: '智谱 GLM', provider: 'openai_compatible_chat', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { value: 'siliconflow', label: '硅基流动', provider: 'openai_compatible_chat', baseUrl: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-72B-Instruct' },
];

const SystemConfig: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingAI, setTestingAI] = useState(false);
  const [aiKeyHint, setAiKeyHint] = useState('尚未配置');
  const [models, setModels] = useState<PlatformModel[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [editingModelId, setEditingModelId] = useState<string | null>(null);
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
          ai_provider: data.ai_platform?.provider || 'openai_responses',
          ai_base_url: data.ai_platform?.base_url || 'https://api.openai.com/v1',
          ai_model: data.ai_platform?.model || '',
          ai_api_key: '',
          ai_name: data.ai_platform?.name || '平台默认模型',
          ai_task_types: data.ai_platform?.task_types || [],
          ai_complexity_level: data.ai_platform?.complexity_level || 'standard',
          ai_point_multiplier: data.ai_platform?.point_multiplier || 1,
          ai_priority: data.ai_platform?.priority ?? 100,
          ai_is_default: data.ai_platform?.is_default !== false,
        });
        setEditingModelId(data.ai_platform?.source === 'admin' ? data.ai_platform.id : null);
        setAiKeyHint(data.ai_platform?.key_configured ? data.ai_platform.masked_api_key : '尚未配置');
      }
      const [modelResp, usageResp] = await Promise.all([
        apiService.get<any>('/system/config/ai-models'),
        apiService.get<any>('/system/ai/usage?days=30'),
      ]);
      const modelData = (modelResp as any)?.data?.data ?? (modelResp as any)?.data ?? modelResp;
      const usageData = (usageResp as any)?.data?.data ?? (usageResp as any)?.data ?? usageResp;
      setModels(Array.isArray(modelData) ? modelData : []);
      setUsage(usageData || null);
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
      const runtime = {
        maintenance_mode: values.maintenance_mode,
        registration_enabled: values.registration_enabled,
        max_upload_size_mb: values.max_upload_size_mb,
        session_timeout_minutes: values.session_timeout_minutes,
      };
      await apiService.put('/system/config', runtime);
      message.success('系统配置已保存并生效');
      await loadConfig();
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const saveAIModel = async () => {
    const values = await form.validateFields([
      'ai_name', 'ai_provider', 'ai_base_url', 'ai_model', 'ai_api_key',
      'ai_task_types', 'ai_complexity_level', 'ai_point_multiplier', 'ai_priority', 'ai_is_default',
    ]);
    const payload = {
      name: values.ai_name,
      provider: values.ai_provider,
      base_url: values.ai_base_url,
      model: values.ai_model,
      api_key: values.ai_api_key || undefined,
      task_types: values.ai_task_types || [],
      complexity_level: values.ai_complexity_level,
      point_multiplier: values.ai_point_multiplier,
      priority: values.ai_priority,
      is_default: !!values.ai_is_default,
    };
    setSaving(true);
    try {
      if (editingModelId) {
        await apiService.put(`/system/config/ai-models/${editingModelId}`, payload);
      } else {
        await apiService.post('/system/config/ai-models', payload);
      }
      message.success(editingModelId ? '模型配置已更新' : '模型配置已创建');
      await loadConfig();
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '模型配置保存失败');
    } finally {
      setSaving(false);
    }
  };

  const editModel = (item: PlatformModel) => {
    setEditingModelId(item.id);
    setAiKeyHint(item.masked_api_key);
    form.setFieldsValue({
      ai_name: item.name,
      ai_provider: item.provider as SystemConfigForm['ai_provider'],
      ai_base_url: item.base_url,
      ai_model: item.model,
      ai_api_key: '',
      ai_task_types: item.task_types || [],
      ai_complexity_level: item.complexity_level as SystemConfigForm['ai_complexity_level'],
      ai_point_multiplier: item.point_multiplier,
      ai_priority: item.priority,
      ai_is_default: item.is_default,
    });
  };

  const newModel = () => {
    setEditingModelId(null);
    setAiKeyHint('新配置尚未保存');
    form.setFieldsValue({
      ai_name: '', ai_provider: 'openai_compatible_chat', ai_base_url: 'https://api.deepseek.com',
      ai_model: 'deepseek-v4-flash', ai_api_key: '', ai_task_types: [],
      ai_complexity_level: 'standard', ai_point_multiplier: 1, ai_priority: 100, ai_is_default: false,
    });
  };

  const testAIConnection = async () => {
    try {
      const values = await form.validateFields(['ai_provider', 'ai_base_url', 'ai_model']);
      setTestingAI(true);
      const enteredKey = form.getFieldValue('ai_api_key');
      const resp = editingModelId && !enteredKey
        ? await apiService.post<any>(`/system/config/ai-models/${editingModelId}/test`, {})
        : await apiService.post<any>('/system/config/test-ai', {
            provider: values.ai_provider,
            base_url: values.ai_base_url,
            model: values.ai_model,
            api_key: enteredKey || undefined,
            task_types: form.getFieldValue('ai_task_types') || [],
          });
      const result = resp?.data?.data || resp?.data || resp;
      result.success ? message.success(result.message) : message.error(result.message || '连接测试失败');
    } catch (error) {
      message.error('连接测试失败，请检查地址、模型和 API Key');
    } finally {
      setTestingAI(false);
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

        <Card
          title={<span><RobotOutlined /> 平台大模型与任务路由</span>}
          extra={<Button icon={<PlusOutlined />} onClick={newModel}>新增模型</Button>}
          style={{ marginBottom: 16 }}
        >
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message={`API Key：${aiKeyHint}`}
            description="可同时配置多个模型。系统按任务类型和难度选择模型；只有测试通过的模型才会提供给用户端。适用于图纸识别（或留空适用于全部任务）的模型会额外验证图片输入。"
          />
          {!!models.length && (
            <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
              {models.map((item) => (
                <Card key={item.id} size="small">
                  <Row align="middle" gutter={12}>
                    <Col flex="auto">
                      <Space wrap>
                        <strong>{item.name}</strong><Tag>{item.model}</Tag>
                        <Tag color={item.complexity_level === 'advanced' ? 'purple' : item.complexity_level === 'simple' ? 'green' : 'blue'}>{item.complexity_level}</Tag>
                        <Tag color="orange">{item.point_multiplier}× 积分</Tag>
                        {item.is_default && <Tag color="gold">默认</Tag>}
                        <Tag color={item.last_test_status === 'success' ? 'success' : item.last_test_status === 'failed' ? 'error' : 'default'}>{item.last_test_status}</Tag>
                      </Space>
                      <div style={{ color: '#64748b', marginTop: 6 }}>任务：{item.task_types?.length ? item.task_types.join('、') : '全部任务'} · Key {item.masked_api_key}</div>
                    </Col>
                    <Col>
                      <Space>
                        <Button icon={<EditOutlined />} onClick={() => editModel(item)}>编辑</Button>
                        <Button onClick={async () => {
                          const resp = await apiService.post<any>(`/system/config/ai-models/${item.id}/test`, {});
                          const result = resp?.data?.data || resp?.data || resp;
                          result.success ? message.success(`${item.name}：${result.message}`) : message.error(`${item.name}：${result.message}`);
                          await loadConfig();
                        }}>测试</Button>
                        <Popconfirm title="停用这个模型？" onConfirm={async () => { await apiService.delete(`/system/config/ai-models/${item.id}`); await loadConfig(); }}>
                          <Button danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              ))}
            </Space>
          )}
          <Divider>{editingModelId ? '编辑模型' : '新增模型'}</Divider>
          <Form.Item name="ai_name" label="配置名称" rules={[{ required: true }]}>
            <Input placeholder="例如：简单任务 / 高精度图纸" maxLength={100} />
          </Form.Item>
          <Form.Item label="服务商预设">
            <Select
              placeholder="选择后自动填写协议、地址和推荐模型"
              options={providerPresets.map(({ value, label }) => ({ value, label }))}
              onChange={(value) => {
                const preset = providerPresets.find((item) => item.value === value);
                if (preset) form.setFieldsValue({
                  ai_provider: preset.provider as SystemConfigForm['ai_provider'],
                  ai_base_url: preset.baseUrl,
                  ai_model: preset.model,
                });
              }}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="ai_provider" label="接口协议" rules={[{ required: true }]}>
                <Select options={[
                  { value: 'openai_responses', label: 'OpenAI Responses' },
                  { value: 'openai_compatible_chat', label: 'OpenAI 兼容 Chat Completions' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ai_model" label="模型名称" extra="填写模型名称后，保存时会启用平台 AI 配置">
                <Input placeholder="例如：deepseek-v4-flash" maxLength={120} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="ai_base_url" label="接口地址" rules={[{ required: true, type: 'url', message: '请输入完整 HTTPS 地址' }]}>
            <Input placeholder="https://api.example.com/v1" maxLength={500} />
          </Form.Item>
          <Form.Item name="ai_api_key" label="API Key" extra="首次配置必须填写；后续留空不会覆盖已保存的 Key">
            <Input.Password autoComplete="new-password" maxLength={500} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="ai_complexity_level" label="难度等级" rules={[{ required: true }]}>
                <Select options={[{ value: 'simple', label: '简单' }, { value: 'standard', label: '标准' }, { value: 'advanced', label: '困难' }]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="ai_point_multiplier" label="积分倍率" rules={[{ required: true }]}>
                <InputNumber min={0.1} max={20} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="ai_task_types" label="适用任务（留空代表全部）">
            <Select mode="multiple" options={[
              { value: 'wps_import', label: 'WPS 导入' }, { value: 'pqr_import', label: 'PQR 导入' },
              { value: 'ppqr_import', label: 'pPQR 导入' }, { value: 'welder_import', label: '焊工导入' },
              { value: 'drawing_import', label: '图纸识别' }, { value: 'general', label: '通用任务' },
            ]} />
          </Form.Item>
          <Row gutter={16} align="middle">
            <Col span={12}><Form.Item name="ai_priority" label="路由优先级（越小越优先）"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><Form.Item name="ai_is_default" label="设为兜底模型" valuePropName="checked"><Switch /></Form.Item></Col>
          </Row>
          <Space>
            <Button icon={<RobotOutlined />} loading={testingAI} onClick={() => void testAIConnection()}>测试当前填写</Button>
            <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => void saveAIModel()}>保存模型</Button>
          </Space>
        </Card>

        <Card title="近 30 天平台 AI 用量" style={{ marginBottom: 16 }}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}><Statistic title="任务数" value={usage?.totals?.tasks || 0} /></Col>
            <Col span={6}><Statistic title="输入 Token" value={usage?.totals?.input_tokens || 0} /></Col>
            <Col span={6}><Statistic title="输出 Token" value={usage?.totals?.output_tokens || 0} /></Col>
            <Col span={6}><Statistic title="消耗积分" value={usage?.totals?.points || 0} /></Col>
          </Row>
          <Table size="small" pagination={{ pageSize: 10 }} rowKey="user_id" dataSource={usage?.by_user || []} columns={[
            { title: '用户', dataIndex: 'user_name' }, { title: '任务', dataIndex: 'tasks' },
            { title: '输入 Token', dataIndex: 'input_tokens' }, { title: '输出 Token', dataIndex: 'output_tokens' },
            { title: '总 Token', dataIndex: 'total_tokens' }, { title: '积分', dataIndex: 'points' },
          ]} />
        </Card>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
              保存基础配置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
};

export default SystemConfig;
