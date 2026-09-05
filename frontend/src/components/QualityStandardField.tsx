import React, { useEffect, useState } from 'react'
import { Alert, Button, Form, Select, Space, Typography } from 'antd'
import { qualityStandardApi, readWorkspaceQuery } from '@/services/businessExtensions'

export const StandardSnapshot: React.FC<{ snapshot?: any }> = ({ snapshot }) => {
  if (!snapshot) return <Typography.Text type="secondary">未关联质量标准；历史记录不补造标准快照。</Typography.Text>
  const texts = (value: any) => {
    try { return JSON.parse(value || '[]').join('；') } catch { return String(value || '') }
  }
  return <Alert type="info" showIcon message={`检验依据：${snapshot.standard_code} · ${snapshot.standard_name} · 版本 ${snapshot.version}`} description={<Space direction="vertical">
    <span>检验方法：{texts(snapshot.test_methods) || '未填写'}</span>
    <span>验收项：{texts(snapshot.acceptance_criteria)}</span>
    <span>已保存的检验依据不会随标准库修改而变化。</span>
  </Space>} />
}

const QualityStandardField: React.FC<{ form: any; snapshot?: any }> = ({ form, snapshot }) => {
  const [items, setItems] = useState<any[]>([])
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(false)
  const [retry, setRetry] = useState(0)
  const selected = Form.useWatch('standard_id', form)
  const workspaceKey = JSON.stringify(readWorkspaceQuery())
  useEffect(() => {
    if (snapshot) return
    let active = true
    setLoading(true); setError(false)
    qualityStandardApi.list({ ...readWorkspaceQuery(), limit: 200, status: 'active' })
      .then(data => { if (active) setItems(data.items || []) })
      .catch(() => { if (active) { setItems([]); setError(true) } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [workspaceKey, retry, snapshot])
  if (snapshot) return <StandardSnapshot snapshot={snapshot} />
  return <>
    {error && <Alert type="error" message="质量标准加载失败" action={<Button onClick={() => setRetry(x => x + 1)}>重试</Button>} />}
    <Form.Item name="standard_id" label="质量标准" extra="选用标准时会保存版本、检验方法和验收项；标准须在检验日期有效。">
      <Select allowClear showSearch optionFilterProp="label" loading={loading} disabled={error} options={items.map(item => ({ value: item.id, label: `${item.standard_code} · ${item.standard_name} · ${item.version || '缺少版本'}` }))} />
    </Form.Item>
    {selected && <StandardSnapshot snapshot={items.find(item => item.id === selected)} />}
  </>
}
export default QualityStandardField
