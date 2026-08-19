/**
 * 焊工证书添加/编辑模态框
 */
import React, { useEffect, useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Row,
  Col,
  Divider,
  Tabs,
  message,
} from 'antd';
import dayjs from 'dayjs';
import EditableTable, { type EditableTableRow } from './EditableTable';
import AttachmentUpload from './AttachmentUpload';
import type {
  WelderCertification,
  CreateCertificationRequest,
  QualifiedItem,
  QualifiedRangeItem,
  AttachmentItem,
} from '../../../services/certifications';

const { Option } = Select;
const { TextArea } = Input;

interface CertificationModalProps {
  visible: boolean;
  certification?: WelderCertification;
  onOk: (values: CreateCertificationRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

/**
 * 证书表单模态框组件
 */
const CertificationModal: React.FC<CertificationModalProps> = ({
  visible,
  certification,
  onOk,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();
  const isEdit = !!certification;

  // 合格项目表格数据
  const [qualifiedItems, setQualifiedItems] = useState<EditableTableRow[]>([]);

  // 合格范围表格数据
  const [qualifiedRange, setQualifiedRange] = useState<EditableTableRow[]>([]);

  // 附件列表
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);

  // 初始化表单数据
  useEffect(() => {
    if (visible && certification) {
      // 解析合格项目
      try {
        const items = certification.qualified_items
          ? JSON.parse(certification.qualified_items)
          : [];
        setQualifiedItems(
          items.map((item: QualifiedItem, index: number) => ({
            key: `item_${index}`,
            ...item,
          }))
        );
      } catch (e) {
        setQualifiedItems([]);
      }

      // 解析合格范围
      try {
        const range = certification.qualified_range
          ? JSON.parse(certification.qualified_range)
          : [];
        setQualifiedRange(
          range.map((item: QualifiedRangeItem, index: number) => ({
            key: `range_${index}`,
            ...item,
          }))
        );
      } catch (e) {
        setQualifiedRange([]);
      }

      // 解析附件
      try {
        const files = certification.attachments
          ? JSON.parse(certification.attachments)
          : [];
        setAttachments(files);
      } catch (e) {
        setAttachments([]);
      }

      // 设置表单值
      form.setFieldsValue({
        ...certification,
        issue_date: certification.issue_date ? dayjs(certification.issue_date) : null,
        expiry_date: certification.expiry_date ? dayjs(certification.expiry_date) : null,
        exam_date: certification.exam_date ? dayjs(certification.exam_date) : null,
        renewal_date: certification.renewal_date ? dayjs(certification.renewal_date) : null,
        next_renewal_date: certification.next_renewal_date ? dayjs(certification.next_renewal_date) : null,
      });
    } else if (visible) {
      // 新建时重置
      form.resetFields();
      setQualifiedItems([]);
      setQualifiedRange([]);
      setAttachments([]);
    }
  }, [visible, certification, form]);

  // 提交表单
  const handleOk = async () => {
    try {
      const values = await form.validateFields();

      // 转换日期格式 - 只包含有值的字段
      const formattedValues: any = {};

      // 复制所有非日期、非undefined的字段
      Object.keys(values).forEach(key => {
        const value = values[key];
        // 跳过日期字段（稍后单独处理）和 undefined 值
        if (!['issue_date', 'expiry_date', 'exam_date', 'renewal_date', 'next_renewal_date'].includes(key)
            && value !== undefined) {
          formattedValues[key] = value;
        }
      });

      // 处理日期字段 - 只有当日期存在时才添加到对象中
      if (values.issue_date) {
        formattedValues.issue_date = values.issue_date.format('YYYY-MM-DD');
      }
      if (values.expiry_date) {
        formattedValues.expiry_date = values.expiry_date.format('YYYY-MM-DD');
      }
      if (values.exam_date) {
        formattedValues.exam_date = values.exam_date.format('YYYY-MM-DD');
      }
      if (values.renewal_date) {
        formattedValues.renewal_date = values.renewal_date.format('YYYY-MM-DD');
      }
      if (values.next_renewal_date) {
        formattedValues.next_renewal_date = values.next_renewal_date.format('YYYY-MM-DD');
      }

      // 转换表格数据为JSON字符串
      formattedValues.qualified_items = JSON.stringify(
        qualifiedItems.map(({ key, ...rest }) => rest)
      );
      formattedValues.qualified_range = JSON.stringify(
        qualifiedRange.map(({ key, ...rest }) => rest)
      );
      formattedValues.attachments = JSON.stringify(attachments);

      await onOk(formattedValues);
    } catch (error: any) {
      console.error('表单验证失败:', error);
      // 显示验证错误信息
      if (error.errorFields && error.errorFields.length > 0) {
        const firstError = error.errorFields[0];
        message.error(firstError.errors[0] || '请检查表单填写是否完整');
      }
    }
  };

  // 合格项目表格列定义
  const qualifiedItemsColumns = [
    {
      title: '合格项目代号',
      dataIndex: 'item',
      width: '40%',
      placeholder: '如：GTAW-FeIV-6G-3/159-FefS-02/10/12',
    },
    {
      title: '描述',
      dataIndex: 'description',
      width: '35%',
      placeholder: '如：氩弧焊-碳钢-全位置',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      width: '25%',
      placeholder: '备注信息',
    },
  ];

  // 合格范围表格列定义
  const qualifiedRangeColumns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      width: '30%',
      placeholder: '如：母材、焊接位置、厚度范围',
    },
    {
      title: '范围值',
      dataIndex: 'value',
      width: '45%',
      placeholder: '如：Q345R、1G,2G,3G、3-12mm',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      width: '25%',
      placeholder: '备注信息',
    },
  ];

