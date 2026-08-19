import React, { useState, useEffect } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Layout as AntLayout,
  Menu,
  Avatar,
  Dropdown,
  Badge,
  Button,
  Space,
  Typography,
  Drawer,
  Input,
  theme,
  message,
} from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  SettingOutlined,
  TeamOutlined,
  BarChartOutlined,
  UserOutlined,
  EditOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  CrownOutlined,
  DatabaseOutlined,
  ToolOutlined,
  SafetyCertificateOutlined,
  PartitionOutlined,
  FileSearchOutlined,
  ShopOutlined,
  WalletOutlined,
  HistoryOutlined,
  NotificationOutlined,
  SecurityScanOutlined,
  SearchOutlined,
  GlobalOutlined,
  QuestionCircleOutlined,
  FullscreenOutlined,
  StarOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  GiftOutlined,
  SafetyOutlined,
  SwitcherOutlined,
  ShareAltOutlined,
  CloudOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import { workspaceService, Workspace } from '@/services/workspace'
import WorkspaceSwitcher from '@/components/WorkspaceSwitcher'
import NotificationCenter from '@/components/NotificationCenter'
import Footer from '@/components/Footer'

const { Header, Sider, Content } = AntLayout
const { Text } = Typography

interface LayoutProps {
  children?: React.ReactNode
}

