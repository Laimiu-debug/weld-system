/**
 * 焊工培训记录添加/编辑模态框
 */
import React, { useState } from 'react';
import { Modal, Form, Input, DatePicker, InputNumber, Select, Row, Col, message, Switch } from 'antd';
import dayjs from 'dayjs';
import { trainingRecordService } from '../../../services/welderRecords';
import { workspaceService } from '../../../services/workspace';

const { TextArea } = Input;
const { Option } = Select;

interface TrainingRecordModalProps {
  visible: boolean;
  welderId: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const TrainingRecordModal: React.FC<TrainingRecordModalProps> = ({
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
        start_date: values.start_date ? values.start_date.format('YYYY-MM-DD') : undefined,
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : undefined,
      };

      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };

      await trainingRecordService.create(welderId, formattedValues, params);
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
      title="添加培训记录"
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
              label="培训名称"
              name="training_name"
              rules={[{ required: true, message: '请输入培训名称' }]}
            >
              <Input placeholder="请输入培训名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="培训类型" name="training_type">
              <Select placeholder="请选择培训类型">
                <Option value="内部培训">内部培训</Option>
                <Option value="外部培训">外部培训</Option>
                <Option value="在线培训">在线培训</Option>
                <Option value="实操培训">实操培训</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="开始日期"
              name="start_date"
              rules={[{ required: true, message: '请选择开始日期' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="结束日期" name="end_date">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="培训时长(h)" name="duration_hours">
              <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="培训机构" name="training_organization">
              <Input placeholder="请输入培训机构" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="培训师" name="trainer_name">
              <Input placeholder="请输入培训师姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="培训地点" name="training_location">
              <Input placeholder="请输入培训地点" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="培训内容" name="training_content">
          <TextArea rows={3} placeholder="请输入培训内容" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="考核成绩" name="assessment_score">
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="是否通过" name="pass_status" valuePropName="checked">
              <Switch checkedChildren="通过" unCheckedChildren="未通过" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="是否颁发证书" name="certificate_issued" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="证书编号" name="certificate_number">
              <Input placeholder="请输入证书编号" />
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

export default TrainingRecordModal;

