import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Button,
  Space,
  List,
  Avatar,
  Tag,
  Progress,
  Tabs,
  Badge,
  Divider,
} from 'antd'
import {
  TrophyOutlined,
  FileTextOutlined,
  TeamOutlined,
  BarChartOutlined,
  BellOutlined,
  CalendarOutlined,
  UserOutlined,
  ClockCircleOutlined,
  FireOutlined,
  ThunderboltOutlined,
  StarOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  ResponsiveContainer,
  ResponsiveGrid,
  ResponsiveCard,
  ResponsiveTable,
  useResponsive,
  useBreakpoint,
} from '@/components/Responsive'

const { Title, Text } = Typography

const MobileDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const { isMobile, isTablet, isDesktop } = useResponsive()
  const breakpoint = useBreakpoint()

  // 模拟数据
  const stats = {
    totalWPS: 156,
    approvedWPS: 128,
    totalPQR: 89,
    completedPQR: 76,
    totalInspections: 342,
    passedInspections: 315,
    activeProjects: 45,
    completedProjects: 38,
  }

  const recentActivities = [
    {
      id: '1',
      title: '创建了新的WPS文档',
      description: 'WPS-2024-015 管道对接焊工艺',
      time: '2小时前',
      type: 'create',
      icon: <FileTextOutlined style={{ color: '#1890ff' }} />,
    },
    {
      id: '2',
      title: 'PQR审核通过',
      description: 'PQR-2024-008 不锈钢容器焊接工艺评定',
      time: '4小时前',
      type: 'approve',
      icon: <TrophyOutlined style={{ color: '#52c41a' }} />,
    },
    {
      id: '3',
      title: '质量检验完成',
      description: '批次 #12345 检验合格',
      time: '1天前',
      type: 'quality',
      icon: <StarOutlined style={{ color: '#faad14' }} />,
    },
  ]

  const teamMembers = [
    {
      id: '1',
      name: '张三',
      avatar: '',
      role: '焊接工程师',
      status: 'active',
      performance: 92,
      projects: 12,
    },
    {
      id: '2',
      name: '李四',
      avatar: '',
      role: '质量检验员',
      status: 'active',
      performance: 88,
      projects: 8,
    },
    {
      id: '3',
      name: '王五',
      avatar: '',
      role: '生产主管',
      status: 'active',
      performance: 95,
      projects: 15,
    },
  ]

  const columns = [
    {
      title: '员工',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <Avatar src={record.avatar} icon={<UserOutlined />} />
          <div>
            <div className="font-medium">{text}</div>
            <div className="text-xs text-gray-500">{record.role}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '绩效',
      dataIndex: 'performance',
      key: 'performance',
      render: (score: number) => (
        <div>
          <div className="flex items-center">
            <Text strong>{score}</Text>
            <Text className="ml-1">/100</Text>
          </div>
          <Progress percent={score} size="small" showInfo={false} />
        </div>
      ),
    },
    {
      title: '项目数',
      dataIndex: 'projects',
      key: 'projects',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge
          status={status === 'active' ? 'success' : 'default'}
          text={status === 'active' ? '在职' : '离职'}
        />
      ),
    },
  ]

  // 渲染统计卡片
  const renderStatCards = () => {
    const statItems = [
      {
        title: 'WPS文档',
        value: stats.totalWPS,
        prefix: <FileTextOutlined />,
        color: '#1890ff',
        extra: (
          <div className="text-xs">
            已批准: {stats.approvedWPS}
            <Progress
              percent={Math.round((stats.approvedWPS / stats.totalWPS) * 100)}
              size="small"
              showInfo={false}
            />
          </div>
        ),
      },
      {
        title: 'PQR记录',
        value: stats.totalPQR,
        prefix: <TrophyOutlined />,
        color: '#52c41a',
        extra: (
          <div className="text-xs">
            已完成: {stats.completedPQR}
            <Progress
              percent={Math.round((stats.completedPQR / stats.totalPQR) * 100)}
              size="small"
              showInfo={false}
            />
          </div>
        ),
      },
      {
        title: '质量检验',
        value: stats.totalInspections,
        prefix: <StarOutlined />,
        color: '#faad14',
        extra: (
          <div className="text-xs">
            通过率: {Math.round((stats.passedInspections / stats.totalInspections) * 100)}%
            <Progress
              percent={Math.round((stats.passedInspections / stats.totalInspections) * 100)}
              size="small"
              showInfo={false}
            />
          </div>
        ),
      },
      {
        title: '项目进度',
        value: stats.activeProjects,
        prefix: <BarChartOutlined />,
        color: '#722ed1',
        extra: (
          <div className="text-xs">
            已完成: {stats.completedProjects}
            <Progress
              percent={Math.round((stats.completedProjects / stats.activeProjects) * 100)}
              size="small"
              showInfo={false}
            />
          </div>
        ),
      },
    ]

    if (isMobile) {
      return (
        <ResponsiveGrid cols={{ xs: 1, sm: 2 }}>
          {statItems.map((item, index) => (
            <ResponsiveCard key={index} className="stat-card">
              <div className="text-center">
                <div style={{ fontSize: 32, color: item.color, marginBottom: 8 }}>
                  {item.prefix}
                </div>
                <Statistic
                  title={item.title}
                  value={item.value}
                  valueStyle={{ color: item.color, fontSize: 24 }}
                />
                {item.extra}
              </div>
            </ResponsiveCard>
          ))}
        </ResponsiveGrid>
      )
    }

    return (
      <Row gutter={[16, 16]}>
        {statItems.map((item, index) => (
          <Col xs={24} sm={12} md={6} key={index}>
            <Card className="stat-card">
              <Statistic
                title={item.title}
                value={item.value}
                prefix={<div style={{ color: item.color }}>{item.prefix}</div>}
                valueStyle={{ color: item.color }}
              />
              {item.extra}
            </Card>
          </Col>
        ))}
      </Row>
    )
  }

  // 渲染概览页面
  const renderOverview = () => (
    <div>
      {renderStatCards()}

      <ResponsiveGrid cols={{ xs: 1, lg: 2 }} gutter={[16, 16]} className="mt-6">
        <ResponsiveCard
          title="最近活动"
          extra={<Button type="link" size="small">查看全部</Button>}
          collapsible={isMobile}
        >
          <List
            dataSource={recentActivities}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={item.icon}
                  title={item.title}
                  description={
                    <div>
                      <div className="text-sm text-gray-600">{item.description}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        <ClockCircleOutlined className="mr-1" />
                        {item.time}
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </ResponsiveCard>

        <ResponsiveCard
          title="团队成员"
          extra={<Button type="link" size="small">查看全部</Button>}
          collapsible={isMobile}
        >
          <List
            dataSource={teamMembers}
            renderItem={(member) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar src={member.avatar} icon={<UserOutlined />} />}
                  title={member.name}
                  description={
                    <div>
                      <Tag color="blue" size="small">{member.role}</Tag>
                      <div className="mt-2">
                        <div className="flex justify-between text-xs mb-1">
                          <span>绩效</span>
                          <span>{member.performance}/100</span>
                        </div>
                        <Progress
                          percent={member.performance}
                          size="small"
                          showInfo={false}
                        />
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </ResponsiveCard>
      </ResponsiveGrid>
    </div>
  )

  // 渲染团队页面
  const renderTeam = () => (
    <div>
      <ResponsiveCard title="团队成员绩效" className="mb-6">
        <ResponsiveTable
          columns={columns}
          dataSource={teamMembers}
          pagination={false}
        />
      </ResponsiveCard>

      {!isMobile && (
        <ResponsiveGrid cols={{ xs: 1, lg: 3 }}>
          {teamMembers.map((member) => (
            <ResponsiveCard key={member.id}>
              <div className="text-center">
                <Avatar size={64} src={member.avatar} icon={<UserOutlined />} />
                <Title level={5} className="mt-3 mb-1">
                  {member.name}
                </Title>
                <Tag color="blue">{member.role}</Tag>
                <Divider />
                <Statistic
                  title="绩效评分"
                  value={member.performance}
                  suffix="/100"
                  valueStyle={{ color: member.performance >= 90 ? '#52c41a' : '#1890ff' }}
                />
                <Statistic
                  title="参与项目"
                  value={member.projects}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </div>
            </ResponsiveCard>
          ))}
        </ResponsiveGrid>
      )}
    </div>
  )

  // 渲染移动端侧边栏
  const renderMobileSidebar = () => (
    <div className="mobile-sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <FireOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          <span style={{ marginLeft: 8, fontSize: 16, fontWeight: 'bold', color: '#fff' }}>
            WeldSystem
          </span>
        </div>
      </div>
      <div className="sidebar-menu">
        <div className="menu-item active">
          <BarChartOutlined />
          <span>仪表盘</span>
        </div>
        <div className="menu-item">
          <FileTextOutlined />
          <span>WPS管理</span>
        </div>
        <div className="menu-item">
          <TrophyOutlined />
          <span>PQR管理</span>
        </div>
        <div className="menu-item">
          <TeamOutlined />
          <span>团队成员</span>
        </div>
      </div>
    </div>
  )

  // 渲染顶部导航
  const renderHeader = () => (
    <div className="mobile-header">
      <div className="flex items-center">
        {isMobile && (
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 'bold' }}>
              移动仪表盘
            </h1>
        )}
        {!isMobile && (
          <Title level={3} style={{ margin: 0 }}>
            移动优化仪表盘
          </Title>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Badge count={5}>
          <Button type="text" icon={<BellOutlined />} />
        </Badge>
        <Avatar icon={<UserOutlined />} />
      </div>
    </div>
  )

  return (
    <ResponsiveContainer
      sidebar={isMobile ? renderMobileSidebar() : undefined}
      header={renderHeader()}
    >
      <div className="dashboard-content">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          centered={isMobile}
          size={isMobile ? 'small' : 'default'}
          items={[
            {
              key: 'overview',
              label: '概览',
              children: renderOverview(),
            },
            {
              key: 'team',
              label: '团队',
              children: renderTeam(),
            },
          ]}
        />
      </div>

      {/* 设备信息调试 */}
      {process.env.NODE_ENV === 'development' && (
        <div className="device-info" style={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '12px',
          zIndex: 9999,
        }}>
          <div>设备: {isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'}</div>
          <div>断点: {breakpoint}</div>
          <div>窗口: {window.innerWidth}x{window.innerHeight}</div>
        </div>
      )}
    </ResponsiveContainer>
  )
}

export default MobileDashboard