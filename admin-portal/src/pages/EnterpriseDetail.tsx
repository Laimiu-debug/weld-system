import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Table,
  Button,
  Space,
  Spin,
  message,
  Row,
  Col,
  Statistic,
  Progress,
} from 'antd';
import {
  ArrowLeftOutlined,
  BankOutlined,
  TeamOutlined,
  HomeOutlined,
  UserOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import apiService from '@/services/api';

interface EnterpriseDetailData {
  company_id: string;
  company_name: string;
  membership_tier: string;
  subscription_status: string;
  subscription_end_date?: string;
  max_employees: number;
  max_factories: number;
  created_at: string;
  admin_user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
  };
  members: Array<{
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: string;
    position: string;
    department: string;
    employee_number: string;
  }>;
}

const EnterpriseDetail: React.FC = () => {
  const { enterpriseId } = useParams<{ enterpriseId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [enterpriseData, setEnterpriseData] = useState<EnterpriseDetailData | null>(null);

  // 获取企业详情
  const fetchEnterpriseDetail = async () => {
    if (!enterpriseId) return;

    setLoading(true);
    try {
      const enterprise = await apiService.getEnterpriseDetail(enterpriseId);
      if (enterprise) {
        setEnterpriseData(enterprise as EnterpriseDetailData);
      } else {
        message.error('未找到企业信息');
        navigate('/enterprises');
      }
    } catch (error: any) {
      console.error('获取企业详情失败:', error);
      message.error(error.response?.data?.detail || '获取企业详情失败');
      navigate('/enterprises');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnterpriseDetail();
  }, [enterpriseId]);

  // 获取会员等级显示名称
  const getMembershipTierName = (tier: string) => {
    const tierNames: Record<string, string> = {
      enterprise: '企业版',
      enterprise_pro: '企业版PRO',
      enterprise_pro_max: '企业版PRO MAX',
    };
    return tierNames[tier] || tier;
  };

  // 获取会员等级颜色
  const getMembershipTierColor = (tier: string) => {
    const tierColors: Record<string, string> = {
      enterprise: 'orange',
      enterprise_pro: 'magenta',
      enterprise_pro_max: 'red',
    };
    return tierColors[tier] || 'default';
  };

  // 员工表格列定义
  const employeeColumns = [
    {
      title: '员工编号',
      dataIndex: 'employee_number',
      key: 'employee_number',
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text: string, record: any) => (
        <div>
          <div>{text || record.username}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>{record.email}</div>
        </div>
      ),
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
        const roleMap: Record<string, { text: string; color: string }> = {
          admin: { text: '管理员', color: 'red' },
          manager: { text: '经理', color: 'blue' },
          employee: { text: '员工', color: 'default' },
        };
        const roleInfo = roleMap[role] || { text: role, color: 'default' };
        return <Tag color={roleInfo.color}>{roleInfo.text}</Tag>;
      },
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!enterpriseData) {
    return (
      <div>
        <div className="admin-header">
          <h1 className="page-title">企业详情</h1>
        </div>
        <Card>
          <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
            未找到企业信息
          </div>
        </Card>
      </div>
    );
  }

  const employeeUsagePercentage = Math.round(
    ((enterpriseData.members?.length || 0) / Math.max(enterpriseData.max_employees || 1, 1)) * 100
  );

  return (
    <div>
      <div className="admin-header">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/enterprises')}
          >
            返回
          </Button>
          <h1 className="page-title">企业详情</h1>
        </Space>
      </div>

      {/* 企业基本信息 */}
      <Card
        title={
          <Space>
            <BankOutlined />
            <span>企业基本信息</span>
          </Space>
        }
        className="mb-4"
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="企业名称">
            {enterpriseData.company_name}
          </Descriptions.Item>
          <Descriptions.Item label="企业ID">
            {enterpriseData.company_id}
          </Descriptions.Item>
          <Descriptions.Item label="会员等级">
            <Tag color={getMembershipTierColor(enterpriseData.membership_tier)}>
              {getMembershipTierName(enterpriseData.membership_tier)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="订阅状态">
            <Tag color={enterpriseData.subscription_status === 'active' ? 'success' : 'default'}>
              {enterpriseData.subscription_status === 'active' ? '激活' : enterpriseData.subscription_status || '未激活'}
            </Tag>
            {enterpriseData.subscription_end_date && (
              <span style={{ marginLeft: 8, color: '#8c8c8c', fontSize: 12 }}>
                到期 {new Date(enterpriseData.subscription_end_date).toLocaleDateString()}
              </span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(enterpriseData.created_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
          <Descriptions.Item label="企业管理员">
            <div>
              <div><UserOutlined /> {enterpriseData.admin_user.username}</div>
              <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                {enterpriseData.admin_user.email}
              </div>
            </div>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 配额使用情况 */}
      <Card
        title={
          <Space>
            <TeamOutlined />
            <span>配额使用情况</span>
          </Space>
        }
        className="mb-4"
      >
        <Row gutter={16}>
          <Col span={12}>
            <Card>
              <Statistic
                title="员工配额"
                value={enterpriseData.members?.length || 0}
                suffix={`/ ${enterpriseData.max_employees || 0}`}
                prefix={<TeamOutlined />}
              />
              <Progress
                percent={employeeUsagePercentage}
                status={employeeUsagePercentage >= 90 ? 'exception' : 'normal'}
                className="mt-2"
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card>
              <Statistic
                title="工厂配额"
                value={0}
                suffix={`/ ${enterpriseData.max_factories}`}
                prefix={<HomeOutlined />}
              />
              <Progress
                percent={0}
                status="normal"
                className="mt-2"
              />
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 员工列表 */}
      <Card
        title={
          <Space>
            <TeamOutlined />
            <span>员工列表 ({enterpriseData.members?.length || 0})</span>
          </Space>
        }
      >
        <Table
          columns={employeeColumns}
          dataSource={enterpriseData.members || []}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 名员工`,
          }}
        />
      </Card>
    </div>
  );
};

export default EnterpriseDetail;