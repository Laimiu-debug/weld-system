/**
 * 焊工工作履历添加/编辑模态框
 */
import React, { useEffect, useState } from 'react'
import { Modal, Form, Input, DatePicker, Row, Col, Checkbox, message } from 'antd'
import dayjs from 'dayjs'
import { workHistoryService, type WelderWorkHistory } from '../../../services/welderRecords'
import { workspaceService } from '../../../services/workspace'

const { TextArea } = Input
const { RangePicker } = DatePicker

interface WorkHistoryModalProps {
  visible: boolean
  welderId: number
  editing?: WelderWorkHistory | null
  onSuccess: () => void
  onCancel: () => void
}

const WorkHistoryModal: React.FC<WorkHistoryModalProps> = ({
  visible,
  welderId,
  editing,
  onSuccess,
  onCancel,
}) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
  const [form] = Form.useForm()
  const isCurrent = Form.useWatch('is_current', form)
  const [loading, setLoading] = useState(false)
  const isEdit = !!editing

  useEffect(() => {
    if (!visible) return
    if (editing) {
      form.setFieldsValue({
        company_name: editing.company_name,
        position: editing.position,
        department: editing.department,
        location: editing.location,
        job_description: editing.job_description,
        achievements: editing.achievements,
        leaving_reason: editing.leaving_reason,
        is_current: !editing.end_date,
        work_period: [
          editing.start_date ? dayjs(editing.start_date) : undefined,
          editing.end_date ? dayjs(editing.end_date) : undefined,
        ],
      })
    } else {
      form.resetFields()
    }
  }, [visible, editing, form])

  const handleOk = async () => {
    if (!currentWorkspace) {
      message.error('未找到工作区信息')
      return
    }
    try {
      const values = await form.validateFields()
      setLoading(true)
      const formattedValues = {
        company_name: values.company_name,
        position: values.position,
        department: values.department,
        location: values.location,
        job_description: values.job_description,
        achievements: values.achievements,
        leaving_reason: values.leaving_reason,
        start_date: values.work_period?.[0]
          ? values.work_period[0].format('YYYY-MM-DD')
          : undefined,
        end_date: !values.is_current && values.work_period?.[1]
          ? values.work_period[1].format('YYYY-MM-DD')
          : null,
      }
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      }
      if (isEdit && editing) {
        await workHistoryService.update(welderId, editing.id, formattedValues, params)
        message.success('履历已更新')
      } else {
        await workHistoryService.create(welderId, formattedValues, params)
        message.success('履历已添加')
      }
      form.resetFields()
      onSuccess()
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请填写必填字段')
      } else {
        message.error(error.response?.data?.detail || '保存失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? '编辑工作履历' : '添加工作履历'}
      open={visible}
      onOk={handleOk}
      onCancel={() => {
        if (loading) return
        form.resetFields()
        onCancel()
      }}
      confirmLoading={loading}
      cancelButtonProps={{ disabled: loading }}
      closable={!loading}
      maskClosable={!loading}
      width={800}
      destroyOnClose
    >
      <Form form={form} layout="vertical" disabled={loading}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="公司名称"
              name="company_name"
              rules={[{ required: true, message: '请输入公司名称' }]}
            >
              <Input placeholder="请输入公司名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="职位"
              name="position"
              rules={[{ required: true, message: '请输入职位' }]}
            >
              <Input placeholder="如：焊工、高级焊工" />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="工作时间"
              name="work_period"
              rules={[{ required: true, message: '请选择工作时间' }]}
            >
              <RangePicker
                style={{ width: '100%' }}
                placeholder={['开始日期', '结束日期（可不填）']}
                allowEmpty={[false, true]}
                disabled={[false, !!isCurrent]}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="部门" name="department">
              <Input placeholder="请输入部门" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="is_current" valuePropName="checked">
          <Checkbox onChange={event => {
            if (event.target.checked) {
              form.setFieldValue('work_period', [form.getFieldValue('work_period')?.[0], null])
            }
          }}>仍在职（不填写结束日期）</Checkbox>
        </Form.Item>
        <Form.Item label="工作地点" name="location">
          <Input placeholder="请输入工作地点" />
        </Form.Item>
        <Form.Item label="工作内容" name="job_description">
          <TextArea rows={3} placeholder="请描述主要工作内容" />
        </Form.Item>
        <Form.Item label="主要成就" name="achievements">
          <TextArea rows={3} placeholder="主要成就或项目经验" />
        </Form.Item>
        <Form.Item label="离职原因" name="leaving_reason">
          <Input placeholder="可选" />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default WorkHistoryModal