const Layout: React.FC<LayoutProps> = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [membershipInfo, setMembershipInfo] = useState<any>(null)
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const { user, logout, checkPermission, hasAnyPermission, refreshUserInfo } = useAuthStore()

  // 判断是否为游客模式
  const isGuestMode = !user

  // 判断是否为企业用户
  const isEnterpriseUser = () => {
    const userTier = user?.membership_tier || user?.member_tier || 'free'
    return ['enterprise', 'enterprise_pro', 'enterprise_pro_max'].includes(userTier)
  }

  // 刷新用户信息和会员信息
  useEffect(() => {
    const refreshData = async () => {
      if (!user || isGuestMode) return

      try {
        // 保存当前的会员等级
        const oldTier = user?.member_tier || user?.membership_tier || 'free'

        // 刷新用户信息以获取最新的会员等级
        // 这样可以确保在支付升级后,前端能获取到最新的会员信息
        const refreshed = await refreshUserInfo()

        if (refreshed) {
          // 获取刷新后的用户信息
          const { user: newUser } = useAuthStore.getState()
          const newTier = newUser?.member_tier || newUser?.membership_tier || 'free'

          // 如果会员等级发生变化,刷新页面以更新菜单
          if (oldTier !== newTier) {
            console.log(`[Layout] 检测到会员等级变化: ${oldTier} -> ${newTier}, 刷新页面...`)
            message.success(`会员等级已更新, 页面即将刷新...`)
            setTimeout(() => {
              window.location.reload()
            }, 1500)
            return
          }
        }

        // 获取会员信息
        const { membershipService } = await import('@/services/membership')
        const info = await membershipService.getUserMembershipInfo()
        setMembershipInfo(info)
      } catch (error) {
        console.error('Failed to refresh user data:', error)
      }
    }

    refreshData()

    // 每30秒检查一次会员等级是否变化
    const interval = setInterval(refreshData, 30000)

    return () => clearInterval(interval)
  }, [isGuestMode]) // 只在组件挂载时执行一次

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      if (mobile) {
        setCollapsed(true)
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // 加载当前工作区信息
  useEffect(() => {
    if (user && !isGuestMode) {
      const loadCurrentWorkspace = async () => {
        try {
          // 优先使用本地存储，避免覆盖用户手动切换的工作区
          const storedWorkspace = workspaceService.getCurrentWorkspaceFromStorage()

          if (storedWorkspace) {
            setCurrentWorkspace(storedWorkspace)
            // 不再从服务器获取，避免覆盖用户选择的工作区
            return
          }

          // 只有本地存储不存在时才从服务器获取
          const response = await workspaceService.getCurrentWorkspace()
          if (response && response.data) {
            setCurrentWorkspace(response.data)
            workspaceService.saveCurrentWorkspaceToStorage(response.data)
          }
        } catch (error) {
          console.error('Layout 加载工作区失败:', error)
          // 如果服务器获取失败，尝试获取默认工作区
          try {
            const response = await workspaceService.getDefaultWorkspace()
            if (response && response.data) {
              setCurrentWorkspace(response.data)
              workspaceService.saveCurrentWorkspaceToStorage(response.data)
            }
          } catch (defaultError) {
            console.error('Layout 获取默认工作区失败:', defaultError)
          }
        }
      }

      loadCurrentWorkspace()
    }
  }, [user, isGuestMode])

  // 在用户登录后，定期刷新用户信息以更新权限
  useEffect(() => {
    if (user && !isGuestMode) {
      // 页面获得焦点时刷新用户信息
      const handleVisibilityChange = () => {
        if (!document.hidden) {
          refreshUserInfo()
        }
      }

      // 页面获得焦点时刷新用户信息
      const handleFocus = () => {
        refreshUserInfo()
      }

      // 定期刷新用户信息（每5分钟）
      const intervalId = setInterval(() => {
        refreshUserInfo()
      }, 5 * 60 * 1000) // 5分钟

      document.addEventListener('visibilitychange', handleVisibilityChange)
      window.addEventListener('focus', handleFocus)

      return () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange)
        window.removeEventListener('focus', handleFocus)
        clearInterval(intervalId)
      }
    }
  }, [user, isGuestMode, refreshUserInfo])

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: 'resource-library-group',
      icon: <DatabaseOutlined />,
      label: '资源库',
      children: [
        {
          key: '/modules',
          label: '模块管理',
        },
        {
          key: '/templates',
          label: '模板管理',
        },
        {
          key: '/shared-library',
          label: '共享库',
        },
      ],
      hidden: false, // 所有用户都可以访问资源库
    },
    {
      key: 'wps-group',
      icon: <FileTextOutlined />,
      label: 'WPS管理',
      children: [
        {
          key: '/wps',
          label: 'WPS列表',
        },
        ...(isGuestMode || checkPermission('wps.create')
          ? [
              {
                key: '/wps/create',
                label: '创建WPS',
              },
            ]
          : []),
      ],
      hidden: isGuestMode ? false : !checkPermission('wps.read'),
    },
    {
      key: 'pqr-group',
      icon: <ExperimentOutlined />,
      label: 'PQR管理',
      children: [
        {
          key: '/pqr',
          label: 'PQR列表',
        },
        ...(isGuestMode || checkPermission('pqr.create')
          ? [
              {
                key: '/pqr/create',
                label: '创建PQR',
              },
            ]
          : []),
      ],
      hidden: isGuestMode ? false : !checkPermission('pqr.read'),
    },
    {
      key: 'ppqr-group',
      icon: <SettingOutlined />,
      label: 'pPQR管理',
      children: [
        {
          key: '/ppqr',
          label: 'pPQR列表',
        },
        ...(checkPermission('ppqr.create')
          ? [
              {
                key: '/ppqr/create',
                label: '创建pPQR',
              },
            ]
          : []),
      ],
      hidden: isGuestMode ? true : !checkPermission('ppqr.read'),
    },
    {
      key: 'materials-group',
      icon: <DatabaseOutlined />,
      label: '焊材管理',
      children: [
        {
          key: '/materials',
          label: '焊材列表',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('materials.read'),
    },
    {
      key: 'welders-group',
      icon: <TeamOutlined />,
      label: '焊工管理',
      children: [
        {
          key: '/welders',
          label: '焊工列表',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('welders.read'),
    },
    {
      key: 'equipment-group',
      icon: <ToolOutlined />,
      label: '设备管理',
      children: [
        {
          key: '/equipment',
          label: '设备列表',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('equipment.read'),
    },
    {
      key: 'production-group',
      icon: <SafetyCertificateOutlined />,
      label: '生产管理',
      children: [
        {
          key: '/production',
          label: '生产任务',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('production.read'),
    },
    {
      key: 'quality-group',
      icon: <PartitionOutlined />,
      label: '质量管理',
      children: [
        {
          key: '/quality',
          label: '质量检验',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('quality.read'),
    },
    {
      key: 'reports-group',
      icon: <BarChartOutlined />,
      label: '报表统计',
      children: [
        {
          key: '/reports',
          label: '报表概览',
        },
        {
          key: '/reports/wps',
          label: 'WPS统计',
        },
        {
          key: '/reports/pqr',
          label: 'PQR统计',
        },
        {
          key: '/reports/usage',
          label: '使用统计',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('reports.read'),
    },
    {
      key: 'enterprise-group',
      icon: <ShopOutlined />,
      label: '企业管理',
      children: [
        {
          key: '/enterprise/employees',
          label: '员工管理',
          hidden: !checkPermission('enterprise.employees'),
        },
        {
          key: '/enterprise/factories',
          label: '工厂管理',
          hidden: !checkPermission('enterprise.factories'),
        },
        {
          key: '/enterprise/departments',
          label: '部门管理',
          hidden: !checkPermission('enterprise.departments'),
        },
        {
          key: '/enterprise/roles',
          label: '角色设置',
          hidden: !checkPermission('enterprise.roles'),
        },
        {
          key: '/enterprise/approval-workflows',
          label: '审批流程',
          hidden: !checkPermission('enterprise.roles'),
        },
        {
          key: '/enterprise/invitations',
          label: '邀请管理',
          hidden: !checkPermission('enterprise.invitations'),
        },
      ].filter(item => !item.hidden),
      hidden: isGuestMode ? true : !isEnterpriseUser() || ![
        'enterprise.employees',
        'enterprise.factories',
        'enterprise.departments',
        'enterprise.roles',
        'enterprise.invitations',
      ].some(perm => checkPermission(perm)),
    },

    {
      key: 'employees-group',
      icon: <TeamOutlined />,
      label: '员工管理',
      children: [
        {
          key: '/employees',
          label: '员工列表',
        },
      ],
      hidden: isGuestMode ? true : (!checkPermission('employees.read') || isEnterpriseUser()),
    },
    {
      key: 'membership-group',
      icon: <CrownOutlined />,
      label: '会员中心',
      children: [
        {
          key: '/membership',
          label: isGuestMode ? '套餐介绍' : '当前套餐',
        },
        ...(isGuestMode ? [] : [
          {
            key: '/membership/upgrade',
            label: '升级套餐',
          },
          {
            key: '/membership/history',
            label: '订阅历史',
          },
        ]),
      ],
    },
    {
      key: 'profile-group',
      icon: <UserOutlined />,
      label: isGuestMode ? '账户相关' : '我的',
      children: isGuestMode ? [
        {
          key: '/login',
          label: '登录账户',
        },
        {
          key: '/register',
          label: '注册账户',
        },
      ] : [
        {
          key: '/profile',
          label: '个人中心',
        },
        {
          key: '/profile/settings',
          label: '系统设置',
        },
        {
          key: '/profile/security',
          label: '安全设置',
        },
        {
          key: '/profile/notifications',
          label: '通知设置',
        },
      ],
    },
  ].filter(item => !item.hidden)

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
    if (isMobile) {
      setMobileDrawerVisible(false)
    }
  }

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    const pathname = location.pathname
    return [pathname]
  }

  // 获取当前展开的子菜单
  const getOpenKeys = () => {
    const pathname = location.pathname
    const openKeys: string[] = []

    menuItems.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => 
          pathname === child.key || pathname.startsWith(child.key + '/')
        )
        if (hasActiveChild) {
          openKeys.push(item.key)
        }
      }
    })

    return openKeys
  }

  // 用户下拉菜单
  const userMenuItems = isGuestMode ? [
    {
      key: 'login',
      icon: <UserOutlined />,
      label: '登录账户',
      onClick: () => navigate('/login'),
    },
    {
      key: 'register',
      icon: <CrownOutlined />,
      label: '注册账户',
      onClick: () => navigate('/register'),
    },
  ] : [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
      {
      key: 'membership',
      icon: <CrownOutlined />,
      label: '会员中心',
      onClick: () => navigate('/membership'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      onClick: () => navigate('/profile/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ]

  // 通知下拉菜单
  const notificationMenuItems = [
    {
      key: 'notifications',
      icon: <NotificationOutlined />,
      label: '查看所有通知',
      onClick: () => navigate('/profile/notifications'),
    },
  ]

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
      // 兼容旧的等级名称
      free: '个人免费版',
    }
    return tierNames[tier] || '未知'
  }

  // 获取会员等级颜色
  const getMembershipTierColor = (tier: string) => {
    const tierColors: Record<string, string> = {
      personal_free: '#8c8c8c',
      personal_pro: '#1890ff',
      personal_advanced: '#52c41a',
      personal_flagship: '#722ed1',
      enterprise: '#fa8c16',
      enterprise_pro: '#eb2f96',
      enterprise_pro_max: '#f5222d',
      // 兼容旧的等级名称
      free: '#8c8c8c',
    }
    return tierColors[tier] || '#8c8c8c'
  }

  // 获取会员等级图标
  const getPlanIcon = (tier: string) => {
    switch (tier) {
      case 'personal_free':
      case 'free':
        return <UserOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'personal_pro':
        return <StarOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'personal_advanced':
        return <ThunderboltOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'personal_flagship':
        return <CrownOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'enterprise':
        return <RocketOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'enterprise_pro':
        return <SafetyOutlined style={{ color: getMembershipTierColor(tier) }} />
      case 'enterprise_pro_max':
        return <GiftOutlined style={{ color: getMembershipTierColor(tier) }} />
      default:
        return <UserOutlined style={{ color: '#8c8c8c' }} />
    }
  }

  const sidebarContent = (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={getSelectedKeys()}
      defaultOpenKeys={getOpenKeys()}
      items={menuItems}
      onClick={handleMenuClick}
    />
  )

  return (
    <AntLayout className="h-full">
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          className="shadow-lg"
          width={256}
          collapsedWidth={80}
        >
          <div className="sidebar-header">
            {collapsed ? (
              <div className="sidebar-logo-collapsed">
                <span className="logo-text">焊序</span>
              </div>
            ) : (
              <div className="sidebar-logo-expanded">
                <div className="logo-icon">
                  <SafetyCertificateOutlined />
                </div>
                <div className="logo-text-wrapper">
                  <span className="logo-title">焊序</span>
                  <span className="logo-subtitle">Hanxu</span>
                </div>
              </div>
            )}
          </div>
          {sidebarContent}
        </Sider>
      )}

      {/* 移动端抽屉 */}
      {isMobile && (
        <Drawer
          title="焊序"
          placement="left"
          onClose={() => setMobileDrawerVisible(false)}
          open={mobileDrawerVisible}
          styles={{ body: { padding: 0 } }}
          width={256}
        >
          {sidebarContent}
        </Drawer>
      )}

      <AntLayout>
        <Header className="modern-header">
          <div className="header-left">
            {/* 菜单切换按钮 */}
            <div className="menu-toggle">
              {isMobile ? (
                <Button
                  type="text"
                  icon={<MenuUnfoldOutlined />}
                  onClick={() => setMobileDrawerVisible(true)}
                  className="header-btn"
                />
              ) : (
                <Button
                  type="text"
                  icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                  onClick={() => setCollapsed(!collapsed)}
                  className="header-btn"
                />
              )}
            </div>

            {/* 全局搜索栏 */}
            {!isMobile && (
              <div className="global-search">
                <Input
                  placeholder="搜索WPS、PQR、焊工..."
                  prefix={<SearchOutlined />}
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  onPressEnter={(e) => {
                    if (searchValue.trim()) {
                      // 这里可以实现搜索逻辑
                    }
                  }}
                  className="search-input"
                />
              </div>
            )}
          </div>

          <div className="header-right" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {/* 快捷操作按钮组 */}
            <div className="header-actions" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
              marginRight: '8px'
            }}>
              <Button
                type="text"
                icon={<QuestionCircleOutlined />}
                className="header-btn"
                title="帮助中心"
                style={{ width: '32px', height: '32px' }}
              />
              <Button
                type="text"
                icon={<GlobalOutlined />}
                className="header-btn"
                title="切换语言"
                style={{ width: '32px', height: '32px' }}
              />
              <Button
                type="text"
                icon={<FullscreenOutlined />}
                className="header-btn"
                title="全屏"
                onClick={() => {
                  if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen()
                  } else {
                    document.exitFullscreen()
                  }
                }}
                style={{ width: '32px', height: '32px' }}
              />
            </div>

            {/* 会员状态 - 企业版PRO */}
            <div className="membership-status" style={{
              flexShrink: 0,
              marginRight: '4px'
            }}>
              <div
                className="membership-badge"
                onClick={() => navigate('/membership/current')}
                style={{ cursor: 'pointer' }}
                title={membershipInfo?.is_inherited_from_company ? `继承自企业「${membershipInfo.company_name}」` : '点击查看会员详情'}
              >
                {(() => {
                  const tier = (user as any)?.member_tier || user?.membership_tier || 'free'
                  const icon = getPlanIcon(tier)
                  return icon
                })()}
                <span className="membership-text">
                  {isGuestMode ? '游客模式' : getMembershipTierName((user as any)?.member_tier || user?.membership_tier || 'free')}
                  {membershipInfo?.is_inherited_from_company && (
                    <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.8 }}>
                      (企业)
                    </span>
                  )}
                </span>
              </div>
            </div>

            {/* 工作区切换器 - 显示当前工作区 */}
            {!isMobile && (
              <div style={{
                width: 'auto',
                minWidth: '180px',
                maxWidth: '220px',
                flexShrink: 0,
                marginRight: '8px',
                overflow: 'hidden'
              }}>
                <WorkspaceSwitcher
                  compact={false}
                />
              </div>
            )}

            {/* 通知中心 */}
            {!isGuestMode && (
              <div className="notification-center" style={{
                flexShrink: 0,
                marginRight: '4px'
              }}>
                <NotificationCenter />
              </div>
            )}

            {/* 用户信息 */}
            <div className="user-profile" style={{
              flexShrink: 0,
              width: 'auto',
              minWidth: '120px',
              maxWidth: '180px'
            }}>
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
                trigger={['click']}
              >
                <div className="user-info" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <Avatar
                    size={28}
                    src={user?.avatar_url}
                    icon={<UserOutlined />}
                    className="user-avatar"
                  />
                  {!isMobile && (
                    <div className="user-details" style={{
                      minWidth: 0,
                      flex: 1,
                      overflow: 'hidden'
                    }}>
                      <div className="user-name" style={{
                        fontSize: '13px',
                        fontWeight: 500,
                        color: '#1e293b',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {isGuestMode ? '访客用户' : (user?.full_name || user?.username)}
                      </div>
                      {isGuestMode && (
                        <div className="user-role" style={{
                          fontSize: '11px',
                          color: '#64748b',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}>
                          游客模式
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </Dropdown>
            </div>
          </div>
        </Header>

        <Content
          className="main-content"
          style={{
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            margin: '24px',
            padding: '24px',
            minHeight: 'calc(100vh - 200px)',
          }}
        >
          <Outlet />
        </Content>

        {/* Footer */}
        <Footer />
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
