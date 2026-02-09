"""
Company roles management endpoints for enterprise members.
企业角色管理API端点
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.company import Company, CompanyRole, CompanyEmployee
from app.api.deps import get_current_active_user

router = APIRouter()


# ==================== 初始化API ====================

@router.post("/roles/init-table")
async def init_company_roles_table_only(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    仅创建企业角色表（不创建默认角色）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.core.database import Base, engine
        from sqlalchemy import text

        # 创建表
        print("创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建完成")

        # 添加 company_role_id 列到 company_employees 表
        print("添加 company_role_id 列...")
        try:
            db.execute(text("""
                ALTER TABLE company_employees
                ADD COLUMN IF NOT EXISTS company_role_id INTEGER REFERENCES company_roles(id) ON DELETE SET NULL
            """))
            db.commit()
            print("✅ company_role_id 列添加成功")
        except Exception as e:
            print(f"⚠️  添加列失败（可能已存在）: {str(e)}")
            db.rollback()

        return {
            "success": True,
            "message": "企业角色表创建成功"
        }
    except Exception as e:
        db.rollback()
        print(f"❌ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建表失败: {str(e)}"
        )


@router.post("/roles/init")
async def init_company_roles_table(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    初始化企业角色表和默认角色（仅用于开发/测试）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.core.database import Base, engine
        from sqlalchemy import text

        # 创建表
        print("创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建完成")

        # 添加 company_role_id 列到 company_employees 表
        print("添加 company_role_id 列...")
        try:
            db.execute(text("""
                ALTER TABLE company_employees
                ADD COLUMN IF NOT EXISTS company_role_id INTEGER REFERENCES company_roles(id) ON DELETE SET NULL
            """))
            db.commit()
            print("✅ company_role_id 列添加成功")
        except Exception as e:
            print(f"⚠️  添加列失败（可能已存在）: {str(e)}")
            db.rollback()

        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 检查是否已有角色
        existing_roles = db.query(CompanyRole).filter(
            CompanyRole.company_id == company.id
        ).count()

        if existing_roles > 0:
            return {
                "success": True,
                "message": f"企业已有 {existing_roles} 个角色，无需初始化",
                "data": {"existing_roles": existing_roles}
            }

        # 创建默认角色
        default_roles = [
            {
                'name': '企业管理员',
                'code': 'ADMIN',
                'description': '拥有所有权限的管理员角色',
                'permissions': {
                    'wps_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'pqr_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'ppqr_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'equipment_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'materials_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'welders_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': True},
                    'employee_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': False},
                    'factory_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': False},
                    'department_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': False},
                    'role_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': False},
                    'reports_management': {'view': True, 'create': True, 'edit': True, 'delete': True, 'approve': False},
                },
                'data_access_scope': 'company',
                'is_system': True
            },
            {
                'name': '部门经理',
                'code': 'MANAGER',
                'description': '部门经理，可以管理本部门的数据',
                'permissions': {
                    'wps_management': {'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True},
                    'pqr_management': {'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True},
                    'ppqr_management': {'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': True},
                    'equipment_management': {'view': True, 'create': True, 'edit': True, 'delete': False, 'approve': False},
                    'materials_management': {'view': True, 'create': True, 'edit': False, 'delete': False, 'approve': False},
                    'welders_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'employee_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'factory_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'department_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'role_management': {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'reports_management': {'view': True, 'create': True, 'edit': False, 'delete': False, 'approve': False},
                },
                'data_access_scope': 'factory',
                'is_system': True
            },
            {
                'name': '普通员工',
                'code': 'EMPLOYEE',
                'description': '普通员工，只能查看和创建基本数据',
                'permissions': {
                    'wps_management': {'view': True, 'create': True, 'edit': False, 'delete': False, 'approve': False},
                    'pqr_management': {'view': True, 'create': True, 'edit': False, 'delete': False, 'approve': False},
                    'ppqr_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'equipment_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'materials_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'welders_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'employee_management': {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'factory_management': {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'department_management': {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'role_management': {'view': False, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                    'reports_management': {'view': True, 'create': False, 'edit': False, 'delete': False, 'approve': False},
                },
                'data_access_scope': 'factory',
                'is_system': True
            }
        ]

        admin_role_id = None
        created_roles = []

        for role_data in default_roles:
            # 创建角色
            new_role = CompanyRole(
                company_id=company.id,
                name=role_data['name'],
                code=role_data['code'],
                description=role_data['description'],
                permissions=role_data['permissions'],
                data_access_scope=role_data['data_access_scope'],
                is_system=role_data['is_system'],
                created_by=current_user.id
            )

            db.add(new_role)
            db.flush()  # 获取ID

            created_roles.append({
                "id": str(new_role.id),
                "name": new_role.name,
                "code": new_role.code
            })

            # 记录管理员角色ID
            if role_data['code'] == 'ADMIN':
                admin_role_id = new_role.id

        # 将企业所有者分配到管理员角色
        if admin_role_id:
            admin_employee = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.role == 'admin'
            ).first()

            if admin_employee:
                admin_employee.company_role_id = admin_role_id

        db.commit()

        return {
            "success": True,
            "message": "企业角色初始化成功",
            "data": {
                "created_roles": created_roles,
                "admin_role_assigned": admin_role_id is not None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化角色失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化角色失败: {str(e)}"
        )


# 权限检查函数
def check_enterprise_membership(user: User) -> User:
    """检查用户是否为企业会员"""
    if user.membership_type != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此功能仅限企业会员使用"
        )
    
    if user.member_tier not in ["enterprise", "enterprise_pro", "enterprise_pro_max"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此功能仅限企业会员使用"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未激活"
        )
    
    return user


# Pydantic模型
class PermissionConfig(BaseModel):
    """权限配置"""
    view: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False
    approve: bool = False


class RolePermissions(BaseModel):
    """角色权限配置"""
    wps_management: Optional[PermissionConfig] = None
    pqr_management: Optional[PermissionConfig] = None
    ppqr_management: Optional[PermissionConfig] = None
    equipment_management: Optional[PermissionConfig] = None
    materials_management: Optional[PermissionConfig] = None
    welders_management: Optional[PermissionConfig] = None
    employee_management: Optional[PermissionConfig] = None
    factory_management: Optional[PermissionConfig] = None
    department_management: Optional[PermissionConfig] = None
    role_management: Optional[PermissionConfig] = None
    reports_management: Optional[PermissionConfig] = None


class CreateRoleRequest(BaseModel):
    """创建角色请求"""
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    permissions: Dict[str, Dict[str, bool]]
    data_access_scope: str = "factory"  # factory, company


class UpdateRoleRequest(BaseModel):
    """更新角色请求"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, Dict[str, bool]]] = None
    data_access_scope: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== 角色管理API ====================

