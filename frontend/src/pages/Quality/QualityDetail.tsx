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
  Avatar,
  Tooltip,
  Modal,
  message,
  Alert,
  Image,
  Upload,
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
  FileImageOutlined,
  UploadOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { QualityInspection, InspectionType, InspectionResult } from '@/types'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography

const QualityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')

  // 模拟获取质量检验详情数据
  const inspectionData: QualityInspection = {
    id: id || '1',
    user_id: 'user1',
    production_task_id: '1',
    inspection_number: 'INS-2024-001',
    inspection_date: '2024-01-15',
    inspector_name: '张检验员',
    inspection_type: 'visual',
    result: 'pass',
    defects_found: {},
    corrective_actions: '无',
    follow_up_required: false,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
  }

  // 模拟检验项目
  const inspectionItems = [
    {
      id: '1',
      name: '焊缝外观',
      standard: '无裂纹、气孔、咬边等缺陷',
      result: '合格',
      notes: '焊缝成型良好，无可见缺陷',
    },
    {
      id: '2',
      name: '焊缝尺寸',
      standard: '焊缝宽度6-8mm，余高0-2mm',
      result: '合格',
      notes: '焊缝宽度7mm，余高1mm，符合要求',
    },
    {
      id: '3',
      name: '焊接变形',
     标准: '角变形≤3mm',
      result: '合格',
      notes: '实测角变形1.5mm，符合要求',
    },
  ]

  // 模拟缺陷记录
  const defectRecords = [
    {
      id: '1',
      location: '焊缝A段',
      type: '气孔',
      size: '直径1mm',
      quantity: 2,
      description: '分散小气孔，不影响强度',
      images: ['defect1.jpg', 'defect2.jpg'],
    },
  ]

  // 模拟检验图片
  const inspectionImages = [
    {
      id: '1',
      name: '焊缝外观照片',
      url: 'https://via.placeholder.com/300x200?text=Weld+Appearance',
      description: '整体焊缝外观良好',
    },
    {
      id: '2',
      name: '尺寸测量照片',
      url: 'https://via.placeholder.com/300x200?text=Size+Measurement',
      description: '焊缝尺寸测量记录',
    },
  ]

  // 获取检验类型显示名称
  const getInspectionTypeName = (type: InspectionType) => {
    const typeNames: Record<InspectionType, { color: string; text: string }> = {
      'visual': { color: 'blue', text: '外观检验' },
      'radiographic': { color: 'green', text: '射线检验' },
      'ultrasonic': { color: 'orange', text: '超声波检验' },
      'magnetic_particle': { color: 'purple', text: '磁粉检验' },
      'liquid_penetrant': { color: 'cyan', text: '渗透检验' },
      'destructive': { color: 'red', text: '破坏性检验' },
    }
    return typeNames[type] || { color: 'default', text: type }
  }

  // 获取检验结果显示名称
  const getInspectionResultName = (result: InspectionResult) => {
    const resultNames: Record<InspectionResult, { color: string; text: string; icon: React.ReactNode }> = {
      'pass': { color: 'success', text: '合格', icon: <CheckCircleOutlined /> },
      'fail': { color: 'error', text: '不合格', icon: <ExclamationCircleOutlined /> },
      'conditional': { color: 'warning', text: '有条件合格', icon: <WarningOutlined /> },
    }
    return resultNames[result] || resultNames['pass']
  }

  // 处理编辑
  const handleEdit = () => {
    navigate(`/quality/${id}/edit`)
  }

  // 处理删除
  const handleDelete = () => {
    Modal.confirm({
      title: '确定要删除这个检验记录吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      onOk() {
        message.success('删除成功')
        navigate('/quality')
      },
    })
  }

  // 处理上传图片
  const handleUploadImage = () => {
    message.info('上传图片功能开发中')
  }

  // 检验项目表格列
  const inspectionColumns = [
    {
      title: '检验项目',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '标准要求',
      dataIndex: 'standard',
      key: 'standard',
      ellipsis: true,
    },
    {
      title: '检验结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: string) => (
        <Tag color={result === '合格' ? 'success' : 'error'}>
          {result}
        </Tag>
      ),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
  ]

  // 缺陷记录表格列
  const defectColumns = [
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: '缺陷类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color="red">{type}</Tag>
      ),
    },
    {
      title: '尺寸',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '图片',
      dataIndex: 'images',
      key: 'images',
      render: (images: string[]) => (
        <Space>
          {images.map((image, index) => (
            <Button
              key={index}
              type="text"
              icon={<EyeOutlined />}
              onClick={() => message.info('查看图片功能开发中')}
            >
              查看
            </Button>
          ))}
        </Space>
      ),
    },
  ]

  const inspectionType = getInspectionTypeName(inspectionData.inspection_type)
  const inspectionResult = getInspectionResultName(inspectionData.result)

  return (
    <div className="page-container">
      <div className="page-header">
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/quality')}
          >
            返回列表
          </Button>
          <Title level={2}>质量检验详情</Title>
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
                      <Descriptions.Item label="检验编号">
                        {inspectionData.inspection_number}
                      </Descriptions.Item>
                      <Descriptions.Item label="检验类型">
                        <Tag color={inspectionType.color}>
                          {inspectionType.text}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="检验日期">
                        {dayjs(inspectionData.inspection_date).format('YYYY-MM-DD')}
                      </Descriptions.Item>
                      <Descriptions.Item label="检验员">
                        {inspectionData.inspector_name}
                      </Descriptions.Item>
                      <Descriptions.Item label="生产任务">
                        压力容器筒体焊接 (TSK-2024-001)
                      </Descriptions.Item>
                      <Descriptions.Item label="检验结果">
                        <Tag color={inspectionResult.color} icon={inspectionResult.icon}>
                          {inspectionResult.text}
                        </Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="纠正措施" span={2}>
                        {inspectionData.corrective_actions}
                      </Descriptions.Item>
                      <Descriptions.Item label="跟进要求" span={2}>
                        <Tag color={inspectionData.follow_up_required ? 'warning' : 'success'}>
                          {inspectionData.follow_up_required ? '需要跟进' : '无需跟进'}
                        </Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  )
                },
                {
                  key: 'items',
                  label: '检验项目',
                  children: (
                    <Table
                      dataSource={inspectionItems}
                      columns={inspectionColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                },
                {
                  key: 'defects',
                  label: '缺陷记录',
                  children: (
                    <Table
                      dataSource={defectRecords}
                      columns={defectColumns}
                      rowKey="id"
                      pagination={false}
                    />
                  )
                },
                {
                  key: 'images',
                  label: '检验图片',
                  children: (
                    <div className="p-4">
                      <Row gutter={[16, 16]}>
                        {inspectionImages.map((image) => (
                          <Col xs={24} sm={12} md={8} key={image.id}>
                            <Card
                              hoverable
                              cover={<Image src={image.url} alt={image.name} />}
                              actions={[
                                <Button type="text" icon={<EyeOutlined />}>
                                  查看
                                </Button>,
                              ]}
                            >
                              <Card.Meta title={image.name} description={image.description} />
                            </Card>
                          </Col>
                        ))}
                      </Row>
                      <div className="mt-4 text-center">
                        <Button icon={<UploadOutlined />} onClick={handleUploadImage}>
                          上传图片
                        </Button>
                      </div>
                    </div>
                  )
                }
              ]}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="检验结果">
            <div className="text-center p-4">
              <div className="mb-4">
                <Avatar size={64} icon={inspectionResult.icon} className="mb-3" />
                <Title level={4}>{inspectionResult.text}</Title>
                <Tag color={inspectionResult.color} icon={inspectionResult.icon}>
                  {inspectionResult.text}
                </Tag>
              </div>
              <Divider />
              <div className="mb-4">
                <Text>检验编号: {inspectionData.inspection_number}</Text>
              </div>
              <div className="mb-4">
                <Text>检验类型: </Text>
                <Tag color={inspectionType.color}>
                  {inspectionType.text}
                </Tag>
              </div>
            </div>
          </Card>

          <Card title="检验信息" className="mt-6">
            <div className="p-4">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>检验日期:</Text>
                  <Text>{dayjs(inspectionData.inspection_date).format('YYYY-MM-DD')}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>检验员:</Text>
                  <Text>{inspectionData.inspector_name}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>生产任务:</Text>
                  <Text>TSK-2024-001</Text>
                </div>
              </Space>
            </div>
          </Card>

          <Card title="缺陷统计" className="mt-6">
            <div className="p-4">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between">
                  <Text>缺陷总数:</Text>
                  <Text strong>{defectRecords.length}</Text>
                </div>
                <div className="flex justify-between">
                  <Text>缺陷类型:</Text>
                  <Text>{defectRecords.length > 0 ? defectRecords[0].type : '无'}</Text>
                </div>
              </Space>
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
                编辑检验
              </Button>
              <Button
                icon={<PlusOutlined />}
                block
              >
                添加检验项目
              </Button>
              <Button
                icon={<FileImageOutlined />}
                block
              >
                添加图片
              </Button>
              <Button
                icon={<DownloadOutlined />}
                block
              >
                导出报告
              </Button>
              <Button
                icon={<DeleteOutlined />}
                block
                danger
                onClick={handleDelete}
              >
                删除检验
              </Button>
            </Space>
          </Card>

          {inspectionResult.text === '不合格' && (
            <Alert
              message="检验不合格"
              description="检验结果为不合格，请查看缺陷记录并采取纠正措施"
              type="error"
              showIcon
              className="mt-6"
            />
          )}

          {inspectionResult.text === '有条件合格' && (
            <Alert
              message="有条件合格"
              description="检验结果为有条件合格，请查看缺陷记录并采取相应措施"
              type="warning"
              showIcon
              className="mt-6"
            />
          )}
        </Col>
      </Row>
    </div>
  )
}

export default QualityDetail