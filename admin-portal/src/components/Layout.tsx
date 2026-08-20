import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Avatar, Dropdown, Badge, Button, Space } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  CreditCardOutlined,
  DollarOutlined,
  MonitorOutlined,
  BarChartOutlined,
  NotificationOutlined,
  SettingOutlined,
  SafetyOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ShareAltOutlined,
  TagsOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthContext } from '@/contexts/AuthContext';

const { Header, Sider, Content } = AntLayout;

const Layout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthContext();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/enterprises',
      icon: <TeamOutlined />,
      label: '企业管理',
    },
    {
      key: '/subscriptions',
      icon: <CreditCardOutlined />,
      label: '订阅管理',
    },
    {
      key: '/pricing',
      icon: <TagsOutlined />,
      label: '价格管理',
    },
    {
      key: '/payments',
      icon: <DollarOutlined />,
      label: '支付订单',
    },
    {
      key: '/system',
      icon: <MonitorOutlined />,
      label: '系统监控',
    },
    {
      key: '/statistics',
      icon: <BarChartOutlined />,
      label: '数据统计',
    },
    {
      key: '/announcements',
      icon: <NotificationOutlined />,
      label: '公告管理',
    },
    {
      key: '/shared-library',
      icon: <ShareAltOutlined />,
      label: '共享库管理',
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: '系统配置',
    },
    {
      key: '/security',
      icon: <SafetyOutlined />,
      label: '安全管理',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = async () => {
    await logout();
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <AntLayout className="admin-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '16px',
            borderRadius: '6px',
            color: '#1F5EFF',
            fontSize: collapsed ? '14px' : '18px',
            fontWeight: 700,
            letterSpacing: '0.08em',
          }}
        >
          {collapsed ? '焊序' : '焊序 · 管理端'}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <AntLayout
        style={{
          marginLeft: collapsed ? 80 : 200,
          transition: 'margin-left 0.2s',
          minWidth: 0,
          overflow: 'hidden',
        }}
      >
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />

          <Space size="middle">
            <Badge count={5} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                style={{ fontSize: '16px' }}
                onClick={() => navigate('/notifications')}
              />
            </Badge>

            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.full_name || user?.username}</span>
                <span
                  style={{
                    padding: '2px 8px',
                    background: '#f0f0f0',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#666',
                  }}
                >
                  {user?.admin_level === 'super_admin' ? '超级管理员' : '管理员'}
                </span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content className="admin-content">
          {children || <Outlet />}
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;