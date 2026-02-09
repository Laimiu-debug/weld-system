"""
企业权限验证中间件
"""
from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.company import CompanyEmployee, CompanyRole
from app.core.database import get_db


class PermissionChecker:
    """权限检查器"""
    
    def __init__(
        self,
        module: str,
        action: str,
        require_company_role: bool = True
    ):
        """
        初始化权限检查器
        
        Args:
            module: 权限模块名称（如 'wps_management', 'employee_management'）
            action: 权限操作（'view', 'create', 'edit', 'delete'）
            require_company_role: 是否要求必须有企业角色
        """
        self.module = module
        self.action = action
        self.require_company_role = require_company_role
    
    def __call__(
        self,
        current_user: User,
        db: Session
    ) -> bool:
        """
        检查用户是否有权限
        
        Args:
            current_user: 当前用户
            db: 数据库会话
            
        Returns:
            bool: 是否有权限
            
        Raises:
            HTTPException: 如果没有权限
        """
        # 1. 检查是否是企业会员
        if current_user.membership_type != "enterprise":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要企业会员权限"
            )
        
        # 2. 获取员工信息
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.status == "active"
        ).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="未找到员工信息"
            )
        
        # 3. 检查企业角色
        if not employee.company_role_id:
            if self.require_company_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="未分配企业角色，请联系管理员"
                )
            # 如果不要求企业角色，则允许通过（使用系统角色权限）
            return True
        
        # 4. 获取角色权限
        role = db.query(CompanyRole).filter(
            CompanyRole.id == employee.company_role_id,
            CompanyRole.is_active == True
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="角色不存在或已禁用"
            )
        
        # 5. 检查模块权限
        permissions = role.permissions or {}
        module_permissions = permissions.get(self.module, {})
        
        if not module_permissions.get(self.action, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有{self.module}的{self.action}权限"
            )
        
        return True


def require_permission(
    module: str,
    action: str,
    require_company_role: bool = True
):
    """
    权限检查装饰器
    
    使用示例:
    @router.get("/wps")
    @require_permission("wps_management", "view")
    async def get_wps_list(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        ...
    
    Args:
        module: 权限模块名称
        action: 权限操作
        require_company_role: 是否要求必须有企业角色
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user和db
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="权限检查失败：缺少必要参数"
                )
            
            # 执行权限检查
            checker = PermissionChecker(module, action, require_company_role)
            checker(current_user, db)
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_employee_permission(
    current_user: User,
    db: Session,
    module: str,
    action: str,
    require_company_role: bool = True
) -> tuple[CompanyEmployee, Optional[CompanyRole]]:
    """
    检查员工权限并返回员工和角色信息
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        module: 权限模块名称
        action: 权限操作
        require_company_role: 是否要求必须有企业角色
        
    Returns:
        tuple: (员工对象, 角色对象)
        
    Raises:
        HTTPException: 如果没有权限
    """
    # 1. 检查是否是企业会员
    if current_user.membership_type != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要企业会员权限"
        )
    
    # 2. 获取员工信息
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == current_user.id,
        CompanyEmployee.status == "active"
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未找到员工信息"
        )
    
    # 3. 检查企业角色
    if not employee.company_role_id:
        if require_company_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="未分配企业角色，请联系管理员"
            )
        # 如果不要求企业角色，则返回员工信息
        return employee, None
    
    # 4. 获取角色权限
    role = db.query(CompanyRole).filter(
        CompanyRole.id == employee.company_role_id,
        CompanyRole.is_active == True
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="角色不存在或已禁用"
        )
    
    # 5. 检查模块权限
    permissions = role.permissions or {}
    module_permissions = permissions.get(module, {})
    
    if not module_permissions.get(action, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有{module}的{action}权限"
        )
    
    return employee, role


def get_employee_data_scope(
    current_user: User,
    db: Session
) -> tuple[str, Optional[int], Optional[int]]:
    """
    获取员工的数据访问范围
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        tuple: (数据范围, 公司ID, 工厂ID)
            - 数据范围: 'company' 或 'factory'
            - 公司ID: 员工所属公司ID
            - 工厂ID: 如果是工厂级权限，返回工厂ID；否则为None
    """
    # 获取员工信息
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == current_user.id,
        CompanyEmployee.status == "active"
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未找到员工信息"
        )
    
    # 获取角色的数据访问范围
    if employee.company_role_id:
        role = db.query(CompanyRole).filter(
            CompanyRole.id == employee.company_role_id,
            CompanyRole.is_active == True
        ).first()
        
        if role:
            data_scope = role.data_access_scope
        else:
            data_scope = employee.data_access_scope
    else:
        data_scope = employee.data_access_scope
    
    # 返回数据范围信息
    if data_scope == "company":
        return "company", employee.company_id, None
    else:
        return "factory", employee.company_id, employee.factory_id