@router.get("/roles")
async def get_company_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业角色列表（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 构建查询
        query = db.query(CompanyRole).filter(CompanyRole.company_id == company.id)

        if is_active is not None:
            query = query.filter(CompanyRole.is_active == is_active)

        # 获取总数
        total = query.count()

        # 分页
        roles = query.order_by(CompanyRole.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        # 格式化数据
        items = []
        for role in roles:
            # 统计使用该角色的员工数
            employee_count = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.company_role_id == role.id,
                CompanyEmployee.status == "active"
            ).count()

            items.append({
                "id": str(role.id),
                "name": role.name,
                "code": role.code or "",
                "description": role.description or "",
                "permissions": role.permissions or {},
                "data_access_scope": role.data_access_scope,
                "is_active": role.is_active,
                "is_system": role.is_system,
                "employee_count": employee_count,
                "created_at": role.created_at.isoformat() if role.created_at else "",
                "updated_at": role.updated_at.isoformat() if role.updated_at else ""
            })

        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取角色列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )


@router.post("/roles")
async def create_company_role(
    role_data: CreateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建企业角色（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 检查角色名称是否重复
        existing_role = db.query(CompanyRole).filter(
            CompanyRole.company_id == company.id,
            CompanyRole.name == role_data.name
        ).first()

        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名称已存在"
            )

        # 检查角色代码是否重复
        if role_data.code:
            existing_code = db.query(CompanyRole).filter(
                CompanyRole.company_id == company.id,
                CompanyRole.code == role_data.code
            ).first()

            if existing_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色代码已存在"
                )

        # 创建角色
        new_role = CompanyRole(
            company_id=company.id,
            name=role_data.name,
            code=role_data.code,
            description=role_data.description,
            permissions=role_data.permissions,
            data_access_scope=role_data.data_access_scope,
            is_system=False,
            created_by=current_user.id
        )

        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return {
            "success": True,
            "message": "角色创建成功",
            "data": {
                "id": str(new_role.id),
                "name": new_role.name,
                "code": new_role.code,
                "description": new_role.description,
                "permissions": new_role.permissions,
                "data_access_scope": new_role.data_access_scope
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 创建角色失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )


@router.put("/roles/{role_id}")
async def update_company_role(
    role_id: int,
    role_data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新企业角色（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 获取角色
        role = db.query(CompanyRole).filter(
            CompanyRole.id == role_id,
            CompanyRole.company_id == company.id
        ).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 系统角色不允许修改某些字段
        if role.is_system and role_data.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不允许修改代码"
            )

        # 更新字段
        if role_data.name is not None:
            # 检查名称是否重复
            existing = db.query(CompanyRole).filter(
                CompanyRole.company_id == company.id,
                CompanyRole.name == role_data.name,
                CompanyRole.id != role_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色名称已存在"
                )
            role.name = role_data.name

        if role_data.code is not None and not role.is_system:
            role.code = role_data.code

        if role_data.description is not None:
            role.description = role_data.description

        if role_data.permissions is not None:
            role.permissions = role_data.permissions

        if role_data.data_access_scope is not None:
            role.data_access_scope = role_data.data_access_scope

        if role_data.is_active is not None:
            role.is_active = role_data.is_active

        role.updated_by = current_user.id
        role.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(role)

        return {
            "success": True,
            "message": "角色更新成功",
            "data": {
                "id": str(role.id),
                "name": role.name,
                "code": role.code,
                "description": role.description,
                "permissions": role.permissions,
                "data_access_scope": role.data_access_scope,
                "is_active": role.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 更新角色失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失败: {str(e)}"
        )


@router.delete("/roles/{role_id}")
async def delete_company_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除企业角色（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 获取角色
        role = db.query(CompanyRole).filter(
            CompanyRole.id == role_id,
            CompanyRole.company_id == company.id
        ).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 系统角色不允许删除
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不允许删除"
            )

        # 检查是否有员工使用该角色
        employee_count = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.company_role_id == role_id
        ).count()

        if employee_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该角色还有{employee_count}名员工使用，无法删除"
            )

        # 删除角色
        db.delete(role)
        db.commit()

        return {
            "success": True,
            "message": "角色删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 删除角色失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除角色失败: {str(e)}"
        )

