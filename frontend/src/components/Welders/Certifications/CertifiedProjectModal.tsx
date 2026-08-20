/**
 * 持证项目编辑弹窗（体系证书下的独立到期项目）
 */
import React, { useEffect } from 'react'
import { Modal, Form, Input, DatePicker, InputNumber, Select, message } from 'antd'
import dayjs from 'dayjs'
import type {
  CertifiedProject,
  CreateCertifiedProjectRequest,
} from '../../../services/certifications'

const { Option } = Select
const { TextArea } = Input

interface Props {
  visible: boolean
  submitting?: boolean
  editing?: CertifiedProject | null
  onCancel: () => void
  onSubmit: (values: CreateCertifiedProjectRequest) => Promise<void> | void
}

const CertifiedProjectModal: React.FC<Props> = ({
  visible,
  submitting,
  editing,
  onCancel,
  onSubmit,
}) => {
  const [form] = Form.useForm()
  const isEdit = !!editing

  useEffect(() => {
    if (!visible) return
    if (editing) {
      form.setFieldsValue({
        project_code: editing.project_code,
        project_name: editing.project_name,
        issue_date: editing.issue_date ? dayjs(editing.issue_date) : undefined,
        expiry_date: editing.expiry_date ? dayjs(editing.expiry_date) : undefined,
        renewal_date: editing.renewal_date ? dayjs(editing.renewal_date) : undefined,
        next_renewal_date: editing.next_renewal_date
          ? dayjs(editing.next_renewal_date)
          : undefined,
        renewal_count: editing.renewal_count || 0,
        renewal_result: editing.renewal_result,
        renewal_notes: editing.renewal_notes,
        status: editing.status || 'valid',
        notes: editing.notes,
      })
    } else {
      form.resetFields()
      form.setFieldsValue({ status: 'valid', renewal_count: 0 })
    }
  }, [visible, editing, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      const payload: CreateCertifiedProjectRequest = {
        project_code: values.project_code,
        project_name: values.project_name,
        issue_date: values.issue_date
          ? dayjs(values.issue_date).format('YYYY-MM-DD')
          : undefined,
        expiry_date: values.expiry_date
          ? dayjs(values.expiry_date).format('YYYY-MM-DD')
          : undefined,
        renewal_date: values.renewal_date
          ? dayjs(values.renewal_date).format('YYYY-MM-DD')
          : undefined,
        next_renewal_date: values.next_renewal_date
          ? dayjs(values.next_renewal_date).format('YYYY-MM-DD')
          : undefined,
        renewal_count: values.renewal_count,
        renewal_result: values.renewal_result,
        renewal_notes: values.renewal_notes,
        status: values.status,
        notes: values.notes,
      }
      await onSubmit(payload)
    } catch (error: any) {
      if (error?.errorFields) return
      message.error(error?.message || '提交失败')
    }
  }

  return (
    <Modal
      title={isEdit ? '编辑持证项目' : '添加持证项目'}
      open={visible}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={submitting}
      destroyOnClose
      width={640}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="project_code" label="项目代号">
          <Input placeholder="可选，如 GTAW-6G" />
        </Form.Item>
        <Form.Item
          name="project_name"
          label="持证项目"
          rules={[{ required: true, message: '请输入持证项目名称' }]}
        >
          <Input placeholder="例如：板对接 6G 碳钢" />
        </Form.Item>
        <Form.Item name="issue_date" label="生效/发证日">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="expiry_date" label="到期日">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="renewal_date" label="最近审证日">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="next_renewal_date" label="下次审证日">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="renewal_count" label="审证次数">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="renewal_result" label="审证结果">
          <Select allowClear>
            <Option value="通过">通过</Option>
            <Option value="不通过">不通过</Option>
          </Select>
        </Form.Item>
        <Form.Item name="status" label="状态">
          <Select>
            <Option value="valid">有效</Option>
            <Option value="expiring_soon">即将过期</Option>
            <Option value="expired">已过期</Option>
          </Select>
        </Form.Item>
        <Form.Item name="renewal_notes" label="审证备注">
          <TextArea rows={2} />
        </Form.Item>
        <Form.Item name="notes" label="备注">
          <TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CertifiedProjectModal
