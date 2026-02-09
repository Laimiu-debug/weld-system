"""
自定义模块服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import uuid

from app.models.custom_module import CustomModule
from app.models.user import User
from app.schemas.custom_module import CustomModuleCreate, CustomModuleUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext, WorkspaceType


class CustomModuleService:
    """自定义模块服务类"""

    def __init__(self, db: Session):
        """初始化自定义模块服务"""
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get_available_modules(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        module_type: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CustomModule]:
        """
        获取用户可用的模块列表（使用统一的数据隔离机制）
        包括：系统模块 + 用户自己的模块 + 企业共享模块

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            module_type: 模块类型过滤 (wps/pqr/ppqr/common)，如果指定，则返回该类型和common类型的模块
            category: 分类过滤
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            模块列表
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 构建基础查询
        query = self.db.query(CustomModule)

        # 构建访问权限过滤条件
        # 注意：模块有特殊的可见性规则（系统模块对所有人可见）
        access_conditions = [
            CustomModule.workspace_type == 'system',  # 系统模块
        ]

        # 个人工作区：用户自己的模块
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            access_conditions.append(
                and_(
                    CustomModule.workspace_type == WorkspaceType.PERSONAL,
                    CustomModule.user_id == current_user.id
                )
            )

        # 企业工作区：企业内的模块
        # 企业工作区内创建的模块都是企业资产，同一企业的所有员工都可以看到
        elif workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            if workspace_context.company_id:
                access_conditions.append(
                    and_(
                        CustomModule.workspace_type == WorkspaceType.ENTERPRISE,
                        CustomModule.company_id == workspace_context.company_id
                        # 不再检查 is_shared，企业内所有模块都对企业员工可见
                    )
                )

        query = query.filter(or_(*access_conditions))

        # 模块类型过滤
        # 如果指定了module_type，则返回该类型和common类型的模块
        # common类型的模块可用于所有记录类型
        if module_type:
            query = query.filter(
                or_(
                    CustomModule.module_type == module_type,
                    CustomModule.module_type == 'common'
                )
            )

        # 分类过滤
        if category:
            query = query.filter(CustomModule.category == category)

        # 排序
        query = query.order_by(
            CustomModule.workspace_type.desc(),  # 系统模块优先
            CustomModule.usage_count.desc(),
            CustomModule.created_at.desc()
        )

        return query.offset(skip).limit(limit).all()

    def get_module(
        self,
        module_id: str,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[CustomModule]:
        """
        获取单个模块

        Args:
            module_id: 模块ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            CustomModule对象或None
        """
        module = self.db.query(CustomModule).filter(CustomModule.id == module_id).first()

        # 检查访问权限
        if module and not self._check_module_access(module, current_user, workspace_context):
            return None

        return module

    def create_module(
        self,
        module_data: CustomModuleCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> CustomModule:
        """
        创建自定义模块

        Args:
            module_data: 模块创建数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            创建的CustomModule对象
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 生成模块ID
        if not module_data.id:
            module_id = f"custom_{current_user.id}_{uuid.uuid4().hex[:8]}"
        else:
            module_id = module_data.id

        # 转换字段定义为dict
        fields_dict = {
            key: value.model_dump() for key, value in module_data.fields.items()
        }

        # 创建模块
        module = CustomModule(
            id=module_id,
            name=module_data.name,
            description=module_data.description,
            icon=module_data.icon,
            module_type=module_data.module_type,  # 添加module_type
            category=module_data.category,
            repeatable=module_data.repeatable,
            fields=fields_dict,
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            is_shared=module_data.is_shared,
            access_level=module_data.access_level
        )

        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        return module

    def update_module(
        self,
        module_id: str,
        module_data: CustomModuleUpdate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[CustomModule]:
        """
        更新自定义模块

        Args:
            module_id: 模块ID
            module_data: 更新数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            更新后的CustomModule对象或None
        """
        module = self.db.query(CustomModule).filter(CustomModule.id == module_id).first()
        if not module:
            return None

        # 检查权限（只能修改自己创建的模块）
        if not self._check_module_permission(module, current_user, workspace_context):
            return None

        # 更新字段
        update_data = module_data.model_dump(exclude_unset=True)

        # 转换字段定义
        if 'fields' in update_data and update_data['fields']:
            update_data['fields'] = {
                key: value.model_dump() if hasattr(value, 'model_dump') else value
                for key, value in update_data['fields'].items()
            }

        for field, value in update_data.items():
            setattr(module, field, value)

        self.db.commit()
        self.db.refresh(module)

        return module

    def delete_module(
        self,
        module_id: str,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除自定义模块

        Args:
            module_id: 模块ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否删除成功
        """
        module = self.db.query(CustomModule).filter(CustomModule.id == module_id).first()
        if not module:
            return False

        # 检查权限
        if not self._check_module_permission(module, current_user, workspace_context):
            return False

        self.db.delete(module)
        self.db.commit()

        return True

    def increment_usage(self, module_id: str):
        """
        增加模块使用次数

        Args:
            module_id: 模块ID
        """
        module = self.db.query(CustomModule).filter(CustomModule.id == module_id).first()
        if module:
            module.usage_count += 1
            self.db.commit()

    def _check_module_access(
        self,
        module: CustomModule,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        检查用户是否有权访问模块（查看权限）

        Args:
            module: 模块对象
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否有权访问
        """
        # 系统模块所有人可访问
        if module.workspace_type == 'system':
            return True

        # 自己创建的模块
        if module.user_id == current_user.id:
            return True

        # 企业工作区：同一企业的所有模块都可访问（企业资产）
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            if module.workspace_type == WorkspaceType.ENTERPRISE and module.company_id == workspace_context.company_id:
                return True

        return False

    def _check_module_permission(
        self,
        module: CustomModule,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        检查用户是否有权限修改/删除模块

        Args:
            module: 模块对象
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否有权限
        """
        # 系统模块只读
        if module.workspace_type == 'system':
            return False

        # 用户自己创建的模块,无论是 personal 还是 enterprise,都有完全权限
        if module.user_id == current_user.id:
            return True

        # 企业内其他人创建的共享模块（仅查看权限,不能修改/删除）
        return False

