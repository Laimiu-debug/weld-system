import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  DatePicker,
  InputNumber,
  message,
  Tooltip,
  Dropdown,
  Row,
  Col,
  Descriptions,
  Typography,
  Alert,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  ExportOutlined,
  EyeOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useAuthStore } from '@/store/authStore'
import qualityService from '@/services/quality'
import type { QualityInspection, QualityInspectionCreate, QualityInspectionUpdate } from '@/services/quality'
import workspaceService from '@/services/workspace'
import ListPageHeader from '@/components/ListPageHeader'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select
const { TextArea } = Input

const QualityList: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const taskIdFromQuery = searchParams.get('taskId')
  const { checkPermission } = useAuthStore()
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [searchText, setSearchText] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [resultFilter, setResultFilter] = useState<string>('')
  const [taskIdFilter, setTaskIdFilter] = useState<number | undefined>(
    taskIdFromQuery ? Number(taskIdFromQuery) : undefined
  )
  const [loading, setLoading] = useState(false)
  const [inspections, setInspections] = useState<QualityInspection[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [modalType, setModalType] = useState<'create' | 'edit' | 'view'>('create')
  const [currentInspection, setCurrentInspection] = useState<QualityInspection | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    if (taskIdFromQuery) {
      setTaskIdFilter(Number(taskIdFromQuery))
      setCurrentPage(1)
    }
  }, [taskIdFromQuery])

  // 获取质量检验列表
  const fetchInspections = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    setLoading(true)
    try {
      const params = {
        workspace_type: currentWorkspace.type,
        company_id: currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
        factory_id: currentWorkspace.factory_id,
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchText || undefined,
        inspection_type: typeFilter || undefined,
        result: resultFilter || undefined,
        production_task_id: taskIdFilter,
      }

      const response = await qualityService.getQualityInspectionList(params)

      if (response.success) {
        const { items, total: totalCount } = response.data
        setInspections(items || [])
        setTotal(totalCount || 0)
      } else {
        message.error('获取质量检验列表失败')
      }
    } catch (error: any) {
      console.error('获取质量检验列表失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else {
        message.error('获取质量检验列表失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInspections()
  }, [currentPage, pageSize, searchText, typeFilter, resultFilter, taskIdFilter])

  // 处理创建质量检验
  const handleCreate = () => {
    if (taskIdFilter) {
      navigate(`/quality/create?taskId=${taskIdFilter}&from=production`)
      return
    }
    navigate('/quality/create')
  }

  // 处理编辑质量检验
  const handleEdit = (inspection: QualityInspection) => {
    setModalType('edit')
    setCurrentInspection(inspection)
    form.setFieldsValue({
      inspection_number: inspection.inspection_number,
      inspection_type: inspection.inspection_type,
      inspection_date: inspection.inspection_date ? dayjs(inspection.inspection_date) : undefined,
      inspector_id: inspection.inspector_id,
      inspector_name: inspection.inspector_name,
      result: inspection.result,
      // is_qualified 由 result 自动计算，不需要手动设置
      defects_found: inspection.defects_found,
      corrective_actions: inspection.corrective_actions,
      rework_required: inspection.rework_required,
      follow_up_required: inspection.follow_up_required,
    })
    setIsModalVisible(true)
  }

  // 处理查看质量检验
  const handleView = (inspection: QualityInspection) => {
    setModalType('view')
    setCurrentInspection(inspection)
    setIsModalVisible(true)
  }

  // 处理删除质量检验
  const handleDelete = async (inspectionId: number) => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条质量检验记录吗？此操作不可恢复。',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await qualityService.deleteQualityInspection(
            inspectionId,
            currentWorkspace.type,
            currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
            currentWorkspace.factory_id
          )

          if (response.success) {
            message.success('删除成功')
            fetchInspections()
          } else {
            message.error('删除失败')
          }
        } catch (error: any) {
          console.error('删除质量检验失败:', error)
          message.error('删除失败，请稍后重试')
        }
      },
    })
  }

  // 处理批量删除
  const handleBatchDelete = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的质量检验')
      return
    }

    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 条质量检验记录吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await qualityService.batchDeleteQualityInspections(
            selectedRowKeys.map(key => Number(key)),
            currentWorkspace.type,
            currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
            currentWorkspace.factory_id
          )

          if (response.success) {
            message.success('批量删除成功')
            setSelectedRowKeys([])
            fetchInspections()
          } else {
            message.error('批量删除失败')
          }
        } catch (error: any) {
          console.error('批量删除质量检验失败:', error)
          message.error('批量删除失败，请稍后重试')
        }
      },
    })
  }

  // 处理表单提交
  const handleModalOk = async () => {
    const currentWorkspace = workspaceService.getCurrentWorkspaceFromStorage()
    if (!currentWorkspace) {
      message.warning('请先选择工作区')
      return
    }

    try {
      const values = await form.validateFields()

      const formData: QualityInspectionCreate | QualityInspectionUpdate = {
        ...values,
        inspection_date: values.inspection_date ? values.inspection_date.format('YYYY-MM-DD') : undefined,
      }

      setLoading(true)

      if (modalType === 'create') {
        const response = await qualityService.createQualityInspection(
          formData as QualityInspectionCreate,
          currentWorkspace.type,
          currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
          currentWorkspace.factory_id
        )

        if (response.success) {
          message.success('创建成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchInspections()
        } else {
          message.error('创建失败')
        }
      } else if (modalType === 'edit' && currentInspection) {
        const response = await qualityService.updateQualityInspection(
          currentInspection.id,
          formData as QualityInspectionUpdate,
          currentWorkspace.type,
          currentWorkspace.type === 'enterprise' ? currentWorkspace.company_id : undefined,
          currentWorkspace.factory_id
        )

        if (response.success) {
          message.success('更新成功')
          setIsModalVisible(false)
          form.resetFields()
          fetchInspections()
        } else {
          message.error('更新失败')
        }
      }
    } catch (error: any) {
      console.error('操作失败:', error)
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else if (error.errorFields) {
        message.error('请检查表单填写是否正确')
      } else {
        message.error('操作失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  // 处理模态框取消
  const handleModalCancel = () => {
    setIsModalVisible(false)
    form.resetFields()
    setCurrentInspection(null)
  }

  // 辅助函数 - 获取检验类型配置
  const getInspectionTypeConfig = (type: string) => {
    const typeConfig: Record<string, { color: string; text: string }> = {
      visual: { color: 'blue', text: '外观检验' },
      radiographic: { color: 'green', text: '射线检验' },
      ultrasonic: { color: 'orange', text: '超声波检验' },
      magnetic: { color: 'purple', text: '磁粉检验' },
      magnetic_particle: { color: 'purple', text: '磁粉检验' },
      penetrant: { color: 'cyan', text: '渗透检验' },
      liquid_penetrant: { color: 'cyan', text: '渗透检验' },
      destructive: { color: 'red', text: '破坏性检验' },
      other: { color: 'default', text: '其他' },
    }
    return typeConfig[type] || { color: 'default', text: type }
  }

  // 辅助函数 - 获取检验结果配置
  const getResultConfig = (result: string) => {
    const resultConfig: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      pass: { color: 'success', text: '合格', icon: <CheckCircleOutlined /> },
      fail: { color: 'error', text: '不合格', icon: <CloseCircleOutlined /> },
      conditional: { color: 'warning', text: '有条件合格', icon: <ExclamationCircleOutlined /> },
      pending: { color: 'default', text: '待检验', icon: <ClockCircleOutlined /> },
    }
    return resultConfig[result] || { color: 'default', text: result, icon: null }
  }

  // 表格列配置
  const columns: ColumnsType<QualityInspection> = [
    {
      title: '检验编号',
      dataIndex: 'inspection_number',
      key: 'inspection_number',
      width: 160,
      fixed: 'left',
    },
    {
      title: '项目',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 140,
      ellipsis: true,
      render: (v?: string) => v || '-',
    },
    {
      title: '容器号',
      dataIndex: 'vessel_no',
      key: 'vessel_no',
      width: 100,
      render: (v?: string) => v || '-',
    },
    {
      title: '工令号',
      dataIndex: 'work_order_no',
      key: 'work_order_no',
      width: 110,
      render: (v?: string) => v || '-',
    },
    {
      title: '焊缝',
      dataIndex: 'weld_joint_number',
      key: 'weld_joint_number',
      width: 90,
      render: (v?: string, row?: QualityInspection) => v || row?.joint_number || '-',
    },
    {
      title: '生产任务',
      dataIndex: 'production_task_id',
      key: 'production_task_id',
      width: 100,
      render: (taskId?: number) =>
        taskId ? (
          <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/production/${taskId}?tab=quality`)}>
            #{taskId}
          </Button>
        ) : (
          '-'
        ),
    },
    {
      title: '检验类型',
      dataIndex: 'inspection_type',
      key: 'inspection_type',
      width: 110,
      render: (type: string) => {
        const config = getInspectionTypeConfig(type)
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '检验结果',
      dataIndex: 'result',
      key: 'result',
      width: 110,
      render: (result: string) => {
        const config = getResultConfig(result)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '检验日期',
      dataIndex: 'inspection_date',
      key: 'inspection_date',
      width: 110,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '检验员',
      dataIndex: 'inspector_name',
      key: 'inspector_name',
      width: 90,
    },
    {
      title: '缺陷',
      dataIndex: 'defects_found',
      key: 'defects_found',
      width: 70,
      render: (defects: number) => defects || 0,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record: QualityInspection) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          {checkPermission('quality.update') && (
            <Tooltip title="编辑">
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
            </Tooltip>
          )}
          {checkPermission('quality.delete') && (
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record.id)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys)
    },
  }

  return (
    <div className="list-page">
      <ListPageHeader
        title="质量管理"
        description="质量检验记录、结果与复检管理"
      />
      {taskIdFilter ? (
        <Alert
          className="mb-4"
          type="info"
          showIcon
          message={`已按生产任务 #${taskIdFilter} 筛选质检`}
          action={
            <Space>
              <Button size="small" onClick={() => navigate(`/production/${taskIdFilter}?tab=quality`)}>
                返回生产任务
              </Button>
              <Button
                size="small"
                onClick={() => {
                  setTaskIdFilter(undefined)
                  setSearchParams({})
                }}
              >
                清除筛选
              </Button>
            </Space>
          }
        />
      ) : null}
      <Card className="list-page-card">
        <div className="doc-list-toolbar">
          <div className="toolbar-search">
            <Search
              placeholder="搜索编号 / 项目 / 容器 / 工令 / 焊缝"
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={setSearchText}
              onChange={(e) => !e.target.value && setSearchText('')}
            />
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="检验类型"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={(value) => setTypeFilter(value || '')}
              value={typeFilter || undefined}
            >
              <Option value="visual">外观检验</Option>
              <Option value="radiographic">射线检验</Option>
              <Option value="ultrasonic">超声波检验</Option>
              <Option value="magnetic_particle">磁粉检验</Option>
              <Option value="liquid_penetrant">渗透检验</Option>
              <Option value="destructive">破坏性检验</Option>
            </Select>
          </div>
          <div className="toolbar-filter">
            <Select
              placeholder="检验结果"
              allowClear
              size="large"
              style={{ width: '100%' }}
              onChange={(value) => setResultFilter(value || '')}
              value={resultFilter || undefined}
            >
              <Option value="pass">合格</Option>
              <Option value="fail">不合格</Option>
              <Option value="conditional">有条件合格</Option>
              <Option value="pending">待检验</Option>
            </Select>
          </div>
          <div className="toolbar-actions">
            {selectedRowKeys.length > 0 && (
              <Button danger size="large" onClick={handleBatchDelete}>
                批量删除 ({selectedRowKeys.length})
              </Button>
            )}
            {checkPermission('quality.create') && (
              <Button type="primary" icon={<PlusOutlined />} size="large" onClick={handleCreate}>
                新增质量检验
              </Button>
            )}
            <Button icon={<ReloadOutlined />} size="large" onClick={fetchInspections}>
              刷新
            </Button>
          </div>
        </div>

        <div className="list-table-wrap">
          <Table
            columns={columns}
            dataSource={inspections}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1100 }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, size) => {
                setCurrentPage(page)
                setPageSize(size)
              },
            }}
            rowSelection={rowSelection}
          />
        </div>
      </Card>

      {/* 质量检验模态框 */}
      <Modal
        title={
          modalType === 'create'
            ? '新增质量检验'
            : modalType === 'edit'
            ? '编辑质量检验'
            : '查看质量检验'
        }
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
        okText={modalType === 'view' ? '关闭' : '确定'}
        cancelText="取消"
        cancelButtonProps={{ style: { display: modalType === 'view' ? 'none' : 'inline-block' } }}
      >
        {modalType === 'view' && currentInspection ? (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="检验编号">{currentInspection.inspection_number}</Descriptions.Item>
            <Descriptions.Item label="检验类型">{getInspectionTypeConfig(currentInspection.inspection_type).text}</Descriptions.Item>
            <Descriptions.Item label="项目">{currentInspection.project_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="容器号">{currentInspection.vessel_no || '-'}</Descriptions.Item>
            <Descriptions.Item label="工令号">{currentInspection.work_order_no || '-'}</Descriptions.Item>
            <Descriptions.Item label="焊缝">{currentInspection.weld_joint_number || currentInspection.joint_number || '-'}</Descriptions.Item>
            <Descriptions.Item label="检验日期">{currentInspection.inspection_date ? dayjs(currentInspection.inspection_date).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
            <Descriptions.Item label="检验员">{currentInspection.inspector_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="检验结果">{getResultConfig(currentInspection.result).text}</Descriptions.Item>
            <Descriptions.Item label="是否合格">{currentInspection.is_qualified ? '合格' : '不合格'}</Descriptions.Item>
            <Descriptions.Item label="缺陷总数">{currentInspection.defects_found || 0}</Descriptions.Item>
            <Descriptions.Item label="裂纹">{currentInspection.crack_count || 0}</Descriptions.Item>
            <Descriptions.Item label="气孔">{currentInspection.porosity_count || 0}</Descriptions.Item>
            <Descriptions.Item label="夹渣">{currentInspection.inclusion_count || 0}</Descriptions.Item>
            <Descriptions.Item label="咬边">{currentInspection.undercut_count || 0}</Descriptions.Item>
            <Descriptions.Item label="未焊透">{currentInspection.incomplete_penetration_count || 0}</Descriptions.Item>
            <Descriptions.Item label="未熔合">{currentInspection.incomplete_fusion_count || 0}</Descriptions.Item>
            <Descriptions.Item label="其他缺陷">{currentInspection.other_defect_count || 0}</Descriptions.Item>
            {currentInspection.other_defect_description && (
              <Descriptions.Item label="其他缺陷描述" span={2}>{currentInspection.other_defect_description}</Descriptions.Item>
            )}
            <Descriptions.Item label="需要纠正措施">{currentInspection.corrective_action_required ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="需要返工">{currentInspection.rework_required ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="需要修复">{currentInspection.repair_required ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="需要跟进">{currentInspection.follow_up_required ? '是' : '否'}</Descriptions.Item>
            {currentInspection.corrective_actions && (
              <Descriptions.Item label="纠正措施" span={2}>{currentInspection.corrective_actions}</Descriptions.Item>
            )}
            {currentInspection.repair_description && (
              <Descriptions.Item label="修复说明" span={2}>{currentInspection.repair_description}</Descriptions.Item>
            )}
            <Descriptions.Item label="需要复检">{currentInspection.reinspection_required ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="复检日期">{currentInspection.reinspection_date ? dayjs(currentInspection.reinspection_date).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
            {currentInspection.reinspection_result && (
              <Descriptions.Item label="复检结果" span={2}>{currentInspection.reinspection_result}</Descriptions.Item>
            )}
            {currentInspection.reinspection_notes && (
              <Descriptions.Item label="复检备注" span={2}>{currentInspection.reinspection_notes}</Descriptions.Item>
            )}
            <Descriptions.Item label="环境温度">{currentInspection.ambient_temperature ? `${currentInspection.ambient_temperature}°C` : '-'}</Descriptions.Item>
            <Descriptions.Item label="天气条件">{currentInspection.weather_conditions || '-'}</Descriptions.Item>
            {currentInspection.tags && (
              <Descriptions.Item label="标签" span={2}>{currentInspection.tags}</Descriptions.Item>
            )}
          </Descriptions>
        ) : (
          <Form form={form} layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="inspection_number"
                  label="检验编号"
                  rules={[{ required: true, message: '请输入检验编号' }]}
                >
                  <Input placeholder="请输入检验编号" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="inspection_type"
                  label="检验类型"
                >
                  <Select placeholder="请选择检验类型">
                    <Option value="visual">外观检验</Option>
                    <Option value="radiographic">射线检验</Option>
                    <Option value="ultrasonic">超声波检验</Option>
                    <Option value="magnetic_particle">磁粉检验</Option>
                    <Option value="liquid_penetrant">渗透检验</Option>
                    <Option value="destructive">破坏性检验</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="inspection_date"
                  label="检验日期"
                >
                  <DatePicker style={{ width: '100%' }} placeholder="请选择检验日期" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="inspector_id"
                  label="检验员ID"
                >
                  <InputNumber style={{ width: '100%' }} placeholder="请输入检验员ID" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="inspector_name"
                  label="检验员姓名"
                >
                  <Input placeholder="请输入检验员姓名" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="result"
                  label="检验结果"
                >
                  <Select placeholder="请选择检验结果">
                    <Option value="pending">待检验</Option>
                    <Option value="pass">合格</Option>
                    <Option value="fail">不合格</Option>
                    <Option value="conditional">有条件合格</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="defects_found"
                  label="缺陷数量"
                >
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="请输入缺陷数量" />
                </Form.Item>
              </Col>
            </Row>

            {/* 缺陷详细计数 */}
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="crack_count" label="裂纹数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="裂纹数量" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="porosity_count" label="气孔数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="气孔数量" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="inclusion_count" label="夹渣数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="夹渣数量" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="undercut_count" label="咬边数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="咬边数量" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="incomplete_penetration_count" label="未焊透数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="未焊透数量" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="incomplete_fusion_count" label="未熔合数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="未熔合数量" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="other_defect_count" label="其他缺陷数量">
                  <InputNumber style={{ width: '100%' }} min={0} placeholder="其他缺陷数量" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="other_defect_description" label="其他缺陷描述">
                  <Input placeholder="请输入其他缺陷描述" />
                </Form.Item>
              </Col>
            </Row>

            {/* 处理措施 */}
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="corrective_action_required" label="需要纠正措施">
                  <Select placeholder="请选择">
                    <Option value={true}>是</Option>
                    <Option value={false}>否</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="rework_required" label="需要返工">
                  <Select placeholder="请选择">
                    <Option value={true}>是</Option>
                    <Option value={false}>否</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="repair_required" label="需要修复">
                  <Select placeholder="请选择">
                    <Option value={true}>是</Option>
                    <Option value={false}>否</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="follow_up_required" label="需要跟进">
                  <Select placeholder="请选择">
                    <Option value={true}>是</Option>
                    <Option value={false}>否</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="repair_description" label="修复说明">
                  <Input placeholder="请输入修复说明" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="corrective_actions" label="纠正措施">
              <TextArea rows={2} placeholder="请输入纠正措施" />
            </Form.Item>

            {/* 复检信息 */}
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item name="reinspection_required" label="需要复检">
                  <Select placeholder="请选择">
                    <Option value={true}>是</Option>
                    <Option value={false}>否</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="reinspection_date" label="复检日期">
                  <DatePicker style={{ width: '100%' }} placeholder="请选择复检日期" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="reinspection_result" label="复检结果">
                  <Select placeholder="请选择复检结果">
                    <Option value="pass">合格</Option>
                    <Option value="fail">不合格</Option>
                    <Option value="conditional">有条件合格</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="reinspection_notes" label="复检备注">
              <TextArea rows={2} placeholder="请输入复检备注" />
            </Form.Item>

            {/* 环境条件 */}
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="ambient_temperature" label="环境温度(°C)">
                  <InputNumber style={{ width: '100%' }} placeholder="请输入环境温度" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="weather_conditions" label="天气条件">
                  <Input placeholder="请输入天气条件" />
                </Form.Item>
              </Col>
            </Row>

            {/* 附加信息 */}
            <Form.Item name="tags" label="标签">
              <Input placeholder="请输入标签，多个标签用逗号分隔" />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}

export default QualityList

