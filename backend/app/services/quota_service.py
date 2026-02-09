"""
配额管理服务
Quota Management Service
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.company import Company, CompanyEmployee
from app.core.data_access import WorkspaceContext, WorkspaceType


class QuotaType:
    """配额类型常量"""
    # 文档类模块 - 所有工作区都需要检查配额
    WPS = "wps"
    PQR = "pqr"
    PPQR = "ppqr"

    # 物理资产类模块 - 个人工作区不检查配额
    EQUIPMENT = "equipment"
    MATERIALS = "materials"
    WELDERS = "welders"
    PRODUCTION = "production"
    QUALITY = "quality"

    # 其他配额类型
    STORAGE = "storage"
    EMPLOYEES = "employees"
    FACTORIES = "factories"


class QuotaService:
    """配额管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_quota(
        self,
        user: User,
        workspace_context: WorkspaceContext,
        quota_type: str,
        increment: int = 1
    ) -> bool:
        """
        检查配额是否充足

        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            quota_type: 配额类型
            increment: 需要增加的数量

        Returns:
            bool: 配额是否充足

        Raises:
            HTTPException: 如果配额不足

        Note:
            个人工作区中，物理资产类模块（设备、焊材、焊工、生产、质量）不检查配额
            文档类模块（WPS、PQR、pPQR）在所有工作区都检查配额
        """
        # 定义物理资产类模块（个人工作区不检查配额）
        physical_asset_modules = {
            QuotaType.EQUIPMENT,
            QuotaType.MATERIALS,
            QuotaType.WELDERS,
            QuotaType.PRODUCTION,
            QuotaType.QUALITY
        }

        # 个人工作区：物理资产类模块跳过配额检查
        if workspace_context.is_personal() and quota_type in physical_asset_modules:
            return True

        # 其他情况：正常检查配额
        if workspace_context.is_personal():
            return self._check_personal_quota(user, quota_type, increment)
        elif workspace_context.is_enterprise():
            return self._check_enterprise_quota(
                workspace_context.company_id,
                quota_type,
                increment
            )

        return False
    
    def _check_personal_quota(
        self,
        user: User,
        quota_type: str,
        increment: int
    ) -> bool:
        """检查个人配额"""
        # 获取配额限制
        quota_limits = self._get_personal_quota_limits(user.membership_tier)
        limit_key = f"{quota_type}_limit"
        used_key = f"{quota_type}_quota_used"
        
        if limit_key not in quota_limits:
            raise ValueError(f"不支持的配额类型: {quota_type}")
        
        limit = quota_limits[limit_key]
        used = getattr(user, used_key, 0) or 0
        
        if used + increment > limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"个人工作区{quota_type}配额不足。已使用: {used}/{limit}"
            )
        
        return True
    
    def _check_enterprise_quota(
        self,
        company_id: int,
        quota_type: str,
        increment: int
    ) -> bool:
        """检查企业配额"""
        company = self.db.query(Company).filter(
            Company.id == company_id
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业不存在"
            )

        # 定义物理资产类模块（企业工作区不检查配额）
        physical_asset_modules = {
            QuotaType.EQUIPMENT,
            QuotaType.MATERIALS,
            QuotaType.WELDERS,
            QuotaType.PRODUCTION,
            QuotaType.QUALITY
        }

        # 企业工作区：物理资产类模块跳过配额检查
        if quota_type in physical_asset_modules:
            return True

        # 获取配额限制和使用情况（只检查文档类模块）
        limit_mapping = {
            QuotaType.WPS: ("max_wps_records", "wps_quota_used"),
            QuotaType.PQR: ("max_pqr_records", "pqr_quota_used"),
            QuotaType.PPQR: ("max_ppqr_records", "ppqr_quota_used"),
            QuotaType.STORAGE: ("max_storage_gb", "storage_quota_used"),
            QuotaType.EMPLOYEES: ("max_employees", "employee_count"),
            QuotaType.FACTORIES: ("max_factories", "factory_count")
        }

        if quota_type not in limit_mapping:
            # 如果是不支持的配额类型，直接返回True（不检查）
            return True

        limit_field, used_field = limit_mapping[quota_type]

        # 检查字段是否存在
        if not hasattr(company, limit_field):
            # 如果字段不存在，跳过检查
            return True

        limit = getattr(company, limit_field, 0) or 0
        used = getattr(company, used_field, 0) or 0

        if used + increment > limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"企业{quota_type}配额不足。已使用: {used}/{limit}"
            )

        return True
    
    def increment_quota_usage(
        self,
        user: User,
        workspace_context: WorkspaceContext,
        quota_type: str,
        increment: int = 1
    ):
        """
        增加配额使用量

        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            quota_type: 配额类型
            increment: 增加的数量

        Note:
            物理资产类模块（设备、焊材、焊工、生产、质量）在所有工作区都不跟踪配额使用量
        """
        # 定义物理资产类模块
        physical_asset_modules = {
            QuotaType.EQUIPMENT,
            QuotaType.MATERIALS,
            QuotaType.WELDERS,
            QuotaType.PRODUCTION,
            QuotaType.QUALITY
        }

        # 物理资产类模块：跳过配额使用量更新（个人和企业工作区都跳过）
        if quota_type in physical_asset_modules:
            return

        if workspace_context.is_personal():
            self._increment_personal_quota(user, quota_type, increment)
        elif workspace_context.is_enterprise():
            self._increment_enterprise_quota(
                workspace_context.company_id,
                quota_type,
                increment
            )

        self.db.commit()
    
    def _increment_personal_quota(
        self,
        user: User,
        quota_type: str,
        increment: int
    ):
        """增加个人配额使用量"""
        used_key = f"{quota_type}_quota_used"
        
        if not hasattr(user, used_key):
            raise ValueError(f"不支持的配额类型: {quota_type}")
        
        current_used = getattr(user, used_key, 0) or 0
        setattr(user, used_key, current_used + increment)
    
    def _increment_enterprise_quota(
        self,
        company_id: int,
        quota_type: str,
        increment: int
    ):
        """增加企业配额使用量"""
        company = self.db.query(Company).filter(
            Company.id == company_id
        ).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业不存在"
            )

        used_mapping = {
            QuotaType.WPS: "wps_quota_used",
            QuotaType.PQR: "pqr_quota_used",
            QuotaType.PPQR: "ppqr_quota_used",
            QuotaType.EQUIPMENT: "equipment_quota_used",
            QuotaType.MATERIALS: "materials_quota_used",
            QuotaType.WELDERS: "welders_quota_used",
            QuotaType.PRODUCTION: "production_quota_used",
            QuotaType.QUALITY: "quality_quota_used",
            QuotaType.STORAGE: "storage_quota_used",
            QuotaType.EMPLOYEES: "employee_count",
            QuotaType.FACTORIES: "factory_count"
        }

        if quota_type not in used_mapping:
            # 不支持的配额类型，直接返回
            return

        used_field = used_mapping[quota_type]

        # 检查字段是否存在
        if not hasattr(company, used_field):
            # 字段不存在，跳过更新
            return

        current_used = getattr(company, used_field, 0) or 0
        setattr(company, used_field, current_used + increment)
    
    def decrement_quota_usage(
        self,
        user: User,
        workspace_context: WorkspaceContext,
        quota_type: str,
        decrement: int = 1
    ):
        """
        减少配额使用量（删除数据时调用）

        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            quota_type: 配额类型
            decrement: 减少的数量

        Note:
            物理资产类模块（设备、焊材、焊工、生产、质量）在所有工作区都不跟踪配额使用量
        """
        # 定义物理资产类模块
        physical_asset_modules = {
            QuotaType.EQUIPMENT,
            QuotaType.MATERIALS,
            QuotaType.WELDERS,
            QuotaType.PRODUCTION,
            QuotaType.QUALITY
        }

        # 物理资产类模块：跳过配额使用量更新（个人和企业工作区都跳过）
        if quota_type in physical_asset_modules:
            return

        if workspace_context.is_personal():
            self._decrement_personal_quota(user, quota_type, decrement)
        elif workspace_context.is_enterprise():
            self._decrement_enterprise_quota(
                workspace_context.company_id,
                quota_type,
                decrement
            )

        self.db.commit()
    
    def _decrement_personal_quota(
        self,
        user: User,
        quota_type: str,
        decrement: int
    ):
        """减少个人配额使用量"""
        used_key = f"{quota_type}_quota_used"
        
        if not hasattr(user, used_key):
            raise ValueError(f"不支持的配额类型: {quota_type}")
        
        current_used = getattr(user, used_key, 0) or 0
        new_used = max(0, current_used - decrement)
        setattr(user, used_key, new_used)
    
    def _decrement_enterprise_quota(
        self,
        company_id: int,
        quota_type: str,
        decrement: int
    ):
        """减少企业配额使用量"""
        company = self.db.query(Company).filter(
            Company.id == company_id
        ).first()

        if not company:
            return

        used_mapping = {
            QuotaType.WPS: "wps_quota_used",
            QuotaType.PQR: "pqr_quota_used",
            QuotaType.PPQR: "ppqr_quota_used",
            QuotaType.EQUIPMENT: "equipment_quota_used",
            QuotaType.MATERIALS: "materials_quota_used",
            QuotaType.WELDERS: "welders_quota_used",
            QuotaType.PRODUCTION: "production_quota_used",
            QuotaType.QUALITY: "quality_quota_used",
            QuotaType.STORAGE: "storage_quota_used",
            QuotaType.EMPLOYEES: "employee_count",
            QuotaType.FACTORIES: "factory_count"
        }

        if quota_type not in used_mapping:
            return

        used_field = used_mapping[quota_type]

        # 检查字段是否存在
        if not hasattr(company, used_field):
            # 字段不存在，跳过更新
            return

        current_used = getattr(company, used_field, 0) or 0
        new_used = max(0, current_used - decrement)
        setattr(company, used_field, new_used)
    
    def get_quota_info(
        self,
        user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        获取配额信息
        
        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            
        Returns:
            Dict: 配额信息
        """
        if workspace_context.is_personal():
            return self._get_personal_quota_info(user)
        elif workspace_context.is_enterprise():
            return self._get_enterprise_quota_info(workspace_context.company_id)
        
        return {}
    
    def _get_personal_quota_info(self, user: User) -> Dict[str, Any]:
        """获取个人配额信息"""
        quota_limits = self._get_personal_quota_limits(user.membership_tier)
        
        return {
            "workspace_type": WorkspaceType.PERSONAL,
            "membership_tier": user.membership_tier,
            "quotas": {
                "wps": {
                    "used": user.wps_quota_used or 0,
                    "limit": quota_limits.get("wps_limit", 0),
                    "percentage": self._calculate_percentage(
                        user.wps_quota_used or 0,
                        quota_limits.get("wps_limit", 0)
                    )
                },
                "pqr": {
                    "used": user.pqr_quota_used or 0,
                    "limit": quota_limits.get("pqr_limit", 0),
                    "percentage": self._calculate_percentage(
                        user.pqr_quota_used or 0,
                        quota_limits.get("pqr_limit", 0)
                    )
                },
                "ppqr": {
                    "used": user.ppqr_quota_used or 0,
                    "limit": quota_limits.get("ppqr_limit", 0),
                    "percentage": self._calculate_percentage(
                        user.ppqr_quota_used or 0,
                        quota_limits.get("ppqr_limit", 0)
                    )
                },
                "storage": {
                    "used": user.storage_quota_used or 0,
                    "limit": quota_limits.get("storage_limit", 0),
                    "unit": "MB",
                    "percentage": self._calculate_percentage(
                        user.storage_quota_used or 0,
                        quota_limits.get("storage_limit", 0)
                    )
                }
            }
        }
    
    def _get_enterprise_quota_info(self, company_id: int) -> Dict[str, Any]:
        """获取企业配额信息"""
        company = self.db.query(Company).filter(
            Company.id == company_id
        ).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业不存在"
            )
        
        return {
            "workspace_type": WorkspaceType.ENTERPRISE,
            "company_id": company.id,
            "company_name": company.name,
            "membership_tier": company.membership_tier,
            "quotas": {
                "wps": {
                    "used": company.wps_quota_used or 0,
                    "limit": company.max_wps_records or 0,
                    "percentage": self._calculate_percentage(
                        company.wps_quota_used or 0,
                        company.max_wps_records or 0
                    )
                },
                "pqr": {
                    "used": company.pqr_quota_used or 0,
                    "limit": company.max_pqr_records or 0,
                    "percentage": self._calculate_percentage(
                        company.pqr_quota_used or 0,
                        company.max_pqr_records or 0
                    )
                },
                "ppqr": {
                    "used": company.ppqr_quota_used or 0,
                    "limit": company.max_ppqr_records or 0,
                    "percentage": self._calculate_percentage(
                        company.ppqr_quota_used or 0,
                        company.max_ppqr_records or 0
                    )
                },
                "storage": {
                    "used": company.storage_quota_used or 0,
                    "limit": company.max_storage_gb or 0,
                    "unit": "GB",
                    "percentage": self._calculate_percentage(
                        company.storage_quota_used or 0,
                        company.max_storage_gb or 0
                    )
                },
                "employees": {
                    "used": company.employee_count or 0,
                    "limit": company.max_employees or 0,
                    "percentage": self._calculate_percentage(
                        company.employee_count or 0,
                        company.max_employees or 0
                    )
                },
                "factories": {
                    "used": company.factory_count or 0,
                    "limit": company.max_factories or 0,
                    "percentage": self._calculate_percentage(
                        company.factory_count or 0,
                        company.max_factories or 0
                    )
                }
            }
        }
    
    def _calculate_percentage(self, used: int, limit: int) -> float:
        """计算使用百分比"""
        if limit == 0:
            return 0.0
        return round((used / limit) * 100, 2)

    def update_quota_usage(
        self,
        user: User,
        workspace_context: WorkspaceContext,
        quota_type: str,
        increment: int = 1
    ):
        """
        更新配额使用量

        Args:
            user: 用户对象
            workspace_context: 工作区上下文
            quota_type: 配额类型
            increment: 增加或减少的数量（正数增加，负数减少）
        """
        if increment > 0:
            self.increment_quota_usage(user, workspace_context, quota_type, increment)
        elif increment < 0:
            self.decrement_quota_usage(user, workspace_context, quota_type, abs(increment))
    
    def _get_personal_quota_limits(self, tier: str) -> Dict[str, int]:
        """根据会员等级获取个人配额限制"""
        quotas = {
            "free": {
                "wps_limit": 5,
                "pqr_limit": 3,
                "ppqr_limit": 0,
                "equipment_limit": 0,
                "storage_limit": 100  # MB
            },
            "professional": {
                "wps_limit": 50,
                "pqr_limit": 30,
                "ppqr_limit": 30,
                "equipment_limit": 10,
                "storage_limit": 1024  # 1GB
            },
            "advanced": {
                "wps_limit": 200,
                "pqr_limit": 100,
                "ppqr_limit": 50,
                "equipment_limit": 50,
                "storage_limit": 5120  # 5GB
            },
            "flagship": {
                "wps_limit": 500,
                "pqr_limit": 300,
                "ppqr_limit": 100,
                "equipment_limit": 100,
                "storage_limit": 10240  # 10GB
            }
        }
        
        return quotas.get(tier, quotas["free"])


def get_quota_service(db: Session) -> QuotaService:
    """获取配额服务实例"""
    return QuotaService(db)

