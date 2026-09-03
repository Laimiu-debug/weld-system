/**
 * 体系证书卡片：展示证书信息 + 下属持证项目
 */
import React from 'react'
import { Card, Tag, Space, Button, Descriptions, Badge, Popconfirm, List, Typography } from 'antd'
import {
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  StarOutlined,
  AuditOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type {
  WelderCertification,
  CertifiedProject,
  QualifiedItem,
  QualifiedRangeItem,
} from '../../../services/certifications'

const { Text } = Typography

interface CertificationCardProps {
  certification: WelderCertification
  onEdit: (certification: WelderCertification) => void
  onDelete: (certificationId: number) => void
  onSetPrimary?: (certification: WelderCertification) => void
  onAddProject?: (certification: WelderCertification) => void
  onEditProject?: (certification: WelderCertification, project: CertifiedProject) => void
  onDeleteProject?: (certification: WelderCertification, project: CertifiedProject) => void
  onRenewProject?: (certification: WelderCertification, project: CertifiedProject) => void
}

const CertificationCard: React.FC<CertificationCardProps> = ({
  certification,
  onEdit,
  onDelete,
  onSetPrimary,
  onAddProject,
  onEditProject,
  onDeleteProject,
  onRenewProject,
}) => {
  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { status: any; text: string; icon: React.ReactNode }> = {
      valid: { status: 'success', text: '有效', icon: <CheckCircleOutlined /> },
      expiring_soon: { status: 'warning', text: '即将过期', icon: <ClockCircleOutlined /> },
      expired: { status: 'error', text: '已过期', icon: <ExclamationCircleOutlined /> },
      suspended: { status: 'default', text: '已暂停', icon: <CloseCircleOutlined /> },
      revoked: { status: 'error', text: '已吊销', icon: <CloseCircleOutlined /> },
    }
    const config = statusMap[status] || statusMap.valid
    return (
      <Badge
        status={config.status}
        text={
          <span>
            {config.icon} {config.text}
          </span>
        }
      />
    )
  }

  const getSystemColor = (system?: string) => {
    const colorMap: Record<string, string> = {
      ASME: 'blue',
      国标: 'green',
      欧标: 'purple',
      AWS: 'orange',
      API: 'cyan',
      DNV: 'geekblue',
    }
    return colorMap[system || ''] || 'default'
  }

  const formatDate = (date?: string) => (date ? dayjs(date).format('YYYY-MM-DD') : '-')

  const parseQualifiedItems = (): QualifiedItem[] => {
    try {
      if (!certification.qualified_items) return []
      return JSON.parse(certification.qualified_items)
    } catch {
      return []
    }
  }

  const parseQualifiedRange = (): QualifiedRangeItem[] => {
    try {
      if (!certification.qualified_range) return []
      return JSON.parse(certification.qualified_range)
    } catch {
      return []
    }
  }

  const projects = certification.projects || []
  const qualifiedItems = parseQualifiedItems()
  const qualifiedRange = parseQualifiedRange()

  return (
    <Card
      size="small"
      title={
        <Space wrap>
          <FileTextOutlined />
          <span>
            {certification.certification_system || '体系证书'} ·{' '}
            {certification.certification_number}
          </span>
          {certification.is_primary && <Tag color="gold">主要</Tag>}
          {certification.certification_system && (
            <Tag color={getSystemColor(certification.certification_system)}>
              {certification.certification_system}
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space wrap size={0}>
          {onSetPrimary && !certification.is_primary && (
            <Button
              type="link"
              size="small"
              icon={<StarOutlined />}
              onClick={() => onSetPrimary(certification)}
            >
              设为主要
            </Button>
          )}
          {onAddProject && (
            <Button
              type="link"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => onAddProject(certification)}
            >
              加持证项目
            </Button>
          )}
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => onEdit(certification)}>
            编辑证书
          </Button>
          <Popconfirm
            title="确定删除该体系证书及其持证项目？"
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
        <Descriptions.Item label="证书编号" span={2}>
          <strong>{certification.certification_number}</strong>
        </Descriptions.Item>
        <Descriptions.Item label="证书类型">{certification.certification_type}</Descriptions.Item>
        <Descriptions.Item label="发证机构">
          {certification.issuing_authority || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="发证日">{formatDate(certification.issue_date)}</Descriptions.Item>
        <Descriptions.Item label="状态">
          {getStatusBadge(certification.status || 'valid')}
        </Descriptions.Item>
      </Descriptions>

      <div style={{ marginTop: 12 }}>
        <Space style={{ marginBottom: 8 }}>
          <Text strong>持证项目</Text>
          <Tag>{projects.length} 项</Tag>
        </Space>
        {projects.length === 0 ? (
          <Text type="secondary">暂无持证项目，请点击「加持证项目」</Text>
        ) : (
          <List
            size="small"
            bordered
            dataSource={projects}
            renderItem={(p) => {
              const days = p.expiry_date ? dayjs(p.expiry_date).diff(dayjs(), 'day') : null
              return (
                <List.Item
                  actions={[
                    onRenewProject ? (
                      <Button key="renew" type="link" size="small" icon={<AuditOutlined />} onClick={() => onRenewProject(certification, p)}>
                        记审证
                      </Button>
                    ) : null,
                    onEditProject ? (
                      <Button
                        key="edit"
                        type="link"
                        size="small"
                        onClick={() => onEditProject(certification, p)}
                      >
                        编辑
                      </Button>
                    ) : null,
                    onDeleteProject ? (
                      <Popconfirm
                        key="del"
                        title="删除该持证项目？"
                        onConfirm={() => onDeleteProject(certification, p)}
                      >
                        <Button type="link" size="small" danger>
                          删除
                        </Button>
                      </Popconfirm>
                    ) : null,
                  ].filter(Boolean)}
                >
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <span>{p.project_name}</span>
                        {p.project_code && <Tag>{p.project_code}</Tag>}
                        {getStatusBadge(p.status || 'valid')}
                      </Space>
                    }
                    description={
                      <span>
                        到期 {formatDate(p.expiry_date)}
                        {days !== null && (
                          <Text type={days <= 30 ? 'danger' : 'secondary'}>
                            {' '}
                            · 剩余 {days} 天
                          </Text>
                        )}
                        {p.next_renewal_date && ` · 下次审证 ${formatDate(p.next_renewal_date)}`}
                      </span>
                    }
                  />
                </List.Item>
              )
            }}
          />
        )}
      </div>

      {qualifiedItems.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">合格项目（兼容）</Text>
          <div style={{ marginTop: 4 }}>
            {qualifiedItems.map((item, index) => (
              <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
                {item.item}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {qualifiedRange.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">合格范围（兼容）</Text>
          <div style={{ marginTop: 4 }}>
            {qualifiedRange.map((item, index) => (
              <Tag key={index} style={{ marginBottom: 4 }}>
                {item.name}: {item.value}
              </Tag>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

export default CertificationCard
