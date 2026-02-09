import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Avatar,
  Button,
  Space,
  Statistic,
  Progress,
  Tag,
  Badge,
  List,
  Alert,
  Divider,
  Upload,
  message,
  Form,
  Input,
  Modal,
} from 'antd'
import {
  UserOutlined,
  EditOutlined,
  CrownOutlined,
  TrophyOutlined,
  CheckCircleOutlined,
  StarOutlined,
  FireOutlined,
  ThunderboltOutlined,
  TeamOutlined,
  FileTextOutlined,
  BarChartOutlined,
    DeleteOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { useAuthStore } from '@/store/authStore'
import { workspaceService } from '@/services/workspace'
import enterpriseService from '@/services/enterprise'
import { triggerWorkspaceSwitch } from '@/contexts/MembershipContext'
import { useMembership } from '@/contexts/MembershipContext'

const { Title, Text } = Typography


interface Workspace {
  id: string
  name: string
  type: 'personal' | 'enterprise'
  status: 'active' | 'inactive'
  member_count: number
  created_at: string
  role: string
}

const PersonalCenter: React.FC = () => {
  const navigate = useNavigate()
  const { user, updateProfile, refreshUserInfo } = useAuthStore()
  const { membershipInfo } = useMembership()
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null)
  const [form] = Form.useForm()

  // 加载工作区数据
  useEffect(() => {
    loadWorkspaces()
  }, [])

  const loadWorkspaces = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) {
        message.error('请先登录')
        return
      }

      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const response = await fetch(`${apiBaseUrl}/workspace/workspaces`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const apiResponse = await response.json()

      // 处理API响应格式 - 后端直接返回数组
      let workspaceData: any[] = []
      if (Array.isArray(apiResponse)) {
        // 直接数组格式
        workspaceData = apiResponse
      } else if (apiResponse?.success && apiResponse?.data) {
        // 兼容ApiResponse格式
        workspaceData = Array.isArray(apiResponse.data) ? apiResponse.data : [apiResponse.data]
      }

      // 转换API数据为前端格式
      const formattedWorkspaceData: Workspace[] = workspaceData.map((item: any) => ({
        id: item.id,
        name: item.name,
        type: item.type,
        status: item.status || 'active',
        member_count: item.member_count || 1,
        created_at: item.created_at,
        role: item.role,
        department: item.department,
        description: item.description || '',
        quota_info: item.quota_info || {},
        membership_tier: item.membership_tier || 'personal_free'
      }))

      // 去重处理：基于工作区ID合并相同的工作区，收集所有角色信息
      const workspaceMap = new Map<string, {
        workspace: Workspace,
        roles: string[],
        departments: string[],
        membership_tiers: string[]
      }>()

      formattedWorkspaceData.forEach(workspace => {
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

      // 转换为包含合并角色信息的工作区数组
      const uniqueWorkspaces = Array.from(workspaceMap.values()).map(({
        workspace,
        roles,
        departments,
        membership_tiers
      }) => {
        // 重新计算成员数量 - 基于user_id去重
        const uniqueUsers = new Set<string>()
        workspaceData.forEach(w => {
          if (w.id === workspace.id) {
            uniqueUsers.add(w.user_id)
          }
        })

        return {
          ...workspace,
          all_roles: roles,
          all_departments: departments,
          all_membership_tiers: membership_tiers,
          // 重新计算成员数量
          member_count: uniqueUsers.size
        }
      })

      setWorkspaces(uniqueWorkspaces as any)

      // 异步更新企业工作区的真实成员数
      uniqueWorkspaces.forEach(async (workspace) => {
        if (workspace.type === 'enterprise') {
          try {
            const employeeResponse = await enterpriseService.getEmployees({ page: 1, page_size: 100 })

            let employees = []
            if (employeeResponse?.data?.employees) {
              // 标准格式：data.employees
              employees = employeeResponse.data.employees
            } else if (employeeResponse?.data && Array.isArray(employeeResponse.data)) {
              // 直接数组格式：data就是员工数组
              employees = employeeResponse.data
            } else if (employeeResponse?.success && employeeResponse?.data?.data?.items) {
              // 嵌套格式：data.data.items
              employees = employeeResponse.data.data.items
            } else if (employeeResponse?.success && employeeResponse?.data) {
              // 其他格式，尝试从data中提取各种可能的字段
              const data = employeeResponse.data
              // 尝试所有可能的员工数据字段
              const possibleFields = ['employees', 'items', 'list', 'data', 'results', 'users', 'staff']
              for (const field of possibleFields) {
                if (data[field] && Array.isArray(data[field])) {
                  employees = data[field]
                  break
                }
              }
            }

            if (employees.length > 0) {
              const uniqueUserIds = new Set(employees.map((emp: any) => emp.user_id))

              // 更新工作区的成员数量
              setWorkspaces(prev => {
                const updated = prev.map(w =>
                  w.id === workspace.id
                    ? { ...w, member_count: uniqueUserIds.size }
                    : w
                )
                return updated
              })
            }
          } catch (error) {
            console.error('获取企业成员数失败:', error)
          }
        }
      })

      // 优先使用本地存储的当前工作区
      const storedWorkspace = workspaceService.getCurrentWorkspaceFromStorage()

      if (storedWorkspace) {
        // 验证存储的工作区是否在当前工作区列表中
        const isValidWorkspace = formattedWorkspaceData.some(w => w.id === storedWorkspace.id)

        if (isValidWorkspace) {
          setCurrentWorkspace(storedWorkspace)
          // 不再覆盖本地存储，避免与WorkspaceSwitcher冲突
        } else {
          // 存储的工作区无效，使用活跃工作区或第一个
          const activeWorkspace = formattedWorkspaceData.find(w => w.status === 'active') || formattedWorkspaceData[0]
          setCurrentWorkspace(activeWorkspace)
          workspaceService.saveCurrentWorkspaceToStorage(activeWorkspace)
        }
      } else {
        // 没有本地存储，使用活跃工作区或第一个
        const activeWorkspace = formattedWorkspaceData.find(w => w.status === 'active') || formattedWorkspaceData[0]
        setCurrentWorkspace(activeWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(activeWorkspace)
      }
    } catch (error) {
      console.error('Failed to load workspaces:', error)
      message.error('加载工作区失败: ' + (error as Error).message)

      // 如果API失败，提供空数组而不是模拟数据
      setWorkspaces([])
      setCurrentWorkspace(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSwitchWorkspace = async (workspace: Workspace) => {
    try {
      // 使用workspaceService保持一致性
      const response = await workspaceService.switchWorkspace({
        workspace_id: workspace.id
      })

      // 处理不同的响应格式
      let newWorkspace: Workspace | null = null

      if (response?.success && response?.data?.workspace) {
        // ApiResponse格式
        newWorkspace = response.data.workspace
      } else if (response?.success && response?.workspace) {
        // 直接的WorkspaceSwitchResponse格式
        newWorkspace = response.workspace
      } else if (response?.workspace) {
        // 简化的响应格式
        newWorkspace = response.workspace
      }

      if (newWorkspace) {
        // 更新当前工作区
        setCurrentWorkspace(newWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(newWorkspace)

        // 触发会员等级更新
        if (user) {
          triggerWorkspaceSwitch(newWorkspace, user.membership_type)
        }

        message.success(`已切换到 ${workspaceService.getWorkspaceDisplayName(newWorkspace)}`)

        // 刷新页面数据
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      } else {
        message.error('切换工作区失败：响应格式错误')
      }
    } catch (error) {
      console.error('Failed to switch workspace:', error)
      message.error('切换工作区失败: ' + (error as Error).message)
    }
  }

  
  const handleDeleteWorkspace = (workspaceId: string) => {
    Modal.confirm({
      title: '删除工作区',
      content: '确定要删除此工作区吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token')
          if (!token) {
            message.error('请先登录')
            return
          }

          const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
          const response = await fetch(`${apiBaseUrl}/workspace/${workspaceId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const updatedWorkspaces = workspaces.filter(w => w.id !== workspaceId)
          setWorkspaces(updatedWorkspaces)
          if (currentWorkspace?.id === workspaceId) {
            setCurrentWorkspace(updatedWorkspaces[0] || null)
          }
          message.success('工作区删除成功')
        } catch (error) {
          console.error('Failed to delete workspace:', error)
          message.error('删除工作区失败: ' + (error as Error).message)
        }
      }
    })
  }

  const handleEditProfile = () => {
    form.setFieldsValue({
      username: user?.username,
      email: user?.email,
      full_name: user?.full_name,
    })
    setEditModalVisible(true)
  }

  const handleSaveProfile = async (values: any) => {
    try {
      setLoading(true)
      const success = await updateProfile(values)

      if (success) {
        message.success('个人信息保存成功')
        setEditModalVisible(false)
        // 刷新用户信息
        await refreshUserInfo()
      } else {
        message.error('保存失败')
      }
    } catch (error) {
      console.error('保存个人信息失败:', error)
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取会员等级信息
  const getMembershipInfo = (tier: string) => {
    const tierInfo: Record<string, any> = {
      free: {
        name: '免费版',
        color: '#8c8c8c',
        icon: <UserOutlined />,
        features: ['基础WPS管理', '10个文档限制', '社区支持'],
        nextTier: 'personal_pro',
        nextTierName: '专业版',
        upgradePrice: '¥19/月',
      },
      personal_pro: {
        name: '专业版',
        color: '#1890ff',
        icon: <StarOutlined />,
        features: ['完整WPS/PQR功能', '30个文档限制', '邮件支持', '数据导出'],
        nextTier: 'personal_advanced',
        nextTierName: '高级版',
        upgradePrice: '¥49/月',
      },
      personal_advanced: {
        name: '高级版',
        color: '#52c41a',
        icon: <CrownOutlined />,
        features: ['高级功能', '50个文档限制', '优先支持', '高级分析'],
        nextTier: 'personal_flagship',
        nextTierName: '旗舰版',
        upgradePrice: '¥99/月',
      },
      personal_flagship: {
        name: '旗舰版',
        color: '#722ed1',
        icon: <TrophyOutlined />,
        features: ['全部功能', '100个文档限制', '专属客服', '定制服务'],
        nextTier: null,
        nextTierName: null,
        upgradePrice: null,
      },
    }
    return tierInfo[tier] || tierInfo.free
  }

  // 使用 membership context 来获取基于当前工作区的会员信息

  // 获取使用统计
  const getUsageStats = () => {
    const stats = {
      wps: { used: 12, limit: 30, percentage: 40 },
      pqr: { used: 8, limit: 30, percentage: 27 },
      storage: { used: 125, limit: 1024, percentage: 12 },
      api: { used: 850, limit: 10000, percentage: 8.5 },
    }
    return stats
  }

  const usageStats = getUsageStats()

  // 渲染个人信息部分
  const renderProfileInfo = () => (
    <Card title="个人信息" extra={
      <Button
        type="primary"
        icon={<EditOutlined />}
        onClick={handleEditProfile}
        size="small"
      >
        编辑
      </Button>
    }>
      <div className="text-center mb-4">
        <Upload
          name="avatar"
          listType="picture-card"
          className="avatar-uploader"
          showUploadList={false}
          action="/api/upload/avatar"
          onChange={(info) => {
            if (info.file.status === 'done') {
              message.success('头像上传成功')
            } else if (info.file.status === 'error') {
              message.error('头像上传失败')
            }
          }}
        >
          <Avatar
            size={80}
            src={user?.avatar_url}
            icon={<UserOutlined />}
            className="cursor-pointer"
          />
        </Upload>
        <Title level={4} className="mt-3 mb-1">
          {user?.full_name || user?.username}
        </Title>
        {membershipInfo ? (
          <Tag color={membershipInfo.color} icon={membershipInfo.isEnterprise ? <CrownOutlined /> : <StarOutlined />}>
            {membershipInfo.displayName}
            {membershipInfo.isEnterprise && (
              <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.8 }}>
                (企业)
              </span>
            )}
          </Tag>
        ) : (
          <Tag color="default">
            加载中...
          </Tag>
        )}
      </div>

      <Space direction="vertical" size="small" className="w-full">
        <div>
          <Text type="secondary" className="text-xs">用户名</Text>
          <div className="font-medium">{user?.username}</div>
        </div>
        <div>
          <Text type="secondary" className="text-xs">邮箱</Text>
          <div className="font-medium text-truncate">{user?.email}</div>
        </div>
        <div>
          <Text type="secondary" className="text-xs">注册时间</Text>
          <div className="font-medium">
            {user?.created_at ? dayjs(user.created_at).format('YYYY-MM-DD') : '未知'}
          </div>
        </div>
        <div>
          <Text type="secondary" className="text-xs">最后登录</Text>
          <div className="font-medium">
            {user?.last_login_at ? dayjs(user.last_login_at).format('MM-DD HH:mm') : '未知'}
          </div>
        </div>
      </Space>

      <Divider />

      {/* 使用统计 */}
      <div className="space-y-3">
        <Title level={5}>使用统计</Title>
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <Statistic
              title="WPS文档"
              value={usageStats.wps.used}
              suffix={`/ ${usageStats.wps.limit}`}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '16px' }}
            />
            <Progress
              percent={usageStats.wps.percentage}
              size="small"
              className="mt-1"
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="PQR记录"
              value={usageStats.pqr.used}
              suffix={`/ ${usageStats.pqr.limit}`}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '16px' }}
            />
            <Progress
              percent={usageStats.pqr.percentage}
              size="small"
              className="mt-1"
              strokeColor="#52c41a"
            />
          </Col>
        </Row>
        <Row gutter={[16, 8]} className="mt-2">
          <Col span={12}>
            <Statistic
              title="存储空间"
              value={usageStats.storage.used}
              suffix="MB"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#fa8c16', fontSize: '16px' }}
            />
            <Progress
              percent={usageStats.storage.percentage}
              size="small"
              className="mt-1"
              strokeColor="#fa8c16"
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="API调用"
              value={usageStats.api.used}
              suffix={`/ ${usageStats.api.limit}`}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#722ed1', fontSize: '16px' }}
            />
            <Progress
              percent={usageStats.api.percentage}
              size="small"
              className="mt-1"
              strokeColor="#722ed1"
            />
          </Col>
        </Row>
      </div>

      <Divider />

      {/* 会员权益 */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <Title level={5} className="mb-0">会员权益</Title>
          {membershipInfo.nextTier && (
            <Button type="primary" size="small">
              升级到{membershipInfo.nextTierName}
            </Button>
          )}
        </div>
        <div className="space-y-2">
          {membershipInfo?.features?.map((feature: string, index: number) => (
            <div key={index} className="flex items-center">
              <CheckCircleOutlined className="text-green-500 mr-2" />
              <Text style={{ fontSize: '12px' }}>{feature}</Text>
            </div>
          ))}
        </div>
        {membershipInfo.nextTier && (
          <Alert
            message={`升级到${membershipInfo.nextTierName}只需 ${membershipInfo.upgradePrice}`}
            type="info"
            showIcon
            className="mt-3"
            style={{ padding: '8px 12px' }}
          />
        )}
      </div>
    </Card>
  )

  // 渲染工作区管理部分
  const renderWorkspaceManagement = () => (
    <Card
      title="工作区管理"
    >
      {/* 当前工作区信息 */}
      {currentWorkspace && (
        <Alert
          message={
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">当前工作区: {currentWorkspace.name}</div>
                <div className="text-sm text-gray-500">
                  类型: {currentWorkspace.type === 'enterprise' ? '企业' : '个人'} |
                  成员: {currentWorkspace.member_count}人 |
                  角色: {currentWorkspace.role}
                </div>
              </div>
              <Tag color={currentWorkspace.status === 'active' ? 'green' : 'red'}>
                {currentWorkspace.status === 'active' ? '活跃' : '未激活'}
              </Tag>
            </div>
          }
          type="info"
          className="mb-4"
        />
      )}

      {/* 工作区列表 */}
      <div className="space-y-3">
        <Title level={5}>所有工作区</Title>
        <List
          dataSource={workspaces}
          renderItem={(workspace) => (
            <List.Item
              actions={[
                <Button
                  key="switch"
                  type={currentWorkspace?.id === workspace.id ? 'primary' : 'default'}
                  size="small"
                  onClick={() => handleSwitchWorkspace(workspace)}
                  disabled={currentWorkspace?.id === workspace.id}
                >
                  {currentWorkspace?.id === workspace.id ? '当前' : '切换'}
                </Button>,
                workspace.type === 'personal' && workspace.id !== currentWorkspace?.id && (
                  <Button
                    key="delete"
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={() => handleDeleteWorkspace(workspace.id)}
                  />
                )
              ].filter(Boolean)}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    icon={workspace.type === 'enterprise' ? <TeamOutlined /> : <UserOutlined />}
                    style={{
                      backgroundColor: workspace.type === 'enterprise' ? '#1890ff' : '#52c41a'
                    }}
                  />
                }
                title={
                  <div className="flex items-center gap-2">
                    <span>{workspace.name}</span>
                    {workspace.type === 'enterprise' && (
                      <Tag color="blue" size="small">企业</Tag>
                    )}
                    {currentWorkspace?.id === workspace.id && (
                      <Tag color="green" size="small">当前</Tag>
                    )}
                  </div>
                }
                description={
                  <div>
                    <div className="text-sm text-gray-500">
                      创建时间: {dayjs(workspace.created_at).format('YYYY-MM-DD')} |
                      成员数: {workspace.member_count}人 |
                      你的角色: {workspace.role}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      状态: {workspace.status === 'active' ? '活跃' : '未激活'}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </div>

      {workspaces.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-4">
            <TeamOutlined style={{ fontSize: '48px' }} />
          </div>
          <div className="text-gray-500 mb-4">暂无工作区</div>
        </div>
      )}
    </Card>
  )

  
  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>个人中心</Title>
        <Text type="secondary">管理您的个人信息和工作区</Text>
      </div>

      <Row gutter={[24, 24]}>
        {/* 左侧：个人信息 */}
        <Col xs={24} lg={8}>
          {renderProfileInfo()}
        </Col>

        {/* 右侧：工作区管理 */}
        <Col xs={24} lg={16}>
          {renderWorkspaceManagement()}
        </Col>
      </Row>

      {/* 编辑个人信息模态框 */}
      <Modal
        title="编辑个人信息"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
        width={400}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveProfile}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="姓名"
            name="full_name"
          >
            <Input />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存
              </Button>
              <Button onClick={() => setEditModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PersonalCenter