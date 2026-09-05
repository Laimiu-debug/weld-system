import { Alert, Modal, Select, Table, Tag, Typography } from 'antd'
import type { WelderImportReview } from '@/services/smartImport'
const { Text } = Typography
interface Props {
  review: WelderImportReview | null
  choices: Record<string, number | 'new'>
  publishing: boolean
  onCancel: () => void
  onPublish: () => void
  onChoice: (key: string, value: number | 'new') => void
}
export default function WelderReviewModal({ review, choices, publishing, onCancel, onPublish, onChoice }: Props) {
  return (
      <Modal
        title="焊工、证书与持证项目审核"
        open={Boolean(review)}
        onCancel={() => !publishing && onCancel()}
        onOk={onPublish}
        confirmLoading={publishing}
        okText="确认导入现有焊工库"
        width="min(1200px, 96vw)"
      >
        <Alert
          type="info"
          showIcon
          message="编号或身份证件优先匹配；只有姓名相同的记录必须人工确认"
          description="重复证书默认跳过；有效期更晚的同号证书按续证更新。每个持证项目会单独保存到期状态。"
          style={{ marginBottom: 16 }}
        />
        <Table
          rowKey="record_key"
          dataSource={review?.records || []}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1050 }}
          columns={[
            { title: '姓名 / 编号', width: 180, render: (_, item) => <><Text strong>{item.full_name || '未识别姓名'}</Text><br /><Text type="secondary">{item.welder_code || item.id_number || '无身份编号'}</Text></> },
            { title: '身份处理', width: 250, render: (_, item) => (
              <Select
                value={choices[item.record_key]}
                placeholder="请选择对应焊工"
                style={{ width: '100%' }}
                onChange={value => onChoice(item.record_key, value)}
                options={[
                  ...item.candidates.map(candidate => ({ value: candidate.id, label: `${candidate.full_name} · ${candidate.welder_code}` })),
                  { value: 'new', label: '确认新建焊工' },
                ]}
              />
            ) },
            { title: '证书号', dataIndex: 'certification_number', width: 170, render: value => value || '未识别' },
            { title: '证书判断', width: 120, render: (_, item) => {
              const config = { new: ['blue', '新证书'], duplicate: ['default', '重复·跳过'], renewal: ['green', '续证更新'], conflict: ['red', '归属冲突'] }[item.certificate_status]
              return <Tag color={config[0]}>{config[1]}</Tag>
            } },
            { title: '有效期', width: 110, render: (_, item) => {
              const config = { valid: ['success', '有效'], expiring_soon: ['warning', '即将到期'], expired: ['error', '已过期'] }[item.expiry_status]
              return <Tag color={config[0]}>{config[1]}</Tag>
            } },
            { title: '持证项目', width: 100, render: (_, item) => `${item.qualified_projects.length} 项` },
          ]}
        />
      </Modal>
  )
}
