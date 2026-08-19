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
import { useAuthContext } from '@/contexts/AuthContext';
import apiService from '@/services/api';
import './SharedLibraryManagement.css';

const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

// 类型定义
interface LibraryStats {
  total_modules: number;
  total_templates: number;
  pending_modules: number;
  pending_templates: number;
  total_downloads: number;
  featured_modules: number;
  featured_templates: number;
}

interface SharedModule {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty_level: string;
  uploader_name: string;
  uploader_id: number;
  created_at: string;
  view_count: number;
  like_count: number;
  dislike_count: number;
  download_count: number;
  status: string;
  is_featured: boolean;
  featured_order: number;
  tags: string[];
  fields?: any;
}

interface SharedTemplate {
  id: string;
  name: string;
  description: string;
  welding_process: string;
  welding_process_name: string;
  standard: string;
  uploader_name: string;
  uploader_id: number;
  created_at: string;
  view_count: number;
  like_count: number;
  dislike_count: number;
  download_count: number;
  status: string;
  is_featured: boolean;
  featured_order: number;
  tags: string[];
  difficulty_level?: string;
  fields?: never;
  module_instances?: any;
}

// API 服务类
class SharedLibraryService {
  static async getLibraryStats(): Promise<LibraryStats> {
    return apiService.authGet('/shared-library/admin/stats');
  }

  static async getPendingResources(
    resourceType: 'module' | 'template',
    page: number = 1,
    pageSize: number = 10
  ): Promise<{ items: SharedModule[] | SharedTemplate[], total: number }> {
    return apiService.authGet(`/shared-library/admin/pending/${resourceType}`, {
      params: { page, page_size: pageSize },
    });
  }

  static async getSharedModules(params: {
    page?: number;
    page_size?: number;
    status?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<{ items: SharedModule[], total: number }> {
    return apiService.authGet('/shared-library/modules', { params });
  }

  static async getSharedTemplates(params: {
    page?: number;
    page_size?: number;
    status?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<{ items: SharedTemplate[], total: number }> {
    return apiService.authGet('/shared-library/templates', { params });
  }

  static async reviewSharedResource(
    resourceType: 'module' | 'template',
    resourceId: string,
    reviewData: { status: string, review_comment?: string }
  ): Promise<void> {
    await apiService.authPost(`/shared-library/admin/review/${resourceType}/${resourceId}`, reviewData);
  }

  static async setFeaturedResource(
    resourceType: 'module' | 'template',
    resourceId: string,
    featuredData: { is_featured: boolean, featured_order?: number }
  ): Promise<void> {
    await apiService.authPost(`/shared-library/admin/featured/${resourceType}/${resourceId}`, featuredData);
  }
}

const SharedLibraryManagement: React.FC = () => {
  const { user } = useAuthContext();
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
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentItem, setCurrentItem] = useState<SharedModule | SharedTemplate | null>(null);
  const [reviewForm] = Form.useForm();
  const [featuredForm] = Form.useForm();

  // 检查管理员权限
  useEffect(() => {
    if (!user) {
      message.error('需要管理员权限才能访问此页面');
    }
  }, [user]);

  // 加载统计信息
  const loadStats = async () => {
    try {
      // 使用普通API端点计算统计信息（page_size最大100）
      const [allModules, allTemplates, pendingModules, pendingTemplates] = await Promise.all([
        SharedLibraryService.getSharedModules({ status: 'all', page: 1, page_size: 100 }),
        SharedLibraryService.getSharedTemplates({ status: 'all', page: 1, page_size: 100 }),
        SharedLibraryService.getSharedModules({ status: 'pending', page: 1, page_size: 100 }),
        SharedLibraryService.getSharedTemplates({ status: 'pending', page: 1, page_size: 100 })
      ]);

      const stats: LibraryStats = {
        total_modules: allModules.total,
        total_templates: allTemplates.total,
        pending_modules: pendingModules.total,
        pending_templates: pendingTemplates.total,
        total_downloads: allModules.items.reduce((sum, m) => sum + (m.download_count || 0), 0) +
                        allTemplates.items.reduce((sum, t) => sum + (t.download_count || 0), 0),
        featured_modules: allModules.items.filter(m => m.is_featured).length,
        featured_templates: allTemplates.items.filter(t => t.is_featured).length
      };

      setStats(stats);
    } catch (error) {
      console.error('加载统计信息失败:', error);
      // 静默失败，不显示错误消息
    }
  };

  // 加载待审核模块
  const loadPendingModules = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedModules({
        page,
        page_size: pageSize,
        status: 'pending',
        sort_by: 'created_at',
        sort_order: 'desc'
      });
      setPendingModules(response.items);
      setPendingPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载待审核模块失败:', error);
      // 静默失败，不显示错误消息
    } finally {
      setLoading(false);
    }
  };

  // 加载待审核模板
  const loadPendingTemplates = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedTemplates({
        page,
        page_size: pageSize,
        status: 'pending',
        sort_by: 'created_at',
        sort_order: 'desc'
      });
      setPendingTemplates(response.items);
      setPendingPagination(prev => ({
        ...prev,
        current: page,
        total: response.total
      }));
    } catch (error) {
      console.error('加载待审核模板失败:', error);
      // 静默失败，不显示错误消息
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
        status: 'all',  // 管理员查看所有状态的资源
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
        status: 'all',  // 管理员查看所有状态的资源
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
    if (user) {
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
      const resourceType = 'fields' in currentItem ? 'module' : 'template';
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
      message.error('审核失败');
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
      const resourceType = 'fields' in currentItem ? 'module' : 'template';
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
      message.error('推荐设置失败');
    }
  };

