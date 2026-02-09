"""
共享库相关的 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# 导入模块实例定义
from app.schemas.wps_template import ModuleInstance


class SharedModuleBase(BaseModel):
    """共享模块基础 schema"""
    name: str = Field(..., min_length=1, max_length=200, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    icon: str = Field(default="BlockOutlined", description="模块图标")
    module_type: str = Field(default="wps", description="模块类型: wps/pqr/ppqr/common")
    category: str = Field(default="basic", description="模块分类")
    repeatable: bool = Field(default=False, description="是否可重复")
    fields: Dict[str, Any] = Field(default={}, description="字段定义")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    difficulty_level: str = Field(default="beginner", description="难度等级")


class SharedModuleCreate(SharedModuleBase):
    """创建共享模块 schema"""
    original_module_id: str = Field(..., description="原始模块ID")
    changelog: Optional[str] = Field(None, description="版本更新日志")


class SharedModuleUpdate(BaseModel):
    """更新共享模块 schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = None
    module_type: Optional[str] = None
    category: Optional[str] = None
    repeatable: Optional[bool] = None
    fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    changelog: Optional[str] = None


class SharedModuleInDB(SharedModuleBase):
    """数据库中的共享模块 schema"""
    id: str
    original_module_id: str
    uploader_id: int
    upload_time: datetime
    version: str
    changelog: Optional[str]
    download_count: int
    like_count: int
    dislike_count: int
    view_count: int
    status: str
    reviewer_id: Optional[int]
    review_time: Optional[datetime]
    review_comment: Optional[str]
    is_featured: bool
    featured_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SharedModule(SharedModuleInDB):
    """共享模块响应 schema"""
    uploader_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    user_rating: Optional[str] = None  # 当前用户的评分: like, dislike, null


class SharedTemplateBase(BaseModel):
    """共享模板基础 schema"""
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    module_type: str = Field(default="wps", description="模块类型: wps/pqr/ppqr")
    welding_process: Optional[str] = Field(None, description="焊接工艺")
    welding_process_name: Optional[str] = Field(None, description="焊接工艺名称")
    standard: Optional[str] = Field(None, description="焊接标准")
    module_instances: List[ModuleInstance] = Field(..., description="模块实例列表")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    difficulty_level: str = Field(default="beginner", description="难度等级")
    industry_type: Optional[str] = Field(None, description="行业类型")


class SharedTemplateCreate(SharedTemplateBase):
    """创建共享模板 schema"""
    original_template_id: str = Field(..., description="原始模板ID")
    changelog: Optional[str] = Field(None, description="版本更新日志")


class SharedTemplateUpdate(BaseModel):
    """更新共享模板 schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    module_type: Optional[str] = None
    welding_process: Optional[str] = None
    welding_process_name: Optional[str] = None
    standard: Optional[str] = None
    module_instances: Optional[List[ModuleInstance]] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[str] = None
    industry_type: Optional[str] = None
    changelog: Optional[str] = None


class SharedTemplateInDB(SharedTemplateBase):
    """数据库中的共享模板 schema"""
    id: str
    original_template_id: str
    uploader_id: int
    upload_time: datetime
    version: str
    changelog: Optional[str]
    download_count: int
    like_count: int
    dislike_count: int
    view_count: int
    status: str
    reviewer_id: Optional[int]
    review_time: Optional[datetime]
    review_comment: Optional[str]
    is_featured: bool
    featured_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SharedTemplate(SharedTemplateInDB):
    """共享模板响应 schema"""
    uploader_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    user_rating: Optional[str] = None  # 当前用户的评分


class UserRatingBase(BaseModel):
    """用户评分基础 schema"""
    rating_type: str = Field(..., pattern="^(like|dislike)$", description="评分类型")


class UserRatingCreate(UserRatingBase):
    """创建用户评分 schema"""
    target_type: str = Field(..., pattern="^(module|template)$", description="评分对象类型")
    target_id: str = Field(..., description="评分对象ID")


class UserRatingInDB(UserRatingBase):
    """数据库中的用户评分 schema"""
    id: str
    user_id: int
    target_type: str
    target_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SharedDownloadBase(BaseModel):
    """下载记录基础 schema"""
    target_type: str = Field(..., pattern="^(module|template)$", description="下载对象类型")
    target_id: str = Field(..., description="下载对象ID")


class SharedDownloadInDB(SharedDownloadBase):
    """数据库中的下载记录 schema"""
    id: str
    user_id: int
    download_time: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class SharedCommentBase(BaseModel):
    """评论基础 schema"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parent_id: Optional[str] = Field(None, description="父评论ID（用于回复）")


class SharedCommentCreate(SharedCommentBase):
    """创建评论 schema"""
    target_type: str = Field(..., pattern="^(module|template)$", description="评论对象类型")
    target_id: str = Field(..., description="评论对象ID")


class SharedCommentUpdate(BaseModel):
    """更新评论 schema"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000)


class SharedCommentInDB(SharedCommentBase):
    """数据库中的评论 schema"""
    id: str
    user_id: int
    target_type: str
    target_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SharedComment(SharedCommentInDB):
    """评论响应 schema"""
    user_name: Optional[str] = None
    replies: Optional[List["SharedComment"]] = []


class ReviewAction(BaseModel):
    """审核操作 schema"""
    status: str = Field(..., pattern="^(approved|rejected|removed)$", description="审核结果")
    review_comment: Optional[str] = Field(None, description="审核意见")


class FeaturedAction(BaseModel):
    """推荐操作 schema"""
    is_featured: bool = Field(..., description="是否推荐")
    featured_order: Optional[int] = Field(0, description="推荐排序")


class LibraryStats(BaseModel):
    """共享库统计信息 schema"""
    total_modules: int = Field(..., description="总模块数")
    total_templates: int = Field(..., description="总模板数")
    approved_modules: int = Field(..., description="已审核模块数")
    approved_templates: int = Field(..., description="已审核模板数")
    pending_modules: int = Field(..., description="待审核模块数")
    pending_templates: int = Field(..., description="待审核模板数")
    total_downloads: int = Field(..., description="总下载数")
    total_ratings: int = Field(..., description="总评分数")


class LibrarySearchQuery(BaseModel):
    """共享库搜索查询 schema"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类筛选")
    difficulty_level: Optional[str] = Field(None, description="难度筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    status: Optional[str] = Field(None, description="状态筛选，None表示查询所有状态")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    featured_only: bool = Field(default=False, description="只显示推荐内容")


# 解决前向引用问题
SharedComment.model_rebuild()