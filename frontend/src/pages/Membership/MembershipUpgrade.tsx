import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Tag,
  Divider,
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  Radio,
  Alert,
  Tooltip,
  Progress,
  Statistic,
  List,
  Avatar,
  Badge,
  message,
  Steps,
  Spin,
} from 'antd'
import apiService from '@/services/api'
import {
  CrownOutlined,
  ThunderboltOutlined,
  CheckOutlined,
  StarOutlined,
  GiftOutlined,
  SafetyOutlined,
  RocketOutlined,
  TeamOutlined,
  ToolOutlined,
  FileTextOutlined,
  BarChartOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  UserOutlined,
  CreditCardOutlined,
  WechatOutlined,
  BankOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { membershipService, SubscriptionPlan, MembershipUpgradeRequest } from '@/services/membership'
import ManualPaymentModal from '@/components/Payment/ManualPaymentModal'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { Step } = Steps

// 自定义样式
const cardStyles = `
.membership-card {
  position: relative;
  transition: all 0.3s ease;
  cursor: pointer;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
}

.membership-card.focused {
  border: 2px solid #1890ff !important;
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.1), 0 8px 32px rgba(24, 144, 255, 0.2) !important;
  transform: translateY(-6px);
  position: relative;
  z-index: 10;
}

.recommended-card {
  position: relative;
  border: 2px solid #1890ff;
  background: linear-gradient(145deg, #f0f8ff, #e6f7ff);
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.15);
}

.recommended-card .recommended-badge {
  position: absolute;
  top: -1px;
  right: 16px;
  background: linear-gradient(45deg, #1890ff, #40a9ff);
  color: white;
  padding: 4px 12px;
  border-radius: 0 0 8px 8px;
  font-size: 12px;
  font-weight: 600;
  z-index: 1;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.membership-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  background: linear-gradient(145deg, #ffffff, #f0f4f8);
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  position: relative;
  z-index: 10;
}

.recommended-card:hover {
  box-shadow: 0 16px 40px rgba(24, 144, 255, 0.25);
  background: linear-gradient(145deg, #e6f7ff, #d6f4ff);
  border-radius: 16px !important;
  border: 2px solid #1890ff !important;
}

.membership-card.free-card {
  background: linear-gradient(145deg, #f6ffed, #f0f9e8);
  border-color: #52c41a;
}

.membership-card.free-card:hover {
  background: linear-gradient(145deg, #f0f9e8, #e9f5dc);
}

.membership-card.pro-card {
  background: linear-gradient(145deg, #f0f8ff, #e6f4ff);
  border-color: #1890ff;
}

.membership-card.pro-card:hover {
  background: linear-gradient(145deg, #e6f4ff, #d9e9ff);
}

.membership-card.advanced-card {
  background: linear-gradient(145deg, #f9f0ff, #f2e9ff);
  border-color: #722ed1;
}

.membership-card.advanced-card:hover {
  background: linear-gradient(145deg, #f2e9ff, #eadcff);
}

.membership-card.flagship-card {
  background: linear-gradient(145deg, #fff7e6, #ffeecf);
  border-color: #fa8c16;
}

.membership-card.flagship-card:hover {
  background: linear-gradient(145deg, #ffeecf, #ffe4b8);
}

.membership-card.enterprise-card {
  background: linear-gradient(145deg, #e6fffb, #d1f7f0);
  border-color: #13c2c2;
}

.membership-card.enterprise-card:hover {
  background: linear-gradient(145deg, #d1f7f0, #b7f3ec);
}

.membership-card.enterprise-pro-card {
  background: linear-gradient(145deg, #fff1f0, #ffebe8);
  border-color: #f5222d;
}

.membership-card.enterprise-pro-card:hover {
  background: linear-gradient(145deg, #ffebe8, #ffd4d0);
}

.membership-card.enterprise-max-card {
  background: linear-gradient(145deg, #fff0f6, #ffe6eb);
  border-color: #eb2f96;
}

.membership-card.enterprise-max-card:hover {
  background: linear-gradient(145deg, #ffe6eb, #ffd1de);
}
`

interface MembershipPlan {
  id: string
  name: string
  type: 'personal_free' | 'personal_pro' | 'personal_advanced' | 'personal_flagship' | 'enterprise' | 'enterprise_pro' | 'enterprise_pro_max'
  prices: {
    monthly: number
    quarterly: number
    yearly: number
  }
  features: string[]
  limitations: string[]
  recommended?: boolean
  icon: React.ReactNode
  color: string
  gradient?: string
  maxUsers?: number
  storage?: string
  support: string
}

interface UserMembership {
  currentPlan: string
  expiryDate: string
  features: string[]
  upgradeOptions: string[]
  remainingDays: number
}

const MembershipUpgrade: React.FC = () => {
  const navigate = useNavigate()
  const { user, refreshUserInfo } = useAuthStore()
  const [currentPlan, setCurrentPlan] = useState<string>('personal_free')
  const [selectedPlan, setSelectedPlan] = useState<string>('')
  const [focusedPlan, setFocusedPlan] = useState<string>('')
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [upgradeModalVisible, setUpgradeModalVisible] = useState(false)
  const [paymentModalVisible, setPaymentModalVisible] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [paymentMethod, setPaymentMethod] = useState<string>('alipay')
  const [agreeTerms, setAgreeTerms] = useState(false)
  const [loading, setLoading] = useState(false)

  // 手动支付相关状态
  const [manualPaymentVisible, setManualPaymentVisible] = useState(false)
  const [currentOrderId, setCurrentOrderId] = useState('')
  const [currentAmount, setCurrentAmount] = useState(0)
  const [currentPlanName, setCurrentPlanName] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [plansLoading, setPlansLoading] = useState(true)
  const [subscriptionPlans, setSubscriptionPlans] = useState<SubscriptionPlan[]>([])

  // 价格预览相关状态
  const [pricePreview, setPricePreview] = useState<{
    original_price: number
    actual_price: number
    discount: number
    is_upgrade: boolean
  } | null>(null)
  const [priceLoading, setPriceLoading] = useState(false)

  // 获取计划图标
  const getPlanIcon = (planId: string) => {
    switch (planId) {
      case 'free':
      case 'personal_free':
        return <UserOutlined />
      case 'personal_pro':
        return <StarOutlined />
      case 'personal_advanced':
        return <ThunderboltOutlined />
      case 'personal_flagship':
        return <CrownOutlined />
      case 'enterprise':
        return <RocketOutlined />
      case 'enterprise_pro':
        return <SafetyOutlined />
      case 'enterprise_pro_max':
        return <GiftOutlined />
      default:
        return <UserOutlined />
    }
  }

  // 获取计划颜色
  const getPlanColor = (planId: string) => {
    switch (planId) {
      case 'free':
      case 'personal_free':
        return '#52c41a'
      case 'personal_pro':
        return '#1890ff'
      case 'personal_advanced':
        return '#722ed1'
      case 'personal_flagship':
        return '#fa8c16'
      case 'enterprise':
        return '#13c2c2'
      case 'enterprise_pro':
        return '#f5222d'
      case 'enterprise_pro_max':
        return '#eb2f96'
      default:
        return '#8c8c8c'
    }
  }

  // 会员套餐数据 - 根据开发指南重新设计，使用正确的价格
  const fallbackPlans: MembershipPlan[] = [
    {
      id: 'free',
      name: '个人免费版',
      type: 'personal_free',
      prices: { monthly: 0, quarterly: 0, yearly: 0 },
      features: [
        'WPS管理模块（10个）',
        'PQR管理模块（10个）',
      ],
      limitations: [
        '无pPQR管理模块',
        '无焊材管理模块',
        '无焊工管理模块',
        '无生产管理模块',
        '无设备管理模块',
        '无质量管理模块',
        '无报表统计模块',
      ],
      icon: <UserOutlined />,
      color: '#52c41a',
      maxUsers: 1,
      storage: '基础存储',
      support: '社区支持',
    },
    {
      id: 'personal_pro',
      name: '个人专业版',
      type: 'personal_pro',
      prices: { monthly: 19, quarterly: 51, yearly: 183 },
      features: [
        'WPS管理模块（30个）',
        'PQR管理模块（30个）',
        'pPQR管理模块（30个）',
        '焊材管理模块',
        '焊工管理模块',
      ],
      limitations: [
        '无生产管理模块',
        '无设备管理模块',
        '无质量管理模块',
        '无报表统计模块',
      ],
      recommended: true,
      icon: <StarOutlined />,
      color: '#1890ff',
      maxUsers: 1,
      storage: '标准存储',
      support: '邮件支持',
    },
    {
      id: 'personal_advanced',
      name: '个人高级版',
      type: 'personal_advanced',
      prices: { monthly: 49, quarterly: 132, yearly: 470 },
      features: [
        'WPS管理模块（50个）',
        'PQR管理模块（50个）',
        'pPQR管理模块（50个）',
        '焊材管理模块',
        '焊工管理模块',
        '生产管理模块',
        '设备管理模块',
        '质量管理模块',
      ],
      limitations: [
        '无企业员工管理功能',
      ],
      icon: <ThunderboltOutlined />,
      color: '#722ed1',
      maxUsers: 1,
      storage: '高级存储',
      support: '优先支持',
    },
    {
      id: 'personal_flagship',
      name: '个人旗舰版',
      type: 'personal_flagship',
      prices: { monthly: 99, quarterly: 267, yearly: 950 },
      features: [
        'WPS管理模块（100个）',
        'PQR管理模块（100个）',
        'pPQR管理模块（100个）',
        '焊材管理模块',
        '焊工管理模块',
        '生产管理模块',
        '设备管理模块',
        '质量管理模块',
        '报表统计模块',
      ],
      limitations: [
        '不包含企业员工管理功能',
      ],
      icon: <CrownOutlined />,
      color: '#fa8c16',
      maxUsers: 1,
      storage: '专业存储',
      support: '专属支持',
    },
    {
      id: 'enterprise',
      name: '企业版',
      type: 'enterprise',
      prices: { monthly: 199, quarterly: 537, yearly: 1910 },
      features: [
        'WPS管理模块（200个）',
        'PQR管理模块（200个）',
        'pPQR管理模块（200个）',
        '焊材管理模块',
        '焊工管理模块',
        '生产管理模块',
        '设备管理模块',
        '质量管理模块',
        '报表统计模块',
        '企业员工管理模块（10人）',
        '多工厂数量：1个',
      ],
      limitations: [
        '最多10个员工',
        '最多1个工厂',
      ],
      icon: <RocketOutlined />,
      color: '#13c2c2',
      maxUsers: 10,
      storage: '企业存储',
      support: '7x24支持',
    },
    {
      id: 'enterprise_pro',
      name: '企业版PRO',
      type: 'enterprise_pro',
      prices: { monthly: 399, quarterly: 1077, yearly: 3830 },
      features: [
        'WPS管理模块（400个）',
        'PQR管理模块（400个）',
        'pPQR管理模块（400个）',
        '焊材管理模块',
        '焊工管理模块',
        '生产管理模块',
        '设备管理模块',
        '质量管理模块',
        '报表统计模块',
        '企业员工管理模块（20人）',
        '多工厂数量：3个',
      ],
      limitations: [],
      icon: <SafetyOutlined />,
      color: '#f5222d',
      maxUsers: 20,
      storage: '企业高级存储',
      support: '企业专属',
    },
    {
      id: 'enterprise_pro_max',
      name: '企业版PRO MAX',
      type: 'enterprise_pro_max',
      prices: { monthly: 899, quarterly: 2427, yearly: 8630 },
      features: [
        'WPS管理模块（500个）',
        'PQR管理模块（500个）',
        'pPQR管理模块（500个）',
        '焊材管理模块',
        '焊工管理模块',
        '生产管理模块',
        '设备管理模块',
        '质量管理模块',
        '报表统计模块',
        '企业员工管理模块（50人）',
        '多工厂数量：5个',
      ],
      limitations: [],
      icon: <GiftOutlined />,
      color: '#eb2f96',
      maxUsers: 50,
      storage: '定制存储',
      support: '战略支持',
    },
  ]

  // 将后端计划转换为前端格式
  // 优先使用从后端获取的订阅计划，如果没有则使用 fallbackPlans
  const membershipPlans: MembershipPlan[] = subscriptionPlans.length > 0
    ? subscriptionPlans.map(plan => ({
        id: plan.id,
        name: plan.name,
        type: plan.id,
        prices: {
          monthly: plan.monthly_price,
          quarterly: plan.quarterly_price,
          yearly: plan.yearly_price
        },
        features: Array.isArray(plan.features) ? plan.features : [],
        limitations: [],
        icon: getIconForPlan(plan.id),
        color: getColorForPlan(plan.id),
        maxUsers: plan.max_employees || 1,
        storage: getStorageForPlan(plan.id),
        support: getSupportForPlan(plan.id),
      }))
    : fallbackPlans

  // 辅助函数：根据计划ID获取图标
  function getIconForPlan(planId: string) {
    if (planId.includes('free')) return <UserOutlined />
    if (planId.includes('basic')) return <FileTextOutlined />
    if (planId.includes('pro') && !planId.includes('max')) return <RocketOutlined />
    if (planId.includes('enterprise') && !planId.includes('max')) return <TeamOutlined />
    if (planId.includes('max')) return <GiftOutlined />
    return <StarOutlined />
  }

  // 辅助函数：根据计划ID获取颜色
  function getColorForPlan(planId: string) {
    if (planId.includes('free')) return '#52c41a'
    if (planId.includes('basic')) return '#1890ff'
    if (planId.includes('pro') && !planId.includes('max')) return '#722ed1'
    if (planId.includes('enterprise') && !planId.includes('max')) return '#fa8c16'
    if (planId.includes('max')) return '#eb2f96'
    return '#1890ff'
  }

  // 辅助函数：根据计划ID获取存储说明
  function getStorageForPlan(planId: string) {
    if (planId.includes('free')) return '基础存储'
    if (planId.includes('basic')) return '标准存储'
    if (planId.includes('pro')) return '扩展存储'
    if (planId.includes('enterprise')) return '定制存储'
    return '标准存储'
  }

  // 辅助函数：根据计划ID获取支持说明
  function getSupportForPlan(planId: string) {
    if (planId.includes('free')) return '社区支持'
    if (planId.includes('basic')) return '邮件支持'
    if (planId.includes('pro')) return '优先支持'
    if (planId.includes('enterprise')) return '专属支持'
    if (planId.includes('max')) return '战略支持'
    return '标准支持'
  }

  // 刷新用户信息
  const handleRefreshUserInfo = async () => {
    setRefreshing(true)
    try {
      await refreshUserInfo()
      message.success('用户信息已刷新')
      // 重新获取会员信息
      fetchUserMembership()
    } catch (error) {
      message.error('刷新用户信息失败')
    } finally {
      setRefreshing(false)
    }
  }

  // 根据会员等级获取功能列表
  const getFeaturesByTier = (tier: string) => {
    // 处理免费版的特殊情况
    if (tier === 'free' || tier === 'personal_free') {
      tier = 'personal_free'
    }

    const plan = membershipPlans.find(p => p.type === tier || p.id === tier)
    return plan ? plan.features : []
  }

  // 获取用户会员信息的独立函数
  const fetchUserMembership = async () => {
    try {
      const membershipInfo = await membershipService.getUserMembershipInfo()
      if (membershipInfo) {
        setCurrentPlan(membershipInfo.membership_tier)

        // 计算到期日期和剩余天数
        let expiryDate = '永久有效'
        let remainingDays = 999

        const tier = membershipInfo.membership_tier || 'personal_free'

        // 免费版永久有效
        if (tier === 'free' || tier === 'personal_free') {
          expiryDate = '永久有效'
          remainingDays = 999
        } else if (membershipInfo.subscription_end_date) {
          // 付费版有结束日期
          const endDate = new Date(membershipInfo.subscription_end_date)
          const now = new Date()
          const diffTime = endDate.getTime() - now.getTime()
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

          expiryDate = membershipInfo.subscription_end_date
          remainingDays = diffDays > 0 ? diffDays : 0
        } else {
          // 付费版但没有结束日期
          expiryDate = '未订阅'
          remainingDays = 0
        }

        setUserMembership({
          currentPlan: membershipInfo.membership_tier,
          expiryDate: expiryDate,
          features: membershipInfo.features || [],
          upgradeOptions: [],
          remainingDays: remainingDays
        })
      }
    } catch (error) {
      console.error('Failed to fetch user membership:', error)
      // 如果API失败，使用用户store中的信息
      if (user) {
        const tier = (user as any).member_tier || user.membership_tier || 'personal_free'
        setCurrentPlan(tier)

        // 计算到期日期和剩余天数
        let expiryDate = '永久有效'
        let remainingDays = 999

        // 免费版永久有效
        if (tier === 'free' || tier === 'personal_free') {
          expiryDate = '永久有效'
          remainingDays = 999
        } else if ((user as any).subscription_end_date) {
          // 付费版有结束日期
          const endDate = new Date((user as any).subscription_end_date)
          const now = new Date()
          const diffTime = endDate.getTime() - now.getTime()
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

          expiryDate = (user as any).subscription_end_date
          remainingDays = diffDays > 0 ? diffDays : 0
        } else {
          // 付费版但没有结束日期
          expiryDate = '未订阅'
          remainingDays = 0
        }

        setUserMembership({
          currentPlan: tier,
          expiryDate: expiryDate,
          features: getFeaturesByTier(tier),
          upgradeOptions: [],
          remainingDays: remainingDays
        })
      }
    }
  }

  // 获取订阅计划
  useEffect(() => {
    const fetchSubscriptionPlans = async () => {
      try {
        setPlansLoading(true)
        const plans = await membershipService.getSubscriptionPlans()
        setSubscriptionPlans(plans)
      } catch (error) {
        console.error('Failed to fetch subscription plans:', error)
        message.error('获取订阅计划失败')
      } finally {
        setPlansLoading(false)
      }
    }

    fetchSubscriptionPlans()
  }, [])

  // 获取当前用户会员信息
  useEffect(() => {
    fetchUserMembership()
  }, [user])
  // const membershipPlans: MembershipPlan[] = subscriptionPlans.length > 0 ? subscriptionPlans.map(plan => ({
  //   id: plan.id,
  //   name: plan.name,
  //   type: plan.id as any,
  //   prices: {
  //     monthly: plan.monthly_price,
  //     quarterly: plan.quarterly_price,
  //     yearly: plan.yearly_price,
  //   },
  //   features: Array.isArray(plan.features) ? plan.features : [],
  //   limitations: [],
  //   recommended: plan.is_recommended,
  //   icon: getPlanIcon(plan.id),
  //   color: getPlanColor(plan.id),
  //   maxUsers: plan.max_employees,
  //   storage: `${plan.max_wps_files}个WPS`,
  //   support: '标准支持',
  // })) : fallbackPlans

  // 用户当前会员状态
  const [userMembership, setUserMembership] = useState<UserMembership>({
    currentPlan: 'personal_free',
    expiryDate: '永久有效',
    features: ['WPS管理模块（10个）', 'PQR管理模块（10个）'],
    upgradeOptions: ['personal_pro', 'personal_advanced', 'personal_flagship', 'enterprise', 'enterprise_pro', 'enterprise_pro_max'],
    remainingDays: 999,
  })

  // 获取套餐对比数据
  const getComparisonData = () => {
    const features = [
      { name: 'WPS管理', free: '10个', personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个', enterprise: '无限', enterprise_pro: '无限', enterprise_pro_max: '无限' },
      { name: 'PQR管理', free: '10个', personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个', enterprise: '无限', enterprise_pro: '无限', enterprise_pro_max: '无限' },
      { name: 'pPQR管理', free: false, personal_pro: '30个', personal_advanced: '50个', personal_flagship: '100个', enterprise: '无限', enterprise_pro: '无限', enterprise_pro_max: '无限' },
      { name: '设备管理', free: false, personal_pro: false, personal_advanced: true, personal_flagship: true, enterprise: true, enterprise_pro: true, enterprise_pro_max: true },
      { name: '生产管理', free: false, personal_pro: false, personal_advanced: '基础', personal_flagship: true, enterprise: true, enterprise_pro: true, enterprise_pro_max: true },
      { name: '质量管理', free: false, personal_pro: false, personal_advanced: '基础', personal_flagship: true, enterprise: true, enterprise_pro: true, enterprise_pro_max: true },
      { name: '焊材管理', free: false, personal_pro: false, personal_advanced: false, personal_flagship: true, enterprise: true, enterprise_pro: true, enterprise_pro_max: true },
      { name: '焊工管理', free: false, personal_pro: false, personal_advanced: false, personal_flagship: true, enterprise: true, enterprise_pro: true, enterprise_pro_max: true },
      { name: '员工管理', free: false, personal_pro: false, personal_advanced: false, personal_flagship: false, enterprise: '20人', enterprise_pro: '无限', enterprise_pro_max: '无限' },
      { name: '多工厂管理', free: false, personal_pro: false, personal_advanced: false, personal_flagship: false, enterprise: '3个', enterprise_pro: '无限', enterprise_pro_max: '无限' },
      { name: 'API访问', free: false, personal_pro: '基础', personal_advanced: '完整', personal_flagship: '完整', enterprise: '企业版', enterprise_pro: '企业版', enterprise_pro_max: '完全定制' },
      { name: '技术支持', free: '社区', personal_pro: '邮件', personal_advanced: '优先', personal_flagship: '专属', enterprise: '7x24', enterprise_pro: '企业专属', enterprise_pro_max: '战略支持' },
      { name: '存储空间', free: '10GB', personal_pro: '50GB', personal_advanced: '100GB', personal_flagship: '500GB', enterprise: '1TB', enterprise_pro: '10TB', enterprise_pro_max: '定制' },
    ]
    return features
  }

  // 获取当前套餐信息
  const getCurrentPlanInfo = () => {
    return membershipPlans.find(plan =>
      plan.id === userMembership.currentPlan ||
      plan.type === userMembership.currentPlan
    )
  }

  // 处理卡片聚焦
  const handleCardFocus = (planId: string) => {
    setFocusedPlan(planId)
    setSelectedPlan(planId)
  }

  // 获取价格预览
  const fetchPricePreview = async (planId: string, cycle: 'monthly' | 'quarterly' | 'yearly') => {
    setPriceLoading(true)
    try {
      const response = await apiService.post('/payments/preview-price', {
        plan_id: planId,
        billing_cycle: cycle
      })

      console.log('Price preview response:', response)

      // 后端返回 { success: true, data: { actual_price: ... } }
      // apiService 包装后变成 { success: true, data: { success: true, data: { actual_price: ... } } }
      // 所以需要访问 response.data.data
      if (response.success && response.data) {
        const priceData = response.data.data || response.data
        console.log('Price data:', priceData)
        setPricePreview(priceData)
      } else {
        message.error('获取价格信息失败')
        setPricePreview(null)
      }
    } catch (error) {
      console.error('Failed to fetch price preview:', error)
      setPricePreview(null)
    } finally {
      setPriceLoading(false)
    }
  }

  // 处理升级
  const handleUpgrade = (planId: string) => {
    setSelectedPlan(planId)
    setCurrentStep(0)
    setBillingCycle('monthly') // 重置为月付
    setPricePreview(null) // 重置价格预览
    setUpgradeModalVisible(true)
    // 获取价格预览
    fetchPricePreview(planId, 'monthly')
  }

  // 当计费周期改变时，重新获取价格预览
  useEffect(() => {
    if (selectedPlan && upgradeModalVisible) {
      fetchPricePreview(selectedPlan, billingCycle)
    }
  }, [billingCycle])

  // 处理支付
  const handlePayment = async () => {
    if (!agreeTerms) {
      message.error('请同意服务条款')
      return
    }

    setLoading(true)
    try {
      // 创建支付订单
      const response = await apiService.post('/payments/create', {
        plan_id: selectedPlan,
        billing_cycle: billingCycle,
        payment_method: paymentMethod,
        auto_renew: true
      })

      console.log('Payment create response:', response)

      if (response.success && response.data) {
        // 后端返回 { success: true, data: { transaction_id: ... } }
        // apiService 包装后变成 { success: true, data: { success: true, data: { transaction_id: ... } } }
        const paymentData = response.data.data || response.data
        console.log('Payment data:', paymentData)

        // 关闭支付确认弹窗
        setPaymentModalVisible(false)

        // 设置手动支付信息
        const selectedPlanInfo = membershipPlans.find(p => p.id === selectedPlan)
        setCurrentOrderId(paymentData.transaction_id)  // 使用 transaction_id 而不是 order_id
        setCurrentAmount(paymentData.amount)
        setCurrentPlanName(selectedPlanInfo?.name || selectedPlan)

        // 显示手动支付弹窗
        setManualPaymentVisible(true)
      } else {
        message.error(response.message || '创建订单失败')
      }
    } catch (error) {
      console.error('Payment failed:', error)
      message.error('创建订单失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const nextStep = () => {
    setCurrentStep(currentStep + 1)
  }

  const prevStep = () => {
    setCurrentStep(currentStep - 1)
  }

  const currentPlanInfo = getCurrentPlanInfo()
  const comparisonData = getComparisonData()

  // 显示加载状态
  if (plansLoading) {
    return (
      <div className="page-container flex justify-center items-center" style={{ height: '400px' }}>
        <div className="text-center">
          <Spin size="large" />
          <div className="mt-4">
            <Text type="secondary">加载订阅计划中...</Text>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <style>{cardStyles}</style>
      <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <Title level={2} className="mb-2">会员升级</Title>
          <Text type="secondary">选择适合的会员套餐，解锁更多功能</Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleRefreshUserInfo}
          loading={refreshing}
          type="default"
        >
          刷新信息
        </Button>
      </div>

      {/* 当前会员状态 */}
      <Card className="mb-6">
        <Row gutter={16} align="middle">
          <Col xs={24} md={12}>
            <Space size="large">
              <Avatar size={64} style={{ backgroundColor: currentPlanInfo?.color }}>
                {currentPlanInfo?.icon}
              </Avatar>
              <div>
                <Title level={3} className="mb-1">{currentPlanInfo?.name}</Title>
                {userMembership.currentPlan === 'free' || userMembership.currentPlan === 'personal_free' ? (
                  <Text type="secondary">永久有效</Text>
                ) : (
                  <>
                    <Text type="secondary">
                      到期时间：
                      {userMembership.expiryDate === '未订阅'
                        ? userMembership.expiryDate
                        : (userMembership.expiryDate === '永久有效'
                          ? userMembership.expiryDate
                          : new Date(userMembership.expiryDate).toLocaleDateString('zh-CN'))}
                    </Text>
                    {userMembership.expiryDate !== '未订阅' && userMembership.expiryDate !== '永久有效' && (
                      <div className="mt-2">
                        <Tag color={userMembership.remainingDays > 30 ? 'blue' : (userMembership.remainingDays > 7 ? 'orange' : 'red')}>
                          剩余 {userMembership.remainingDays} 天
                        </Tag>
                      </div>
                    )}
                  </>
                )}
              </div>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <div className="text-right">
              <Statistic
                title="当前功能"
                value={userMembership.features.length}
                suffix={`/ ${membershipPlans.find(p => p.id === 'enterprise')?.features.length}`}
              />
            </div>
          </Col>
        </Row>
        <Divider />
        <div>
          <Text strong>当前可用功能：</Text>
          <div className="mt-2">
            <Space wrap>
              {userMembership.features.map((feature, index) => (
                <Tag key={index} color="green" icon={<CheckOutlined />}>
                  {feature}
                </Tag>
              ))}
            </Space>
          </div>
        </div>
      </Card>


      {/* 会员套餐 */}
      <div className="mb-6">
        <Title level={3} className="text-center mb-6">选择会员套餐</Title>
        <div className="overflow-x-auto pb-4 px-4">
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '16px',
            minWidth: '1900px'
          }}>
            {membershipPlans.map((plan) => {
              const cardClassNames = [
                'membership-card',
                plan.recommended ? 'recommended-card' : '',
                focusedPlan === plan.id ? 'focused' : '',
                plan.id === 'free' ? 'free-card' : '',
                plan.id === 'personal_pro' ? 'pro-card' : '',
                plan.id === 'personal_advanced' ? 'advanced-card' : '',
                plan.id === 'personal_flagship' ? 'flagship-card' : '',
                plan.id === 'enterprise' ? 'enterprise-card' : '',
                plan.id === 'enterprise_pro' ? 'enterprise-pro-card' : '',
                plan.id === 'enterprise_pro_max' ? 'enterprise-max-card' : ''
              ].filter(Boolean).join(' ')

              return (
                <div key={plan.id} style={{
                  height: '740px',
                  display: 'flex',
                  flexDirection: 'column',
                  paddingTop: '6px'
                }}>
                  <Card
                    hoverable
                    className={cardClassNames}
                    style={{
                      position: 'relative',
                      height: '100%',
                      borderRadius: '16px',
                      transition: 'all 0.3s ease',
                      cursor: plan.id === currentPlan ? 'default' : 'pointer'
                    }}
                    onClick={() => plan.id !== currentPlan ? handleUpgrade(plan.id) : null}
                  >
                    {/* 右上角标签 */}
                    {plan.recommended && (
                      <div className="recommended-badge">
                        热门推荐
                      </div>
                    )}

                    {plan.id === currentPlan && (
                      <div style={{
                        position: 'absolute',
                        top: '-1px',
                        left: '16px',
                        background: '#52c41a',
                        color: 'white',
                        padding: '4px 12px',
                        borderRadius: '0 0 8px 8px',
                        fontSize: '12px',
                        fontWeight: 600,
                        zIndex: 1,
                        boxShadow: '0 2px 8px rgba(82, 196, 26, 0.3)'
                      }}>
                        当前套餐
                      </div>
                    )}

                    {/* 卡片头部 */}
                    <div className="text-center pb-4" style={{ borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                      <div
                        className="inline-flex items-center justify-center w-14 h-14 rounded-full mb-3"
                        style={{ backgroundColor: plan.color }}
                      >
                        <div style={{ color: 'white', fontSize: '24px' }}>
                          {plan.icon}
                        </div>
                      </div>
                      <Title level={5} className="mb-2" style={{ color: plan.color, fontWeight: 600, margin: 0, fontSize: '14px' }}>
                        {plan.name}
                      </Title>

                      {/* 价格显示 */}
                      {plan.prices.monthly > 0 ? (
                        <div>
                          <div className="flex items-baseline justify-center gap-1">
                            <Text strong style={{ fontSize: 28, color: plan.color, lineHeight: 1 }}>
                              ¥{plan.prices.monthly.toLocaleString()}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              /月起
                            </Text>
                          </div>
                          <Text type="secondary" style={{ fontSize: 9 }}>
                            季付9折，年付8.3折
                          </Text>
                        </div>
                      ) : (
                        <div>
                          <Text strong style={{ fontSize: 24, color: plan.color }}>
                            免费
                          </Text>
                        </div>
                      )}
                    </div>

                    {/* 功能列表 */}
                    <div style={{ flex: 1, padding: '16px 0' }}>
                      <Space direction="vertical" className="w-full" size="small">
                        {Array.isArray(plan.features) && plan.features.map((feature, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <CheckOutlined className="mt-1 flex-shrink-0" style={{ fontSize: '11px', color: '#52c41a' }} />
                            <Text style={{ fontSize: '11px', lineHeight: '1.5' }}>{feature}</Text>
                          </div>
                        ))}
                      </Space>
                    </div>

                    {/* 限制说明 */}
                    <div style={{ padding: '16px 0' }}>
                      {plan.limitations.length > 0 && (
                        <Space direction="vertical" className="w-full" size="small">
                          {plan.limitations.slice(0, 2).map((limitation, index) => (
                            <div key={index} className="flex items-start gap-2">
                              <Text type="secondary" style={{ fontSize: '9px', marginTop: '2px' }}>•</Text>
                              <Text type="secondary" style={{ fontSize: '9px', lineHeight: '1.4' }}>{limitation}</Text>
                            </div>
                          ))}
                          {plan.limitations.length > 2 && (
                            <Text type="secondary" style={{ fontSize: '9px' }}>
                              共 {plan.limitations.length} 项限制
                            </Text>
                          )}
                        </Space>
                      )}
                    </div>
                  </Card>
                </div>
              )
            })}
          </div>
        </div>
      </div>


      {/* 升级流程弹窗 */}
      <Modal
        title="升级会员"
        open={upgradeModalVisible}
        onCancel={() => setUpgradeModalVisible(false)}
        footer={null}
        width={800}
      >
        <Steps current={currentStep} className="mb-6">
          <Step title="选择套餐" />
          <Step title="确认信息" />
          <Step title="选择支付" />
          <Step title="完成升级" />
        </Steps>

        {currentStep === 0 && (
          <div>
            <Title level={4}>确认升级套餐</Title>
            {selectedPlan && (
              <Card>
                <Row gutter={16} align="middle">
                  <Col span={4}>
                    <Avatar size={48} style={{ backgroundColor: membershipPlans.find(p => p.id === selectedPlan)?.color }}>
                      {membershipPlans.find(p => p.id === selectedPlan)?.icon}
                    </Avatar>
                  </Col>
                  <Col span={20}>
                    <Title level={4}>{membershipPlans.find(p => p.id === selectedPlan)?.name}</Title>

                    {/* 计费周期选择 */}
                    <div className="mt-3">
                      <Text strong>选择计费周期：</Text>
                      <Radio.Group
                        value={billingCycle}
                        onChange={(e) => setBillingCycle(e.target.value)}
                        size="small"
                        className="ml-3"
                      >
                        <Radio.Button value="monthly">
                          月付 ¥{membershipPlans.find(p => p.id === selectedPlan)?.prices.monthly.toLocaleString()}
                        </Radio.Button>
                        <Radio.Button value="quarterly">
                          季付 ¥{membershipPlans.find(p => p.id === selectedPlan)?.prices.quarterly.toLocaleString()} (9折)
                        </Radio.Button>
                        <Radio.Button value="yearly">
                          年付 ¥{membershipPlans.find(p => p.id === selectedPlan)?.prices.yearly.toLocaleString()} (8.3折)
                        </Radio.Button>
                      </Radio.Group>
                    </div>

                    {/* 价格信息 */}
                    {priceLoading ? (
                      <div className="mt-3">
                        <Spin size="small" /> <Text type="secondary">正在计算价格...</Text>
                      </div>
                    ) : pricePreview && pricePreview.is_upgrade && pricePreview.discount > 0 ? (
                      <div className="mt-3">
                        <Alert
                          message={
                            <div>
                              <div>套餐原价：¥{pricePreview.original_price.toLocaleString()}</div>
                              <div style={{ color: '#52c41a' }}>剩余价值抵扣：-¥{pricePreview.discount.toLocaleString()}</div>
                              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                                实际支付：¥{pricePreview.actual_price.toLocaleString()}
                              </div>
                            </div>
                          }
                          type="success"
                          showIcon
                          icon={<GiftOutlined />}
                        />
                      </div>
                    ) : pricePreview ? (
                      <div className="mt-3">
                        <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                          支付金额：¥{pricePreview.actual_price.toLocaleString()}
                        </Text>
                      </div>
                    ) : null}

                    <div className="mt-2">
                      <Text type="secondary">
                        将在 {dayjs().add(billingCycle === 'monthly' ? 1 : billingCycle === 'quarterly' ? 3 : 12, 'month').format('YYYY-MM-DD')} 到期
                      </Text>
                    </div>
                  </Col>
                </Row>
              </Card>
            )}
            <div className="mt-4 text-right">
              <Space>
                <Button onClick={() => setUpgradeModalVisible(false)}>取消</Button>
                <Button type="primary" onClick={nextStep}>
                  下一步 <RightOutlined />
                </Button>
              </Space>
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <Title level={4}>确认升级信息</Title>
            <Alert
              message="升级确认"
              description={`您将从 ${currentPlanInfo?.name} 升级到 ${membershipPlans.find(p => p.id === selectedPlan)?.name}，升级后将获得更多功能权限。`}
              type="info"
              showIcon
              className="mb-4"
            />

            <List
              header="升级后将获得以下功能："
              dataSource={membershipPlans.find(p => p.id === selectedPlan)?.features || []}
              renderItem={(item) => (
                <List.Item>
                  <CheckOutlined className="text-green-500 mr-2" />
                  {item}
                </List.Item>
              )}
            />

            <div className="mt-4 text-right">
              <Space>
                <Button onClick={prevStep}>
                  <RightOutlined rotate={180} /> 上一步
                </Button>
                <Button type="primary" onClick={nextStep}>
                  下一步 <RightOutlined />
                </Button>
              </Space>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div>
            <Title level={4}>选择支付方式</Title>
            <Radio.Group value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="w-full">
              <Space direction="vertical" className="w-full" size="middle">
                <Radio value="alipay" className="w-full">
                  <Card
                    className={`w-full cursor-pointer transition-all ${paymentMethod === 'alipay' ? 'border-blue-500 shadow-md' : 'hover:shadow-md'}`}
                    style={{
                      borderRadius: '12px',
                      border: paymentMethod === 'alipay' ? '2px solid #1677ff' : '1px solid #d9d9d9'
                    }}
                  >
                    <Row align="middle" gutter={16}>
                      <Col>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '12px',
                          background: 'linear-gradient(135deg, #1677ff, #40a9ff)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '20px',
                          fontWeight: 'bold'
                        }}>
                          支
                        </div>
                      </Col>
                      <Col flex="auto">
                        <div>
                          <Text strong style={{ fontSize: '16px', color: '#262626' }}>支付宝</Text>
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>使用支付宝快捷支付</Text>
                          </div>
                        </div>
                      </Col>
                      <Col>
                        <CreditCardOutlined style={{ fontSize: '20px', color: '#1677ff' }} />
                      </Col>
                    </Row>
                  </Card>
                </Radio>

                <Radio value="wechat" className="w-full">
                  <Card
                    className={`w-full cursor-pointer transition-all ${paymentMethod === 'wechat' ? 'border-green-500 shadow-md' : 'hover:shadow-md'}`}
                    style={{
                      borderRadius: '12px',
                      border: paymentMethod === 'wechat' ? '2px solid #07c160' : '1px solid #d9d9d9'
                    }}
                  >
                    <Row align="middle" gutter={16}>
                      <Col>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '12px',
                          background: 'linear-gradient(135deg, #07c160, #38d9a9)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '20px',
                          fontWeight: 'bold'
                        }}>
                          微
                        </div>
                      </Col>
                      <Col flex="auto">
                        <div>
                          <Text strong style={{ fontSize: '16px', color: '#262626' }}>微信支付</Text>
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>使用微信扫码支付</Text>
                          </div>
                        </div>
                      </Col>
                      <Col>
                        <WechatOutlined style={{ fontSize: '20px', color: '#07c160' }} />
                      </Col>
                    </Row>
                  </Card>
                </Radio>

                <Radio value="bank" className="w-full">
                  <Card
                    className={`w-full cursor-pointer transition-all ${paymentMethod === 'bank' ? 'border-orange-500 shadow-md' : 'hover:shadow-md'}`}
                    style={{
                      borderRadius: '12px',
                      border: paymentMethod === 'bank' ? '2px solid #ff6a00' : '1px solid #d9d9d9'
                    }}
                  >
                    <Row align="middle" gutter={16}>
                      <Col>
                        <div style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '12px',
                          background: 'linear-gradient(135deg, #ff6a00, #ff9500)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '20px',
                          fontWeight: 'bold'
                        }}>
                          银
                        </div>
                      </Col>
                      <Col flex="auto">
                        <div>
                          <Text strong style={{ fontSize: '16px', color: '#262626' }}>银行转账</Text>
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>对公账户转账支付</Text>
                          </div>
                        </div>
                      </Col>
                      <Col>
                        <BankOutlined style={{ fontSize: '20px', color: '#ff6a00' }} />
                      </Col>
                    </Row>
                  </Card>
                </Radio>
              </Space>
            </Radio.Group>

            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <Checkbox checked={agreeTerms} onChange={(e) => setAgreeTerms(e.target.checked)}>
                <Text style={{ fontSize: '14px' }}>
                  我已阅读并同意 <a href="#" onClick={(e) => e.preventDefault()} style={{ color: '#1677ff' }}>服务条款</a> 和 <a href="#" onClick={(e) => e.preventDefault()} style={{ color: '#1677ff' }}>隐私政策</a>
                </Text>
              </Checkbox>
            </div>

            <div className="mt-6 text-right">
              <Space>
                <Button onClick={prevStep} size="large">
                  <RightOutlined rotate={180} /> 上一步
                </Button>
                <Button
                  type="primary"
                  onClick={() => setPaymentModalVisible(true)}
                  disabled={!agreeTerms}
                  size="large"
                  style={{
                    background: 'linear-gradient(135deg, #1677ff, #40a9ff)',
                    border: 'none',
                    borderRadius: '8px',
                    height: '44px',
                    paddingLeft: '24px',
                    paddingRight: '24px'
                  }}
                >
                  确认支付
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>

      {/* 支付确认弹窗 */}
      <Modal
        title="确认支付"
        open={paymentModalVisible}
        onCancel={() => setPaymentModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setPaymentModalVisible(false)}>
            取消
          </Button>,
          <Button key="pay" type="primary" loading={loading} onClick={handlePayment}>
            确认支付 ¥{pricePreview ? pricePreview.actual_price.toLocaleString() : membershipPlans.find(p => p.id === selectedPlan)?.prices[billingCycle].toLocaleString()}
          </Button>,
        ]}
      >
        {priceLoading ? (
          <div className="text-center py-4">
            <Spin />
            <div className="mt-2">
              <Text type="secondary">正在计算价格...</Text>
            </div>
          </div>
        ) : pricePreview && pricePreview.is_upgrade && pricePreview.discount > 0 ? (
          <div>
            <Alert
              message="升级补差价"
              description={
                <div>
                  <div>套餐：{membershipPlans.find(p => p.id === selectedPlan)?.name}</div>
                  <div>计费周期：{billingCycle === 'monthly' ? '月付' : billingCycle === 'quarterly' ? '季付' : '年付'}</div>
                  <div>支付方式：{paymentMethod === 'alipay' ? '支付宝' : paymentMethod === 'wechat' ? '微信支付' : '银行转账'}</div>
                  <div className="mt-2" style={{ borderTop: '1px dashed #d9d9d9', paddingTop: '8px' }}>
                    <div>套餐原价：¥{pricePreview.original_price.toLocaleString()}</div>
                    <div style={{ color: '#52c41a' }}>剩余价值抵扣：-¥{pricePreview.discount.toLocaleString()}</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff', marginTop: '4px' }}>
                      实际支付：¥{pricePreview.actual_price.toLocaleString()}
                    </div>
                  </div>
                </div>
              }
              type="info"
              showIcon
            />
            <div className="mt-3">
              <Text type="secondary" style={{ fontSize: '12px' }}>
                💡 您当前套餐的剩余时间价值将自动抵扣新套餐费用
              </Text>
            </div>
          </div>
        ) : (
          <Alert
            message="支付确认"
            description={
              <div>
                <div>套餐：{membershipPlans.find(p => p.id === selectedPlan)?.name}</div>
                <div>金额：¥{pricePreview ? pricePreview.actual_price.toLocaleString() : membershipPlans.find(p => p.id === selectedPlan)?.prices[billingCycle].toLocaleString()}/{billingCycle === 'monthly' ? '月' : billingCycle === 'quarterly' ? '季' : '年'}</div>
                <div>支付方式：{paymentMethod === 'alipay' ? '支付宝' : paymentMethod === 'wechat' ? '微信支付' : '银行转账'}</div>
              </div>
            }
            type="warning"
            showIcon
          />
        )}
      </Modal>

      {/* 手动支付弹窗 */}
      <ManualPaymentModal
        visible={manualPaymentVisible}
        orderId={currentOrderId}
        amount={currentAmount}
        planName={currentPlanName}
        paymentMethod={paymentMethod as 'alipay' | 'wechat'}
        onSuccess={() => {
          setManualPaymentVisible(false)
          setUpgradeModalVisible(false)
          message.success('支付凭证已提交，请等待管理员确认')
          // 跳转到订单页面
          navigate('/membership/history')
        }}
        onCancel={() => setManualPaymentVisible(false)}
      />
      </div>
    </>
  )
}

export default MembershipUpgrade