  // 查看详情
  const handleViewDetail = (item: SharedModule | SharedTemplate) => {
    setCurrentItem(item);
    setDetailModalVisible(true);
  };

  // 删除资源
  const handleDelete = (item: SharedModule | SharedTemplate) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 "${item.name}" 吗？此操作不可恢复。`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const resourceType = 'fields' in item ? 'module' : 'template';
          // 通过审核接口将状态设置为 removed
          await SharedLibraryService.reviewSharedResource(
            resourceType,
            item.id,
            {
              status: 'removed',
              review_comment: '管理员删除'
            }
          );

          message.success('删除成功');

          // 重新加载数据
          if (activeTab === 'modules') {
            loadAllModules(allPagination.current, allPagination.pageSize);
          } else if (activeTab === 'templates') {
            loadAllTemplates(allPagination.current, allPagination.pageSize);
          } else if (activeTab === 'pending') {
            loadPendingModules(pendingPagination.current, pendingPagination.pageSize);
            loadPendingTemplates(pendingPagination.current, pendingPagination.pageSize);
          }
          loadStats();
        } catch (error: any) {
          message.error('删除失败');
        }
      }
    });
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
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Button
            size="small"
            danger
            icon={<CloseOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
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
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Button
            size="small"
            danger
            icon={<CloseOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  if (!user) {
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
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as any)}
          items={[
            {
              key: 'pending',
              label: (
                <span>
                  待审核
                  <Badge
                    count={(stats?.pending_modules || 0) + (stats?.pending_templates || 0)}
                    style={{ marginLeft: 8 }}
                  />
                </span>
              ),
              children: (
                <Tabs size="small" items={[
                  {
                    key: 'pending-modules',
                    label: `模块 (${pendingModules.length})`,
                    children: (
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
                    )
                  },
                  {
                    key: 'pending-templates',
                    label: `模板 (${pendingTemplates.length})`,
                    children: (
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
                    )
                  }
                ]} />
              )
            },
            {
              key: 'modules',
              label: `所有模块 (${allModules.length})`,
              children: (
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
              )
            },
            {
              key: 'templates',
              label: `所有模板 (${allTemplates.length})`,
              children: (
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
              )
            }
          ]}
        />
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

      {/* 详情查看模态框 */}
      <Modal
        title="资源详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {currentItem && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="名称" span={2}>
              {currentItem.name}
            </Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {currentItem.description}
            </Descriptions.Item>
            {'category' in currentItem && (
              <>
                <Descriptions.Item label="分类">
                  {currentItem.category}
                </Descriptions.Item>
                <Descriptions.Item label="难度">
                  {currentItem.difficulty_level}
                </Descriptions.Item>
              </>
            )}
            {'welding_process_name' in currentItem && (
              <>
                <Descriptions.Item label="焊接工艺">
                  {currentItem.welding_process_name}
                </Descriptions.Item>
                <Descriptions.Item label="标准">
                  {currentItem.standard}
                </Descriptions.Item>
              </>
            )}
            <Descriptions.Item label="上传者">
              {currentItem.uploader_name}
            </Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {new Date(currentItem.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {(() => {
                const statusMap = {
                  pending: { color: 'processing', text: '待审核' },
                  approved: { color: 'success', text: '已通过' },
                  rejected: { color: 'error', text: '已拒绝' },
                  removed: { color: 'default', text: '已移除' }
                };
                const config = statusMap[currentItem.status as keyof typeof statusMap] || statusMap.pending;
                return <Tag color={config.color}>{config.text}</Tag>;
              })()}
            </Descriptions.Item>
            <Descriptions.Item label="推荐">
              {currentItem.is_featured ? (
                <Tag color="gold"><StarOutlined /> 已推荐</Tag>
              ) : (
                <Tag>未推荐</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="浏览次数">
              <EyeOutlined /> {currentItem.view_count}
            </Descriptions.Item>
            <Descriptions.Item label="点赞数">
              <LikeOutlined /> {currentItem.like_count}
            </Descriptions.Item>
            <Descriptions.Item label="点踩数">
              <DislikeOutlined /> {currentItem.dislike_count}
            </Descriptions.Item>
            <Descriptions.Item label="下载次数">
              <DownloadOutlined /> {currentItem.download_count}
            </Descriptions.Item>
            {currentItem.tags && currentItem.tags.length > 0 && (
              <Descriptions.Item label="标签" span={2}>
                {currentItem.tags.map((tag: string) => (
                  <Tag key={tag}>{tag}</Tag>
                ))}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default SharedLibraryManagement;
