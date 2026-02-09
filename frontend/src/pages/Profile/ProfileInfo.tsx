import React, { useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  Avatar,
  Upload,
  Row,
  Col,
  Divider,
  message,
  Space,
} from 'antd'
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'

const { Title, Text } = Typography

const ProfileInfo: React.FC = () => {
  const { user, updateProfile, refreshUserInfo } = useAuthStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // 页面加载时刷新用户信息
  React.useEffect(() => {
    const loadUserInfo = async () => {
      setRefreshing(true)
      try {
        await refreshUserInfo()
      } catch (error) {
        console.error('刷新用户信息失败:', error)
      } finally {
        setRefreshing(false)
      }
    }

    loadUserInfo()
  }, [refreshUserInfo])

  // 初始化表单数据
  React.useEffect(() => {
    if (user) {
      form.setFieldsValue({
        username: user.username,
        full_name: user.full_name,
        email: user.email,
        phone: user.phone,
        timezone: user.timezone,
        language: user.language,
      })
    }
  }, [user, form])

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const success = await updateProfile(values)
      if (success) {
        message.success('个人信息更新成功')
      }
    } catch (error) {
      message.error('更新失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 处理头像上传
  const handleAvatarUpload = async (info: any) => {
    const { file } = info

    // 检查文件类型
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件！')
      return
    }

    // 检查文件大小（5MB限制）
    const isLt5M = file.size / 1024 / 1024 < 5
    if (!isLt5M) {
      message.error('图片大小不能超过5MB！')
      return
    }

    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('file', file.originFileObj)

      const response = await fetch('/api/v1/upload/avatar', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      })

      const result = await response.json()

      if (response.ok && result.success) {
        message.success('头像上传成功')
        // 刷新用户信息
        await updateProfile({ avatar_url: result.url })
        // 刷新整个用户信息以获取最新的头像URL
        await refreshUserInfo()
      } else {
        message.error(result.detail || '头像上传失败')
      }
    } catch (error) {
      console.error('头像上传错误:', error)
      message.error('头像上传失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取会员等级显示名称
  const getMembershipTierName = (tier: string) => {
    const tierNames: Record<string, string> = {
      free: '免费版',
      personal_pro: '专业版',
      personal_advanced: '高级版',
      personal_flagship: '旗舰版',
      enterprise: '企业版',
      enterprise_pro: '企业版PRO',
      enterprise_pro_max: '企业版PRO MAX',
    }
    return tierNames[tier] || '未知'
  }

  // 获取会员等级颜色
  const getMembershipTierColor = (tier: string) => {
    const tierColors: Record<string, string> = {
      free: '#8c8c8c',
      personal_pro: '#1890ff',
      personal_advanced: '#52c41a',
      personal_flagship: '#722ed1',
      enterprise: '#fa8c16',
      enterprise_pro: '#eb2f96',
      enterprise_pro_max: '#f5222d',
    }
    return tierColors[tier] || '#8c8c8c'
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>个人信息</Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card>
            <div className="text-center">
              <Upload
                name="avatar"
                listType="picture-card"
                className="avatar-uploader"
                showUploadList={false}
                accept="image/*"
                beforeUpload={() => false}  // 阻止自动上传
                onChange={handleAvatarUpload}
              >
                {loading ? (
                  <Avatar size={120} className="avatar-uploader">
                    <div className="ant-upload-text">上传中...</div>
                  </Avatar>
                ) : (
                  <Avatar
                    size={120}
                    src={user?.avatar_url}
                    icon={<UserOutlined />}
                    className="avatar-uploader"
                  />
                )}
              </Upload>
              <Title level={4} className="mt-3">
                {user?.full_name || user?.username}
              </Title>
              <Text type="secondary">
                会员等级: <span style={{ color: getMembershipTierColor(user?.membership_tier || '') }}>
                  {getMembershipTierName(user?.membership_tier || '')}
                </span>
              </Text>
              <Divider />
              <div className="text-left">
                <Space direction="vertical" size="small">
                  <Text>
                    <UserOutlined className="mr-2" />
                    用户名: {user?.username}
                  </Text>
                  <Text>
                    <MailOutlined className="mr-2" />
                    邮箱: {user?.email}
                  </Text>
                  {user?.phone && (
                    <Text>
                      <PhoneOutlined className="mr-2" />
                      电话: {user?.phone}
                    </Text>
                  )}
                  <Text>
                    注册时间: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '未知'}
                  </Text>
                  <Text>
                    最后登录: {user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : '未知'}
                  </Text>
                </Space>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={16}>
          <Card title="编辑个人信息">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="username"
                    label="用户名"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' },
                      { max: 20, message: '用户名最多20个字符' },
                    ]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="full_name"
                    label="姓名"
                    rules={[
                      { required: true, message: '请输入姓名' },
                    ]}
                  >
                    <Input placeholder="请输入姓名" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="email"
                    label="邮箱"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="phone"
                    label="电话"
                    rules={[
                      { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
                    ]}
                  >
                    <Input prefix={<PhoneOutlined />} placeholder="请输入电话" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="timezone" label="时区">
                    <Input placeholder="请输入时区" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="language" label="语言">
                    <Input placeholder="请输入语言" />
                  </Form.Item>
                </Col>
              </Row>

              <div className="text-right">
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={loading}
                >
                  保存修改
                </Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default ProfileInfo