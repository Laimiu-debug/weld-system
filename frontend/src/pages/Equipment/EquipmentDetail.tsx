import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Typography,
  Button,
  Space,
  Tag,
  Descriptions,
  Row,
  Col,
  Divider,
  Tabs,
  Badge,
  Progress,
  Statistic,
  Modal,
  message,
  Spin,
  Empty,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  SettingOutlined,
  CalendarOutlined,
  ToolOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { equipmentService, Equipment } from '@/services/equipment'
import dayjs from 'dayjs'

const { Title } = Typography

const EquipmentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')
  const [equipment, setEquipment] = useState<Equipment | null>(null)
  const [loading, setLoading] = useState(false)

  // 加载设备详情
  const loadEquipmentDetail = async () => {
    if (!id) return

    setLoading(true)
    try {
      const response = await equipmentService.getEquipmentDetail(id)
      if (response.success) {
        setEquipment(response.data || null)
      } else {
        message.error(response.message || '获取设备详情失败')
      }
    } catch (error: any) {
      console.error('获取设备详情失败:', error)
      message.error(error.response?.data?.detail || '获取设备详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEquipmentDetail()
  }, [id])

  // 删除设备
  const handleDelete = () => {
    if (!equipment) return

    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: '确定要删除这个设备吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await equipmentService.deleteEquipment(equipment.id.toString())
          if (response.success) {
            message.success('删除成功')
            navigate('/equipment')
          } else {
            message.error(response.message || '删除失败')
          }
        } catch (error: any) {
          console.error('删除设备失败:', error)
          message.error(error.response?.data?.detail || '删除失败')
        }
      },
    })
  }

  // 更新设备状态
  const handleStatusUpdate = () => {
    if (!equipment) return

    Modal.confirm({
      title: '更新设备状态',
      content: (
        <div>
          <p>当前状态: {equipmentService.formatEquipmentStatus(equipment.status).text}</p>
          <p>请选择新的状态:</p>
          <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
            {equipmentService.getEquipmentStatusOptions().map(option => (
              <Button
                key={option.value}
                onClick={() => updateEquipmentStatus(option.value)}
                type={option.value === equipment.status ? 'primary' : 'default'}
              >
                {option.label}
              </Button>
            ))}
          </Space>
        </div>
      ),
      okText: '取消',
      cancelButtonProps: { style: { display: 'none' } },
    })
  }

  // 执行状态更新
  const updateEquipmentStatus = async (newStatus: string) => {
    if (!equipment) return

    try {
      const response = await equipmentService.updateEquipmentStatus(equipment.id.toString(), {
        status: newStatus as any
      })
      if (response.success) {
        message.success('状态更新成功')
        loadEquipmentDetail()
        Modal.destroyAll()
      } else {
        message.error(response.message || '状态更新失败')
      }
    } catch (error: any) {
      console.error('更新状态失败:', error)
      message.error(error.response?.data?.detail || '状态更新失败')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  if (!equipment) {
    return (
      <div className="p-6">
        <Empty description="设备不存在或已被删除" />
      </div>
    )
  }

  const statusConfig = equipmentService.formatEquipmentStatus(equipment.status)

  return (
    <div className="p-6">
      {/* 页面头部 */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/equipment')}
            >
              返回列表
            </Button>
            <Title level={2} className="mb-0">
              {equipment.equipment_name}
            </Title>
            <Tag color={statusConfig.color} icon={<SettingOutlined />}>
              {statusConfig.text}
            </Tag>
            {equipment.is_critical && <Tag color="red">关键设备</Tag>}
          </Space>

          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadEquipmentDetail}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              icon={<EditOutlined />}
              onClick={() => navigate(`/equipment/${equipment.id}/edit`)}
            >
              编辑
            </Button>
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={handleDelete}
            >
              删除
            </Button>
          </Space>
        </div>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic
              title="运行工时"
              value={equipment.total_operating_hours || 0}
              suffix="小时"
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="使用率"
              value={equipment.utilization_rate || 0}
              suffix="%"
              prefix={<SettingOutlined />}
              valueStyle={{ color: (equipment.utilization_rate || 0) >= 80 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="维护次数"
              value={equipment.maintenance_count || 0}
              prefix={<ToolOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="使用次数"
              value={equipment.usage_count || 0}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 设备详情标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane tab="基本信息" key="info">
            <Descriptions title="设备信息" column={2} bordered>
              <Descriptions.Item label="设备编号">{equipment.equipment_code}</Descriptions.Item>
              <Descriptions.Item label="设备名称">{equipment.equipment_name}</Descriptions.Item>
              <Descriptions.Item label="设备类型">
                {equipmentService.formatEquipmentType(equipment.equipment_type)}
              </Descriptions.Item>
              <Descriptions.Item label="设备类别">{equipment.category || '-'}</Descriptions.Item>
              <Descriptions.Item label="制造商">{equipment.manufacturer || '-'}</Descriptions.Item>
              <Descriptions.Item label="品牌">{equipment.brand || '-'}</Descriptions.Item>
              <Descriptions.Item label="型号">{equipment.model || '-'}</Descriptions.Item>
              <Descriptions.Item label="序列号">{equipment.serial_number || '-'}</Descriptions.Item>
              <Descriptions.Item label="存放位置">{equipment.location || '-'}</Descriptions.Item>
              <Descriptions.Item label="车间">{equipment.workshop || '-'}</Descriptions.Item>
              <Descriptions.Item label="区域">{equipment.area || '-'}</Descriptions.Item>
              <Descriptions.Item label="关键设备">
                {equipment.is_critical ? <Tag color="red">是</Tag> : <Tag>否</Tag>}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="技术参数" column={2} bordered>
              <Descriptions.Item label="额定功率">{equipment.rated_power || '-'} kW</Descriptions.Item>
              <Descriptions.Item label="额定电压">{equipment.rated_voltage || '-'} V</Descriptions.Item>
              <Descriptions.Item label="额定电流">{equipment.rated_current || '-'} A</Descriptions.Item>
              <Descriptions.Item label="最大容量">{equipment.max_capacity || '-'}</Descriptions.Item>
              <Descriptions.Item label="工作范围" span={2}>{equipment.working_range || '-'}</Descriptions.Item>
              <Descriptions.Item label="技术规格" span={2}>{equipment.specifications || '-'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="采购信息" column={2} bordered>
              <Descriptions.Item label="采购日期">{equipment.purchase_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="采购价格">¥{equipment.purchase_price || 0}</Descriptions.Item>
              <Descriptions.Item label="供应商">{equipment.supplier || '-'}</Descriptions.Item>
              <Descriptions.Item label="保修期">{equipment.warranty_period || 0} 月</Descriptions.Item>
              <Descriptions.Item label="保修到期">{equipment.warranty_expiry_date || '-'}</Descriptions.Item>
              <Descriptions.Item label="安装日期">{equipment.installation_date || '-'}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="维护信息" column={2} bordered>
              <Descriptions.Item label="上次维护">{equipment.last_maintenance_date || '未维护'}</Descriptions.Item>
              <Descriptions.Item label="下次维护">{equipment.next_maintenance_date || '未设置'}</Descriptions.Item>
              <Descriptions.Item label="维护间隔">{equipment.maintenance_interval_days || 0} 天</Descriptions.Item>
              <Descriptions.Item label="上次检验">{equipment.last_inspection_date || '未检验'}</Descriptions.Item>
              <Descriptions.Item label="下次检验">{equipment.next_inspection_date || '未设置'}</Descriptions.Item>
              <Descriptions.Item label="检验间隔">{equipment.inspection_interval_days || 0} 天</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="附加信息" column={1} bordered>
              <Descriptions.Item label="设备描述">{equipment.description || '无'}</Descriptions.Item>
              <Descriptions.Item label="备注信息">{equipment.notes || '无'}</Descriptions.Item>
              <Descriptions.Item label="标签">{equipment.tags || '无'}</Descriptions.Item>
              <Descriptions.Item label="访问级别">{equipment.access_level}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(equipment.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{dayjs(equipment.updated_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
            </Descriptions>
          </Tabs.TabPane>

          <Tabs.TabPane tab="状态管理" key="status">
            <div className="text-center py-8">
              <Title level={4}>设备状态管理</Title>
              <div className="mb-6">
                <p>当前状态: <Tag color={statusConfig.color}>{statusConfig.text}</Tag></p>
              </div>
              <Button
                type="primary"
                icon={<SettingOutlined />}
                onClick={handleStatusUpdate}
              >
                更新设备状态
              </Button>
            </div>
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default EquipmentDetail