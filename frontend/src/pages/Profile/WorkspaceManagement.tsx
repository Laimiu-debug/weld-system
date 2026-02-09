import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Descriptions,
  Progress,
  Statistic,
  Alert,
  List,
  Avatar,
  Divider,
  Empty,
  Spin,
  Tooltip,
  Badge,
} from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  SwitcherOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  CrownOutlined,
  HomeOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { workspaceService, Workspace, QuotaInfo } from '@/services/workspace'
import { useAuthStore } from '@/store/authStore'

const { Title, Text, Paragraph } = Typography

// 扩展Workspace接口以包含合并的角色信息
interface ExtendedWorkspace extends Workspace {
  all_roles?: string[]
  all_departments?: string[]
  all_membership_tiers?: string[]
}

const WorkspaceManagement: React.FC = () => {
  const { user, setUser } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [workspaces, setWorkspaces] = useState<ExtendedWorkspace[]>([])
  const [currentWorkspace, setCurrentWorkspace] = useState<ExtendedWorkspace | null>(null)
  const [switchModalVisible, setSwitchModalVisible] = useState(false)
  const [targetWorkspace, setTargetWorkspace] = useState<ExtendedWorkspace | null>(null)

  // 加载工作区数据
  useEffect(() => {
    loadWorkspaces()
  }, [])

  const loadWorkspaces = async () => {
    setLoading(true)
    try {
      // 获取工作区列表
      const workspacesResponse = await workspaceService.getUserWorkspaces()
      let workspaceData: Workspace[] = []

      // 处理不同的响应格式
      if (Array.isArray(workspacesResponse)) {
        workspaceData = workspacesResponse
      } else if (workspacesResponse?.success && workspacesResponse?.data) {
        if (Array.isArray(workspacesResponse.data)) {
          workspaceData = workspacesResponse.data
        } else {
          workspaceData = [workspacesResponse.data]
        }
      } else if (workspacesResponse?.data) {
        // 兼容其他格式
        if (Array.isArray(workspacesResponse.data)) {
          workspaceData = workspacesResponse.data
        } else {
          workspaceData = [workspacesResponse.data]
        }
      }

      console.log('工作区原始数据:', workspaceData)

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

      // 转换为ExtendedWorkspace数组
      const uniqueWorkspaces = Array.from(workspaceMap.values()).map(({
        workspace,
        roles,
        departments,
        membership_tiers
      }) => ({
        ...workspace,
        all_roles: roles,
        all_departments: departments,
        all_membership_tiers: membership_tiers
      }))

      console.log('合并后的工作区:', uniqueWorkspaces)
      setWorkspaces(uniqueWorkspaces)

      // 获取当前工作区
      const currentResponse = await workspaceService.getCurrentWorkspace()
      console.log('当前工作区响应:', currentResponse)

      let currentWorkspaceData: ExtendedWorkspace | null = null
      if (currentResponse && currentResponse.data) {
        // 处理直接对象格式
        if (currentResponse.data && !currentResponse.success) {
          currentWorkspaceData = currentResponse.data
        } else if (currentResponse.success && currentResponse.data) {
          currentWorkspaceData = currentResponse.data
        }
      } else if (currentResponse && !currentResponse.success) {
        // 直接是工作区对象
        currentWorkspaceData = currentResponse
      }

      if (currentWorkspaceData) {
        setCurrentWorkspace(currentWorkspaceData)
      } else {
        // 如果没有当前工作区，使用默认工作区
        const defaultResponse = await workspaceService.getDefaultWorkspace()
        console.log('默认工作区响应:', defaultResponse)

        if (defaultResponse && defaultResponse.data) {
          if (defaultResponse.data && !defaultResponse.success) {
            setCurrentWorkspace(defaultResponse.data)
          } else if (defaultResponse.success && defaultResponse.data) {
            setCurrentWorkspace(defaultResponse.data)
          }
        } else if (defaultResponse && !defaultResponse.success) {
          setCurrentWorkspace(defaultResponse)
        }
      }
    } catch (error) {
      console.error('加载工作区失败:', error)
      message.error('加载工作区失败')
    } finally {
      setLoading(false)
    }
  }

  // 切换工作区
  const handleSwitchWorkspace = async (workspace: ExtendedWorkspace) => {
    const canSwitch = workspaceService.canSwitchToWorkspace(workspace)
    if (!canSwitch.allowed) {
      message.error(canSwitch.reason || '无法切换到此工作区')
      return
    }

    setTargetWorkspace(workspace)
    setSwitchModalVisible(true)
  }

  // 确认切换工作区
  const confirmSwitchWorkspace = async () => {
    if (!targetWorkspace) return

    setSwitching(true)
    try {
      const response = await workspaceService.switchWorkspace({
        workspace_id: targetWorkspace.id
      })

      if (response.success && response.data) {
        // 更新当前工作区
        const newWorkspace = response.data.workspace
        setCurrentWorkspace(newWorkspace)
        workspaceService.saveCurrentWorkspaceToStorage(newWorkspace)

        // 更新用户信息
        if (user) {
          setUser({
            ...user,
            current_workspace: newWorkspace
          })
        }

        message.success(`已切换到 ${workspaceService.getWorkspaceDisplayName(newWorkspace)}`)
        setSwitchModalVisible(false)

        // 刷新页面数据
        window.location.reload()
      } else {
        message.error(response.message || '切换工作区失败')
      }
    } catch (error) {
      console.error('切换工作区失败:', error)
      message.error('切换工作区失败')
    } finally {
      setSwitching(false)
      setTargetWorkspace(null)
    }
  }

  // 渲染工作区卡片
  const renderWorkspaceCard = (workspace: ExtendedWorkspace) => {
    const typeInfo = workspaceService.formatWorkspaceType(workspace.type)
    const tierInfo = workspaceService.formatMembershipTier(workspace.membership_tier)
    const isCurrent = currentWorkspace?.id === workspace.id

    return (
      <Card
        key={`${workspace.id}_${workspace.name}`}
        hoverable
        className={isCurrent ? 'border-primary border-2' : ''}
        style={{ height: '100%' }}
        actions={[
          isCurrent ? (
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <Text type="success">当前工作区</Text>
            </Space>
          ) : (
            <Button
              type="primary"
              icon={<SwitcherOutlined />}
              onClick={() => handleSwitchWorkspace(workspace)}
              loading={switching && targetWorkspace?.id === workspace.id}
            >
              切换到此工作区
            </Button>
          )
        ]}
      >
        <Card.Meta
          avatar={
            <Avatar
              icon={workspace.type === 'personal' ? <UserOutlined /> : <TeamOutlined />}
              style={{ backgroundColor: isCurrent ? '#1890ff' : undefined }}
            />
          }
          title={
            <Space>
              <Text strong>{workspace.name}</Text>
              {isCurrent && <Tag color="success">当前</Tag>}
            </Space>
          }
          description={
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text type="secondary">{workspace.description}</Text>

              <Space wrap>
                <Tag color={typeInfo.color} icon={typeInfo.icon === 'user' ? <UserOutlined /> : <TeamOutlined />}>
                  {typeInfo.text}
                </Tag>
                {workspace.all_roles && workspace.all_roles.length > 0 && (
                  <Tag color="blue">
                    {workspace.all_roles.map(role => {
                      switch (role) {
                        case 'owner': return '企业主'
                        case 'employee': return '员工'
                        case 'admin': return '管理员'
                        default: return role
                      }
                    }).join('、')}
                    {workspace.all_departments && workspace.all_departments.length > 0 &&
                      ` (${workspace.all_departments.join('、')})`
                    }
                  </Tag>
                )}
                <Tag color={tierInfo.color} icon={<CrownOutlined />}>
                  {tierInfo.text}
                </Tag>
                {workspace.factory_name && (
                  <Tag color="orange">
                    <HomeOutlined /> {workspace.factory_name}
                  </Tag>
                )}
              </Space>

              {/* 配额信息 */}
              <div style={{ marginTop: 8 }}>
                <Text strong>配额使用情况：</Text>
                <div style={{ marginTop: 4 }}>
                  {renderQuotaInfo(workspace.quota_info)}
                </div>
              </div>
            </Space>
          }
        />
      </Card>
    )
  }

  // 渲染配额信息
  const renderQuotaInfo = (quotaInfo: QuotaInfo) => {
    const quotaItems = []

    if (quotaInfo.wps) {
      const wpsStatus = workspaceService.checkQuotaUsage({} as Workspace, 'wps')
      quotaItems.push(
        <div key="wps" style={{ marginBottom: 4 }}>
          <Text small>WPS: {quotaInfo.wps.used}/{quotaInfo.wps.limit}</Text>
          <Progress
            percent={quotaInfo.wps.percentage}
            size="small"
            status={wpsStatus.isNearLimit ? 'exception' : 'normal'}
            showInfo={false}
            style={{ marginLeft: 8, width: 60 }}
          />
        </div>
      )
    }

    if (quotaInfo.equipment) {
      const equipmentStatus = workspaceService.checkQuotaUsage({} as Workspace, 'equipment')
      quotaItems.push(
        <div key="equipment" style={{ marginBottom: 4 }}>
          <Text small>设备: {quotaInfo.equipment.used}/{quotaInfo.equipment.limit}</Text>
          <Progress
            percent={quotaInfo.equipment.percentage}
            size="small"
            status={equipmentStatus.isNearLimit ? 'exception' : 'normal'}
            showInfo={false}
            style={{ marginLeft: 8, width: 60 }}
          />
        </div>
      )
    }

    if (quotaInfo.storage) {
      const storageStatus = workspaceService.checkQuotaUsage({} as Workspace, 'storage')
      quotaItems.push(
        <div key="storage" style={{ marginBottom: 4 }}>
          <Text small>存储: {quotaInfo.storage.used}MB/{quotaInfo.storage.limit}MB</Text>
          <Progress
            percent={quotaInfo.storage.percentage}
            size="small"
            status={storageStatus.isNearLimit ? 'exception' : 'normal'}
            showInfo={false}
            style={{ marginLeft: 8, width: 60 }}
          />
        </div>
      )
    }

    if (quotaItems.length === 0) {
      return <Text type="secondary">无配额限制</Text>
    }

    return <>{quotaItems}</>
  }

  // 渲染当前工作区详情
  const renderCurrentWorkspaceInfo = () => {
    if (!currentWorkspace) {
      return (
        <Alert
          message="未选择工作区"
          description="请选择一个工作区开始使用"
          type="info"
          showIcon
        />
      )
    }

    const typeInfo = workspaceService.formatWorkspaceType(currentWorkspace.type)
    const tierInfo = workspaceService.formatMembershipTier(currentWorkspace.membership_tier)

    return (
      <Card>
        <Descriptions title="当前工作区信息" bordered column={1}>
          <Descriptions.Item label="工作区名称">
            <Space>
              <Avatar
                icon={currentWorkspace.type === 'personal' ? <UserOutlined /> : <TeamOutlined />}
                style={{ backgroundColor: '#1890ff' }}
              />
              <Text strong>{currentWorkspace.name}</Text>
            </Space>
          </Descriptions.Item>

          <Descriptions.Item label="工作区类型">
            <Tag color={typeInfo.color} icon={typeInfo.icon === 'user' ? <UserOutlined /> : <TeamOutlined />}>
              {typeInfo.text}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="会员等级">
            <Tag color={tierInfo.color} icon={<CrownOutlined />}>
              {tierInfo.text}
            </Tag>
          </Descriptions.Item>

          {currentWorkspace.all_roles && currentWorkspace.all_roles.length > 0 && (
            <Descriptions.Item label="角色">
              <Tag color="blue">
                {currentWorkspace.all_roles.map(role => {
                  switch (role) {
                    case 'owner': return '企业主'
                    case 'employee': return '员工'
                    case 'admin': return '管理员'
                    default: return role
                  }
                }).join('、')}
                {currentWorkspace.all_departments && currentWorkspace.all_departments.length > 0 &&
                  ` (${currentWorkspace.all_departments.join('、')})`
                }
              </Tag>
            </Descriptions.Item>
          )}

          {currentWorkspace.factory_name && (
            <Descriptions.Item label="所属工厂">
              <Tag color="orange" icon={<HomeOutlined />}>
                {currentWorkspace.factory_name}
              </Tag>
            </Descriptions.Item>
          )}

          <Descriptions.Item label="工作区ID">
            <Text code>{currentWorkspace.id}</Text>
          </Descriptions.Item>

          <Descriptions.Item label="最后切换时间">
            {dayjs().format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 页面标题 */}
        <div>
          <Title level={2}>
            <SettingOutlined /> 工作区管理
          </Title>
          <Paragraph type="secondary">
            管理您的工作区，切换不同的数据空间，查看配额使用情况
          </Paragraph>
        </div>

        {/* 当前工作区信息 */}
        {renderCurrentWorkspaceInfo()}

        {/* 工作区列表 */}
        <Card>
          <Title level={4}>
            <SwitcherOutlined /> 可用工作区
          </Title>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text>正在加载工作区...</Text>
              </div>
            </div>
          ) : workspaces.length > 0 ? (
            <Row gutter={[16, 16]}>
              {workspaces.map((workspace, index) => (
                <Col xs={24} sm={24} md={12} lg={8} key={`${workspace.id}_${index}`}>
                  {renderWorkspaceCard(workspace)}
                </Col>
              ))}
            </Row>
          ) : (
            <Empty
              description="暂无可用工作区"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>

        {/* 使用提示 */}
        <Alert
          message="工作区使用提示"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>个人工作区：仅您自己可见的私人数据空间</li>
              <li>企业工作区：与团队成员共享的协作空间</li>
              <li>切换工作区后，您看到的数据和功能会有所不同</li>
              <li>配额限制因工作区类型和会员等级而异</li>
            </ul>
          }
          type="info"
          showIcon
        />
      </Space>

      {/* 工作区切换确认弹窗 */}
      <Modal
        title="切换工作区"
        open={switchModalVisible}
        onOk={confirmSwitchWorkspace}
        onCancel={() => {
          setSwitchModalVisible(false)
          setTargetWorkspace(null)
        }}
        confirmLoading={switching}
        okText="确认切换"
        cancelText="取消"
      >
        {currentWorkspace && targetWorkspace && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>从：</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="blue">
                  {workspaceService.getWorkspaceDisplayName(currentWorkspace)}
                </Tag>
              </div>
            </div>

            <div>
              <Text strong>切换到：</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="green">
                  {workspaceService.getWorkspaceDisplayName(targetWorkspace)}
                </Tag>
              </div>
            </div>

            <Divider />

            <Alert
              message="注意事项"
              description="切换工作区后，页面将刷新并显示新工作区的数据。请确保已保存当前工作区的更改。"
              type="warning"
              showIcon
            />
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default WorkspaceManagement