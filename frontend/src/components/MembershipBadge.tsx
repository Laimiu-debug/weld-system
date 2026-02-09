import React from 'react'
import { Tag } from 'antd'
import { CrownOutlined } from '@ant-design/icons'
import { useMembership } from '@/contexts/MembershipContext'

interface MembershipBadgeProps {
  size?: 'small' | 'default'
  showIcon?: boolean
  className?: string
}

const MembershipBadge: React.FC<MembershipBadgeProps> = ({
  size = 'default',
  showIcon = true,
  className = ''
}) => {
  const { membershipInfo, isLoading } = useMembership()

  if (isLoading || !membershipInfo) {
    return (
      <Tag size={size} className={className}>
        {showIcon && <CrownOutlined />}
        加载中...
      </Tag>
    )
  }

  const getTagColor = (tier: string) => {
    const colorMap: Record<string, string> = {
      'personal_free': 'default',
      'personal_basic': 'blue',
      'personal_pro': 'purple',
      'personal_advanced': 'gold',
      'enterprise_basic': 'green',
      'enterprise_pro': 'orange',
      'enterprise_advanced': 'red'
    }
    return colorMap[tier] || 'default'
  }

  return (
    <Tag
      color={getTagColor(membershipInfo.tier)}
      size={size}
      className={className}
      style={{
        fontWeight: membershipInfo.isEnterprise ? 'bold' : 'normal'
      }}
    >
      {showIcon && <CrownOutlined />}
      {membershipInfo.displayName}
      {membershipInfo.isEnterprise && ' (企业)'}
    </Tag>
  )
}

export default MembershipBadge