import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  Card,
  Button,
  Space,
  Tag,
  Descriptions,
  Row,
  Col,
  Avatar,
  Modal,
  message,
  Alert,
  Dropdown,
  Spin,
} from 'antd'
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
  EditOutlined,
  PrinterOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import WorkHistoryList from '../../components/Welders/WorkHistory/WorkHistoryList'
import WorkRecordList from '../../components/Welders/WorkRecords/WorkRecordList'
import TrainingRecordList from '../../components/Welders/TrainingRecords/TrainingRecordList'
import AssessmentRecordList from '../../components/Welders/AssessmentRecords/AssessmentRecordList'
import weldersService, { type Welder } from '@/services/welders'
import { CertificationList } from '@/components/Welders/Certifications'
import certificationService, { type WelderCertification } from '@/services/certifications'
import { workHistoryService, type WelderWorkHistory } from '@/services/welderRecords'
import { workspaceService } from '@/services/workspace'
import ListPageHeader from '@/components/ListPageHeader'

const WeldersDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const [welderData, setWelderData] = useState<Welder | null>(null)
  const [certs, setCerts] = useState<WelderCertification[]>([])
  const [histories, setHistories] = useState<WelderWorkHistory[]>([])
  const [loading, setLoading] = useState(false)

  const workspace = workspaceService.getCurrentWorkspaceFromStorage()

  const loadCertsAndHistory = useCallback(async (welderId: number) => {
    if (!workspace) return
    try {
      const [certRes, histRes] = await Promise.all([
        certificationService.getList(
          welderId,
          workspace.type,
          workspace.company_id,
          workspace.factory_id
        ),
        workHistoryService.getList(welderId, {
          workspace_type: workspace.type,
          company_id: workspace.company_id,
          factory_id: workspace.factory_id,
        }),
      ])
      setCerts(certRes.items || [])
      setHistories(histRes.items || [])
    } catch {
      /* ignore secondary load errors */
    }
  }, [workspace])

  const fetchWelderDetail = async () => {
    if (!id) return
    setLoading(true)
    try {
      const response = await weldersService.getDetail(parseInt(id))
      if (response.success && response.data) {
        setWelderData(response.data)
        await loadCertsAndHistory(response.data.id)
      } else {
        message.error(response.message || '获取焊工详情失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取焊工详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWelderDetail()
  }, [id])

  useEffect(() => {
    if ((location.state as any)?.highlightCerts) {
      message.info('请在下方「持证项目」中按体系添加持证')
    }
  }, [location.state])

  const nearestExpiry = (() => {
    const dates: dayjs.Dayjs[] = []
    certs.forEach((c) => {
      const projects = c.projects || []
      if (projects.length) {
        projects.forEach((p) => {
          if (p.expiry_date) dates.push(dayjs(p.expiry_date))
        })
      } else if (c.expiry_date) {
        dates.push(dayjs(c.expiry_date))
      }
    })
    dates.sort((a, b) => a.valueOf() - b.valueOf())
    return dates[0]
  })()

  const riskCount = certs.reduce((acc, c) => {
    const projects = c.projects || []
    if (projects.length) {
      return (
        acc +
        projects.filter((p) => {
          if (!p.expiry_date) return false
          return dayjs(p.expiry_date).diff(dayjs(), 'day') <= 30
        }).length
      )
    }
    if (!c.expiry_date) return acc
    return acc + (dayjs(c.expiry_date).diff(dayjs(), 'day') <= 30 ? 1 : 0)
  }, 0)

  const systems = Array.from(new Set(certs.map((c) => c.certification_system).filter(Boolean)))

  const maskIdNumber = (idNumber: string) => {
    if (idNumber && idNumber.length >= 10) {
      return `${idNumber.substring(0, 6)}********${idNumber.substring(idNumber.length - 4)}`
    }
    return idNumber
  }

  const maskPhoneNumber = (phone: string) => {
    if (phone && phone.length >= 7) {
      return `${phone.substring(0, 3)}****${phone.substring(phone.length - 4)}`
    }
    return phone
  }

  const handleDelete = () => {
    if (!id) return
    Modal.confirm({
      title: '确定删除该焊工？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后将无法恢复',
      onOk: async () => {
        try {
          await weldersService.delete(parseInt(id))
          message.success('删除成功')
          navigate('/welders')
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败')
        }
      },
    })
  }

  const buildResumePayload = () => {
    if (!welderData) return null
    return {
      welder: {
        welder_code: welderData.welder_code,
        full_name: welderData.full_name,
        phone: welderData.phone,
        department: welderData.department,
        position: welderData.position,
        status: welderData.status,
      },
      certifications: certs.flatMap((c) => {
        const projects = c.projects || []
        if (!projects.length) {
          return [
            {
              system: c.certification_system,
              project: c.project_name || c.certification_type,
              project_code: undefined,
              number: c.certification_number,
              issue_date: c.issue_date,
              expiry_date: c.expiry_date,
              next_renewal_date: c.next_renewal_date,
              status: c.status,
            },
          ]
        }
        return projects.map((p) => ({
          system: c.certification_system,
          project: p.project_name,
          project_code: p.project_code,
          number: c.certification_number,
          issue_date: p.issue_date || c.issue_date,
          expiry_date: p.expiry_date,
          next_renewal_date: p.next_renewal_date,
          status: p.status,
        }))
      }),
      work_histories: histories.map((h) => ({
        company_name: h.company_name,
        position: h.position,
        start_date: h.start_date,
        end_date: h.end_date,
        department: h.department,
        job_description: h.job_description,
      })),
      exported_at: dayjs().toISOString(),
    }
  }

  const handleExportJson = () => {
    const payload = buildResumePayload()
    if (!payload) return
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${welderData?.welder_code || 'welder'}-resume-${dayjs().format('YYYYMMDD')}.json`
    link.click()
    URL.revokeObjectURL(url)
    message.success('已导出履历数据 JSON')
  }

  const handlePrintResume = async () => {
    if (!welderData || !workspace) return
    let latestCerts = certs
    let latestHistories = histories
    try {
      const [certRes, histRes] = await Promise.all([
        certificationService.getList(
          welderData.id,
          workspace.type,
          workspace.company_id,
          workspace.factory_id
        ),
        workHistoryService.getList(welderData.id, {
          workspace_type: workspace.type,
          company_id: workspace.company_id,
          factory_id: workspace.factory_id,
        }),
      ])
      latestCerts = certRes.items || []
      latestHistories = histRes.items || []
      setCerts(latestCerts)
      setHistories(latestHistories)
    } catch {
      /* use cached */
    }
    const certRows = latestCerts
      .flatMap((c) => {
        const projects = c.projects || []
        if (!projects.length) {
          return [
            `<tr>
            <td>${c.certification_system || '-'}</td>
            <td>${c.project_name || c.certification_type || '-'}</td>
            <td>${c.certification_number || '-'}</td>
            <td>${c.issue_date || '-'}</td>
            <td>${c.expiry_date || '-'}</td>
            <td>${c.next_renewal_date || '-'}</td>
          </tr>`,
          ]
        }
        return projects.map(
          (p) =>
            `<tr>
            <td>${c.certification_system || '-'}</td>
            <td>${p.project_name || '-'}</td>
            <td>${c.certification_number || '-'}</td>
            <td>${p.issue_date || c.issue_date || '-'}</td>
            <td>${p.expiry_date || '-'}</td>
            <td>${p.next_renewal_date || '-'}</td>
          </tr>`
        )
      })
      .join('')
    const histRows = latestHistories
      .map(
        (h) =>
          `<tr>
            <td>${h.company_name || '-'}</td>
            <td>${h.position || '-'}</td>
            <td>${h.start_date || '-'}</td>
            <td>${h.end_date || '至今'}</td>
            <td>${h.job_description || '-'}</td>
          </tr>`
      )
      .join('')
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"/><title>焊工履历表-${welderData.full_name}</title>
      <style>
        body{font-family:Segoe UI,Microsoft YaHei,sans-serif;padding:24px;color:#222}
        h1{font-size:22px;margin:0 0 8px}
        h2{font-size:16px;margin:24px 0 8px;border-bottom:1px solid #ddd;padding-bottom:4px}
        table{width:100%;border-collapse:collapse;font-size:12px}
        th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}
        th{background:#f5f5f5}
        .meta{color:#666;font-size:13px;margin-bottom:16px}
      </style></head><body>
      <h1>焊工履历表</h1>
      <div class="meta">${welderData.full_name}（${welderData.welder_code}） · 导出时间 ${dayjs().format('YYYY-MM-DD HH:mm')}</div>
      <h2>一、人员信息</h2>
      <table>
        <tr><th>姓名</th><td>${welderData.full_name}</td><th>编号</th><td>${welderData.welder_code}</td></tr>
        <tr><th>部门</th><td>${welderData.department || '-'}</td><th>岗位</th><td>${welderData.position || '-'}</td></tr>
        <tr><th>电话</th><td>${welderData.phone || '-'}</td><th>状态</th><td>${welderData.status === 'active' ? '在职' : welderData.status}</td></tr>
      </table>
      <h2>二、持证项目（按体系）</h2>
      <table>
        <thead><tr><th>体系</th><th>持证项目</th><th>证书编号</th><th>发证日</th><th>到期日</th><th>下次审证</th></tr></thead>
        <tbody>${certRows || '<tr><td colspan="6">暂无持证</td></tr>'}</tbody>
      </table>
      <h2>三、工作履历</h2>
      <table>
        <thead><tr><th>单位</th><th>职位</th><th>开始</th><th>结束</th><th>工作内容</th></tr></thead>
        <tbody>${histRows || '<tr><td colspan="5">暂无履历</td></tr>'}</tbody>
      </table>
      <script>window.onload=function(){window.print()}</script>
      </body></html>`
    const win = window.open('', '_blank')
    if (!win) {
      message.error('浏览器拦截了打印窗口，请允许弹窗后重试')
      return
    }
    win.document.write(html)
    win.document.close()
  }

  const handleDownloadPdf = async () => {
    if (!welderData || !workspace) return
    try {
      const params = new URLSearchParams({
        workspace_type: workspace.type,
      })
      if (workspace.company_id) params.set('company_id', String(workspace.company_id))
      if (workspace.factory_id) params.set('factory_id', String(workspace.factory_id))
      const token = localStorage.getItem('token')
      const resp = await fetch(
        `/api/v1/welders/${welderData.id}/resume.pdf?${params.toString()}`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      )
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || '下载 PDF 失败')
      }
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `焊工履历表-${welderData.full_name || welderData.welder_code}.pdf`
      link.click()
      URL.revokeObjectURL(url)
      message.success('履历表 PDF 已下载')
    } catch (error: any) {
      message.error(error.message || 'PDF 导出失败，可改用打印履历表')
    }
  }

  if (loading) {
    return (
      <div className="list-page" style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  if (!welderData) {
    return (
      <div className="list-page">
        <Alert message="焊工不存在" type="error" showIcon />
      </div>
    )
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title={`${welderData.full_name} · 焊工详情`}
        description={`编号 ${welderData.welder_code} · 持证按体系管理，履历可打印导出`}
        extra={
          <Space wrap>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/welders')}>
              返回列表
            </Button>
            <Button icon={<EditOutlined />} onClick={() => navigate(`/welders/${welderData.id}/edit`)}>
              编辑人员
            </Button>
            <Dropdown
              menu={{
                items: [
                  { key: 'print', label: '打印履历表', icon: <PrinterOutlined />, onClick: handlePrintResume },
                  { key: 'pdf', label: '下载履历 PDF', icon: <DownloadOutlined />, onClick: () => void handleDownloadPdf() },
                  { key: 'json', label: '导出履历 JSON', icon: <DownloadOutlined />, onClick: handleExportJson },
                ],
              }}
            >
              <Button icon={<DownloadOutlined />}>履历表</Button>
            </Dropdown>
            <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
              删除
            </Button>
          </Space>
        }
      />

      {riskCount > 0 && (
        <Alert
          className="mb-4"
          type={nearestExpiry && nearestExpiry.isBefore(dayjs()) ? 'error' : 'warning'}
          showIcon
          icon={nearestExpiry && nearestExpiry.isBefore(dayjs()) ? <ExclamationCircleOutlined /> : <WarningOutlined />}
          message={`持证风险：${riskCount} 个项目在 30 天内到期或已过期`}
          description={
            nearestExpiry
              ? `最近到期日 ${nearestExpiry.format('YYYY-MM-DD')}（剩余 ${nearestExpiry.diff(dayjs(), 'day')} 天）。请在「持证项目」中处理审证。`
              : undefined
          }
        />
      )}

      {!certs.length && (
        <Alert
          className="mb-4"
          type="info"
          showIcon
          message="尚未添加持证项目"
          description="请在下方按 ASME / 国标等体系添加持证项目，以便列表预警与履历表完整。"
        />
      )}

      <Card className="list-page-card" style={{ marginBottom: 16 }}>
        <Row gutter={[24, 24]}>
          <Col xs={24} md={6} style={{ textAlign: 'center' }}>
            <Avatar size={96} icon={<UserOutlined />} />
            <div style={{ marginTop: 12, fontSize: 18, fontWeight: 600 }}>{welderData.full_name}</div>
            <Tag color="blue">{welderData.welder_code}</Tag>
            <div style={{ marginTop: 8 }}>
              <Tag color={welderData.status === 'active' ? 'success' : 'default'}>
                {welderData.status === 'active' ? '在职' : welderData.status}
              </Tag>
            </div>
          </Col>
          <Col xs={24} md={18}>
            <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="证件号">{maskIdNumber(welderData.id_number || '')}</Descriptions.Item>
              <Descriptions.Item label="电话">{maskPhoneNumber(welderData.phone || '')}</Descriptions.Item>
              <Descriptions.Item label="部门">{welderData.department || '-'}</Descriptions.Item>
              <Descriptions.Item label="岗位">{welderData.position || '-'}</Descriptions.Item>
              <Descriptions.Item label="持证体系" span={2}>
                <Space wrap>
                  {systems.length
                    ? systems.map((s) => (
                        <Tag key={s as string} color="blue">
                          {s as string}
                        </Tag>
                      ))
                    : '暂无'}
                  <Tag icon={<SafetyCertificateOutlined />}>{certs.length} 个持证项目</Tag>
                  {riskCount === 0 && certs.length > 0 && (
                    <Tag color="success" icon={<CheckCircleOutlined />}>
                      持证风险正常
                    </Tag>
                  )}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="最近到期">
                {nearestExpiry ? nearestExpiry.format('YYYY-MM-DD') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="入职/建档">
                {welderData.hire_date
                  ? dayjs(welderData.hire_date).format('YYYY-MM-DD')
                  : dayjs(welderData.created_at).format('YYYY-MM-DD')}
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>
      </Card>

      <Card
        className="list-page-card"
        title={
          <span>
            <SafetyCertificateOutlined /> 持证项目（按体系）
          </span>
        }
        style={{ marginBottom: 16 }}
      >
        <CertificationList welderId={welderData.id} onChanged={() => loadCertsAndHistory(welderData.id)} />
      </Card>

      <div style={{ marginBottom: 16 }}>
        <WorkHistoryList welderId={welderData.id} />
      </div>
      <div style={{ marginBottom: 16 }}>
        <TrainingRecordList welderId={welderData.id} />
      </div>
      <div style={{ marginBottom: 16 }}>
        <AssessmentRecordList welderId={welderData.id} />
      </div>
      <div style={{ marginBottom: 16 }}>
        <WorkRecordList welderId={welderData.id} />
      </div>
    </div>
  )
}

export default WeldersDetail
