import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert, Button, Card, Col, Divider, Form, Input, InputNumber, List, Modal, Row,
  Segmented, Select, Space, Statistic, Tabs, Tag, Typography, message,
} from 'antd'
import {
  CalculatorOutlined, DeleteOutlined, FileExcelOutlined, FilePdfOutlined,
  PlusOutlined, SaveOutlined,
} from '@ant-design/icons'
import { DataRow, engineeringService } from '@/services/engineering'
import {
  Joint, LengthDraft, Operation, OperationRole,
  calcWeldLength, createJoint, createOperation, defaultParamsForGroove, geometry, grooveOptions,
  isBackGougeGroove, isTubePlateGroove, materialPresets, methodPresets, normalizeGroove, num,
  operationResult, sumResults, thicknessLabel,
} from './consumableCalc'
import ConsumableQuotePanel from './ConsumableQuotePanel'
import ConsumableIssuePanel from './ConsumableIssuePanel'
import './consumableCalculator.css'

const { Title, Text } = Typography

const GroovePreview: React.FC<{ value: Joint }> = ({ value }) => {
  const area = geometry(value).total
  const label = grooveOptions.find(item => item.value === value.groove)?.label
  const isFillet = value.groove === 'FILLET' || value.groove === 'LAP'
  const isTubePlate = isTubePlateGroove(value.groove)
  const isBackGouge = isBackGougeGroove(value.groove)
  return (
    <div className="cc-preview" role="img" aria-label={`${label}截面预览`}>
      <div className="cc-preview__title">{label}　A = {area.toFixed(1)} mm²</div>
      <svg viewBox="0 0 480 230" aria-hidden="true">
        {isFillet ? (
          <>
            <rect x="70" y="145" width="340" height="55" fill="#8a9097" stroke="#4b5563" />
            <rect x="210" y="30" width="55" height="145" fill="#8a9097" stroke="#4b5563" />
            <path d="M210 145 L145 145 L210 82 Z" fill="#e3a11a" stroke="#9a6700" strokeWidth="3" />
          </>
        ) : isTubePlate ? (
          <>
            <rect x="40" y="150" width="400" height="45" fill="#8a9097" stroke="#4b5563" strokeWidth="2" />
            <rect x="200" y="35" width="80" height="120" fill="#8a9097" stroke="#4b5563" strokeWidth="2" />
            <path
              d={
                value.groove === 'TP_X'
                  ? 'M208 40 L272 40 L240 95 L260 150 H220 L240 95 Z'
                  : 'M208 40 L272 40 L240 150 H220 Z'
              }
              fill="#e3a11a"
              stroke="#9a6700"
              strokeWidth="3"
            />
            {value.groove === 'TP_V' && value.legSize > 0 && (
              <path d="M200 150 L170 150 L200 120 Z" fill="#fbbf24" stroke="#9a6700" strokeWidth="2" />
            )}
            <text x="248" y="28" fill="#475569" fontSize="14" textAnchor="middle">
              Φ{value.tubeDiameter || 219}
            </text>
          </>
        ) : (
          <>
            <path d="M45 70 H205 L240 145 L275 70 H435 V190 H275 L240 145 L205 190 H45 Z" fill="#8a9097" stroke="#4b5563" strokeWidth="3" />
            <path
              d={
                value.groove === 'I'
                  ? 'M226 65 H254 V194 H226 Z'
                  : 'M196 65 H284 L240 145 L265 194 H215 L240 145 Z'
              }
              fill="#e3a11a"
              stroke="#9a6700"
              strokeWidth="3"
            />
            {value.groove !== 'I' && (
              <path d="M196 65 Q240 35 284 65" fill="#e3a11a" stroke="#9a6700" strokeWidth="3" />
            )}
            {isBackGouge && value.backGougeDepth > 0 && (
              <path d="M218 194 L262 194 L240 168 Z" fill="#fb923c" stroke="#c2410c" strokeWidth="2" />
            )}
          </>
        )}
        {!isFillet && (
          <>
            <line x1="370" y1="70" x2="370" y2="190" stroke="#1677ff" strokeWidth="2" />
            <text x="378" y="136" fill="#1677ff" fontSize="18">
              t={value.thickness}
            </text>
          </>
        )}
      </svg>
    </div>
  )
}

