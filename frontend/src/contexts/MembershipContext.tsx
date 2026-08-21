import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { message } from 'antd'
import { useAuthStore } from '@/store/authStore'
import { workspaceService } from '@/services/workspace'
import { membershipService } from '@/services/membership'
import { Workspace } from '@/services/workspace'

// 会员信息类型
export interface CurrentMembershipInfo {
  tier: string
  displayName: string
  color: string
  isEnterprise: boolean
  features: string[]
  quotas: any
  workspaceType: string
  lastUpdated: Date
  nextTier?: string
  nextTierName?: string
  upgradePrice?: string | number
}

// 会员上下文类型
interface MembershipContextType {
  membershipInfo: CurrentMembershipInfo | null
  updateMembershipForWorkspace: (workspace: Workspace, userMembershipType: string) => void
  refreshMembership: () => Promise<void>
  isLoading: boolean
}

// 创建上下文
const MembershipContext = createContext<MembershipContextType | undefined>(undefined)

// 会员上下文Provider组件
export const MembershipProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuthStore()
  const [membershipInfo, setMembershipInfo] = useState<CurrentMembershipInfo | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // 根据工作区更新会员信息
  const updateMembershipForWorkspace = async (workspace: Workspace, userMembershipType: string) => {
    if (!user || !workspace) return

    try {
      // 确定当前工作区的会员等级
      const currentTier = membershipService.determineWorkspaceMembership(
        userMembershipType,
        workspace.type,
        workspace.membership_tier
      )

      const displayName = membershipService.getMembershipDisplayName(currentTier)
      const color = membershipService.getMembershipColor(currentTier)
      const isEnterprise = workspace.type === 'enterprise'

      // 获取详细的会员信息
      const membershipDetails = await membershipService.getUserMembershipInfo()

      const newMembershipInfo: CurrentMembershipInfo = {
        tier: currentTier,
        displayName,
        color,
        isEnterprise,
        features: membershipDetails?.features || [],
        quotas: membershipDetails?.quotas || {},
        workspaceType: workspace.type,
        lastUpdated: new Date()
      }

      setMembershipInfo(newMembershipInfo)

      // 保存到本地存储
      localStorage.setItem('current_membership', JSON.stringify({
        ...newMembershipInfo,
        lastUpdated: newMembershipInfo.lastUpdated.toISOString()
      }))
    } catch (error) {
      console.error('更新会员信息失败:', error)
      message.error('更新会员信息失败')
    }
  }

  // 刷新会员信息
  const refreshMembership = async () => {
    if (!user) return

    setIsLoading(true)
    try {
      // 获取当前工作区
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      if (currentWorkspace) {
        await updateMembershipForWorkspace(currentWorkspace, user.membership_type)
      }
    } catch (error) {
      console.error('刷新会员信息失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 监听用户变化（仅用户 id，避免 refreshUserInfo 更新对象引用后反复拉取）
  useEffect(() => {
    if (user?.id) {
      // 从本地存储恢复会员信息
      const storedMembership = localStorage.getItem('current_membership')
      if (storedMembership) {
        try {
          const parsed = JSON.parse(storedMembership)
          setMembershipInfo({
            ...parsed,
            lastUpdated: new Date(parsed.lastUpdated)
          })
        } catch (error) {
          console.error('解析本地存储的会员信息失败:', error)
        }
      }

      // 刷新会员信息
      refreshMembership()
    } else {
      // 用户登出时清除会员信息
      setMembershipInfo(null)
      localStorage.removeItem('current_membership')
    }
  }, [user?.id])

  // 监听工作区切换事件
  useEffect(() => {
    const handleWorkspaceSwitch = (event: CustomEvent) => {
      const { workspace, userMembershipType } = event.detail
      updateMembershipForWorkspace(workspace, userMembershipType)
    }

    // 监听自定义事件
    window.addEventListener('workspace-switched', handleWorkspaceSwitch as EventListener)

    return () => {
      window.removeEventListener('workspace-switched', handleWorkspaceSwitch as EventListener)
    }
  }, [user])

  const value: MembershipContextType = {
    membershipInfo,
    updateMembershipForWorkspace,
    refreshMembership,
    isLoading
  }

  return (
    <MembershipContext.Provider value={value}>
      {children}
    </MembershipContext.Provider>
  )
}

// 使用会员上下文的Hook
export const useMembership = (): MembershipContextType => {
  const context = useContext(MembershipContext)
  if (context === undefined) {
    throw new Error('useMembership must be used within a MembershipProvider')
  }
  return context
}

// 工作区切换辅助函数
export const triggerWorkspaceSwitch = (workspace: Workspace, userMembershipType: string) => {
  const event = new CustomEvent('workspace-switched', {
    detail: { workspace, userMembershipType }
  })
  window.dispatchEvent(event)
}

export default MembershipContext
