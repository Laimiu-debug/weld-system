"""
数据访问权限中间件
Data Access Middleware for workspace isolation and permission control
"""
from typing import Optional, Type, TypeVar, List, Any
from sqlalchemy.orm import Session, Query
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole, Factory

# 泛型类型，用于数据模型
T = TypeVar('T')


class WorkspaceType:
    """工作区类型常量"""
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"


class AccessLevel:
    """访问级别常量"""
    PRIVATE = "private"      # 仅创建者可见
    FACTORY = "factory"      # 同工厂成员可见
    COMPANY = "company"      # 全公司成员可见
    PUBLIC = "public"        # 公开（模板等）


class DataAccessAction:
    """数据访问操作类型"""
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"


class WorkspaceContext:
    """工作区上下文"""
    
    def __init__(
        self,
        user_id: int,
        workspace_type: str = WorkspaceType.PERSONAL,
        company_id: Optional[int] = None,
        factory_id: Optional[int] = None
    ):
        self.user_id = user_id
        self.workspace_type = workspace_type
        self.company_id = company_id
        self.factory_id = factory_id
    
    def is_personal(self) -> bool:
        """是否为个人工作区"""
        return self.workspace_type == WorkspaceType.PERSONAL
    
    def is_enterprise(self) -> bool:
        """是否为企业工作区"""
        return self.workspace_type == WorkspaceType.ENTERPRISE
    
    def validate(self):
        """验证工作区上下文的有效性"""
        if self.is_enterprise() and not self.company_id:
            raise ValueError("企业工作区必须指定company_id")


