"""
共享库模型 - 用于管理用户共享的模块和模板
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, CheckConstraint, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class SharedModule(Base):
    """共享模块模型 - 用户上传到共享库的自定义模块"""
    __tablename__ = "shared_modules"

    id = Column(String(100), primary_key=True, index=True)
    # 修改为 SET NULL：当用户删除原始模块时，共享库中的副本不应被删除
    # 共享库中的模块是独立的副本，应该保持独立性
    original_module_id = Column(String(100), ForeignKey('custom_modules.id', ondelete='SET NULL'), nullable=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default='BlockOutlined')

    # 模块类型：wps, pqr, ppqr, common
    module_type = Column(String(20), nullable=False, default='wps', index=True)

    category = Column(String(20), default='basic')
    repeatable = Column(Boolean, default=False)

    # 字段定义（JSONB格式）
    fields = Column(JSONB, nullable=False, default={})

    # 共享信息
    uploader_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    # 版本信息
    version = Column(String(20), default="1.0")
    changelog = Column(Text)  # 版本更新日志

    # 统计信息
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    dislike_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # 状态管理
    status = Column(String(20), default="pending")  # pending, approved, rejected, removed
    reviewer_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    review_time = Column(DateTime(timezone=True))
    review_comment = Column(Text)

    # 推荐标记
    is_featured = Column(Boolean, default=False)
    featured_order = Column(Integer, default=0)

    # 标签和分类
    tags = Column(JSONB, default=[])  # 标签列表
    difficulty_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'removed')",
            name='check_shared_module_status'
        ),
        CheckConstraint(
            "category IN ('basic', 'material', 'gas', 'electrical', 'motion', 'equipment', 'calculation')",
            name='check_shared_module_category'
        ),
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name='check_difficulty_level'
        ),
    )


class SharedTemplate(Base):
    """共享模板模型 - 用户上传到共享库的WPS模板"""
    __tablename__ = "shared_templates"

    id = Column(String(100), primary_key=True, index=True)
    # 修改为 SET NULL：当用户删除原始模板时，共享库中的副本不应被删除
    # 共享库中的模板是独立的副本，应该保持独立性
    original_template_id = Column(String(100), ForeignKey('wps_templates.id', ondelete='SET NULL'), nullable=True)

    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 模块类型：wps, pqr, ppqr
    module_type = Column(String(20), nullable=False, default='wps', index=True)

    # 适用范围
    welding_process = Column(String(50), nullable=True, index=True)
    welding_process_name = Column(String(100))
    standard = Column(String(50), index=True)

    # 模板配置（JSONB）
    module_instances = Column(JSONB, nullable=False)

    # 共享信息
    uploader_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    # 版本信息
    version = Column(String(20), default="1.0")
    changelog = Column(Text)

    # 统计信息
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    dislike_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # 状态管理
    status = Column(String(20), default="pending")
    reviewer_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    review_time = Column(DateTime(timezone=True))
    review_comment = Column(Text)

    # 推荐标记
    is_featured = Column(Boolean, default=False)
    featured_order = Column(Integer, default=0)

    # 标签和分类
    tags = Column(JSONB, default=[])
    difficulty_level = Column(String(20), default="beginner")
    industry_type = Column(String(50))  # 行业类型：造船、压力容器、建筑等

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'removed')",
            name='check_shared_template_status'
        ),
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name='check_shared_template_difficulty'
        ),
    )


class UserRating(Base):
    """用户评分模型 - 记录用户对共享模块/模板的点赞点踩"""
    __tablename__ = "user_ratings"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # 评分对象
    target_type = Column(String(20), nullable=False)  # module 或 template
    target_id = Column(String(100), nullable=False)

    # 评分类型
    rating_type = Column(String(10), nullable=False)  # like 或 dislike

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint(
            "rating_type IN ('like', 'dislike')",
            name='check_rating_type'
        ),
        CheckConstraint(
            "target_type IN ('module', 'template')",
            name='check_target_type'
        ),
    )


class SharedDownload(Base):
    """下载记录模型 - 记录用户下载共享资源的历史"""
    __tablename__ = "shared_downloads"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # 下载对象
    target_type = Column(String(20), nullable=False)  # module 或 template
    target_id = Column(String(100), nullable=False)

    # 下载信息
    download_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # 支持IPv6

    # 约束
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('module', 'template')",
            name='check_download_target_type'
        ),
    )


class SharedComment(Base):
    """评论模型 - 用户对共享资源的评论"""
    __tablename__ = "shared_comments"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # 评论对象
    target_type = Column(String(20), nullable=False)  # module 或 template
    target_id = Column(String(100), nullable=False)

    # 评论内容
    content = Column(Text, nullable=False)
    parent_id = Column(String(100), ForeignKey('shared_comments.id', ondelete='CASCADE'))  # 回复评论

    # 状态
    status = Column(String(20), default="active")  # active, hidden, deleted

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('module', 'template')",
            name='check_comment_target_type'
        ),
        CheckConstraint(
            "status IN ('active', 'hidden', 'deleted')",
            name='check_comment_status'
        ),
    )