const ConsumableUsagePage: React.FC = () => {
  const [projects, setProjects] = useState<DataRow[]>([])
  const [products, setProducts] = useState<DataRow[]>([])
  const [revisions, setRevisions] = useState<DataRow[]>([])
  const [projectId, setProjectId] = useState<string>()
  const [productId, setProductId] = useState<string>()
  const [revisionId, setRevisionId] = useState<string>()
  const [joints, setJoints] = useState<Joint[]>([createJoint()])
  const [selectedId, setSelectedId] = useState('')
  const [selectedOpId, setSelectedOpId] = useState('')
  const [lengthOpen, setLengthOpen] = useState(false)
  const [grooveOpen, setGrooveOpen] = useState(false)
  const [calculated, setCalculated] = useState(false)
  const [lengthDraft, setLengthDraft] = useState<LengthDraft>({
    mode: 'circumference',
    diameter: 219,
    wallThickness: 8,
    diameterBasis: 'od',
    angle: 360,
    count: 1,
    straight: 1000,
  })

  useEffect(() => { void engineeringService.projects().then(setProjects) }, [])
  useEffect(() => {
    setProductId(undefined)
    setRevisionId(undefined)
    setProducts([])
    setRevisions([])
    if (projectId) void engineeringService.products(projectId).then(setProducts)
  }, [projectId])
  useEffect(() => {
    setRevisionId(undefined)
    setRevisions([])
    if (productId) void engineeringService.revisions(productId).then(setRevisions)
  }, [productId])
  useEffect(() => {
    if (!selectedId && joints[0]) setSelectedId(joints[0].id)
  }, [joints, selectedId])

  const selected = joints.find(item => item.id === selectedId) || joints[0]
  const selectedOp =
    selected?.operations.find(item => item.id === selectedOpId) || selected?.operations[0]

  useEffect(() => {
    if (
      selected?.operations[0] &&
      !selected.operations.some(item => item.id === selectedOpId)
    ) {
      setSelectedOpId(selected.operations[0].id)
    }
  }, [selected, selectedOpId])

  const storageKey = `consumable-calculator-v3:${projectId || 'unassigned'}`
  useEffect(() => {
    if (!projectId) return
    const raw = localStorage.getItem(storageKey)
    if (!raw) return
    try {
      const saved = JSON.parse(raw) as Joint[]
      // 兼容旧草稿：补齐新增字段
      const migrated = saved.map(item =>
        createJoint({
          ...item,
          tubeDiameter: item.tubeDiameter ?? 219,
          gougeOpeningWidth: item.gougeOpeningWidth ?? 0,
          operations: (item.operations || []).map(op =>
            createOperation(op.role, {
              ...op,
              stubLoss: op.stubLoss ?? 0,
              spatterLoss: op.spatterLoss ?? 0.03,
              fluxLoss: op.fluxLoss ?? 0,
              enterpriseFactor: op.enterpriseFactor ?? 1,
              packageSizeKg: op.packageSizeKg ?? null,
              depositionRateKgH: op.depositionRateKgH ?? 2,
              arcTimeRatio: op.arcTimeRatio ?? 0.4,
              gasFlowLMin: op.gasFlowLMin ?? null,
            }),
          ),
        }),
      )
      setJoints(migrated)
      setSelectedId(migrated[0]?.id || '')
      message.info('已恢复该项目的焊材计算草稿')
    } catch {
      /* ignore invalid local draft */
    }
  }, [projectId, storageKey])

  const updateJoint = (values: Partial<Joint>) => {
    setJoints(current =>
      current.map(item => (item.id === selected.id ? { ...item, ...values } : item)),
    )
    setCalculated(false)
  }

  const changeGroove = (groove: Joint['groove']) => {
    const defaults = defaultParamsForGroove(groove)
    const nextOps = defaults.operations ?? selected.operations
    updateJoint({
      ...defaults,
      groove,
      name: selected.name,
      length: selected.length,
      operations: nextOps,
    })
    if (isTubePlateGroove(groove)) {
      setLengthDraft(current => ({
        ...current,
        mode: 'circumference',
        diameter: defaults.tubeDiameter ?? selected.tubeDiameter ?? 219,
        angle: 360,
      }))
    }
  }

  const updateOperation = (values: Partial<Operation>) => {
    if (!selectedOp) return
    updateJoint({
      operations: selected.operations.map(item =>
        item.id === selectedOp.id ? { ...item, ...values } : item,
      ),
    })
  }

  const applyMaterialPreset = (label: string) => {
    const preset = materialPresets.find(item => item.label === label)
    if (!preset) return
    updateOperation({
      material: preset.material,
      density: preset.density,
      efficiency: preset.efficiency,
      unitPrice: preset.unitPrice,
      depositionRateKgH: preset.depositionRateKgH,
      stubLoss: preset.stubLoss,
      spatterLoss: preset.spatterLoss,
    })
  }

  const applyMethodPreset = (label: string) => {
    const preset = methodPresets.find(item => item.label === label)
    if (!preset) return
    updateOperation({
      method: preset.method,
      fluxRatio: preset.fluxRatio,
      gasFlowLMin: preset.gasFlowLMin,
      arcTimeRatio: preset.arcTimeRatio,
      fluxLoss: preset.fluxRatio > 0 ? 0.05 : 0,
    })
  }

  const importRevision = async () => {
    if (!revisionId) return
    const detail = await engineeringService.detail(revisionId)
    const parts = new Map(detail.parts.map(item => [item.id, item]))
    const imported = detail.weld_joints.map((item, index) => {
      const a = parts.get(item.part_a_id)
      const b = parts.get(item.part_b_id)
      const req = detail.requirements.find(value => value.weld_joint_id === item.id)
      return createJoint({
        id: item.id,
        name: item.weld_number || `焊缝 ${index + 1}`,
        length: num(item.length_mm),
        groove: normalizeGroove(item.groove_type || item.joint_type),
        thickness: Math.max(num(a?.thickness_mm), num(b?.thickness_mm), 12),
        angle: num(item.groove_angle, 60),
        gap: num(item.root_gap, 2),
        rootFace: num(item.root_face, 2),
        legSize: num(item.weld_size, 8),
        operations: [
          createOperation('face', {
            material:
              req?.filler_material_spec ||
              req?.filler_material_classification ||
              'ER50-6 焊丝 Φ1.2',
          }),
        ],
      })
    })
    if (!imported.length) {
      return message.warning('该图纸版本没有焊缝，请先完成图纸识别或人工新增焊缝')
    }
    setJoints(imported)
    setSelectedId(imported[0].id)
    message.success(`已导入 ${imported.length} 条焊缝`)
  }

  const allResults = useMemo(
    () =>
      joints.flatMap(item =>
        item.operations.map(operation => ({
          joint: item,
          operation,
          ...operationResult(item, operation),
        })),
      ),
    [joints],
  )
  const totals = useMemo(() => sumResults(allResults), [allResults])
  const currentResults = selected
    ? selected.operations.map(operation => ({
        operation,
        ...operationResult(selected, operation),
      }))
    : []
  const currentTotals = sumResults(currentResults)

  const addOperation = (role: OperationRole) =>
    updateJoint({ operations: [...selected.operations, createOperation(role)] })

  const save = () => {
    if (!projectId) return message.warning('请先选择项目')
    localStorage.setItem(storageKey, JSON.stringify(joints))
    message.success('项目焊材计算草稿已保存')
  }

  const exportCsv = () => {
    const lines = [
      [
        '焊缝', '工序', '方法', '焊材', '截面积mm²', '长度mm',
        '熔敷kg', '理论消耗kg', '工艺消耗kg', '建议领用kg', '焊剂kg', '气体L', '材料费',
      ],
      ...allResults.map(item => [
        item.joint.name,
        item.operation.name,
        item.operation.method,
        item.operation.material,
        item.area.toFixed(2),
        item.joint.length.toFixed(1),
        item.deposit.toFixed(3),
        item.primary.toFixed(3),
        item.process.toFixed(3),
        item.suggested.toFixed(3),
        item.enterpriseFlux.toFixed(3),
        (item.gasVolumeL ?? 0).toFixed(1),
        item.cost.toFixed(2),
      ]),
    ]
    const blob = new Blob([`\uFEFF${lines.map(line => line.join(',')).join('\n')}`], {
      type: 'text/csv;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '项目焊材用量.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!selected) return null

  const areas = geometry(selected)
  const lengthValue = calcWeldLength(lengthDraft)
  const selectedOpResult = selectedOp ? operationResult(selected, selectedOp) : null
  const projectLabel = projects.find(item => item.id === projectId)?.name

  const calcTab = (
    <>
      <Card className="cc-toolbar">
        <div className="cc-toolbar__inner">
          <Space wrap>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="当前项目"
              style={{ width: 220 }}
              value={projectId}
              options={projects.map(item => ({
                value: item.id,
                label: `${item.code} · ${item.name}`,
              }))}
              onChange={setProjectId}
            />
            <Select
              placeholder="产品"
              disabled={!projectId}
              style={{ width: 200 }}
              value={productId}
              options={products.map(item => ({ value: item.id, label: item.name }))}
              onChange={setProductId}
            />
            <Select
              placeholder="图纸版本"
              disabled={!productId}
              style={{ width: 220 }}
              value={revisionId}
              options={revisions.map(item => ({
                value: item.id,
                label: `版本 ${item.revision_number} · ${item.drawing_filename}`,
              }))}
              onChange={setRevisionId}
            />
            <Button disabled={!revisionId} onClick={() => void importRevision()}>
              导入图纸焊缝
            </Button>
          </Space>
          <Space>
            <Button type="primary" className="cc-save" icon={<SaveOutlined />} onClick={save}>
              保存项目
            </Button>
            <Button icon={<FileExcelOutlined />} onClick={exportCsv}>
              导出 Excel
            </Button>
            <Button icon={<FilePdfOutlined />} onClick={() => window.print()}>
              导出 PDF
            </Button>
          </Space>
        </div>
      </Card>

      <div className="cc-workbench">
        <Card className="cc-joints" title="焊缝列表">
          <Button
            type="primary"
            block
            icon={<PlusOutlined />}
            onClick={() => {
              const value = createJoint({ name: `焊缝 ${joints.length + 1}` })
              setJoints(current => [...current, value])
              setSelectedId(value.id)
            }}
          >
            添加为新焊缝
          </Button>
          <List
            dataSource={joints}
            locale={{ emptyText: '暂无焊缝' }}
            renderItem={item => (
              <List.Item
                className={item.id === selected.id ? 'cc-joint cc-joint--active' : 'cc-joint'}
                onClick={() => setSelectedId(item.id)}
                actions={[
                  <Button
                    key="delete"
                    danger
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={event => {
                      event.stopPropagation()
                      setJoints(current => current.filter(value => value.id !== item.id))
                      setSelectedId('')
                    }}
                  />,
                ]}
              >
                <List.Item.Meta
                  title={item.name || '未命名焊缝'}
                  description={`${grooveOptions.find(value => value.value === item.groove)?.label} · ${item.length.toFixed(1)} mm`}
                />
              </List.Item>
            )}
          />
        </Card>

        <main className="cc-editor">
          <Card title={<span><b>①</b> 焊口</span>}>
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={15}>
                  <Form.Item label="焊缝名称">
                    <Input
                      value={selected.name}
                      placeholder="如：筒体纵缝 A-1"
                      onChange={event => updateJoint({ name: event.target.value })}
                    />
                  </Form.Item>
                </Col>
                <Col span={9}>
                  <Form.Item label="焊缝长度">
                    <Space.Compact block>
                      <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        precision={1}
                        value={selected.length}
                        addonAfter="mm"
                        onChange={value => updateJoint({ length: num(value) })}
                      />
                      <Button onClick={() => setLengthOpen(true)}>计算长度</Button>
                    </Space.Compact>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>

          <Card
            title={
              <span>
                <b>②</b> 坡口几何 <Text type="secondary">（系统计算截面积）</Text>
              </span>
            }
          >
            <Row gutter={[16, 12]} align="middle">
              <Col xs={24} md={10}>
                <Text type="secondary">坡口形式</Text>
                <Select
                  style={{ width: '100%', marginTop: 6 }}
                  value={selected.groove}
                  options={grooveOptions}
                  onChange={value => changeGroove(value)}
                />
              </Col>
              <Col xs={24} md={7}>
                <Text type="secondary">{thicknessLabel(selected.groove)}</Text>
                <InputNumber
                  style={{ width: '100%', marginTop: 6 }}
                  min={0.1}
                  value={selected.thickness}
                  addonAfter="mm"
                  onChange={value => updateJoint({ thickness: num(value) })}
                />
              </Col>
              {isTubePlateGroove(selected.groove) && (
                <Col xs={24} md={7}>
                  <Text type="secondary">接管外径 Φ</Text>
                  <InputNumber
                    style={{ width: '100%', marginTop: 6 }}
                    min={1}
                    value={selected.tubeDiameter}
                    addonAfter="mm"
                    onChange={value => updateJoint({ tubeDiameter: num(value, 219) })}
                  />
                </Col>
              )}
              <Col xs={24} md={7}>
                <Button
                  block
                  onClick={() => {
                    if (isTubePlateGroove(selected.groove)) {
                      setLengthDraft(current => ({
                        ...current,
                        mode: 'circumference',
                        diameter: selected.tubeDiameter,
                        angle: 360,
                      }))
                    }
                    setGrooveOpen(true)
                  }}
                >
                  精确计算
                </Button>
              </Col>
              {isBackGougeGroove(selected.groove) && (
                <Col span={24}>
                  <Alert
                    type="info"
                    showIcon
                    message="背面开清根：正面填缝后从背面清根，再执行「清根填充」工序。请分别设置正面/清根面积并添加对应工序。"
                  />
                </Col>
              )}
              {isTubePlateGroove(selected.groove) && (
                <Col span={24}>
                  <Alert
                    type="info"
                    showIcon
                    message={`管板环缝长度 ≈ π×Φ${selected.tubeDiameter} = ${(Math.PI * selected.tubeDiameter).toFixed(1)} mm（整圈）`}
                  />
                </Col>
              )}
              <Col span={24}>
                <Space size="large" wrap>
                  <span>
                    正面面积 <b>{areas.face.toFixed(2)} mm²</b>
                  </span>
                  <span>
                    清根面积 <b>{areas.gouge.toFixed(2)} mm²</b>
                  </span>
                  <span>
                    合计面积 <b className="cc-accent">{areas.total.toFixed(2)} mm²</b>
                  </span>
                </Space>
              </Col>
              {areas.warnings.length > 0 && (
                <Col span={24}>
                  <Alert
                    type="warning"
                    showIcon
                    message={areas.warnings.join('；')}
                  />
                </Col>
              )}
            </Row>
          </Card>

          <Card
            title={
              <span>
                <b>③</b> 焊接工序 <Text type="secondary">（方法与焊材）</Text>
              </span>
            }
          >
            <div className="cc-op-actions">
              <Button onClick={() => addOperation('face')}>＋ 正面填充</Button>
              <Button onClick={() => addOperation('gouge')}>＋ 清根填充</Button>
              <Button onClick={() => addOperation('tack')}>＋ 固定焊</Button>
              <Button onClick={() => addOperation('custom')}>＋ 自定义</Button>
            </div>
            <div className="cc-op-layout">
              <List
                className="cc-op-list"
                dataSource={selected.operations}
                renderItem={item => (
                  <List.Item
                    className={item.id === selectedOp?.id ? 'cc-op cc-op--active' : 'cc-op'}
                    onClick={() => setSelectedOpId(item.id)}
                  >
                    {item.name}
                    <Text type="secondary">
                      {operationResult(selected, item).area.toFixed(1)}mm² ×{' '}
                      {selected.length.toFixed(0)}mm
                    </Text>
                  </List.Item>
                )}
              />
              {selectedOp && (
                <Form layout="vertical" className="cc-op-form">
                  <Row gutter={12}>
                    <Col span={12}>
                      <Form.Item label="工序">
                        <Input
                          value={selectedOp.name}
                          onChange={event => updateOperation({ name: event.target.value })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="焊接方法预设">
                        <Select
                          allowClear
                          placeholder="选择后自动填方法参数"
                          options={methodPresets.map(item => ({
                            value: item.label,
                            label: item.label,
                          }))}
                          onChange={value => value && applyMethodPreset(value)}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="焊接方法">
                        <Input
                          value={selectedOp.method}
                          onChange={event => updateOperation({ method: event.target.value })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="焊材预设">
                        <Select
                          allowClear
                          showSearch
                          optionFilterProp="label"
                          placeholder="选择后自动填密度/效率"
                          options={materialPresets.map(item => ({
                            value: item.label,
                            label: item.label,
                          }))}
                          onChange={value => value && applyMaterialPreset(value)}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="焊材">
                        <Input
                          value={selectedOp.material}
                          onChange={event => updateOperation({ material: event.target.value })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item label="密度 g/cm³">
                        <InputNumber
                          min={0.01}
                          value={selectedOp.density}
                          onChange={value => updateOperation({ density: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item label="熔敷效率 η">
                        <InputNumber
                          min={0.01}
                          max={1}
                          step={0.01}
                          value={selectedOp.efficiency}
                          onChange={value => updateOperation({ efficiency: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="单价 元/kg">
                        <InputNumber
                          min={0}
                          value={selectedOp.unitPrice}
                          onChange={value => updateOperation({ unitPrice: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="焊剂/焊丝比">
                        <InputNumber
                          min={0}
                          step={0.1}
                          value={selectedOp.fluxRatio}
                          onChange={value => updateOperation({ fluxRatio: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="自定义截面积">
                        <InputNumber
                          disabled={!['tack', 'custom'].includes(selectedOp.role)}
                          min={0}
                          value={selectedOp.customArea}
                          addonAfter="mm²"
                          onChange={value => updateOperation({ customArea: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="焊条头损耗">
                        <InputNumber
                          min={0}
                          max={0.99}
                          step={0.01}
                          value={selectedOp.stubLoss}
                          onChange={value => updateOperation({ stubLoss: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="飞溅损耗">
                        <InputNumber
                          min={0}
                          max={0.99}
                          step={0.01}
                          value={selectedOp.spatterLoss}
                          onChange={value => updateOperation({ spatterLoss: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="焊剂损耗">
                        <InputNumber
                          min={0}
                          max={0.99}
                          step={0.01}
                          value={selectedOp.fluxLoss}
                          onChange={value => updateOperation({ fluxLoss: num(value) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="企业修正系数">
                        <InputNumber
                          min={0.01}
                          step={0.01}
                          value={selectedOp.enterpriseFactor}
                          onChange={value => updateOperation({ enterpriseFactor: num(value, 1) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="包装规格 kg">
                        <InputNumber
                          min={0}
                          placeholder="空=不取整"
                          value={selectedOp.packageSizeKg ?? undefined}
                          onChange={value =>
                            updateOperation({
                              packageSizeKg: value == null || value <= 0 ? null : num(value),
                            })
                          }
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="熔敷速度 kg/h">
                        <InputNumber
                          min={0}
                          step={0.1}
                          value={selectedOp.depositionRateKgH ?? undefined}
                          onChange={value =>
                            updateOperation({
                              depositionRateKgH: value == null || value <= 0 ? null : num(value),
                            })
                          }
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="燃弧系数">
                        <InputNumber
                          min={0.01}
                          max={1}
                          step={0.05}
                          value={selectedOp.arcTimeRatio}
                          onChange={value => updateOperation({ arcTimeRatio: num(value, 0.4) })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="气体流量 L/min">
                        <InputNumber
                          min={0}
                          value={selectedOp.gasFlowLMin ?? undefined}
                          onChange={value =>
                            updateOperation({
                              gasFlowLMin: value == null || value <= 0 ? null : num(value),
                            })
                          }
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 12 }}
                    message="焊道数不参与用量计算：截面积已代表完整熔敷量（与 weldmoney / P6 一致）。"
                  />
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    disabled={selected.operations.length <= 1}
                    onClick={() =>
                      updateJoint({
                        operations: selected.operations.filter(
                          item => item.id !== selectedOp.id,
                        ),
                      })
                    }
                  >
                    删除工序
                  </Button>
                </Form>
              )}
            </div>
          </Card>
        </main>

        <aside className="cc-side">
          <Card title="截面预览">
            <GroovePreview value={selected} />
          </Card>
          <Card title="试算结果">
            <Button
              type="primary"
              block
              size="large"
              icon={<CalculatorOutlined />}
              onClick={() => {
                setCalculated(true)
                message.success('当前焊缝计算完成')
              }}
            >
              计算当前焊缝
            </Button>
            <Tag color={calculated ? 'success' : 'processing'} className="cc-status">
              状态：{calculated ? '已计算' : '参数编辑中'}
            </Tag>
            <Divider />
            <Statistic title="熔敷金属" value={currentTotals.deposit} precision={3} suffix="kg" />
            <Statistic title="理论消耗（÷η）" value={currentTotals.primary} precision={3} suffix="kg" />
            <Statistic title="工艺消耗（+损耗）" value={currentTotals.process} precision={3} suffix="kg" />
            <Statistic
              title="建议领用"
              value={currentTotals.suggested}
              precision={3}
              suffix="kg"
              valueStyle={{ color: '#ea580c' }}
            />
            <Statistic title="消耗焊剂" value={currentTotals.enterpriseFlux} precision={3} suffix="kg" />
            {currentTotals.gasVolumeL > 0 && (
              <Statistic title="保护气体" value={currentTotals.gasVolumeL} precision={1} suffix="L" />
            )}
            <Statistic title="材料费" value={currentTotals.cost} precision={2} prefix="¥" />
            {selectedOpResult && (
              <>
                <Divider />
                <Text type="secondary" className="cc-formula">
                  当前工序：{selectedOpResult.area.toFixed(1)} mm² × {selected.length.toFixed(0)} mm ×{' '}
                  {selectedOp?.density} / 1e6 = {selectedOpResult.deposit.toFixed(3)} kg 熔敷
                  {selectedOpResult.arcTimeH != null &&
                    ` · 电弧 ${selectedOpResult.arcTimeH.toFixed(2)} h`}
                </Text>
              </>
            )}
            <Divider />
            <Text strong>项目建议领用合计：{totals.suggested.toFixed(3)} kg</Text>
          </Card>
      </aside>
    </div>
    </>
  )

  return (
    <div className="cc-page">
      <div className="cc-heading">
        <div>
          <Title level={2}>焊材用量计算器</Title>
          <Text type="secondary">
            用量计算 + weldmoney 成本报价 + P6 定额领用（双路径）
          </Text>
        </div>
      </div>

      <Tabs
        defaultActiveKey="calc"
        items={[
          { key: 'calc', label: '用量计算', children: calcTab },
          {
            key: 'quote',
            label: '成本报价',
            children: <ConsumableQuotePanel joints={joints} projectLabel={projectLabel} />,
          },
          {
            key: 'issue',
            label: '定额领用',
            children: <ConsumableIssuePanel />,
          },
        ]}
      />

      <Modal
        title="焊缝长度计算器"
        open={lengthOpen}
        onCancel={() => setLengthOpen(false)}
        onOk={() => {
          updateJoint({ length: lengthValue })
          setLengthOpen(false)
        }}
        okText="应用长度"
      >
        <Form layout="vertical">
          <Form.Item label="类型">
            <Segmented
              block
              value={lengthDraft.mode}
              options={[
                { value: 'circumference', label: '环缝' },
                { value: 'straight', label: '直缝' },
              ]}
              onChange={value =>
                setLengthDraft(current => ({
                  ...current,
                  mode: value as LengthDraft['mode'],
                }))
              }
            />
          </Form.Item>
          {lengthDraft.mode === 'circumference' ? (
            <>
              <Form.Item label="外径 D">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={lengthDraft.diameter}
                  addonAfter="mm"
                  onChange={value =>
                    setLengthDraft(current => ({ ...current, diameter: num(value) }))
                  }
                />
              </Form.Item>
              <Form.Item label="壁厚">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={lengthDraft.wallThickness}
                  addonAfter="mm"
                  onChange={value =>
                    setLengthDraft(current => ({ ...current, wallThickness: num(value) }))
                  }
                />
              </Form.Item>
              <Form.Item label="计算直径基准">
                <Segmented
                  block
                  value={lengthDraft.diameterBasis}
                  options={[
                    { value: 'od', label: '外径' },
                    { value: 'mean', label: '中径' },
                    { value: 'id', label: '内径' },
                  ]}
                  onChange={value =>
                    setLengthDraft(current => ({
                      ...current,
                      diameterBasis: value as LengthDraft['diameterBasis'],
                    }))
                  }
                />
              </Form.Item>
              <Form.Item label="单道包角">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={360}
                  value={lengthDraft.angle}
                  addonAfter="°"
                  onChange={value =>
                    setLengthDraft(current => ({ ...current, angle: num(value) }))
                  }
                />
              </Form.Item>
            </>
          ) : (
            <Form.Item label="单条长度">
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                value={lengthDraft.straight}
                addonAfter="mm"
                onChange={value =>
                  setLengthDraft(current => ({ ...current, straight: num(value) }))
                }
              />
            </Form.Item>
          )}
          <Form.Item label="条数">
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              precision={0}
              value={lengthDraft.count}
              onChange={value =>
                setLengthDraft(current => ({ ...current, count: num(value, 1) }))
              }
            />
          </Form.Item>
          <Alert type="info" showIcon message={`焊缝总长度 = ${lengthValue.toFixed(1)} mm`} />
        </Form>
      </Modal>

      <Modal
        title="坡口截面积计算器"
        width="min(1180px, 96vw)"
        open={grooveOpen}
        onCancel={() => setGrooveOpen(false)}
        onOk={() => setGrooveOpen(false)}
        okText="应用参数"
      >
        <div className="cc-groove-modal">
          <Form layout="vertical">
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item label="坡口形式">
                  <Select
                    value={selected.groove}
                    options={grooveOptions}
                    onChange={value => changeGroove(value)}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label={`${thicknessLabel(selected.groove)} (mm)`}>
                  <InputNumber
                    value={selected.thickness}
                    onChange={value => updateJoint({ thickness: num(value) })}
                  />
                </Form.Item>
              </Col>
              {(
                [
                  ['坡口夹角 α', 'angle'],
                  ['间隙 b', 'gap'],
                  ['钝边 p', 'rootFace'],
                  ['余高 c', 'reinforcement'],
                  ['清根深度', 'backGougeDepth'],
                  ['清根开口宽（0=参考）', 'gougeOpeningWidth'],
                  ['焊缝展宽（单侧）', 'faceExtra'],
                  ['半径 R', 'radius'],
                  ...(selected.groove === 'TP_V' ? [['管板角焊焊脚 K', 'legSize'] as const] : []),
                  ...(selected.groove === 'TP_X' || selected.groove === 'X'
                    ? [['上坡口高度', 'upperHeight'] as const]
                    : []),
                  ['填充系数', 'fillFactor'],
                  ...(isTubePlateGroove(selected.groove)
                    ? [['接管外径 Φ', 'tubeDiameter'] as const]
                    : []),
                ] as const
              ).map(([label, key]) => (
                <Col span={12} key={key}>
                  <Form.Item label={label}>
                    <InputNumber
                      value={selected[key] as number}
                      step={key === 'fillFactor' ? 0.01 : 0.1}
                      onChange={value => updateJoint({ [key]: num(value) })}
                    />
                  </Form.Item>
                </Col>
              ))}
            </Row>
          </Form>
          <GroovePreview value={selected} />
        </div>
        <Alert
          type="info"
          message={`几何面积 ${areas.geometryTotal.toFixed(2)} × 填充系数 ${selected.fillFactor.toFixed(2)} → 熔敷截面积 ${areas.total.toFixed(2)} mm²`}
        />
      </Modal>
    </div>
  )
}

export default ConsumableUsagePage
