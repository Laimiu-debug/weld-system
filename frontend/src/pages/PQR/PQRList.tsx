import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Input,
  Select,
  Tag,
  Tooltip,
  message,
  Row,
  Col,
  Popconfirm,
  Statistic,
  Progress,
  Alert,
  Divider,
  Spin,
  Empty,
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
  ExperimentOutlined,
  CopyOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useAuthStore } from '@/store/authStore'
import { usePreferencesStore } from '@/store/preferencesStore'
import pqrService, { PQRSummary } from '@/services/pqr'
import { ApprovalButton } from '@/components/Approval/ApprovalButton'
import { sanitizeDocumentHtml } from '@/utils/sanitizeHtml'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

const PQRList: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { checkPermission, canCreateMore, user } = useAuthStore()
  const defaultPageSize = usePreferencesStore((s) => s.preferences.pageSize) || 20
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [qualificationFilter, setQualificationFilter] = useState<string>('')
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: defaultPageSize,
    total: 0,
  })

  useEffect(() => {
    setPagination((prev) => ({ ...prev, pageSize: defaultPageSize, current: 1 }))
  }, [defaultPageSize])

  // 使用真实API获取PQR列表
  const {
    data: pqrData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['pqrList', pagination.current, pagination.pageSize, searchText, statusFilter, qualificationFilter],
    queryFn: async () => {
      const result = await pqrService.list({
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: searchText || undefined,
        status: statusFilter || undefined,
        qualification_result: qualificationFilter || undefined,
      })
      setPagination(prev => ({ ...prev, total: result.total }))
      return result
    },
  })

  // 删除PQR
  const deleteMutation = useMutation({
    mutationFn: (id: number) => pqrService.delete(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['pqrList'] })
    },
    onError: () => {
      message.error('删除失败')
    },
  })

  // 复制PQR
  const duplicateMutation = useMutation({
    mutationFn: (id: number) => pqrService.duplicate(id),
    onSuccess: () => {
      message.success('复制成功')
      queryClient.invalidateQueries({ queryKey: ['pqrList'] })
    },
    onError: (error: any) => {
      console.error('复制PQR失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '复制失败'
      message.error(errorMsg)
    },
  })

  // 导出Word
  const handleExportWord = async (id: number, pqr_number: string) => {
    try {
      message.loading('正在生成Word文档...', 0)

      const response = await fetch(`/api/v1/pqr/${id}/export/word`, {
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
      link.download = `PQR_${pqr_number}_${new Date().toISOString().split('T')[0]}.docx`
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

  // 导出PDF - 使用浏览器打印功能
  const handleExportPDF = async (id: number, pqr_number: string) => {
    try {
      message.loading('正在获取文档内容...', 0)

      // 获取PQR详情（包含document_html）
      const response = await fetch(`/api/v1/pqr/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('获取文档失败')
      }

      const pqrData = await response.json()
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
          <title>PQR-${pqr_number}</title>
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
          ${sanitizeDocumentHtml(pqrData.document_html) || '<p>文档内容为空，请先在编辑页面使用文档编辑模式编辑内容</p>'}
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

  // 导出Excel
  const handleExportExcel = async (id: number, title: string) => {
    try {
      const blob = await pqrService.exportExcel(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${title}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
      message.success('导出Excel成功')
    } catch (error) {
      message.error('导出Excel失败')
    }
  }

  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      draft: { color: 'default', text: '草稿' },
      review: { color: 'processing', text: '审核中' },
      approved: { color: 'success', text: '已批准' },
      rejected: { color: 'error', text: '已拒绝' },
      archived: { color: 'warning', text: '已归档' },
    }
    return statusConfig[status] || { color: 'default', text: status }
  }

  // 获取合格判定配置
  const getQualificationConfig = (result: string) => {
    if (!result) return null
    const qualificationConfig: Record<string, { color: string; text: string }> = {
      qualified: { color: 'success', text: '合格' },
      failed: { color: 'error', text: '不合格' },
      pending: { color: 'warning', text: '待定' },
    }
    return qualificationConfig[result] || { color: 'default', text: result }
  }

  // 渲染PQR卡片
  const renderPQRCard = (record: PQRSummary) => {
    const qualificationConfig = getQualificationConfig(record.qualification_result || '')

    return (
      <Card
        key={record.id}
        className="pqr-card"
        hoverable
        style={{ marginBottom: 16 }}
        cover={
          <div style={{ padding: '16px', backgroundColor: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Space direction="vertical" size={0}>
                  <Text strong style={{ fontSize: 16 }}>
                    {record.pqr_number}
                  </Text>
                  <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
                    {record.title}
                  </Text>
                </Space>
              </Col>
              <Col>
                <Space direction="vertical" size={4} align="end">
                  <Space>
                    <Tag color={getStatusConfig(record.status).color}>
                      {getStatusConfig(record.status).text}
                    </Tag>
                    {qualificationConfig && (
                      <Tag color={qualificationConfig.color}>
                        {qualificationConfig.text}
                      </Tag>
                    )}
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
              <Text type="secondary">母材规格:</Text>
              <Text style={{ marginLeft: 8 }}>{record.base_material_spec || '-'}</Text>
            </Col>
            <Col>
              <Text type="secondary">试验日期:</Text>
              <Text style={{ marginLeft: 8 }}>
                {record.test_date ? dayjs(record.test_date).format('YYYY-MM-DD') : '-'}
              </Text>
            </Col>
          </Row>
          <Row justify="space-between">
            <Col>
              <Text type="secondary">焊接工艺:</Text>
              <Text style={{ marginLeft: 8 }}>{record.welding_process || '-'}</Text>
            </Col>
            <Col>
              <Text type="secondary">评定结果:</Text>
              <Text style={{ marginLeft: 8 }}>
                {record.qualification_result === 'qualified' && <Tag color="success">合格</Tag>}
                {record.qualification_result === 'pending' && <Tag color="warning">待评定</Tag>}
                {record.qualification_result === 'failed' && <Tag color="error">不合格</Tag>}
                {!record.qualification_result && '-'}
              </Text>
            </Col>
          </Row>
          <Row justify="space-between">
            <Col>
              <Text type="secondary">关联WPS:</Text>
              <Text style={{ marginLeft: 8 }}>{record.wps_number || '-'}</Text>
            </Col>
            <Col>
              <Text type="secondary">创建时间:</Text>
              <Text style={{ marginLeft: 8 }}>{dayjs(record.created_at).format('YYYY-MM-DD')}</Text>
            </Col>
          </Row>
        </Space>

        <Divider style={{ margin: '12px 0' }} />

        {/* 审批状态提示 */}
        {record.approval_status === 'approved' && (
          <Alert
            message="已批准"
            description="此PQR已通过审批，评定结果有效"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {record.approval_status === 'rejected' && (
          <Alert
            message="已拒绝"
            description="此PQR审批被拒绝，需要修改后重新提交"
            type="error"
            showIcon
            icon={<CloseCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {(record.approval_status === 'pending' || record.approval_status === 'in_progress') && (
          <Alert
            message="审批中"
            description="此PQR正在审批流程中，请等待审批完成"
            type="warning"
            showIcon
            icon={<ClockCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {!record.approval_status && record.status === 'draft' && (
          <Alert
            message="草稿状态"
            description="此PQR处于草稿状态，可以提交审批"
            type="info"
            showIcon
            icon={<ClockCircleOutlined />}
            style={{ marginBottom: 12 }}
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
                onClick={() => navigate(`/pqr/${record.id}`)}
              >
                查看
              </Button>
            </Tooltip>

            {checkPermission('pqr.update') && (
              <Tooltip title="编辑">
                <Button
                  icon={<EditOutlined />}
                  size="small"
                  onClick={() => navigate(`/pqr/${record.id}/edit`)}
                >
                  编辑
                </Button>
              </Tooltip>
            )}

            <Tooltip title="复制">
              <Button
                icon={<CopyOutlined />}
                size="small"
                onClick={() => duplicateMutation.mutate(record.id)}
              >
                复制
              </Button>
            </Tooltip>

            <Tooltip title="导出Word">
              <Button
                icon={<FileWordOutlined />}
                size="small"
                onClick={() => handleExportWord(record.id, record.pqr_number)}
              >
                Word
              </Button>
            </Tooltip>

            <Tooltip title="导出PDF">
              <Button
                icon={<FilePdfOutlined />}
                size="small"
                onClick={() => handleExportPDF(record.id, record.pqr_number)}
              >
                PDF
              </Button>
            </Tooltip>

            <Tooltip title="导出Excel">
              <Button
                icon={<FileExcelOutlined />}
                size="small"
                onClick={() => handleExportExcel(record.id, record.title)}
              >
                Excel
              </Button>
            </Tooltip>

            {/* 审批按钮 */}
            <ApprovalButton
              documentType="pqr"
              documentId={record.id}
              documentNumber={record.pqr_number}
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
            {checkPermission('pqr.delete') && (
              <Tooltip title="删除">
                <Popconfirm
                  title="确定要删除这条PQR记录吗？"
                  description="删除后将无法恢复"
                  onConfirm={() => deleteMutation.mutate(record.id)}
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
  }

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理状态筛选
  const handleStatusFilter = (value: string) => {
    setStatusFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理合格判定筛选
  const handleQualificationFilter = (value: string) => {
    setQualificationFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理表格分页变化
  const handleTableChange = (page: number, pageSize: number) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }))
  }

  // 计算统计数据
  const getPQRStats = () => {
    const items = pqrData?.items || []
    return {
      total: pqrData?.total || 0,
      qualified: items.filter(item => item.qualification_result === 'qualified').length,
      pending: items.filter(item => item.qualification_result === 'pending').length,
      failed: items.filter(item => item.qualification_result === 'failed').length,
      approved: items.filter(item => item.status === 'approved').length,
    }
  }

  // 获取PQR配额
  const getPQRQuota = (membershipTier: string) => {
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

  const stats = getPQRStats()
  const tier = (user as any)?.member_tier || user?.membership_tier || 'personal_free'

  return (
    <div className="pqr-list-container list-page">
      <ListPageHeader
        title="PQR管理"
        description="工艺评定记录 (Procedure Qualification Record) 管理"
      />

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="stats-cards" style={{ marginBottom: 16 }}>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="总计"
              value={stats.total}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1F5EFF' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="合格"
              value={stats.qualified}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="待处理"
              value={stats.pending}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="已批准"
              value={stats.approved}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1546c9' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 配额提醒 */}
      {tier !== 'enterprise_pro_max' && (
        <Alert
          message={`PQR配额使用情况: ${stats.total}/${getPQRQuota(tier)}`}
          description={
            <Progress
              percent={(stats.total / getPQRQuota(tier)) * 100}
              status={
                (stats.total / getPQRQuota(tier)) >= 0.8
                  ? 'exception'
                  : 'normal'
              }
            />
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card>
        {/* 搜索和筛选区域 */}
        <div className="doc-list-toolbar">
          <div className="toolbar-search">
            <Search
              placeholder="搜索PQR编号或标题"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </div>
          <div className="toolbar-filter">
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
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="合格判定"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={handleQualificationFilter}
            >
              <Option value="qualified">合格</Option>
              <Option value="failed">不合格</Option>
              <Option value="pending">待定</Option>
            </Select>
          </div>
          <div className="toolbar-actions">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="large"
              onClick={() => navigate('/pqr/create')}
              disabled={!canCreateMore('pqr', stats.total)}
            >
              创建PQR
            </Button>
            <Button
              icon={<ReloadOutlined />}
              size="large"
              onClick={() => refetch()}
            >
              刷新
            </Button>
          </div>
        </div>

        {/* 卡片列表区域 */}
        <Spin spinning={isLoading}>
          {pqrData?.items && pqrData.items.length > 0 ? (
            <div className="pqr-cards-container">
              {pqrData.items.map(record => renderPQRCard(record))}

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
              description="暂无PQR记录"
              style={{ marginTop: 48, marginBottom: 48 }}
            >
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => navigate('/pqr/create')}
              >
                创建第一个PQR
              </Button>
            </Empty>
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default PQRList
