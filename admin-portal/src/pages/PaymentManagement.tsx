import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Input, 
  Select, 
  Tag, 
  Badge, 
  Modal, 
  Descriptions,
  message,
  Row,
  Col,
  Statistic,
  Empty
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  EyeOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  CheckOutlined,
  StopOutlined
} from '@ant-design/icons';
import apiService from '@/services/api';

const { Search } = Input;
const { Option } = Select;

interface PaymentRecord {
  order_id: string;
  transaction_id: string;
  user_id: number;
  user_name: string;
  user_email: string;
  plan_id: string;
  plan_name: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  description: string;
  created_at: string;
  updated_at: string;
  transaction_date?: string;
}

interface PaymentStats {
  total_pending: number;
  total_confirmed: number;
  total_rejected: number;
  total_amount_pending: number;
}

const PaymentManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [stats, setStats] = useState<PaymentStats>({
    total_pending: 0,
    total_confirmed: 0,
    total_rejected: 0,
    total_amount_pending: 0,
  });
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('pending_confirm');
  const [selectedPayment, setSelectedPayment] = useState<PaymentRecord | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // 加载支付数据
  const loadPayments = async () => {
    setLoading(true);
    try {
      const response = await apiService.get('/payments/pending', {
        params: {
          status_filter: statusFilter
        }
      });

      console.log('支付数据响应:', response);

      if (response && Array.isArray(response)) {
        setPayments(response);

        // 计算统计数据
        const pending = response.filter(p => p.status === 'pending_confirm');
        const confirmed = response.filter(p => p.status === 'success');
        const rejected = response.filter(p => p.status === 'rejected');
        const pendingAmount = pending.reduce((sum, p) => sum + (p.amount || 0), 0);

        setStats({
          total_pending: pending.length,
          total_confirmed: confirmed.length,
          total_rejected: rejected.length,
          total_amount_pending: pendingAmount,
        });
      } else {
        setPayments([]);
      }
    } catch (error: any) {
      console.error('获取支付数据失败:', error);
      message.error('获取支付数据失败');
      setPayments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
    // 每30秒自动刷新
    const interval = setInterval(loadPayments, 30000);
    return () => clearInterval(interval);
  }, [statusFilter]);

  // 确认支付
  const confirmPayment = async (orderId: string) => {
    Modal.confirm({
      title: '确认支付',
      content: '确定要确认这笔支付吗?确认后将立即开通会员权益。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          // API拦截器会自动提取data字段，所以这里直接接收data对象
          // 如果请求成功，response就是data对象；如果失败，会抛出异常进入catch块
          await apiService.post('/payments/confirm', {
            order_id: orderId
          });

          // 请求成功
          message.success('支付已确认,会员已开通');
          // 切换到"全部"状态以显示已确认的订单
          setStatusFilter('all');
          loadPayments();
        } catch (error: any) {
          console.error('确认支付失败:', error);
          message.error(error.response?.data?.detail || '确认失败');
        }
      }
    });
  };

  // 拒绝支付
  const rejectPayment = async (orderId: string) => {
    Modal.confirm({
      title: '拒绝支付',
      content: '确定要拒绝这笔支付吗?',
      okText: '拒绝',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          // API拦截器会自动提取data字段，所以这里直接接收data对象
          // 如果请求成功，response就是data对象；如果失败，会抛出异常进入catch块
          await apiService.post('/payments/reject', {
            order_id: orderId
          });

          // 请求成功
          message.success('支付已拒绝');
          // 切换到"全部"状态以显示已拒绝的订单
          setStatusFilter('all');
          loadPayments();
        } catch (error: any) {
          console.error('拒绝支付失败:', error);
          message.error(error.response?.data?.detail || '操作失败');
        }
      }
    });
  };

  // 查看详情
  const viewDetail = (payment: PaymentRecord) => {
    setSelectedPayment(payment);
    setDetailVisible(true);
  };

  // 刷新数据
  const handleRefresh = () => {
    loadPayments();
    message.success('数据已刷新');
  };

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const configs: Record<string, { text: string; color: string; badge: any }> = {
      'pending_confirm': { text: '待确认', color: 'orange', badge: 'warning' },
      'success': { text: '已确认', color: 'green', badge: 'success' },
      'rejected': { text: '已拒绝', color: 'red', badge: 'error' },
      'pending': { text: '待支付', color: 'blue', badge: 'processing' },
      'failed': { text: '失败', color: 'red', badge: 'error' },
    };
    return configs[status] || { text: status, color: 'default', badge: 'default' };
  };

  // 获取支付方式文本
  const getPaymentMethodText = (method: string) => {
    const methods: Record<string, string> = {
      'alipay': '支付宝',
      'wechat': '微信支付',
      'bank_transfer': '银行转账',
    };
    return methods[method] || method;
  };

  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_id',
      key: 'order_id',
      width: 180,
      fixed: 'left' as const,
      render: (text: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{text}</span>
      )
    },
    {
      title: '用户交易号',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 180,
      render: (text: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: text ? '#1890ff' : '#999' }}>
          {text || '未提供'}
        </span>
      )
    },
    {
      title: '用户信息',
      key: 'user_info',
      width: 200,
      render: (record: PaymentRecord) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.user_name}</div>
          <div style={{ color: '#8c8c8c', fontSize: 12 }}>{record.user_email}</div>
        </div>
      )
    },
    {
      title: '套餐',
      dataIndex: 'plan_name',
      key: 'plan_name',
      width: 150,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number, record: PaymentRecord) => (
        <span style={{ color: '#ff4d4f', fontWeight: 'bold', fontSize: 14 }}>
          {record.currency === 'CNY' ? '¥' : '$'}{amount.toFixed(2)}
        </span>
      )
    },
    {
      title: '支付方式',
      dataIndex: 'payment_method',
      key: 'payment_method',
      width: 120,
      render: (method: string) => (
        <Tag color={method === 'alipay' ? 'blue' : method === 'wechat' ? 'green' : 'cyan'}>
          {getPaymentMethodText(method)}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = getStatusConfig(status);
        return <Badge status={config.badge} text={config.text} />;
      }
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: PaymentRecord) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending_confirm' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => confirmPayment(record.order_id)}
                style={{ color: '#52c41a' }}
              >
                确认
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<CloseCircleOutlined />}
                onClick={() => rejectPayment(record.order_id)}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  // 过滤数据
  const filteredPayments = payments.filter(payment => {
    if (!searchText) return true;
    const search = searchText.toLowerCase();
    return (
      payment.transaction_id?.toLowerCase().includes(search) ||
      payment.user_name?.toLowerCase().includes(search) ||
      payment.user_email?.toLowerCase().includes(search) ||
      payment.plan_name?.toLowerCase().includes(search)
    );
  });

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">支付订单管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待确认订单"
              value={stats.total_pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待确认金额"
              value={stats.total_amount_pending}
              prefix="¥"
              precision={2}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已确认订单"
              value={stats.total_confirmed}
              prefix={<CheckOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已拒绝订单"
              value={stats.total_rejected}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选区域 */}
      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索交易号、用户名、邮箱或套餐"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '100%' }}
            >
              <Option value="pending_confirm">待确认</Option>
              <Option value="success">已确认</Option>
              <Option value="rejected">已拒绝</Option>
              <Option value="all">全部</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Card>
        {filteredPayments.length === 0 && !loading ? (
          <Empty
            description="暂无支付订单"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={filteredPayments}
            loading={loading}
            rowKey="order_id"
            scroll={{ x: 1500 }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: filteredPayments.length,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条订单`,
              onChange: (page, size) => {
                setCurrentPage(page);
                setPageSize(size || 10);
              }
            }}
          />
        )}
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="支付订单详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={
          selectedPayment?.status === 'pending_confirm' ? [
            <Button key="reject" danger onClick={() => {
              if (selectedPayment) {
                rejectPayment(selectedPayment.order_id);
                setDetailVisible(false);
              }
            }}>
              拒绝支付
            </Button>,
            <Button key="confirm" type="primary" onClick={() => {
              if (selectedPayment) {
                confirmPayment(selectedPayment.order_id);
                setDetailVisible(false);
              }
            }}>
              确认支付
            </Button>
          ] : [
            <Button key="close" onClick={() => setDetailVisible(false)}>
              关闭
            </Button>
          ]
        }
        width={700}
      >
        {selectedPayment && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="订单号" span={2}>
              <span style={{ fontFamily: 'monospace', fontSize: 12 }}>
                {selectedPayment.order_id}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="用户交易号" span={2}>
              <span style={{ fontFamily: 'monospace', fontSize: 12, color: selectedPayment.transaction_id ? '#1890ff' : '#999' }}>
                {selectedPayment.transaction_id || '未提供'}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="用户名">
              {selectedPayment.user_name}
            </Descriptions.Item>
            <Descriptions.Item label="用户邮箱">
              {selectedPayment.user_email}
            </Descriptions.Item>
            <Descriptions.Item label="套餐">
              {selectedPayment.plan_name}
            </Descriptions.Item>
            <Descriptions.Item label="金额">
              <span style={{ color: '#ff4d4f', fontWeight: 'bold', fontSize: 16 }}>
                {selectedPayment.currency === 'CNY' ? '¥' : '$'}
                {selectedPayment.amount.toFixed(2)}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="支付方式">
              <Tag color={selectedPayment.payment_method === 'alipay' ? 'blue' : 'green'}>
                {getPaymentMethodText(selectedPayment.payment_method)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {(() => {
                const config = getStatusConfig(selectedPayment.status);
                return <Badge status={config.badge} text={config.text} />;
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="用户提交的交易凭证" span={2}>
              {selectedPayment.description || '无'}
            </Descriptions.Item>
            <Descriptions.Item label="提交时间">
              {new Date(selectedPayment.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(selectedPayment.updated_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            {selectedPayment.transaction_date && (
              <Descriptions.Item label="交易时间" span={2}>
                {new Date(selectedPayment.transaction_date).toLocaleString('zh-CN')}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default PaymentManagement;

