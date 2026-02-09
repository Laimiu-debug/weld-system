"""
pPQR Service
处理pPQR相关的业务逻辑
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.ppqr import PPQR
from app.models.user import User
from app.core.data_access import WorkspaceContext, DataAccessMiddleware


class PPQRService:
    """pPQR业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        current_user: User,
        workspace_context: WorkspaceContext,
        status: Optional[str] = None,
        test_conclusion: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[PPQR]:
        """
        获取pPQR列表（带工作区上下文数据隔离）

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            current_user: 当前用户
            workspace_context: 工作区上下文
            status: 状态筛选
            test_conclusion: 试验结论筛选
            search_term: 搜索关键词

        Returns:
            pPQR列表
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 构建基础查询
        query = db.query(PPQR)

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        # 应用状态筛选
        if status:
            query = query.filter(PPQR.status == status)

        # 应用试验结论筛选
        if test_conclusion:
            query = query.filter(PPQR.test_conclusion == test_conclusion)

        # 应用搜索
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    PPQR.ppqr_number.ilike(search_pattern),
                    PPQR.title.ilike(search_pattern),
                    PPQR.test_purpose.ilike(search_pattern)
                )
            )

        # 排序和分页
        query = query.order_by(PPQR.created_at.desc())
        query = query.offset(skip).limit(limit)

        return query.all()

    def count(
        self,
        db: Session,
        *,
        current_user: User,
        workspace_context: WorkspaceContext,
        status: Optional[str] = None,
        test_conclusion: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> int:
        """
        获取pPQR总数（带工作区上下文数据隔离）

        Args:
            db: 数据库会话
            current_user: 当前用户
            workspace_context: 工作区上下文
            status: 状态筛选
            test_conclusion: 试验结论筛选
            search_term: 搜索关键词

        Returns:
            pPQR总数
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 构建基础查询
        query = db.query(func.count(PPQR.id))

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        # 应用状态筛选
        if status:
            query = query.filter(PPQR.status == status)

        # 应用试验结论筛选
        if test_conclusion:
            query = query.filter(PPQR.test_conclusion == test_conclusion)

        # 应用搜索
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    PPQR.ppqr_number.ilike(search_pattern),
                    PPQR.title.ilike(search_pattern),
                    PPQR.test_purpose.ilike(search_pattern)
                )
            )

        return query.scalar()

    def get(
        self,
        db: Session,
        *,
        id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[PPQR]:
        """
        获取单个pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            pPQR对象或None
        """
        query = db.query(PPQR).filter(PPQR.id == id)

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        return query.first()

    def create(
        self,
        db: Session,
        *,
        ppqr_data: dict,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> PPQR:
        """
        创建pPQR（带工作区上下文）

        Args:
            db: 数据库会话
            ppqr_data: pPQR数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            创建的pPQR对象

        Raises:
            ValueError: 如果pPQR编号已存在
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 检查pPQR编号是否已存在
        existing = db.query(PPQR).filter(
            PPQR.ppqr_number == ppqr_data.get("ppqr_number")
        ).first()
        if existing:
            raise ValueError(f"pPQR编号 {ppqr_data.get('ppqr_number')} 已存在")

        # 获取模块数据（支持 module_data 和 modules_data 两种字段名）
        module_data = ppqr_data.get("module_data") or ppqr_data.get("modules_data", {})

        # 创建pPQR对象
        ppqr = PPQR(
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,  # 已经是字符串，不需要.value
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            ppqr_number=ppqr_data.get("ppqr_number"),
            title=ppqr_data.get("title"),
            revision=ppqr_data.get("revision", "A"),
            status=ppqr_data.get("status", "draft"),
            template_id=ppqr_data.get("template_id"),
            module_data=module_data,
            created_by=current_user.id  # 添加创建人ID
        )

        db.add(ppqr)
        db.commit()
        db.refresh(ppqr)

        return ppqr

    def update(
        self,
        db: Session,
        *,
        id: int,
        ppqr_data: dict,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[PPQR]:
        """
        更新pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            ppqr_data: 更新数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            更新后的pPQR对象或None
        """
        ppqr = self.get(db, id=id, current_user=current_user, workspace_context=workspace_context)
        if not ppqr:
            return None

        # 字段名映射（前端使用 modules_data，数据库使用 module_data）
        field_mapping = {
            'modules_data': 'module_data'
        }

        # 更新字段
        for key, value in ppqr_data.items():
            # 转换字段名
            db_field_name = field_mapping.get(key, key)

            if hasattr(ppqr, db_field_name) and value is not None:
                setattr(ppqr, db_field_name, value)

        # 设置更新人
        ppqr.updated_by = current_user.id

        db.commit()
        db.refresh(ppqr)

        return ppqr

    def delete(
        self,
        db: Session,
        *,
        id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否删除成功
        """
        ppqr = self.get(db, id=id, current_user=current_user, workspace_context=workspace_context)
        if not ppqr:
            return False

        db.delete(ppqr)
        db.commit()

        return True

