# 共享库功能实现指南

## 功能概述

共享库功能允许用户将自己创建的自定义模块和WPS模板分享到服务器平台的模块库和模板库，其他有权限的用户可以从共享库下载这些资源使用。这有助于促进行业标准化和知识分享。

## 核心功能

### 1. 资源共享
- **模块共享**: 用户可以将自定义模块复制到共享库
- **模板共享**: 用户可以将WPS模板复制到共享库
- **版本管理**: 支持版本控制和更新日志

### 2. 资源浏览与搜索
- **关键词搜索**: 支持按名称和描述搜索
- **分类筛选**: 按模块分类、焊接工艺、标准等筛选
- **难度筛选**: 按初级、中级、高级筛选
- **标签系统**: 支持自定义标签分类
- **排序功能**: 支持按时间、下载量、点赞数等排序

### 3. 用户互动
- **点赞/点踩**: 用户可以对资源进行评价
- **评论系统**: 支持对资源进行评论和回复
- **下载统计**: 记录资源下载次数
- **浏览统计**: 记录资源浏览次数

### 4. 管理功能
- **审核机制**: 管理员可以审核用户提交的资源
- **推荐系统**: 管理员可以设置推荐资源
- **统计面板**: 提供详细的共享库统计信息
- **权限控制**: 基于用户角色的权限管理

## 数据库设计

### 核心表结构

1. **shared_modules** - 共享模块表
2. **shared_templates** - 共享模板表
3. **user_ratings** - 用户评分表
4. **shared_downloads** - 下载记录表
5. **shared_comments** - 评论表

### 关键字段

- **status**: 资源状态 (pending/approved/rejected/removed)
- **is_featured**: 是否推荐
- **download_count**: 下载次数
- **like_count**: 点赞数
- **dislike_count**: 点踩数
- **view_count**: 浏览次数

## API 接口

### 模块相关接口

```
POST /api/v1/shared-library/modules/share    # 共享模块
GET  /api/v1/shared-library/modules          # 获取模块列表
GET  /api/v1/shared-library/modules/{id}     # 获取模块详情
POST /api/v1/shared-library/modules/{id}/download  # 下载模块
PUT  /api/v1/shared-library/modules/{id}     # 更新模块信息
```

### 模板相关接口

```
POST /api/v1/shared-library/templates/share  # 共享模板
GET  /api/v1/shared-library/templates        # 获取模板列表
GET  /api/v1/shared-library/templates/{id}   # 获取模板详情
POST /api/v1/shared-library/templates/{id}/download  # 下载模板
PUT  /api/v1/shared-library/templates/{id}   # 更新模板信息
```

### 互动接口

```
POST /api/v1/shared-library/rate             # 评分(点赞/点踩)
POST /api/v1/shared-library/comments         # 创建评论
GET  /api/v1/shared-library/comments/{type}/{id}  # 获取评论列表
```

### 管理员接口

```
POST /api/v1/shared-library/admin/review/{type}/{id}     # 审核资源
POST /api/v1/shared-library/admin/featured/{type}/{id}   # 设置推荐
GET  /api/v1/shared-library/admin/stats                   # 获取统计
GET  /api/v1/shared-library/admin/pending/{type}          # 获取待审核资源
```

## 前端页面

### 1. 共享库列表页面 (`/shared-library`)
- 资源浏览和搜索
- 筛选和排序功能
- 资源卡片展示
- 下载和评分功能

### 2. 管理端页面 (`/admin/shared-library`)
- 待审核资源管理
- 统计信息面板
- 推荐设置
- 资源状态管理

## 使用流程

### 用户共享资源流程

1. **创建资源**: 用户先在自己的工作区创建自定义模块或WPS模板
2. **分享资源**: 点击分享按钮，填写共享信息（描述、标签、难度等）
3. **等待审核**: 资源提交后进入待审核状态
4. **审核通过**: 管理员审核通过后，资源出现在共享库中
5. **获得反馈**: 其他用户可以下载、点赞、评论资源

### 用户下载资源流程

1. **浏览资源**: 在共享库中浏览和搜索需要的资源
2. **查看详情**: 查看资源的详细信息、评价和评论
3. **下载资源**: 点击下载按钮，资源复制到用户的工作区
4. **使用资源**: 在自己的项目中使用下载的资源
5. **评价资源**: 对资源进行点赞、点踩或评论

### 管理员审核流程

1. **查看待审核**: 在管理后台查看待审核的资源
2. **审核资源**: 查看资源详情，决定通过或拒绝
3. **添加意见**: 可以添加审核意见
4. **设置推荐**: 对优质资源设置推荐
5. **监控统计**: 查看共享库的使用统计

## 安装和部署

### 1. 数据库迁移

```bash
# 执行数据库迁移脚本
cd backend
psql -d your_database -f migrations/create_shared_library_tables.sql
```

### 2. 后端部署

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 或构建生产版本
npm run build
```

## 测试

### 快速测试

```bash
cd backend
python quick_test_shared_library.py
```

### 完整测试

```bash
cd backend
python test_shared_library.py
```

## 配置说明

### 权限配置

- **普通用户**: 可以下载、评分、评论资源
- **认证用户**: 可以上传自己的资源
- **管理员**: 可以审核资源、设置推荐、查看统计

### 审核配置

- **自动审核**: 可以配置某些分类的资源自动通过审核
- **审核通知**: 可以配置审核结果通知
- **审核规则**: 可以设置审核标准和规则

## 扩展功能

### 计划中的功能

1. **资源版本管理**: 支持资源的多版本管理
2. **资源收藏**: 用户可以收藏喜欢的资源
3. **资源举报**: 用户可以举报不当内容
4. **资源推荐算法**: 基于用户行为的智能推荐
5. **资源质量评分**: 基于多个维度的质量评分系统
6. **API接口**: 开放API供第三方使用
7. **资源导出**: 支持导出资源为多种格式

### 性能优化

1. **缓存机制**: 对热门资源进行缓存
2. **CDN加速**: 对资源文件进行CDN分发
3. **搜索优化**: 使用Elasticsearch优化搜索
4. **图片优化**: 对资源图片进行压缩和优化

## 注意事项

1. **数据安全**: 确保用户数据的安全和隐私
2. **版权保护**: 明确资源的版权和使用权
3. **内容审核**: 加强内容审核，防止不当内容
4. **性能监控**: 监控系统性能，及时优化
5. **用户反馈**: 收集用户反馈，持续改进功能

## 故障排除

### 常见问题

1. **导入错误**: 检查Python路径和模块安装
2. **数据库错误**: 检查数据库连接和表结构
3. **权限错误**: 检查用户角色和权限配置
4. **API错误**: 检查API路由和参数配置

### 调试技巧

1. 查看日志文件了解详细错误信息
2. 使用数据库工具检查数据完整性
3. 使用Postman测试API接口
4. 使用浏览器开发者工具调试前端

---

## 联系支持

如有问题或建议，请联系开发团队或提交Issue。