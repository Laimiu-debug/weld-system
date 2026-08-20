"""
WPS Template service for the welding system backend.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime
import re

from app.models.wps_template import WPSTemplate
from app.models.user import User
from app.models.company import CompanyEmployee
from app.schemas.wps_template import WPSTemplateCreate, WPSTemplateUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext, WorkspaceType
from fastapi import HTTPException, status


class WPSTemplateService:
    """WPS模板服务"""

    def __init__(self, db: Session):
        """初始化WPS模板服务"""
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get_available_templates(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        welding_process: Optional[str] = None,
        standard: Optional[str] = None,
        module_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[WPSTemplate], int]:
        """
        获取用户可用的模板列表（使用统一的数据隔离机制）
        包括：系统模板 + 用户自己的模板 + 企业共享模板

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            welding_process: 焊接工艺过滤
            standard: 标准过滤
            module_type: 模块类型过滤 (wps/pqr/ppqr)
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            (templates, total_count)
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工作区上下文验证失败: {str(e)}"
            )

        # 构建基础查询
        query = self.db.query(WPSTemplate).filter(WPSTemplate.is_active == True)

        # 应用数据隔离过滤（使用统一的DataAccessMiddleware）
        # 注意：模板有特殊的可见性规则（系统模板对所有人可见）
        # 所以我们需要自定义过滤逻辑
        visibility_filters = [
            # 1. 系统模板（所有人可见）
            WPSTemplate.template_source == "system",
        ]

        # 2. 个人工作区：用户自己的模板
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            visibility_filters.append(
                and_(
                    WPSTemplate.workspace_type == WorkspaceType.PERSONAL,
                    WPSTemplate.user_id == current_user.id
                )
            )

        # 3. 企业工作区：企业内的模板
        # 企业工作区内创建的模板都是企业资产，同一企业的所有员工都可以看到
        elif workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            if workspace_context.company_id:
                visibility_filters.append(
                    and_(
                        WPSTemplate.workspace_type == WorkspaceType.ENTERPRISE,
                        WPSTemplate.company_id == workspace_context.company_id
                        # 不再检查 is_shared，企业内所有模板都对企业员工可见
                    )
                )

        query = query.filter(or_(*visibility_filters))

        # 按模块类型过滤
        if module_type:
            query = query.filter(WPSTemplate.module_type == module_type)

        # 按焊接工艺过滤
        if welding_process:
            query = query.filter(WPSTemplate.welding_process == welding_process)

        # 按标准过滤
        if standard:
            query = query.filter(WPSTemplate.standard == standard)

        # 获取总数
        total = query.count()

        # 排序和分页
        templates = query.order_by(
            WPSTemplate.template_source.desc(),  # 系统模板优先
            WPSTemplate.usage_count.desc(),      # 使用次数多的优先
            WPSTemplate.created_at.desc()
        ).offset(skip).limit(limit).all()

        return templates, total
    
    def get_template_by_id(
        self,
        template_id: str,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPSTemplate:
        """
        获取模板详情

        Args:
            template_id: 模板ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            WPSTemplate对象
        """
        template = self.db.query(WPSTemplate).filter(
            WPSTemplate.id == template_id,
            WPSTemplate.is_active == True
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="WPS模板不存在或已被删除"
            )

        # 检查访问权限
        if not self._check_template_access(template, current_user, workspace_context):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问此WPS模板"
            )

        return template

    def create_template(
        self,
        template_in: WPSTemplateCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPSTemplate:
        """
        创建用户自定义模板

        Args:
            template_in: 模板创建数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            创建的WPSTemplate对象
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 检查配额
        self._check_template_quota(current_user)

        # 生成模板ID
        template_id = self._generate_template_id(
            template_in.standard,
            template_in.welding_process,
            current_user.id
        )

        # 检查ID是否已存在
        existing = self.db.query(WPSTemplate).filter(WPSTemplate.id == template_id).first()
        if existing:
            # 如果ID冲突，添加时间戳
            template_id = f"{template_id}_{int(datetime.now().timestamp())}"

        # 创建模板
        template_data = template_in.model_dump()
        # 移除 workspace_type，因为我们要使用 workspace_context 中的值
        template_data.pop('workspace_type', None)

        db_template = WPSTemplate(
            id=template_id,
            **template_data,
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            template_source="system" if workspace_context.workspace_type == "system" else (
                "user" if workspace_context.workspace_type == WorkspaceType.PERSONAL else "enterprise"
            ),
            created_by=current_user.id,
            updated_by=current_user.id
        )

        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)

        return db_template
    
    def update_template(
        self,
        template_id: str,
        template_in: WPSTemplateUpdate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPSTemplate:
        """
        更新模板

        Args:
            template_id: 模板ID
            template_in: 更新数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            更新后的WPSTemplate对象
        """
        template = self.db.query(WPSTemplate).filter(WPSTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 检查权限（只能修改自己创建的模板）
        if template.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此模板")

        # 不能修改系统模板
        if template.is_system:
            raise HTTPException(status_code=403, detail="不能修改系统模板")

        # 更新字段
        update_data = template_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_by = current_user.id
        template.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        return template

    def delete_template(
        self,
        template_id: str,
        current_user: User,
        workspace_context: WorkspaceContext
    ):
        """
        删除模板（软删除）

        Args:
            template_id: 模板ID
            current_user: 当前用户
            workspace_context: 工作区上下文
        """
        template = self.db.query(WPSTemplate).filter(WPSTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 检查权限
        if template.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此模板")

        # 不能删除系统模板
        if template.is_system:
            raise HTTPException(status_code=403, detail="不能删除系统模板")

        # 软删除
        template.is_active = False
        template.updated_by = current_user.id
        template.updated_at = datetime.utcnow()

        self.db.commit()

    def increment_usage(self, template_id: str):
        """
        增加模板使用次数

        Args:
            template_id: 模板ID
        """
        template = self.db.query(WPSTemplate).filter(WPSTemplate.id == template_id).first()
        if template:
            template.usage_count += 1
            self.db.commit()

    def _check_template_access(
        self,
        template: WPSTemplate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        检查用户是否有权访问模板

        Args:
            template: 模板对象
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否有权访问
        """
        # 系统模板所有人可访问
        if template.template_source == "system":
            return True

        # 自己创建的模板
        if template.user_id == current_user.id:
            return True

        # 企业工作区：同一企业的所有模板都可访问（企业资产）
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            if template.workspace_type == WorkspaceType.ENTERPRISE and template.company_id == workspace_context.company_id:
                return True

        return False

    def _check_template_quota(self, user: User):
        """
        检查模板配额

        Args:
            user: 用户对象
        """
        # 这里简化处理，实际应该从会员配置中读取
        # 免费用户不能创建自定义模板
        if user.member_tier == "personal_free":
            raise HTTPException(
                status_code=403,
                detail="免费版不支持创建自定义模板，请升级会员"
            )

        # 检查模板数量限制
        max_templates_map = {
            "personal_pro": 3,
            "personal_advanced": 10,
            "personal_flagship": -1,  # 无限制
            "enterprise": -1,
            "enterprise_pro": -1,
            "enterprise_pro_max": -1
        }

        max_templates = max_templates_map.get(user.member_tier, 0)

        if max_templates >= 0:  # -1表示无限制
            current_count = self.db.query(WPSTemplate).filter(
                WPSTemplate.user_id == user.id,
                WPSTemplate.is_active == True
            ).count()

            if current_count >= max_templates:
                raise HTTPException(
                    status_code=403,
                    detail=f"已达到自定义模板配额限制（{max_templates}个），请升级会员或删除旧模板"
                )

    def _generate_template_id(
        self,
        standard: Optional[str],
        welding_process: Optional[str],
        user_id: int
    ) -> str:
        """
        生成模板ID

        Args:
            standard: 标准名称
            welding_process: 焊接工艺
            user_id: 用户ID

        Returns:
            生成的模板ID
        """
        # 标准化标准名称
        std_part = ""
        if standard:
            std_part = re.sub(r'[^a-zA-Z0-9]', '_', standard.lower())
        else:
            std_part = "custom"

        # 焊接工艺部分
        process_part = welding_process if welding_process else "general"

        # 用户ID后4位
        user_suffix = str(user_id)[-4:].zfill(4)

        # 时间戳后6位
        timestamp = datetime.now().strftime("%y%m%d")

        return f"{std_part}_{process_part}_u{user_suffix}_{timestamp}"

