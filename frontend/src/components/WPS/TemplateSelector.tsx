/**
 * WPS模板选择组件
 * 直接显示所有可用模板，支持搜索和筛选
 */
import React, { useState, useEffect, useMemo } from 'react'
import { Card, Space, Typography, Alert, Spin, Tag, Empty, message, Button, Row, Col, Input, Pagination } from 'antd'
import { FileTextOutlined, ExclamationCircleOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import wpsTemplateService, {
  WPSTemplateSummary,
  WPSTemplate
} from '@/services/wpsTemplates'
import styles from './TemplateSelector.module.css'

const { Text, Title } = Typography

interface TemplateSelectorProps {
  value?: string // 选中的模板ID
  onChange?: (templateId: string, template: WPSTemplate | null) => void
  disabled?: boolean
  moduleType?: 'wps' | 'pqr' | 'ppqr' // 模块类型，用于筛选对应类型的模板
}

const ITEMS_PER_PAGE = 10

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  moduleType = 'wps' // 默认为WPS类型
}) => {
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<WPSTemplateSummary[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<WPSTemplate | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  // 初始化加载所有模板，当moduleType变化时重新加载
  useEffect(() => {
    loadAllTemplates()
  }, [moduleType])

  // 加载所有可用模板
  const loadAllTemplates = async () => {
    try {
      setLoading(true)
      setError(null)
      // 根据moduleType筛选模板
      const response = await wpsTemplateService.getTemplates({
        module_type: moduleType
      })
      if (response.success && response.data) {
        setTemplates(response.data.items)
        setCurrentPage(1)
      } else {
        setError('加载模板列表失败，请稍后重试')
      }
    } catch (error: any) {
      console.error('加载模板列表失败:', error)
      // 处理权限错误
      if (error?.response?.status === 403) {
        setError(`您没有权限访问${moduleType.toUpperCase()}模板，请联系管理员`)
      } else if (error?.response?.status === 401) {
        setError('登录已过期，请重新登录')
      } else {
        setError(error?.response?.data?.detail || '加载模板列表失败，请稍后重试')
      }
      message.error(error?.response?.data?.detail || '加载模板列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 过滤模板
  const filteredTemplates = useMemo(() => {
    if (!searchText) return templates
    const searchLower = searchText.toLowerCase()
    return templates.filter(template =>
      template.name.toLowerCase().includes(searchLower) ||
      template.welding_process?.toLowerCase().includes(searchLower) ||
      template.welding_process_name?.toLowerCase().includes(searchLower) ||
      template.standard?.toLowerCase().includes(searchLower)
    )
  }, [templates, searchText])

  // 分页数据
  const paginatedTemplates = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    const endIndex = startIndex + ITEMS_PER_PAGE
    return filteredTemplates.slice(startIndex, endIndex)
  }, [filteredTemplates, currentPage])

  // 处理模板选择
  const handleTemplateChange = async (templateId: string) => {
    try {
      const response = await wpsTemplateService.getTemplate(templateId)
      if (response.success && response.data) {
        setSelectedTemplate(response.data)
        onChange?.(templateId, response.data)
      } else {
        message.error('加载模板详情失败')
      }
    } catch (error: any) {
      console.error('加载模板详情失败:', error)
      // 处理权限错误
      if (error?.response?.status === 403) {
        message.error('您没有权限访问此模板')
      } else if (error?.response?.status === 404) {
        message.error('模板不存在')
      } else {
        message.error(error?.response?.data?.detail || '加载模板详情失败')
      }
    }
  }

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          <span>选择{moduleType.toUpperCase()}模板</span>
        </Space>
      }
      variant="borderless"
      className={styles.templateSelector}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 错误提示 */}
        {error && (
          <Alert
            message="加载失败"
            description={error}
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
            closable
            onClose={() => setError(null)}
            className={styles.errorAlert}
            action={
              <Button
                size="small"
                type="link"
                icon={<ReloadOutlined />}
                onClick={loadAllTemplates}
              >
                重试
              </Button>
            }
          />
        )}

        {/* 提示信息 */}
        {!error && (
          <Alert
            message={`请从下方列表中选择一个${moduleType.toUpperCase()}模板作为创建基础`}
            type="info"
            showIcon
            className={styles.infoAlert}
          />
        )}

        {/* 模板选择 */}
        <div>
          <div className={styles.selectLabel}>
            <Text className={styles.selectLabelText}>{moduleType.toUpperCase()}模板</Text>
            <Text className={styles.selectLabelRequired}>*</Text>
            {templates.length > 0 && (
              <Text className={styles.selectLabelCount}>
                （共 {templates.length} 个可用模板）
              </Text>
            )}
          </div>

          {/* 搜索框 */}
          {templates.length > 0 && (
            <Input
              placeholder="搜索模板名称、焊接工艺或标准..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => {
                setSearchText(e.target.value)
                setCurrentPage(1)
              }}
              allowClear
              size="large"
              className={styles.searchInput}
            />
          )}

          <Spin spinning={loading} tip="加载模板列表中...">
            {/* 模板网格 */}
            {paginatedTemplates.length > 0 ? (
              <div className={styles.templateGrid}>
                <Row gutter={[16, 16]}>
                  {paginatedTemplates.map((template) => (
                    <Col key={template.id} xs={24} sm={12} md={8} lg={6} className={styles.templateGridItem}>
                      <Card
                        hoverable
                        className={`${styles.templateGridCard} ${value === template.id ? styles.templateGridCardSelected : ''}`}
                        onClick={() => handleTemplateChange(template.id)}
                      >
                        <div className={styles.templateGridContent}>
                          <div className={styles.templateGridName}>
                            <Text strong ellipsis>{template.name}</Text>
                          </div>
                          <div className={styles.templateGridTags}>
                            {/* 模板类型标签 */}
                            {template.module_type === 'wps' && (
                              <Tag color="cyan" style={{ margin: '2px' }}>WPS</Tag>
                            )}
                            {template.module_type === 'pqr' && (
                              <Tag color="orange" style={{ margin: '2px' }}>PQR</Tag>
                            )}
                            {template.module_type === 'ppqr' && (
                              <Tag color="magenta" style={{ margin: '2px' }}>pPQR</Tag>
                            )}

                            {/* 来源标签 */}
                            {template.is_system && (
                              <Tag color="green" style={{ margin: '2px' }}>系统</Tag>
                            )}
                            {template.template_source === 'user' && (
                              <Tag color="blue" style={{ margin: '2px' }}>个人</Tag>
                            )}
                            {template.template_source === 'enterprise' && (
                              <Tag color="purple" style={{ margin: '2px' }}>企业</Tag>
                            )}
                          </div>
                          <div className={styles.templateGridMeta}>
                            {template.welding_process_name && (
                              <div className={styles.templateGridMetaItem}>
                                <Text type="secondary" className={styles.templateGridMetaLabel}>工艺：</Text>
                                <Text ellipsis>{template.welding_process_name}</Text>
                              </div>
                            )}
                            {template.standard && (
                              <div className={styles.templateGridMetaItem}>
                                <Text type="secondary" className={styles.templateGridMetaLabel}>标准：</Text>
                                <Text ellipsis>{template.standard}</Text>
                              </div>
                            )}
                            {template.usage_count !== undefined && (
                              <div className={styles.templateGridMetaItem}>
                                <Text type="secondary">已使用 {template.usage_count} 次</Text>
                              </div>
                            )}
                          </div>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            ) : (
              <div className={styles.emptyState}>
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    searchText ? '未找到匹配的模板' : (
                      <Space direction="vertical" size="small">
                        <Text type="secondary">暂无可用的{moduleType.toUpperCase()}模板</Text>
                        <Text className={styles.emptyStateText}>
                          系统中暂无可用的{moduleType.toUpperCase()}模板，请联系管理员添加模板
                        </Text>
                      </Space>
                    )
                  }
                />
              </div>
            )}
          </Spin>

          {/* 分页 */}
          {filteredTemplates.length > ITEMS_PER_PAGE && (
            <div className={styles.paginationContainer}>
              <Pagination
                current={currentPage}
                pageSize={ITEMS_PER_PAGE}
                total={filteredTemplates.length}
                onChange={setCurrentPage}
                showSizeChanger={false}
                showQuickJumper
              />
            </div>
          )}

          {/* 模板详情显示 */}
          {selectedTemplate && (
            <Card
              size="small"
              className={styles.templateCard}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Title level={5} className={styles.templateCardTitle}>
                    {selectedTemplate.name}
                  </Title>
                  {selectedTemplate.description && (
                    <Text className={styles.templateCardDescription}>
                      {selectedTemplate.description}
                    </Text>
                  )}
                </div>

                <div className={styles.templateCardInfo}>
                  <div className={styles.templateCardInfoItem}>
                    <Text className={styles.templateCardLabel}>焊接工艺：</Text>
                    <div>
                      <Tag color="blue">{selectedTemplate.welding_process}</Tag>
                      <Text className={styles.templateCardValue}>
                        {selectedTemplate.welding_process_name}
                      </Text>
                    </div>
                  </div>

                  {selectedTemplate.standard && (
                    <div className={styles.templateCardInfoItem}>
                      <Text className={styles.templateCardLabel}>执行标准：</Text>
                      <Text className={styles.templateCardValue}>
                        {selectedTemplate.standard}
                      </Text>
                    </div>
                  )}

                  {selectedTemplate.usage_count !== undefined && (
                    <div className={styles.templateCardInfoItem}>
                      <Text className={styles.templateCardLabel}>使用次数：</Text>
                      <Text className={styles.templateCardValue}>
                        {selectedTemplate.usage_count} 次
                      </Text>
                    </div>
                  )}
                </div>
              </Space>
            </Card>
          )}
        </div>
      </Space>
    </Card>
  )
}

export default TemplateSelector

