/**
 * 焊工考核记录添加/编辑模态框
 */
import React, { useState } from 'react';
import { Modal, Form, Input, DatePicker, InputNumber, Select, Row, Col, message, Switch } from 'antd';
import dayjs from 'dayjs';
import { assessmentRecordService } from '../../../services/welderRecords';
import { workspaceService } from '../../../services/workspace';

const { TextArea } = Input;
const { Option } = Select;

interface AssessmentRecordModalProps {
  visible: boolean;
  welderId: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const AssessmentRecordModal: React.FC<AssessmentRecordModalProps> = ({
  visible,
  welderId,
  onSuccess,
  onCancel,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage();
    if (!currentWorkspace) {
      message.error('请先选择工作区');
      return;
    }

    try {
      const values = await form.validateFields();
      setLoading(true);

      // 格式化日期
      const formattedValues = {
        ...values,
        assessment_date: values.assessment_date ? values.assessment_date.format('YYYY-MM-DD') : undefined,
      };

      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };

      await assessmentRecordService.create(welderId, formattedValues, params);
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
      title="添加考核记录"
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
        initialValues={{
          certificate_issued: false,
          pass_status: false,
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="考核名称"
              name="assessment_name"
              rules={[{ required: true, message: '请输入考核名称' }]}
            >
              <Input placeholder="请输入考核名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="考核类型" name="assessment_type">
              <Select placeholder="请选择考核类型">
                <Option value="理论考核">理论考核</Option>
                <Option value="实操考核">实操考核</Option>
                <Option value="综合考核">综合考核</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="考核日期"
              name="assessment_date"
              rules={[{ required: true, message: '请选择考核日期' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="考核时长(分钟)" name="duration_minutes">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="考核人" name="assessor_name">
              <Input placeholder="请输入考核人姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="考核机构" name="assessor_organization">
              <Input placeholder="请输入考核机构" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="考核内容" name="assessment_content">
          <TextArea rows={3} placeholder="请输入考核内容" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item label="理论成绩" name="theory_score">
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="实操成绩" name="practical_score">
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="总成绩" name="total_score">
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="考核结果" name="assessment_result">
              <Select placeholder="请选择考核结果">
                <Option value="优秀">优秀</Option>
                <Option value="良好">良好</Option>
                <Option value="合格">合格</Option>
                <Option value="不合格">不合格</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="是否通过" name="pass_status" valuePropName="checked">
              <Switch checkedChildren="通过" unCheckedChildren="未通过" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="备注" name="notes">
          <TextArea rows={3} placeholder="请输入备注信息" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default AssessmentRecordModal;

