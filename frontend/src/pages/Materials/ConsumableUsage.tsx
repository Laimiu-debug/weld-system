import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert, Button, Card, Col, Divider, Form, Input, InputNumber, List, Modal, Row,
  Segmented, Select, Space, Statistic, Tag, Typography, message,
} from 'antd'
import {
  CalculatorOutlined, DeleteOutlined, FileExcelOutlined, FilePdfOutlined,
  PlusOutlined, SaveOutlined,
} from '@ant-design/icons'
import { DataRow, engineeringService } from '@/services/engineering'
import './consumableCalculator.css'

const { Title, Text } = Typography
type Groove = 'I' | 'V' | 'X' | 'U' | 'FILLET' | 'LAP'
type OperationRole = 'face' | 'gouge' | 'tack' | 'custom'
type Operation = {
  id: string; role: OperationRole; name: string; method: string; material: string
  density: number; efficiency: number; unitPrice: number; fluxRatio: number; customArea: number
}
type Joint = {
  id: string; name: string; length: number; groove: Groove; thickness: number; angle: number
  gap: number; rootFace: number; radius: number; upperHeight: number; legSize: number
  reinforcement: number; backGougeDepth: number; faceExtra: number; fillFactor: number
  operations: Operation[]
}
type LengthDraft = { mode: 'circumference' | 'straight'; diameter: number; angle: number; count: number; straight: number }

