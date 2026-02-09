"""
Enterprise service for managing companies, factories, and employees.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.company import Company, Factory, CompanyEmployee
from app.models.user import User


class EnterpriseService:
    """Service for enterprise management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Company Management ====================
    
    def create_company(
        self,
        owner_id: int,
        name: str,
        membership_tier: str = "enterprise",
        **kwargs
    ) -> Company:
        """
        创建企业
        
        Args:
            owner_id: 企业所有者ID
            name: 企业名称
            membership_tier: 会员等级
            **kwargs: 其他企业信息
        
        Returns:
            Company: 创建的企业对象
        """
        # 根据会员等级设置配额
        tier_limits = self._get_tier_limits(membership_tier)
        
        company = Company(
            owner_id=owner_id,
            name=name,
            membership_tier=membership_tier,
            max_factories=tier_limits["max_factories"],
            max_employees=tier_limits["max_employees"],
            max_wps_records=tier_limits["max_wps_records"],
            max_pqr_records=tier_limits["max_pqr_records"],
            subscription_status="active",
            subscription_start_date=datetime.utcnow(),
            created_by=owner_id,
            **kwargs
        )
        
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        
        return company
    
    def get_company_by_owner(self, owner_id: int) -> Optional[Company]:
        """根据所有者ID获取企业"""
        return self.db.query(Company).filter(
            Company.owner_id == owner_id,
            Company.is_active == True
        ).first()
    
    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """根据ID获取企业"""
        return self.db.query(Company).filter(Company.id == company_id).first()
    
    def update_company(self, company_id: int, **kwargs) -> Optional[Company]:
        """更新企业信息"""
        company = self.get_company_by_id(company_id)
        if not company:
            return None
        
        for key, value in kwargs.items():
            if hasattr(company, key):
                setattr(company, key, value)
        
        company.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(company)
        
        return company
    
    # ==================== Factory Management ====================
    
    def create_factory(
        self,
        company_id: int,
        name: str,
        is_headquarters: bool = False,
        created_by: Optional[int] = None,
        **kwargs
    ) -> Factory:
        """创建工厂"""
        factory = Factory(
            company_id=company_id,
            name=name,
            is_headquarters=is_headquarters,
            created_by=created_by,
            **kwargs
        )
        
        self.db.add(factory)
        self.db.commit()
        self.db.refresh(factory)
        
        return factory
    
    def get_factories_by_company(self, company_id: int) -> List[Factory]:
        """获取企业的所有工厂"""
        return self.db.query(Factory).filter(
            Factory.company_id == company_id,
            Factory.is_active == True
        ).all()
    
    # ==================== Employee Management ====================
    
    def create_employee(
        self,
        company_id: int,
        user_id: int,
        role: str = "admin",
        employee_number: Optional[str] = None,
        factory_id: Optional[int] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        permissions: Optional[Dict[str, bool]] = None,
        data_access_scope: str = "company",
        created_by: Optional[int] = None
    ) -> CompanyEmployee:
        """
        创建企业员工
        
        Args:
            company_id: 企业ID
            user_id: 用户ID
            role: 角色 (admin, manager, employee)
            employee_number: 员工编号
            factory_id: 工厂ID
            department: 部门
            position: 职位
            permissions: 权限配置
            data_access_scope: 数据访问范围 (factory, company)
            created_by: 创建者ID
        
        Returns:
            CompanyEmployee: 创建的员工对象
        """
        # 检查是否已存在
        existing = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company_id,
            CompanyEmployee.user_id == user_id
        ).first()
        
        if existing:
            # 如果已存在，更新状态为active
            existing.status = "active"
            existing.role = role
            existing.joined_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            if factory_id:
                existing.factory_id = factory_id
            if department:
                existing.department = department
            if position:
                existing.position = position
            if permissions:
                existing.permissions = permissions
            existing.data_access_scope = data_access_scope
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # 生成员工编号
        if not employee_number:
            employee_number = self._generate_employee_number(company_id)
        
        # 设置默认权限
        if permissions is None:
            permissions = self._get_default_permissions(role)
        
        employee = CompanyEmployee(
            company_id=company_id,
            user_id=user_id,
            employee_number=employee_number,
            role=role,
            status="active",
            factory_id=factory_id,
            department=department,
            position=position,
            permissions=permissions,
            data_access_scope=data_access_scope,
            joined_at=datetime.utcnow(),
            invited_at=datetime.utcnow(),
            created_by=created_by
        )
        
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        
        return employee
    
    def get_employees_by_company(
        self,
        company_id: int,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[CompanyEmployee], int]:
        """
        获取企业员工列表
        
        Returns:
            tuple: (员工列表, 总数)
        """
        query = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company_id
        )
        
        # 状态筛选
        if status:
            query = query.filter(CompanyEmployee.status == status)
        
        # 角色筛选
        if role:
            query = query.filter(CompanyEmployee.role == role)
        
        # 搜索
        if search:
            query = query.join(User, CompanyEmployee.user_id == User.id).filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.phone.ilike(f"%{search}%"),
                    CompanyEmployee.employee_number.ilike(f"%{search}%")
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页
        employees = query.order_by(CompanyEmployee.created_at.desc()).offset(skip).limit(limit).all()
        
        return employees, total
    
    def get_employee_by_id(self, employee_id: int) -> Optional[CompanyEmployee]:
        """根据ID获取员工"""
        return self.db.query(CompanyEmployee).filter(CompanyEmployee.id == employee_id).first()
    
    def get_employee_by_user(self, company_id: int, user_id: int) -> Optional[CompanyEmployee]:
        """根据用户ID获取员工"""
        return self.db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company_id,
            CompanyEmployee.user_id == user_id
        ).first()
    
    def update_employee(self, employee_id: int, **kwargs) -> Optional[CompanyEmployee]:
        """更新员工信息"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return None
        
        for key, value in kwargs.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
        
        employee.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(employee)
        
        return employee
    
    def disable_employee(self, employee_id: int) -> bool:
        """停用员工"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return False
        
        employee.status = "inactive"
        employee.left_at = datetime.utcnow()
        employee.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def enable_employee(self, employee_id: int) -> bool:
        """启用员工"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return False
        
        employee.status = "active"
        employee.left_at = None
        employee.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def delete_employee(self, employee_id: int) -> bool:
        """删除员工"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return False
        
        self.db.delete(employee)
        self.db.commit()
        return True
    
    # ==================== Helper Methods ====================
    
    def _get_tier_limits(self, tier: str) -> Dict[str, int]:
        """
        根据会员等级获取配额限制

        根据 MEMBERSHIP_TIERS_CORRECTION.md 文档：
        - 企业版：10人员工，1个工厂
        - 企业版PRO：20人员工，3个工厂
        - 企业版PRO MAX：50人员工，5个工厂
        """
        limits = {
            "enterprise": {
                "max_factories": 1,
                "max_employees": 10,
                "max_wps_records": 200,
                "max_pqr_records": 200
            },
            "enterprise_pro": {
                "max_factories": 3,
                "max_employees": 20,
                "max_wps_records": 400,
                "max_pqr_records": 400
            },
            "enterprise_pro_max": {
                "max_factories": 5,
                "max_employees": 50,
                "max_wps_records": 500,
                "max_pqr_records": 500
            }
        }
        return limits.get(tier, limits["enterprise"])
    
    def _generate_employee_number(self, company_id: int) -> str:
        """生成员工编号"""
        # 获取该企业的员工数量
        count = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company_id
        ).count()
        
        return f"EMP{company_id:04d}{count + 1:04d}"
    
    def _get_default_permissions(self, role: str) -> Dict[str, bool]:
        """根据角色获取默认权限"""
        if role == "admin":
            return {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "materials_management": True,
                "welders_management": True,
                "equipment_management": True,
                "employee_management": True,
                "factory_management": True
            }
        elif role == "manager":
            return {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "materials_management": True,
                "welders_management": True,
                "equipment_management": False,
                "employee_management": False,
                "factory_management": False
            }
        else:  # employee
            return {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": False,
                "materials_management": False,
                "welders_management": False,
                "equipment_management": False,
                "employee_management": False,
                "factory_management": False
            }

