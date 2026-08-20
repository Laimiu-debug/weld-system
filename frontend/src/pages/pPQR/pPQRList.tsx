import React, { useState } from 'react'
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
  Pagination,
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
  SwapOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { useAuthStore } from '@/store/authStore'
import ppqrService, { PPQRSummary } from '@/services/ppqr'
import { ApprovalButton } from '@/components/Approval/ApprovalButton'
import { sanitizeDocumentHtml } from '@/utils/sanitizeHtml'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

const PPQRList: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { checkPermission, canCreateMore, user } = useAuthStore()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [conclusionFilter, setConclusionFilter] = useState<string>('')
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  })

  // 使用真实API获取pPQR列表
  const {
    data: ppqrData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['ppqrList', pagination.current, pagination.pageSize, searchText, statusFilter, conclusionFilter],
    queryFn: async () => {
      const result = await ppqrService.list({
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: searchText || undefined,
        status: statusFilter || undefined,
        test_conclusion: conclusionFilter || undefined,
      })
      setPagination(prev => ({ ...prev, total: result.total }))
      return result
    },
  })

  // 删除pPQR
  const deleteMutation = useMutation({
    mutationFn: (id: number) => ppqrService.delete(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['ppqrList'] })
    },
    onError: () => {
      message.error('删除失败')
    },
  })

  // 复制pPQR
  const duplicateMutation = useMutation({
    mutationFn: (id: number) => ppqrService.duplicate(id),
    onSuccess: () => {
      message.success('复制成功')
      queryClient.invalidateQueries({ queryKey: ['ppqrList'] })
    },
    onError: () => {
      message.error('复制失败')
    },
  })



  // 获取状态配置
  const getStatusConfig = (status: string) => {
    const configMap: Record<string, { color: string; text: string }> = {
      draft: { color: 'default', text: '草稿' },
      testing: { color: 'processing', text: '试验中' },
      completed: { color: 'success', text: '已完成' },
      converted: { color: 'cyan', text: '已转换' },
    }
    return configMap[status] || { color: 'default', text: status }
  }

  // 获取试验结论配置
  const getConclusionConfig = (conclusion: string | undefined) => {
    if (!conclusion) return null
    const configMap: Record<string, { color: string; text: string }> = {
      qualified: { color: 'success', text: '合格' },
      pending: { color: 'warning', text: '待定' },
      failed: { color: 'error', text: '不合格' },
    }
    return configMap[conclusion] || { color: 'default', text: conclusion }
  }

  // 渲染pPQR卡片
  const renderPPQRCard = (record: PPQRSummary) => {
    const statusConfig = getStatusConfig(record.status)
    const conclusionConfig = getConclusionConfig(record.test_conclusion)

    return (
      <Card
        key={record.id}
        className="ppqr-card"
        hoverable
        style={{ marginBottom: 16 }}
        cover={
          <div style={{ padding: '16px', backgroundColor: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Space direction="vertical" size={0}>
                  <Text strong style={{ fontSize: 16 }}>
                    {record.ppqr_number}
                  </Text>
                  <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
                    {record.title}
                  </Text>
                </Space>
              </Col>
              <Col>
                <Space direction="vertical" size={4} align="end">
                  <Space>
                    <Tag color={statusConfig.color}>{statusConfig.text}</Tag>
                    {record.convert_to_pqr === 'yes' && <Tag color="success">已转PQR</Tag>}
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
              <Text type="secondary">版本:</Text>
              <Text style={{ marginLeft: 8 }}>{record.revision || 'A'}</Text>
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
              <Text type="secondary">试验结论:</Text>
              <Text style={{ marginLeft: 8 }}>
                {conclusionConfig ? (
                  <Tag color={conclusionConfig.color}>{conclusionConfig.text}</Tag>
                ) : (
                  '-'
                )}
              </Text>
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
            description="此pPQR已通过审批，试验结果有效"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {record.approval_status === 'rejected' && (
          <Alert
            message="已拒绝"
            description="此pPQR审批被拒绝，需要修改后重新提交"
            type="error"
            showIcon
            icon={<CloseCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {(record.approval_status === 'pending' || record.approval_status === 'in_progress') && (
          <Alert
            message="审批中"
            description="此pPQR正在审批流程中，请等待审批完成"
            type="warning"
            showIcon
            icon={<ClockCircleOutlined />}
            style={{ marginBottom: 12 }}
          />
        )}

        {!record.approval_status && record.status === 'draft' && (
          <Alert
            message="草稿状态"
            description="此pPQR处于草稿状态，可以提交审批"
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
                onClick={() => navigate(`/ppqr/${record.id}`)}
              >
                查看
              </Button>
            </Tooltip>

            {checkPermission('ppqr.update') && (
              <Tooltip title="编辑">
                <Button
                  icon={<EditOutlined />}
                  size="small"
                  onClick={() => navigate(`/ppqr/${record.id}/edit`)}
                >
                  编辑
                </Button>
              </Tooltip>
            )}

            <Tooltip title="复制">
              <Button
                icon={<CopyOutlined />}
                size="small"
                onClick={() => handleDuplicate(record.id)}
              >
                复制
              </Button>
            </Tooltip>

            <Tooltip title="导出Word">
              <Button
                icon={<FileWordOutlined />}
                size="small"
                onClick={() => handleExportWord(record.id, record.ppqr_number)}
              >
                Word
              </Button>
            </Tooltip>

            <Tooltip title="导出PDF">
              <Button
                icon={<FilePdfOutlined />}
                size="small"
                onClick={() => handleExportPDF(record.id, record.ppqr_number)}
              >
                PDF
              </Button>
            </Tooltip>

            {record.convert_to_pqr !== 'yes' && (
              <Tooltip title="转换为PQR">
                <Popconfirm
                  title="确定要转换为PQR吗？"
                  onConfirm={() => handleConvertToPQR(record.id)}
                  icon={<ExclamationCircleOutlined style={{ color: '#1890ff' }} />}
                >
                  <Button
                    icon={<SwapOutlined />}
                    size="small"
                  >
                    转PQR
                  </Button>
                </Popconfirm>
              </Tooltip>
            )}

            {/* 审批按钮 */}
            <ApprovalButton
              documentType="ppqr"
              documentId={record.id}
              documentNumber={record.ppqr_number}
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
            {checkPermission('ppqr.delete') && (
              <Tooltip title="删除">
                <Popconfirm
                  title="确定要删除这个pPQR吗？"
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

  // 处理结论筛选
  const handleConclusionFilter = (value: string) => {
    setConclusionFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  // 处理分页变化
  const handlePageChange = (page: number, pageSize: number) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }))
  }

  // 处理删除
  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  // 处理复制
  const handleDuplicate = (id: number) => {
    duplicateMutation.mutate(id)
  }

  // 处理导出Word
  const handleExportWord = async (id: number, ppqr_number: string) => {
    try {
      message.loading('正在生成Word文档...', 0)

      const response = await fetch(`/api/v1/ppqr/${id}/export/word`, {
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
      link.download = `pPQR_${ppqr_number}_${new Date().toISOString().split('T')[0]}.docx`
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
  const handleExportPDF = async (id: number, ppqr_number: string) => {
    try {
      message.loading('正在获取文档内容...', 0)

      // 获取pPQR详情（包含document_html）
      const response = await fetch(`/api/v1/ppqr/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('获取文档失败')
      }

      const ppqrData = await response.json()
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
          <title>pPQR-${ppqr_number}</title>
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
          ${sanitizeDocumentHtml(ppqrData.document_html) || '<p>文档内容为空，请先在编辑页面使用文档编辑模式编辑内容</p>'}
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

  // 处理转换为PQR
  const handleConvertToPQR = async (id: number) => {
    try {
      await ppqrService.convertToPQR(id)
      message.success('转换成功')
      queryClient.invalidateQueries({ queryKey: ['ppqrList'] })
    } catch (error) {
      message.error('转换失败')
    }
  }

  // 计算统计数据
  const getPPQRStats = () => {
    const items = ppqrData?.items || []
    return {
      total: ppqrData?.total || 0,
      draft: items.filter((item: PPQRSummary) => item.status === 'draft').length,
      testing: items.filter((item: PPQRSummary) => item.status === 'testing').length,
      completed: items.filter((item: PPQRSummary) => item.status === 'completed').length,
      converted: items.filter((item: PPQRSummary) => item.status === 'converted').length,
    }
  }

  const stats = getPPQRStats()

  // 获取pPQR配额
  const getPPQRQuota = (membershipTier: string) => {
    const quotaMap: Record<string, number> = {
      free: 0,
      personal_pro: 30,
      personal_advanced: 50,
      personal_flagship: 100,
      enterprise: 200,
      enterprise_pro: 400,
      enterprise_pro_max: 500,
    }
    return quotaMap[membershipTier] || 0
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title="pPQR管理"
        description="预备工艺评定记录 (Preliminary Procedure Qualification Record) 管理"
        icon={<ExperimentOutlined />}
      />

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总计"
              value={stats.total}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="草稿"
              value={stats.draft}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="试验中"
              value={stats.testing}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completed}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 配额提醒 */}
      {(() => {
        const tier = (user as any)?.member_tier || user?.membership_tier || 'free'
        return tier !== 'enterprise_pro_max' && (
          <Alert
            message={`pPQR配额使用情况: ${stats.total}/${getPPQRQuota(tier)}`}
            description={
              <Progress
                percent={(stats.total / getPPQRQuota(tier)) * 100}
                status={
                  (stats.total / getPPQRQuota(tier)) >= 0.8
                    ? 'exception'
                    : 'normal'
                }
              />
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )
      })()}

      {/* 主内容卡片 */}
      <Card className="list-page-card">
        <div className="doc-list-toolbar">
          <div className="toolbar-search">
            <Search
              placeholder="搜索pPQR编号或标题"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
            />
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="筛选状态"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={handleStatusFilter}
              value={statusFilter || undefined}
            >
              <Option value="draft">草稿</Option>
              <Option value="testing">试验中</Option>
              <Option value="completed">已完成</Option>
              <Option value="converted">已转换</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="试验结论"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={handleConclusionFilter}
              value={conclusionFilter || undefined}
            >
              <Option value="qualified">合格</Option>
              <Option value="unqualified">不合格</Option>
              <Option value="pending">待定</Option>
            </Select>
          </div>
          <div className="toolbar-actions">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="large"
              onClick={() => navigate('/ppqr/create')}
            >
              创建pPQR
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
          {ppqrData?.items && ppqrData.items.length > 0 ? (
            <>
              {ppqrData.items.map((record: PPQRSummary) => renderPPQRCard(record))}

              {/* 分页 */}
              <div style={{ marginTop: '24px', textAlign: 'center' }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`}
                  onChange={handlePageChange}
                  pageSizeOptions={['10', '20', '50', '100']}
                />
              </div>
            </>
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无pPQR记录"
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/ppqr/create')}>
                创建第一个pPQR
              </Button>
            </Empty>
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default PPQRList
