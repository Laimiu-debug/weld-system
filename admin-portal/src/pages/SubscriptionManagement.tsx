import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  Tag,
  Row,
  Col,
  message,
  Empty,
  Statistic,
  Typography,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  ExportOutlined,
  EyeOutlined,
  UserOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';
import { downloadCsv } from '@/utils/csv';

const { Search } = Input;
const { Option } = Select;
const { Text } = Typography;

const TIER_LABELS: Record<string, string> = {
  personal_pro: '个人专业版',
  personal_advanced: '个人高级版',
  personal_flagship: '个人旗舰版',
  enterprise: '企业版',
  enterprise_pro: '企业版PRO',
  enterprise_pro_max: '企业版PRO MAX',
};

const TIER_COLORS: Record<string, string> = {
  personal_pro: 'blue',
  personal_advanced: 'green',
  personal_flagship: 'geekblue',
  enterprise: 'orange',
  enterprise_pro: 'magenta',
  enterprise_pro_max: 'red',
};

const SubscriptionManagement: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [subscriptionData, setSubscriptionData] = useState<any[]>([]);
  const [searchText, setSearchText] = useState('');
  const [membershipType, setMembershipType] = useState<string | undefined>();
  const [membershipTier, setMembershipTier] = useState<string | undefined>();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<{ total_paid_users?: number; tier_distribution?: Record<string, number> }>({});

  const fetchSubscriptionData = useCallback(
    async (
      page = currentPage,
      search = searchText,
      type = membershipType,
      tier = membershipTier,
      size = pageSize,
    ) => {
      setLoading(true);
      try {
        const response = await apiService.get('/subscriptions', {
          params: {
            page,
            page_size: size,
            search: search || undefined,
            membership_type: type || undefined,
            membership_tier: tier || undefined,
          },
        });

        if (response && response.items) {
          setSubscriptionData(response.items);
          setTotal(response.total || 0);
          setSummary(response.summary || {});
        } else {
          setSubscriptionData([]);
          setTotal(0);
          setSummary({});
        }
      } catch (error: any) {
        console.error('获取订阅用户数据失败:', error);
        message.error(error?.response?.data?.detail || '获取订阅用户数据失败');
        setSubscriptionData([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    },
    [currentPage, searchText, membershipType, membershipTier, pageSize],
  );

  useEffect(() => {
    void fetchSubscriptionData();
  }, []);

  const handleSearch = () => {
    setCurrentPage(1);
    void fetchSubscriptionData(1, searchText, membershipType, membershipTier, pageSize);
  };

  const handleReset = () => {
    setSearchText('');
    setMembershipType(undefined);
    setMembershipTier(undefined);
    setCurrentPage(1);
    void fetchSubscriptionData(1, '', undefined, undefined, pageSize);
  };

  const handleRefresh = () => {
    void fetchSubscriptionData(currentPage, searchText, membershipType, membershipTier, pageSize);
    message.success('数据已刷新');
  };

  const handleExport = () => {
    downloadCsv(
      `subscriptions-${new Date().toISOString().slice(0, 10)}.csv`,
      ['用户名', '邮箱', '姓名', '会员等级', '订阅状态', '会员类型', '到期时间'],
      subscriptionData.map((item) => [
        item.username,
        item.email,
        item.full_name,
        item.subscription_info?.tier || item.membership_tier,
        item.subscription_info?.status || item.subscription_status,
        item.subscription_info?.type || item.membership_type,
        item.subscription_info?.expires_at || item.expires_at,
      ]),
    );
  };

  const handleTableChange = (pagination: any) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    void fetchSubscriptionData(
      pagination.current,
      searchText,
      membershipType,
      membershipTier,
      pagination.pageSize,
    );
  };

  const getPlanText = (plan: string) => TIER_LABELS[plan] || plan;
  const getPlanColor = (plan: string) => TIER_COLORS[plan] || 'default';

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      expired: 'red',
      cancelled: 'orange',
      pending: 'blue',
      inactive: 'default',
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      active: '正常',
      expired: '已过期',
      cancelled: '已取消',
      pending: '待支付',
      inactive: '未激活',
    };
    return texts[status] || status;
  };

  const columns = [
    {
      title: '用户信息',
      key: 'user_info',
      render: (record: any) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <UserOutlined style={{ marginRight: 4 }} />
            {record.username || 'N/A'}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>{record.email || 'N/A'}</div>
          {record.full_name && (
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>{record.full_name}</div>
          )}
        </div>
      ),
    },
    {
      title: '会员等级',
      key: 'membership_tier',
      render: (record: any) => {
        const tier = record.subscription_info?.tier || record.membership_tier || 'free';
        return <Tag color={getPlanColor(tier)}>{getPlanText(tier)}</Tag>;
      },
    },
    {
      title: '订阅状态',
      key: 'subscription_status',
      render: (record: any) => {
        const status = record.subscription_info?.status || record.subscription_status || 'inactive';
        return <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>;
      },
    },
    {
      title: '会员类型',
      key: 'membership_type',
      render: (record: any) => {
        const type = record.subscription_info?.type || record.membership_type || 'personal';
        return (
          <Tag color={type === 'enterprise' ? 'orange' : 'cyan'}>
            {type === 'personal' ? '个人' : '企业'}
          </Tag>
        );
      },
    },
    {
      title: '到期时间',
      key: 'expires_at',
      render: (record: any) => {
        const expiresAt = record.subscription_info?.expires_at || record.subscription_expires_at;
        if (expiresAt) {
          return <div style={{ fontSize: '12px' }}>{new Date(expiresAt).toLocaleDateString()}</div>;
        }
        return <span style={{ color: '#8c8c8c' }}>未设置</span>;
      },
    },
    {
      title: '配额',
      key: 'quotas',
      render: (record: any) => {
        const quotas = record.quotas || {};
        return (
          <div style={{ fontSize: '12px' }}>
            <div>
              WPS: {quotas.current_wps || quotas.wps_quota_used || 0}/{quotas.wps_limit || 0}
            </div>
            <div>
              PQR: {quotas.current_pqr || quotas.pqr_quota_used || 0}/{quotas.pqr_limit || 0}
            </div>
          </div>
        );
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/users?search=${encodeURIComponent(record.email || record.username || '')}`)}
          >
            用户
          </Button>
          {record.company_id ||
          record.membership_type === 'enterprise' ||
          (record.subscription_info?.type || '').startsWith('enterprise') ||
          String(record.subscription_info?.tier || '').startsWith('enterprise') ? (
            <Button
              type="link"
              size="small"
              onClick={() => {
                if (record.company_id) {
                  navigate(`/enterprises/${record.company_id}`);
                } else {
                  navigate(
                    `/enterprises?search=${encodeURIComponent(record.email || record.company_name || record.username || '')}`,
                  );
                }
              }}
            >
              企业
            </Button>
          ) : null}
        </Space>
      ),
    },
  ];

  const personalCount = Object.entries(summary.tier_distribution || {})
    .filter(([k]) => k.startsWith('personal'))
    .reduce((s, [, n]) => s + n, 0);
  const enterpriseCount = Object.entries(summary.tier_distribution || {})
    .filter(([k]) => k.startsWith('enterprise'))
    .reduce((s, [, n]) => s + n, 0);

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">订阅管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      </div>

      <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
        展示所有非免费付费用户（含个人与企业高等级，含管理员直接授会）
      </Text>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="付费用户" value={summary.total_paid_users ?? total} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="个人付费" value={personalCount} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="企业付费" value={enterpriseCount} valueStyle={{ color: '#fa8c16' }} />
          </Card>
        </Col>
      </Row>

      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索用户名、邮箱、姓名或手机"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              allowClear
              placeholder="会员类型"
              value={membershipType}
              onChange={(v) => setMembershipType(v)}
              style={{ width: '100%' }}
            >
              <Option value="personal">个人</Option>
              <Option value="enterprise">企业</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={5}>
            <Select
              allowClear
              placeholder="会员等级"
              value={membershipTier}
              onChange={(v) => setMembershipTier(v)}
              style={{ width: '100%' }}
            >
              {Object.entries(TIER_LABELS).map(([value, label]) => (
                <Option key={value} value={value}>
                  {label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={3}>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} block>
              搜索
            </Button>
          </Col>
          <Col xs={24} sm={12} md={2}>
            <Button onClick={handleReset} block>
              重置
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        {subscriptionData.length === 0 && !loading ? (
          <Empty description="暂无付费订阅用户" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Table
            columns={columns}
            dataSource={subscriptionData}
            loading={loading}
            scroll={{ x: 1100 }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (t, range) => `第 ${range[0]}-${range[1]} 条，共 ${t} 条付费用户`,
              onChange: (page, size) => handleTableChange({ current: page, pageSize: size }),
            }}
            rowKey="id"
          />
        )}
      </Card>
    </div>
  );
};

export default SubscriptionManagement;
