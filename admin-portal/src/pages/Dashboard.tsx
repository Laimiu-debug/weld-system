import React, { useCallback, useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Progress, Space, Button, Alert } from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  DollarOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import apiService from '@/services/api';

const Dashboard: React.FC = () => {
  console.log('Dashboard: Component loading...');

  // 使用错误边界和安全的API调用
  const [apiError, setApiError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [subscriptionStats, setSubscriptionStats] = useState<any>(null);
  const [errorLogs, setErrorLogs] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // 安全的API调用函数
  const safeApiCall = async (apiCall: () => Promise<any>, errorMessage: string) => {
    try {
      console.log(`Dashboard: Making API call: ${errorMessage}`);
      const result = await apiCall();
      console.log(`Dashboard: API call success: ${errorMessage}`, result);
      return result;
    } catch (error: any) {
      console.error(`Dashboard: API call failed: ${errorMessage}`, error);

      // 详细的错误信息
      let errorDetails = '';
      if (error.response) {
        // 服务器响应了错误状态码
        errorDetails = `服务器错误 ${error.response.status}: ${error.response.data?.message || error.response.statusText || '未知错误'}`;
      } else if (error.request) {
        // 请求已发出但没有收到响应
        errorDetails = '网络连接失败：服务器无响应，请检查后端服务是否启动';
      } else {
        // 请求配置出错
        errorDetails = `请求配置错误: ${error.message}`;
      }

      // 如果是401错误，不自动清除认证状态，让用户手动处理
      if (error.response?.status === 401) {
        console.log('Dashboard: 401 error detected, but not auto-clearing auth');
        setApiError(`API认证失败，但保持登录状态。${errorDetails}`);
      } else {
        setApiError(`${errorMessage}: ${errorDetails}`);
      }
      return null;
    }
  };

  // 数据加载函数
  const loadData = useCallback(async () => {
    // 检查认证状态
    const token = localStorage.getItem('admin_token');
    if (!token) {
      setApiError('没有找到认证token，请先登录');
      setLoading(false);
      return;
    }
    setLoading(true);
    setApiError(null);

    // 并行调用所有API，但不会因为一个失败而影响其他
    const [statusData, userData, subscriptionData, logsData] = await Promise.allSettled([
      safeApiCall(() => apiService.getSystemStatus(), '获取系统状态'),
      safeApiCall(() => apiService.getUserStatistics({
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
      }), '获取用户统计'),
      safeApiCall(() => apiService.getSubscriptionStatistics({
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
      }), '获取订阅统计'),
      safeApiCall(() => apiService.getErrorLogs({ page: 1, page_size: 10 }), '获取错误日志')
    ]);

    // 处理结果
    if (statusData.status === 'fulfilled' && statusData.value) {
      setSystemStatus(statusData.value);
    }
    if (userData.status === 'fulfilled' && userData.value) {
      setUserStats(userData.value);
    }
    if (subscriptionData.status === 'fulfilled' && subscriptionData.value) {
      setSubscriptionStats(subscriptionData.value);
    }
    if (logsData.status === 'fulfilled' && logsData.value) {
      setErrorLogs(logsData.value);
    }

    setLoading(false);
  }, []);

  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, [loadData]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#52c41a';
      case 'warning':
        return '#faad14';
      case 'error':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <AlertOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const pieColors = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1'];

  const logColumns = [
    {
      title: '级别',
      dataIndex: 'log_level',
      key: 'log_level',
      render: (level: string) => {
        const color = level === 'error' ? 'red' : level === 'warning' ? 'orange' : 'blue';
        return <Tag color={color}>{level.toUpperCase()}</Tag>;
      },
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <h2>正在加载数据...</h2>
        <Progress percent={100} showInfo={false} status="active" />
      </div>
    );
  }

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">系统数据概览</h1>
        <Space>
          <Button
            type="primary"
            onClick={() => {
              setLoading(true);
              setApiError(null);
              loadData();
            }}
            loading={loading}
          >
            刷新数据
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
          style={{ marginBottom: 24 }}
          onClose={() => setApiError(null)}
        />
      )}

      {/* 数据概览卡片 */}
      {userStats && subscriptionStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24}>
            <Card title="业务概览" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6} lg={4}>
                  <Statistic
                    title="总用户数"
                    value={userStats.total_users}
                    prefix={<UserOutlined style={{ color: 'white' }} />}
                    valueStyle={{ color: 'white' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6} lg={4}>
                  <Statistic
                    title="付费用户"
                    value={subscriptionStats.active_subscriptions}
                    prefix={<DollarOutlined style={{ color: 'white' }} />}
                    valueStyle={{ color: 'white' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6} lg={4}>
                  <Statistic
                    title="继承会员"
                    value={subscriptionStats.inherited_members_count || 0}
                    prefix={<TeamOutlined style={{ color: 'white' }} />}
                    valueStyle={{ color: 'white' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6} lg={4}>
                  <Statistic
                    title="月收入"
                    value={subscriptionStats.revenue.monthly}
                    precision={0}
                    prefix="¥"
                    valueStyle={{ color: 'white' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6} lg={4}>
                  <Statistic
                    title="转化率"
                    value={subscriptionStats.conversion_rate}
                    precision={1}
                    suffix="%"
                    prefix={<TrophyOutlined style={{ color: 'white' }} />}
                    valueStyle={{ color: 'white' }}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {/* 系统状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={systemStatus?.status || 'unknown'}
              prefix={getStatusIcon(systemStatus?.status || 'unknown')}
              valueStyle={{ color: getStatusColor(systemStatus?.status || 'unknown') }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="CPU 使用率"
              value={systemStatus?.cpu_usage || 0}
              precision={1}
              suffix="%"
              valueStyle={{ color: (systemStatus?.cpu_usage || 0) > 80 ? '#ff4d4f' : '#3f8600' }}
            />
            <Progress
              percent={systemStatus?.cpu_usage || 0}
              strokeColor={(systemStatus?.cpu_usage || 0) > 80 ? '#ff4d4f' : '#3f8600'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={systemStatus?.memory_usage || 0}
              precision={1}
              suffix="%"
              valueStyle={{ color: (systemStatus?.memory_usage || 0) > 80 ? '#ff4d4f' : '#3f8600' }}
            />
            <Progress
              percent={systemStatus?.memory_usage || 0}
              strokeColor={(systemStatus?.memory_usage || 0) > 80 ? '#ff4d4f' : '#3f8600'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={systemStatus?.active_users || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 用户和订阅统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={userStats?.total_users || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={userStats?.active_users || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${userStats?.total_users || 0}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="付费订阅"
              value={subscriptionStats?.active_subscriptions || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="转化率"
              value={subscriptionStats?.conversion_rate || 0}
              precision={1}
              suffix="%"
              prefix={subscriptionStats?.conversion_rate > 10 ? <TrophyOutlined /> : <RiseOutlined />}
              valueStyle={{
                color: (subscriptionStats?.conversion_rate || 0) > 15 ? '#52c41a' :
                        (subscriptionStats?.conversion_rate || 0) > 10 ? '#faad14' : '#ff4d4f'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 收入统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="月收入"
              value={subscriptionStats?.revenue?.monthly || 0}
              precision={0}
              prefix="¥"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="年收入"
              value={subscriptionStats?.revenue?.annual || 0}
              precision={0}
              prefix="¥"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="用户平均收入"
              value={subscriptionStats?.average_revenue_per_user || 0}
              precision={0}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 增长指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="用户增长率"
              value={userStats?.growth_rate || 0}
              precision={1}
              suffix="%"
              prefix={userStats?.growth_rate > 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{
                color: (userStats?.growth_rate || 0) > 20 ? '#52c41a' :
                        (userStats?.growth_rate || 0) > 0 ? '#faad14' : '#ff4d4f'
              }}
            />
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
                color: (subscriptionStats?.churn_rate || 0) < 5 ? '#52c41a' :
                        (subscriptionStats?.churn_rate || 0) < 10 ? '#faad14' : '#ff4d4f'
              }}
            />
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
              title="取消订阅"
              value={subscriptionStats?.cancelled_subscriptions || 0}
              prefix={<FallOutlined />}
              valueStyle={{ color: (subscriptionStats?.cancelled_subscriptions || 0) > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="用户增长趋势" className="chart-container">
            {userStats?.trend && (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={userStats.trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip
                    formatter={(value) => [`${value} 用户`, '新增用户']}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#1890ff"
                    strokeWidth={2}
                    dot={{ fill: '#1890ff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="用户等级分布" className="chart-container">
            {userStats?.by_tier && (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={Object.entries(userStats.by_tier).map(([name, value]) => ({
                      name: name === 'free' ? '免费用户' :
                            name === 'personal_advanced' ? '个人高级版' :
                            name === 'personal_flagship' ? '个人旗舰版' :
                            name === 'enterprise' ? '企业版' : name,
                      value,
                    }))}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {Object.entries(userStats.by_tier).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
      </Row>

      {/* 订阅类型分布 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="订阅类型分布" className="chart-container">
            {subscriptionStats?.by_type && (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={Object.entries(subscriptionStats.by_type).map(([name, value]) => ({
                      name: name === 'personal_advanced' ? '个人高级版' :
                            name === 'personal_flagship' ? '个人旗舰版' :
                            name === 'enterprise' ? '企业版' : name,
                      value,
                    }))}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {Object.entries(subscriptionStats.by_type).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="用户状态分布" className="chart-container">
            {userStats?.by_status && (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={Object.entries(userStats.by_status).map(([name, value]) => ({
                      name: name === 'active' ? '活跃用户' : name === 'inactive' ? '非活跃用户' : name,
                      value,
                    }))}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {Object.entries(userStats.by_status).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
      </Row>

      {/* 最近错误日志 */}
      <Card title="最近错误日志" style={{ marginBottom: 24 }}>
        <Table
          columns={logColumns}
          dataSource={errorLogs?.items || []}
          pagination={false}
          size="small"
          rowKey="id"
        />
        {errorLogs?.items?.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
            暂无错误日志
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;