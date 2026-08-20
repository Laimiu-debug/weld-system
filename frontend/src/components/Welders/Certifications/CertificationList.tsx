/**
 * 焊工持证：按认证体系分组；证书下挂持证项目
 */
import React, { useState, useEffect, useMemo } from 'react'
import {
  Button,
  Space,
  Empty,
  Spin,
  message,
  Select,
  Input,
  Collapse,
  Tag,
  Badge,
} from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import CertificationCard from './CertificationCard'
import CertificationModal from './CertificationModal'
import CertifiedProjectModal from './CertifiedProjectModal'
import certificationService, {
  type WelderCertification,
  type CertifiedProject,
  type CreateCertificationRequest,
  type CreateCertifiedProjectRequest,
} from '../../../services/certifications'
import { workspaceService } from '../../../services/workspace'

const { Option } = Select

interface CertificationListProps {
  welderId: number
  onChanged?: () => void
}

const SYSTEM_ORDER = ['ASME', '国标', '欧标', 'AWS', 'API', 'DNV', '其他']

const CertificationList: React.FC<CertificationListProps> = ({ welderId, onChanged }) => {
  const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
  const [certifications, setCertifications] = useState<WelderCertification[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingCertification, setEditingCertification] = useState<WelderCertification | undefined>()
  const [submitting, setSubmitting] = useState(false)
  const [filterSystem, setFilterSystem] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [searchText, setSearchText] = useState('')

  const [projectModalVisible, setProjectModalVisible] = useState(false)
  const [projectParent, setProjectParent] = useState<WelderCertification | null>(null)
  const [editingProject, setEditingProject] = useState<CertifiedProject | null>(null)
  const [projectSubmitting, setProjectSubmitting] = useState(false)

  const loadCertifications = async () => {
    if (!currentWorkspace) return
    setLoading(true)
    try {
      const response = await certificationService.getList(
        welderId,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      )
      setCertifications(response.items || [])
    } catch (error: any) {
      message.error(error.message || '加载持证失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCertifications()
  }, [welderId])

  const notifyChanged = () => {
    loadCertifications()
    onChanged?.()
  }

  const handleAdd = () => {
    setEditingCertification(undefined)
    setModalVisible(true)
  }

  const handleEdit = (certification: WelderCertification) => {
    setEditingCertification(certification)
    setModalVisible(true)
  }

  const handleDelete = async (certificationId: number) => {
    if (!currentWorkspace) return
    try {
      await certificationService.delete(
        welderId,
        certificationId,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      )
      message.success('体系证书已删除')
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '删除失败')
    }
  }

  const handleSetPrimary = async (cert: WelderCertification) => {
    if (!currentWorkspace) return
    try {
      await certificationService.update(
        welderId,
        cert.id,
        { is_primary: true } as any,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      )
      message.success('已设为主要持证（列表摘要已更新）')
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '设置失败')
    }
  }

  const handleSubmit = async (values: CreateCertificationRequest) => {
    if (!currentWorkspace) return
    setSubmitting(true)
    try {
      if (editingCertification) {
        await certificationService.update(
          welderId,
          editingCertification.id,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        )
        message.success('体系证书已更新')
      } else {
        await certificationService.create(
          welderId,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        )
        message.success('已添加体系证书（含首个持证项目）')
      }
      setModalVisible(false)
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  const openAddProject = (cert: WelderCertification) => {
    setProjectParent(cert)
    setEditingProject(null)
    setProjectModalVisible(true)
  }

  const openEditProject = (cert: WelderCertification, project: CertifiedProject) => {
    setProjectParent(cert)
    setEditingProject(project)
    setProjectModalVisible(true)
  }

  const handleProjectSubmit = async (values: CreateCertifiedProjectRequest) => {
    if (!currentWorkspace || !projectParent) return
    setProjectSubmitting(true)
    try {
      if (editingProject) {
        await certificationService.updateProject(
          welderId,
          projectParent.id,
          editingProject.id,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        )
        message.success('持证项目已更新')
      } else {
        await certificationService.createProject(
          welderId,
          projectParent.id,
          values,
          currentWorkspace.type,
          currentWorkspace.company_id,
          currentWorkspace.factory_id
        )
        message.success('持证项目已添加')
      }
      setProjectModalVisible(false)
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '操作失败')
    } finally {
      setProjectSubmitting(false)
    }
  }

  const handleDeleteProject = async (cert: WelderCertification, project: CertifiedProject) => {
    if (!currentWorkspace) return
    try {
      await certificationService.deleteProject(
        welderId,
        cert.id,
        project.id,
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      )
      message.success('持证项目已删除')
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '删除失败')
    }
  }

  const handleRenewProject = async (cert: WelderCertification, project: CertifiedProject) => {
    if (!currentWorkspace) return
    try {
      const today = dayjs()
      const nextExpiry = project.expiry_date
        ? dayjs(project.expiry_date).add(1, 'year')
        : today.add(1, 'year')
      await certificationService.updateProject(
        welderId,
        cert.id,
        project.id,
        {
          renewal_date: today.format('YYYY-MM-DD'),
          renewal_count: (project.renewal_count || 0) + 1,
          next_renewal_date: today.add(1, 'year').format('YYYY-MM-DD'),
          renewal_result: '通过',
          expiry_date: nextExpiry.format('YYYY-MM-DD'),
          status: 'valid',
        },
        currentWorkspace.type,
        currentWorkspace.company_id,
        currentWorkspace.factory_id
      )
      message.success('已记录审证，有效期已延长')
      notifyChanged()
    } catch (error: any) {
      message.error(error.message || '审证记录失败')
    }
  }

  const filtered = certifications.filter((cert) => {
    if (filterSystem && cert.certification_system !== filterSystem) return false
    if (filterStatus) {
      const projects = cert.projects || []
      const matchProject = projects.some((p) => (p.status || cert.status) === filterStatus)
      const matchCert = !projects.length && cert.status === filterStatus
      if (!matchProject && !matchCert) return false
    }
    if (searchText) {
      const q = searchText.toLowerCase()
      const inProjects = (cert.projects || []).some(
        (p) =>
          p.project_name?.toLowerCase().includes(q) ||
          p.project_code?.toLowerCase().includes(q)
      )
      return (
        inProjects ||
        cert.certification_number?.toLowerCase().includes(q) ||
        cert.certification_type?.toLowerCase().includes(q) ||
        cert.project_name?.toLowerCase().includes(q) ||
        cert.issuing_authority?.toLowerCase().includes(q)
      )
    }
    return true
  })

  const grouped = useMemo(() => {
    const map = new Map<string, WelderCertification[]>()
    filtered.forEach((c) => {
      const key = c.certification_system || '未标注体系'
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(c)
    })
    const keys = Array.from(map.keys()).sort((a, b) => {
      const ia = SYSTEM_ORDER.indexOf(a)
      const ib = SYSTEM_ORDER.indexOf(b)
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
    return keys.map((k) => ({ system: k, items: map.get(k)! }))
  }, [filtered])

  return (
    <div>
      <div className="doc-list-toolbar" style={{ borderBottom: 'none', marginBottom: 12, paddingBottom: 0 }}>
        <div className="toolbar-search">
          <Input
            placeholder="搜索证号、持证项目、发证机构..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            size="large"
          />
        </div>
        <div className="toolbar-filter">
          <Select
            placeholder="认证体系"
            value={filterSystem}
            onChange={setFilterSystem}
            allowClear
            size="large"
            style={{ width: '100%' }}
          >
            <Option value="ASME">ASME</Option>
            <Option value="国标">国标</Option>
            <Option value="欧标">欧标</Option>
            <Option value="AWS">AWS</Option>
            <Option value="API">API</Option>
            <Option value="DNV">DNV</Option>
          </Select>
          <Select
            placeholder="项目状态"
            value={filterStatus}
            onChange={setFilterStatus}
            allowClear
            size="large"
            style={{ width: '100%' }}
          >
            <Option value="valid">有效</Option>
            <Option value="expiring_soon">即将过期</Option>
            <Option value="expired">已过期</Option>
          </Select>
        </div>
        <div className="toolbar-actions">
          <Button type="primary" icon={<PlusOutlined />} size="large" onClick={handleAdd}>
            添加体系证书
          </Button>
        </div>
      </div>

      <Spin spinning={loading}>
        {grouped.length > 0 ? (
          <Collapse
            defaultActiveKey={grouped.map((g) => g.system)}
            items={grouped.map((g) => {
              const risk = g.items.reduce((acc, c) => {
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
              const projectCount = g.items.reduce(
                (n, c) => n + (c.projects?.length || (c.project_name || c.expiry_date ? 1 : 0)),
                0
              )
              return {
                key: g.system,
                label: (
                  <Space>
                    <Tag color="blue">{g.system}</Tag>
                    <span>
                      {g.items.length} 本证书 · {projectCount} 个持证项目
                    </span>
                    {risk > 0 && <Badge count={risk} title="30天内到期" />}
                  </Space>
                ),
                children: g.items.map((cert) => (
                  <CertificationCard
                    key={cert.id}
                    certification={cert}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onSetPrimary={handleSetPrimary}
                    onAddProject={openAddProject}
                    onEditProject={openEditProject}
                    onDeleteProject={handleDeleteProject}
                    onRenewProject={handleRenewProject}
                  />
                )),
              }
            })}
          />
        ) : (
          <Empty description={certifications.length === 0 ? '暂无体系证书' : '没有符合筛选条件的记录'}>
            {certifications.length === 0 && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                添加第一本体系证书
              </Button>
            )}
          </Empty>
        )}
      </Spin>

      <CertificationModal
        visible={modalVisible}
        certification={editingCertification}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        loading={submitting}
      />

      <CertifiedProjectModal
        visible={projectModalVisible}
        editing={editingProject}
        submitting={projectSubmitting}
        onCancel={() => setProjectModalVisible(false)}
        onSubmit={handleProjectSubmit}
      />
    </div>
  )
}

export default CertificationList
