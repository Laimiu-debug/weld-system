"""
Enterprise management endpoints for the welding system backend.
企业会员专用API端点
"""
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.api.v1.endpoints.enterprise_deps import check_enterprise_membership
from app.core.security import get_password_hash
from app.schemas.api import success_payload
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



@router.post("/employees", response_model=Dict[str, Any])
def create_enterprise_employee(
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
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建员工失败"
        )


@router.get("/employees", response_model=Dict[str, Any])
def get_enterprise_employees(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取员工列表失败"
        )



@router.get("/employees/{employee_id}", response_model=Dict[str, Any])
def get_enterprise_employee_detail(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取员工详情失败"
        )


@router.put("/employees/{employee_id}")
def update_enterprise_employee(
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
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新员工信息失败"
        )


@router.post("/employees/{employee_id}/disable")
def disable_enterprise_employee(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用员工失败"
        )


@router.post("/employees/{employee_id}/enable")
def enable_enterprise_employee(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启用员工失败"
        )


@router.delete("/employees/{employee_id}")
def delete_enterprise_employee(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除员工失败"
        )


@router.get("/quota/employees")
def get_enterprise_employee_quota(
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

        return success_payload(quota_info)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取员工配额信息失败"
        )


@router.get("/statistics/employees")
def get_enterprise_employee_statistics(
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

        return success_payload(stats)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取员工统计数据失败"
        )
