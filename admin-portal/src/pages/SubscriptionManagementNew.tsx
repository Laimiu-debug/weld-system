import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Input, Select, Tag, Badge, Row, Col, message, Modal, Descriptions } from 'antd';
import { SearchOutlined, ReloadOutlined, ExportOutlined, EyeOutlined, CreditCardOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import apiService from '@/services/api';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;

interface FilterType {
  page: number;
  page_size: number;
  search?: string;
  plan_id?: string;
  status?: string;
}

const SubscriptionManagementNew: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filters, setFilters] = useState<FilterType>({
    page: 1,
    page_size: 10,
  });
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentSubscription, setCurrentSubscription] = useState<any>(null);

  // 加载订阅数据
  const loadSubscriptions = async () => {
    setLoading(true);
    try {
      const response = await apiService.get('/admin/membership/subscriptions', {
        params: filters
      });
      
      if (response.success) {
        setSubscriptions(response.data.items || []);
        setPagination({
          current: filters.page,
          pageSize: filters.page_size,
          total: response.data.total || 0,
        });
      } else {
        message.error('获取订阅数据失败');
      }
    } catch (error) {
      console.error('加载订阅数据失败:', error);
      message.error('获取订阅数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadSubscriptions();
  }, [filters]);

  // 处理搜索
  const handleSearch = (value: string) => {
    setFilters((prev: FilterType) => ({ ...prev, search: value, page: 1 }));
  };

  // 处理筛选变化
  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev: FilterType) => ({ ...prev, [key]: value, page: 1 }));
  };

  // 处理表格变化
  const handleTableChange = (paginationInfo: any) => {
    setFilters((prev: FilterType) => ({
      ...prev,
      page: paginationInfo.current,
      page_size: paginationInfo.pageSize,
    }));
  };

  // 查看订阅详情
  const handleViewDetail = async (subscriptionId: number) => {
    try {
      const response = await apiService.get(`/admin/membership/subscriptions/${subscriptionId}`);
      
      if (response.success) {
        setCurrentSubscription(response.data);
        setDetailModalVisible(true);
      } else {
        message.error('获取订阅详情失败');
      }
    } catch (error) {
      console.error('获取订阅详情失败:', error);
      message.error('获取订阅详情失败');
    }
  };

  // 手动续费
  const handleProcessRenewal = async (subscriptionId: number) => {
    try {
      const response = await apiService.post(`/admin/membership/subscriptions/${subscriptionId}/process-renewal`);
      
      if (response.success) {
        message.success('续费处理成功');
        loadSubscriptions(); // 重新加载数据
      } else {
        message.error('续费处理失败');
      }
    } catch (error) {
      console.error('续费处理失败:', error);
      message.error('续费处理失败');
    }
  };

  const getPlanColor = (plan: string) => {
    const colors: Record<string, string> = {
      free: 'default',
      personal_pro: 'blue',
      personal_advanced: 'green',
      personal_flagship: 'purple',
      enterprise: 'gold',
      enterprise_pro: 'red',
      enterprise_pro_max: 'magenta',
    };
    return colors[plan] || 'default';
  };

  const getPlanText = (plan: string) => {
    const texts: Record<string, string> = {
      free: '免费版',
      personal_pro: '个人专业版',
      personal_advanced: '个人高级版',
      personal_flagship: '个人旗舰版',
      enterprise: '企业版',
      enterprise_pro: '企业版PRO',
      enterprise_pro_max: '企业版PRO MAX',
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
      key: 'user',
      render: (record: any) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <UserOutlined style={{ marginRight: 4 }} />
            {record.user_email}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            ID: {record.user_id}
          </div>
        </div>
      ),
    },
    {
      title: '订阅计划',
      dataIndex: 'plan_id',
      key: 'plan_id',
      render: (plan: string) => (
        <Tag color={getPlanColor(plan)}>
          {getPlanText(plan)}
        </Tag>
      ),
      filters: [
        { text: '免费版', value: 'free' },
        { text: '个人专业版', value: 'personal_pro' },
        { text: '个人高级版', value: 'personal_advanced' },
        { text: '个人旗舰版', value: 'personal_flagship' },
        { text: '企业版', value: 'enterprise' },
        { text: '企业版PRO', value: 'enterprise_pro' },
        { text: '企业版PRO MAX', value: 'enterprise_pro_max' },
      ],
      onFilter: (value: any, record: any) => record.plan_id === value,
    },
    {
      title: '金额',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => (
        <span style={{ fontWeight: 500, color: '#1890ff' }}>
          ¥{price.toFixed(2)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
      filters: [
        { text: '正常', value: 'active' },
        { text: '已过期', value: 'expired' },
        { text: '已取消', value: 'cancelled' },
        { text: '待支付', value: 'pending' },
      ],
      onFilter: (value: any, record: any) => record.status === value,
    },
    {
      title: '订阅期间',
      key: 'period',
      render: (record: any) => (
        <div style={{ fontSize: '12px' }}>
          <div>开始: {record.start_date ? dayjs(record.start_date).format('YYYY-MM-DD') : '-'}</div>
          <div>结束: {record.end_date ? dayjs(record.end_date).format('YYYY-MM-DD') : '-'}</div>
        </div>
      ),
    },
    {
      title: '计费周期',
      dataIndex: 'billing_cycle',
      key: 'billing_cycle',
      render: (cycle: string) => {
        const cycleTexts: Record<string, string> = {
          monthly: '月付',
          quarterly: '季付',
          yearly: '年付',
        };
        return cycleTexts[cycle] || cycle;
      },
    },
    {
      title: '自动续费',
      dataIndex: 'auto_renew',
      key: 'auto_renew',
      render: (autoRenew: boolean) => (
        <Tag color={autoRenew ? 'green' : 'red'}>
          {autoRenew ? '已开启' : '已关闭'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          >
            查看
          </Button>
          {record.status === 'active' && (
            <Button 
              type="link" 
              size="small" 
              icon={<CreditCardOutlined />}
              onClick={() => handleProcessRenewal(record.id)}
            >
              续费
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">订阅管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadSubscriptions}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />} onClick={() => message.info('导出功能开发中')}>
            导出
          </Button>
        </Space>
      </div>

      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={6}>
            <Search
              placeholder="搜索用户邮箱"
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select 
              placeholder="订阅计划" 
              allowClear 
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('plan_id', value)}
            >
              <Option value="free">免费版</Option>
              <Option value="personal_pro">个人专业版</Option>
              <Option value="personal_advanced">个人高级版</Option>
              <Option value="personal_flagship">个人旗舰版</Option>
              <Option value="enterprise">企业版</Option>
              <Option value="enterprise_pro">企业版PRO</Option>
              <Option value="enterprise_pro_max">企业版PRO MAX</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select 
              placeholder="订阅状态" 
              allowClear 
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('status', value)}
            >
              <Option value="active">正常</Option>
              <Option value="expired">已过期</Option>
              <Option value="cancelled">已取消</Option>
              <Option value="pending">待支付</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button type="primary" icon={<SearchOutlined />} onClick={loadSubscriptions}>
              搜索
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={subscriptions}
          loading={loading}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      {/* 订阅详情弹窗 */}
      <Modal
        title="订阅详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {currentSubscription && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="订阅ID">
              {currentSubscription.id}
            </Descriptions.Item>
            <Descriptions.Item label="用户邮箱">
              {currentSubscription.user_email}
            </Descriptions.Item>
            <Descriptions.Item label="订阅计划">
              <Tag color={getPlanColor(currentSubscription.plan_id)}>
                {getPlanText(currentSubscription.plan_id)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(currentSubscription.status)}>
                {getStatusText(currentSubscription.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="金额">
              ¥{currentSubscription.price.toFixed(2)}
            </Descriptions.Item>
            <Descriptions.Item label="计费周期">
              {currentSubscription.billing_cycle === 'monthly' ? '月付' : 
               currentSubscription.billing_cycle === 'quarterly' ? '季付' : '年付'}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {currentSubscription.start_date ? 
                dayjs(currentSubscription.start_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="结束时间">
              {currentSubscription.end_date ? 
                dayjs(currentSubscription.end_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="自动续费">
              <Tag color={currentSubscription.auto_renew ? 'green' : 'red'}>
                {currentSubscription.auto_renew ? '已开启' : '已关闭'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="支付方式">
              {currentSubscription.payment_method || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="最后支付时间">
              {currentSubscription.last_payment_date ? 
                dayjs(currentSubscription.last_payment_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="下次计费时间">
              {currentSubscription.next_billing_date ? 
                dayjs(currentSubscription.next_billing_date).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {currentSubscription.created_at ? 
                dayjs(currentSubscription.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {currentSubscription.updated_at ? 
                dayjs(currentSubscription.updated_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}

        {/* 交易记录 */}
        {currentSubscription && currentSubscription.transactions && (
          <div style={{ marginTop: 20 }}>
            <h3>交易记录</h3>
            <Table
              dataSource={currentSubscription.transactions}
              columns={[
                {
                  title: '交易ID',
                  dataIndex: 'transaction_id',
                  key: 'transaction_id',
                },
                {
                  title: '金额',
                  dataIndex: 'amount',
                  key: 'amount',
                  render: (amount: number) => `¥${amount.toFixed(2)}`,
                },
                {
                  title: '支付方式',
                  dataIndex: 'payment_method',
                  key: 'payment_method',
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  render: (status: string) => (
                    <Tag color={status === 'success' ? 'green' : 'red'}>
                      {status === 'success' ? '成功' : '失败'}
                    </Tag>
                  ),
                },
                {
                  title: '交易时间',
                  dataIndex: 'transaction_date',
                  key: 'transaction_date',
                  render: (date: string) => date ? 
                    dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
                },
                {
                  title: '描述',
                  dataIndex: 'description',
                  key: 'description',
                },
              ]}
              pagination={false}
              size="small"
            />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SubscriptionManagementNew;