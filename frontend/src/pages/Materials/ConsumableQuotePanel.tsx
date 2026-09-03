import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert, Button, Card, Col, Divider, Form, Input, InputNumber, Row, Space, Statistic, Table, Typography, message,
} from 'antd'
import { CloudSyncOutlined, FileExcelOutlined, SaveOutlined } from '@ant-design/icons'
import materialsService, { Material } from '@/services/materials'
import consumablesService, { mapServerSummary } from '@/services/consumables'
import { workspaceService } from '@/services/workspace'
import type { Joint } from './consumableCalc'
import { operationResult } from './consumableCalc'
import {
  CostParams, ProjectCostSummary, exportQuoteCsv,
  jointsToQuotePayload, loadCostParams, operationCostBreakdown, saveCostParams, summarizeProjectCosts,
} from './consumableCost'

const { Text, Title } = Typography

type Props = {
  joints: Joint[]
  projectLabel?: string
}

const ConsumableQuotePanel: React.FC<Props> = ({ joints, projectLabel }) => {
  const [cost, setCost] = useState<CostParams>(loadCostParams)
  const [customer, setCustomer] = useState('')
  const [serverSummary, setServerSummary] = useState<ProjectCostSummary | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [materials, setMaterials] = useState<Material[]>([])

  useEffect(() => {
    const ws = workspaceService.getCurrentWorkspaceFromStorage()
    if (!ws) return
    void materialsService.getMaterialsList({
      workspace_type: ws.type,
      company_id: ws.company_id,
      factory_id: ws.factory_id,
      limit: 200,
    }).then((res) => setMaterials(res.data.items))
  }, [])

  const localSummary = useMemo(() => summarizeProjectCosts(joints, cost), [joints, cost])
  const summary = serverSummary ?? localSummary

  const updateCost = (patch: Partial<CostParams>) => setCost(current => ({ ...current, ...patch }))

  const persistCost = () => {
    saveCostParams(cost)
    message.success('成本参数已保存')
  }

  const syncServer = async () => {
    setSyncing(true)
    try {
      const response = await consumablesService.quoteProject(
        jointsToQuotePayload(joints, cost, {
          projectName: projectLabel,
          customer: customer || undefined,
        }),
      )
      setServerSummary(mapServerSummary(response.summary))
      message.success('已用服务端 P6 引擎复核报价')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '服务端报价失败，已保留本地估算')
    } finally {
      setSyncing(false)
    }
  }

  const detailRows = joints.flatMap(joint =>
    joint.operations.map(operation => {
      const usage = operationResult(joint, operation)
      const costs = operationCostBreakdown(joint, operation, cost)
      return {
        key: `${joint.id}-${operation.id}`,
        weld: joint.name || '未命名',
        operation: operation.name,
        material: operation.material,
        length: joint.length,
        suggested: usage.suggested,
        materialCost: costs.materialCost,
        laborCost: costs.laborCost,
        equipmentCost: costs.equipmentCost,
        auxCost: costs.auxCost,
        subtotal: costs.subtotal,
      }
    }),
  )

  return (
    <div className="cc-quote">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="成本参数（weldmoney 口径）">
            <Form layout="vertical">
              <Row gutter={12}>
                <Col span={12}><Form.Item label="客户"><Input value={customer} onChange={e => setCustomer(e.target.value)} /></Form.Item></Col>
                <Col span={12}><Form.Item label="人工时薪 元/h"><InputNumber style={{ width: '100%' }} min={0} value={cost.laborRatePerHour} onChange={v => updateCost({ laborRatePerHour: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="管理费率"><InputNumber style={{ width: '100%' }} min={0} step={0.01} value={cost.overheadRate} onChange={v => updateCost({ overheadRate: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="气体单价 元/L"><InputNumber style={{ width: '100%' }} min={0} step={0.01} value={cost.gasPricePerL} onChange={v => updateCost({ gasPricePerL: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="焊机功率 kW"><InputNumber style={{ width: '100%' }} min={0} value={cost.machinePowerKw} onChange={v => updateCost({ machinePowerKw: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="电价 元/kWh"><InputNumber style={{ width: '100%' }} min={0} step={0.1} value={cost.electricityPrice} onChange={v => updateCost({ electricityPrice: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="日折旧 元"><InputNumber style={{ width: '100%' }} min={0} value={cost.dailyDepreciation} onChange={v => updateCost({ dailyDepreciation: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="日工时 h"><InputNumber style={{ width: '100%' }} min={0.1} value={cost.dailyWorkHours} onChange={v => updateCost({ dailyWorkHours: Number(v) || 8 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="利润率"><InputNumber style={{ width: '100%' }} min={0} step={0.01} value={cost.profitMargin} onChange={v => updateCost({ profitMargin: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="税率"><InputNumber style={{ width: '100%' }} min={0} step={0.01} value={cost.taxRate} onChange={v => updateCost({ taxRate: Number(v) || 0 })} /></Form.Item></Col>
                <Col span={12}><Form.Item label="焊剂单价 元/kg"><InputNumber style={{ width: '100%' }} min={0} step={0.1} value={cost.fluxUnitPrice} onChange={v => updateCost({ fluxUnitPrice: Number(v) || 0 })} /></Form.Item></Col>
              </Row>
              <Space wrap>
                <Button icon={<SaveOutlined />} onClick={persistCost}>保存参数</Button>
                <Button type="primary" icon={<CloudSyncOutlined />} loading={syncing} onClick={() => void syncServer()}>服务端 P6 复核</Button>
              </Space>
            </Form>
            {materials.length > 0 && (
              <>
                <Divider />
                <Text type="secondary">焊材台账 {materials.length} 条可对照单价（在工序里填 unitPrice 或选预设）</Text>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="项目报价汇总">
            {serverSummary && <Alert type="success" showIcon message="当前显示服务端 P6 复核结果" style={{ marginBottom: 12 }} />}
            <Row gutter={[12, 12]}>
              <Col span={8}><Statistic title="建议领用" value={summary.suggested} precision={2} suffix="kg" /></Col>
              <Col span={8}><Statistic title="熔敷金属" value={summary.deposit} precision={2} suffix="kg" /></Col>
              <Col span={8}><Statistic title="保护气体" value={summary.gasVolumeL} precision={0} suffix="L" /></Col>
              <Col span={6}><Statistic title="材料费" value={summary.materialCost} precision={0} prefix="¥" /></Col>
              <Col span={6}><Statistic title="人工费" value={summary.laborCost} precision={0} prefix="¥" /></Col>
              <Col span={6}><Statistic title="气体费" value={summary.auxCost} precision={0} prefix="¥" /></Col>
              <Col span={6}><Statistic title="设备/电费" value={summary.equipmentCost} precision={0} prefix="¥" /></Col>
            </Row>
            <Divider />
            <Space size="large" wrap>
              <Text>直接成本 <b>¥{summary.directCost.toFixed(0)}</b></Text>
              <Text>税前 <b>¥{summary.priceBeforeTax.toFixed(0)}</b></Text>
              <Title level={4} style={{ margin: 0, color: '#ea580c' }}>含税报价 ¥{summary.quotedPrice.toFixed(0)}</Title>
            </Space>
            <Divider />
            <Button icon={<FileExcelOutlined />} onClick={() => exportQuoteCsv(joints, cost, summary, projectLabel || '项目')}>
              导出报价 CSV
            </Button>
          </Card>
          <Card title="焊缝成本明细" style={{ marginTop: 16 }}>
            <Table
              size="small"
              pagination={false}
              scroll={{ x: 900 }}
              dataSource={detailRows}
              columns={[
                { title: '焊缝', dataIndex: 'weld', width: 120 },
                { title: '工序', dataIndex: 'operation', width: 100 },
                { title: '焊材', dataIndex: 'material', ellipsis: true },
                { title: '领用kg', dataIndex: 'suggested', render: v => Number(v).toFixed(3) },
                { title: '材料费', dataIndex: 'materialCost', render: v => `¥${Number(v).toFixed(0)}` },
                { title: '人工', dataIndex: 'laborCost', render: v => `¥${Number(v).toFixed(0)}` },
                { title: '设备', dataIndex: 'equipmentCost', render: v => `¥${Number(v).toFixed(0)}` },
                { title: '气体', dataIndex: 'auxCost', render: v => `¥${Number(v).toFixed(0)}` },
                { title: '小计', dataIndex: 'subtotal', render: v => `¥${Number(v).toFixed(0)}` },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default ConsumableQuotePanel
