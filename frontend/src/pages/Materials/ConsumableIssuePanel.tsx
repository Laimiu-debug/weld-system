import React, { useEffect, useState } from 'react'
import { Alert, Button, Card, Space, Table, Tag, Typography, message } from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import consumablesService, {
  ConsumableIssueListItem,
  ConsumableUsageItem,
} from '@/services/consumables'
import apiService from '@/services/api'

const { Text } = Typography

const statusColor: Record<string, string> = {
  suggested: 'processing',
  approved: 'success',
  issued: 'blue',
  closed: 'default',
  superseded: 'warning',
}

const ConsumableIssuePanel: React.FC = () => {
  const [issueLists, setIssueLists] = useState<ConsumableIssueListItem[]>([])
  const [usageEvents, setUsageEvents] = useState<ConsumableUsageItem[]>([])
  const [loading, setLoading] = useState(false)

  const reload = async () => {
    setLoading(true)
    try {
      const [lists, usage] = await Promise.all([
        consumablesService.listIssueLists({ limit: 50 }),
        consumablesService.listUsage({ limit: 50 }),
      ])
      setIssueLists(lists.items)
      setUsageEvents(usage.items)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载定额领用数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload()
  }, [])

  const downloadExport = async (
    issueListId: string,
    exportType: 'weld-detail' | 'product-summary' | 'formal-issue-list',
    filename: string,
  ) => {
    try {
      const response = await apiService.get<Blob>(
        `/consumables/issue-lists/${issueListId}/export/${exportType}`,
        { responseType: 'blob' },
      )
      const blob = response.data
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } catch {
      message.error('导出失败')
    }
  }

  return (
    <div className="cc-issue">
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="生产定额闭环"
        description="正式领用清单由已批准的 P6 定额 run 生成。此处可查看领用清单、实际领退料记录，并导出 CSV。用量计算器里的「服务端 P6 复核」用于校验公式，不自动创建 quota run。"
      />
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void reload()}>
          刷新
        </Button>
      </Space>

      <Card title="领用清单" style={{ marginBottom: 16 }}>
        <Table
          size="small"
          rowKey="id"
          loading={loading}
          dataSource={issueLists}
          locale={{ emptyText: '暂无领用清单（需先有已批准的 quota run）' }}
          columns={[
            { title: '单据号', dataIndex: 'document_number', width: 160 },
            {
              title: '状态',
              dataIndex: 'status',
              render: (value: string) => <Tag color={statusColor[value] || 'default'}>{value}</Tag>,
            },
            { title: '版本', dataIndex: 'version_number', width: 70 },
            { title: '生成时间', dataIndex: 'generated_at', width: 180 },
            {
              title: '操作',
              render: (_, row) => (
                <Space>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() =>
                      void downloadExport(row.id, 'formal-issue-list', `${row.document_number}-领用.csv`)
                    }
                  >
                    导出
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Card title="实际领用 / 退料 / 消耗">
        <Table
          size="small"
          rowKey="id"
          loading={loading}
          dataSource={usageEvents}
          locale={{ emptyText: '暂无领用事件' }}
          columns={[
            { title: '类型', dataIndex: 'event_type', width: 90 },
            { title: '焊材', dataIndex: 'material_name', ellipsis: true },
            { title: '规格', dataIndex: 'specification', ellipsis: true },
            { title: '数量', dataIndex: 'quantity', render: (v, r) => `${v} ${r.unit}` },
            { title: '批次', dataIndex: 'batch_number', width: 120 },
            { title: '单据', dataIndex: 'document_number', width: 140 },
            { title: '时间', dataIndex: 'recorded_at', width: 180 },
          ]}
        />
        {usageEvents.length > 0 && (
          <Text type="secondary">共 {usageEvents.length} 条记录，数据来自焊材台账 P6 实际事件 API。</Text>
        )}
      </Card>
    </div>
  )
}

export default ConsumableIssuePanel
