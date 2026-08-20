import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Input, Select, Tag, Badge, Row, Col, message, Empty, Collapse } from 'antd';
import { SearchOutlined, ReloadOutlined, ExportOutlined, EyeOutlined, BankOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '@/services/api';
import { downloadCsv } from '@/utils/csv';

const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;

const EnterpriseManagement: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [enterpriseData, setEnterpriseData] = useState<any[]>([]);
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  // 获取企业数据
  const fetchEnterpriseData = async (page = currentPage, search = searchText) => {
    setLoading(true);
    try {
      const response = await apiService.get('/enterprises', {
        params: {
          page,
          page_size: pageSize,
          search: search || undefined
        }
      });

      if (response && response.data && response.data.items) {
        setEnterpriseData(response.data.items);
        setTotal(response.data.total || 0);
      } else if (response && response.items) {
        // 兼容旧格式
        setEnterpriseData(response.items);
        setTotal(response.total || 0);
      } else {
        setEnterpriseData([]);
        setTotal(0);
      }
    } catch (error: any) {
      console.error('❌ 获取企业数据失败:', error);
      message.error(error.response?.data?.detail || '获取企业数据失败');
      setEnterpriseData([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnterpriseData();
  }, []);

  // 搜索处理
  const handleSearch = () => {
    setCurrentPage(1);
    fetchEnterpriseData(1, searchText);
  };

  // 重置搜索
  const handleReset = () => {
    setSearchText('');
    setCurrentPage(1);
    fetchEnterpriseData(1, '');
  };

  const handleRefresh = () => {
    fetchEnterpriseData(currentPage, searchText);
  };

  // 刷新数据
  const handleExport = () => {
    downloadCsv(
      `enterprises-${new Date().toISOString().slice(0, 10)}.csv`,
      ['企业ID', '企业名称', '管理员', '管理员邮箱', '员工数', '员工配额', '工厂配额'],
      enterpriseData.map((item) => [
        item.company_id,
        item.company_name,
        item.admin_user?.username,
        item.admin_user?.email,
        item.members?.length || 0,
        item.max_employees || 0,
        item.max_factories || 0,
      ]),
    );
  };

  // 分页处理
  const handleTableChange = (pagination: any) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    fetchEnterpriseData(pagination.current, searchText);
  };

  // 获取会员等级显示名称
  const getMembershipTierName = (tier: string) => {
    const tierNames: Record<string, string> = {
      personal_free: '个人免费版',
      personal_pro: '个人专业版',
      personal_advanced: '个人高级版',
      personal_flagship: '个人旗舰版',
      enterprise: '企业版',
      enterprise_pro: '企业版PRO',
      enterprise_pro_max: '企业版PRO MAX',
      free: '个人免费版',
    };
    return tierNames[tier] || tier;
  };

  // 获取会员等级颜色
  const getMembershipTierColor = (tier: string) => {
    const tierColors: Record<string, string> = {
      personal_free: 'default',
      personal_pro: 'blue',
      personal_advanced: 'green',
      personal_flagship: 'geekblue',
      enterprise: 'orange',
      enterprise_pro: 'magenta',
      enterprise_pro_max: 'red',
      free: 'default',
    };
    return tierColors[tier] || 'default';
  };

  const columns = [
    {
      title: '企业信息',
      key: 'enterprise_info',
      render: (record: any) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <BankOutlined style={{ marginRight: 4 }} />
            {record.company_name}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            企业ID: {record.company_id}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
            配额限制: {record.max_employees || 0} 员工 / {record.max_factories || 0} 工厂
          </div>
          <div style={{ color: '#52c41a', fontSize: '12px' }}>
            当前使用: {record.members?.length || 0} 员工
          </div>
        </div>
      ),
    },
    {
      title: '企业管理员',
      key: 'admin_user',
      render: (record: any) => (
        <div style={{ fontSize: '12px' }}>
          <div><UserOutlined style={{ marginRight: 4 }} />{record.admin_user?.username || 'N/A'}</div>
          <div style={{ color: '#8c8c8c' }}>{record.admin_user?.email || 'N/A'}</div>
          <Tag color="blue">管理员</Tag>
        </div>
      ),
    },
    {
      title: '成员数量',
      key: 'member_count',
      render: (record: any) => (
        <div style={{ textAlign: 'center' }}>
          <Badge
            count={record.members?.length || 0}
            showZero
            style={{ backgroundColor: '#52c41a' }}
          />
          <div style={{ color: '#8c8c8c', fontSize: '12px', marginTop: 4 }}>
            / {record.max_employees || 0}
          </div>
        </div>
      ),
    },
    {
      title: '订阅状态',
      key: 'subscription_status',
      render: (record: any) => {
        const status = record.subscription_status || 'inactive';
        const statusConfig: Record<string, { color: string; text: string }> = {
          active: { color: 'green', text: '活跃' },
          expired: { color: 'red', text: '已过期' },
          cancelled: { color: 'orange', text: '已取消' },
          inactive: { color: 'default', text: '未激活' },
        };
        const config = statusConfig[status] || statusConfig.inactive;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '会员等级',
      key: 'tier',
      render: (record: any) => (
        <Tag color={getMembershipTierColor(record.membership_tier || record.admin_user?.membership_tier || 'free')}>
          {getMembershipTierName(record.membership_tier || record.admin_user?.membership_tier || 'free')}
        </Tag>
      ),
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
            onClick={() => navigate(`/enterprises/${record.company_id}`)}
          >
            查看详情
          </Button>
        </Space>
      ),
    },
  ];

  // 展开显示企业成员的表格
  const expandedRowRender = (record: any) => {
    const memberColumns = [
      {
        title: '员工编号',
        dataIndex: 'employee_number',
        key: 'employee_number',
        width: 120,
      },
      {
        title: '用户名',
        dataIndex: 'username',
        key: 'username',
      },
      {
        title: '邮箱',
        dataIndex: 'email',
        key: 'email',
      },
      {
        title: '姓名',
        dataIndex: 'full_name',
        key: 'full_name',
      },
      {
        title: '职位',
        dataIndex: 'position',
        key: 'position',
      },
      {
        title: '部门',
        dataIndex: 'department',
        key: 'department',
      },
      {
        title: '角色',
        dataIndex: 'role',
        key: 'role',
        render: (role: string) => {
          const roleConfig: Record<string, { color: string; text: string }> = {
            admin: { color: 'red', text: '管理员' },
            manager: { color: 'orange', text: '经理' },
            employee: { color: 'blue', text: '员工' },
          };
          const config = roleConfig[role] || { color: 'default', text: role };
          return <Tag color={config.color}>{config.text}</Tag>;
        },
      },
      {
        title: '状态',
        dataIndex: 'is_active',
        key: 'is_active',
        render: (isActive: boolean) => (
          <Tag color={isActive ? 'green' : 'red'}>
            {isActive ? '活跃' : '停用'}
          </Tag>
        ),
      },
    ];

    return (
      <Table
        columns={memberColumns}
        dataSource={record.members || []}
        pagination={false}
        size="small"
        rowKey="id"
        locale={{ emptyText: '暂无员工' }}
      />
    );
  };

  return (
    <div>
      <div className="admin-header">
        <h1 className="page-title">企业管理</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      </div>

      <Card className="filter-section" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索企业名称、管理员邮箱或用户名"
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
        {enterpriseData.length === 0 && !loading ? (
          <Empty
            description="暂无企业用户"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={enterpriseData}
            loading={loading}
            scroll={{ x: 1100 }}
            expandable={{
              expandedRowRender,
              rowExpandable: (record) => record.members && record.members.length > 0,
            }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条企业`,
              onChange: handleTableChange,
            }}
            rowKey="company_id"
          />
        )}
      </Card>
    </div>
  );
};

export default EnterpriseManagement;
