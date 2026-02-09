import React, { useState } from 'react'
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
  Table,
  Timeline,
  Badge,
  Progress,
  Alert,
  Statistic,
  Avatar,
  Tooltip,
  Modal,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  DownloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { WeldingMaterial, MaterialType } from '@/types'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography

const MaterialsDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')
  const [isModalVisible, setIsModalVisible] = useState(false)

  // 模拟获取焊材详情数据
  const materialData: WeldingMaterial = {
    id: id || '1',
    material_code: 'MAT-2024-001',
    material_name: 'E7018碳钢焊条',
    material_type: 'electrode',
    specification: '3.2mm',
    manufacturer: '金桥焊材有限公司',
    current_stock: 150,
    unit: 'kg',
    min_stock_level: 20,
    storage_location: 'A-01-03',
    unit_price: 15.5,
    currency: 'CNY',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    user_id: 'user1',
  }

  // 模拟库存变动记录
  const stockHistory = [
    {
      id: '1',
      date: '2024-01-20',
      type: '入库',
      quantity: 50,
      operator: '张三',
      remark: '新采购入库',
    },
    {
      id: '2',
      date: '2024-01-18',
      type: '出库',
      quantity: 20,
      operator: '李四',
      remark: '生产领用',
    },
    {
      id: '3',
      date: '2024-01-15',
      type: '入库',
      quantity: 120,
      operator: '王五',
      remark: '初期库存',
    },
  ]

  // 模拟使用记录
  const usageRecords = [
    {
      id: '1',
      date: '2024-01-20',
      project: '压力容器项目',
      quantity: 20,
      operator: '李四',
      status: '已完成',
    },
    {
      id: '2',
      date: '2024-01-18',
      project: '管道焊接项目',
      quantity: 15,
      operator: '张三',
      status: '进行中',
    },
  ]

  // 获取焊材类型显示名称
  const getMaterialTypeName = (type: MaterialType) => {
    const typeNames: Record<MaterialType, string> = {
      electrode: '焊条',
      wire: '焊丝',
      flux: '焊剂',
      gas: '保护气体',
    }
    return typeNames[type] || type
  }

  // 获取库存状态
  const getStockStatus = (currentStock: number, minStockLevel: number) => {
    if (currentStock === 0) {
      return { color: 'error', text: '缺货', icon: <ExclamationCircleOutlined /> }
    } else if (currentStock <= minStockLevel) {
      return { color: 'warning', text: '库存不足', icon: <WarningOutlined /> }
    } else {
      return { color: 'success', text: '有库存', icon: <CheckCircleOutlined /> }
    }
  }

  const stockStatus = getStockStatus(materialData.current_stock, materialData.min_stock_level)
  const stockPercentage = Math.min((materialData.current_stock / (materialData.min_stock_level * 3)) * 100, 100)

  // 处理编辑
  const handleEdit = () => {
    navigate(`/materials/${id}/edit`)
  }

  // 处理删除
  const handleDelete = () => {
    Modal.confirm({
      title: '确定要删除这个焊材吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      onOk() {
        message.success('删除成功')
        navigate('/materials')
      },
    })
  }

  // 处理添加库存
  const handleAddStock = () => {
    setIsModalVisible(true)
  }

  // 库存变动记录表格列
  const stockHistoryColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === '入库' ? 'green' : 'red'}>
          {type}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => (
        <Text strong>{quantity} {materialData.unit}</Text>
      ),
    },
    {
      title: '操作人',
      dataIndex: 'operator',
      key: 'operator',
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
    },
  ]

  // 使用记录表格列
  const usageColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '项目',
      dataIndex: 'project',
      key: 'project',
    },
    {
      title: '使用量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => (
        <Text strong>{quantity} {materialData.unit}</Text>
      ),
    },
    {
      title: '操作人',
      dataIndex: 'operator',
      key: 'operator',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === '已完成' ? 'success' : 'processing'}>
          {status}
        </Tag>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/materials')}
          >
            返回列表
          </Button>
          <Title level={2}>焊材详情</Title>
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                {
                  key: 'info',
                  label: '基本信息',
                  children: (
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="焊材编号">
                        {materialData.material_code}
                      </Descriptions.Item>
                      <Descriptions.Item label="焊材名称">
                        {materialData.material_name}
                      </Descriptions.Item>
                      <Descriptions.Item label="焊材类型">
                        <Tag color="blue">{getMaterialTypeName(materialData.material_type)}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="规格">
                        {materialData.specification}
                      </Descriptions.Item>
                      <Descriptions.Item label="制造商">
                        {materialData.manufacturer}
                      </Descriptions.Item>
                      <Descriptions.Item label="存储位置">
                        {materialData.storage_location}
                      </Descriptions.Item>
                      <Descriptions.Item label="创建时间">
                        {dayjs(materialData.created_at).format('YYYY-MM-DD HH:mm:ss')}
                      </Descriptions.Item>
                      <Descriptions.Item label="更新时间">
                        {dayjs(materialData.updated_at).format('YYYY-MM-DD HH:mm:ss')}
                      </Descriptions.Item>
                    </Descriptions>
                  )
                },
                {
                  key: 'stock',
                  label: '库存变动',
                  children: (
                    <Table
                      dataSource={stockHistory}
                      columns={stockHistoryColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                },
                {
                  key: 'usage',
                  label: '使用记录',
                  children: (
                    <Table
                      dataSource={usageRecords}
                      columns={usageColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                }
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="库存状态">
            <div className="text-center p-4">
              <div className="mb-4">
                <Text style={{ fontSize: 48, fontWeight: 'bold' }}>
                  {materialData.current_stock}
                </Text>
                <Text style={{ fontSize: 24, marginLeft: 8 }}>
                  {materialData.unit}
                </Text>
              </div>
              <Tag color={stockStatus.color} style={{ fontSize: 16, padding: '4px 12px' }}>
                {stockStatus.icon}
                {stockStatus.text}
              </Tag>
              <div className="mt-4">
                <Progress
                  percent={stockPercentage}
                  status={stockStatus.color === 'error' ? 'exception' : 'normal'}
                  strokeColor={stockStatus.color}
                />
              </div>
              <div className="mt-2">
                <Text type="secondary">
                  最低库存水平: {materialData.min_stock_level} {materialData.unit}
                </Text>
              </div>
            </div>
          </Card>

          <Card title="价格信息" className="mt-6">
            <div className="text-center p-4">
              <Statistic
                title="单价"
                value={materialData.unit_price}
                prefix={materialData.currency === 'CNY' ? '¥' : materialData.currency}
                suffix={`/ ${materialData.unit}`}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
              />
              <Divider />
              <Statistic
                title="库存总价值"
                value={materialData.current_stock * (materialData.unit_price || 0)}
                prefix={materialData.currency === 'CNY' ? '¥' : materialData.currency}
                precision={2}
                valueStyle={{ color: '#cf1322' }}
              />
            </div>
          </Card>

          <Card title="操作" className="mt-6">
            <Space direction="vertical" className="w-full">
              <Button
                type="primary"
                icon={<EditOutlined />}
                block
                onClick={handleEdit}
              >
                编辑焊材
              </Button>
              <Button
                icon={<PlusOutlined />}
                block
                onClick={handleAddStock}
              >
                添加库存
              </Button>
              <Button
                icon={<DownloadOutlined />}
                block
              >
                导出信息
              </Button>
              <Button
                icon={<DeleteOutlined />}
                block
                danger
                onClick={handleDelete}
              >
                删除焊材
              </Button>
            </Space>
          </Card>

          {materialData.current_stock <= materialData.min_stock_level && (
            <Alert
              message="库存不足"
              description="当前库存已低于最低库存水平，建议及时补充库存"
              type="warning"
              showIcon
              className="mt-6"
            />
          )}
        </Col>
      </Row>

      <Modal
        title="添加库存"
        visible={isModalVisible}
        onOk={() => setIsModalVisible(false)}
        onCancel={() => setIsModalVisible(false)}
      >
        <p>这里可以添加库存变动的表单</p>
      </Modal>
    </div>
  )
}

export default MaterialsDetail