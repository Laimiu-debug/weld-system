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
  Avatar,
  Modal,
  message,
  Alert,
  Dropdown,
  Spin,
} from 'antd'
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import WorkHistoryList from '../../components/Welders/WorkHistory/WorkHistoryList'
import WorkRecordList from '../../components/Welders/WorkRecords/WorkRecordList'
import TrainingRecordList from '../../components/Welders/TrainingRecords/TrainingRecordList'
import AssessmentRecordList from '../../components/Welders/AssessmentRecords/AssessmentRecordList'
import weldersService, { type Welder } from '@/services/welders'
import { CertificationList } from '@/components/Welders/Certifications'

const { Title, Text } = Typography

const WeldersDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [welderData, setWelderData] = useState<Welder | null>(null)
  const [loading, setLoading] = useState(false)

  // 获取焊工详情数据
  const fetchWelderDetail = async () => {
    if (!id) return

    setLoading(true)
    try {
      const response = await weldersService.getDetail(parseInt(id))
      if (response.success && response.data) {
        setWelderData(response.data)
      } else {
        message.error(response.message || '获取焊工详情失败')
      }
    } catch (error: any) {
      console.error('获取焊工详情失败:', error)
      message.error(error.response?.data?.detail || '获取焊工详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWelderDetail()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  // 获取证书等级显示名称
  const getCertificationLevelName = (level: string) => {
    const levelNames: Record<string, { color: string; text: string }> = {
      '初级': { color: 'default', text: '初级' },
      '中级': { color: 'processing', text: '中级' },
      '高级': { color: 'success', text: '高级' },
      '技师': { color: 'warning', text: '技师' },
      '高级技师': { color: 'error', text: '高级技师' },
    }
    return levelNames[level] || levelNames['初级']
  }

  // 获取证书状态
  const getCertificationStatus = (expiryDate: string) => {
    const now = dayjs()
    const expiry = dayjs(expiryDate)
    const diffDays = expiry.diff(now, 'days')
    
    if (diffDays < 0) {
      return { color: 'error', text: '已过期', icon: <ExclamationCircleOutlined /> }
    } else if (diffDays <= 30) {
      return { color: 'warning', text: '即将过期', icon: <WarningOutlined /> }
    } else {
      return { color: 'success', text: '有效', icon: <CheckCircleOutlined /> }
    }
  }

  // 处理删除
  const handleDelete = async () => {
    if (!id) return

    Modal.confirm({
      title: '确定要删除这个焊工吗？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await weldersService.delete(parseInt(id))
          if (response.success) {
            message.success('删除成功')
            navigate('/welders')
          } else {
            message.error(response.message || '删除失败')
          }
        } catch (error: any) {
          console.error('删除焊工失败:', error)
          message.error(error.response?.data?.detail || '删除失败，请稍后重试')
        }
      },
    })
  }

  // 隐藏身份证号中间部分
  const maskIdNumber = (idNumber: string) => {
    if (idNumber && idNumber.length >= 10) {
      return `${idNumber.substring(0, 6)}********${idNumber.substring(idNumber.length - 4)}`
    }
    return idNumber
  }

  // 隐藏手机号中间部分
  const maskPhoneNumber = (phone: string) => {
    if (phone && phone.length >= 7) {
      return `${phone.substring(0, 3)}****${phone.substring(phone.length - 4)}`
    }
    return phone
  }

  const handleExport = (format: 'csv' | 'json') => {
    if (!welderData) return
    const extra = welderData as Welder & {
      primary_certification_number?: string
      primary_certification_level?: string
      primary_certification_date?: string
      primary_expiry_date?: string
    }
    const payload: Record<string, string> = {
      welder_code: extra.welder_code || '',
      full_name: extra.full_name || '',
      phone: extra.phone || '',
      certification_number: extra.primary_certification_number || extra.certification_number || '',
      certification_level: extra.primary_certification_level || extra.certification_level || '',
      certification_date: extra.primary_certification_date || extra.certification_date || '',
      expiry_date: extra.primary_expiry_date || extra.expiry_date || '',
      is_active: extra.is_active ? '在职' : '离职',
    }
    const filename = `${extra.welder_code || 'welder'}-${dayjs().format('YYYYMMDD')}`
    switch (format) {
      case 'json': {
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${filename}.json`
        link.click()
        URL.revokeObjectURL(url)
        message.success('已导出 JSON')
        return
      }
      case 'csv': {
        const rows = [['字段', '值'], ...Object.entries(payload)]
        const csv = `\uFEFF${rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')}`
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${filename}.csv`
        link.click()
        URL.revokeObjectURL(url)
        message.success('已导出 CSV')
        return
      }
      default: {
        const exhaustive: never = format
        return exhaustive
      }
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <Spin size="large" tip="加载中..." />
        </div>
      </div>
    )
  }

  if (!welderData) {
    return (
      <div className="page-container">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <Alert
            message="焊工不存在"
            description="请检查焊工ID是否正确"
            type="error"
            showIcon
          />
        </div>
      </div>
    )
  }

  // 计算证书状态（在 welderData 存在之后）
  const certStatus = getCertificationStatus(welderData.primary_expiry_date || '')

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/welders')}
            >
              返回列表
            </Button>
            <Title level={2} style={{ margin: 0 }}>焊工详情</Title>
          </Space>
          <Space>
            <Dropdown
              menu={{
                items: [
                  { key: 'csv', label: '导出 CSV', onClick: () => handleExport('csv') },
                  { key: 'json', label: '导出 JSON', onClick: () => handleExport('json') },
                ],
              }}
            >
              <Button icon={<DownloadOutlined />}>
                导出信息
              </Button>
            </Dropdown>
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={handleDelete}
            >
              删除焊工
            </Button>
          </Space>
        </div>
      </div>

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: 24 }}>
        <Row gutter={[24, 24]}>
          <Col xs={24} md={8}>
            <div className="text-center">
              <Avatar size={120} icon={<UserOutlined />} src="" />
              <Title level={3} className="mt-3">
                {welderData.full_name}
              </Title>
              <Tag color="blue">{welderData.welder_code}</Tag>
            </div>
          </Col>
          <Col xs={24} md={16}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="焊工编号">
                {welderData.welder_code}
              </Descriptions.Item>
              <Descriptions.Item label="姓名">
                {welderData.full_name}
              </Descriptions.Item>
              <Descriptions.Item label="身份证号">
                {maskIdNumber(welderData.id_number || '')}
              </Descriptions.Item>
              <Descriptions.Item label="联系电话">
                {maskPhoneNumber(welderData.phone || '')}
              </Descriptions.Item>
              <Descriptions.Item label="证书编号">
                {welderData.primary_certification_number}
              </Descriptions.Item>
              <Descriptions.Item label="证书等级">
                <Tag color={getCertificationLevelName(welderData.primary_certification_level || '').color}>
                  {getCertificationLevelName(welderData.primary_certification_level || '').text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="发证日期">
                {welderData.primary_certification_date ? dayjs(welderData.primary_certification_date).format('YYYY-MM-DD') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="有效期至">
                <Space>
                  <Text>{welderData.primary_expiry_date ? dayjs(welderData.primary_expiry_date).format('YYYY-MM-DD') : '-'}</Text>
                  {welderData.primary_expiry_date && (
                    <Tag color={certStatus.color} icon={certStatus.icon}>
                      {certStatus.text}
                    </Tag>
                  )}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="资质工艺" span={2}>
                <Space wrap>
                  {welderData.qualified_processes ? (
                    JSON.parse(welderData.qualified_processes).map((process: string) => (
                          <Tag key={process} color="blue">
                            {process}
                          </Tag>
                        ))
                  ) : []}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={welderData.is_active ? 'success' : 'default'}>
                  {welderData.is_active ? '在职' : '离职'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="入职日期">
                {dayjs(welderData.created_at).format('YYYY-MM-DD')}
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
      </Card>

      {/* 证书管理 */}
      <Card
        title={
          <span>
            <SafetyCertificateOutlined /> 证书管理
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        {welderData.id ? (
          <CertificationList welderId={welderData.id} />
        ) : null}
      </Card>

      {/* 工作履历 */}
      {welderData.id ? (
        <div style={{ marginBottom: 24 }}>
          <WorkHistoryList welderId={welderData.id} />
        </div>
      ) : null}

      {/* 培训记录 */}
      {welderData.id ? (
        <div style={{ marginBottom: 24 }}>
          <TrainingRecordList welderId={welderData.id} />
        </div>
      ) : null}

      {/* 考核记录 */}
      {welderData.id ? (
        <div style={{ marginBottom: 24 }}>
          <AssessmentRecordList welderId={welderData.id} />
        </div>
      ) : null}

      {/* 焊接操作记录 */}
      {welderData.id ? (
        <div style={{ marginBottom: 24 }}>
          <WorkRecordList welderId={welderData.id} />
        </div>
      ) : null}
    </div>
  )
}

export default WeldersDetail
