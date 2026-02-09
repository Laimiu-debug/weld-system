import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Modal,
  message,
  Row,
  Col,
  Popconfirm,
  Statistic,
  Progress,
  Empty,
  Alert,
  Divider,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SendOutlined,
  RollbackOutlined,
  ClockCircleOutlined,
  FileWordOutlined,
  FilePdfOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { WPSRecord, WPSStatus, PaginatedResponse } from '@/types'
import { useAuthStore } from '@/store/authStore'
import wpsService, { WPSSummary } from '@/services/wps'
import { approvalApi } from '@/services/approval'
import ApprovalButton from '@/components/Approval/ApprovalButton'

const { Title, Text } = Typography
const { Search } = Input
const { RangePicker } = DatePicker
const { Option } = Select

const WPSList: React.FC = () => {
  const navigate = useNavigate()
  const { checkPermission, canCreateMore, user } = useAuthStore()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<WPSStatus | ''>('')
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })
  const [previewRecord, setPreviewRecord] = useState<WPSRecord | null>(null)
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [statusModalVisible, setStatusModalVisible] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<WPSRecord | null>(null)
  const [statusAction, setStatusAction] = useState<'submit' | 'approve' | 'reject' | 'withdraw'>('submit')

  // 从 modules_data 中提取关键字段
  const extractKeyFieldsFromModules = (modulesData: any) => {
    const extracted = {
      welding_process: '',
      base_material: '',
      filler_material: '',
    }

    if (!modulesData) return extracted

    // 遍历 modules_data，提取关键字段
    Object.values(modulesData).forEach((module: any) => {
      if (module && module.data) {
        // 优先使用 modules_data 中的数据
        extracted.welding_process = module.data.welding_process || extracted.welding_process
        extracted.base_material = module.data.base_material_spec || module.data.base_material || extracted.base_material
        extracted.filler_material = module.data.filler_material_classification || module.data.filler_material || extracted.filler_material
      }
    })

    return extracted
  }

  // 计算WPS统计数据
  const getWPSStats = (data: WPSSummary[] = []) => {
    const stats = {
      total: data.length,
      approved: data.filter(item => item.status === 'approved').length,
      review: data.filter(item => item.status === 'review').length,
      draft: data.filter(item => item.status === 'draft').length,
      highPriority: 0, // 后端暂时没有priority字段
    }
    return stats
  }

  // 调用实际API
  const fetchWPSList = async ({
    page = 1,
    pageSize = 20,
    search = '',
    status = '',
    dateRange = null,
  }: {
    page?: number
    pageSize?: number
    search?: string
    status?: WPSStatus | ''
    dateRange?: [dayjs.Dayjs, dayjs.Dayjs] | null
  }) => {
    try {
      const skip = (page - 1) * pageSize
      const data = await wpsService.getWPSList({
        skip,
        limit: pageSize,
        status: status || undefined,
        search_term: search || undefined,
      })

      // 转换为前端需要的格式
      const items = data.map(item => {
        // 优先从 modules_data 中提取数据
        const moduleFields = extractKeyFieldsFromModules(item.modules_data)

        return {
          id: item.id.toString(),
          wps_number: item.wps_number,
          title: item.title,
          status: item.status as WPSStatus,
          priority: 'normal' as const, // 默认值
          standard: item.company || '',
          base_material: moduleFields.base_material || item.base_material_spec || '',
          filler_material: moduleFields.filler_material || item.filler_material_classification || '',
          welding_process: moduleFields.welding_process || item.welding_process || '',
          joint_type: '',
          welding_position: '',
          created_at: item.created_at,
          updated_at: item.updated_at,
          user_id: 'current',
          view_count: 0,
          download_count: 0,
          // 审批相关字段
          approval_instance_id: item.approval_instance_id,
          approval_status: item.approval_status,
          workflow_name: item.workflow_name,
          can_approve: item.can_approve,
          can_submit_approval: item.can_submit_approval,
          submitter_id: item.submitter_id,
        }
      })

      return {
        success: true,
        data: {
          items,
          total: items.length, // 注意：后端需要返回total count
          page,
          page_size: pageSize,
          total_pages: Math.ceil(items.length / pageSize),
          has_next: items.length === pageSize,
          has_prev: page > 1,
        },
      }
    } catch (error) {
      console.error('获取WPS列表失败:', error)
      message.error('获取WPS列表失败')
      return {
        success: false,
        data: {
          items: [],
          total: 0,
          page,
          page_size: pageSize,
          total_pages: 0,
          has_next: false,
          has_prev: false,
        },
      }
    }
  }

  // 使用React Query获取数据
  const {
    data: wpsData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['wpsList', pagination.current, pagination.pageSize, searchText, statusFilter, dateRange],
    queryFn: () =>
      fetchWPSList({
        page: pagination.current,
        pageSize: pagination.pageSize,
        search: searchText,
        status: statusFilter,
        dateRange,
      }),
    onSuccess: (data) => {
      if (data.success && data.data) {
        setPagination(prev => ({
          ...prev,
          total: data.data?.total || 0,
        }))
      }
    },
  })

  // 获取状态配置
  const getStatusConfig = (status: WPSStatus) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿' },
      review: { color: 'processing', text: '审核中' },
      approved: { color: 'success', text: '已批准' },
      rejected: { color: 'error', text: '已拒绝' },
      archived: { color: 'default', text: '已归档' },
      obsolete: { color: 'warning', text: '已过时' },
    }
    return statusConfig[status] || statusConfig.draft
  }

  // 渲染WPS卡片
  const renderWPSCard = (record: WPSRecord) => (
    <Card
      key={record.id}
      className="wps-card"
      hoverable
      style={{ marginBottom: 16 }}
      cover={
        <div style={{ padding: '16px', backgroundColor: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space direction="vertical" size={0}>
                <Text strong style={{ fontSize: 16 }}>
                  {record.wps_number}
                </Text>
                <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
                  {record.title}
                </Text>
              </Space>
            </Col>
            <Col>
              <Space direction="vertical" size={4} align="end">
                <Space>
                  <Tag color={getStatusConfig(record.status as WPSStatus).color}>
                    {getStatusConfig(record.status as WPSStatus).text}
                  </Tag>
                  {record.approval_status && (
                    <Tag
                      color={
                        record.approval_status === 'approved'
                          ? 'success'
                          : record.approval_status === 'rejected'
                          ? 'error'
                          : record.approval_status === 'pending' || record.approval_status === 'in_progress'
                          ? 'processing'
                          : 'default'
                      }
                      icon={
                        record.approval_status === 'approved' ? (
                          <CheckCircleOutlined />
                        ) : record.approval_status === 'rejected' ? (
                          <CloseCircleOutlined />
                        ) : record.approval_status === 'pending' || record.approval_status === 'in_progress' ? (
                          <ClockCircleOutlined />
                        ) : null
                      }
                    >
                      {record.approval_status === 'approved'
                        ? '已批准'
                        : record.approval_status === 'rejected'
                        ? '已拒绝'
                        : record.approval_status === 'pending'
                        ? '待审批'
                        : record.approval_status === 'in_progress'
                        ? '审批中'
                        : record.approval_status}
                    </Tag>
                  )}
                </Space>
                {record.workflow_name && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    工作流: {record.workflow_name}
                  </Text>
                )}
              </Space>
            </Col>
          </Row>
        </div>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Row justify="space-between">
          <Col>
            <Text type="secondary">焊接方法:</Text>
            <Text style={{ marginLeft: 8 }}>{record.welding_process || '-'}</Text>
          </Col>
          <Col>
            <Text type="secondary">标准:</Text>
            <Text style={{ marginLeft: 8 }}>{record.standard || '-'}</Text>
          </Col>
        </Row>
        <Row justify="space-between">
          <Col>
            <Text type="secondary">母材:</Text>
            <Text style={{ marginLeft: 8 }}>{record.base_material || '-'}</Text>
          </Col>
          <Col>
            <Text type="secondary">创建时间:</Text>
            <Text style={{ marginLeft: 8 }}>{dayjs(record.created_at).format('YYYY-MM-DD')}</Text>
          </Col>
        </Row>
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* 审批状态操作按钮 */}
      {record.status === 'draft' && (
        <Alert
          message="草稿状态"
          description="此WPS处于草稿状态，可以提交审批"
          type="info"
          showIcon
          icon={<ClockCircleOutlined />}
          style={{ marginBottom: 12 }}
          action={
            <Button
              size="small"
              type="primary"
              icon={<SendOutlined />}
              onClick={() => handleSubmitApproval(record)}
            >
              提交审批
            </Button>
          }
        />
      )}

      {record.status === 'review' && (
        <Alert
          message="审核中"
          description="此WPS正在审核中，等待审批"
          type="warning"
          showIcon
          icon={<ClockCircleOutlined />}
          style={{ marginBottom: 12 }}
          action={
            <Space>
              {checkPermission('wps.approve') && (
                <>
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleApprove(record)}
                  >
                    批准
                  </Button>
                  <Button
                    size="small"
                    danger
                    icon={<CloseCircleOutlined />}
                    onClick={() => handleReject(record)}
                  >
                    拒绝
                  </Button>
                </>
              )}
              <Button
                size="small"
                icon={<RollbackOutlined />}
                onClick={() => handleWithdraw(record)}
              >
                撤回
              </Button>
            </Space>
          }
        />
      )}

      {record.status === 'approved' && (
        <Alert
          message="已批准"
          description="此WPS已通过审批，可以正式使用"
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
          style={{ marginBottom: 12 }}
        />
      )}

      {record.status === 'rejected' && (
        <Alert
          message="已拒绝"
          description="此WPS审批被拒绝，需要修改后重新提交"
          type="error"
          showIcon
          icon={<CloseCircleOutlined />}
          style={{ marginBottom: 12 }}
          action={
            <Button
              size="small"
              type="primary"
              icon={<SendOutlined />}
              onClick={() => handleSubmitApproval(record)}
            >
              重新提交
            </Button>
          }
        />
      )}

      {/* 操作按钮 */}
      <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="primary"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => navigate(`/wps/${record.id}`)}
            >
              查看
            </Button>
          </Tooltip>

          {checkPermission('wps.update') && record.status !== 'approved' && (
            <Tooltip title="编辑">
              <Button
                icon={<EditOutlined />}
                size="small"
                onClick={() => navigate(`/wps/${record.id}/edit`)}
              >
                编辑
              </Button>
            </Tooltip>
          )}

          <Tooltip title="预览">
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => handlePreview(record)}
            >
              预览
            </Button>
          </Tooltip>

          <Tooltip title="复制">
            <Button
              icon={<CopyOutlined />}
              size="small"
              onClick={() => handleCopy(record)}
            >
              复制
            </Button>
          </Tooltip>

          <Tooltip title="导出Word">
            <Button
              icon={<FileWordOutlined />}
              size="small"
              onClick={() => handleExportWord(record)}
            >
              Word
            </Button>
          </Tooltip>

          <Tooltip title="导出PDF">
            <Button
              icon={<FilePdfOutlined />}
              size="small"
              onClick={() => handleExportPDF(record)}
            >
              PDF
            </Button>
          </Tooltip>

          {/* 审批按钮 */}
          <ApprovalButton
            documentType="wps"
            documentId={parseInt(record.id)}
            documentNumber={record.wps_number}
            documentTitle={record.title}
            instanceId={record.approval_instance_id}
            status={record.approval_status || record.status}
            canSubmit={record.can_submit_approval}
            canApprove={record.can_approve}
            canCancel={record.submitter_id === user?.id}
            onSuccess={refetch}
            size="small"
          />
        </Space>

        <Space>
          {checkPermission('wps.delete') && record.status !== 'approved' && (
            <Tooltip title="删除">
              <Popconfirm
                title="确定要删除这个WPS吗？"
                description="删除后将无法恢复"
                onConfirm={() => handleDelete(record.id)}
                icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                >
                  删除
                </Button>
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      </Space>
    </Card>
  )

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理状态筛选
  const handleStatusFilter = (value: WPSStatus | '') => {
    setStatusFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理日期范围筛选
  const handleDateRangeChange = (dates: [dayjs.Dayjs, dayjs.Dayjs] | null) => {
    setDateRange(dates)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理表格分页变化
  const handleTableChange = (page: number, pageSize: number) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }))
  }

  // 处理导出Word
  const handleExportWord = async (record: WPSRecord) => {
    try {
      message.loading('正在生成Word文档...', 0)

      const response = await fetch(`/api/v1/wps/${record.id}/export/word`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('导出失败')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `WPS_${record.wps_number}_${new Date().toISOString().split('T')[0]}.docx`
      link.click()
      URL.revokeObjectURL(url)

      message.destroy()
      message.success('导出成功')
    } catch (error) {
      message.destroy()
      message.error('导出失败，请稍后重试')
      console.error('导出Word失败:', error)
    }
  }

  // 处理导出PDF - 使用浏览器打印功能
  const handleExportPDF = async (record: WPSRecord) => {
    try {
      message.loading('正在获取文档内容...', 0)

      // 获取WPS详情（包含document_html）
      const response = await fetch(`/api/v1/wps/${record.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('获取文档失败')
      }

      const wpsData = await response.json()
      message.destroy()

      // 打开打印预览窗口
      const printWindow = window.open('', '_blank')
      if (!printWindow) {
        message.error('无法打开打印窗口，请检查浏览器弹窗设置')
        return
      }

      // 生成打印页面HTML
      const printHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>WPS-${record.wps_number}</title>
          <style>
            @page {
              size: A4;
              margin: 2cm;
            }
            body {
              font-family: 'Microsoft YaHei', Arial, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 21cm;
              margin: 0 auto;
              padding: 20px;
            }
            h1 {
              text-align: center;
              color: #1890ff;
              margin-bottom: 10px;
            }
            h2, h3 {
              color: #1890ff;
              margin-top: 20px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 20px 0;
              page-break-inside: avoid;
            }
            table, th, td {
              border: 1px solid #ddd;
            }
            th, td {
              padding: 8px;
              text-align: left;
            }
            th {
              background-color: #f0f0f0;
              font-weight: bold;
            }
            hr {
              border: none;
              border-top: 2px solid #ddd;
              margin: 20px 0;
            }
            .footer {
              margin-top: 40px;
              text-align: center;
              font-size: 12px;
              color: #999;
            }
            @media print {
              body {
                padding: 0;
              }
              .no-print {
                display: none;
              }
            }
          </style>
        </head>
        <body>
          ${wpsData.document_html || '<p>文档内容为空，请先在编辑页面使用文档编辑模式编辑内容</p>'}
          <div class="footer">
            <p>打印日期: ${new Date().toLocaleString('zh-CN')}</p>
          </div>
          <div class="no-print" style="position: fixed; top: 20px; right: 20px;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
              打印/保存为PDF
            </button>
            <button onclick="window.close()" style="padding: 10px 20px; background: #999; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-left: 10px;">
              关闭
            </button>
          </div>
        </body>
        </html>
      `

      printWindow.document.write(printHTML)
      printWindow.document.close()

      message.success('已打开打印预览窗口，请使用浏览器的"打印"功能保存为PDF')
    } catch (error) {
      message.destroy()
      message.error('打开打印预览失败')
      console.error('导出PDF失败:', error)
    }
  }

  // 处理删除
  const handleDelete = async (id: string) => {
    try {
      await wpsService.deleteWPS(parseInt(id))
      message.success('删除成功')
      refetch()
    } catch (error) {
      console.error('删除WPS失败:', error)
      message.error('删除失败')
    }
  }

  // 获取WPS配额
  const getWPSQuota = (membershipTier: string) => {
    const quotaMap: Record<string, number> = {
      free: 10,
      personal_pro: 30,
      personal_advanced: 50,
      personal_flagship: 100,
      enterprise: 200,
      enterprise_pro: 400,
      enterprise_pro_max: 500,
    }
    return quotaMap[membershipTier] || 10
  }

  // 处理预览
  const handlePreview = (record: WPSRecord) => {
    setPreviewRecord(record)
    setPreviewModalVisible(true)
  }

  // 处理复制
  const handleCopy = async (record: WPSRecord) => {
    try {
      // 获取完整的 WPS 数据
      const response = await wpsService.getWPS(parseInt(record.id))
      if (!response.success || !response.data) {
        message.error('获取WPS数据失败')
        return
      }

      const wpsData = response.data

      // 创建新的 WPS 数据
      const copyData = {
        ...wpsData,
        title: `${wpsData.title} (副本)`,
        wps_number: `${wpsData.wps_number}-COPY-${Date.now()}`,
        status: 'draft',
      }

      // 删除不需要的字段
      delete (copyData as any).id
      delete (copyData as any).created_at
      delete (copyData as any).updated_at
      delete (copyData as any).created_by
      delete (copyData as any).updated_by

      // 创建新 WPS
      const createResponse = await wpsService.createWPS(copyData)
      if (createResponse.success) {
        message.success('复制成功')
        refetch()
      } else {
        message.error(createResponse.message || '复制失败')
      }
    } catch (error: any) {
      console.error('复制WPS失败:', error)
      message.error(error.response?.data?.detail || '复制失败')
    }
  }

  // 处理提交审批
  const handleSubmitApproval = (record: WPSRecord) => {
    setCurrentRecord(record)
    setStatusAction('submit')
    setStatusModalVisible(true)
  }

  // 处理批准
  const handleApprove = (record: WPSRecord) => {
    setCurrentRecord(record)
    setStatusAction('approve')
    setStatusModalVisible(true)
  }

  // 处理拒绝
  const handleReject = (record: WPSRecord) => {
    setCurrentRecord(record)
    setStatusAction('reject')
    setStatusModalVisible(true)
  }

  // 处理撤回
  const handleWithdraw = (record: WPSRecord) => {
    setCurrentRecord(record)
    setStatusAction('withdraw')
    setStatusModalVisible(true)
  }

  // 确认状态变更
  const handleStatusChange = async (values: any) => {
    if (!currentRecord) return

    try {
      let newStatus = ''
      let statusUpdate: any = {
        status: '',
        reason: values.reason || '',
      }

      switch (statusAction) {
        case 'submit':
          // 提交审批：调用审批系统API
          await approvalApi.submitForApproval({
            document_type: 'wps',
            document_ids: [parseInt(currentRecord.id)],
            notes: values.reason || ''
          })

          // 更新WPS状态为审核中
          newStatus = 'review'
          statusUpdate.status = 'review'
          await wpsService.updateWPSStatus(parseInt(currentRecord.id), statusUpdate)
          break
        case 'approve':
          newStatus = 'approved'
          statusUpdate.status = 'approved'
          statusUpdate.approved_by = user?.id
          await wpsService.updateWPSStatus(parseInt(currentRecord.id), statusUpdate)
          break
        case 'reject':
          newStatus = 'rejected'
          statusUpdate.status = 'rejected'
          statusUpdate.reviewed_by = user?.id
          await wpsService.updateWPSStatus(parseInt(currentRecord.id), statusUpdate)
          break
        case 'withdraw':
          newStatus = 'draft'
          statusUpdate.status = 'draft'
          await wpsService.updateWPSStatus(parseInt(currentRecord.id), statusUpdate)
          break
      }

      const actionText = {
        submit: '提交审批',
        approve: '批准',
        reject: '拒绝',
        withdraw: '撤回',
      }[statusAction]

      message.success(`${actionText}成功`)
      setStatusModalVisible(false)
      setCurrentRecord(null)
      refetch()
    } catch (error: any) {
      console.error('更新状态失败:', error)
      message.error(error.response?.data?.detail || '操作失败')
    }
  }



  return (
    <div className="wps-list-container">
      <div className="page-header" style={{ justifyContent: 'center' }}>
        <div className="page-title" style={{ textAlign: 'center' }}>
          <Title level={2}>WPS管理</Title>
          <Text type="secondary">
            焊接工艺规程 (Welding Procedure Specification) 管理
          </Text>
        </div>
      </div>

      {/* 统计卡片 */}
      {wpsData?.data?.items && (
        <Row gutter={[16, 16]} className="stats-cards">
          <Col xs={12} sm={8} md={6}>
            <Card className="stat-card">
              <Statistic
                title="总计"
                value={getWPSStats(wpsData.data.items).total}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card className="stat-card">
              <Statistic
                title="已批准"
                value={getWPSStats(wpsData.data.items).approved}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card className="stat-card">
              <Statistic
                title="审核中"
                value={getWPSStats(wpsData.data.items).review}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card className="stat-card">
              <Statistic
                title="高优先级"
                value={getWPSStats(wpsData.data.items).highPriority}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 配额提醒 */}
      {(() => {
        const tier = (user as any)?.member_tier || user?.membership_tier || 'personal_free'
        return tier !== 'enterprise_pro_max' && (
          <Alert
            message={`WPS配额使用情况: ${wpsData?.data?.total || 0}/${getWPSQuota(tier)}`}
            description={
              <Progress
                percent={((wpsData?.data?.total || 0) / getWPSQuota(tier)) * 100}
                status={
                  ((wpsData?.data?.total || 0) / getWPSQuota(tier)) >= 0.8
                    ? 'exception'
                    : 'normal'
                }
              />
            }
            type="info"
            showIcon
            className="mb-4"
          />
        )
      })()}

      <Card className="wps-list-card">
        {/* 搜索和筛选区域 */}
        <Row gutter={[16, 16]} className="search-filters" style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索WPS编号或标题"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="筛选状态"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={handleStatusFilter}
            >
              <Option value="draft">草稿</Option>
              <Option value="review">审核中</Option>
              <Option value="approved">已批准</Option>
              <Option value="rejected">已拒绝</Option>
              <Option value="archived">已归档</Option>
              <Option value="obsolete">已过时</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              placeholder={['开始日期', '结束日期']}
              size="large"
              style={{ width: '100%' }}
              onChange={handleDateRangeChange}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                size="large"
                onClick={() => navigate('/wps/create')}
                disabled={!canCreateMore('wps', wpsData?.data?.total || 0)}
              >
                创建WPS
              </Button>
              <Button
                icon={<ReloadOutlined />}
                size="large"
                onClick={() => refetch()}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        {/* 卡片列表区域 */}
        <Spin spinning={isLoading}>
          {wpsData?.data?.items && wpsData.data.items.length > 0 ? (
            <div className="wps-cards-container">
              {wpsData.data.items.map(record => renderWPSCard(record))}

              {/* 分页信息 */}
              <Row justify="center" style={{ marginTop: 24 }}>
                <Text type="secondary">
                  第 {pagination.current} 页，共 {Math.ceil(pagination.total / pagination.pageSize)} 页
                  （总计 {pagination.total} 条）
                </Text>
              </Row>

              {/* 分页按钮 */}
              <Row justify="center" gutter={[8, 8]} style={{ marginTop: 16 }}>
                <Col>
                  <Button
                    disabled={pagination.current === 1}
                    onClick={() => handleTableChange(pagination.current - 1, pagination.pageSize)}
                  >
                    上一页
                  </Button>
                </Col>
                <Col>
                  <Button
                    disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
                    onClick={() => handleTableChange(pagination.current + 1, pagination.pageSize)}
                  >
                    下一页
                  </Button>
                </Col>
                <Col>
                  <Select
                    value={pagination.pageSize}
                    onChange={(value) => handleTableChange(1, value)}
                    style={{ width: 100 }}
                  >
                    <Option value={10}>10条/页</Option>
                    <Option value={20}>20条/页</Option>
                    <Option value={50}>50条/页</Option>
                    <Option value={100}>100条/页</Option>
                  </Select>
                </Col>
              </Row>
            </div>
          ) : (
            <Empty
              description="暂无WPS记录"
              style={{ marginTop: 48, marginBottom: 48 }}
            >
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => navigate('/wps/create')}
              >
                创建第一个WPS
              </Button>
            </Empty>
          )}
        </Spin>
      </Card>

      {/* 预览模态框 */}
      <Modal
        title={`预览 - ${previewRecord?.wps_number}`}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        width={900}
        style={{ maxHeight: '90vh' }}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            onClick={() => {
              setPreviewModalVisible(false)
              navigate(`/wps/${previewRecord?.id}/edit`)
            }}
          >
            编辑
          </Button>,
        ]}
      >
        {previewRecord && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 基本信息 */}
            <div>
              <Title level={5}>基本信息</Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>WPS编号:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.wps_number}</Text>
                </div>
                <div>
                  <Text strong>标题:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.title}</Text>
                </div>
                <div>
                  <Text strong>状态:</Text>
                  <Tag
                    color={getStatusConfig(previewRecord.status as WPSStatus).color}
                    style={{ marginLeft: 16 }}
                  >
                    {getStatusConfig(previewRecord.status as WPSStatus).text}
                  </Tag>
                </div>
                <div>
                  <Text strong>焊接方法:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.welding_process || '-'}</Text>
                </div>
                <div>
                  <Text strong>母材:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.base_material || '-'}</Text>
                </div>
                <div>
                  <Text strong>填充金属:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.filler_material || '-'}</Text>
                </div>
                <div>
                  <Text strong>标准:</Text>
                  <Text style={{ marginLeft: 16 }}>{previewRecord.standard || '-'}</Text>
                </div>
                <div>
                  <Text strong>创建时间:</Text>
                  <Text style={{ marginLeft: 16 }}>
                    {dayjs(previewRecord.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Text>
                </div>
                <div>
                  <Text strong>最后更新:</Text>
                  <Text style={{ marginLeft: 16 }}>
                    {dayjs(previewRecord.updated_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Text>
                </div>
              </Space>
            </div>

            {/* 模块数据 */}
            {previewRecord.modules_data && Object.keys(previewRecord.modules_data).length > 0 && (
              <div>
                <Title level={5}>模块数据详情</Title>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {Object.entries(previewRecord.modules_data).map(([moduleId, moduleContent]: [string, any]) => (
                    <Card key={moduleId} size="small" title={moduleContent.customName || moduleContent.moduleId || moduleId}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        {moduleContent.data && Object.entries(moduleContent.data).map(([key, value]: [string, any]) => (
                          <div key={key}>
                            <Text strong>{key}:</Text>
                            <Text style={{ marginLeft: 16 }}>
                              {typeof value === 'object' ? JSON.stringify(value) : String(value || '-')}
                            </Text>
                          </div>
                        ))}
                      </Space>
                    </Card>
                  ))}
                </Space>
              </div>
            )}
          </Space>
        )}
      </Modal>

      {/* 状态变更模态框 */}
      <Modal
        title={
          statusAction === 'submit' ? '提交审批' :
          statusAction === 'approve' ? '批准WPS' :
          statusAction === 'reject' ? '拒绝WPS' :
          '撤回审批'
        }
        open={statusModalVisible}
        onCancel={() => {
          setStatusModalVisible(false)
          setCurrentRecord(null)
        }}
        onOk={() => {
          Modal.confirm({
            title: '确认操作',
            content: `确定要${
              statusAction === 'submit' ? '提交审批' :
              statusAction === 'approve' ? '批准' :
              statusAction === 'reject' ? '拒绝' :
              '撤回'
            }这个WPS吗？`,
            onOk: () => {
              handleStatusChange({
                reason: (document.getElementById('status-reason') as HTMLTextAreaElement)?.value || ''
              })
            }
          })
        }}
        okText="确认"
        cancelText="取消"
      >
        {currentRecord && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>WPS编号：</Text>
              <Text>{currentRecord.wps_number}</Text>
            </div>
            <div>
              <Text strong>标题：</Text>
              <Text>{currentRecord.title}</Text>
            </div>
            <div>
              <Text strong>当前状态：</Text>
              <Tag color={getStatusConfig(currentRecord.status as WPSStatus).color}>
                {getStatusConfig(currentRecord.status as WPSStatus).text}
              </Tag>
            </div>
            <div>
              <Text strong>
                {statusAction === 'submit' ? '提交说明' :
                 statusAction === 'approve' ? '批准意见' :
                 statusAction === 'reject' ? '拒绝原因' :
                 '撤回原因'}
                ：
              </Text>
              <Input.TextArea
                id="status-reason"
                rows={4}
                placeholder={
                  statusAction === 'submit' ? '请输入提交说明（可选）' :
                  statusAction === 'approve' ? '请输入批准意见（可选）' :
                  statusAction === 'reject' ? '请输入拒绝原因' :
                  '请输入撤回原因（可选）'
                }
                style={{ marginTop: 8 }}
              />
            </div>
            {statusAction === 'submit' && (
              <Alert
                message="提示"
                description="提交后，WPS将进入审核流程，需要相关人员审批后才能使用。"
                type="info"
                showIcon
              />
            )}
            {statusAction === 'approve' && (
              <Alert
                message="提示"
                description="批准后，WPS将可以正式使用，且不能再编辑。"
                type="warning"
                showIcon
              />
            )}
            {statusAction === 'reject' && (
              <Alert
                message="提示"
                description="拒绝后，WPS将返回草稿状态，需要修改后重新提交。"
                type="error"
                showIcon
              />
            )}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default WPSList