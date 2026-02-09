import React, { useState } from 'react'
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
  InputNumber,
  ColorPicker,
  TimePicker,
  Input,
} from 'antd'
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select

interface SystemSettings {
  // 语言设置
  language: string
  timezone: string
  dateFormat: string
  timeFormat: string

  // 外观设置
  theme: string
  primaryColor: string
  compactMode: boolean
  sidebarCollapsed: boolean

  // 工作时间设置
  workDays: string[]
  workStartTime: string
  workEndTime: string

  // 系统行为设置
  autoSave: boolean
  autoSaveInterval: number
  notificationSound: boolean
  desktopNotifications: boolean

  // 数据显示设置
  pageSize: number
  decimalPlaces: number
  currency: string
  measurementUnit: string
}

const SystemSettingsPage: React.FC = () => {
  const { user, updateProfile } = useAuthStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [settings, setSettings] = useState<SystemSettings>({
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    dateFormat: 'YYYY-MM-DD',
    timeFormat: 'HH:mm:ss',
    theme: 'light',
    primaryColor: '#1890ff',
    compactMode: false,
    sidebarCollapsed: false,
    workDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
    workStartTime: '09:00',
    workEndTime: '18:00',
    autoSave: true,
    autoSaveInterval: 30,
    notificationSound: true,
    desktopNotifications: true,
    pageSize: 20,
    decimalPlaces: 2,
    currency: 'CNY',
    measurementUnit: 'metric',
  })

  // 初始化表单数据
  React.useEffect(() => {
    try {
      const formValues = {
        ...settings,
        workStartTime: settings.workStartTime ? dayjs(settings.workStartTime, 'HH:mm') : null,
        workEndTime: settings.workEndTime ? dayjs(settings.workEndTime, 'HH:mm') : null,
      }
      form.setFieldsValue(formValues)
    } catch (error) {
      console.error('Form initialization error:', error)
      // Fallback to default time values
      const formValues = {
        ...settings,
        workStartTime: dayjs('09:00', 'HH:mm'),
        workEndTime: dayjs('18:00', 'HH:mm'),
      }
      form.setFieldsValue(formValues)
    }
  }, [settings, form])

  // 处理设置保存
  const handleSave = async (values: any) => {
    setLoading(true)
    try {
      // 处理时间值
      const processedValues = {
        ...values,
        workStartTime: values.workStartTime && typeof values.workStartTime.format === 'function'
          ? values.workStartTime.format('HH:mm')
          : settings.workStartTime,
        workEndTime: values.workEndTime && typeof values.workEndTime.format === 'function'
          ? values.workEndTime.format('HH:mm')
          : settings.workEndTime,
      }

      // 合并表单值和现有设置
      const updatedSettings = { ...settings, ...processedValues }

      // 这里应该调用API保存系统设置
      // const success = await systemSettingsService.updateSettings(updatedSettings)

      setSettings(updatedSettings)
      message.success('系统设置保存成功')
    } catch (error) {
      message.error('保存失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 重置为默认设置
  const handleReset = () => {
    const defaultSettings: SystemSettings = {
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      dateFormat: 'YYYY-MM-DD',
      timeFormat: 'HH:mm:ss',
      theme: 'light',
      primaryColor: '#1890ff',
      compactMode: false,
      sidebarCollapsed: false,
      workDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      workStartTime: '09:00',
      workEndTime: '18:00',
      autoSave: true,
      autoSaveInterval: 30,
      notificationSound: true,
      desktopNotifications: true,
      pageSize: 20,
      decimalPlaces: 2,
      currency: 'CNY',
      measurementUnit: 'metric',
    }

    const formValues = {
      ...defaultSettings,
      workStartTime: dayjs(defaultSettings.workStartTime, 'HH:mm'),
      workEndTime: dayjs(defaultSettings.workEndTime, 'HH:mm'),
    }

    form.setFieldsValue(formValues)
    setSettings(defaultSettings)
    message.info('已重置为默认设置')
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <Title level={2}>系统设置</Title>
        <Text type="secondary">配置您的个人系统偏好和工作环境</Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          ...settings,
          workStartTime: dayjs(settings.workStartTime, 'HH:mm'),
          workEndTime: dayjs(settings.workEndTime, 'HH:mm'),
        }}
      >
        <Row gutter={[24, 24]}>
          {/* 语言和地区设置 */}
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
                  <Form.Item
                    name="language"
                    label="界面语言"
                    tooltip="选择系统界面显示语言"
                  >
                    <Select>
                      <Option value="zh-CN">简体中文</Option>
                      <Option value="zh-TW">繁体中文</Option>
                      <Option value="en-US">English</Option>
                      <Option value="ja-JP">日本語</Option>
                      <Option value="ko-KR">한국어</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="timezone"
                    label="时区"
                    tooltip="设置您所在时区"
                  >
                    <Select>
                      <Option value="Asia/Shanghai">北京时间 (UTC+8)</Option>
                      <Option value="Asia/Tokyo">东京时间 (UTC+9)</Option>
                      <Option value="America/New_York">纽约时间 (UTC-5)</Option>
                      <Option value="Europe/London">伦敦时间 (UTC+0)</Option>
                      <Option value="Europe/Paris">巴黎时间 (UTC+1)</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="dateFormat"
                    label="日期格式"
                  >
                    <Select>
                      <Option value="YYYY-MM-DD">2024-01-15</Option>
                      <Option value="DD/MM/YYYY">15/01/2024</Option>
                      <Option value="MM/DD/YYYY">01/15/2024</Option>
                      <Option value="YYYY年MM月DD日">2024年01月15日</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="timeFormat"
                    label="时间格式"
                  >
                    <Select>
                      <Option value="HH:mm:ss">24小时制</Option>
                      <Option value="hh:mm:ss A">12小时制</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* 外观设置 */}
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
                  <Form.Item
                    name="theme"
                    label="主题模式"
                  >
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
                  >
                    <ColorPicker />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="compactMode"
                    label="紧凑模式"
                    valuePropName="checked"
                  >
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

          {/* 工作时间设置 */}
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
                  <Form.Item
                    name="workDays"
                    label="工作日"
                  >
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
                  <Form.Item
                    name="workStartTime"
                    label="工作开始时间"
                  >
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      placeholder="选择开始时间"
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="workEndTime"
                    label="工作结束时间"
                  >
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      placeholder="选择结束时间"
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* 系统行为设置 */}
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
                  <Form.Item
                    name="autoSave"
                    label="自动保存"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="autoSaveInterval"
                    label="自动保存间隔(秒)"
                  >
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

          {/* 数据显示设置 */}
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
                  <Form.Item
                    name="pageSize"
                    label="默认分页大小"
                  >
                    <InputNumber min={10} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={6}>
                  <Form.Item
                    name="decimalPlaces"
                    label="小数位数"
                  >
                    <InputNumber min={0} max={6} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={6}>
                  <Form.Item
                    name="currency"
                    label="货币单位"
                  >
                    <Select>
                      <Option value="CNY">人民币 (¥)</Option>
                      <Option value="USD">美元 ($)</Option>
                      <Option value="EUR">欧元 (€)</Option>
                      <Option value="JPY">日元 (¥)</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={6}>
                  <Form.Item
                    name="measurementUnit"
                    label="度量单位"
                  >
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
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              重置默认
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              保存设置
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  )
}

export default SystemSettingsPage