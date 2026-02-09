import React, { useState, useEffect } from 'react'
import { Dropdown, Button, Avatar, Space, message, Badge } from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  SwitcherOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { workspaceService, Workspace } from '@/services/workspace'
import { useAuthStore } from '@/store/authStore'
import { triggerWorkspaceSwitch } from '@/contexts/MembershipContext'

interface WorkspaceSwitcherProps {
  compact?: boolean
  className?: string
}

// 扩展Workspace接口以包含合并的角色信息
interface ExtendedWorkspace extends Workspace {
  all_roles?: string[]
  all_departments?: string[]
  all_membership_tiers?: string[]
}

const WorkspaceSwitcher: React.FC<WorkspaceSwitcherProps> = ({
  compact = false,
  className = ''
}) => {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [workspaces, setWorkspaces] = useState<ExtendedWorkspace[]>([])
  const [currentWorkspace, setCurrentWorkspace] = useState<ExtendedWorkspace | null>(null)

  // 加载工作区数据
  useEffect(() => {
    if (user) {
      loadWorkspaces()
    }
  }, [user])

  const loadWorkspaces = async () => {
    setLoading(true)
    try {
      // 获取工作区列表 - 后端直接返回数组
      const workspacesResponse = await workspaceService.getUserWorkspaces()

      // 处理直接数组格式
      let workspaceData: Workspace[] = []
      if (Array.isArray(workspacesResponse)) {
        workspaceData = workspacesResponse
      } else if (workspacesResponse?.success && workspacesResponse?.data) {
        // 兼容ApiResponse格式
        workspaceData = Array.isArray(workspacesResponse.data) ? workspacesResponse.data : [workspacesResponse.data]
      } else {
        console.warn('工作区响应格式异常:', workspacesResponse)
      }

      // 去重处理：基于工作区ID合并相同的工作区，收集所有角色信息
      const workspaceMap = new Map<string, {
        workspace: Workspace,
        roles: string[],
        departments: string[],
        membership_tiers: string[]
      }>()

      workspaceData.forEach(workspace => {
        const existing = workspaceMap.get(workspace.id)

        if (!existing) {
          // 如果工作区不存在，创建新条目
          const roles = workspace.role ? [workspace.role] : []
          const departments = workspace.department ? [workspace.department] : []
          const membership_tiers = workspace.membership_tier ? [workspace.membership_tier] : []

          workspaceMap.set(workspace.id, {
            workspace,
            roles,
            departments,
            membership_tiers
          })
        } else {
          // 如果工作区已存在，添加角色和部门信息
          if (workspace.role && !existing.roles.includes(workspace.role)) {
            existing.roles.push(workspace.role)
          }
          if (workspace.department && !existing.departments.includes(workspace.department)) {
            existing.departments.push(workspace.department)
          }
          if (workspace.membership_tier && !existing.membership_tiers.includes(workspace.membership_tier)) {
            existing.membership_tiers.push(workspace.membership_tier)
          }

          // 合并其他信息
          existing.workspace = {
            ...existing.workspace,
            factory_name: workspace.factory_name || existing.workspace.factory_name,
          }
        }
      })

      // 转换为Workspace数组，并添加合并的角色信息
      const uniqueWorkspaces = Array.from(workspaceMap.values()).map(({
        workspace,
        roles,
        departments,
        membership_tiers
      }) => ({
        ...workspace,
        // 将合并的角色信息作为额外属性
        all_roles: roles,
        all_departments: departments,
        all_membership_tiers: membership_tiers
      }))

      // console.log('合并后的工作区（包含所有角色）:', uniqueWorkspaces) // 调试用

      setWorkspaces(uniqueWorkspaces)

      // 优先使用本地存储的当前工作区
      const storedWorkspace = workspaceService.getCurrentWorkspaceFromStorage()

      if (storedWorkspace) {
        // 验证存储的工作区是否在当前工作区列表中
        const isValidWorkspace = workspaceData.some(w => w.id === storedWorkspace.id)

        if (isValidWorkspace) {
          setCurrentWorkspace(storedWorkspace)
          // 不再从服务器获取，避免覆盖本地存储的正确工作区
        } else {
          // 存储的工作区无效，清除并重新获取
          workspaceService.clearCurrentWorkspaceStorage()
          await fetchCurrentWorkspaceFromServer(workspaceData)
        }
      } else {
        // 没有本地存储，从服务器获取
        await fetchCurrentWorkspaceFromServer(workspaceData)
      }
    } catch (error) {
      console.error('加载工作区失败:', error)
      message.error('加载工作区失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }

  // 从服务器获取当前工作区（仅在本地存储无效时调用）
  const fetchCurrentWorkspaceFromServer = async (workspaceData: Workspace[]) => {
    try {
      const currentResponse = await workspaceService.getCurrentWorkspace()

      let newWorkspace: Workspace | null = null

      // 处理直接对象格式
      if (currentResponse && !currentResponse.success) {
        // 直接是工作区对象
        newWorkspace = currentResponse
      } else if (currentResponse?.success && currentResponse?.data) {
        // ApiResponse格式
        newWorkspace = currentResponse.data
      } else if (currentResponse?.data) {
        // 其他格式
        newWorkspace = currentResponse.data
      }

      if (newWorkspace) {
        setCurrentWorkspace(newWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(newWorkspace)
      } else {
        // 服务器返回无效，使用第一个可用工作区
        if (workspaceData.length > 0) {
          const firstWorkspace = workspaceData[0]
          setCurrentWorkspace(firstWorkspace)
          workspaceService.saveCurrentWorkspaceToStorage(firstWorkspace)
        }
      }
    } catch (error) {
      console.error('获取当前工作区失败:', error)
      // 使用第一个可用工作区作为最后备选
      if (workspaceData.length > 0) {
        const firstWorkspace = workspaceData[0]
        setCurrentWorkspace(firstWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(firstWorkspace)
      }
    }
  }

  // 切换工作区
  const handleSwitchWorkspace = async (workspace: Workspace) => {
    if (workspace.id === currentWorkspace?.id) {
      return
    }

    const canSwitch = workspaceService.canSwitchToWorkspace(workspace)
    if (!canSwitch.allowed) {
      message.error(canSwitch.reason || '无法切换到此工作区')
      return
    }

    // 直接切换工作区，无需确认
    setSwitching(true)
    try {
      await confirmSwitchWorkspace(workspace)
    } catch (error) {
      console.error('切换工作区失败:', error)
      message.error('切换工作区失败: ' + (error as Error).message)
    } finally {
      setSwitching(false)
    }
  }

  // 确认切换工作区
  const confirmSwitchWorkspace = async (workspace: Workspace) => {
    setSwitching(true)
    try {
      console.log('开始切换工作区到:', workspace)

      const response = await workspaceService.switchWorkspace({
        workspace_id: workspace.id
      })

      console.log('切换工作区响应:', response)

      // 处理不同的响应格式
      let newWorkspace: Workspace | null = null

      if (response?.success && response?.data?.workspace) {
        // ApiResponse格式
        newWorkspace = response.data.workspace
        console.log('使用ApiResponse格式，新工作区:', newWorkspace)
      } else if (response?.success && response?.workspace) {
        // 直接的WorkspaceSwitchResponse格式
        newWorkspace = response.workspace
        console.log('使用直接响应格式，新工作区:', newWorkspace)
      } else if (response?.workspace) {
        // 简化的响应格式
        newWorkspace = response.workspace
        console.log('使用简化格式，新工作区:', newWorkspace)
      }

      if (newWorkspace) {
        console.log('切换成功，保存工作区:', newWorkspace)

        // 更新当前工作区
        setCurrentWorkspace(newWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(newWorkspace)

        // 触发会员等级更新
        const { user } = useAuthStore.getState()
        if (user) {
          console.log('触发会员等级更新')
          triggerWorkspaceSwitch(newWorkspace, user.membership_type)
        }

        message.success(`已切换到 ${workspaceService.getWorkspaceDisplayName(newWorkspace)}`)

        // 延迟刷新页面，确保状态已保存
        setTimeout(() => {
          console.log('准备刷新页面')
          window.location.reload()
        }, 1500)
      } else {
        console.error('切换工作区响应格式异常:', response)
        message.error('切换工作区失败：响应格式错误')
      }
    } catch (error) {
      console.error('切换工作区失败:', error)
      message.error('切换工作区失败: ' + (error as Error).message)
    } finally {
      setSwitching(false)
    }
  }

  // 获取工作区显示组件
  const getWorkspaceDisplay = (workspace: ExtendedWorkspace, index: number) => {
    const typeInfo = workspaceService.formatWorkspaceType(workspace.type)
    const tierInfo = workspaceService.formatMembershipTier(workspace.membership_tier)
    const isCurrent = currentWorkspace?.id === workspace.id

    // 创建唯一key，确保不会重复
    const uniqueKey = `${workspace.id}_${workspace.name}_${index}`

    // 格式化角色显示
    const formatRoles = (roles: string[], departments: string[]) => {
      if (!roles || roles.length === 0) return ''

      const roleNames: string[] = []
      roles.forEach(role => {
        switch (role) {
          case 'owner':
            roleNames.push('企业主')
            break
          case 'employee':
            roleNames.push('员工')
            break
          case 'admin':
            roleNames.push('管理员')
            break
          default:
            roleNames.push(role)
        }
      })

      const roleText = roleNames.join('、')
      const deptText = departments && departments.length > 0 ? ` (${departments.join('、')})` : ''
      return ` (${roleText}${deptText})`
    }

    return {
      key: uniqueKey,
      label: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', minWidth: '280px' }}>
          <Space>
            <Avatar
              size="small"
              icon={workspace.type === 'personal' ? <UserOutlined /> : <TeamOutlined />}
              style={{
                backgroundColor: isCurrent ? '#1890ff' : (workspace.type === 'personal' ? '#1890ff' : '#52c41a')
              }}
            />
            <div>
              <div style={{ fontWeight: isCurrent ? 'bold' : 'normal' }}>
                {workspace.name}
                {isCurrent && (
                  <CheckCircleOutlined style={{ color: '#52c41a', marginLeft: '8px' }} />
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                {typeInfo.text}
                {formatRoles(workspace.all_roles, workspace.all_departments)}
                {tierInfo.text && ` • ${tierInfo.text}`}
                {workspace.factory_name && ` • ${workspace.factory_name}`}
              </div>
            </div>
          </Space>
          {isCurrent && (
            <Badge status="success" text="当前" />
          )}
        </div>
      ),
      onClick: () => {
        console.log('下拉菜单项被点击:', workspace.name, workspace.id)
        handleSwitchWorkspace(workspace)
      },
      disabled: switching || workspace.id === currentWorkspace?.id
    }
  }

  // 渲染当前工作区按钮
  const renderCurrentWorkspaceButton = () => {
    if (loading || !currentWorkspace) {
      return (
        <Button
          type="text"
          icon={<SwitcherOutlined />}
          className={className}
          loading={loading}
        >
          {compact ? '' : '工作区'}
        </Button>
      )
    }

    const typeInfo = workspaceService.formatWorkspaceType(currentWorkspace.type)

    if (compact) {
      return (
        <Button
          type="text"
          icon={
            <Avatar
              size="small"
              icon={currentWorkspace.type === 'personal' ? <UserOutlined /> : <TeamOutlined />}
              style={{
                backgroundColor: currentWorkspace.type === 'personal' ? '#1890ff' : '#52c41a'
              }}
            />
          }
          className={className}
          title={`${currentWorkspace.name} (${typeInfo.text})`}
        />
      )
    }

    return (
      <Button
        type="text"
        icon={<SwitcherOutlined />}
        className={className}
        style={{
          display: 'flex',
          alignItems: 'center',
          width: '100%',
          justifyContent: 'flex-start',
          padding: '4px 8px'
        }}
      >
        <Space>
          <Avatar
            size="small"
            icon={currentWorkspace.type === 'personal' ? <UserOutlined /> : <TeamOutlined />}
            style={{
              backgroundColor: currentWorkspace.type === 'personal' ? '#1890ff' : '#52c41a'
            }}
          />
          <div style={{
            textAlign: 'left',
            minWidth: 0,
            flex: 1,
            overflow: 'hidden'
          }}>
            <div style={{
              fontSize: '12px',
              fontWeight: 500,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {currentWorkspace.name}
            </div>
            <div style={{
              fontSize: '10px',
              color: '#666',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {typeInfo.text}
            </div>
          </div>
        </Space>
      </Button>
    )
  }

  if (!user) {
    return null
  }

  const dropdownItems = workspaces.map((workspace, index) => getWorkspaceDisplay(workspace, index))

  if (dropdownItems.length === 0) {
    // 下拉菜单为空，显示普通按钮
    return renderCurrentWorkspaceButton()
  }
  return (
    <Dropdown
      menu={{
        items: dropdownItems,
        onClick: ({ key }) => {
          console.log('Dropdown onClick触发:', key)
        }
      }}
      placement="bottomRight"
      trigger={['click']}
      disabled={loading || switching}
      onOpenChange={(open) => {
        console.log('Dropdown打开状态改变:', open)
      }}
    >
      {renderCurrentWorkspaceButton()}
    </Dropdown>
  )
}

export default WorkspaceSwitcher