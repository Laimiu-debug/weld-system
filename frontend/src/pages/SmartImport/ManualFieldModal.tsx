import { Alert, Form, Input, Modal, Select, Tag } from 'antd'
import type { FormInstance } from 'antd'
import type { WorkbenchValidation } from '@/services/smartImport'
interface Props {
  open: boolean
  saving: boolean
  form: FormInstance
  options: WorkbenchValidation['binding_options']
  selected?: WorkbenchValidation['binding_options'][number]
  onCancel: () => void
  onSave: () => void
}
export default function ManualFieldModal({ open, saving, form, options, selected, onCancel, onSave }: Props) {
  return (
      <Modal
        title="手工录入模块字段"
        open={open}
        onCancel={() => !saving && onCancel()}
        onOk={onSave}
        confirmLoading={saving}
        okText="保存并确认"
      >
        <Alert
          type="info"
          showIcon
          message="用于补录未识别或禁止自动提取的模块字段"
          description="本操作不会调用模型或扣减额度；保存后字段直接标记为人工确认，并进入审核历史。"
          className="smart-import__modal-alert"
        />
        <Form form={form} layout="vertical">
          <Form.Item name="target" label="模块字段" rules={[{ required: true, message: '请选择字段' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={options.map(item => ({
                value: `${item.field_id || ''}|${item.module_id || ''}|${item.instance_id || ''}|${item.field_key}`,
                label: `${item.label} · ${item.extractable ? '支持自动提取' : item.ai_extract_mode === 'disabled' ? '已禁用自动提取' : '仅手工录入'}`,
              }))}
              placeholder={options.length ? '选择需要补录的字段' : '没有可补录字段'}
            />
          </Form.Item>
          {selected && (
            <Tag color={selected.extractable ? 'blue' : 'orange'}>
              {selected.extractable ? 'AI 未识别，可人工补录' : '该字段不支持自动提取'}
            </Tag>
          )}
          <Form.Item
            name="value"
            label="字段值"
            rules={[{ required: true, message: '请输入字段值' }]}
            extra={selected?.field_type === 'table' ? '表格字段请输入合法 JSON 数组。' : undefined}
          >
            {selected?.field_type === 'checkbox' ? (
              <Select options={[{ value: 'true', label: '是' }, { value: 'false', label: '否' }]} />
            ) : (
              <Input.TextArea rows={4} maxLength={10000} />
            )}
          </Form.Item>
          <Form.Item name="reason" label="录入说明（可选）">
            <Input.TextArea rows={2} maxLength={1000} />
          </Form.Item>
        </Form>
      </Modal>
  )
}
