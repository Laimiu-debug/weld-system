import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Table, Select, DatePicker, Button, Space, message, Progress, Alert, Typography } from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  DollarOutlined,
  RiseOutlined,
  ReloadOutlined,
  BarChartOutlined,
  EyeOutlined,
  FallOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';
import dayjs from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text } = Typography;

const DataStatistics: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('month');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [subscriptionStats, setSubscriptionStats] = useState<any>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const getDateRange = useCallback(() => {
    const now = dayjs();
    let startDate: dayjs.Dayjs;
    let endDate = now;

    switch (timeRange) {
      case 'week':
        startDate = now.subtract(7, 'day');
        break;
      case 'month':
        startDate = now.subtract(30, 'day');
        break;
      case 'quarter':
        startDate = now.subtract(90, 'day');
        break;
      case 'year':
        startDate = now.subtract(365, 'day');
        break;
      default:
        startDate = now.subtract(30, 'day');
    }

    if (dateRange) {
      startDate = dateRange[0];
      endDate = dateRange[1];
    }

    return {
      start_date: startDate.format('YYYY-MM-DD'),
      end_date: endDate.format('YYYY-MM-DD'),
    };
  }, [timeRange, dateRange]);

  const safeApiCall = async (apiCall: () => Promise<any>, errorMessage: string) => {
    try {
      return await apiCall();
    } catch (error: any) {
      console.error(`DataStatistics: ${errorMessage} failed:`, error);
      setApiError(`${errorMessage}: ${error.message || '网络错误'}`);
      return null;
    }
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    setApiError(null);

    const dateParams = getDateRange();
    const [userData, subscriptionData] = await Promise.allSettled([
      safeApiCall(() => apiService.getUserStatistics(dateParams), '获取用户统计'),
      safeApiCall(() => apiService.getSubscriptionStatistics(dateParams), '获取订阅统计'),
    ]);

    if (userData.status === 'fulfilled' && userData.value) {
      setUserStats(userData.value);
    }
    if (subscriptionData.status === 'fulfilled' && subscriptionData.value) {
      setSubscriptionStats(subscriptionData.value);
    }

    setLoading(false);
  }, [getDateRange]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // 真实趋势：每日新增注册 + 当日登录活跃 + 累计用户
  const activityData = React.useMemo(() => {
    if (!userStats?.trend) return [];

    return userStats.trend.map((item: any, index: number) => {
      const newUsers = item.new_users ?? item.count ?? 0;
      const activeUsers = item.active_users ?? null;
      const totalUsers = item.total_users ?? null;
      const activeRate =
        totalUsers && activeUsers != null
          ? `${((activeUsers / totalUsers) * 100).toFixed(1)}%`
          : '-';

      return {
        key: String(index + 1),
        date: item.date,
        newUsers,
        activeUsers: activeUsers ?? '-',
        totalUsers: totalUsers ?? '-',
        activeRate,
      };
    });
  }, [userStats]);

  const activityColumns = [
    { title: '日期', dataIndex: 'date', key: 'date' },
    {
      title: '新增注册',
      dataIndex: 'newUsers',
      key: 'newUsers',
      render: (text: number) => (
        <span style={{ color: '#1F5EFF', fontWeight: 500 }}>{Number(text).toLocaleString()}</span>
      ),
    },
    {
      title: '当日登录',
      dataIndex: 'activeUsers',
      key: 'activeUsers',
    },
    {
      title: '累计用户',
      dataIndex: 'totalUsers',
      key: 'totalUsers',
    },
    {
      title: '当日活跃率',
      dataIndex: 'activeRate',
      key: 'activeRate',
      render: (rate: string) => {
        if (rate === '-') return rate;
        return (
          <span style={{ color: parseFloat(rate) > 10 ? '#52c41a' : '#8c8c8c' }}>{rate}</span>
        );
      },
    },
  ];

  const handleRefresh = () => {
    void loadData();
    message.success('数据已刷新');
  };

  const periodRevenue = subscriptionStats?.revenue?.period ?? subscriptionStats?.revenue?.monthly ?? 0;

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">数据统计</h1>
        <Space>
          <Select
            value={dateRange ? 'custom' : timeRange}
            onChange={(value) => {
              if (value === 'custom') return;
              setTimeRange(value);
              setDateRange(null);
            }}
            style={{ width: 120 }}
          >
            <Option value="week">近 7 天</Option>
            <Option value="month">近 30 天</Option>
            <Option value="quarter">近 90 天</Option>
            <Option value="year">近 1 年</Option>
            {dateRange && <Option value="custom">自定义</Option>}
          </Select>
          <RangePicker
            value={dateRange}
            onChange={(dates) =>
              setDateRange(dates?.[0] && dates?.[1] ? [dates[0], dates[1]] : null)
            }
            style={{ width: 240 }}
          />
          <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {apiError && (
        <Alert
          message="数据加载错误"
          description={apiError}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
          onClose={() => setApiError(null)}
        />
      )}

      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        区间：{getDateRange().start_date} ~ {getDateRange().end_date} · 活跃用户按近 30 天登录统计
      </Text>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={userStats?.total_users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1F5EFF' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#52c41a' }}>
              <RiseOutlined /> 区间新增 {userStats?.new_users || 0} 人
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户（30天）"
              value={userStats?.active_users || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#8c8c8c' }}>
              活跃率{' '}
              {userStats?.total_users
                ? ((userStats.active_users / userStats.total_users) * 100).toFixed(1)
                : 0}
              %
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="区间收入"
              value={periodRevenue}
              prefix={<DollarOutlined />}
              suffix="元"
              valueStyle={{ color: '#faad14' }}
              precision={0}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#8c8c8c' }}>
              近 365 天实收 ¥{(subscriptionStats?.revenue?.annual || 0).toLocaleString()}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="付费订阅"
              value={subscriptionStats?.active_subscriptions || 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1546c9' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#8c8c8c' }}>
              转化率 {subscriptionStats?.conversion_rate || 0}%
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="继承会员"
              value={subscriptionStats?.inherited_members_count || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1F5EFF' }}
            />
            <div style={{ marginTop: 8, fontSize: '12px', color: '#8c8c8c' }}>
              企业员工继承（不计入付费）
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="用户等级分布">
            {userStats?.by_tier && (
              <div style={{ padding: '16px 0' }}>
                {Object.entries(userStats.by_tier as Record<string, number>).map(([tier, count]) => (
                  <div key={tier} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span>
                        {tier === 'free' || tier === 'personal_free'
                          ? '免费用户'
                          : tier === 'personal_advanced'
                            ? '个人高级版'
                            : tier === 'personal_flagship'
                              ? '个人旗舰版'
                              : tier === 'personal_pro'
                                ? '个人专业版'
                                : tier === 'enterprise'
                                  ? '企业版'
                                  : tier}
                      </span>
                      <span style={{ fontWeight: 500 }}>{count} 人</span>
                    </div>
                    <Progress
                      percent={userStats.total_users ? (count / userStats.total_users) * 100 : 0}
                      showInfo={false}
                      strokeColor={
                        tier === 'free' || tier === 'personal_free'
                          ? '#d9d9d9'
                          : tier === 'personal_advanced' || tier === 'personal_pro'
                            ? '#1F5EFF'
                            : tier === 'personal_flagship'
                              ? '#1546c9'
                              : tier?.startsWith('enterprise')
                                ? '#52c41a'
                                : '#faad14'
                      }
                    />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="付费等级分布">
            {subscriptionStats?.by_type && Object.keys(subscriptionStats.by_type).length > 0 ? (
              <div style={{ padding: '16px 0' }}>
                {Object.entries(subscriptionStats.by_type as Record<string, number>).map(
                  ([type, count]) => (
                    <div key={type} style={{ marginBottom: 12 }}>
                      <div
                        style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}
                      >
                        <span>
                          {type === 'personal_advanced'
                            ? '个人高级版'
                            : type === 'personal_flagship'
                              ? '个人旗舰版'
                              : type === 'personal_pro'
                                ? '个人专业版'
                                : type === 'enterprise'
                                  ? '企业版'
                                  : type}
                        </span>
                        <span style={{ fontWeight: 500 }}>{count} 个</span>
                      </div>
                      <Progress
                        percent={
                          subscriptionStats.total_subscriptions
                            ? (count / subscriptionStats.total_subscriptions) * 100
                            : subscriptionStats.active_subscriptions
                              ? (count / subscriptionStats.active_subscriptions) * 100
                              : 0
                        }
                        showInfo={false}
                        strokeColor={
                          type === 'personal_advanced' || type === 'personal_pro'
                            ? '#1F5EFF'
                            : type === 'personal_flagship'
                              ? '#1546c9'
                              : type?.startsWith('enterprise')
                                ? '#52c41a'
                                : '#faad14'
                        }
                      />
                    </div>
                  )
                )}
              </div>
            ) : (
              <Text type="secondary">暂无付费等级数据</Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="用户增长率"
              value={userStats?.growth_rate || 0}
              precision={1}
              suffix="%"
              prefix={(userStats?.growth_rate || 0) >= 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{
                color:
                  (userStats?.growth_rate || 0) > 20
                    ? '#52c41a'
                    : (userStats?.growth_rate || 0) > 0
                      ? '#faad14'
                      : '#ff4d4f',
              }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              相对区间起点存量
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="流失率"
              value={subscriptionStats?.churn_rate || 0}
              precision={1}
              suffix="%"
              prefix={<FallOutlined />}
              valueStyle={{
                color:
                  (subscriptionStats?.churn_rate || 0) < 5
                    ? '#52c41a'
                    : (subscriptionStats?.churn_rate || 0) < 10
                      ? '#faad14'
                      : '#ff4d4f',
              }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              区间取消 / 近似期初活跃
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="新增订阅"
              value={subscriptionStats?.new_subscriptions || 0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="取消/过期"
              value={subscriptionStats?.cancelled_subscriptions || 0}
              prefix={<FallOutlined />}
              valueStyle={{
                color:
                  (subscriptionStats?.cancelled_subscriptions || 0) > 0 ? '#ff4d4f' : '#52c41a',
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="近 365 天收入"
              value={subscriptionStats?.revenue?.annual || 0}
              prefix="¥"
              valueStyle={{ color: '#1F5EFF' }}
              precision={0}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="用户平均收入（区间）"
              value={subscriptionStats?.average_revenue_per_user || 0}
              prefix="¥"
              valueStyle={{ color: '#1546c9' }}
              precision={0}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card>
            <Statistic
              title="久未登录用户"
              value={userStats?.inactive_users || 0}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#8c8c8c' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              启用账号且近 30 天未登录
              {userStats?.disabled_users != null ? ` · 已禁用 ${userStats.disabled_users}` : ''}
            </Text>
          </Card>
        </Col>
      </Row>

      <Card title="用户增长与活跃（按日）" extra={<Text type="secondary">基于注册与登录时间，非页面浏览</Text>}>
        <Table
          columns={activityColumns}
          dataSource={activityData}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          locale={{ emptyText: '暂无趋势数据' }}
        />
      </Card>
    </div>
  );
};

export default DataStatistics;
