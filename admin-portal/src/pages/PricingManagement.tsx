import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  InputNumber,
  message,
  Row,
  Col,
  Statistic,
  Switch,
  Tooltip,
  Alert,
  Typography,
  Radio,
} from 'antd';
import {
  EditOutlined,
  ReloadOutlined,
  DollarOutlined,
  PercentageOutlined,
  TagsOutlined,
  SaveOutlined,
  CloseOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import apiService from '../services/api';

const { TextArea } = Input;

interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  monthly_price: number;
  quarterly_price: number;
  yearly_price: number;
  currency: string;
  max_wps_files: number;
  max_pqr_files: number;
  max_ppqr_files: number;
  max_materials: number;
  max_welders: number;
  max_equipment: number;
  max_factories: number;
  max_employees: number;
  features: string | string[]; // 可以是字符串或数组
  sort_order: number;
  is_recommended: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

const PricingManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [discountModalVisible, setDiscountModalVisible] = useState(false);
  const [currentPlan, setCurrentPlan] = useState<SubscriptionPlan | null>(null);
  const [form] = Form.useForm();
  const [discountForm] = Form.useForm();

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      setLoading(true);
      // 拦截器已解包 {success,data}，此处应直接拿到数组
      const response = await apiService.getSubscriptionPlans();
      const list = Array.isArray(response)
        ? response
        : Array.isArray((response as any)?.data)
          ? (response as any).data
          : [];

      if (list.length === 0) {
        message.warning('暂无订阅计划数据，请确认后端已初始化套餐');
      }
      setPlans(list);
    } catch (error: any) {
      console.error('加载订阅计划失败:', error);
      message.error('加载订阅计划失败: ' + (error.message || '未知错误'));
      setPlans([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (plan: SubscriptionPlan) => {
    setCurrentPlan(plan);

    // 处理 features：可能是字符串或数组
    let featuresArray: string[] = [];
    if (plan.features) {
      if (typeof plan.features === 'string') {
        featuresArray = plan.features.split(',').map(f => f.trim()).filter(f => f);
      } else if (Array.isArray(plan.features)) {
        featuresArray = plan.features;
      }
    }

    form.setFieldsValue({
      ...plan,
      features: featuresArray,
    });
    setEditModalVisible(true);
  };

  const handleSetDiscount = (plan: SubscriptionPlan) => {
    setCurrentPlan(plan);
    discountForm.setFieldsValue({
      adjust_mode: 'percent',
      monthly_discount_percent: 0,
      quarterly_discount_percent: 0,
      yearly_discount_percent: 0,
      monthly_discount_amount: 0,
      quarterly_discount_amount: 0,
      yearly_discount_amount: 0,
    });
    setDiscountModalVisible(true);
  };

  const handleSaveEdit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      let features: string[] = [];
      if (Array.isArray(values.features)) {
        features = values.features.map((f: string) => String(f).trim()).filter(Boolean);
      } else if (typeof values.features === 'string') {
        features = values.features.split(',').map((f: string) => f.trim()).filter(Boolean);
      }

      const updateData = {
        ...values,
        features,
      };

      await apiService.updateSubscriptionPlan(String(currentPlan?.id), updateData);
      message.success('订阅计划更新成功');
      setEditModalVisible(false);
      loadPlans();
    } catch (error: any) {
      console.error('更新订阅计划失败:', error);
      const detail = error?.response?.data?.detail;
      message.error(
        detail === '需要超级管理员权限'
          ? '需要超级管理员权限才能修改套餐'
          : `更新失败: ${detail || error.message || '未知错误'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDiscount = async () => {
    try {
      const values = await discountForm.validateFields();
      setLoading(true);

      if (!currentPlan) return;

      const mode = values.adjust_mode || 'percent';
      const newPrices: Record<string, number> = {
        monthly_price: currentPlan.monthly_price,
        quarterly_price: currentPlan.quarterly_price,
        yearly_price: currentPlan.yearly_price,
      };

      if (mode === 'percent') {
        if (values.monthly_discount_percent) {
          newPrices.monthly_price =
            currentPlan.monthly_price * (1 + values.monthly_discount_percent / 100);
        }
        if (values.quarterly_discount_percent) {
          newPrices.quarterly_price =
            currentPlan.quarterly_price * (1 + values.quarterly_discount_percent / 100);
        }
        if (values.yearly_discount_percent) {
          newPrices.yearly_price =
            currentPlan.yearly_price * (1 + values.yearly_discount_percent / 100);
        }
      } else {
        if (values.monthly_discount_amount) {
          newPrices.monthly_price = Math.max(
            0,
            currentPlan.monthly_price + values.monthly_discount_amount
          );
        }
        if (values.quarterly_discount_amount) {
          newPrices.quarterly_price = Math.max(
            0,
            currentPlan.quarterly_price + values.quarterly_discount_amount
          );
        }
        if (values.yearly_discount_amount) {
          newPrices.yearly_price = Math.max(
            0,
            currentPlan.yearly_price + values.yearly_discount_amount
          );
        }
      }

      Object.keys(newPrices).forEach((key) => {
        newPrices[key] = Math.round(newPrices[key] * 100) / 100;
      });

      await apiService.updateSubscriptionPlan(String(currentPlan.id), newPrices);
      message.success('价格调整成功');
      setDiscountModalVisible(false);
      loadPlans();
    } catch (error: any) {
      console.error('设置折扣失败:', error);
      const detail = error?.response?.data?.detail;
      message.error(
        detail === '需要超级管理员权限'
          ? '需要超级管理员权限才能调价'
          : `设置折扣失败: ${detail || error.message || '未知错误'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const getPlanTypeTag = (planId: string) => {
    if (planId.includes('free')) return <Tag color="default">免费版</Tag>;
    if (planId.includes('personal')) return <Tag color="blue">个人版</Tag>;
    if (planId.includes('enterprise')) return <Tag color="geekblue">企业版</Tag>;
    return <Tag>{planId}</Tag>;
  };

  const columns = [
    {
      title: '计划名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: SubscriptionPlan) => (
        <Space direction="vertical" size={0}>
          <Space>
            <strong>{text}</strong>
            {record.is_recommended && <Tag color="gold">推荐</Tag>}
            {!record.is_active && <Tag color="red">已停用</Tag>}
          </Space>
          {getPlanTypeTag(record.id)}
        </Space>
      ),
    },
    {
      title: '月付价格',
      dataIndex: 'monthly_price',
      key: 'monthly_price',
      width: 120,
      render: (price: number) => (
        <span style={{ color: '#1F5EFF', fontWeight: 500 }}>
          ¥{price.toFixed(2)}
        </span>
      ),
    },
    {
      title: '季付价格',
      dataIndex: 'quarterly_price',
      key: 'quarterly_price',
      width: 120,
      render: (price: number, record: SubscriptionPlan) => {
        const discount = record.monthly_price > 0 
          ? ((1 - price / (record.monthly_price * 3)) * 100).toFixed(0)
          : 0;
        return (
          <Space direction="vertical" size={0}>
            <span style={{ color: '#52c41a', fontWeight: 500 }}>¥{price.toFixed(2)}</span>
            {Number(discount) > 0 && <Tag color="green">{discount}折</Tag>}
          </Space>
        );
      },
    },
    {
      title: '年付价格',
      dataIndex: 'yearly_price',
      key: 'yearly_price',
      width: 120,
      render: (price: number, record: SubscriptionPlan) => {
        const discount = record.monthly_price > 0
          ? ((1 - price / (record.monthly_price * 12)) * 100).toFixed(0)
          : 0;
        return (
          <Space direction="vertical" size={0}>
            <span style={{ color: '#f5222d', fontWeight: 500 }}>¥{price.toFixed(2)}</span>
            {Number(discount) > 0 && <Tag color="red">{discount}折</Tag>}
          </Space>
        );
      },
    },
    {
      title: '配额限制',
      key: 'quotas',
      width: 200,
      render: (_: any, record: SubscriptionPlan) => (
        <div style={{ fontSize: '12px' }}>
          <div>WPS: {record.max_wps_files}</div>
          <div>PQR: {record.max_pqr_files}</div>
          <div>pPQR: {record.max_ppqr_files}</div>
          <div>材料: {record.max_materials}</div>
          <div>焊工: {record.max_welders}</div>
          <div>设备: {record.max_equipment}</div>
          {record.max_factories > 0 && <div>工厂: {record.max_factories}</div>}
          {record.max_employees > 0 && <div>员工: {record.max_employees}</div>}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: SubscriptionPlan) => (
        <Space size="small">
          <Tooltip title="编辑计划">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            >
              编辑
            </Button>
          </Tooltip>
          <Tooltip title="设置折扣/降价">
            <Button
              type="link"
              size="small"
              icon={<PercentageOutlined />}
              onClick={() => handleSetDiscount(record)}
              style={{ color: '#f5222d' }}
            >
              调价
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">
          <TagsOutlined /> 订阅计划与价格管理
        </h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadPlans} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <Alert
        message="价格管理说明"
        description="可编辑套餐价格与配额。调价支持百分比或固定金额（二选一），正数涨价、负数降价。修改需超级管理员账号。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card>
        <Table
          columns={columns}
          dataSource={plans}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 编辑计划模态框 */}
      <Modal
        title={`编辑订阅计划: ${currentPlan?.name}`}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={handleSaveEdit}
        width={800}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="计划名称" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="description" label="计划描述">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Typography.Title level={5} style={{ marginTop: 24, marginBottom: 16 }}>价格设置</Typography.Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="monthly_price" label="月付价格 (¥)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} precision={2} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="quarterly_price" label="季付价格 (¥)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} precision={2} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="yearly_price" label="年付价格 (¥)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} precision={2} />
              </Form.Item>
            </Col>
          </Row>

          <Typography.Title level={5} style={{ marginTop: 24, marginBottom: 16 }}>配额设置</Typography.Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_wps_files" label="WPS文件数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_pqr_files" label="PQR文件数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_ppqr_files" label="pPQR文件数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_materials" label="材料数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_welders" label="焊工数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_equipment" label="设备数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_factories" label="工厂数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_employees" label="员工数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sort_order" label="排序">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="is_recommended" label="推荐计划" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_active" label="启用状态" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 设置折扣/降价模态框 */}
      <Modal
        title={
          <Space>
            <PercentageOutlined style={{ color: '#f5222d' }} />
            <span>设置折扣/降价: {currentPlan?.name}</span>
          </Space>
        }
        open={discountModalVisible}
        onCancel={() => setDiscountModalVisible(false)}
        width={700}
        footer={[
          <Button key="cancel" onClick={() => setDiscountModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSaveDiscount}
            loading={loading}
          >
            应用调价
          </Button>,
        ]}
      >
        <Alert
          message="调价说明"
          description="请选择一种调价方式：百分比或固定金额。正数涨价，负数降价。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {currentPlan && (
          <Card size="small" style={{ marginBottom: 16, background: '#f5f5f5' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="当前月付价格"
                  value={currentPlan.monthly_price}
                  prefix="¥"
                  precision={2}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="当前季付价格"
                  value={currentPlan.quarterly_price}
                  prefix="¥"
                  precision={2}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="当前年付价格"
                  value={currentPlan.yearly_price}
                  prefix="¥"
                  precision={2}
                />
              </Col>
            </Row>
          </Card>
        )}

        <Form form={discountForm} layout="vertical">
          <Form.Item name="adjust_mode" label="调价方式" initialValue="percent">
            <Radio.Group>
              <Radio.Button value="percent">按百分比</Radio.Button>
              <Radio.Button value="amount">按固定金额</Radio.Button>
            </Radio.Group>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.adjust_mode !== cur.adjust_mode}>
            {({ getFieldValue }) =>
              getFieldValue('adjust_mode') === 'amount' ? (
                <>
                  <Typography.Title level={5} style={{ marginBottom: 16 }}>
                    按固定金额调整
                  </Typography.Title>
                  <Alert
                    message="例如：100 涨价 100 元，-100 降价 100 元"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item name="monthly_discount_amount" label="月付调整 (¥)">
                        <InputNumber style={{ width: '100%' }} precision={2} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="quarterly_discount_amount" label="季付调整 (¥)">
                        <InputNumber style={{ width: '100%' }} precision={2} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="yearly_discount_amount" label="年付调整 (¥)">
                        <InputNumber style={{ width: '100%' }} precision={2} />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              ) : (
                <>
                  <Typography.Title level={5} style={{ marginBottom: 16 }}>
                    按百分比调整
                  </Typography.Title>
                  <Alert
                    message="例如：10 涨价 10%，-10 降价 10%"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item name="monthly_discount_percent" label="月付调整 (%)">
                        <InputNumber min={-100} max={1000} style={{ width: '100%' }} precision={1} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="quarterly_discount_percent" label="季付调整 (%)">
                        <InputNumber min={-100} max={1000} style={{ width: '100%' }} precision={1} />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="yearly_discount_percent" label="年付调整 (%)">
                        <InputNumber min={-100} max={1000} style={{ width: '100%' }} precision={1} />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              )
            }
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PricingManagement;

