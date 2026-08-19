import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  message,
  Spin,
  Alert,
  Modal,
  Form,
  Input,
  DatePicker,
  Row,
  Col,
  Statistic,
  Popconfirm,
  Select,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  StopOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  SaveOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';
import dayjs from 'dayjs';

const { TextArea } = Input;

interface UserDetailData {
  id: string;
  email: string;
  username: string;
  full_name: string;
  membership_tier: string;
  membership_type: string;
  is_active: boolean;
  is_admin: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string;
  phone: string;
  company: string;
  company_name?: string;
  is_inherited_from_company?: boolean;
  subscription_expires_at: string;
  quotas: {
    wps_limit: number;
    pqr_limit: number;
    ppqr_limit: number;
    current_wps: number;
    current_pqr: number;
    current_ppqr: number;
    storage_used: number;
  };
  auto_renewal: boolean;
  subscription_status: string;
  last_login_ip: string;
}

const UserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [statusModalVisible, setStatusModalVisible] = useState(false);
  const [statusAction, setStatusAction] = useState<'enable' | 'disable'>('enable');
  const [form] = Form.useForm();
  const [statusForm] = Form.useForm();

  useEffect(() => {
    if (userId) {
      loadUserDetail();
    }
  }, [userId]);

  const loadUserDetail = async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      // API拦截器会自动提取data字段，所以这里直接接收用户数据对象
      const userData = await apiService.getUserDetail(userId);
      setUser(userData as unknown as UserDetailData);
    } catch (error: any) {
      console.error('获取用户详情失败:', error);
      setError(error.message || '获取用户详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = () => {
    if (!user) return;

    form.setFieldsValue({
      membership_tier: user.membership_tier,
      subscription_expires_at: user.subscription_expires_at ? dayjs(user.subscription_expires_at) : null,
      email: user.email,
      phone: user.phone,
      company: user.company,
      full_name: user.full_name,
    });
    setEditModalVisible(true);
  };

  const handleSaveUser = async (values: any) => {
    if (!user) return;

    try {
      // 分两步更新：先更新基本信息，再更新会员等级
      // 1. 更新基本信息（email, phone, company, full_name）
      if (values.email !== user.email || values.phone !== user.phone ||
          values.company !== user.company || values.full_name !== user.full_name) {
        await apiService.post(`/users/${user.id}/update-profile`, {
          email: values.email,
          phone: values.phone,
          company: values.company,
          full_name: values.full_name,
        });
      }

      // 2. 更新会员等级和订阅信息
      if (values.membership_tier !== user.membership_tier ||
          values.subscription_expires_at?.format('YYYY-MM-DD') !== user.subscription_expires_at) {
        await apiService.adjustUserMembership(user.id, {
          membership_tier: values.membership_tier,
          expires_at: values.subscription_expires_at?.format('YYYY-MM-DD'),
          reason: `管理员手动编辑用户信息`,
        });
      }

      // 请求成功
      message.success('用户信息更新成功');
      setEditModalVisible(false);
      loadUserDetail(); // 重新加载数据
    } catch (error: any) {
      console.error('更新用户信息失败:', error);
      message.error(error.message || '更新用户信息失败');
    }
  };

  const handleToggleUserStatus = (action: 'enable' | 'disable') => {
    setStatusAction(action);
    setStatusModalVisible(true);
  };

  const handleConfirmStatusChange = async (values: any) => {
    if (!user) return;

    try {
      // API拦截器会自动提取data字段，所以这里直接接收data对象
      await apiService.toggleUserStatus(
        user.id,
        statusAction === 'enable',
        values.reason
      );

      // 请求成功
      message.success(`用户已${statusAction === 'enable' ? '启用' : '禁用'}`);
      setStatusModalVisible(false);
      statusForm.resetFields();
      loadUserDetail(); // 重新加载数据
    } catch (error: any) {
      console.error(`${statusAction === 'enable' ? '启用' : '禁用'}用户失败:`, error);
      message.error(error.message || `${statusAction === 'enable' ? '启用' : '禁用'}用户失败`);
    }
  };

  const handleDeleteUser = async () => {
    if (!user) return;

    try {
      // API拦截器会自动提取data字段，所以这里直接接收data对象
      await apiService.deleteUser(user.id);

      // 请求成功
      message.success('用户删除成功');
      navigate('/users'); // 返回用户列表
    } catch (error: any) {
      console.error('删除用户失败:', error);
      message.error(error.message || '删除用户失败');
    }
  };

  const getMembershipColor = (tier: string) => {
    const colors: Record<string, string> = {
      free: 'default',
      personal_pro: 'blue',
      personal_advanced: 'green',
      personal_flagship: 'purple',
      enterprise: 'gold',
    };
    return colors[tier] || 'default';
  };

  const getMembershipText = (tier: string) => {
    const texts: Record<string, string> = {
      free: '免费版',
      personal_pro: '个人专业版',
      personal_advanced: '个人高级版',
      personal_flagship: '个人旗舰版',
      enterprise: '企业版',
    };
    return texts[tier] || tier;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载用户详情中...</div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div>
        <div className="admin-header">
          <h1 className="page-title">用户详情</h1>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/users')}>
            返回用户列表
          </Button>
        </div>
        <Alert
          message="加载失败"
          description={error || '用户不存在'}
          type="error"
          showIcon
        />
      </div>
    );
  }

  // TypeScript 类型守卫：确保 user 不为 null
  if (!user) return null;

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">用户详情</h1>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/users')}>
            返回用户列表
          </Button>
          <Button icon={<EditOutlined />} onClick={handleEditUser}>
            编辑用户
          </Button>
          {user.is_active ? (
            <Button
              icon={<StopOutlined />}
              danger
              onClick={() => handleToggleUserStatus('disable')}
            >
              禁用用户
            </Button>
          ) : (
            <Button
              icon={<PlayCircleOutlined />}
              type="primary"
              onClick={() => handleToggleUserStatus('enable')}
            >
              启用用户
            </Button>
          )}
          <Popconfirm
            title="确定要删除该用户吗？"
            description="此操作不可恢复，请谨慎操作！"
            onConfirm={handleDeleteUser}
            okText="确定删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button icon={<DeleteOutlined />} danger>
              删除用户
            </Button>
          </Popconfirm>
        </Space>
      </div>

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="用户ID">{user.id}</Descriptions.Item>
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
          <Descriptions.Item label="真实姓名">{user.full_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="手机号码">{user.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="公司">{user.company || '-'}</Descriptions.Item>
          <Descriptions.Item label="账户状态">
            <Tag color={user.is_active ? 'green' : 'red'}>
              {user.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="邮箱验证">
            <Tag color={user.is_verified ? 'green' : 'orange'}>
              {user.is_verified ? '已验证' : '未验证'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="管理员权限">
            <Tag color={user.is_admin ? 'red' : 'default'}>
              {user.is_admin ? '管理员' : '普通用户'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="最后登录IP">{user.last_login_ip || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 会员信息 */}
      <Card title="会员信息" style={{ marginBottom: 16 }}>
        {user.is_inherited_from_company && (
          <Alert
            message={
              <span>
                <TeamOutlined style={{ marginRight: 8 }} />
                该用户通过企业继承会员权限
              </span>
            }
            description={`该用户已加入企业「${user.company_name}」，自动继承企业会员等级和配额。`}
            type="info"
            showIcon={false}
            style={{ marginBottom: 16 }}
          />
        )}

        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="会员等级"
              value={getMembershipText(user.membership_tier)}
              valueStyle={{ color: getMembershipColor(user.membership_tier) === 'default' ? '#8c8c8c' : undefined }}
              prefix={
                <Tag color={getMembershipColor(user.membership_tier)}>
                  {getMembershipText(user.membership_tier)}
                </Tag>
              }
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="订阅状态"
              value={user.subscription_status || 'inactive'}
              valueStyle={{ color: user.subscription_status === 'active' ? '#3f8600' : '#8c8c8c' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="到期时间"
              value={user.subscription_expires_at ? dayjs(user.subscription_expires_at).format('YYYY-MM-DD') : '永久'}
            />
          </Col>
        </Row>

        <div style={{ margin: '24px 0', borderTop: '1px solid #f0f0f0' }} />

        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="WPS 使用情况"
              value={`${user.quotas.current_wps}/${user.quotas.wps_limit}`}
              suffix={`份 (${Math.round((user.quotas.current_wps / user.quotas.wps_limit) * 100)}%)`}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="PQR 使用情况"
              value={`${user.quotas.current_pqr}/${user.quotas.pqr_limit}`}
              suffix={`份 (${Math.round((user.quotas.current_pqr / user.quotas.pqr_limit) * 100)}%)`}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="pPQR 使用情况"
              value={`${user.quotas.current_ppqr}/${user.quotas.ppqr_limit}`}
              suffix={`份 (${user.quotas.ppqr_limit > 0 ? Math.round((user.quotas.current_ppqr / user.quotas.ppqr_limit) * 100) : 0}%)`}
            />
          </Col>
        </Row>
      </Card>

      {/* 时间信息 */}
      <Card title="时间信息">
        <Descriptions column={1} bordered>
          <Descriptions.Item label="注册时间">
            {dayjs(user.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="最后更新">
            {dayjs(user.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="最后登录">
            {user.last_login_at ? dayjs(user.last_login_at).format('YYYY-MM-DD HH:mm:ss') : '从未登录'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 编辑用户弹窗 */}
      <Modal
        title="编辑用户信息"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
        >
          <Form.Item
            name="membership_tier"
            label="会员等级"
            rules={[{ required: true, message: '请选择会员等级' }]}
          >
            <Select placeholder="选择会员等级">
              <Select.Option value="free">免费版</Select.Option>
              <Select.Option value="personal_pro">个人专业版</Select.Option>
              <Select.Option value="personal_advanced">个人高级版</Select.Option>
              <Select.Option value="personal_flagship">个人旗舰版</Select.Option>
              <Select.Option value="enterprise">企业版</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="subscription_expires_at"
            label="订阅到期时间"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱地址"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="真实姓名"
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="phone"
            label="手机号码"
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="company"
            label="公司"
          >
            <Input />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                保存更改
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 状态变更弹窗 */}
      <Modal
        title={`${statusAction === 'enable' ? '启用' : '禁用'}用户`}
        open={statusModalVisible}
        onCancel={() => setStatusModalVisible(false)}
        footer={null}
      >
        <Form
          form={statusForm}
          layout="vertical"
          onFinish={handleConfirmStatusChange}
        >
          <Form.Item
            name="reason"
            label={`${statusAction === 'enable' ? '启用' : '禁用'}原因`}
            rules={[{ required: true, message: `请输入${statusAction === 'enable' ? '启用' : '禁用'}原因` }]}
          >
            <TextArea rows={3} placeholder={`请输入${statusAction === 'enable' ? '启用' : '禁用'}原因`} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                danger={statusAction === 'disable'}
              >
                确认{statusAction === 'enable' ? '启用' : '禁用'}
              </Button>
              <Button onClick={() => setStatusModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserDetail;
