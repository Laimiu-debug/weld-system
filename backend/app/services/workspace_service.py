"""
工作区管理服务
Workspace Management Service
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company, CompanyEmployee, Factory
from app.core.data_access import WorkspaceContext, WorkspaceType


class WorkspaceService:
    """工作区管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_workspaces(self, user: User) -> List[Dict[str, Any]]:
        """
        获取用户所有可用的工作区
        
        Args:
            user: 用户对象
            
        Returns:
            List[Dict]: 工作区列表
        """
        workspaces = []
        
        # 1. 个人工作区（所有用户都有）
        # 个人工作区使用用户的会员等级
        membership_tier = user.member_tier or 'personal_free'

        # 如果用户是企业会员，检查企业会员获得方式
        if user.membership_type == "enterprise":
            from app.models.company import Company, CompanyEmployee

            # 检查用户是否是企业的所有者（付费企业会员）
            owned_company = self.db.query(Company).filter(
                Company.owner_id == user.id,
                Company.is_active == True
            ).first()

            if owned_company:
                # 用户是企业所有者，直接付费购买的企业会员，个人工作区使用个人高级版配额
                membership_tier = 'personal_advanced'
            else:
                # 检查用户是否是企业员工（通过企业加入获得会员身份）
                enterprise_employee = self.db.query(CompanyEmployee).filter(
                    CompanyEmployee.user_id == user.id,
                    CompanyEmployee.status == "active"
                ).first()

                if enterprise_employee:
                    # 通过企业加入的会员，个人工作区使用个人专业版配额
                    membership_tier = 'personal_pro'
                else:
                    # 企业会员但没有关联企业，使用个人高级版配额作为默认
                    membership_tier = 'personal_advanced'

        personal_workspace = {
            "type": WorkspaceType.PERSONAL,
            "id": f"personal_{user.id}",
            "name": "个人工作区",
            "description": "您的私人数据空间",
            "user_id": user.id,
            "company_id": None,
            "factory_id": None,
            "is_default": True,
            "membership_tier": membership_tier,
            "quota_info": self._get_personal_quota_info_by_tier(user, membership_tier)
        }
        workspaces.append(personal_workspace)
        
        # 2. 企业工作区（如果用户是企业成员）
        if user.membership_type == "enterprise":
            enterprise_workspaces = self._get_enterprise_workspaces(user)
            workspaces.extend(enterprise_workspaces)
        
        return workspaces
    
    def _get_enterprise_workspaces(self, user: User) -> List[Dict[str, Any]]:
        """获取用户的企业工作区列表"""
        workspaces = []
        
        # 查询用户所属的所有企业
        employees = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id,
            CompanyEmployee.status == "active"
        ).all()
        
        for employee in employees:
            company = self.db.query(Company).filter(
                Company.id == employee.company_id
            ).first()
            
            if not company:
                continue
            
            # 获取工厂信息
            factory = None
            if employee.factory_id:
                factory = self.db.query(Factory).filter(
                    Factory.id == employee.factory_id
                ).first()
            
            workspace = {
                "type": WorkspaceType.ENTERPRISE,
                "id": f"enterprise_{company.id}",
                "name": company.name,
                "description": f"{company.name} - 企业共享工作区",
                "user_id": user.id,
                "company_id": company.id,
                "factory_id": employee.factory_id,
                "factory_name": factory.name if factory else None,
                "is_default": False,
                "role": employee.role,
                "company_role_id": employee.company_role_id,
                "membership_tier": company.membership_tier,
                "quota_info": self._get_company_quota_info(company)
            }
            workspaces.append(workspace)
        
        return workspaces
    
    def _get_personal_quota_info_by_tier(self, user: User, membership_tier: str) -> Dict[str, Any]:
        """根据指定会员等级获取个人配额信息"""
        from app.services.quota_service import QuotaService

        quota_service = QuotaService(self.db)
        quota_limits = quota_service._get_personal_quota_limits(membership_tier)

        def calculate_percentage(used: int, limit: int) -> float:
            """计算使用百分比"""
            if limit == 0:
                return 0.0
            return round((used / limit) * 100, 2)

        return {
            "wps": {
                "used": getattr(user, 'wps_quota_used', 0) or 0,
                "limit": quota_limits.get("wps_limit", 0),
                "percentage": calculate_percentage(
                    getattr(user, 'wps_quota_used', 0) or 0, quota_limits.get("wps_limit", 0)
                )
            },
            "pqr": {
                "used": getattr(user, 'pqr_quota_used', 0) or 0,
                "limit": quota_limits.get("pqr_limit", 0),
                "percentage": calculate_percentage(
                    getattr(user, 'pqr_quota_used', 0) or 0, quota_limits.get("pqr_limit", 0)
                )
            },
            "ppqr": {
                "used": getattr(user, 'ppqr_quota_used', 0) or 0,
                "limit": quota_limits.get("ppqr_limit", 0),
                "percentage": calculate_percentage(
                    getattr(user, 'ppqr_quota_used', 0) or 0, quota_limits.get("ppqr_limit", 0)
                )
            },
            "equipment": {
                "used": getattr(user, 'equipment_quota_used', 0) or 0,
                "limit": quota_limits.get("equipment_limit", 0),
                "percentage": calculate_percentage(
                    getattr(user, 'equipment_quota_used', 0) or 0, quota_limits.get("equipment_limit", 0)
                )
            },
            "storage": {
                "used": getattr(user, 'storage_quota_used', 0) or 0,
                "limit": quota_limits.get("storage_limit", 0),
                "percentage": calculate_percentage(
                    getattr(user, 'storage_quota_used', 0) or 0, quota_limits.get("storage_limit", 0)
                )
            }
        }

    def _get_personal_quota_info(self, user: User) -> Dict[str, Any]:
        """获取个人配额信息"""
        return self._get_personal_quota_info_by_tier(user, user.member_tier or 'personal_free')
    
    def _get_company_quota_info(self, company: Company) -> Dict[str, Any]:
        """获取企业配额信息"""
        def calculate_percentage(used: int, limit: int) -> float:
            """计算使用百分比"""
            if limit == 0:
                return 0.0
            return round((used / limit) * 100, 2)

        # 计算实际的员工和工厂数量
        employee_count = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.status == "active"
        ).count()

        factory_count = self.db.query(Factory).filter(
            Factory.company_id == company.id,
            Factory.is_active == True
        ).count()

        return {
            "wps": {
                "used": getattr(company, 'wps_quota_used', 0) or 0,
                "limit": getattr(company, 'max_wps_records', 0) or 0,
                "percentage": calculate_percentage(
                    getattr(company, 'wps_quota_used', 0) or 0,
                    getattr(company, 'max_wps_records', 0) or 0
                )
            },
            "pqr": {
                "used": getattr(company, 'pqr_quota_used', 0) or 0,
                "limit": getattr(company, 'max_pqr_records', 0) or 0,
                "percentage": calculate_percentage(
                    getattr(company, 'pqr_quota_used', 0) or 0,
                    getattr(company, 'max_pqr_records', 0) or 0
                )
            },
            "ppqr": {
                "used": getattr(company, 'ppqr_quota_used', 0) or 0,
                "limit": getattr(company, 'max_ppqr_records', 0) or 0,
                "percentage": calculate_percentage(
                    getattr(company, 'ppqr_quota_used', 0) or 0,
                    getattr(company, 'max_ppqr_records', 0) or 0
                )
            },
            "equipment": {
                "used": getattr(company, 'equipment_quota_used', 0) or 0,
                "limit": getattr(company, 'max_equipment', 50) or 50,  # 默认值
                "percentage": calculate_percentage(
                    getattr(company, 'equipment_quota_used', 0) or 0,
                    getattr(company, 'max_equipment', 50) or 50
                )
            },
            "storage": {
                "used": getattr(company, 'storage_quota_used', 0) or 0,
                "limit": getattr(company, 'max_storage_mb', 10240) or 10240,  # 默认10GB
                "percentage": calculate_percentage(
                    getattr(company, 'storage_quota_used', 0) or 0,
                    getattr(company, 'max_storage_mb', 10240) or 10240
                )
            },
            "employees": {
                "used": employee_count,
                "limit": getattr(company, 'max_employees', 10) or 10,
                "percentage": calculate_percentage(
                    employee_count, getattr(company, 'max_employees', 10) or 10
                )
            },
            "factories": {
                "used": factory_count,
                "limit": getattr(company, 'max_factories', 1) or 1,
                "percentage": calculate_percentage(
                    factory_count, getattr(company, 'max_factories', 1) or 1
                )
            }
        }
    
    def _get_quota_limits_by_tier(self, tier: str) -> Dict[str, int]:
        """根据会员等级获取配额限制"""
        # 个人会员配额
        personal_quotas = {
            "personal_free": {
                "wps_limit": 5,
                "pqr_limit": 3,
                "ppqr_limit": 0,
                "equipment_limit": 0,
                "storage_limit": 100  # MB
            },
            "personal_pro": {
                "wps_limit": 50,
                "pqr_limit": 30,
                "ppqr_limit": 30,
                "equipment_limit": 10,
                "storage_limit": 1024  # 1GB
            },
            "personal_advanced": {
                "wps_limit": 200,
                "pqr_limit": 100,
                "ppqr_limit": 50,
                "equipment_limit": 50,
                "storage_limit": 5120  # 5GB
            },
            "personal_flagship": {
                "wps_limit": 500,
                "pqr_limit": 300,
                "ppqr_limit": 100,
                "equipment_limit": 100,
                "storage_limit": 10240  # 10GB
            },
            # 企业会员配额（用于个人工作区）
            "enterprise": {
                "wps_limit": 200,
                "pqr_limit": 100,
                "ppqr_limit": 50,
                "equipment_limit": 100,
                "storage_limit": 10240  # 10GB
            },
            "enterprise_pro": {
                "wps_limit": 500,
                "pqr_limit": 300,
                "ppqr_limit": 100,
                "equipment_limit": 200,
                "storage_limit": 20480  # 20GB
            },
            "enterprise_pro_max": {
                "wps_limit": 1000,
                "pqr_limit": 500,
                "ppqr_limit": 200,
                "equipment_limit": 500,
                "storage_limit": 51200  # 50GB
            }
        }

        # 兼容旧的会员等级名称
        legacy_mapping = {
            "free": "personal_free",
            "professional": "personal_pro",
            "advanced": "personal_advanced",
            "flagship": "personal_flagship"
        }

        normalized_tier = legacy_mapping.get(tier, tier)
        return personal_quotas.get(normalized_tier, personal_quotas["personal_free"])
    
    def create_workspace_context(
        self,
        user: User,
        workspace_id: str
    ) -> WorkspaceContext:
        """
        创建工作区上下文
        
        Args:
            user: 用户对象
            workspace_id: 工作区ID（格式：personal_{user_id} 或 enterprise_{company_id}）
            
        Returns:
            WorkspaceContext: 工作区上下文对象
            
        Raises:
            HTTPException: 如果工作区不存在或用户无权访问
        """
        # 解析工作区ID
        parts = workspace_id.split("_")
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的工作区ID格式"
            )
        
        workspace_type, workspace_identifier = parts
        
        # 个人工作区
        if workspace_type == "personal":
            if int(workspace_identifier) != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此个人工作区"
                )
            
            return WorkspaceContext(
                user_id=user.id,
                workspace_type=WorkspaceType.PERSONAL
            )
        
        # 企业工作区
        elif workspace_type == "enterprise":
            company_id = int(workspace_identifier)
            
            # 验证用户是否是企业成员
            employee = self.db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.company_id == company_id,
                CompanyEmployee.status == "active"
            ).first()
            
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您不是该企业的成员"
                )
            
            return WorkspaceContext(
                user_id=user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=company_id,
                factory_id=employee.factory_id
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的工作区类型"
            )
    
    def validate_workspace_access(
        self,
        user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        验证用户对工作区的访问权限
        
        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            
        Returns:
            bool: 是否有权限
            
        Raises:
            HTTPException: 如果没有权限
        """
        # 个人工作区：只能访问自己的
        if workspace_context.is_personal():
            if workspace_context.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此个人工作区"
                )
            return True
        
        # 企业工作区：必须是企业成员
        if workspace_context.is_enterprise():
            employee = self.db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()
            
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您不是该企业的成员"
                )
            
            return True
        
        return False
    
    def get_default_workspace(self, user: User) -> Dict[str, Any]:
        """
        获取用户的默认工作区

        优先级逻辑：
        1. 优先返回个人工作区（用户登录后默认进入个人工作区）
        2. 如果没有个人工作区，返回企业工作区

        Args:
            user: 用户对象

        Returns:
            Dict: 默认工作区信息
        """
        workspaces = self.get_user_workspaces(user)

        if not workspaces:
            return None

        # 优先级：个人工作区 > 企业工作区
        # 首先查找个人工作区
        for workspace in workspaces:
            if workspace["type"] == WorkspaceType.PERSONAL:
                return workspace

        # 如果没有个人工作区，返回企业工作区
        for workspace in workspaces:
            if workspace["type"] == WorkspaceType.ENTERPRISE:
                return workspace

        # 如果都没有，返回第一个（作为fallback）
        return workspaces[0]
    
    def switch_workspace(
        self,
        user: User,
        target_workspace_id: str
    ) -> Dict[str, Any]:
        """
        切换工作区
        
        Args:
            user: 用户对象
            target_workspace_id: 目标工作区ID
            
        Returns:
            Dict: 切换后的工作区信息
            
        Raises:
            HTTPException: 如果切换失败
        """
        # 创建工作区上下文（会自动验证权限）
        workspace_context = self.create_workspace_context(user, target_workspace_id)
        
        # 获取工作区详细信息
        workspaces = self.get_user_workspaces(user)
        for workspace in workspaces:
            if workspace["id"] == target_workspace_id:
                return workspace
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作区不存在"
        )


def get_workspace_service(db: Session) -> WorkspaceService:
    """获取工作区服务实例"""
    return WorkspaceService(db)

