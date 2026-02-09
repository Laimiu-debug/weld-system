/**
 * 焊材出入库记录组件
 */

import React, { useState, useEffect } from 'react'
import { Modal, Table, Tag, Select, message, Space } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Material, MaterialTransaction } from '../../services/materials'
import materialsService from '../../services/materials'
import { workspaceService } from '../../services/workspace'
import dayjs from 'dayjs'

interface TransactionHistoryProps {
  visible: boolean
  material: Material | null
  onCancel: () => void
}

const TransactionHistory: React.FC<TransactionHistoryProps> = ({
  visible,
  material,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false)
  const [transactions, setTransactions] = useState<MaterialTransaction[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [transactionType, setTransactionType] = useState<string | undefined>(undefined)

  useEffect(() => {
    if (visible && material) {
      fetchTransactions()
    }
  }, [visible, material, currentPage, pageSize, transactionType])

  const fetchTransactions = async () => {
    if (!material) return

    try {
      setLoading(true)

      // 获取当前工作区
      const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
      if (!currentWorkspace) {
        message.warning('请先选择工作区')
        setLoading(false)
        return
      }

      const workspaceType = currentWorkspace.type
      const companyId = currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined
      const factoryId = currentWorkspace.factory_id

      const response = await materialsService.getTransactionList({
        workspace_type: workspaceType,
        company_id: companyId,
        factory_id: factoryId,
        material_id: material.id,
        transaction_type: transactionType,
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      })

      if (response.success && response.data?.success) {
        const items = response.data.data?.items || []
        const totalCount = response.data.data?.total || 0
        setTransactions(items)
        setTotal(totalCount)
      } else {
        setTransactions([])
        setTotal(0)
      }
    } catch (error: any) {
      console.error('获取出入库记录失败:', error)
      message.error('获取出入库记录失败')
      setTransactions([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const getTransactionTypeTag = (type: string) => {
    const typeMap: Record<string, { text: string; color: string }> = {
      in: { text: '入库', color: 'green' },
      out: { text: '出库', color: 'red' },
      adjust: { text: '调整', color: 'orange' },
      return: { text: '退库', color: 'blue' },
      transfer: { text: '调拨', color: 'purple' },
      consume: { text: '消耗', color: 'volcano' },
    }
    const config = typeMap[type] || { text: type, color: 'default' }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns: ColumnsType<MaterialTransaction> = [
    {
      title: '交易单号',
      dataIndex: 'transaction_number',
      key: 'transaction_number',
      width: 180,
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 80,
      render: (type: string) => getTransactionTypeTag(type),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 120,
      render: (quantity: number, record: MaterialTransaction) => {
        const prefix = record.transaction_type === 'in' ? '+' : '-'
        const color = record.transaction_type === 'in' ? '#52c41a' : '#ff4d4f'
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {prefix}{quantity} {record.unit}
          </span>
        )
      },
    },
    {
      title: '库存变化',
      key: 'stock_change',
      width: 150,
      render: (_, record: MaterialTransaction) => (
        <span>
          {record.stock_before} → {record.stock_after} {record.unit}
        </span>
      ),
    },
    {
      title: '金额',
      key: 'amount',
      width: 100,
      render: (_, record: MaterialTransaction) => {
        if (record.total_price) {
          return `¥${record.total_price.toFixed(2)}`
        }
        return '-'
      },
    },
    {
      title: '来源/去向',
      key: 'source_destination',
      width: 150,
      render: (_, record: MaterialTransaction) => {
        if (record.transaction_type === 'in') {
          return record.source || '-'
        } else {
          return record.destination || '-'
        }
      },
    },
    {
      title: '批次号',
      dataIndex: 'batch_number',
      key: 'batch_number',
      width: 120,
      render: (text: string) => text || '-',
    },
    {
      title: '仓库位置',
      key: 'location',
      width: 150,
      render: (_, record: MaterialTransaction) => {
        const parts = []
        if (record.warehouse) parts.push(record.warehouse)
        if (record.storage_location) parts.push(record.storage_location)
        return parts.length > 0 ? parts.join(' / ') : '-'
      },
    },
    {
      title: '关联单据',
      key: 'reference',
      width: 150,
      render: (_, record: MaterialTransaction) => {
        if (record.reference_number) {
          return (
            <div>
              {record.reference_type && <div style={{ fontSize: 12, color: '#999' }}>{record.reference_type}</div>}
              <div>{record.reference_number}</div>
            </div>
          )
        }
        return '-'
      },
    },
    {
      title: '操作人',
      dataIndex: 'operator',
      key: 'operator',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '交易时间',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
  ]

  return (
    <Modal
      title={
        <Space>
          <span>出入库记录</span>
          {material && <span style={{ fontSize: 14, fontWeight: 'normal', color: '#666' }}>
            （{material.material_name} - {material.material_code}）
          </span>}
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={1400}
      footer={null}
      destroyOnClose
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>交易类型：</span>
          <Select
            style={{ width: 120 }}
            placeholder="全部"
            allowClear
            value={transactionType}
            onChange={(value) => {
              setTransactionType(value)
              setCurrentPage(1)
            }}
            options={[
              { label: '入库', value: 'in' },
              { label: '出库', value: 'out' },
              { label: '调整', value: 'adjust' },
              { label: '退库', value: 'return' },
              { label: '调拨', value: 'transfer' },
              { label: '消耗', value: 'consume' },
            ]}
          />
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={transactions}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1800 }}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, size) => {
            setCurrentPage(page)
            setPageSize(size)
          },
        }}
      />
    </Modal>
  )
}

export default TransactionHistory

