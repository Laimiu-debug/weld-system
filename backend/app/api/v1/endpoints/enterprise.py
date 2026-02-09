"""
Enterprise management endpoints for the welding system backend.
企业会员专用API端点
"""
from typing import Any, Dict, Optional, List
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.api.deps import get_current_active_user
from app.core.security import get_password_hash
from pydantic import BaseModel, EmailStr

router = APIRouter()


# 企业员工相关的数据模型
class EmployeeCreate(BaseModel):
    """创建员工的数据模型"""
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    factory: Optional[str] = None
    permissions: Dict[str, bool] = {}
    data_access_scope: str = "factory"


class EmployeeUpdate(BaseModel):
    """更新员工的数据模型"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    factory: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None
    data_access_scope: Optional[str] = None


class EmployeeResponse(BaseModel):
    """员工响应数据模型"""
    id: str
    user_id: str
    employee_number: str
    name: str
    email: str
    phone: Optional[str]
    role: str
    status: str
    position: Optional[str]
    department: Optional[str]
    factory: Optional[str]
    permissions: Dict[str, bool]
    data_access_scope: str
    joined_at: str
    last_active_at: Optional[str]


def check_enterprise_membership(current_user: User) -> User:
    """检查用户是否为企业会员（宽松检查）"""
    # 只检查用户是否激活，允许所有激活用户访问
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )

    return current_user


@router.post("/employees", response_model=Dict[str, Any])
async def create_enterprise_employee(
    employee_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建企业员工（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee, CompanyRole

        enterprise_service = EnterpriseService(db)

        # 获取用户的企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 检查员工配额
        current_employee_count = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.status == "active"
        ).count()

        if current_employee_count >= company.max_employees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已达到员工配额上限（{company.max_employees}人）"
            )

        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == employee_data["email"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被使用"
            )

        # 创建用户账户
        new_user = User(
            email=employee_data["email"],
            username=employee_data.get("name", employee_data["email"].split("@")[0]),
            full_name=employee_data.get("name"),
            phone=employee_data.get("phone"),
            hashed_password=get_password_hash(employee_data["password"]),
            is_active=True,
            is_verified=True,  # 企业管理员创建的用户自动验证邮箱
            membership_type="enterprise",
            member_tier=company.membership_tier
        )
        db.add(new_user)
        db.flush()

        # 验证企业角色（如果提供）
        company_role_id = employee_data.get("company_role_id")
        if company_role_id:
            role = db.query(CompanyRole).filter(
                CompanyRole.id == company_role_id,
                CompanyRole.company_id == company.id,
                CompanyRole.is_active == True
            ).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色不存在或不可用"
                )

        # 创建员工记录
        new_employee = CompanyEmployee(
            company_id=company.id,
            user_id=new_user.id,
            employee_number=employee_data.get("employee_number"),
            position=employee_data.get("position"),
            department=employee_data.get("department"),
            factory_id=employee_data.get("factory_id"),
            role=employee_data.get("role", "employee"),
            company_role_id=company_role_id,
            status="active",
            data_access_scope=employee_data.get("data_access_scope", "factory"),
            permissions=employee_data.get("permissions", {}),
            joined_at=datetime.utcnow(),
            created_by=current_user.id
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)

        return {
            "success": True,
            "message": "员工创建成功",
            "data": {
                "id": str(new_employee.id),
                "user_id": str(new_user.id),
                "email": new_user.email,
                "name": new_user.full_name,
                "employee_number": new_employee.employee_number
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 创建员工失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建员工失败: {str(e)}"
        )


@router.get("/employees", response_model=Dict[str, Any])
async def get_enterprise_employees(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    role: Optional[str] = Query(None, description="角色筛选"),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业员工列表（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取用户的企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息，请联系管理员"
            )

        # 获取员工列表
        skip = (page - 1) * page_size
        employees, total = enterprise_service.get_employees_by_company(
            company_id=company.id,
            status=status,
            role=role,
            search=search,
            skip=skip,
            limit=page_size
        )

        # 格式化员工数据
        employee_list = []
        for emp in employees:
            user = emp.user
            factory = emp.factory

            # 获取企业角色信息
            from app.models.company import CompanyRole
            company_role_name = None
            if emp.company_role_id:
                company_role = db.query(CompanyRole).filter(CompanyRole.id == emp.company_role_id).first()
                if company_role:
                    company_role_name = company_role.name

            employee_list.append({
                "id": str(emp.id),
                "user_id": str(emp.user_id),
                "employee_number": emp.employee_number or "",
                "name": user.full_name or user.username or user.email,
                "email": user.email,
                "phone": user.phone or "",
                "role": emp.role,
                "company_role_id": str(emp.company_role_id) if emp.company_role_id else None,
                "company_role_name": company_role_name,
                "status": emp.status,
                "position": emp.position or "",
                "department_name": emp.department or "",
                "factory_name": factory.name if factory else "",
                "factory_id": str(emp.factory_id) if emp.factory_id else None,
                "permissions": emp.permissions or {},
                "data_access_scope": emp.data_access_scope,
                "joined_at": emp.joined_at.isoformat() if emp.joined_at else "",
                "last_active_at": emp.last_active_at.isoformat() if emp.last_active_at else None,
                "total_wps_created": emp.total_wps_created,
                "total_tasks_completed": emp.total_tasks_completed
            })

        return {
            "success": True,
            "data": {
                "items": employee_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取员工列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取员工列表失败: {str(e)}"
        )



@router.get("/employees/{employee_id}", response_model=Dict[str, Any])
async def get_enterprise_employee_detail(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业员工详细信息（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取员工信息
        employee = enterprise_service.get_employee_by_id(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="员工不存在"
            )

        # 验证员工属于当前用户的企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company or employee.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该员工信息"
            )

        user = employee.user
        factory = employee.factory

        return {
            "success": True,
            "data": {
                "id": str(employee.id),
                "user_id": str(employee.user_id),
                "employee_number": employee.employee_number or "",
                "name": user.full_name or user.username or user.email,
                "email": user.email,
                "phone": user.phone or "",
                "role": employee.role,
                "status": employee.status,
                "position": employee.position or "",
                "department": employee.department or "",
                "factory": factory.name if factory else "",
                "factory_id": str(employee.factory_id) if employee.factory_id else None,
                "permissions": employee.permissions or {},
                "data_access_scope": employee.data_access_scope,
                "joined_at": employee.joined_at.isoformat() if employee.joined_at else "",
                "last_active_at": employee.last_active_at.isoformat() if employee.last_active_at else None,
                "total_wps_created": employee.total_wps_created,
                "total_tasks_completed": employee.total_tasks_completed
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取员工详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取员工详情失败: {str(e)}"
        )


@router.put("/employees/{employee_id}")
async def update_enterprise_employee(
    employee_id: int,
    employee_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新企业员工信息（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee, CompanyRole

        enterprise_service = EnterpriseService(db)

        # 验证权限
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        employee = enterprise_service.get_employee_by_id(employee_id)
        if not employee or employee.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该员工"
            )

        # 更新员工信息
        if "position" in employee_data:
            employee.position = employee_data["position"]

        if "department" in employee_data:
            employee.department = employee_data["department"]

        if "factory_id" in employee_data:
            employee.factory_id = employee_data["factory_id"]

        if "role" in employee_data:
            employee.role = employee_data["role"]

        if "company_role_id" in employee_data:
            # 验证角色是否存在且属于该企业
            role_id = employee_data["company_role_id"]
            if role_id:
                role = db.query(CompanyRole).filter(
                    CompanyRole.id == role_id,
                    CompanyRole.company_id == company.id,
                    CompanyRole.is_active == True
                ).first()
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="角色不存在或不可用"
                    )
                employee.company_role_id = role_id
            else:
                employee.company_role_id = None

        if "permissions" in employee_data:
            employee.permissions = employee_data["permissions"]

        if "data_access_scope" in employee_data:
            employee.data_access_scope = employee_data["data_access_scope"]

        db.commit()
        db.refresh(employee)

        return {
            "success": True,
            "message": "员工信息更新成功",
            "data": {
                "id": str(employee.id),
                "company_role_id": str(employee.company_role_id) if employee.company_role_id else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ 更新员工信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新员工信息失败: {str(e)}"
        )


@router.post("/employees/{employee_id}/disable")
async def disable_enterprise_employee(
    employee_id: int,
    disable_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    停用企业员工（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 验证权限
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        employee = enterprise_service.get_employee_by_id(employee_id)
        if not employee or employee.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该员工"
            )

        # 停用员工
        success = enterprise_service.disable_employee(employee_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="停用员工失败"
            )

        return {
            "success": True,
            "message": "员工已停用"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 停用员工失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停用员工失败: {str(e)}"
        )


@router.post("/employees/{employee_id}/enable")
async def enable_enterprise_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    启用企业员工（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 验证权限
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        employee = enterprise_service.get_employee_by_id(employee_id)
        if not employee or employee.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该员工"
            )

        # 启用员工
        success = enterprise_service.enable_employee(employee_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="启用员工失败"
            )

        return {
            "success": True,
            "message": "员工已启用"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 启用员工失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启用员工失败: {str(e)}"
        )


@router.delete("/employees/{employee_id}")
async def delete_enterprise_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除企业员工（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 验证权限
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        employee = enterprise_service.get_employee_by_id(employee_id)
        if not employee or employee.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作该员工"
            )

        # 不允许删除企业所有者
        if employee.user_id == company.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除企业所有者"
            )

        # 删除员工
        success = enterprise_service.delete_employee(employee_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除员工失败"
            )

        return {
            "success": True,
            "message": "员工已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除员工失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除员工失败: {str(e)}"
        )


@router.get("/quota/employees")
async def get_enterprise_employee_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业员工配额信息（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 统计当前员工数
        current_employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.status == "active"
        ).count()

        # 获取最大员工数
        max_employees = company.max_employees

        # 计算使用百分比
        percentage = int((current_employees / max_employees * 100)) if max_employees > 0 else 0

        # 获取会员等级显示名称
        tier_names = {
            "enterprise": "企业版",
            "enterprise_pro": "企业版PRO",
            "enterprise_pro_max": "企业版PRO MAX"
        }
        tier_display = tier_names.get(company.membership_tier, company.membership_tier)

        quota_info = {
            "current": current_employees,
            "max": max_employees,
            "percentage": percentage,
            "tier": tier_display,
            "tier_code": company.membership_tier
        }

        return {
            "success": True,
            "data": quota_info
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取员工配额信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取员工配额信息失败: {str(e)}"
        )


@router.get("/statistics/employees")
async def get_enterprise_employee_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业员工统计数据（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee
        from datetime import datetime, timedelta
        from sqlalchemy import func

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 统计总员工数
        total_employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id
        ).count()

        # 统计在职员工数
        active_employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.status == "active"
        ).count()

        # 统计离职员工数
        inactive_employees = total_employees - active_employees

        # 统计本月新增员工数
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.joined_at >= month_start
        ).count()

        # 统计部门数（去重）
        departments_count = db.query(func.count(func.distinct(CompanyEmployee.department))).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.department.isnot(None),
            CompanyEmployee.department != ""
        ).scalar() or 0

        # 统计工厂数
        factories_count = len(enterprise_service.get_factories_by_company(company.id))

        # 统计本月创建的WPS数量（需要WPS表，暂时返回0）
        wps_created_this_month = 0

        # 统计本月完成的任务数量（暂时返回0）
        tasks_completed_this_month = 0

        stats = {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "inactive_employees": inactive_employees,
            "new_this_month": new_this_month,
            "departments_count": departments_count,
            "factories_count": factories_count,
            "wps_created_this_month": wps_created_this_month,
            "tasks_completed_this_month": tasks_completed_this_month
        }

        return {
            "success": True,
            "data": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取员工统计数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取员工统计数据失败: {str(e)}"
        )


# ==================== 工厂管理API ====================

@router.get("/factories")
async def get_enterprise_factories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业工厂列表（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import Factory

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 构建查询
        query = db.query(Factory).filter(Factory.company_id == company.id)

        if is_active is not None:
            query = query.filter(Factory.is_active == is_active)

        # 获取总数
        total = query.count()

        # 分页
        factories = query.offset((page - 1) * page_size).limit(page_size).all()

        # 格式化数据
        items = []
        for factory in factories:
            # 获取该工厂的员工列表
            from app.models.company import CompanyEmployee
            employees_query = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.factory_id == factory.id,
                CompanyEmployee.status == "active"
            ).all()

            # 格式化员工数据
            employees = []
            for emp in employees_query:
                user = db.query(User).filter(User.id == emp.user_id).first()
                if user:
                    employees.append({
                        "id": str(emp.id),
                        "user_id": str(emp.user_id),
                        "employee_number": emp.employee_number or "",
                        "name": user.full_name or user.username or user.email,
                        "email": user.email,
                        "phone": user.phone or "",
                        "role": emp.role,
                        "position": emp.position or "",
                        "department": emp.department or "",
                        "joined_at": emp.joined_at.isoformat() if emp.joined_at else ""
                    })

            items.append({
                "id": str(factory.id),
                "name": factory.name,
                "code": factory.code or "",
                "address": factory.address or "",
                "city": factory.city or "",
                "contact_person": factory.contact_person or "",
                "contact_phone": factory.contact_phone or "",
                "employee_count": len(employees),
                "employees": employees,  # 添加员工列表
                "is_headquarters": factory.is_headquarters,
                "is_active": factory.is_active,
                "created_at": factory.created_at.isoformat() if factory.created_at else ""
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
        print(f"❌ 获取工厂列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工厂列表失败: {str(e)}"
        )


@router.post("/factories")
async def create_enterprise_factory(
    factory_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建企业工厂（企业会员专用）
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

        # 检查工厂数量限制
        current_factories = enterprise_service.get_factories_by_company(company.id)
        if len(current_factories) >= company.max_factories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已达到工厂数量上限（{company.max_factories}个）"
            )

        # 创建工厂
        factory = enterprise_service.create_factory(
            company_id=company.id,
            name=factory_data.get("name"),
            code=factory_data.get("code"),
            address=factory_data.get("address"),
            city=factory_data.get("city"),
            contact_person=factory_data.get("contact_person"),
            contact_phone=factory_data.get("contact_phone"),
            is_headquarters=factory_data.get("is_headquarters", False),
            created_by=current_user.id
        )

        return {
            "success": True,
            "message": "工厂创建成功",
            "data": {
                "id": str(factory.id),
                "name": factory.name,
                "code": factory.code,
                "created_at": factory.created_at.isoformat() if factory.created_at else ""
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建工厂失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工厂失败: {str(e)}"
        )


@router.put("/factories/{factory_id}")
async def update_enterprise_factory(
    factory_id: int,
    factory_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新企业工厂（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import Factory

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 获取工厂
        factory = db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory or factory.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工厂不存在"
            )

        # 更新工厂信息
        if "name" in factory_data:
            factory.name = factory_data["name"]
        if "code" in factory_data:
            factory.code = factory_data["code"]
        if "address" in factory_data:
            factory.address = factory_data["address"]
        if "city" in factory_data:
            factory.city = factory_data["city"]
        if "contact_person" in factory_data:
            factory.contact_person = factory_data["contact_person"]
        if "contact_phone" in factory_data:
            factory.contact_phone = factory_data["contact_phone"]
        if "is_headquarters" in factory_data:
            factory.is_headquarters = factory_data["is_headquarters"]
        if "is_active" in factory_data:
            factory.is_active = factory_data["is_active"]

        factory.updated_by = current_user.id
        factory.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(factory)

        return {
            "success": True,
            "message": "工厂更新成功",
            "data": {
                "id": str(factory.id),
                "name": factory.name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新工厂失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工厂失败: {str(e)}"
        )


@router.delete("/factories/{factory_id}")
async def delete_enterprise_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除企业工厂（企业会员专用）
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import Factory, CompanyEmployee

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 获取工厂
        factory = db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory or factory.company_id != company.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工厂不存在"
            )

        # 不允许删除总部工厂
        if factory.is_headquarters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除总部工厂"
            )

        # 检查是否有员工
        employee_count = db.query(CompanyEmployee).filter(
            CompanyEmployee.factory_id == factory_id,
            CompanyEmployee.status == "active"
        ).count()

        if employee_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该工厂还有{employee_count}名在职员工，无法删除"
            )

        # 删除工厂
        db.delete(factory)
        db.commit()

        return {
            "success": True,
            "message": "工厂删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除工厂失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工厂失败: {str(e)}"
        )


# ==================== 部门管理API ====================

@router.get("/departments")
async def get_enterprise_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取企业部门列表（企业会员专用）
    注意：部门信息从员工表的department字段聚合而来
    """
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee
        from sqlalchemy import func, distinct

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        # 简化版本：只返回基本部门数据，避免复杂逻辑
        # 构建查询 - 按部门分组统计员工
        query = db.query(
            CompanyEmployee.department.label('department_name'),
            CompanyEmployee.factory_id.label('factory_id'),
            func.count(CompanyEmployee.id).label('employee_count')
        ).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.department.isnot(None),
            CompanyEmployee.department != "",
            CompanyEmployee.status == "active"
        )

        if factory_id:
            query = query.filter(CompanyEmployee.factory_id == factory_id)

        query = query.group_by(CompanyEmployee.department, CompanyEmployee.factory_id)

        # 获取部门数据
        departments_data = query.all()

        # 格式化数据
        items = []
        for idx, dept in enumerate(departments_data, 1):
            # 获取工厂信息
            from app.models.company import Factory
            factory = db.query(Factory).filter(Factory.id == dept.factory_id).first() if dept.factory_id else None

            # 生成部门编码
            dept_code = f"DEPT{str(idx).zfill(3)}"

            # 获取该部门的员工列表
            employees_query = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.department == dept.department_name,
                CompanyEmployee.factory_id == dept.factory_id,
                CompanyEmployee.status == "active"
            ).all()

            # 格式化员工数据
            employees = []
            for emp in employees_query:
                user = db.query(User).filter(User.id == emp.user_id).first()
                if user:
                    employees.append({
                        "id": str(emp.id),
                        "user_id": str(emp.user_id),
                        "employee_number": emp.employee_number or "",
                        "name": user.full_name or user.username or user.email,
                        "email": user.email,
                        "phone": user.phone or "",
                        "role": emp.role,
                        "position": emp.position or "",
                        "joined_at": emp.joined_at.isoformat() if emp.joined_at else ""
                    })

            items.append({
                "id": str(idx),
                "company_id": str(company.id),
                "factory_id": str(dept.factory_id) if dept.factory_id else None,
                "factory_name": factory.name if factory else "",
                "department_code": dept_code,
                "department_name": dept.department_name,
                "description": "",
                "manager_id": None,
                "manager_name": "",
                "employee_count": dept.employee_count,
                "employees": employees,  # 添加员工列表
                "created_at": datetime.utcnow().isoformat()
            })

        total = len(items)

        # 手动分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]

        return {
            "success": True,
            "data": {
                "items": paginated_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取部门列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取部门列表失败: {str(e)}"
        )


@router.post("/departments")
async def create_enterprise_department(
    department_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建企业部门（企业会员专用）
    改进：将部门信息存储在session或缓存中，以便在部门列表中显示
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

        # 生成唯一部门ID
        department_id = str(int(datetime.utcnow().timestamp()))

        # 生成部门编码（如果没有提供）
        department_code = department_data.get("department_code")
        if not department_code:
            department_code = f"DEPT{department_id[-6:]}"  # 使用时间戳后6位

        # 创建部门记录（临时存储在企业备注中或使用缓存）
        department_info = {
            "id": department_id,
            "company_id": str(company.id),
            "factory_id": department_data.get("factory_id"),
            "department_name": department_data.get("department_name"),
            "department_code": department_code,
            "description": department_data.get("description", ""),
            "manager_name": department_data.get("manager_name", ""),
            "employee_count": 0,  # 初始员工数为0
            "created_at": datetime.utcnow().isoformat()
        }

        # 创建一个虚拟员工记录来存储部门信息
        from app.models.company import CompanyEmployee
        from app.models.user import User

        # 创建系统用户用于存储部门信息
        temp_employee = CompanyEmployee(
            user_id=company.owner_id,  # 使用企业所有者ID
            company_id=company.id,
            factory_id=department_data.get("factory_id"),
            employee_number=f"DEPT_{department_code}",
            role="department",
            status="active",
            department=department_data.get("department_name"),
            position="部门",
            created_by=current_user.id,
            joined_at=datetime.utcnow()
        )

        db.add(temp_employee)
        db.commit()
        db.refresh(temp_employee)

        return {
            "success": True,
            "message": "部门创建成功",
            "data": department_info
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建部门失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建部门失败: {str(e)}"
        )


@router.put("/departments/{department_id}")
async def update_enterprise_department(
    department_id: str,
    department_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    更新企业部门（企业会员专用）
    改进：更新创建的部门记录
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

        # 检查是否为创建的部门记录（数字ID）
        if department_id.isdigit():
            # 更新部门记录
            dept_record = db.query(CompanyEmployee).filter(
                CompanyEmployee.id == int(department_id),
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.role == "department"
            ).first()

            if dept_record:
                # 更新部门信息
                if "department_name" in department_data:
                    dept_record.department = department_data["department_name"]
                if "factory_id" in department_data:
                    dept_record.factory_id = department_data["factory_id"]

                # 更新员工编号中的部门编码
                if "department_code" in department_data:
                    dept_record.employee_number = f"DEPT_{department_data['department_code']}"

                dept_record.updated_by = current_user.id
                dept_record.updated_at = datetime.utcnow()

                db.commit()
                db.refresh(dept_record)

                return {
                    "success": True,
                    "message": "部门更新成功",
                    "data": {
                        "id": department_id,
                        "department_name": dept_record.department,
                        "department_code": dept_record.employee_number.replace("DEPT_", "")
                    }
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="部门不存在"
                )
        else:
            # 对于真实部门（来自员工表），更新员工记录中的部门名称
            # 这里可以实现批量更新员工部门信息的逻辑
            return {
                "success": True,
                "message": "部门更新成功",
                "data": {
                    "id": department_id,
                    "department_name": department_data.get("department_name")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新部门失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新部门失败: {str(e)}"
        )


@router.delete("/departments/{department_id}")
async def delete_enterprise_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    删除企业部门（企业会员专用）
    改进：处理两种情况 - 创建的部门记录和聚合的部门数据
    """
    print(f"🚨 DELETE DEPARTMENT API CALLED with ID: {department_id}")
    current_user = check_enterprise_membership(current_user)

    try:
        from app.services.enterprise_service import EnterpriseService
        from app.models.company import CompanyEmployee

        enterprise_service = EnterpriseService(db)

        # 获取企业
        company = enterprise_service.get_company_by_owner(current_user.id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到企业信息"
            )

        print(f"🔍 尝试删除部门，ID: {department_id}, 类型: {type(department_id)}")

        # 情况1：检查是否为创建的部门记录（数字ID且存在于CompanyEmployee表中）
        if department_id.isdigit():
            dept_record = db.query(CompanyEmployee).filter(
                CompanyEmployee.id == int(department_id),
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.role == "department"
            ).first()

            if dept_record:
                print(f"✅ 找到创建的部门记录: {dept_record.department}")

                # 检查该部门是否有员工
                employee_count = db.query(CompanyEmployee).filter(
                    CompanyEmployee.company_id == company.id,
                    CompanyEmployee.department == dept_record.department,
                    CompanyEmployee.role != "department",
                    CompanyEmployee.status == "active"
                ).count()

                if employee_count > 0:
                    print(f"⚠️ 部门还有{employee_count}名员工，无法删除")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"该部门还有{employee_count}名员工，无法删除"
                    )

                db.delete(dept_record)
                db.commit()
                print(f"✅ 部门记录删除成功")

                return {
                    "success": True,
                    "message": "部门删除成功"
                }

        # 情况2：处理聚合的部门数据（来自员工表的department字段）
        # department_id在这种情况下是索引号，我们需要找到对应的部门名称

        # 获取所有部门并按索引查找
        departments_query = db.query(
            CompanyEmployee.department.label('department_name'),
            CompanyEmployee.factory_id.label('factory_id'),
            func.count(CompanyEmployee.id).label('employee_count')
        ).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.department.isnot(None),
            CompanyEmployee.department != "",
            CompanyEmployee.status == "active"
        ).group_by(CompanyEmployee.department, CompanyEmployee.factory_id)

        departments_data = departments_query.all()

        # 检查索引是否有效
        dept_index = int(department_id) - 1  # 转换为0-based索引
        if 0 <= dept_index < len(departments_data):
            dept = departments_data[dept_index]
            department_name = dept.department_name

            print(f"✅ 找到聚合部门: {department_name}")

            # 检查该部门是否有员工（除了查询出来的员工数）
            if dept.employee_count > 0:
                print(f"⚠️ 聚合部门还有{dept.employee_count}名员工，无法删除")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"该部门还有{dept.employee_count}名员工，无法删除。请先将员工重新分配到其他部门。"
                )

            # 如果没有员工，返回成功（实际上不需要删除任何记录，因为没有对应的记录）
            print(f"✅ 聚合部门删除成功")
            return {
                "success": True,
                "message": "部门删除成功"
            }
        else:
            print(f"❌ 未找到部门，索引超出范围: {dept_index} >= {len(departments_data)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部门不存在"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除部门失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除部门失败: {str(e)}"
        )