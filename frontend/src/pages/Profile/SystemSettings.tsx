import React, { useEffect, useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Switch,
  Select,
  Button,
  Divider,
  message,
  Row,
  Col,
  Space,
  Input,
  InputNumber,
  ColorPicker,
  TimePicker,
  Spin,
  Alert,
} from 'antd'
import type { Color } from 'antd/es/color-picker'
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
  BulbOutlined,
  BankOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  DEFAULT_SYSTEM_PREFERENCES,
  UserSystemPreferences,
} from '@/types/preferences'
import { usePreferencesStore } from '@/store/preferencesStore'
import { loadBranding, updateBranding } from '@/hooks/useBranding'
import {
  AI_DATA_OUTBOUND_NOTICE_VERSION,
  aiDataOutboundNotice,
} from '@/utils/aiPrivacy'

const { Title, Text } = Typography
const { Option } = Select

function toHexColor(value: string | Color | undefined, fallback: string): string {
  if (!value) return fallback
  if (typeof value === 'string') return value
  if (typeof (value as Color).toHexString === 'function') {
    return (value as Color).toHexString()
  }
  return fallback
}

const SystemSettingsPage: React.FC = () => {
  const [form] = Form.useForm()
  const [brandingForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [brandingSaving, setBrandingSaving] = useState(false)
  const preferences = usePreferencesStore((s) => s.preferences)
  const loading = usePreferencesStore((s) => s.loading)
  const loaded = usePreferencesStore((s) => s.loaded)
  const loadFromServer = usePreferencesStore((s) => s.loadFromServer)
  const saveToServer = usePreferencesStore((s) => s.saveToServer)
  const resetToDefault = usePreferencesStore((s) => s.resetToDefault)

  useEffect(() => {
    void loadFromServer()
    void loadBranding(true).then((info) => {
      brandingForm.setFieldsValue({
        brand_name: info.brand_name,
        brand_subtitle: info.brand_subtitle,
        org_name: info.org_name,
      })
    })
  }, [loadFromServer, brandingForm])

  useEffect(() => {
    form.setFieldsValue({
      ...preferences,
      workStartTime: dayjs(preferences.workStartTime || '09:00', 'HH:mm'),
      workEndTime: dayjs(preferences.workEndTime || '18:00', 'HH:mm'),
      primaryColor: preferences.primaryColor || '#1F5EFF',
    })
  }, [preferences, form])

  const handleSave = async (values: Record<string, any>) => {
    setSaving(true)
    try {
      const next: UserSystemPreferences = {
        ...preferences,
        ...values,
        primaryColor: toHexColor(values.primaryColor, preferences.primaryColor || '#1F5EFF'),
        workStartTime:
          values.workStartTime && typeof values.workStartTime.format === 'function'
            ? values.workStartTime.format('HH:mm')
            : preferences.workStartTime,
        workEndTime:
          values.workEndTime && typeof values.workEndTime.format === 'function'
            ? values.workEndTime.format('HH:mm')
            : preferences.workEndTime,
      }

      next.aiDataOutboundNoticeVersion = next.aiDataOutboundAuthorized
        ? AI_DATA_OUTBOUND_NOTICE_VERSION
        : ''

      if (next.desktopNotifications && typeof Notification !== 'undefined') {
        if (Notification.permission === 'default') {
          await Notification.requestPermission()
        }
        if (Notification.permission === 'denied') {
          message.warning('浏览器已拒绝桌面通知权限，可在浏览器设置中开启')
          next.desktopNotifications = false
        }
      }

      await saveToServer(next)
      message.success('系统设置已保存，部分外观效果已立即生效')
    } catch (error) {
      console.error(error)
      message.error('保存失败，请稍后重试')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    const defaults = resetToDefault()
    form.setFieldsValue({
      ...defaults,
      workStartTime: dayjs(defaults.workStartTime, 'HH:mm'),
      workEndTime: dayjs(defaults.workEndTime, 'HH:mm'),
      primaryColor: defaults.primaryColor,
    })
    try {
      setSaving(true)
      await saveToServer(defaults)
      message.success('已恢复默认设置并同步到服务器')
    } catch {
      message.info('已恢复本地默认设置，同步服务器失败')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveBranding = async () => {
    try {
      const values = await brandingForm.validateFields()
      setBrandingSaving(true)
      const info = await updateBranding({
        brand_name: values.brand_name,
        brand_subtitle: values.brand_subtitle,
        org_name: values.org_name || '',
      })
      brandingForm.setFieldsValue({
        brand_name: info.brand_name,
        brand_subtitle: info.brand_subtitle,
        org_name: info.org_name,
      })
      message.success('企业名称已更新，刷新页面后侧栏立即可见')
    } catch (error: any) {
      if (error?.errorFields) return
      message.error('保存企业名称失败')
    } finally {
      setBrandingSaving(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>系统设置</Title>
        <Text type="secondary">配置侧栏企业名、个人界面偏好与工作时间</Text>
      </div>

      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="侧栏「企业名称」在此页修改；个人偏好会同步到您的账号。"
      />

      <Card
        title={
          <Space>
            <BankOutlined />
            <span>品牌与企业名称（用户端侧栏）</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
        extra={
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={brandingSaving}
            onClick={() => void handleSaveBranding()}
          >
            保存企业名
          </Button>
        }
      >
        <Form form={brandingForm} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                name="brand_name"
                label="产品名称"
                rules={[{ required: true, message: '请输入产品名称' }]}
                extra="侧栏主标题，默认「焊序」"
              >
                <Input maxLength={32} placeholder="焊序" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="brand_subtitle"
                label="默认副标题"
                extra="未填企业名称时显示"
              >
                <Input maxLength={64} placeholder="Hanxu" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="org_name"
                label="企业名称"
                extra="填写后显示在侧栏产品名下方"
              >
                <Input maxLength={64} placeholder="例如：某某焊接有限公司" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      <Spin spinning={loading && !loaded}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            ...DEFAULT_SYSTEM_PREFERENCES,
            workStartTime: dayjs('09:00', 'HH:mm'),
            workEndTime: dayjs('18:00', 'HH:mm'),
          }}
        >
          <Row gutter={[24, 24]}>
            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <GlobalOutlined />
                    <span>语言和地区</span>
                  </Space>
                }
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Form.Item name="language" label="界面语言">
                      <Select>
                        <Option value="zh-CN">简体中文</Option>
                        <Option value="zh-TW">繁体中文</Option>
                        <Option value="en-US">English</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="timezone" label="时区">
                      <Select>
                        <Option value="Asia/Shanghai">北京时间 (UTC+8)</Option>
                        <Option value="Asia/Tokyo">东京时间 (UTC+9)</Option>
                        <Option value="America/New_York">纽约时间 (UTC-5)</Option>
                        <Option value="Europe/London">伦敦时间 (UTC+0)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="dateFormat" label="日期格式">
                      <Select>
                        <Option value="YYYY-MM-DD">2024-01-15</Option>
                        <Option value="DD/MM/YYYY">15/01/2024</Option>
                        <Option value="MM/DD/YYYY">01/15/2024</Option>
                        <Option value="YYYY年MM月DD日">2024年01月15日</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="timeFormat" label="时间格式">
                      <Select>
                        <Option value="HH:mm:ss">24小时制</Option>
                        <Option value="hh:mm:ss A">12小时制</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <BulbOutlined />
                    <span>外观设置</span>
                  </Space>
                }
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Form.Item name="theme" label="主题模式">
                      <Select>
                        <Option value="light">浅色模式</Option>
                        <Option value="dark">深色模式</Option>
                        <Option value="auto">跟随系统</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="primaryColor"
                      label="主题色"
                      getValueFromEvent={(color: Color) => color.toHexString()}
                    >
                      <ColorPicker showText format="hex" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="compactMode" label="紧凑模式" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="sidebarCollapsed"
                      label="默认折叠侧边栏"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <ClockCircleOutlined />
                    <span>工作时间设置</span>
                  </Space>
                }
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24}>
                    <Form.Item name="workDays" label="工作日">
                      <Select mode="multiple" placeholder="选择工作日">
                        <Option value="Monday">周一</Option>
                        <Option value="Tuesday">周二</Option>
                        <Option value="Wednesday">周三</Option>
                        <Option value="Thursday">周四</Option>
                        <Option value="Friday">周五</Option>
                        <Option value="Saturday">周六</Option>
                        <Option value="Sunday">周日</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="workStartTime" label="工作开始时间">
                      <TimePicker format="HH:mm" style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="workEndTime" label="工作结束时间">
                      <TimePicker format="HH:mm" style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <SettingOutlined />
                    <span>系统行为</span>
                  </Space>
                }
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Form.Item name="autoSave" label="自动保存" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name="autoSaveInterval" label="自动保存间隔(秒)">
                      <InputNumber min={10} max={300} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="notificationSound"
                      label="通知声音"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="desktopNotifications"
                      label="桌面通知"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col xs={24}>
              <Card
                title={
                  <Space>
                    <SafetyCertificateOutlined />
                    <span>AI 与数据外发</span>
                  </Space>
                }
              >
                <Alert
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                  message="这是账号级授权，保存后不再在每次 AI 提取时重复勾选"
                  description={aiDataOutboundNotice()}
                />
                <Form.Item
                  name="aiDataOutboundAuthorized"
                  label="允许向外部模型发送 AI 处理所需数据"
                  valuePropName="checked"
                  extra="关闭后，PQR 提取和图纸识别会在执行前要求单次确认。隐私声明升级时，本授权会自动失效并要求重新保存。"
                >
                  <Switch checkedChildren="已授权" unCheckedChildren="未授权" />
                </Form.Item>
              </Card>
            </Col>

            <Col xs={24}>
              <Card
                title={
                  <Space>
                    <SettingOutlined />
                    <span>数据显示设置</span>
                  </Space>
                }
              >
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={6}>
                    <Form.Item name="pageSize" label="默认分页大小">
                      <InputNumber min={10} max={100} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name="decimalPlaces" label="小数位数">
                      <InputNumber min={0} max={6} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name="currency" label="货币单位">
                      <Select>
                        <Option value="CNY">人民币 (¥)</Option>
                        <Option value="USD">美元 ($)</Option>
                        <Option value="EUR">欧元 (€)</Option>
                        <Option value="JPY">日元 (¥)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name="measurementUnit" label="度量单位">
                      <Select>
                        <Option value="metric">公制</Option>
                        <Option value="imperial">英制</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          <Divider />

          <div className="text-right">
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleReset} disabled={saving}>
                重置默认
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                保存设置
              </Button>
            </Space>
          </div>
        </Form>
      </Spin>
    </div>
  )
}

export default SystemSettingsPage
