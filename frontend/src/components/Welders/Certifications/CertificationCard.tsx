/**
 * 焊工证书卡片组件
 * 突出显示认证项目和合格范围信息
 */
import React from 'react';
import { Card, Tag, Space, Button, Descriptions, Badge, Tooltip, Popconfirm, Table } from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { WelderCertification, QualifiedItem, QualifiedRangeItem } from '../../../services/certifications';

interface CertificationCardProps {
  certification: WelderCertification;
  onEdit: (certification: WelderCertification) => void;
  onDelete: (certificationId: number) => void;
  onViewDetails?: (certification: WelderCertification) => void;
}

/**
 * 证书卡片组件
 */
const CertificationCard: React.FC<CertificationCardProps> = ({
  certification,
  onEdit,
  onDelete,
  onViewDetails,
}) => {
  // 获取证书状态标签
  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { status: any; text: string; icon: React.ReactNode }> = {
      valid: {
        status: 'success',
        text: '有效',
        icon: <CheckCircleOutlined />,
      },
      expiring_soon: {
        status: 'warning',
        text: '即将过期',
        icon: <ClockCircleOutlined />,
      },
      expired: {
        status: 'error',
        text: '已过期',
        icon: <ExclamationCircleOutlined />,
      },
      suspended: {
        status: 'default',
        text: '已暂停',
        icon: <CloseCircleOutlined />,
      },
      revoked: {
        status: 'error',
        text: '已吊销',
        icon: <CloseCircleOutlined />,
      },
    };

    const config = statusMap[status] || statusMap.valid;
    return (
      <Badge status={config.status} text={
        <span>
          {config.icon} {config.text}
        </span>
      } />
    );
  };

  // 获取认证体系颜色
  const getSystemColor = (system?: string) => {
    const colorMap: Record<string, string> = {
      'ASME': 'blue',
      '国标': 'green',
      '欧标': 'purple',
      'AWS': 'orange',
      'API': 'cyan',
      'DNV': 'geekblue',
    };
    return colorMap[system || ''] || 'default';
  };

  // 格式化日期
  const formatDate = (date?: string) => {
    return date ? dayjs(date).format('YYYY-MM-DD') : '-';
  };

  // 计算剩余天数
  const getDaysRemaining = (expiryDate?: string) => {
    if (!expiryDate) return null;
    const days = dayjs(expiryDate).diff(dayjs(), 'day');
    return days;
  };

  const daysRemaining = getDaysRemaining(certification.expiry_date);

  // 解析合格项目 JSON
  const parseQualifiedItems = (): QualifiedItem[] => {
    try {
      if (!certification.qualified_items) return [];
      return JSON.parse(certification.qualified_items);
    } catch (e) {
      console.error('解析合格项目失败:', e);
      return [];
    }
  };

  // 解析合格范围 JSON
  const parseQualifiedRange = (): QualifiedRangeItem[] => {
    try {
      if (!certification.qualified_range) return [];
      return JSON.parse(certification.qualified_range);
    } catch (e) {
      console.error('解析合格范围失败:', e);
      return [];
    }
  };

  const qualifiedItems = parseQualifiedItems();
  const qualifiedRange = parseQualifiedRange();

  return (
    <Card
      size="small"
      title={
        <Space>
          <FileTextOutlined />
          <span>{certification.certification_type}</span>
          {certification.is_primary && <Tag color="gold">主要证书</Tag>}
          {certification.certification_system && (
            <Tag color={getSystemColor(certification.certification_system)}>
              {certification.certification_system}
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => onEdit(certification)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个证书吗？"
            onConfirm={() => onDelete(certification.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      }
      style={{ marginBottom: 16 }}
    >
      <Descriptions column={2} size="small">
        {/* 证书编号 */}
        <Descriptions.Item label="证书编号" span={2}>
          <strong>{certification.certification_number}</strong>
        </Descriptions.Item>

        {/* 认证标准 */}
        {certification.certification_standard && (
          <Descriptions.Item label="认证标准" span={2}>
            <Tag>{certification.certification_standard}</Tag>
          </Descriptions.Item>
        )}

        {/* 项目名称 */}
        {certification.project_name && (
          <Descriptions.Item label="项目名称" span={2}>
            {certification.project_name}
          </Descriptions.Item>
        )}

        {/* 合格项目 - 突出显示 */}
        {qualifiedItems.length > 0 && (
          <Descriptions.Item label={<strong style={{ color: '#1890ff' }}>合格项目</strong>} span={2}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {qualifiedItems.map((item, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <Tag color="blue">{item.item}</Tag>
                  {item.description && <span style={{ marginLeft: 8, color: '#666' }}>{item.description}</span>}
                  {item.notes && <span style={{ marginLeft: 8, fontSize: '12px', color: '#999' }}>({item.notes})</span>}
                </div>
              ))}
            </Space>
          </Descriptions.Item>
        )}

        {/* 合格范围 - 突出显示 */}
        {qualifiedRange.length > 0 && (
          <Descriptions.Item label={<strong style={{ color: '#1890ff' }}>合格范围</strong>} span={2}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {qualifiedRange.map((range, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <strong>{range.name}:</strong> <Tag color="green">{range.value}</Tag>
                  {range.notes && <span style={{ marginLeft: 8, fontSize: '12px', color: '#999' }}>({range.notes})</span>}
                </div>
              ))}
            </Space>
          </Descriptions.Item>
        )}

        {/* 颁发信息 */}
        <Descriptions.Item label="颁发机构">
          {certification.issuing_authority}
        </Descriptions.Item>
        <Descriptions.Item label="颁发日期">
          {formatDate(certification.issue_date)}
        </Descriptions.Item>

        {/* 有效期 */}
        <Descriptions.Item label="有效期至">
          {certification.expiry_date ? (
            <Space>
              <span>{formatDate(certification.expiry_date)}</span>
              {daysRemaining !== null && daysRemaining > 0 && daysRemaining <= 90 && (
                <Tooltip title={`还有 ${daysRemaining} 天过期`}>
                  <Tag color="warning">即将过期</Tag>
                </Tooltip>
              )}
              {daysRemaining !== null && daysRemaining <= 0 && (
                <Tag color="error">已过期</Tag>
              )}
            </Space>
          ) : '长期有效'}
        </Descriptions.Item>

        {/* 证书状态 */}
        <Descriptions.Item label="状态">
          {getStatusBadge(certification.status)}
        </Descriptions.Item>

        {/* 复审信息 */}
        {certification.renewal_date && (
          <>
            <Descriptions.Item label="最近复审">
              {formatDate(certification.renewal_date)}
            </Descriptions.Item>
            <Descriptions.Item label="复审次数">
              {certification.renewal_count || 0} 次
            </Descriptions.Item>
          </>
        )}

        {certification.next_renewal_date && (
          <Descriptions.Item label="下次复审" span={2}>
            <Space>
              <span>{formatDate(certification.next_renewal_date)}</span>
              {certification.renewal_result && (
                <Tag color={certification.renewal_result === '通过' ? 'success' : 'error'}>
                  {certification.renewal_result}
                </Tag>
              )}
            </Space>
          </Descriptions.Item>
        )}

        {/* 备注 */}
        {certification.notes && (
          <Descriptions.Item label="备注" span={2}>
            {certification.notes}
          </Descriptions.Item>
        )}
      </Descriptions>

      {/* 查看详情按钮 */}
      {onViewDetails && (
        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <Button
            type="link"
            size="small"
            onClick={() => onViewDetails(certification)}
          >
            查看完整信息
          </Button>
        </div>
      )}
    </Card>
  );
};

export default CertificationCard;

