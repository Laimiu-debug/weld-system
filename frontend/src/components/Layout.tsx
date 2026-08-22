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
import { usePreferencesStore } from '@/store/preferencesStore'
import { workspaceService, Workspace } from '@/services/workspace'
import WorkspaceSwitcher from '@/components/WorkspaceSwitcher'
import NotificationCenter from '@/components/NotificationCenter'
import Footer from '@/components/Footer'
import { useBranding } from '@/hooks/useBranding'
import GlobalSearch from '@/components/GlobalSearch'
import BrandMark from '@/components/Brand/BrandMark'
import ProductIcon from '@/components/icons/ProductIcon'

const { Header, Sider, Content } = AntLayout
const { Text } = Typography

/** 统一会员等级别名，避免 free/personal_free 被当成等级变更。 */
function normalizeMembershipTier(tier?: string | null): string {
  const value = (tier || 'personal_free').trim().toLowerCase()
  if (value === 'free' || value === 'personal' || value === 'basic') {
    return 'personal_free'
  }
  return value
}

interface LayoutProps {
  children?: React.ReactNode
}

const Layout: React.FC<LayoutProps> = () => {
  const branding = useBranding()
  const sidebarCollapsedPref = usePreferencesStore((s) => s.preferences.sidebarCollapsed)
  const [collapsed, setCollapsed] = useState(sidebarCollapsedPref)
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [membershipInfo, setMembershipInfo] = useState<any>(null)
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null)
  const location = useLocation()
  const navigate = useNavigate()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const { user, logout, checkPermission, hasAnyPermission, refreshUserInfo } = useAuthStore()

  useEffect(() => {
    setCollapsed(sidebarCollapsedPref)
  }, [sidebarCollapsedPref])

  // 判断是否为游客模式
  const isGuestMode = !user

  // 判断是否为企业用户
  const isEnterpriseUser = () => {
    const userTier = normalizeMembershipTier(user?.membership_tier || user?.member_tier)
    return ['enterprise', 'enterprise_pro', 'enterprise_pro_max'].includes(userTier)
  }

  // 刷新用户信息和会员信息（不整页 reload，避免 free/personal_free 别名误触发循环刷新）
  useEffect(() => {
    if (isGuestMode) return

    const refreshData = async () => {
      const { user: latestUser } = useAuthStore.getState()
      if (!latestUser) return

      try {
        const oldTier = normalizeMembershipTier(
          latestUser.member_tier || latestUser.membership_tier
        )

        const refreshed = await refreshUserInfo()
        if (refreshed) {
          const { user: newUser } = useAuthStore.getState()
          const newTier = normalizeMembershipTier(
            newUser?.member_tier || newUser?.membership_tier
          )
          if (oldTier !== newTier) {
            console.log(`[Layout] 会员等级变化: ${oldTier} -> ${newTier}`)
            message.success('会员等级已更新')
          }
        }

        const { membershipService } = await import('@/services/membership')
        const info = await membershipService.getUserMembershipInfo()
        setMembershipInfo(info)
      } catch (error) {
        console.error('Failed to refresh user data:', error)
      }
    }

    refreshData()
    const interval = setInterval(refreshData, 30000)
    return () => clearInterval(interval)
  }, [isGuestMode, refreshUserInfo])

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
    if (user?.id && !isGuestMode) {
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
  }, [user?.id, isGuestMode])

  // 在用户登录后，定期刷新用户信息以更新权限
  useEffect(() => {
    if (user?.id && !isGuestMode) {
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
  }, [user?.id, isGuestMode, refreshUserInfo])

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <ProductIcon kind="dashboard" />,
      label: '仪表盘',
    },
    {
      key: 'resource-library-group',
      icon: <ProductIcon kind="library" />,
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
      icon: <ProductIcon kind="wps" />,
      label: 'WPS管理',
      children: [
        {
          key: '/wps',
          label: '全部WPS',
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
      icon: <ProductIcon kind="pqr" />,
      label: 'PQR管理',
      children: [
        {
          key: '/pqr',
          label: '全部PQR',
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
      icon: <ProductIcon kind="ppqr" />,
      label: 'pPQR管理',
      children: [
        {
          key: '/ppqr',
          label: '全部pPQR',
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
      key: '/materials',
      icon: <ProductIcon kind="materials" />,
      label: '焊材管理',
      hidden: isGuestMode ? true : !checkPermission('materials.read'),
    },
    {
      key: '/welders',
      icon: <ProductIcon kind="welder" />,
      label: '焊工管理',
      hidden: isGuestMode ? true : !checkPermission('welders.read'),
    },
    {
      key: '/equipment',
      icon: <ProductIcon kind="equipment" />,
      label: '设备管理',
      hidden: isGuestMode ? true : !checkPermission('equipment.read'),
    },
    {
      key: 'production-group',
      icon: <ProductIcon kind="production" />,
      label: '生产管理',
      hidden: isGuestMode ? true : !checkPermission('production.read'),
      children: [
        { key: '/production', label: '生产任务' },
        { key: '/production/plans', label: '生产计划' },
      ],
    },
    {
      key: 'quality-group',
      icon: <ProductIcon kind="quality" />,
      label: '质量管理',
      hidden: isGuestMode ? true : !checkPermission('quality.read'),
      children: [
        { key: '/quality', label: '质量检验' },
        { key: '/quality/standards', label: '质量标准' },
      ],
    },
    {
      key: 'reports-group',
      icon: <ProductIcon kind="reports" />,
      label: '报表统计',
      children: [
        {
          key: '/reports',
          label: '统计概览',
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
        {
          key: '/reports/custom',
          label: '自定义报表',
        },
      ],
      hidden: isGuestMode ? true : !checkPermission('reports.read'),
    },
    {
      key: 'enterprise-group',
      icon: <ProductIcon kind="enterprise" />,
      label: '企业管理',
      children: [
        {
          key: '/enterprise/employees',
          label: '员工管理',
          hidden: !checkPermission('enterprise.employees'),
        },
        {
          key: '/employees/performance',
          label: '员工绩效',
          hidden: !(checkPermission('employees.read') || checkPermission('enterprise.employees')),
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
      icon: <ProductIcon kind="welder" />,
      label: '员工中心',
      hidden: isGuestMode ? true : (!checkPermission('employees.read') || isEnterpriseUser()),
      children: [
        { key: '/employees', label: '员工管理' },
        { key: '/employees/performance', label: '员工绩效' },
      ],
    },
    {
      key: 'membership-group',
      icon: <ProductIcon kind="membership" />,
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
      icon: <ProductIcon kind="profile" />,
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
        {
          key: '/feedback',
          label: '意见反馈',
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

  // 获取当前选中的菜单项（详情/编辑页高亮对应列表入口）
  const getSelectedKeys = () => {
    const pathname = location.pathname
    const candidates = [
      '/wps',
      '/pqr',
      '/ppqr',
      '/materials',
      '/welders',
      '/equipment',
      '/production',
      '/quality',
      '/reports',
      '/employees',
      '/modules',
      '/templates',
      '/shared-library',
      '/membership',
      '/feedback',
      '/profile',
      '/enterprise',
    ]
    for (const base of candidates) {
      if (pathname === base || pathname.startsWith(`${base}/`)) {
        // 会员中心子页：精确高亮对应入口
        if (base === '/membership' && pathname !== base) {
          if (
            pathname.startsWith('/membership/upgrade') ||
            pathname.startsWith('/membership/payment') ||
            pathname.startsWith('/membership/result')
          ) {
            return ['/membership/upgrade']
          }
          if (pathname.startsWith('/membership/history')) {
            return ['/membership/history']
          }
          return [pathname]
        }
        // 我的 / 报表 / 计划 / 标准 / 绩效子路由保留精确选中
        if (
          (base === '/reports' ||
            base === '/production' ||
            base === '/quality' ||
            base === '/employees' ||
            base === '/profile') &&
          pathname !== base
        ) {
          return [pathname]
        }
        // 创建页保留精确选中
        if (
          pathname.endsWith('/create') ||
          pathname.includes('/create/')
        ) {
          return [pathname]
        }
        return [base]
      }
    }
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
                <BrandMark size={36} />
              </div>
            ) : (
              <div className="sidebar-logo-expanded">
                <div className="logo-icon">
                  <BrandMark size={40} />
                </div>
                <div className="logo-text-wrapper">
                  <span className="logo-title">{branding.brand_name}</span>
                  <span className="logo-subtitle" title={branding.display_subtitle}>
                    {branding.display_subtitle}
                  </span>
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
          title={
            branding.org_name
              ? `${branding.brand_name} · ${branding.org_name}`
              : branding.brand_name
          }
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
            {!isMobile && <GlobalSearch />}
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
            minWidth: 0,
            overflowX: 'hidden',
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
