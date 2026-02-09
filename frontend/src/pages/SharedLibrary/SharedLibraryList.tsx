import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Input,
  Select,
  Tag,
  Rate,
  Pagination,
  Spin,
  Empty,
  Tabs,
  Badge,
  message,
  Tooltip,
  Modal,
  Form,
  Space
} from 'antd';
import {
  SearchOutlined,
  DownloadOutlined,
  LikeOutlined,
  DislikeOutlined,
  EyeOutlined,
  StarOutlined,
  FilterOutlined,
  ShareAltOutlined,
  HeartOutlined,
  CommentOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { SharedLibraryService, SharedModule, SharedTemplate, LibrarySearchQuery } from '../../services/sharedLibrary';
import { useAuthStore } from '@/store/authStore';
import './SharedLibraryList.css';

const { Search } = Input;
const { Option } = Select;

const SharedLibraryList: React.FC = () => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'modules' | 'templates'>('modules');
  const [modules, setModules] = useState<SharedModule[]>([]);
  const [templates, setTemplates] = useState<SharedTemplate[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  // 搜索状态
  const [searchQuery, setSearchQuery] = useState<LibrarySearchQuery>({
    status: 'approved',
    sort_by: 'created_at',
    sort_order: 'desc',
    page: 1,
    page_size: 20,
    featured_only: false
  });

  // 筛选器显示状态
  const [showFilters, setShowFilters] = useState(false);

  // 加载共享模块
  const loadModules = async (query: LibrarySearchQuery) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedModules(query);
      setModules(response.items);
      setPagination(prev => ({
        ...prev,
        current: query.page || 1,
        total: response.total
      }));
    } catch (error) {
      console.error('加载共享模块失败:', error);
      message.error('加载共享模块失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载共享模板
  const loadTemplates = async (query: LibrarySearchQuery) => {
    setLoading(true);
    try {
      const response = await SharedLibraryService.getSharedTemplates(query);
      setTemplates(response.items);
      setPagination(prev => ({
        ...prev,
        current: query.page || 1,
        total: response.total
      }));
    } catch (error) {
      console.error('加载共享模板失败:', error);
      message.error('加载共享模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    if (activeTab === 'modules') {
      loadModules(searchQuery);
    } else {
      loadTemplates(searchQuery);
    }
  }, [activeTab, searchQuery]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchQuery(prev => ({
      ...prev,
      keyword: value,
      page: 1
    }));
  };

  // 下载模块
  const handleDownloadModule = async (module: SharedModule) => {
    if (!user) {
      message.error('请先登录');
      return;
    }

    try {
      await SharedLibraryService.downloadSharedModule(module.id);
      message.success('下载成功');
      loadModules(searchQuery);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '下载失败');
    }
  };

  // 下载模板
  const handleDownloadTemplate = async (template: SharedTemplate) => {
    if (!user) {
      message.error('请先登录');
      return;
    }

    try {
      await SharedLibraryService.downloadSharedTemplate(template.id);
      message.success('下载成功');
      loadTemplates(searchQuery);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '下载失败');
    }
  };

  // 删除模块
  const handleDeleteModule = async (module: SharedModule) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除模块"${module.name}"吗？`,
      onOk: async () => {
        try {
          await SharedLibraryService.deleteSharedModule(module.id);
          message.success('删除成功');
          loadModules(searchQuery);
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败');
        }
      }
    });
  };

  // 删除模板
  const handleDeleteTemplate = async (template: SharedTemplate) => {
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除模板"${template.name}"吗？`,
      onOk: async () => {
        try {
          await SharedLibraryService.deleteSharedTemplate(template.id);
          message.success('删除成功');
          loadTemplates(searchQuery);
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败');
        }
      }
    });
  };

  // 评分处理
  const handleRating = async (targetType: 'module' | 'template', targetId: string, ratingType: 'like' | 'dislike') => {
    if (!user) {
      message.error('请先登录');
      return;
    }

    try {
      await SharedLibraryService.rateSharedResource({
        target_type: targetType,
        target_id: targetId,
        rating_type: ratingType
      });

      message.success('评分成功');
      // 重新加载数据
      if (activeTab === 'modules') {
        loadModules(searchQuery);
      } else {
        loadTemplates(searchQuery);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '评分失败');
    }
  };

  // 渲染模块卡片
  const renderModuleCard = (module: SharedModule) => (
    <Card
      key={module.id}
      hoverable
      className="shared-item-card"
      cover={
        <div className="card-cover">
          <div className="icon-container">
            <span className="module-icon">{module.icon}</span>
          </div>
          {module.is_featured && (
            <div className="featured-badge">
              <StarOutlined /> 推荐
            </div>
          )}
        </div>
      }
      actions={[
        <Tooltip title="浏览次数">
          <EyeOutlined /> {module.view_count}
        </Tooltip>,
        <Tooltip title="下载">
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadModule(module)}
          >
            {module.download_count}
          </Button>
        </Tooltip>,
        <Tooltip title="点赞">
          <Button
            type="text"
            icon={<LikeOutlined />}
            className={module.user_rating === 'like' ? 'liked' : ''}
            onClick={() => handleRating('module', module.id, 'like')}
          >
            {module.like_count}
          </Button>
        </Tooltip>,
        <Tooltip title="点踩">
          <Button
            type="text"
            icon={<DislikeOutlined />}
            className={module.user_rating === 'dislike' ? 'disliked' : ''}
            onClick={() => handleRating('module', module.id, 'dislike')}
          >
            {module.dislike_count}
          </Button>
        </Tooltip>,
        ...(user && module.uploader_id === user.id ? [
          <Tooltip key="delete" title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteModule(module)}
            >
              删除
            </Button>
          </Tooltip>
        ] : [])
      ]}
    >
      <Card.Meta
        title={
          <div className="item-title">
            <span className="name">{module.name}</span>
            <Tag color="blue">{module.category}</Tag>
          </div>
        }
        description={
          <div className="item-description">
            <p className="description">{module.description}</p>
            <div className="meta-info">
              <span className="uploader">上传者: {module.uploader_name}</span>
              <span className="difficulty">难度: {module.difficulty_level}</span>
              <span className="date">{new Date(module.created_at).toLocaleDateString()}</span>
            </div>
            {module.tags.length > 0 && (
              <div className="tags">
                {module.tags.map(tag => (
                  <Tag key={tag} size="small">{tag}</Tag>
                ))}
              </div>
            )}
          </div>
        }
      />
    </Card>
  );

  // 渲染模板卡片
  const renderTemplateCard = (template: SharedTemplate) => (
    <Card
      key={template.id}
      hoverable
      className="shared-item-card"
      cover={
        <div className="card-cover">
          <div className="icon-container">
            <span className="template-icon">📋</span>
          </div>
          {template.is_featured && (
            <div className="featured-badge">
              <StarOutlined /> 推荐
            </div>
          )}
        </div>
      }
      actions={[
        <Tooltip title="浏览次数">
          <EyeOutlined /> {template.view_count}
        </Tooltip>,
        <Tooltip title="下载">
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadTemplate(template)}
          >
            {template.download_count}
          </Button>
        </Tooltip>,
        <Tooltip title="点赞">
          <Button
            type="text"
            icon={<LikeOutlined />}
            className={template.user_rating === 'like' ? 'liked' : ''}
            onClick={() => handleRating('template', template.id, 'like')}
          >
            {template.like_count}
          </Button>
        </Tooltip>,
        <Tooltip title="点踩">
          <Button
            type="text"
            icon={<DislikeOutlined />}
            className={template.user_rating === 'dislike' ? 'disliked' : ''}
            onClick={() => handleRating('template', template.id, 'dislike')}
          >
            {template.dislike_count}
          </Button>
        </Tooltip>,
        ...(user && template.uploader_id === user.id ? [
          <Tooltip key="delete" title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteTemplate(template)}
            >
              删除
            </Button>
          </Tooltip>
        ] : [])
      ]}
    >
      <Card.Meta
        title={
          <div className="item-title">
            <span className="name">{template.name}</span>
            {template.welding_process && <Tag color="green">{template.welding_process_name}</Tag>}
            {template.standard && <Tag color="orange">{template.standard}</Tag>}
          </div>
        }
        description={
          <div className="item-description">
            <p className="description">{template.description}</p>
            <div className="meta-info">
              <span className="uploader">上传者: {template.uploader_name}</span>
              <span className="difficulty">难度: {template.difficulty_level}</span>
              <span className="date">{new Date(template.created_at).toLocaleDateString()}</span>
            </div>
            {template.industry_type && (
              <div className="industry-type">
                <Tag color="purple">行业: {template.industry_type}</Tag>
              </div>
            )}
            {template.tags.length > 0 && (
              <div className="tags">
                {template.tags.map(tag => (
                  <Tag key={tag} size="small">{tag}</Tag>
                ))}
              </div>
            )}
          </div>
        }
      />
    </Card>
  );

  // 定义Tab items
  const tabItems = [
    {
      key: 'modules',
      label: (
        <span>
          <i className="module-tab-icon">🧩</i>
          共享模块
          <Badge count={modules.length} showZero={false} />
        </span>
      ),
      children: (
        <Spin spinning={loading}>
          {modules.length === 0 ? (
            <Empty description="暂无共享模块" />
          ) : (
            <Row gutter={[16, 16]}>
              {modules.map(module => (
                <Col xs={24} sm={12} md={8} lg={6} key={module.id}>
                  {renderModuleCard(module)}
                </Col>
              ))}
            </Row>
          )}
        </Spin>
      )
    },
    {
      key: 'templates',
      label: (
        <span>
          <i className="template-tab-icon">📋</i>
          共享模板
          <Badge count={templates.length} showZero={false} />
        </span>
      ),
      children: (
        <Spin spinning={loading}>
          {templates.length === 0 ? (
            <Empty description="暂无共享模板" />
          ) : (
            <Row gutter={[16, 16]}>
              {templates.map(template => (
                <Col xs={24} sm={12} md={8} lg={6} key={template.id}>
                  {renderTemplateCard(template)}
                </Col>
              ))}
            </Row>
          )}
        </Spin>
      )
    }
  ];

  // 筛选处理
  const handleFilterChange = (key: string, value: any) => {
    setSearchQuery(prev => ({
      ...prev,
      [key]: value,
      page: 1
    }));
  };

  // 分页处理
  const handlePageChange = (page: number, pageSize?: number) => {
    setSearchQuery(prev => ({
      ...prev,
      page,
      page_size: pageSize || prev.page_size
    }));
  };

  // 排序处理
  const handleSortChange = (value: string) => {
    const [sort_by, sort_order] = value.split('_');
    setSearchQuery(prev => ({
      ...prev,
      sort_by,
      sort_order,
      page: 1
    }));
  };

  return (
    <div className="shared-library-list">
      <div className="search-section">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Search
              placeholder="搜索模块或模板..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              onSearch={handleSearch}
            />
          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Button
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(!showFilters)}
              >
                筛选
              </Button>
              <Select
                placeholder="排序方式"
                style={{ width: 150 }}
                value={`${searchQuery.sort_by}_${searchQuery.sort_order}`}
                onChange={handleSortChange}
              >
                <Option value="created_at_desc">最新发布</Option>
                <Option value="created_at_asc">最早发布</Option>
                <Option value="download_count_desc">下载最多</Option>
                <Option value="like_count_desc">点赞最多</Option>
                <Option value="name_asc">名称 A-Z</Option>
                <Option value="name_desc">名称 Z-A</Option>
              </Select>
            </Space>
          </Col>
        </Row>

        {showFilters && (
          <div className="filters-panel">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8} md={6}>
                <Select
                  placeholder="分类"
                  style={{ width: '100%' }}
                  allowClear
                  onChange={(value) => handleFilterChange('category', value)}
                >
                  <Option value="basic">基础</Option>
                  <Option value="material">材料</Option>
                  <Option value="gas">气体</Option>
                  <Option value="electrical">电气</Option>
                  <Option value="motion">运动</Option>
                  <Option value="equipment">设备</Option>
                  <Option value="calculation">计算</Option>
                </Select>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <Select
                  placeholder="难度等级"
                  style={{ width: '100%' }}
                  allowClear
                  onChange={(value) => handleFilterChange('difficulty_level', value)}
                >
                  <Option value="beginner">初级</Option>
                  <Option value="intermediate">中级</Option>
                  <Option value="advanced">高级</Option>
                </Select>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <Select
                  placeholder="焊接工艺"
                  style={{ width: '100%' }}
                  allowClear
                  onChange={(value) => handleFilterChange('welding_process', value)}
                >
                  <Option value="111">手工电弧焊</Option>
                  <Option value="114">埋弧焊</Option>
                  <Option value="121">钨极氩弧焊</Option>
                  <Option value="135">熔化极氩弧焊</Option>
                  <Option value="141">钨极氩弧焊</Option>
                  <Option value="15">气焊</Option>
                  <Option value="311">气割</Option>
                </Select>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <Button
                  type={searchQuery.featured_only ? 'primary' : 'default'}
                  icon={<StarOutlined />}
                  onClick={() => handleFilterChange('featured_only', !searchQuery.featured_only)}
                >
                  仅显示推荐
                </Button>
              </Col>
            </Row>
          </div>
        )}
      </div>

      <div className="content-section">
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as 'modules' | 'templates')}
          items={tabItems}
        />

        {pagination.total > pagination.pageSize && (
          <div className="pagination-wrapper">
            <Pagination
              current={pagination.current}
              pageSize={pagination.pageSize}
              total={pagination.total}
              showSizeChanger
              showQuickJumper
              showTotal={(total, range) => `${range[0]}-${range[1]} 共 ${total} 条`}
              onChange={handlePageChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default SharedLibraryList;