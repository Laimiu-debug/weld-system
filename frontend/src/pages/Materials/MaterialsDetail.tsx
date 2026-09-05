import React, { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Descriptions, Modal, Space, Spin, Tag, Typography, message } from 'antd'
import { ArrowLeftOutlined, EditOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import materialsService, { Material } from '@/services/materials'
import { workspaceService } from '@/services/workspace'
import { downloadCsv } from '@/utils/csv'
import StockInModal from './StockInModal'
import StockOutModal from './StockOutModal'
import TransactionHistory from './TransactionHistory'

const typeNames: Record<string, string> = { electrode: '焊条', wire: '焊丝', flux: '焊剂', gas: '保护气体' }

const MaterialsDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [workspace] = useState(() => workspaceService.getCurrentWorkspaceFromStorage())
  const [material, setMaterial] = useState<Material | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  const [action, setAction] = useState<'in' | 'out' | 'history' | null>(null)
  const refresh = useCallback(() => setRevision(value => value + 1), [])

  useEffect(() => {
    let active = true
    setMaterial(null)
    setError('')
    if (!workspace || !Number.isSafeInteger(Number(id)) || Number(id) <= 0) {
      setError('请确认焊材编号并选择工作区')
      setLoading(false)
      return
    }
    setLoading(true)
    materialsService.getMaterialById(Number(id), workspace.type,
      workspace.type === 'enterprise' ? workspace.company_id : undefined, workspace.factory_id)
      .then(response => {
        if (!response.success || !response.data?.id) throw new Error('未返回焊材资料')
        if (active) setMaterial(response.data)
      })
      .catch(() => { if (active) setError('无法加载焊材，记录可能已删除或您没有访问权限。请重试或返回列表。') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id, workspace, revision])

  const remove = () => {
    if (!material || !workspace) return
    Modal.confirm({
      title: `确认删除焊材“${material.material_name}”？`,
      content: '删除后该焊材将从在用列表中移除。',
      okText: '删除', cancelText: '取消', okButtonProps: { danger: true },
      onOk: async () => {
        try {
          const response = await materialsService.deleteMaterial(material.id, workspace.type,
            workspace.type === 'enterprise' ? workspace.company_id : undefined, workspace.factory_id)
          if (!response.success) throw new Error('删除失败')
          message.success('焊材已删除')
          navigate('/materials')
        } catch (error) {
          message.error('删除失败，请重试，焊材资料仍保留')
          throw error
        }
      },
    })
  }

  const exportInfo = () => {
    if (!material) return
    downloadCsv(`焊材-${material.id}`, ['编号', '名称', '类型', '规格', '制造商', '库存', '单位', '最低库存', '存储位置', '单价', '币种', '备注'], [[
      material.material_code, material.material_name, typeNames[material.material_type] || material.material_type,
      material.specification, material.manufacturer, material.current_stock, material.unit,
      material.min_stock_level, material.storage_location, material.unit_price, material.currency, material.notes,
    ]])
  }

  const onStockSuccess = () => { setAction(null); refresh() }
  const lowStock = material && material.min_stock_level != null && material.current_stock <= material.min_stock_level

  return <div className="page-container">
    <Space wrap style={{ marginBottom: 16 }}>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/materials')}>返回列表</Button>
      <Typography.Title level={2} style={{ margin: 0 }}>焊材详情</Typography.Title>
      <Button icon={<ReloadOutlined />} onClick={refresh} disabled={loading}>刷新</Button>
    </Space>
    {loading ? <Spin /> : error ? <Alert type="error" showIcon message={error} action={<Button onClick={refresh}>重试</Button>} /> : material && <>
      {(lowStock || material.current_stock === 0) && <Alert type="warning" showIcon message={material.current_stock === 0 ? '当前库存为零，请及时补充' : '库存已达到最低库存水平，请及时补充'} style={{ marginBottom: 16 }} />}
      <Card title={material.material_name} extra={<Tag>{typeNames[material.material_type] || material.material_type}</Tag>}>
        <Descriptions bordered column={{ xs: 1, sm: 2 }} items={[
          { key: 'code', label: '焊材编号', children: material.material_code },
          { key: 'spec', label: '规格', children: material.specification || '—' },
          { key: 'maker', label: '制造商', children: material.manufacturer || '—' },
          { key: 'supplier', label: '供应商', children: material.supplier || '—' },
          { key: 'stock', label: '当前库存', children: `${material.current_stock} ${material.unit}` },
          { key: 'min', label: '最低库存', children: material.min_stock_level == null ? '未设置' : `${material.min_stock_level} ${material.unit}` },
          { key: 'location', label: '存储位置', children: material.storage_location || '—' },
          { key: 'batch', label: '批次号', children: material.batch_number || '—' },
          { key: 'price', label: '单价', children: material.unit_price == null ? '未设置' : `${material.unit_price} ${material.currency || 'CNY'} / ${material.unit}` },
          { key: 'value', label: '库存估值', children: material.unit_price == null ? '未设置单价' : `${(material.current_stock * material.unit_price).toFixed(2)} ${material.currency || 'CNY'}` },
          { key: 'notes', label: '备注', children: material.notes || '—', span: 2 },
        ]} />
        <Space wrap style={{ marginTop: 20 }}>
          <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/materials/${material.id}/edit`)}>编辑焊材</Button>
          <Button onClick={() => setAction('in')}>入库</Button>
          <Button onClick={() => setAction('out')} disabled={material.current_stock <= 0}>出库</Button>
          <Button onClick={() => setAction('history')}>库存流水</Button>
          <Button icon={<DownloadOutlined />} onClick={exportInfo}>导出信息</Button>
          <Button danger onClick={remove}>删除焊材</Button>
        </Space>
      </Card>
      <StockInModal visible={action === 'in'} material={material} onCancel={() => setAction(null)} onSuccess={onStockSuccess} />
      <StockOutModal visible={action === 'out'} material={material} onCancel={() => setAction(null)} onSuccess={onStockSuccess} />
      <TransactionHistory key={`${material.id}-${action === 'history'}`} visible={action === 'history'} material={material} onCancel={() => setAction(null)} />
    </>}
  </div>
}

export default MaterialsDetail
