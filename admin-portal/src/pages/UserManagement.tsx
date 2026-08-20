import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Tag,
  Modal,
  Form,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Alert,
} from 'antd';
import {
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  StopOutlined,
  PlayCircleOutlined,
  ExportOutlined,
  ReloadOutlined,
  EyeOutlined,
  TeamOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import apiService from '@/services/api';
import { User } from '@/types';
import dayjs from 'dayjs';

const { Search } = Input;
const { RangePicker } = DatePicker;
const { Option } = Select;

const UserManagement: React.FC = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<any>({
    page: 1,
    page_size: 20,
  });
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [apiError, setApiError] = useState<string | null>(null);
  const [usersData, setUsersData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 安全的API调用函数
  const safeApiCall = async (apiCall: () => Promise<any>, errorMessage: string) => {
    try {
      const result = await apiCall();
      return result;
    } catch (error: any) {
      console.error(`UserManagement: API call failed: ${errorMessage}`, error);

      // 如果是401错误，不自动清除认证状态
      if (error.response?.status === 401) {
        setApiError('API认证失败，但保持登录状态。请检查后端服务是否正常运行。');
      } else {
        setApiError(`${errorMessage}: ${error.message || '未知错误'}`);
      }
      return null;
    }
  };

  // 加载用户数据
  const loadUsers = async () => {
    setIsLoading(true);
    setApiError(null);

    const result = await safeApiCall(() => apiService.getUsers(filters), '获取用户列表');

    if (result) {
      // API返回的是 {success: true, data: {items: [...], total: 22, ...}}
      // 需要设置 data 字段到 usersData
      setUsersData(result.data || result);
    }

    setIsLoading(false);
  };

  // 组件挂载时加载数据
  React.useEffect(() => {
    loadUsers();
  }, [filters]);

  const handleSearch = (value: string) => {
    setFilters((prev: any) => ({ ...prev, search: value, page: 1 }));
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev: any) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates) {
      setFilters((prev: any) => ({
        ...prev,
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
        page: 1,
      }));
    } else {
      setFilters((prev: any) => {
        const { start_date, end_date, ...rest } = prev;
        return rest;
      });
    }
  };

  const handleTableChange = (pagination: any) => {
    setFilters((prev: any) => ({
      ...prev,
      page: pagination.current,
      page_size: pagination.pageSize,
    }));
  };

  const handleEditUser = (user: User) => {
    setCurrentUser(user);
    form.setFieldsValue({
      membership_tier: user.membership_tier,
      expires_at: user.subscription_expires_at ? dayjs(user.subscription_expires_at) : null,
      quotas: user.quotas,
    });
    setModalVisible(true);
  };

  const handleAdjustMembership = async (values: any) => {
    if (!currentUser) return;

    // 不传递quotas，让后端根据会员等级自动设置配额
    const result = await safeApiCall(
      () => apiService.adjustUserMembership(currentUser.id, {
        membership_tier: values.membership_tier,
        expires_at: values.expires_at?.format('YYYY-MM-DD'),
        reason: values.reason,
      }),
      '调整用户会员等级'
    );

    if (result) {
      message.success('会员等级调整成功，配额已自动更新');
      setModalVisible(false);
      loadUsers(); // 重新加载数据
    }
  };

  const handleToggleUserStatus = async (userId: string, isActive: boolean) => {
    const result = await safeApiCall(
      () => apiService.toggleUserStatus(userId, isActive),
      `${isActive ? '启用' : '禁用'}用户`
    );

    if (result) {
      message.success(`用户已${isActive ? '启用' : '禁用'}`);
      loadUsers(); // 重新加载数据
    }
  };

  const handleDeleteUser = async (userId: string) => {
    const result = await safeApiCall(
      () => apiService.deleteUser(userId),
      '删除用户'
    );

    if (result) {
      message.success('用户删除成功');
      setSelectedRowKeys([]);
      loadUsers(); // 重新加载数据
    }
  };

  const handleVerifyEmail = async (userId: string, userEmail: string) => {
    const result = await safeApiCall(
      () => apiService.verifyUserEmail(userId),
      '验证用户邮箱'
    );

    if (result) {
      message.success(`用户 ${userEmail} 的邮箱已验证`);
      loadUsers(); // 重新加载数据
    }
  };

  const handleViewUserDetail = (userId: string) => {
    navigate(`/users/${userId}`);
  };

  const getMembershipColor = (tier: string) => {
    const colors: Record<string, string> = {
      personal_free: 'default',
      personal_pro: 'blue',
      personal_advanced: 'green',
      personal_flagship: 'geekblue',
      enterprise: 'orange',
      enterprise_pro: 'magenta',
      enterprise_pro_max: 'red',
    };
    return colors[tier] || 'default';
  };

  const getMembershipText = (tier: string) => {
    const texts: Record<string, string> = {
      personal_free: '个人免费版',
      personal_pro: '个人专业版',
      personal_advanced: '个人高级版',
      personal_flagship: '个人旗舰版',
      enterprise: '企业版',
      enterprise_pro: '企业版PRO',
      enterprise_pro_max: '企业版PRO MAX',
    };
    return texts[tier] || tier;
  };

  const columns: ColumnsType<User> = [
    {
      title: '用户信息',
      key: 'user_info',
      width: 200,
      ellipsis: true,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.full_name || record.username}</div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            {record.phone || record.email}
          </div>
        </div>
      ),
    },
    {
      title: '会员等级',
      dataIndex: 'membership_tier',
      key: 'membership_tier',
      width: 150,
      render: (tier: string, record: User) => (
        <Space direction="vertical" size={0}>
          <Tag color={getMembershipColor(tier)}>
            {getMembershipText(tier)}
          </Tag>
          {record.is_inherited_from_company && (
            <Tooltip title={`继承自企业「${record.company_name}」`}>
              <Tag icon={<TeamOutlined />} color="blue" style={{ fontSize: '11px' }}>
                企业继承
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
      filters: [
        { text: '个人免费版', value: 'personal_free' },
        { text: '个人专业版', value: 'personal_pro' },
        { text: '个人高级版', value: 'personal_advanced' },
        { text: '个人旗舰版', value: 'personal_flagship' },
        { text: '企业版', value: 'enterprise' },
        { text: '企业版PRO', value: 'enterprise_pro' },
        { text: '企业版PRO MAX', value: 'enterprise_pro_max' },
      ],
      onFilter: (value, record) => record.membership_tier === value,
    },
    {
      title: '状态',
      key: 'status',
      width: 110,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Tag color={record.is_active ? 'green' : 'red'}>
            {record.is_active ? '正常' : '已禁用'}
          </Tag>
          <Tag color={record.is_verified ? 'blue' : 'orange'}>
            {record.is_verified ? '已验证' : '未验证'}
          </Tag>
        </Space>
      ),
      filters: [
        { text: '正常', value: 'active' },
        { text: '已禁用', value: 'inactive' },
        { text: '已验证', value: 'verified' },
        { text: '未验证', value: 'unverified' },
      ],
      onFilter: (value, record) => {
        if (value === 'active') return record.is_active;
        if (value === 'inactive') return !record.is_active;
        if (value === 'verified') return Boolean(record.is_verified);
        if (value === 'unverified') return !record.is_verified;
        return true;
      },
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
      sorter: true,
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      width: 160,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '从未登录',
    },
    {
      title: '配额使用',
      key: 'quotas',
      width: 150,
      render: (_, record) => (
        <div style={{ fontSize: '12px', lineHeight: 1.5, whiteSpace: 'nowrap' }}>
          <div>WPS: {record.quotas?.current_wps || 0}/{record.quotas?.wps_limit || 0}</div>
          <div>PQR: {record.quotas?.current_pqr || 0}/{record.quotas?.pqr_limit || 0}</div>
          <div>pPQR: {record.quotas?.current_ppqr || 0}/{record.quotas?.ppqr_limit || 0}</div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewUserDetail(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑用户">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          {!record.is_verified && (
            <Tooltip title="验证邮箱">
              <Popconfirm
                title="确定要验证该用户的邮箱吗？"
                description="验证后用户将可以正常登录系统"
                onConfirm={() => handleVerifyEmail(record.id, record.email)}
              >
                <Button
                  type="link"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  style={{ color: '#52c41a' }}
                />
              </Popconfirm>
            </Tooltip>
          )}
          <Tooltip title={record.is_active ? '禁用用户' : '启用用户'}>
            <Popconfirm
              title={`确定要${record.is_active ? '禁用' : '启用'}该用户吗？`}
              onConfirm={() => handleToggleUserStatus(record.id, !record.is_active)}
            >
              <Button
                type="link"
                size="small"
                icon={record.is_active ? <StopOutlined /> : <PlayCircleOutlined />}
                danger={record.is_active}
              />
            </Popconfirm>
          </Tooltip>
          <Tooltip title="删除用户">
            <Popconfirm
              title="确定要删除该用户吗？此操作不可恢复！"
              onConfirm={() => handleDeleteUser(record.id)}
            >
              <Button
                type="link"
                size="small"
                icon={<DeleteOutlined />}
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">用户管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadUsers}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />}>
            导出
          </Button>
          <Button onClick={() => window.location.href = '/auth-test'}>
            认证测试
          </Button>
        </Space>
      </div>

      {apiError && (
        <Alert
          message="API调用错误"
          description={apiError}
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
          onClose={() => setApiError(null)}
        />
      )}

      {/* 筛选区域 */}
      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={8} lg={6}>
            <Search
              placeholder="搜索用户名或邮箱"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={12} md={6} lg={4}>
            <Select
              placeholder="会员等级"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('membership_tier', value)}
            >
              <Option value="personal_free">个人免费版</Option>
              <Option value="personal_pro">个人专业版</Option>
              <Option value="personal_advanced">个人高级版</Option>
              <Option value="personal_flagship">个人旗舰版</Option>
              <Option value="enterprise">企业版</Option>
              <Option value="enterprise_pro">企业版PRO</Option>
              <Option value="enterprise_pro_max">企业版PRO MAX</Option>
            </Select>
          </Col>
          <Col xs={12} sm={12} md={6} lg={3}>
            <Select
              placeholder="用户状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('is_active', value)}
            >
              <Option value={true}>正常</Option>
              <Option value={false}>已禁用</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8} lg={7}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={handleDateRangeChange}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
          <Col xs={24} sm={12} md={4} lg={4}>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={loadUsers}
              block
            >
              搜索
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 用户表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={usersData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            current: filters.page,
            pageSize: filters.page_size,
            total: usersData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as string[]),
          }}
          onChange={handleTableChange}
        />
      </Card>

      {/* 会员调整弹窗 */}
      <Modal
        title="调整用户会员等级"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAdjustMembership}
        >
          <Form.Item
            name="membership_tier"
            label="会员等级"
            rules={[{ required: true, message: '请选择会员等级' }]}
          >
            <Select placeholder="选择会员等级">
              <Option value="personal_free">个人免费版</Option>
              <Option value="personal_pro">个人专业版</Option>
              <Option value="personal_advanced">个人高级版</Option>
              <Option value="personal_flagship">个人旗舰版</Option>
              <Option value="enterprise">企业版</Option>
              <Option value="enterprise_pro">企业版PRO</Option>
              <Option value="enterprise_pro_max">企业版PRO MAX</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="expires_at"
            label="订阅到期时间"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Alert
            message="配额自动设置"
            description="系统将根据选择的会员等级自动设置相应的配额限制（WPS、PQR、pPQR等），无需手动配置。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            name="reason"
            label="调整原因"
            rules={[{ required: true, message: '请输入调整原因' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入调整原因" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
              >
                确认调整
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;
