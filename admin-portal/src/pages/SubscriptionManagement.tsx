import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Input, Select, Tag, Badge, Row, Col, message, Empty } from 'antd';
import { SearchOutlined, ReloadOutlined, ExportOutlined, EyeOutlined, CreditCardOutlined, UserOutlined } from '@ant-design/icons';
import apiService from '@/services/api';

const { Search } = Input;
const { Option } = Select;

const SubscriptionManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [subscriptionData, setSubscriptionData] = useState<any[]>([]);
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  // 获取订阅用户数据
  const fetchSubscriptionData = async (page = currentPage, search = searchText) => {
    setLoading(true);
    try {
      const response = await apiService.get('/subscriptions', {
        params: {
          page,
          page_size: pageSize,
          search: search || undefined
        }
      });

      if (response && response.items) {
        setSubscriptionData(response.items);
        setTotal(response.total || 0);
      } else {
        setSubscriptionData([]);
        setTotal(0);
      }
    } catch (error: any) {
      console.error('获取订阅用户数据失败:', error);
      message.error('获取订阅用户数据失败');
      setSubscriptionData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    setCurrentPage(1);
    fetchSubscriptionData(1, searchText);
  };

  // 重置搜索
  const handleReset = () => {
    setSearchText('');
    setCurrentPage(1);
    fetchSubscriptionData(1, '');
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchSubscriptionData(currentPage, searchText);
    message.success('数据已刷新');
  };

  // 分页处理
  const handleTableChange = (pagination: any) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    fetchSubscriptionData(pagination.current, searchText);
  };

  const getPlanColor = (plan: string) => {
    const colors: Record<string, string> = {
      personal_pro: 'blue',
      personal_advanced: 'green',
      personal_flagship: 'purple',
      enterprise: 'gold',
    };
    return colors[plan] || 'default';
  };

  const getPlanText = (plan: string) => {
    const texts: Record<string, string> = {
      personal_pro: '个人专业版',
      personal_advanced: '个人高级版',
      personal_flagship: '个人旗舰版',
      enterprise: '企业版',
    };
    return texts[plan] || plan;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      expired: 'red',
      cancelled: 'orange',
      pending: 'blue',
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      active: '正常',
      expired: '已过期',
      cancelled: '已取消',
      pending: '待支付',
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
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            {record.email || 'N/A'}
          </div>
          {record.full_name && (
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.full_name}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '会员等级',
      key: 'membership_tier',
      render: (record: any) => {
        const tier = record.subscription_info?.tier || record.membership_tier || 'free';
        return (
          <Tag color={getPlanColor(tier)}>
            {getPlanText(tier)}
          </Tag>
        );
      },
    },
    {
      title: '订阅状态',
      key: 'subscription_status',
      render: (record: any) => {
        const status = record.subscription_info?.status || record.subscription_status || 'inactive';
        return (
          <Tag color={getStatusColor(status)}>
            {getStatusText(status)}
          </Tag>
        );
      },
    },
    {
      title: '会员类型',
      key: 'membership_type',
      render: (record: any) => {
        const type = record.subscription_info?.type || record.membership_type || 'personal';
        return (
          <Tag color="cyan">
            {type === 'personal' ? '个人版' : '企业版'}
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
          const date = new Date(expiresAt);
          return (
            <div style={{ fontSize: '12px' }}>
              {date.toLocaleDateString()}
            </div>
          );
        }
        return <span style={{ color: '#8c8c8c' }}>未设置</span>;
      },
    },
    {
      title: '自动续费',
      key: 'auto_renewal',
      render: (record: any) => {
        const autoRenew = record.subscription_info?.auto_renewal || record.auto_renewal || false;
        return (
          <Tag color={autoRenew ? 'green' : 'red'}>
            {autoRenew ? '已开启' : '已关闭'}
          </Tag>
        );
      },
    },
    {
      title: '配额使用情况',
      key: 'quotas',
      render: (record: any) => {
        const quotas = record.quotas || {};
        return (
          <div style={{ fontSize: '12px' }}>
            <div>WPS: {quotas.current_wps || 0}/{quotas.wps_limit || 0}</div>
            <div>PQR: {quotas.current_pqr || 0}/{quotas.pqr_limit || 0}</div>
          </div>
        );
      },
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: any) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />}>
            查看详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">订阅管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />} onClick={() => message.info('导出功能开发中')}>
            导出
          </Button>
        </Space>
      </div>

      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索用户名、邮箱或姓名"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              搜索
            </Button>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button onClick={handleReset}>
              重置
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        {subscriptionData.length === 0 && !loading ? (
          <Empty
            description="暂无付费订阅用户"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={subscriptionData}
            loading={loading}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条订阅用户`,
              onChange: handleTableChange,
            }}
            rowKey="id"
          />
        )}
      </Card>
    </div>
  );
};

export default SubscriptionManagement;
