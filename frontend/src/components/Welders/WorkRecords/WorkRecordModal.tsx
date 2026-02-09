/**
 * 焊工焊接操作记录添加/编辑模态框
 */
import React, { useState } from 'react';
import { Modal, Form, Input, DatePicker, InputNumber, Select, Row, Col, message } from 'antd';
import dayjs from 'dayjs';
import { workRecordService } from '../../../services/welderRecords';
import { workspaceService } from '../../../services/workspace';

const { TextArea } = Input;
const { Option } = Select;

interface WorkRecordModalProps {
  visible: boolean;
  welderId: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const WorkRecordModal: React.FC<WorkRecordModalProps> = ({
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
        work_date: values.work_date ? values.work_date.format('YYYY-MM-DD') : undefined,
      };

      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.company_id,
        factory_id: currentWorkspace.factory_id,
      };

      await workRecordService.create(welderId, formattedValues, params);
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
      title="添加焊接操作记录"
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
          defect_count: 0,
          rework_count: 0,
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="工作日期"
              name="work_date"
              rules={[{ required: true, message: '请选择工作日期' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="班次" name="work_shift">
              <Select placeholder="请选择班次">
                <Option value="早班">早班</Option>
                <Option value="中班">中班</Option>
                <Option value="晚班">晚班</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="工时(h)" name="work_hours">
              <InputNumber min={0} max={24} step={0.5} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="焊接工艺" name="welding_process">
              <Input placeholder="如：SMAW、GTAW、GMAW" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="焊接位置" name="welding_position">
              <Input placeholder="如：1G、2G、3G、4G、5G、6G" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="母材" name="base_material">
              <Input placeholder="如：Q345R、16MnR" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="填充材料" name="filler_material">
              <Input placeholder="如：E5015、ER50-6" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="焊接长度(m)" name="weld_length">
              <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="焊接重量(kg)" name="weld_weight">
              <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="质量结果" name="quality_result">
              <Select placeholder="请选择质量结果">
                <Option value="优秀">优秀</Option>
                <Option value="合格">合格</Option>
                <Option value="不合格">不合格</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="缺陷数量" name="defect_count">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="返工次数" name="rework_count">
              <InputNumber min={0} style={{ width: '100%' }} />
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

export default WorkRecordModal;

