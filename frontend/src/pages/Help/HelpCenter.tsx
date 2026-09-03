import React, { useMemo, useState } from 'react'
import { Button, Card, Collapse, Input, Space, Typography } from 'antd'
import { QuestionCircleOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

const topics = [
  {
    key: 'welder',
    label: '焊工管理与证书记审',
    text: '在焊工详情中维护体系证书与持证项目。记审前请核对认证体系、审核基准日和周期；审核日期不得早于上次审核日期。工作履历、培训、考核和焊接操作记录均可从对应卡片新增或编辑。',
  },
  {
    key: 'settings',
    label: '常规设置与到期预警',
    text: '复审周期、基准日和预警档位应按企业采用的标准配置。修改规则前先确认适用体系和证书类型，避免批量影响其他体系记录。',
  },
  {
    key: 'wps',
    label: 'WPS / PQR / pPQR 操作',
    text: '先选择工作区，再创建或导入工艺文件。导出前应补齐编号、模板和必要工艺字段；权限不足时请联系工作区管理员分配对应模块权限。',
  },
  {
    key: 'equipment',
    label: '设备维护与到期提醒',
    text: '新建或编辑设备时填写维护间隔与维护基准日期，系统据此生成下次维护日期。完成维护记录后，下次维护日期会按周期顺延。停用或报废设备不再产生提醒。',
  },
  {
    key: 'troubleshooting',
    label: '常见报错与自查',
    text: '下载失败时先检查浏览器下载权限和网络；空列表时检查当前工作区；保存失败时根据页面提示补齐必填字段。若仍无法解决，请通过反馈入口提交页面、记录编号和发生时间。',
  },
]

const HelpCenter: React.FC = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    return keyword ? topics.filter((item) => `${item.label}${item.text}`.toLowerCase().includes(keyword)) : topics
  }, [query])

  return (
    <div className="page-container">
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}><QuestionCircleOutlined /> 帮助中心</Title>
            <Text type="secondary">焊序 1.0 · 更新日期 2026-09-03</Text>
          </div>
          <Input
            size="large"
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索功能、流程或错误信息"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {filtered.length ? (
            <Collapse
              defaultActiveKey={['welder']}
              items={filtered.map((item) => ({
                key: item.key,
                label: item.label,
                children: <Paragraph style={{ marginBottom: 0 }}>{item.text}</Paragraph>,
              }))}
            />
          ) : (
            <Paragraph>没有匹配的帮助内容。</Paragraph>
          )}
          <Button type="primary" onClick={() => navigate('/feedback')}>反馈问题</Button>
        </Space>
      </Card>
    </div>
  )
}

export default HelpCenter