  return (
    <Modal
      title={isEdit ? '编辑证书' : '添加证书'}
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      width={1000}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        preserve={false}
      >
        <Tabs
          defaultActiveKey="basic"
          items={[
            {
              key: 'basic',
              label: '基本信息',
              children: (
                <>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="certification_number"
                        label="证书编号"
                        rules={[{ required: true, message: '请输入证书编号' }]}
                      >
                        <Input placeholder="请输入证书编号" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="certification_type"
                        label="证书类型"
                        rules={[{ required: true, message: '请选择证书类型' }]}
                      >
                        <Select placeholder="请选择证书类型">
                          <Option value="焊工等级证书">焊工等级证书</Option>
                          <Option value="特种焊接技术证书">特种焊接技术证书</Option>
                          <Option value="国际认证">国际认证</Option>
                          <Option value="行业认证">行业认证</Option>
                          <Option value="其他">其他</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="certification_system" label="认证体系">
                        <Select placeholder="请选择认证体系">
                          <Option value="ASME">ASME（美国机械工程师协会）</Option>
                          <Option value="国标">国标（GB/T）</Option>
                          <Option value="欧标">欧标（EN ISO）</Option>
                          <Option value="AWS">AWS（美国焊接学会）</Option>
                          <Option value="API">API（美国石油学会）</Option>
                          <Option value="DNV">DNV（挪威船级社）</Option>
                          <Option value="其他">其他</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="certification_standard" label="认证标准">
                        <Input placeholder="如：ASME IX, EN ISO 9606-1" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="certification_level" label="证书等级">
                        <Input placeholder="请输入证书等级" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="project_name" label="项目名称">
                        <Input placeholder="请输入项目名称" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider>颁发信息</Divider>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="issuing_authority"
                        label="颁发机构"
                      >
                        <Input placeholder="请输入颁发机构" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="issuing_country" label="颁发国家">
                        <Input placeholder="请输入颁发国家" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="issue_date"
                        label="颁发日期"
                      >
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="expiry_date" label="有效期至">
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              ),
            },
            {
              key: 'qualified',
              label: '合格项目与范围',
              children: (
                <>
                  <Divider orientation="left">合格项目</Divider>
                  <p style={{ color: '#999', marginBottom: 16 }}>
                    请输入完整的合格项目代号，如：GTAW-FeIV-6G-3/159-FefS-02/10/12
                  </p>
                  <EditableTable
                    columns={qualifiedItemsColumns}
                    value={qualifiedItems}
                    onChange={setQualifiedItems}
                    addButtonText="添加合格项目"
                    emptyRow={{ item: '', description: '', notes: '' }}
                  />

                  <Divider orientation="left" style={{ marginTop: 24 }}>合格范围</Divider>
                  <p style={{ color: '#999', marginBottom: 16 }}>
                    请输入合格范围信息，如母材、焊接位置、厚度范围、直径范围等
                  </p>
                  <EditableTable
                    columns={qualifiedRangeColumns}
                    value={qualifiedRange}
                    onChange={setQualifiedRange}
                    addButtonText="添加合格范围"
                    emptyRow={{ name: '', value: '', notes: '' }}
                  />
                </>
              ),
            },
            {
              key: 'exam',
              label: '考试信息',
              children: (
                <>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="exam_date" label="考试日期">
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="exam_location" label="考试地点">
                        <Input placeholder="请输入考试地点" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item name="exam_score" label="考试成绩">
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0}
                          max={100}
                          placeholder="请输入考试成绩"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="practical_test_result" label="实操测试结果">
                        <Select placeholder="请选择">
                          <Option value="通过">通过</Option>
                          <Option value="不通过">不通过</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name="theory_test_result" label="理论测试结果">
                        <Select placeholder="请选择">
                          <Option value="通过">通过</Option>
                          <Option value="不通过">不通过</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              ),
            },
            {
              key: 'renewal',
              label: '复审信息',
              children: (
                <>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="renewal_date" label="最近复审日期">
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="next_renewal_date" label="下次复审日期">
                        <DatePicker style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="renewal_count" label="复审次数">
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0}
                          placeholder="请输入复审次数"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="renewal_result" label="复审结果">
                        <Select placeholder="请选择复审结果">
                          <Option value="通过">通过</Option>
                          <Option value="不通过">不通过</Option>
                          <Option value="待复审">待复审</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item name="renewal_notes" label="复审备注">
                    <TextArea rows={4} placeholder="请输入复审备注" />
                  </Form.Item>
                </>
              ),
            },
            {
              key: 'attachments',
              label: '证书附件',
              children: (
                <>
                  <p style={{ color: '#999', marginBottom: 16 }}>
                    请上传证书扫描件或照片，支持 PDF、JPG、PNG 格式
                  </p>
                  <AttachmentUpload
                    value={attachments}
                    onChange={setAttachments}
                    maxCount={5}
                  />
                </>
              ),
            },
            {
              key: 'notes',
              label: '备注',
              children: (
                <Form.Item name="notes" label="备注信息">
                  <TextArea rows={6} placeholder="请输入备注信息" />
                </Form.Item>
              ),
            },
          ]}
        />
      </Form>
    </Modal>
  );
};

export default CertificationModal;


