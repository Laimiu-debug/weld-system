/**
 * 审批按钮组件
 * 用于在文档详情页显示提交审批、批准、拒绝等操作按钮
 */
import React, { useState } from 'react';
import { Button, Modal, Input, message, Space } from 'antd';
import {
  CheckOutlined,
  CloseOutlined,
  RollbackOutlined,
  SendOutlined,
  StopOutlined,
} from '@ant-design/icons';
import approvalApi from '@/services/approval';

const { TextArea } = Input;

interface ApprovalButtonProps {
  documentType: string;
  documentId: number;
  documentNumber?: string;
  documentTitle?: string;
  instanceId?: number;
  status?: string;
  canApprove?: boolean;
  canSubmit?: boolean;
  canCancel?: boolean;
  onSuccess?: () => void;
  size?: 'small' | 'middle' | 'large';
}

export const ApprovalButton: React.FC<ApprovalButtonProps> = ({
  documentType,
  documentId,
  documentNumber,
  documentTitle,
  instanceId,
  status,
  canApprove = false,
  canSubmit = false,
  canCancel = false,
  onSuccess,
  size = 'middle',
}) => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState<'submit' | 'approve' | 'reject' | 'return' | 'cancel'>('submit');
  const [comment, setComment] = useState('');

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await approvalApi.submitForApproval({
        document_type: documentType,
        document_ids: [documentId],
        notes: comment,
      });
      message.success('提交审批成功');
      setModalVisible(false);
      setComment('');
      onSuccess?.();
    } catch (error: any) {
      message.error(error.message || '提交审批失败');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!instanceId) return;
    setLoading(true);
    try {
      await approvalApi.approve(instanceId, {
        action: 'approve',
        comment,
        attachments: []
      });
      message.success('审批通过');
      setModalVisible(false);
      setComment('');
      onSuccess?.();
    } catch (error: any) {
      message.error(error.message || '审批失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!instanceId) return;
    setLoading(true);
    try {
      await approvalApi.reject(instanceId, {
        action: 'reject',
        comment,
        attachments: []
      });
      message.success('已拒绝');
      setModalVisible(false);
      setComment('');
      onSuccess?.();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReturn = async () => {
    if (!instanceId) return;
    setLoading(true);
    try {
      await approvalApi.return(instanceId, {
        action: 'return',
        comment,
        attachments: []
      });
      message.success('已退回');
      setModalVisible(false);
      setComment('');
      onSuccess?.();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!instanceId) return;
    setLoading(true);
    try {
      await approvalApi.cancel(instanceId, comment);
      message.success('已取消审批');
      setModalVisible(false);
      setComment('');
      onSuccess?.();
    } catch (error: any) {
      message.error(error.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const openModal = (type: typeof modalType) => {
    setModalType(type);
    setModalVisible(true);
  };

  const handleModalOk = () => {
    switch (modalType) {
      case 'submit':
        handleSubmit();
        break;
      case 'approve':
        handleApprove();
        break;
      case 'reject':
        handleReject();
        break;
      case 'return':
        handleReturn();
        break;
      case 'cancel':
        handleCancel();
        break;
    }
  };

  const getModalTitle = () => {
    switch (modalType) {
      case 'submit':
        return '提交审批';
      case 'approve':
        return '批准文档';
      case 'reject':
        return '拒绝文档';
      case 'return':
        return '退回文档';
      case 'cancel':
        return '取消审批';
      default:
        return '';
    }
  };

  const getCommentLabel = () => {
    switch (modalType) {
      case 'submit':
        return '备注（可选）';
      case 'approve':
        return '审批意见';
      case 'reject':
        return '拒绝原因';
      case 'return':
        return '退回原因';
      case 'cancel':
        return '取消原因';
      default:
        return '备注';
    }
  };

  // 判断是否可以重新提交（被拒绝或退回状态）
  const canResubmit = status === 'rejected' || status === 'returned';

  // 判断是否可以取消审批（待审批、审批中、已拒绝、已退回状态都可以取消，已批准不能取消）
  const showCancelButton = canCancel && status !== 'approved';

  return (
    <>
      <Space>
        {canSubmit && !canResubmit && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            size={size}
            onClick={() => openModal('submit')}
          >
            提交审批
          </Button>
        )}

        {canResubmit && (
          <Button
            type="primary"
            icon={<SendOutlined />}
            size={size}
            onClick={() => openModal('submit')}
          >
            重新提交
          </Button>
        )}

        {canApprove && (
          <>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              size={size}
              onClick={() => openModal('approve')}
            >
              批准
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              size={size}
              onClick={() => openModal('reject')}
            >
              拒绝
            </Button>
            <Button
              icon={<RollbackOutlined />}
              size={size}
              onClick={() => openModal('return')}
            >
              退回
            </Button>
          </>
        )}

        {showCancelButton && (
          <Button
            icon={<StopOutlined />}
            size={size}
            onClick={() => openModal('cancel')}
          >
            取消审批
          </Button>
        )}
      </Space>

      <Modal
        title={getModalTitle()}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setModalVisible(false);
          setComment('');
        }}
        confirmLoading={loading}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <p>文档：{documentTitle || `${documentType}-${documentId}`}</p>
        </div>
        <TextArea
          rows={4}
          placeholder={`请输入${getCommentLabel()}`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          required={modalType !== 'submit' && modalType !== 'approve'}
        />
      </Modal>
    </>
  );
};

export default ApprovalButton;