class DataAccessMiddleware:
    """统一的数据访问权限检查中间件"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_access(
        self,
        user: User,
        resource: Any,
        action: str,
        workspace_context: Optional[WorkspaceContext] = None
    ) -> bool:
        """
        检查用户对资源的访问权限
        
        Args:
            user: 当前用户
            resource: 要访问的资源对象
            action: 操作类型 (view, create, edit, delete, share)
            workspace_context: 工作区上下文（可选）
            
        Returns:
            bool: 是否有权限
            
        Raises:
            HTTPException: 如果没有权限
        """
        # 检查资源是否有必需的数据隔离字段
        action = action.lower()
        if not hasattr(resource, 'workspace_type'):
            raise ValueError(f"资源 {type(resource).__name__} 缺少 workspace_type 字段")

        # 若提供了当前工作区上下文，资源必须属于该工作区
        if workspace_context is not None:
            if workspace_context.is_personal():
                if resource.workspace_type != WorkspaceType.PERSONAL or getattr(resource, "user_id", None) != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：资源不属于当前个人工作区",
                    )
            elif workspace_context.is_enterprise():
                if (
                    resource.workspace_type != WorkspaceType.ENTERPRISE
                    or getattr(resource, "company_id", None) != workspace_context.company_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足：资源不属于当前企业工作区",
                    )
        
        # 1. 个人工作区数据：仅创建者可访问
        if resource.workspace_type == WorkspaceType.PERSONAL:
            allowed = self._check_personal_access(user, resource, action)
        
        # 2. 企业工作区数据：检查企业成员身份和权限
        elif resource.workspace_type == WorkspaceType.ENTERPRISE:
            allowed = self._check_enterprise_access(user, resource, action)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：无法识别该资源的工作区类型",
            )
        # Callers rely on exceptions to stop writes; never return a silent denial.
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足：您无权执行此操作")
        return True
    
    def _check_personal_access(
        self,
        user: User,
        resource: Any,
        action: str
    ) -> bool:
        """检查个人工作区数据访问权限"""
        # 个人工作区数据只有创建者可以访问
        if resource.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：您无权访问其他用户的个人工作区数据"
            )
        return True
    
    def _check_enterprise_access(
        self,
        user: User,
        resource: Any,
        action: str
    ) -> bool:
        """检查企业工作区数据访问权限"""
        from app.models.company import Company

        # 1. 首先检查用户是否是企业所有者（拥有所有权限）
        company = self.db.query(Company).filter(
            Company.id == resource.company_id
        ).first()

        if company and company.owner_id == user.id:
            # 企业所有者拥有所有权限
            return True

        # 2. 检查用户是否是企业员工
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.company_id == resource.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：您不是该企业的成员"
            )

        # 3. 检查访问级别
        if resource.access_level == AccessLevel.PRIVATE:
            # 私有数据：仅创建者可访问
            if resource.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：此数据为私有，仅创建者可访问"
                )
            return True

        elif resource.access_level == AccessLevel.FACTORY:
            # 工厂级别：同工厂成员可访问
            if not self._check_factory_access(employee, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足：您无权访问此工厂的数据"
                )
            return True

        elif resource.access_level == AccessLevel.COMPANY:
            # 公司级别：全公司成员可访问
            # 已经验证是公司成员，检查角色权限
            return self._check_role_permission(employee, resource, action)

        elif resource.access_level == AccessLevel.PUBLIC:
            # 公开数据：所有企业成员可查看
            if action == DataAccessAction.VIEW:
                return True
            # 其他操作需要检查权限
            return self._check_role_permission(employee, resource, action)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：无法识别该资源的访问级别",
        )
    
    def _check_factory_access(
        self,
        employee: CompanyEmployee,
        resource: Any,
        action: str
    ) -> bool:
        """检查工厂级别访问权限"""
        # 如果资源没有指定工厂，则按公司级别处理
        if not resource.factory_id:
            return self._check_role_permission(employee, resource, action)

        # 如果员工在同一工厂，直接检查角色权限
        if employee.factory_id == resource.factory_id:
            return self._check_role_permission(employee, resource, action)

        # 不同工厂，检查员工的数据访问范围
        # 如果员工的data_access_scope是"company"，则可以访问所有工厂的数据
        if employee.data_access_scope == "company":
            return self._check_role_permission(employee, resource, action)

        # 如果员工有角色，检查角色的data_access_scope
        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id,
                CompanyRole.is_active == True
            ).first()

            if role and role.data_access_scope == "company":
                return self._check_role_permission(employee, resource, action)

        # 否则不允许跨工厂访问
        return False
    
    def _check_role_permission(
        self,
        employee: CompanyEmployee,
        resource: Any,
        action: str
    ) -> bool:
        """检查角色权限"""
        # 企业管理员（role="admin"）拥有所有权限
        if employee.role == "admin":
            return True

        # 如果没有角色，使用默认权限
        if not employee.company_role_id:
            return self._check_default_permission(employee, resource, action)

        # 获取角色
        role = self.db.query(CompanyRole).filter(
            CompanyRole.id == employee.company_role_id,
            CompanyRole.is_active == True
        ).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：您的角色不存在或已被禁用"
            )

        # 检查模块权限
        resource_type = type(resource).__name__.lower()
        permissions = role.permissions or {}

        # 映射资源类型到权限模块名称（带_management后缀）
        resource_to_module = {
            "weldingmaterial": "materials_management",
            "equipment": "equipment_management",
            "welder": "welders_management",
            "productionrecord": "production_management",
            "productiontask": "production_management",
            "productionplan": "production_management",
            "qualitystandard": "quality_management",
            "employeeperformance": "employee_management",
            "reporttemplate": "reports_management",
            "qualityinspection": "quality_management",
            "nonconformancerecord": "quality_management",
            "wps": "wps_management",
            "pqr": "pqr_management",
            "ppqr": "ppqr_management"
        }

        module_name = resource_to_module.get(resource_type, f"{resource_type}_management")
        module_permissions = permissions.get(module_name, {})

        # 映射操作到权限
        permission_key = self._map_action_to_permission(action)

        if not module_permissions.get(permission_key, False):
            # 友好的错误提示
            action_names = {
                "view": "查看",
                "create": "创建",
                "edit": "编辑",
                "delete": "删除",
                "share": "分享"
            }
            resource_names = {
                "equipment": "设备",
                "material": "焊材",
                "welder": "焊工",
                "wps": "WPS",
                "pqr": "PQR",
                "ppqr": "pPQR"
            }

            action_name = action_names.get(permission_key, permission_key)
            resource_name = resource_names.get(resource_type, resource_type)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：您没有{action_name}{resource_name}的权限"
            )

        return True
    
    def _check_default_permission(
        self,
        employee: CompanyEmployee,
        resource: Any,
        action: str
    ) -> bool:
        """检查默认权限（无角色时）"""
        # 企业管理员（role="admin"）拥有所有权限
        if employee.role == "admin":
            return True

        # 默认权限：可以查看和创建，但不能编辑和删除他人数据
        if action == DataAccessAction.VIEW:
            return True

        if action == DataAccessAction.CREATE:
            return True

        # 编辑和删除需要是创建者
        if action in [DataAccessAction.EDIT, DataAccessAction.DELETE]:
            return resource.user_id == employee.user_id

        return False
    
    def _map_action_to_permission(self, action: str) -> str:
        """映射操作到权限键"""
        # 转换为小写以支持大小写不敏感的匹配
        action_lower = action.lower()
        mapping = {
            "view": "view",
            "create": "create",
            "edit": "edit",
            "delete": "delete",
            "share": "share"
        }
        return mapping.get(action_lower, action_lower)
    
    def apply_workspace_filter(
        self,
        query: Query,
        model: Type[T],
        user: User,
        workspace_context: WorkspaceContext
    ) -> Query:
        """
        应用工作区过滤器到查询

        Args:
            query: SQLAlchemy查询对象
            model: 数据模型类
            user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Query: 过滤后的查询对象
        """
        workspace_context.validate()

        print(f"[数据隔离] 模型: {model.__name__}")
        print(f"[数据隔离] 用户ID: {user.id}")
        print(f"[数据隔离] 工作区类型: {workspace_context.workspace_type}")
        print(f"[数据隔离] 企业ID: {workspace_context.company_id}")

        # 检测模型是否具有真实的SQLAlchemy列（而非仅property）
        has_ws_col = isinstance(getattr(model, 'workspace_type', None), InstrumentedAttribute)
        has_user_col = isinstance(getattr(model, 'user_id', None), InstrumentedAttribute)
        has_owner_col = isinstance(getattr(model, 'owner_id', None), InstrumentedAttribute)
        has_company_col = isinstance(getattr(model, 'company_id', None), InstrumentedAttribute)
        has_factory_col = isinstance(getattr(model, 'factory_id', None), InstrumentedAttribute)

        # 个人工作区：只查询用户自己的数据
        if workspace_context.is_personal():
            print(f"[数据隔离] 应用个人工作区过滤: user={user.id}")
            if has_ws_col and has_user_col:
                query = query.filter(
                    and_(
                        model.workspace_type == WorkspaceType.PERSONAL,
                        model.user_id == user.id
                    )
                )
            else:
                conditions = []
                if has_company_col:
                    conditions.append(model.company_id == None)
                if has_owner_col:
                    conditions.append(model.owner_id == user.id)
                elif has_user_col:
                    conditions.append(model.user_id == user.id)
                if conditions:
                    query = query.filter(and_(*conditions))

        # 企业工作区：查询企业内可访问的数据
        elif workspace_context.is_enterprise():
            from app.models.company import Company, CompanyRole

            print(f"[数据隔离] 应用企业工作区过滤")

            # 检查用户是否是企业所有者
            company = self.db.query(Company).filter(
                Company.id == workspace_context.company_id
            ).first()

            if company and company.owner_id == user.id:
                # 企业所有者可以查看所有企业数据
                print(f"[数据隔离] 用户是企业所有者,可查看所有企业数据: company_id={workspace_context.company_id}")
                conditions = []
                if has_ws_col:
                    conditions.append(model.workspace_type == WorkspaceType.ENTERPRISE)
                if has_company_col:
                    conditions.append(model.company_id == workspace_context.company_id)
                if conditions:
                    query = query.filter(and_(*conditions))
                return query

            # 获取员工信息
            employee = self.db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()

            if not employee:
                # 不是企业成员，返回空结果
                print(f"[数据隔离] 用户不是企业成员,返回空结果")
                query = query.filter(model.id == -1)
                return query

            print(f"[数据隔离] 员工信息: role={employee.role}, data_access_scope={employee.data_access_scope}, factory_id={employee.factory_id}")

            # 企业管理员可以查看所有企业数据
            if employee.role == "admin":
                print(f"[数据隔离] 用户是企业管理员,可查看所有企业数据")
                conditions = []
                if has_ws_col:
                    conditions.append(model.workspace_type == WorkspaceType.ENTERPRISE)
                if has_company_col:
                    conditions.append(model.company_id == workspace_context.company_id)
                if conditions:
                    query = query.filter(and_(*conditions))
                return query

            # 构建企业数据过滤条件
            conditions = []
            if has_ws_col:
                conditions.append(model.workspace_type == WorkspaceType.ENTERPRISE)
            if has_company_col:
                conditions.append(model.company_id == workspace_context.company_id)

            # 根据data_access_scope决定访问范围
            data_access_scope = "factory"  # 默认工厂级别

            if employee.company_role_id:
                role = self.db.query(CompanyRole).filter(
                    CompanyRole.id == employee.company_role_id,
                    CompanyRole.is_active == True
                ).first()
                if role:
                    data_access_scope = role.data_access_scope or employee.data_access_scope or "factory"
            else:
                data_access_scope = employee.data_access_scope or "factory"

            print(f"[数据隔离] 最终data_access_scope: {data_access_scope}")

            # 如果是company级别，可以查看所有企业数据
            if data_access_scope == "company":
                print(f"[数据隔离] company级别,可查看所有企业数据")
                if conditions:
                    query = query.filter(and_(*conditions))
                return query

            # 如果是factory级别，只能查看所在工厂的数据
            if employee.factory_id and has_factory_col:
                print(f"[数据隔离] factory级别,只能查看工厂{employee.factory_id}的数据")
                conditions.append(model.factory_id == employee.factory_id)
            else:
                # Fail closed: factory-scope without factory assignment must not see all company data
                print(
                    f"[数据隔离] factory级别但缺少factory_id或模型无工厂列,返回空结果"
                )
                return query.filter(model.id == -1)

            if conditions:
                query = query.filter(and_(*conditions))

        return query

