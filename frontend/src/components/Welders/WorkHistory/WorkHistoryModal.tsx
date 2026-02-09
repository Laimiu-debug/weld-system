/**
 * 焊工工作履历添加/编辑模态框
 */
import React, { useState } from 'react';
import { Modal, Form, Input, DatePicker, Row, Col, message } from 'antd';
import dayjs from 'dayjs';
import { workHistoryService } from '../../../services/welderRecords';
import { workspaceService } from '../../../services/workspace';

const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface WorkHistoryModalProps {
  visible: boolean;
  welderId: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const WorkHistoryModal: React.FC<WorkHistoryModalProps> = ({
  visible,
  welderId,
  onSuccess,
  onCancel,
}) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    if (!currentWorkspace) {
      message.error('未找到工作区信息');
      return;
    }

    try {
      const values = await form.validateFields();
      setLoading(true);

      // 格式化日期
      const formattedValues = {
        ...values,
        start_date: values.work_period ? values.work_period[0].format('YYYY-MM-DD') : undefined,
        end_date: values.work_period && values.work_period[1] ? values.work_period[1].format('YYYY-MM-DD') : undefined,
      };
      delete formattedValues.work_period;

      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };

      await workHistoryService.create(welderId, formattedValues, params);

      message.success('添加成功');
      form.resetFields();
      onSuccess();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请填写必填字段');
      } else {
        message.error(error.response?.data?.detail || '添加失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="添加工作履历"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={loading}
      width={800}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
      >
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
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="部门" name="department">
              <Input placeholder="请输入部门" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="工作地点" name="location">
          <Input placeholder="请输入工作地点" />
        </Form.Item>

        <Form.Item label="工作内容" name="job_description">
          <TextArea rows={3} placeholder="请描述主要工作内容" />
        </Form.Item>

        <Form.Item label="主要成就" name="achievements">
          <TextArea rows={3} placeholder="请描述在该公司的主要成就或项目经验" />
        </Form.Item>

        <Form.Item label="离职原因" name="leaving_reason">
          <Input placeholder="请输入离职原因（可选）" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default WorkHistoryModal;