const grooveOptions = [
  { value: 'I', label: 'I形对接' }, { value: 'V', label: 'V形对接' },
  { value: 'X', label: 'X形对接' }, { value: 'U', label: 'U形对接' },
  { value: 'FILLET', label: '角焊缝' }, { value: 'LAP', label: '搭接' },
]
const roleMeta: Record<OperationRole, { label: string; area: 'face' | 'gouge' | 'custom' }> = {
  face: { label: '正面填充', area: 'face' }, gouge: { label: '清根填充', area: 'gouge' },
  tack: { label: '固定焊', area: 'custom' }, custom: { label: '自定义工序', area: 'custom' },
}
const num = (value: unknown, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback
const op = (role: OperationRole = 'face', seed: Partial<Operation> = {}): Operation => ({
  id: crypto.randomUUID(), role, name: roleMeta[role].label, method: 'GMAW(熔化极气保焊) (135)',
  material: 'ER50-6 焊丝', density: 7.85, efficiency: 0.9, unitPrice: 0, fluxRatio: 0,
  customArea: role === 'tack' ? 8 : 0, ...seed,
})
const joint = (seed: Partial<Joint> = {}): Joint => ({
  id: crypto.randomUUID(), name: '', length: 0, groove: 'V', thickness: 12, angle: 60,
  gap: 2, rootFace: 2, radius: 5, upperHeight: 0, legSize: 8, reinforcement: 2,
  backGougeDepth: 2, faceExtra: 1, fillFactor: 1.05, operations: [op()], ...seed,
})
const normalizeGroove = (value: unknown): Groove => {
  const text = String(value || '').toUpperCase()
  if (text.includes('角') || text.includes('FILLET')) return 'FILLET'
  if (text.includes('搭') || text.includes('LAP')) return 'LAP'
  if (text.startsWith('X') || text.includes('X形')) return 'X'
  if (text.startsWith('U') || text.includes('U形')) return 'U'
  if (text.startsWith('I') || text.includes('I形')) return 'I'
  return 'V'
}
const tanHalf = (angle: number) => Math.tan(angle * Math.PI / 360)
const triangle = (width: number, height: number) => Math.max(width, 0) * Math.max(height, 0) / 2
const geometry = (j: Joint) => {
  if (j.groove === 'FILLET' || j.groove === 'LAP') {
    const total = 0.5 * j.legSize ** 2 * j.fillFactor
    return { face: total, gouge: 0, total }
  }
  const t = Math.max(j.thickness, 0); const gap = Math.max(j.gap, 0); const bevel = Math.max(t - j.rootFace, 0)
  const tan = tanHalf(j.angle); let base = t * gap
  if (j.groove === 'I') base += triangle(gap + 2 * j.faceExtra, j.reinforcement)
  if (j.groove === 'V') base += bevel ** 2 * tan + triangle(gap + 2 * bevel * tan + 2 * j.faceExtra, j.reinforcement)
  if (j.groove === 'X') {
    const upper = j.upperHeight > 0 ? Math.min(j.upperHeight, bevel) : bevel / 2; const lower = Math.max(bevel - upper, 0)
    base += upper ** 2 * tan + lower ** 2 * tan
    base += triangle(gap + 2 * upper * tan + 2 * j.faceExtra, j.reinforcement)
    base += triangle(gap + 2 * lower * tan + 2 * j.faceExtra, j.reinforcement)
  }
  if (j.groove === 'U') {
    const radius = Math.min(Math.max(j.radius, 0), bevel); const straight = Math.max(bevel - radius, 0)
    base += 2 * radius * straight + straight ** 2 * tan + Math.PI * radius ** 2 / 2
    base += triangle(gap + 2 * radius + 2 * straight * tan + 2 * j.faceExtra, j.reinforcement)
  }
  const gougeCavity = j.backGougeDepth > 0 ? j.backGougeDepth * (gap + 0.5 * j.backGougeDepth) : 0
  const gougeReinf = j.groove !== 'X' && j.backGougeDepth > 0
    ? triangle(gap + j.backGougeDepth + 2 * j.faceExtra, j.reinforcement) : 0
  const gouge = (gougeCavity + gougeReinf) * j.fillFactor
  const total = Math.max((base + gougeCavity + gougeReinf) * j.fillFactor, 0)
  return { face: Math.max(total - gouge, 0), gouge, total }
}
const operationResult = (j: Joint, operation: Operation) => {
  const areas = geometry(j); const areaKind = roleMeta[operation.role].area
  const area = areaKind === 'face' ? areas.face : areaKind === 'gouge' ? areas.gouge : operation.customArea
  const deposit = area * j.length * operation.density / 1_000_000
  const consumable = operation.efficiency > 0 ? deposit / operation.efficiency : 0
  return { area, deposit, consumable, flux: consumable * operation.fluxRatio, cost: consumable * operation.unitPrice }
}

const GroovePreview: React.FC<{ value: Joint }> = ({ value }) => {
  const area = geometry(value).total
  const label = grooveOptions.find(item => item.value === value.groove)?.label
  const isFillet = value.groove === 'FILLET' || value.groove === 'LAP'
  return <div className="cc-preview" role="img" aria-label={`${label}截面预览`}>
    <div className="cc-preview__title">{label}　A = {area.toFixed(1)} mm²</div>
    <svg viewBox="0 0 480 230" aria-hidden="true">
      {isFillet ? <>
        <rect x="70" y="145" width="340" height="55" fill="#8a9097" stroke="#4b5563" />
        <rect x="210" y="30" width="55" height="145" fill="#8a9097" stroke="#4b5563" />
        <path d="M210 145 L145 145 L210 82 Z" fill="#e3a11a" stroke="#9a6700" strokeWidth="3" />
      </> : <>
        <path d="M45 70 H205 L240 145 L275 70 H435 V190 H275 L240 145 L205 190 H45 Z" fill="#8a9097" stroke="#4b5563" strokeWidth="3" />
        <path d={value.groove === 'I' ? 'M226 65 H254 V194 H226 Z' : 'M196 65 H284 L240 145 L265 194 H215 L240 145 Z'} fill="#e3a11a" stroke="#9a6700" strokeWidth="3" />
        <path d="M196 65 Q240 35 284 65" fill="#e3a11a" stroke="#9a6700" strokeWidth="3" />
      </>}
      <line x1="370" y1="70" x2="370" y2="190" stroke="#1677ff" strokeWidth="2" />
      <text x="378" y="136" fill="#1677ff" fontSize="18">t={value.thickness}</text>
    </svg>
  </div>
}

const ConsumableUsagePage: React.FC = () => {
  const [projects, setProjects] = useState<DataRow[]>([]); const [products, setProducts] = useState<DataRow[]>([])
  const [revisions, setRevisions] = useState<DataRow[]>([]); const [projectId, setProjectId] = useState<string>()
  const [productId, setProductId] = useState<string>(); const [revisionId, setRevisionId] = useState<string>()
  const [joints, setJoints] = useState<Joint[]>([joint()]); const [selectedId, setSelectedId] = useState('')
  const [selectedOpId, setSelectedOpId] = useState(''); const [lengthOpen, setLengthOpen] = useState(false)
  const [grooveOpen, setGrooveOpen] = useState(false); const [calculated, setCalculated] = useState(false)
  const [lengthDraft, setLengthDraft] = useState<LengthDraft>({ mode: 'circumference', diameter: 219, angle: 360, count: 1, straight: 1000 })
  useEffect(() => { void engineeringService.projects().then(setProjects) }, [])
  useEffect(() => { setProductId(undefined); setRevisionId(undefined); setProducts([]); setRevisions([]); if (projectId) void engineeringService.products(projectId).then(setProducts) }, [projectId])
  useEffect(() => { setRevisionId(undefined); setRevisions([]); if (productId) void engineeringService.revisions(productId).then(setRevisions) }, [productId])
  useEffect(() => { if (!selectedId && joints[0]) setSelectedId(joints[0].id) }, [joints, selectedId])
  const selected = joints.find(item => item.id === selectedId) || joints[0]
  const selectedOp = selected?.operations.find(item => item.id === selectedOpId) || selected?.operations[0]
  useEffect(() => { if (selected?.operations[0] && !selected?.operations.some(item => item.id === selectedOpId)) setSelectedOpId(selected.operations[0].id) }, [selected, selectedOpId])
  const storageKey = `consumable-calculator-v2:${projectId || 'unassigned'}`
  useEffect(() => {
    if (!projectId) return
    const raw = localStorage.getItem(storageKey)
    if (!raw) return
    try { const saved = JSON.parse(raw) as Joint[]; setJoints(saved); setSelectedId(saved[0]?.id || ''); message.info('已恢复该项目的焊材计算草稿') } catch { /* ignore invalid local draft */ }
  }, [projectId, storageKey])
  const updateJoint = (values: Partial<Joint>) => { setJoints(current => current.map(item => item.id === selected.id ? { ...item, ...values } : item)); setCalculated(false) }
  const updateOperation = (values: Partial<Operation>) => { if (!selectedOp) return; updateJoint({ operations: selected.operations.map(item => item.id === selectedOp.id ? { ...item, ...values } : item) }) }
  const importRevision = async () => {
    if (!revisionId) return
    const detail = await engineeringService.detail(revisionId); const parts = new Map(detail.parts.map(item => [item.id, item]))
    const imported = detail.weld_joints.map((item, index) => {
      const a = parts.get(item.part_a_id); const b = parts.get(item.part_b_id); const req = detail.requirements.find(value => value.weld_joint_id === item.id)
      return joint({ id: item.id, name: item.weld_number || `焊缝 ${index + 1}`, length: num(item.length_mm), groove: normalizeGroove(item.groove_type || item.joint_type),
        thickness: Math.max(num(a?.thickness_mm), num(b?.thickness_mm), 12), angle: num(item.groove_angle, 60), gap: num(item.root_gap, 2), rootFace: num(item.root_face, 2), legSize: num(item.weld_size, 8),
        operations: [op('face', { material: req?.filler_material_spec || req?.filler_material_classification || 'ER50-6 焊丝' })] })
    })
    if (!imported.length) return message.warning('该图纸版本没有焊缝，请先完成图纸识别或人工新增焊缝')
    setJoints(imported); setSelectedId(imported[0].id); message.success(`已导入 ${imported.length} 条焊缝`)
  }
  const allResults = useMemo(() => joints.flatMap(item => item.operations.map(operation => ({ joint: item, operation, ...operationResult(item, operation) }))), [joints])
  const totals = useMemo(() => allResults.reduce((sum, item) => ({ deposit: sum.deposit + item.deposit, consumable: sum.consumable + item.consumable, flux: sum.flux + item.flux, cost: sum.cost + item.cost }), { deposit: 0, consumable: 0, flux: 0, cost: 0 }), [allResults])
  const currentResults = selected ? selected.operations.map(operation => ({ operation, ...operationResult(selected, operation) })) : []
  const currentTotals = currentResults.reduce((sum, item) => ({ consumable: sum.consumable + item.consumable, flux: sum.flux + item.flux, cost: sum.cost + item.cost }), { consumable: 0, flux: 0, cost: 0 })
  const addOperation = (role: OperationRole) => updateJoint({ operations: [...selected.operations, op(role)] })
  const save = () => { if (!projectId) return message.warning('请先选择项目'); localStorage.setItem(storageKey, JSON.stringify(joints)); message.success('项目焊材计算草稿已保存') }
  const exportCsv = () => {
    const lines = [['焊缝', '工序', '方法', '焊材', '截面积mm²', '长度mm', '焊材kg', '焊剂kg', '材料费'], ...allResults.map(item => [item.joint.name, item.operation.name, item.operation.method, item.operation.material, item.area.toFixed(2), item.joint.length.toFixed(1), item.consumable.toFixed(3), item.flux.toFixed(3), item.cost.toFixed(2)])]
    const blob = new Blob([`\uFEFF${lines.map(line => line.join(',')).join('\n')}`], { type: 'text/csv;charset=utf-8' }); const url = URL.createObjectURL(blob)
    const link = document.createElement('a'); link.href = url; link.download = '项目焊材用量.csv'; link.click(); URL.revokeObjectURL(url)
  }
  if (!selected) return null
  const areas = geometry(selected); const lengthValue = lengthDraft.mode === 'circumference' ? Math.PI * lengthDraft.diameter * lengthDraft.angle / 360 * lengthDraft.count : lengthDraft.straight * lengthDraft.count
  return <div className="cc-page">
    <div className="cc-heading"><div><Title level={2}>焊材用量计算器</Title><Text type="secondary">按项目建立焊缝，精算坡口截面、工序焊材和焊剂用量</Text></div></div>
    <Card className="cc-toolbar"><div className="cc-toolbar__inner">
      <Space wrap><Select showSearch optionFilterProp="label" placeholder="当前项目" style={{ width: 220 }} value={projectId} options={projects.map(item => ({ value: item.id, label: `${item.code} · ${item.name}` }))} onChange={setProjectId} /><Select placeholder="产品" disabled={!projectId} style={{ width: 200 }} value={productId} options={products.map(item => ({ value: item.id, label: item.name }))} onChange={setProductId} /><Select placeholder="图纸版本" disabled={!productId} style={{ width: 220 }} value={revisionId} options={revisions.map(item => ({ value: item.id, label: `版本 ${item.revision_number} · ${item.drawing_filename}` }))} onChange={setRevisionId} /><Button disabled={!revisionId} onClick={() => void importRevision()}>导入图纸焊缝</Button></Space>
      <Space><Button type="primary" className="cc-save" icon={<SaveOutlined />} onClick={save}>保存项目</Button><Button icon={<FileExcelOutlined />} onClick={exportCsv}>导出 Excel</Button><Button icon={<FilePdfOutlined />} onClick={() => window.print()}>导出 PDF</Button></Space>
    </div></Card>
    <div className="cc-workbench">
      <Card className="cc-joints" title="焊缝列表"><Button type="primary" block icon={<PlusOutlined />} onClick={() => { const value = joint({ name: `焊缝 ${joints.length + 1}` }); setJoints(current => [...current, value]); setSelectedId(value.id) }}>添加为新焊缝</Button><List dataSource={joints} locale={{ emptyText: '暂无焊缝' }} renderItem={item => <List.Item className={item.id === selected.id ? 'cc-joint cc-joint--active' : 'cc-joint'} onClick={() => setSelectedId(item.id)} actions={[<Button key="delete" danger type="text" size="small" icon={<DeleteOutlined />} onClick={event => { event.stopPropagation(); setJoints(current => current.filter(value => value.id !== item.id)); setSelectedId('') }} />]}><List.Item.Meta title={item.name || '未命名焊缝'} description={`${grooveOptions.find(value => value.value === item.groove)?.label} · ${item.length.toFixed(1)} mm`} /></List.Item>} /></Card>
      <main className="cc-editor">
        <Card title={<span><b>①</b> 焊口</span>}><Form layout="vertical"><Row gutter={16}><Col span={15}><Form.Item label="焊缝名称"><Input value={selected.name} placeholder="如：筒体纵缝 A-1" onChange={event => updateJoint({ name: event.target.value })} /></Form.Item></Col><Col span={9}><Form.Item label="焊缝长度"><Space.Compact block><InputNumber style={{ width: '100%' }} min={0} precision={1} value={selected.length} addonAfter="mm" onChange={value => updateJoint({ length: num(value) })} /><Button onClick={() => setLengthOpen(true)}>计算长度</Button></Space.Compact></Form.Item></Col></Row></Form></Card>
        <Card title={<span><b>②</b> 坡口几何 <Text type="secondary">（系统计算截面积）</Text></span>}><Row gutter={[16, 12]} align="middle"><Col xs={24} md={10}><Text type="secondary">坡口形式</Text><Select style={{ width: '100%', marginTop: 6 }} value={selected.groove} options={grooveOptions} onChange={value => updateJoint({ groove: value })} /></Col><Col xs={24} md={7}><Text type="secondary">板厚 t</Text><InputNumber style={{ width: '100%', marginTop: 6 }} min={0.1} value={selected.thickness} addonAfter="mm" onChange={value => updateJoint({ thickness: num(value) })} /></Col><Col xs={24} md={7}><Button block onClick={() => setGrooveOpen(true)}>精确计算</Button></Col><Col span={24}><Space size="large" wrap><span>正面面积 <b>{areas.face.toFixed(2)} mm²</b></span><span>清根面积 <b>{areas.gouge.toFixed(2)} mm²</b></span><span>合计面积 <b className="cc-accent">{areas.total.toFixed(2)} mm²</b></span></Space></Col></Row></Card>
        <Card title={<span><b>③</b> 焊接工序 <Text type="secondary">（方法与焊材）</Text></span>}><div className="cc-op-actions"><Button onClick={() => addOperation('face')}>＋ 正面填充</Button><Button onClick={() => addOperation('gouge')}>＋ 清根填充</Button><Button onClick={() => addOperation('tack')}>＋ 固定焊</Button><Button onClick={() => addOperation('custom')}>＋ 自定义</Button></div><div className="cc-op-layout"><List className="cc-op-list" dataSource={selected.operations} renderItem={item => <List.Item className={item.id === selectedOp?.id ? 'cc-op cc-op--active' : 'cc-op'} onClick={() => setSelectedOpId(item.id)}>{item.name}<Text type="secondary">{operationResult(selected, item).area.toFixed(1)}mm² × {selected.length.toFixed(0)}mm</Text></List.Item>} />{selectedOp && <Form layout="vertical" className="cc-op-form"><Row gutter={12}><Col span={12}><Form.Item label="工序"><Input value={selectedOp.name} onChange={event => updateOperation({ name: event.target.value })} /></Form.Item></Col><Col span={12}><Form.Item label="焊接方法"><Input value={selectedOp.method} onChange={event => updateOperation({ method: event.target.value })} /></Form.Item></Col><Col span={12}><Form.Item label="焊材"><Input value={selectedOp.material} onChange={event => updateOperation({ material: event.target.value })} /></Form.Item></Col><Col span={6}><Form.Item label="密度"><InputNumber min={0.01} value={selectedOp.density} onChange={value => updateOperation({ density: num(value) })} /></Form.Item></Col><Col span={6}><Form.Item label="熔敷效率"><InputNumber min={0.01} max={1} step={0.01} value={selectedOp.efficiency} onChange={value => updateOperation({ efficiency: num(value) })} /></Form.Item></Col><Col span={8}><Form.Item label="单价 元/kg"><InputNumber min={0} value={selectedOp.unitPrice} onChange={value => updateOperation({ unitPrice: num(value) })} /></Form.Item></Col><Col span={8}><Form.Item label="焊剂/焊丝比"><InputNumber min={0} step={0.1} value={selectedOp.fluxRatio} onChange={value => updateOperation({ fluxRatio: num(value) })} /></Form.Item></Col><Col span={8}><Form.Item label="自定义截面积"><InputNumber disabled={!['tack', 'custom'].includes(selectedOp.role)} min={0} value={selectedOp.customArea} addonAfter="mm²" onChange={value => updateOperation({ customArea: num(value) })} /></Form.Item></Col></Row><Button danger icon={<DeleteOutlined />} disabled={selected.operations.length <= 1} onClick={() => updateJoint({ operations: selected.operations.filter(item => item.id !== selectedOp.id) })}>删除工序</Button></Form>}</div></Card>
      </main>
      <aside className="cc-side"><Card title="截面预览"><GroovePreview value={selected} /></Card><Card title="试算结果"><Button type="primary" block size="large" icon={<CalculatorOutlined />} onClick={() => { setCalculated(true); message.success('当前焊缝计算完成') }}>计算当前焊缝</Button><Tag color={calculated ? 'success' : 'processing'} className="cc-status">状态：{calculated ? '已计算' : '参数编辑中'}</Tag><Divider /><Statistic title="消耗焊材" value={currentTotals.consumable} precision={3} suffix="kg" /><Statistic title="消耗焊剂" value={currentTotals.flux} precision={3} suffix="kg" /><Statistic title="材料费" value={currentTotals.cost} precision={2} prefix="¥" /><Divider /><Text strong>项目汇总：{totals.consumable.toFixed(3)} kg</Text></Card></aside>
    </div>
    <Modal title="焊缝长度计算器" open={lengthOpen} onCancel={() => setLengthOpen(false)} onOk={() => { updateJoint({ length: lengthValue }); setLengthOpen(false) }} okText="应用长度"><Form layout="vertical"><Form.Item label="类型"><Segmented block value={lengthDraft.mode} options={[{ value: 'circumference', label: '环缝（按外径）' }, { value: 'straight', label: '直缝' }]} onChange={value => setLengthDraft(current => ({ ...current, mode: value as LengthDraft['mode'] }))} /></Form.Item>{lengthDraft.mode === 'circumference' ? <><Form.Item label="外径 D"><InputNumber style={{ width: '100%' }} min={0} value={lengthDraft.diameter} addonAfter="mm" onChange={value => setLengthDraft(current => ({ ...current, diameter: num(value) }))} /></Form.Item><Form.Item label="单道包角"><InputNumber style={{ width: '100%' }} min={0} max={360} value={lengthDraft.angle} addonAfter="°" onChange={value => setLengthDraft(current => ({ ...current, angle: num(value) }))} /></Form.Item></> : <Form.Item label="单条长度"><InputNumber style={{ width: '100%' }} min={0} value={lengthDraft.straight} addonAfter="mm" onChange={value => setLengthDraft(current => ({ ...current, straight: num(value) }))} /></Form.Item>}<Form.Item label="条数"><InputNumber style={{ width: '100%' }} min={1} precision={0} value={lengthDraft.count} onChange={value => setLengthDraft(current => ({ ...current, count: num(value, 1) }))} /></Form.Item><Alert type="info" showIcon message={`焊缝总长度 = ${lengthValue.toFixed(1)} mm`} /></Form></Modal>
    <Modal title="坡口截面积计算器" width="min(1180px, 96vw)" open={grooveOpen} onCancel={() => setGrooveOpen(false)} onOk={() => setGrooveOpen(false)} okText="应用参数"><div className="cc-groove-modal"><Form layout="vertical"><Row gutter={12}><Col span={12}><Form.Item label="坡口形式"><Select value={selected.groove} options={grooveOptions} onChange={value => updateJoint({ groove: value })} /></Form.Item></Col><Col span={12}><Form.Item label="板厚 t (mm)"><InputNumber value={selected.thickness} onChange={value => updateJoint({ thickness: num(value) })} /></Form.Item></Col>{[['坡口夹角 α', 'angle'], ['间隙 b', 'gap'], ['钝边 p', 'rootFace'], ['余高 c', 'reinforcement'], ['清根深度', 'backGougeDepth'], ['焊缝展宽（单侧）', 'faceExtra'], ['半径 R', 'radius'], ['填充系数', 'fillFactor']].map(([label, key]) => <Col span={12} key={key}><Form.Item label={label}><InputNumber value={selected[key as keyof Joint] as number} step={key === 'fillFactor' ? 0.01 : 0.1} onChange={value => updateJoint({ [key]: num(value) })} /></Form.Item></Col>)}</Row></Form><GroovePreview value={selected} /></div><Alert type="info" message={`几何面积 ${(areas.total / selected.fillFactor).toFixed(2)} × 填充系数 ${selected.fillFactor.toFixed(2)} → 熔敷截面积 ${areas.total.toFixed(2)} mm²`} /></Modal>
  </div>
}
export default ConsumableUsagePage
