"""
共享库服务层 - 重新加载
"""
import uuid
import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from fastapi import HTTPException, status

from app.models.shared_library import (
    SharedModule, SharedTemplate, UserRating, SharedDownload, SharedComment
)
from app.models.custom_module import CustomModule
from app.models.wps_template import WPSTemplate
from app.models.user import User
from app.schemas.shared_library import (
    SharedModuleCreate, SharedModuleUpdate, SharedTemplateCreate, SharedTemplateUpdate,
    UserRatingCreate, SharedCommentCreate, LibrarySearchQuery, ReviewAction, FeaturedAction
)


class SharedLibraryService:
    """共享库服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 共享模块相关方法 ====================

    def create_shared_module(self, module_data: SharedModuleCreate, uploader_id: int) -> SharedModule:
        """创建共享模块 - 完整复制原始模块的所有字段"""
        # 验证原始模块是否存在且属于当前用户
        original_module = self.db.query(CustomModule).filter(
            and_(
                CustomModule.id == module_data.original_module_id,
                CustomModule.user_id == uploader_id
            )
        ).first()

        if not original_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="原始模块不存在或无权限访问"
            )

        # 检查是否已经共享过
        existing_shared = self.db.query(SharedModule).filter(
            SharedModule.original_module_id == module_data.original_module_id
        ).first()

        if existing_shared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该模块已经共享过了"
            )

        # 创建共享模块 - 完整复制原始模块的所有字段
        shared_module = SharedModule(
            id=str(uuid.uuid4()),
            original_module_id=module_data.original_module_id,
            # 从原始模块复制所有字段，确保数据完整性
            name=original_module.name,
            description=original_module.description,
            icon=original_module.icon,
            module_type=original_module.module_type,  # 复制模块类型
            category=original_module.category,
            repeatable=original_module.repeatable,
            fields=original_module.fields,  # 完整复制JSONB字段
            # 共享信息
            uploader_id=uploader_id,
            version="1.0",
            changelog=module_data.changelog if hasattr(module_data, 'changelog') else None,
            # 统计信息
            download_count=0,
            like_count=0,
            dislike_count=0,
            view_count=0,
            # 状态管理 - 默认为已审核通过
            status="approved",
            # 标签和分类
            tags=module_data.tags if hasattr(module_data, 'tags') else [],
            difficulty_level=module_data.difficulty_level if hasattr(module_data, 'difficulty_level') else "beginner",
            # 推荐标记
            is_featured=False,
            featured_order=0
        )

        self.db.add(shared_module)
        self.db.commit()
        self.db.refresh(shared_module)
        return shared_module

    def get_shared_modules(self, query: LibrarySearchQuery, user_id: Optional[int] = None) -> Tuple[List[SharedModule], int]:
        """获取共享模块列表"""
        # 构建查询
        db_query = self.db.query(SharedModule)

        # 状态筛选
        if query.status:
            db_query = db_query.filter(SharedModule.status == query.status)

        # 关键词搜索
        if query.keyword:
            search_filter = or_(
                SharedModule.name.ilike(f"%{query.keyword}%"),
                SharedModule.description.ilike(f"%{query.keyword}%")
            )
            db_query = db_query.filter(search_filter)

        # 分类筛选
        if query.category:
            db_query = db_query.filter(SharedModule.category == query.category)

        # 难度筛选
        if query.difficulty_level:
            db_query = db_query.filter(SharedModule.difficulty_level == query.difficulty_level)

        # 标签筛选
        if query.tags:
            for tag in query.tags:
                db_query = db_query.filter(SharedModule.tags.contains([tag]))

        # 推荐筛选
        if query.featured_only:
            db_query = db_query.filter(
                and_(
                    SharedModule.is_featured == True,
                    SharedModule.status == "approved"
                )
            )

        # 统计总数
        total = db_query.count()

        # 排序
        if query.sort_by == "created_at":
            order_col = SharedModule.created_at
        elif query.sort_by == "download_count":
            order_col = SharedModule.download_count
        elif query.sort_by == "like_count":
            order_col = SharedModule.like_count
        elif query.sort_by == "name":
            order_col = SharedModule.name
        else:
            order_col = SharedModule.created_at

        if query.sort_order == "desc":
            db_query = db_query.order_by(desc(order_col))
        else:
            db_query = db_query.order_by(asc(order_col))

        # 分页
        offset = (query.page - 1) * query.page_size
        modules = db_query.offset(offset).limit(query.page_size).all()

        # 添加用户名信息
        from app.models.user import User
        uploader_ids = list(set([m.uploader_id for m in modules]))
        reviewer_ids = list(set([m.reviewer_id for m in modules if m.reviewer_id]))

        # 查询上传者和审核者信息
        uploaders = {}
        if uploader_ids:
            uploader_users = self.db.query(User).filter(User.id.in_(uploader_ids)).all()
            uploaders = {u.id: u.username or u.email for u in uploader_users}

        reviewers = {}
        if reviewer_ids:
            reviewer_users = self.db.query(User).filter(User.id.in_(reviewer_ids)).all()
            reviewers = {u.id: u.username or u.email for u in reviewer_users}

        # 为每个模块添加用户名
        for module in modules:
            module.uploader_name = uploaders.get(module.uploader_id)
            module.reviewer_name = reviewers.get(module.reviewer_id) if module.reviewer_id else None

        # 如果提供了用户ID，查询用户的评分
        if user_id:
            module_ids = [m.id for m in modules]
            user_ratings = self.db.query(UserRating).filter(
                and_(
                    UserRating.user_id == user_id,
                    UserRating.target_type == "module",
                    UserRating.target_id.in_(module_ids)
                )
            ).all()

            rating_map = {r.target_id: r.rating_type for r in user_ratings}
            for module in modules:
                module.user_rating = rating_map.get(module.id)

        return modules, total

    def get_shared_module_by_id(self, module_id: str, user_id: Optional[int] = None) -> Optional[SharedModule]:
        """根据ID获取共享模块"""
        module = self.db.query(SharedModule).filter(SharedModule.id == module_id).first()

        if module:
            # 添加用户名信息
            from app.models.user import User
            if module.uploader_id:
                uploader = self.db.query(User).filter(User.id == module.uploader_id).first()
                module.uploader_name = uploader.username or uploader.email if uploader else None
            if module.reviewer_id:
                reviewer = self.db.query(User).filter(User.id == module.reviewer_id).first()
                module.reviewer_name = reviewer.username or reviewer.email if reviewer else None

            if user_id:
                # 增加浏览次数
                module.view_count += 1
                self.db.commit()

                # 查询用户评分
                rating = self.db.query(UserRating).filter(
                    and_(
                        UserRating.user_id == user_id,
                        UserRating.target_type == "module",
                        UserRating.target_id == module_id
                    )
                ).first()
                module.user_rating = rating.rating_type if rating else None

        return module

    def download_shared_module(self, module_id: str, user_id: int, ip_address: Optional[str] = None, workspace_type: str = "personal", company_id: Optional[int] = None, factory_id: Optional[int] = None) -> Dict[str, Any]:
        """下载共享模块 - 完整复制到用户工作区"""
        shared_module = self.get_shared_module_by_id(module_id)
        if not shared_module or shared_module.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享模块不存在或未通过审核"
            )

        # 检查用户是否已经有同名同类型的模块
        # 注意: 需要同时检查 name 和 module_type,因为不同类型的模块可以同名
        existing_module = self.db.query(CustomModule).filter(
            and_(
                CustomModule.user_id == user_id,
                CustomModule.workspace_type == workspace_type,
                CustomModule.company_id == company_id,
                CustomModule.factory_id == factory_id,
                CustomModule.name == shared_module.name,
                CustomModule.module_type == shared_module.module_type  # 同时检查模块类型
            )
        ).first()

        if existing_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"您的工作区中已存在名为 '{shared_module.name}' 的 {shared_module.module_type} 类型模块"
            )

        # 创建新的模块实例 - 完整复制共享模块的所有字段
        new_module = CustomModule(
            id=str(uuid.uuid4()),
            # 完整复制所有字段，确保数据完整性
            name=shared_module.name,
            description=shared_module.description,
            icon=shared_module.icon,
            module_type=shared_module.module_type,  # 复制模块类型
            category=shared_module.category,
            repeatable=shared_module.repeatable,
            fields=shared_module.fields,  # 完整复制JSONB字段
            # 工作区信息
            user_id=user_id,
            workspace_type=workspace_type,
            company_id=company_id,
            factory_id=factory_id,
            # 访问控制
            is_shared=False,
            access_level="private",
            # 统计信息
            usage_count=0
        )

        self.db.add(new_module)

        # 记录下载
        download_record = SharedDownload(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_type="module",
            target_id=module_id,
            ip_address=ip_address
        )
        self.db.add(download_record)

        # 增加下载次数
        shared_module.download_count += 1

        self.db.commit()
        self.db.refresh(new_module)

        return {
            "message": "模块下载成功",
            "module": {
                "id": new_module.id,
                "name": new_module.name,
                "description": new_module.description,
                "icon": new_module.icon,
                "category": new_module.category,
                "repeatable": new_module.repeatable,
                "fields": new_module.fields,
                "workspace_type": new_module.workspace_type,
                "created_at": new_module.created_at
            },
            "shared_info": {
                "shared_id": shared_module.id,
                "shared_name": shared_module.name,
                "uploader_id": shared_module.uploader_id,
                "version": shared_module.version,
                "download_count": shared_module.download_count
            }
        }

    # ==================== 共享模板相关方法 ====================

    def create_shared_template(self, template_data: SharedTemplateCreate, uploader_id: int) -> SharedTemplate:
        """创建共享模板 - 完整复制原始模板的所有字段"""
        # 验证原始模板是否存在且属于当前用户
        original_template = self.db.query(WPSTemplate).filter(
            and_(
                WPSTemplate.id == template_data.original_template_id,
                WPSTemplate.user_id == uploader_id
            )
        ).first()

        if not original_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="原始模板不存在或无权限访问"
            )

        # 检查是否已经共享过
        existing_shared = self.db.query(SharedTemplate).filter(
            SharedTemplate.original_template_id == template_data.original_template_id
        ).first()

        if existing_shared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该模板已经共享过了"
            )

        # 创建共享模板 - 完整复制原始模板的所有字段
        shared_template = SharedTemplate(
            id=str(uuid.uuid4()),
            original_template_id=template_data.original_template_id,
            # 从原始模板复制所有字段，确保数据完整性
            name=original_template.name,
            description=original_template.description,
            module_type=original_template.module_type,  # 复制模块类型
            welding_process=original_template.welding_process,
            welding_process_name=original_template.welding_process_name,
            standard=original_template.standard,
            module_instances=original_template.module_instances,  # 完整复制JSONB字段
            # 共享信息
            uploader_id=uploader_id,
            version="1.0",
            changelog=template_data.changelog if hasattr(template_data, 'changelog') else None,
            # 统计信息
            download_count=0,
            like_count=0,
            dislike_count=0,
            view_count=0,
            # 状态管理 - 默认为已审核通过
            status="approved",
            # 标签和分类
            tags=template_data.tags if hasattr(template_data, 'tags') else [],
            difficulty_level=template_data.difficulty_level if hasattr(template_data, 'difficulty_level') else "beginner",
            industry_type=template_data.industry_type if hasattr(template_data, 'industry_type') else None,
            # 推荐标记
            is_featured=False,
            featured_order=0
        )

        self.db.add(shared_template)
        self.db.commit()
        self.db.refresh(shared_template)
        return shared_template

    def get_shared_templates(self, query: LibrarySearchQuery, user_id: Optional[int] = None) -> Tuple[List[SharedTemplate], int]:
        """获取共享模板列表 - 使用ORM查询"""
        # 构建基础查询
        db_query = self.db.query(SharedTemplate)

        # 状态筛选
        if query.status:
            db_query = db_query.filter(SharedTemplate.status == query.status)

        # 关键词搜索
        if query.keyword:
            keyword_filter = or_(
                SharedTemplate.name.ilike(f"%{query.keyword}%"),
                SharedTemplate.description.ilike(f"%{query.keyword}%")
            )
            db_query = db_query.filter(keyword_filter)

        # 焊接工艺筛选
        if hasattr(query, 'welding_process') and query.welding_process:
            db_query = db_query.filter(SharedTemplate.welding_process == query.welding_process)

        # 标准筛选
        if hasattr(query, 'standard') and query.standard:
            db_query = db_query.filter(SharedTemplate.standard == query.standard)

        # 推荐筛选
        if hasattr(query, 'is_featured') and query.is_featured is not None:
            db_query = db_query.filter(SharedTemplate.is_featured == query.is_featured)

        # 难度筛选
        if hasattr(query, 'difficulty_level') and query.difficulty_level:
            db_query = db_query.filter(SharedTemplate.difficulty_level == query.difficulty_level)

        # 统计总数
        total = db_query.count()

        # 排序
        if query.sort_by:
            sort_field = getattr(SharedTemplate, query.sort_by, None)
            if sort_field is not None:
                if query.sort_order == "asc":
                    db_query = db_query.order_by(sort_field.asc())
                else:
                    db_query = db_query.order_by(sort_field.desc())
        else:
            # 默认按创建时间降序，推荐的排在前面
            db_query = db_query.order_by(
                SharedTemplate.is_featured.desc(),
                SharedTemplate.featured_order.asc(),
                SharedTemplate.created_at.desc()
            )

        # 分页
        if query.page and query.page_size:
            offset = (query.page - 1) * query.page_size
            db_query = db_query.offset(offset).limit(query.page_size)

        # 执行查询
        templates = db_query.all()

        # 添加用户名信息
        from app.models.user import User
        uploader_ids = list(set([t.uploader_id for t in templates]))
        reviewer_ids = list(set([t.reviewer_id for t in templates if t.reviewer_id]))

        # 查询上传者和审核者信息
        uploaders = {}
        if uploader_ids:
            uploader_users = self.db.query(User).filter(User.id.in_(uploader_ids)).all()
            uploaders = {u.id: u.username or u.email for u in uploader_users}

        reviewers = {}
        if reviewer_ids:
            reviewer_users = self.db.query(User).filter(User.id.in_(reviewer_ids)).all()
            reviewers = {u.id: u.username or u.email for u in reviewer_users}

        # 为每个模板添加用户名
        for template in templates:
            template.uploader_name = uploaders.get(template.uploader_id)
            template.reviewer_name = reviewers.get(template.reviewer_id) if template.reviewer_id else None

        # 如果提供了用户ID，添加用户评分信息
        if user_id:
            for template in templates:
                rating = self.db.query(UserRating).filter(
                    and_(
                        UserRating.user_id == user_id,
                        UserRating.target_type == "template",
                        UserRating.target_id == template.id
                    )
                ).first()
                template.user_rating = rating.rating_type if rating else None

        return templates, total

    def get_shared_template_by_id(self, template_id: str, user_id: Optional[int] = None) -> Optional[SharedTemplate]:
        """根据ID获取共享模板"""
        template = self.db.query(SharedTemplate).filter(SharedTemplate.id == template_id).first()

        if template:
            # 添加用户名信息
            from app.models.user import User
            if template.uploader_id:
                uploader = self.db.query(User).filter(User.id == template.uploader_id).first()
                template.uploader_name = uploader.username or uploader.email if uploader else None
            if template.reviewer_id:
                reviewer = self.db.query(User).filter(User.id == template.reviewer_id).first()
                template.reviewer_name = reviewer.username or reviewer.email if reviewer else None

            if user_id:
                # 增加浏览次数
                template.view_count += 1
                self.db.commit()

                # 查询用户评分
                rating = self.db.query(UserRating).filter(
                    and_(
                        UserRating.user_id == user_id,
                        UserRating.target_type == "template",
                        UserRating.target_id == template_id
                    )
                ).first()
                template.user_rating = rating.rating_type if rating else None

        return template

    def download_shared_template(self, template_id: str, user_id: int, ip_address: Optional[str] = None, workspace_type: str = "personal", company_id: Optional[int] = None, factory_id: Optional[int] = None) -> Dict[str, Any]:
        """下载共享模板 - 完整复制到用户工作区"""
        shared_template = self.get_shared_template_by_id(template_id)
        if not shared_template or shared_template.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享模板不存在或未通过审核"
            )

        # 检查用户是否已经有同名同类型的活跃模板
        # 注意: 需要同时检查 name、module_type 和 is_active,因为:
        # 1. 不同类型的模板可以同名
        # 2. 软删除的模板(is_active=false)不应该阻止重新下载
        existing_template = self.db.query(WPSTemplate).filter(
            and_(
                WPSTemplate.user_id == user_id,
                WPSTemplate.workspace_type == workspace_type,
                WPSTemplate.company_id == company_id,
                WPSTemplate.factory_id == factory_id,
                WPSTemplate.name == shared_template.name,
                WPSTemplate.module_type == shared_template.module_type,  # 同时检查模块类型
                WPSTemplate.is_active == True  # 只检查活跃的模板
            )
        ).first()

        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"您的工作区中已存在名为 '{shared_template.name}' 的 {shared_template.module_type} 类型模板"
            )

        # 创建新的模板实例 - 完整复制共享模板的所有字段
        new_template = WPSTemplate(
            id=str(uuid.uuid4()),
            # 完整复制所有字段，确保数据完整性
            name=shared_template.name,
            description=shared_template.description,
            module_type=shared_template.module_type,  # 复制模块类型
            welding_process=shared_template.welding_process,
            welding_process_name=shared_template.welding_process_name,
            standard=shared_template.standard,
            module_instances=shared_template.module_instances,  # 完整复制JSONB字段
            # 工作区信息
            user_id=user_id,
            workspace_type=workspace_type,
            company_id=company_id,
            factory_id=factory_id,
            # 访问控制
            is_shared=False,
            access_level="private",
            # 模板属性
            template_source="user",
            version="1.0",
            is_active=True,
            is_system=False,
            # 统计信息
            usage_count=0,
            # 创建者信息
            created_by=user_id,
            updated_by=user_id
        )

        self.db.add(new_template)

        # 记录下载
        download_record = SharedDownload(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_type="template",
            target_id=template_id,
            ip_address=ip_address
        )
        self.db.add(download_record)

        # 增加下载次数
        shared_template.download_count += 1

        self.db.commit()
        self.db.refresh(new_template)

        return {
            "message": "模板下载成功",
            "template": {
                "id": new_template.id,
                "name": new_template.name,
                "description": new_template.description,
                "welding_process": new_template.welding_process,
                "welding_process_name": new_template.welding_process_name,
                "standard": new_template.standard,
                "module_instances": new_template.module_instances,
                "workspace_type": new_template.workspace_type,
                "template_source": new_template.template_source,
                "created_at": new_template.created_at
            },
            "shared_info": {
                "shared_id": shared_template.id,
                "shared_name": shared_template.name,
                "uploader_id": shared_template.uploader_id,
                "version": shared_template.version,
                "download_count": shared_template.download_count
            }
        }

    # ==================== 评分相关方法 ====================

    def rate_shared_resource(self, rating_data: UserRatingCreate, user_id: int) -> UserRating:
        """对共享资源进行评分"""
        # 检查是否已经评分过
        existing_rating = self.db.query(UserRating).filter(
            and_(
                UserRating.user_id == user_id,
                UserRating.target_type == rating_data.target_type,
                UserRating.target_id == rating_data.target_id
            )
        ).first()

        if existing_rating:
            # 更新现有评分
            old_rating_type = existing_rating.rating_type
            existing_rating.rating_type = rating_data.rating_type
            self.db.commit()

            # 更新统计
            if rating_data.target_type == "module":
                resource = self.db.query(SharedModule).filter(
                    SharedModule.id == rating_data.target_id
                ).first()
            else:
                resource = self.db.query(SharedTemplate).filter(
                    SharedTemplate.id == rating_data.target_id
                ).first()

            if resource:
                # 减去旧评分
                if old_rating_type == "like":
                    resource.like_count -= 1
                else:
                    resource.dislike_count -= 1

                # 增加新评分
                if rating_data.rating_type == "like":
                    resource.like_count += 1
                else:
                    resource.dislike_count += 1

                self.db.commit()

            return existing_rating
        else:
            # 创建新评分
            new_rating = UserRating(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_type=rating_data.target_type,
                target_id=rating_data.target_id,
                rating_type=rating_data.rating_type
            )
            self.db.add(new_rating)

            # 更新统计
            if rating_data.target_type == "module":
                resource = self.db.query(SharedModule).filter(
                    SharedModule.id == rating_data.target_id
                ).first()
            else:
                resource = self.db.query(SharedTemplate).filter(
                    SharedTemplate.id == rating_data.target_id
                ).first()

            if resource:
                if rating_data.rating_type == "like":
                    resource.like_count += 1
                else:
                    resource.dislike_count += 1

            self.db.commit()
            self.db.refresh(new_rating)
            return new_rating

    # ==================== 评论相关方法 ====================

    def create_comment(self, comment_data: SharedCommentCreate, user_id: int) -> SharedComment:
        """创建评论"""
        # 验证评论对象是否存在
        if comment_data.target_type == "module":
            resource = self.db.query(SharedModule).filter(
                SharedModule.id == comment_data.target_id
            ).first()
        else:
            resource = self.db.query(SharedTemplate).filter(
                SharedTemplate.id == comment_data.target_id
            ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论对象不存在"
            )

        # 如果是回复评论，验证父评论是否存在
        if comment_data.parent_id:
            parent_comment = self.db.query(SharedComment).filter(
                SharedComment.id == comment_data.parent_id
            ).first()
            if not parent_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="父评论不存在"
                )

        # 创建评论
        comment = SharedComment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_type=comment_data.target_type,
            target_id=comment_data.target_id,
            content=comment_data.content,
            parent_id=comment_data.parent_id
        )

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_comments(self, target_type: str, target_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[SharedComment], int]:
        """获取评论列表"""
        # 获取顶级评论（无父评论）
        query = self.db.query(SharedComment).filter(
            and_(
                SharedComment.target_type == target_type,
                SharedComment.target_id == target_id,
                SharedComment.parent_id.is_(None),
                SharedComment.status == "active"
            )
        ).order_by(desc(SharedComment.created_at))

        total = query.count()
        offset = (page - 1) * page_size
        comments = query.offset(offset).limit(page_size).all()

        # 递归获取回复评论
        for comment in comments:
            comment.replies = self._get_comment_replies(comment.id)

        return comments, total

    def _get_comment_replies(self, parent_id: str) -> List[SharedComment]:
        """递归获取回复评论"""
        replies = self.db.query(SharedComment).filter(
            and_(
                SharedComment.parent_id == parent_id,
                SharedComment.status == "active"
            )
        ).order_by(asc(SharedComment.created_at)).all()

        for reply in replies:
            reply.replies = self._get_comment_replies(reply.id)

        return replies

    # ==================== 管理员功能 ====================

    def review_shared_resource(self, resource_type: str, resource_id: str, review_action: ReviewAction, reviewer_id: int) -> bool:
        """审核共享资源"""
        if resource_type == "module":
            resource = self.db.query(SharedModule).filter(
                SharedModule.id == resource_id
            ).first()
        else:
            resource = self.db.query(SharedTemplate).filter(
                SharedTemplate.id == resource_id
            ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享资源不存在"
            )

        resource.status = review_action.status
        resource.reviewer_id = reviewer_id
        resource.review_comment = review_action.review_comment
        resource.review_time = func.now()

        self.db.commit()
        return True

    def set_featured_resource(self, resource_type: str, resource_id: str, featured_action: FeaturedAction) -> bool:
        """设置/取消推荐共享资源"""
        if resource_type == "module":
            resource = self.db.query(SharedModule).filter(
                SharedModule.id == resource_id
            ).first()
        else:
            resource = self.db.query(SharedTemplate).filter(
                SharedTemplate.id == resource_id
            ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享资源不存在"
            )

        resource.is_featured = featured_action.is_featured
        resource.featured_order = featured_action.featured_order

        self.db.commit()
        return True

    def get_library_stats(self) -> Dict[str, Any]:
        """获取共享库统计信息"""
        module_stats = self.db.query(
            func.count(SharedModule.id).label('total'),
            func.sum(func.case([(SharedModule.status == 'approved', 1)], else_=0)).label('approved'),
            func.sum(func.case([(SharedModule.status == 'pending', 1)], else_=0)).label('pending')
        ).filter(SharedModule.status != 'removed').first()

        template_stats = self.db.query(
            func.count(SharedTemplate.id).label('total'),
            func.sum(func.case([(SharedTemplate.status == 'approved', 1)], else_=0)).label('approved'),
            func.sum(func.case([(SharedTemplate.status == 'pending', 1)], else_=0)).label('pending')
        ).filter(SharedTemplate.status != 'removed').first()

        download_stats = self.db.query(func.count(SharedDownload.id)).scalar()
        rating_stats = self.db.query(func.count(UserRating.id)).scalar()

        return {
            "total_modules": module_stats.total or 0,
            "total_templates": template_stats.total or 0,
            "approved_modules": module_stats.approved or 0,
            "approved_templates": template_stats.approved or 0,
            "pending_modules": module_stats.pending or 0,
            "pending_templates": template_stats.pending or 0,
            "total_downloads": download_stats or 0,
            "total_ratings": rating_stats or 0,
            "featured_modules": self.db.query(SharedModule).filter(
                SharedModule.is_featured == True,
                SharedModule.status == 'approved'
            ).count(),
            "featured_templates": self.db.query(SharedTemplate).filter(
                SharedTemplate.is_featured == True,
                SharedTemplate.status == 'approved'
            ).count()
        }

    def delete_shared_module(self, module_id: str, user_id: int) -> bool:
        """删除用户分享的模块"""
        module = self.db.query(SharedModule).filter(
            and_(
                SharedModule.id == module_id,
                SharedModule.uploader_id == user_id
            )
        ).first()

        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享模块不存在或您无权限删除"
            )

        # 检查是否有用户下载过这个模块
        download_count = self.db.query(SharedDownload).filter(
            and_(
                SharedDownload.target_type == "module",
                SharedDownload.target_id == module_id
            )
        ).count()

        # 如果有用户下载过，不能删除，只能标记为已移除
        if download_count > 0:
            module.status = "removed"
            module.is_featured = False
            self.db.commit()
            return True

        # 如果没有用户下载过，可以直接删除
        try:
            # 删除相关评分
            self.db.query(UserRating).filter(
                and_(
                    UserRating.target_type == "module",
                    UserRating.target_id == module_id
                )
            ).delete()

            # 删除相关评论
            self.db.query(SharedComment).filter(
                and_(
                    SharedComment.target_type == "module",
                    SharedComment.target_id == module_id
                )
            ).delete()

            # 删除共享模块记录
            self.db.delete(module)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除模块失败: {str(e)}"
            )

    def delete_shared_template(self, template_id: str, user_id: int) -> bool:
        """删除用户分享的模板"""
        template = self.db.query(SharedTemplate).filter(
            and_(
                SharedTemplate.id == template_id,
                SharedTemplate.uploader_id == user_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="共享模板不存在或您无权限删除"
            )

        # 检查是否有用户下载过这个模板
        download_count = self.db.query(SharedDownload).filter(
            and_(
                SharedDownload.target_type == "template",
                SharedDownload.target_id == template_id
            )
        ).count()

        # 如果有用户下载过，不能删除，只能标记为已移除
        if download_count > 0:
            template.status = "removed"
            template.is_featured = False
            self.db.commit()
            return True

        # 如果没有用户下载过，可以直接删除
        try:
            # 删除相关评分
            self.db.query(UserRating).filter(
                and_(
                    UserRating.target_type == "template",
                    UserRating.target_id == template_id
                )
            ).delete()

            # 删除相关评论
            self.db.query(SharedComment).filter(
                and_(
                    SharedComment.target_type == "template",
                    SharedComment.target_id == template_id
                )
            ).delete()

            # 删除共享模板记录
            self.db.delete(template)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除模板失败: {str(e)}"
            )# Trigger reload
# Trigger reload again
# Using SQLAlchemy model objects
