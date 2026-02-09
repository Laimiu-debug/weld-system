import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  Input,
  Select,
  Tag,
  Modal,
  Form,
  message,
  Space,
  Statistic,
  Tabs,
  Badge,
  Tooltip,
  Popconfirm,
  Switch,
  InputNumber,
  Descriptions,
  Typography
} from 'antd';
import {
  SearchOutlined,
  CheckOutlined,
  CloseOutlined,
  StarOutlined,
  EyeOutlined,
  DownloadOutlined,
  LikeOutlined,
  DislikeOutlined,
  ExclamationCircleOutlined,
  SettingOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { SharedLibraryService, SharedModule, SharedTemplate, LibraryStats } from '../../services/sharedLibrary';
import { useAuthStore } from '@/store/authStore';
import './SharedLibraryManagement.css';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Title, Text } = Typography;

const SharedLibraryManagement: React.FC = () => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [activeTab, setActiveTab] = useState<'pending' | 'modules' | 'templates'>('pending');
  const [pendingModules, setPendingModules] = useState<SharedModule[]>([]);
  const [pendingTemplates, setPendingTemplates] = useState<SharedTemplate[]>([]);
  const [allModules, setAllModules] = useState<SharedModule[]>([]);
  const [allTemplates, setAllTemplates] = useState<SharedTemplate[]>([]);

  // 分页状态
  const [pendingPagination, setPendingPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [allPagination, setAllPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 模态框状态
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [featuredModalVisible, setFeaturedModalVisible] = useState(false);
  const [currentItem, setCurrentItem] = useState<SharedModule | SharedTemplate | null>(null);
  const [reviewForm] = Form.useForm();
  const [featuredForm] = Form.useForm();

  // 检查管理员权限
  useEffect(() => {
    if (user?.is_admin !== true) {
      message.error('需要管理员权限才能访问此页面');
      // 可以在这里重定向到其他页面
    }
  }, [user]);

  // 加载统计信息
  const loadStats = async () => {
    try {
      const response = await SharedLibraryService.getLibraryStats();
      setStats(response);
    } catch (error) {
      console.error('加载统计信息失败:', error);
      message.error('加载统计信息失败');
    }
  };

  // 加载待审核模块
  const loadPendingModules = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getPendingResources('module', page, pageSize);
      setPendingModules(response.items);
      setPendingPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载待审核模块失败:', error);
      message.error('加载待审核模块失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载待审核模板
  const loadPendingTemplates = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getPendingResources('template', page, pageSize);
      setPendingTemplates(response.items);
      setPendingPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载待审核模板失败:', error);
      message.error('加载待审核模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载所有模块
  const loadAllModules = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedModules({
        page,
        page_size: pageSize,
        status: 'approved',
        sort_by: 'created_at',
        sort_order: 'desc'
      });
      setAllModules(response.items);
      setAllPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载所有模块失败:', error);
      message.error('加载所有模块失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载所有模板
  const loadAllTemplates = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedTemplates({
        page,
        page_size: pageSize,
        status: 'approved',
        sort_by: 'created_at',
        sort_order: 'desc'
      });
      setAllTemplates(response.items);
      setAllPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载所有模板失败:', error);
      message.error('加载所有模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    if (user?.is_admin === true) {
      loadStats();
      if (activeTab === 'pending') {
        loadPendingModules();
        loadPendingTemplates();
      } else if (activeTab === 'modules') {
        loadAllModules();
      } else if (activeTab === 'templates') {
        loadAllTemplates();
      }
    }
  }, [activeTab, user]);

  // 审核资源
  const handleReview = (item: SharedModule | SharedTemplate) => {
    setCurrentItem(item);
    setReviewModalVisible(true);
    reviewForm.resetFields();
  };

  // 提交审核
  const handleReviewSubmit = async (values: any) => {
    if (!currentItem) return;

    try {
      const resourceType = 'name' in currentItem && currentItem.fields ? 'module' : 'template';
      await SharedLibraryService.reviewSharedResource(
        resourceType,
        currentItem.id,
        {
          status: values.status,
          review_comment: values.review_comment
        }
      );

      message.success('审核成功');
      setReviewModalVisible(false);

      // 重新加载数据
      if (activeTab === 'pending') {
        loadPendingModules(pendingPagination.current, pendingPagination.pageSize);
        loadPendingTemplates(pendingPagination.current, pendingPagination.pageSize);
      } else if (activeTab === 'modules') {
        loadAllModules(allPagination.current, allPagination.pageSize);
      } else if (activeTab === 'templates') {
        loadAllTemplates(allPagination.current, allPagination.pageSize);
      }

      loadStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '审核失败');
    }
  };

  // 设置推荐
  const handleFeatured = (item: SharedModule | SharedTemplate) => {
    setCurrentItem(item);
    setFeaturedModalVisible(true);
    featuredForm.setFieldsValue({
      is_featured: item.is_featured,
      featured_order: item.featured_order
    });
  };

  // 提交推荐设置
  const handleFeaturedSubmit = async (values: any) => {
    if (!currentItem) return;

    try {
      const resourceType = 'name' in currentItem && currentItem.fields ? 'module' : 'template';
      await SharedLibraryService.setFeaturedResource(
        resourceType,
        currentItem.id,
        {
          is_featured: values.is_featured,
          featured_order: values.featured_order
        }
      );

      message.success('推荐设置成功');
      setFeaturedModalVisible(false);

      // 重新加载数据
      if (activeTab === 'modules') {
        loadAllModules(allPagination.current, allPagination.pageSize);
      } else if (activeTab === 'templates') {
        loadAllTemplates(allPagination.current, allPagination.pageSize);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '推荐设置失败');
    }
  };

  // 待审核模块表格列
  const pendingModuleColumns = [
    {
      title: '模块名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SharedModule) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            分类: {record.category} | 难度: {record.difficulty_level}
          </Text>
        </div>
      )
    },
    {
      title: '上传者',
      dataIndex: 'uploader_name',
      key: 'uploader_name'
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '统计',
      key: 'stats',
      render: (record: SharedModule) => (
        <Space>
          <Tooltip title="浏览次数">
            <EyeOutlined /> {record.view_count}
          </Tooltip>
          <Tooltip title="点赞数">
            <LikeOutlined /> {record.like_count}
          </Tooltip>
          <Tooltip title="下载数">
            <DownloadOutlined /> {record.download_count}
          </Tooltip>
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: SharedModule) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleReview(record)}
          >
            审核
          </Button>
        </Space>
      )
    }
  ];

  // 待审核模板表格列
  const pendingTemplateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SharedTemplate) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            工艺: {record.welding_process_name} | 难度: {record.difficulty_level}
          </Text>
        </div>
      )
    },
    {
      title: '上传者',
      dataIndex: 'uploader_name',
      key: 'uploader_name'
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '统计',
      key: 'stats',
      render: (record: SharedTemplate) => (
        <Space>
          <Tooltip title="浏览次数">
            <EyeOutlined /> {record.view_count}
          </Tooltip>
          <Tooltip title="点赞数">
            <LikeOutlined /> {record.like_count}
          </Tooltip>
          <Tooltip title="下载数">
            <DownloadOutlined /> {record.download_count}
          </Tooltip>
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: SharedTemplate) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            onClick={() => handleReview(record)}
          >
            审核
          </Button>
        </Space>
      )
    }
  ];

  // 所有模块表格列
  const allModuleColumns = [
    {
      title: '模块名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SharedModule) => (
        <div>
          <Text strong>{text}</Text>
          {record.is_featured && (
            <Tag color="gold" style={{ marginLeft: 8 }}>
              <StarOutlined /> 推荐
            </Tag>
          )}
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            分类: {record.category} | 难度: {record.difficulty_level}
          </Text>
        </div>
      )
    },
    {
      title: '上传者',
      dataIndex: 'uploader_name',
      key: 'uploader_name'
    },
    {
      title: '统计',
      key: 'stats',
      render: (record: SharedModule) => (
        <Space>
          <Tooltip title="浏览次数">
            <EyeOutlined /> {record.view_count}
          </Tooltip>
          <Tooltip title="点赞数">
            <LikeOutlined /> {record.like_count}
          </Tooltip>
          <Tooltip title="下载数">
            <DownloadOutlined /> {record.download_count}
          </Tooltip>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'processing', text: '待审核' },
          approved: { color: 'success', text: '已通过' },
          rejected: { color: 'error', text: '已拒绝' },
          removed: { color: 'default', text: '已移除' }
        };
        const config = statusMap[status as keyof typeof statusMap] || statusMap.pending;
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: SharedModule) => (
        <Space>
          <Button
            size="small"
            icon={<StarOutlined />}
            onClick={() => handleFeatured(record)}
          >
            推荐
          </Button>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              // 可以添加查看详情的逻辑
            }}
          >
            详情
          </Button>
        </Space>
      )
    }
  ];

  // 所有模板表格列
  const allTemplateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SharedTemplate) => (
        <div>
          <Text strong>{text}</Text>
          {record.is_featured && (
            <Tag color="gold" style={{ marginLeft: 8 }}>
              <StarOutlined /> 推荐
            </Tag>
          )}
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            工艺: {record.welding_process_name} | 标准: {record.standard}
          </Text>
        </div>
      )
    },
    {
      title: '上传者',
      dataIndex: 'uploader_name',
      key: 'uploader_name'
    },
    {
      title: '统计',
      key: 'stats',
      render: (record: SharedTemplate) => (
        <Space>
          <Tooltip title="浏览次数">
            <EyeOutlined /> {record.view_count}
          </Tooltip>
          <Tooltip title="点赞数">
            <LikeOutlined /> {record.like_count}
          </Tooltip>
          <Tooltip title="下载数">
            <DownloadOutlined /> {record.download_count}
          </Tooltip>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'processing', text: '待审核' },
          approved: { color: 'success', text: '已通过' },
          rejected: { color: 'error', text: '已拒绝' },
          removed: { color: 'default', text: '已移除' }
        };
        const config = statusMap[status as keyof typeof statusMap] || statusMap.pending;
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: SharedTemplate) => (
        <Space>
          <Button
            size="small"
            icon={<StarOutlined />}
            onClick={() => handleFeatured(record)}
          >
            推荐
          </Button>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              // 可以添加查看详情的逻辑
            }}
          >
            详情
          </Button>
        </Space>
      )
    }
  ];

  if (user?.is_admin !== true) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <ExclamationCircleOutlined style={{ fontSize: '48px', color: '#ff4d4f', marginBottom: '16px' }} />
        <Title level={3}>权限不足</Title>
        <Text>需要管理员权限才能访问此页面</Text>
      </div>
    );
  }

  return (
    <div className="shared-library-management">
      <div className="page-header">
        <Title level={2}>
          <SettingOutlined /> 共享库管理
        </Title>
      </div>

      {/* 统计信息 */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总模块数"
                value={stats.total_modules}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总模板数"
                value={stats.total_templates}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="待审核"
                value={stats.pending_modules + stats.pending_templates}
                valueStyle={{ color: '#faad14' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总下载量"
                value={stats.total_downloads}
                prefix={<DownloadOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 主要内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key as any)}>
          <TabPane
            tab={
              <span>
                待审核
                <Badge
                  count={stats?.pending_modules + stats?.pending_templates}
                  style={{ marginLeft: 8 }}
                />
              </span>
            }
            key="pending"
          >
            <Tabs size="small">
              <TabPane tab={`模块 (${pendingModules.length})`} key="pending-modules">
                <Table
                  columns={pendingModuleColumns}
                  dataSource={pendingModules}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    current: pendingPagination.current,
                    pageSize: pendingPagination.pageSize,
                    total: pendingPagination.total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    onChange: (page, pageSize) => {
                      setPendingPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }));
                      loadPendingModules(page, pageSize);
                    }
                  }}
                />
              </TabPane>
              <TabPane tab={`模板 (${pendingTemplates.length})`} key="pending-templates">
                <Table
                  columns={pendingTemplateColumns}
                  dataSource={pendingTemplates}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    current: pendingPagination.current,
                    pageSize: pendingPagination.pageSize,
                    total: pendingPagination.total,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    onChange: (page, pageSize) => {
                      setPendingPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }));
                      loadPendingTemplates(page, pageSize);
                    }
                  }}
                />
              </TabPane>
            </Tabs>
          </TabPane>

          <TabPane tab={`所有模块 (${allModules.length})`} key="modules">
            <Table
              columns={allModuleColumns}
              dataSource={allModules}
              rowKey="id"
              loading={loading}
              pagination={{
                current: allPagination.current,
                pageSize: allPagination.pageSize,
                total: allPagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                onChange: (page, pageSize) => {
                  setAllPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }));
                  loadAllModules(page, pageSize);
                }
              }}
            />
          </TabPane>

          <TabPane tab={`所有模板 (${allTemplates.length})`} key="templates">
            <Table
              columns={allTemplateColumns}
              dataSource={allTemplates}
              rowKey="id"
              loading={loading}
              pagination={{
                current: allPagination.current,
                pageSize: allPagination.pageSize,
                total: allPagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                onChange: (page, pageSize) => {
                  setAllPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }));
                  loadAllTemplates(page, pageSize);
                }
              }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 审核模态框 */}
      <Modal
        title="审核资源"
        open={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        footer={null}
        width={600}
      >
        {currentItem && (
          <Form form={reviewForm} onFinish={handleReviewSubmit} layout="vertical">
            <Descriptions bordered size="small" column={1} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="名称">{currentItem.name}</Descriptions.Item>
              <Descriptions.Item label="描述">{currentItem.description}</Descriptions.Item>
              <Descriptions.Item label="上传者">{currentItem.uploader_name}</Descriptions.Item>
              <Descriptions.Item label="上传时间">
                {new Date(currentItem.created_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            <Form.Item
              name="status"
              label="审核结果"
              rules={[{ required: true, message: '请选择审核结果' }]}
            >
              <Select placeholder="请选择审核结果">
                <Option value="approved">
                  <CheckOutlined style={{ color: '#52c41a' }} /> 通过
                </Option>
                <Option value="rejected">
                  <CloseOutlined style={{ color: '#ff4d4f' }} /> 拒绝
                </Option>
                <Option value="removed">
                  <ExclamationCircleOutlined style={{ color: '#faad14' }} /> 移除
                </Option>
              </Select>
            </Form.Item>

            <Form.Item name="review_comment" label="审核意见">
              <TextArea rows={4} placeholder="请输入审核意见..." />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setReviewModalVisible(false)}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit">
                  提交审核
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* 推荐设置模态框 */}
      <Modal
        title="推荐设置"
        open={featuredModalVisible}
        onCancel={() => setFeaturedModalVisible(false)}
        footer={null}
        width={400}
      >
        {currentItem && (
          <Form form={featuredForm} onFinish={handleFeaturedSubmit} layout="vertical">
            <Form.Item name="is_featured" label="是否推荐" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.is_featured !== currentValues.is_featured
              }
            >
              {({ getFieldValue }) =>
                getFieldValue('is_featured') ? (
                  <Form.Item name="featured_order" label="推荐排序">
                    <InputNumber
                      min={0}
                      max={999}
                      placeholder="数字越小排序越靠前"
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                ) : null
              }
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setFeaturedModalVisible(false)}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit">
                  确认设置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default SharedLibraryManagement;