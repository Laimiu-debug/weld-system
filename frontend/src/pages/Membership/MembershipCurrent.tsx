import React, { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Row,
  Col,
  Button,
  Tag,
  Progress,
  Space,
  Divider,
  Alert,
  Table,
  Spin,
  message,
} from 'antd'
import {
  CrownOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { membershipService, UserMembershipInfo, MembershipUsage } from '@/services/membership'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography

const MembershipCurrent: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [membershipInfo, setMembershipInfo] = useState<UserMembershipInfo | null>(null)
  const [usageStats, setUsageStats] = useState<MembershipUsage | null>(null)

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

  // 获取会员等级配额
  const getMembershipLimits = (tier: string) => {
    const limits: Record<string, any> = {
      personal_free: {
        wps: 10,
        pqr: 10,
        ppqr: 0,
        materials: 0,
        welders: 0,
        equipment: 0,
        storage: 100,
      },
      personal_pro: {
        wps: 30,
        pqr: 30,
        ppqr: 30,
        materials: 50,
        welders: 20,
        equipment: 0,
        storage: 500,
      },
      personal_advanced: {
        wps: 50,
        pqr: 50,
        ppqr: 50,
        materials: 100,
        welders: 50,
        equipment: 20,
        storage: 1000,
      },
      personal_flagship: {
        wps: 100,
        pqr: 100,
        ppqr: 100,
        materials: 200,
        welders: 100,
        equipment: 50,
        storage: 2000,
      },
      enterprise: {
        wps: 200,
        pqr: 200,
        ppqr: 200,
        materials: 500,
        welders: 200,
        equipment: 100,
        storage: 5000,
      },
      enterprise_pro: {
        wps: 400,
        pqr: 400,
        ppqr: 400,
        materials: 1000,
        welders: 500,
        equipment: 200,
        storage: 10000,
      },
      enterprise_pro_max: {
        wps: 500,
        pqr: 500,
        ppqr: 500,
        materials: 2000,
        welders: 1000,
        equipment: 500,
        storage: 20000,
      },
      // 兼容旧的等级名称
      free: {
        wps: 10,
        pqr: 10,
        ppqr: 0,
        materials: 0,
        welders: 0,
        equipment: 0,
        storage: 100,
      },
    }
    return limits[tier] || limits.personal_free
  }

  // 获取订阅状态显示名称
  const getSubscriptionStatusName = (status: string) => {
    const statusNames: Record<string, string> = {
      active: '激活',
      expired: '已过期',
      cancelled: '已取消',
      pending: '待处理',
      inactive: '未激活',
    }
    return statusNames[status] || '未知'
  }

  // 获取订阅状态颜色
  const getSubscriptionStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      active: 'success',
      expired: 'error',
      cancelled: 'default',
      pending: 'warning',
      inactive: 'default',
    }
    return statusColors[status] || 'default'
  }

  // 获取会员信息和使用统计
  useEffect(() => {
    const fetchMembershipData = async () => {
      try {
        setLoading(true)

        // 先刷新用户信息,确保获取到最新的会员等级
        // 这对于支付升级后的场景非常重要
        try {
          const { refreshUserInfo } = useAuthStore.getState()
          await refreshUserInfo()
          console.log('[会员中心] 用户信息已刷新')
        } catch (error) {
          console.error('[会员中心] 刷新用户信息失败:', error)
        }

        // 分别获取数据，避免一个失败导致全部失败
        let membershipData = null
        let usageData = null

        try {
          membershipData = await membershipService.getUserMembershipInfo()
          console.log('[会员中心] 会员信息:', membershipData)
        } catch (error) {
          console.error('Failed to fetch membership info:', error)
          // 如果获取失败，使用默认值
          membershipData = null
        }

        try {
          usageData = await membershipService.getUserUsageStats()
        } catch (error) {
          console.error('Failed to fetch usage stats:', error)
          // 如果获取失败，使用默认值
          usageData = {
            wps: 0,
            pqr: 0,
            ppqr: 0,
            materials: 0,
            welders: 0,
            equipment: 0,
            storage: 0
          }
        }

        setMembershipInfo(membershipData)
        setUsageStats(usageData)
      } catch (error) {
        console.error('Failed to fetch membership data:', error)
        message.error('获取会员信息失败，请稍后重试')
      } finally {
        setLoading(false)
      }
    }

    fetchMembershipData()
  }, [])

  const limits = membershipInfo ? {
    wps: membershipInfo.quotas.wps.limit,
    pqr: membershipInfo.quotas.pqr.limit,
    ppqr: membershipInfo.quotas.ppqr.limit,
    materials: 0, // 后续可以添加
    welders: 0, // 后续可以添加
    equipment: 0, // 后续可以添加
    storage: membershipInfo.quotas.storage.limit,
  } : getMembershipLimits((user as any)?.member_tier || user?.membership_tier || 'personal_free')

  const usageData = usageStats || {
    wps: 0,
    pqr: 0,
    ppqr: 0,
    materials: 0,
    welders: 0,
    equipment: 0,
    storage: 0,
  }

  // 配额表格列配置
  const quotaColumns = [
    {
      title: '资源类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '已使用',
      dataIndex: 'used',
      key: 'used',
    },
    {
      title: '配额上限',
      dataIndex: 'limit',
      key: 'limit',
    },
    {
      title: '使用率',
      dataIndex: 'usage',
      key: 'usage',
      render: (usage: number) => (
        <Progress
          percent={usage}
          size="small"
          status={usage >= 90 ? 'exception' : usage >= 70 ? 'active' : 'normal'}
        />
      ),
    },
  ]

  // 配额表格数据 - 根据会员等级动态生成
  const currentTier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
  const currentLimits = getMembershipLimits(currentTier)

  const quotaData = [
    {
      key: 'wps',
      type: 'WPS记录',
      used: membershipInfo?.quotas?.wps?.used ?? usageStats?.wps ?? 0,
      limit: membershipInfo?.quotas?.wps?.limit || currentLimits.wps,
      usage: (() => {
        const used = membershipInfo?.quotas?.wps?.used ?? usageStats?.wps ?? 0
        const limit = membershipInfo?.quotas?.wps?.limit || currentLimits.wps
        return limit > 0 ? Math.round((used / limit) * 100) : 0
      })(),
    },
    {
      key: 'pqr',
      type: 'PQR记录',
      used: membershipInfo?.quotas?.pqr?.used ?? usageStats?.pqr ?? 0,
      limit: membershipInfo?.quotas?.pqr?.limit || currentLimits.pqr,
      usage: (() => {
        const used = membershipInfo?.quotas?.pqr?.used ?? usageStats?.pqr ?? 0
        const limit = membershipInfo?.quotas?.pqr?.limit || currentLimits.pqr
        return limit > 0 ? Math.round((used / limit) * 100) : 0
      })(),
    },
    // 根据会员等级决定是否显示pPQR配额
    ...((currentTier !== 'free' && currentTier !== 'personal_free') || (membershipInfo?.quotas?.ppqr?.limit && membershipInfo.quotas.ppqr.limit > 0) ? [{
      key: 'ppqr',
      type: 'pPQR记录',
      used: membershipInfo?.quotas?.ppqr?.used ?? usageStats?.ppqr ?? 0,
      limit: membershipInfo?.quotas?.ppqr?.limit || currentLimits.ppqr,
      usage: (() => {
        const used = membershipInfo?.quotas?.ppqr?.used ?? usageStats?.ppqr ?? 0
        const limit = membershipInfo?.quotas?.ppqr?.limit || currentLimits.ppqr
        return limit > 0 ? Math.round((used / limit) * 100) : 0
      })(),
    }] : []),
    {
      key: 'storage',
      type: '存储空间',
      used: `${membershipInfo?.quotas?.storage?.used ?? usageStats?.storage ?? 0}MB`,
      limit: `${membershipInfo?.quotas?.storage?.limit || currentLimits.storage}MB`,
      usage: (() => {
        const used = membershipInfo?.quotas?.storage?.used ?? usageStats?.storage ?? 0
        const limit = membershipInfo?.quotas?.storage?.limit || currentLimits.storage
        return limit > 0 ? Math.round((used / limit) * 100) : 0
      })(),
    },
  ]

  // 显示加载状态
  if (loading) {
    return (
      <div className="page-container flex justify-center items-center" style={{ height: '400px' }}>
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4 text-gray-500">加载会员信息中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>会员中心</Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="当前套餐">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={8}>
                <div className="text-center">
                  <CrownOutlined
                    style={{
                      fontSize: 48,
                      color: getMembershipTierColor(membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'),
                    }}
                  />
                  <Title level={3} className="mt-2">
                    {getMembershipTierName(membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free')}
                  </Title>
                </div>
              </Col>
              <Col xs={24} sm={16}>
                <Space direction="vertical" size="middle" className="w-full">
                  {/* 企业继承提示 */}
                  {membershipInfo?.is_inherited_from_company && (
                    <Alert
                      message={
                        <span>
                          <TeamOutlined style={{ marginRight: 8 }} />
                          您当前使用的是企业会员权限
                        </span>
                      }
                      description={`您已加入企业「${membershipInfo.company_name}」，自动继承企业会员等级和配额。`}
                      type="info"
                      showIcon={false}
                      style={{ marginBottom: 8 }}
                    />
                  )}

                  <div>
                    <Text strong>订阅状态: </Text>
                    <Tag color={getSubscriptionStatusColor(
                      membershipInfo?.subscription_status ||
                      (user as any)?.subscription_status ||
                      'inactive'
                    )}>
                      {getSubscriptionStatusName(
                        membershipInfo?.subscription_status ||
                        (user as any)?.subscription_status ||
                        'inactive'
                      )}
                    </Tag>
                  </div>
                  <div>
                    <Text strong>订阅开始日期: </Text>
                    <Text>
                      {(() => {
                        // 优先使用 membershipInfo 中的数据
                        if (membershipInfo?.subscription_start_date) {
                          return dayjs(membershipInfo.subscription_start_date).format('YYYY-MM-DD')
                        }

                        // 其次使用 user 对象中的数据
                        if ((user as any)?.subscription_start_date) {
                          return dayjs((user as any).subscription_start_date).format('YYYY-MM-DD')
                        }

                        // 最后使用注册日期
                        if (user?.created_at) {
                          return dayjs(user.created_at).format('YYYY-MM-DD')
                        }

                        return '未设置'
                      })()}
                    </Text>
                  </div>
                  <div>
                    <Text strong>订阅结束日期: </Text>
                    <Text>
                      {(() => {
                        const tier = membershipInfo?.membership_tier ||
                                    (user as any)?.member_tier ||
                                    user?.membership_tier ||
                                    'personal_free'

                        // 免费版永久有效
                        if (tier === 'free' || tier === 'personal_free') {
                          return '永久有效'
                        }

                        // 优先使用 membershipInfo 中的数据
                        if (membershipInfo?.subscription_end_date) {
                          return dayjs(membershipInfo.subscription_end_date).format('YYYY-MM-DD')
                        }

                        // 其次使用 user 对象中的数据
                        if ((user as any)?.subscription_end_date) {
                          return dayjs((user as any).subscription_end_date).format('YYYY-MM-DD')
                        }

                        // 付费版但没有结束日期，显示未订阅
                        return '未订阅'
                      })()}
                    </Text>
                  </div>
                  <div>
                    <Text strong>自动续费: </Text>
                    <Tag color={
                      (membershipInfo?.auto_renewal !== undefined
                        ? membershipInfo.auto_renewal
                        : (user as any)?.auto_renewal)
                      ? 'success'
                      : 'default'
                    }>
                      {(membershipInfo?.auto_renewal !== undefined
                        ? membershipInfo.auto_renewal
                        : (user as any)?.auto_renewal)
                      ? '已开启'
                      : '已关闭'}
                    </Tag>
                  </div>
                </Space>
              </Col>
            </Row>

            <Divider />

            <div className="text-center">
              <Space>
                {(() => {
                  const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                  const isInherited = membershipInfo?.is_inherited_from_company

                  // 如果是继承的会员权限，不显示升级按钮
                  if (isInherited) {
                    return null
                  }

                  return (
                    <>
                      {tier !== 'enterprise_pro_max' && (
                        <Button
                          type="primary"
                          icon={<CrownOutlined />}
                          onClick={() => navigate('/membership/upgrade')}
                        >
                          升级套餐
                        </Button>
                      )}
                      {tier !== 'free' && tier !== 'personal_free' && (
                        <Button
                          icon={<SyncOutlined />}
                          onClick={async () => {
                            try {
                              const current = await membershipService.getCurrentSubscription()
                              if (!current) {
                                message.warning('暂无有效订阅，请先升级套餐')
                                return
                              }
                              navigate(
                                `/membership/payment?subscription_id=${current.id}&plan_id=${current.plan_id}&billing_cycle=${current.billing_cycle || 'monthly'}`
                              )
                            } catch (error) {
                              console.error(error)
                              message.error('无法发起续费')
                            }
                          }}
                        >
                          续费
                        </Button>
                      )}
                    </>
                  )
                })()}
                <Button
                  icon={<SyncOutlined />}
                  onClick={() => navigate('/membership/history')}
                >
                  订阅历史
                </Button>
              </Space>
            </div>
          </Card>

          <Card title="使用配额" className="mt-6">
            <Table
              dataSource={quotaData}
              columns={quotaColumns}
              pagination={false}
              size="middle"
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {(() => {
                const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                return tier === 'free' || tier === 'personal_free'
              })() && (
            <Alert
              message="升级您的套餐"
              description="您当前使用的是免费版，升级到付费版本可解锁更多功能和更高配额。"
              type="info"
              showIcon
              action={
                <Button
                  type="primary"
                  size="small"
                  icon={<CrownOutlined />}
                  onClick={() => navigate('/membership/upgrade')}
                >
                  立即升级
                </Button>
              }
              className="mb-6"
            />
          )}

          <Card title="套餐对比">
            <Space direction="vertical" size="small" className="w-full">
              <div className="flex justify-between">
                <Text>专业版</Text>
                <Text>¥19/月</Text>
              </div>
              <div className="flex justify-between">
                <Text>高级版</Text>
                <Text>¥49/月</Text>
              </div>
              <div className="flex justify-between">
                <Text>旗舰版</Text>
                <Text>¥99/月</Text>
              </div>
              <div className="flex justify-between">
                <Text>企业版</Text>
                <Text>¥199/月</Text>
              </div>
              <div className="flex justify-between">
                <Text>企业版PRO</Text>
                <Text>¥399/月</Text>
              </div>
              <div className="flex justify-between">
                <Text>企业版PRO MAX</Text>
                <Text>¥899/月</Text>
              </div>
            </Space>

            <Divider />

            <div className="text-center">
              <Button
                type="primary"
                icon={<CrownOutlined />}
                onClick={() => navigate('/membership/upgrade')}
              >
                查看所有套餐
              </Button>
            </div>
          </Card>

          <Card title="会员权益" className="mt-6">
            <Space direction="vertical" size="small" className="w-full">
              {/* 如果有从API获取的features，优先显示 */}
              {membershipInfo?.features && membershipInfo.features.length > 0 ? (
                membershipInfo.features.map((feature, index) => (
                  <div key={index}>
                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <Text>{feature}</Text>
                  </div>
                ))
              ) : (
                <>
                  {/* 基础功能权益 */}
                  <div>
                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <Text>WPS管理模块（{membershipInfo?.quotas?.wps?.limit || limits.wps}个）</Text>
                  </div>
                  <div>
                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <Text>PQR管理模块（{membershipInfo?.quotas?.pqr?.limit || limits.pqr}个）</Text>
                  </div>

                  {/* 根据会员等级显示高级功能 */}
                  {(() => {
                    const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                    const ppqrLimit = membershipInfo?.quotas?.ppqr?.limit || limits.ppqr
                    return tier !== 'free' && tier !== 'personal_free' && ppqrLimit > 0
                  })() && (
                    <>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>pPQR管理模块（{membershipInfo?.quotas?.ppqr?.limit || limits.ppqr}个）</Text>
                      </div>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>焊材管理模块</Text>
                      </div>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>焊工管理模块</Text>
                      </div>
                    </>
                  )}

                  {/* 高级版及以上显示生产管理模块 */}
                  {(() => {
                    const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                    return tier === 'personal_advanced' || tier === 'personal_flagship' || tier.startsWith('enterprise')
                  })() && (
                    <>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>生产管理模块</Text>
                      </div>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>设备管理模块</Text>
                      </div>
                      <div>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                        <Text>质量管理模块</Text>
                      </div>
                    </>
                  )}

                  {/* 旗舰版及以上显示报表统计 */}
                  {(() => {
                    const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                    return tier === 'personal_flagship' || tier.startsWith('enterprise')
                  })() && (
                    <div>
                      <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                      <Text>报表统计模块</Text>
                    </div>
                  )}

                  {/* 企业版显示员工管理 */}
                  {(() => {
                    const tier = membershipInfo?.membership_tier || (user as any)?.member_tier || user?.membership_tier || 'personal_free'
                    return tier.startsWith('enterprise')
                  })() ? (
                    <div>
                      <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                      <Text>企业员工管理模块</Text>
                    </div>
                  ) : (
                    <div style={{ opacity: 0.5 }}>
                      <CheckCircleOutlined style={{ color: '#d9d9d9', marginRight: 8 }} />
                      <Text type="secondary">企业员工管理模块（升级到企业版解锁）</Text>
                    </div>
                  )}
                </>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default MembershipCurrent