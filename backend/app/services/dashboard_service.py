"""
仪表盘数据服务
提供仪表盘所需的统计数据和概览信息
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.user import User
from app.models.company import Company, CompanyEmployee, Factory
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.material import WeldingMaterial
from app.models.welder import Welder
from app.models.equipment import Equipment
from app.models.production import ProductionTask
from app.models.quality import QualityInspection
from app.core.data_access import WorkspaceContext, WorkspaceType


class DashboardService:
    """仪表盘数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview_stats(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        获取仪表盘概览统计数据
        
        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            统计数据字典
        """
        workspace_context.validate()
        
        # 根据工作区类型获取不同的统计数据
        if workspace_context.is_personal():
            return self._get_personal_stats(current_user)
        elif workspace_context.is_enterprise():
            return self._get_enterprise_stats(current_user, workspace_context)
        
        return {}
    
    def _get_personal_stats(self, user: User) -> Dict[str, Any]:
        """获取个人工作区统计数据"""

        # WPS统计
        wps_count = self.db.query(func.count(WPS.id)).filter(
            WPS.user_id == user.id,
            WPS.workspace_type == WorkspaceType.PERSONAL,
            WPS.is_active == True
        ).scalar() or 0

        # PQR统计
        pqr_count = self.db.query(func.count(PQR.id)).filter(
            PQR.user_id == user.id,
            PQR.workspace_type == WorkspaceType.PERSONAL,
            PQR.is_active == True
        ).scalar() or 0

        # pPQR统计
        ppqr_count = self.db.query(func.count(PPQR.id)).filter(
            PPQR.user_id == user.id,
            PPQR.workspace_type == WorkspaceType.PERSONAL,
            PPQR.is_active == True
        ).scalar() or 0

        # 焊材统计
        materials_count = self.db.query(func.count(WeldingMaterial.id)).filter(
            WeldingMaterial.user_id == user.id,
            WeldingMaterial.workspace_type == WorkspaceType.PERSONAL,
            WeldingMaterial.is_active == True
        ).scalar() or 0

        # 焊工统计
        welders_count = self.db.query(func.count(Welder.id)).filter(
            Welder.user_id == user.id,
            Welder.workspace_type == WorkspaceType.PERSONAL,
            Welder.is_active == True
        ).scalar() or 0

        # 设备统计
        equipment_count = self.db.query(func.count(Equipment.id)).filter(
            Equipment.user_id == user.id,
            Equipment.workspace_type == WorkspaceType.PERSONAL,
            Equipment.is_active == True
        ).scalar() or 0

        # 生产任务统计
        production_count = self.db.query(func.count(ProductionTask.id)).filter(
            ProductionTask.user_id == user.id,
            ProductionTask.workspace_type == WorkspaceType.PERSONAL,
            ProductionTask.is_active == True
        ).scalar() or 0

        # 质量检验统计
        quality_count = self.db.query(func.count(QualityInspection.id)).filter(
            QualityInspection.user_id == user.id,
            QualityInspection.workspace_type == WorkspaceType.PERSONAL,
            QualityInspection.is_active == True
        ).scalar() or 0
        
        # 存储使用情况
        storage_used_mb = user.storage_quota_used or 0
        
        # 获取会员配额限制
        from app.services.membership_service import MembershipService
        membership_service = MembershipService(self.db)
        limits = membership_service.get_membership_limits(user.member_tier)
        
        return {
            "wps_count": wps_count,
            "pqr_count": pqr_count,
            "ppqr_count": ppqr_count,
            "materials_count": materials_count,
            "welders_count": welders_count,
            "equipment_count": equipment_count,
            "production_count": production_count,
            "quality_count": quality_count,
            "storage_used_mb": storage_used_mb,
            "storage_limit_mb": limits.get("storage", 100),
            "membership_usage": {
                "wps_usage": user.wps_quota_used or 0,
                "wps_limit": limits.get("wps", 0),
                "pqr_usage": user.pqr_quota_used or 0,
                "pqr_limit": limits.get("pqr", 0),
                "ppqr_usage": user.ppqr_quota_used or 0,
                "ppqr_limit": limits.get("ppqr", 0),
            }
        }
    
    def _get_enterprise_stats(
        self,
        user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """获取企业工作区统计数据"""

        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if not company:
            return {}

        # WPS统计
        wps_count = self.db.query(func.count(WPS.id)).filter(
            WPS.company_id == workspace_context.company_id,
            WPS.workspace_type == WorkspaceType.ENTERPRISE,
            WPS.is_active == True
        ).scalar() or 0

        # PQR统计
        pqr_count = self.db.query(func.count(PQR.id)).filter(
            PQR.company_id == workspace_context.company_id,
            PQR.workspace_type == WorkspaceType.ENTERPRISE,
            PQR.is_active == True
        ).scalar() or 0

        # pPQR统计
        ppqr_count = self.db.query(func.count(PPQR.id)).filter(
            PPQR.company_id == workspace_context.company_id,
            PPQR.workspace_type == WorkspaceType.ENTERPRISE,
            PPQR.is_active == True
        ).scalar() or 0

        # 焊材统计
        materials_count = self.db.query(func.count(WeldingMaterial.id)).filter(
            WeldingMaterial.company_id == workspace_context.company_id,
            WeldingMaterial.workspace_type == WorkspaceType.ENTERPRISE,
            WeldingMaterial.is_active == True
        ).scalar() or 0

        # 焊工统计
        welders_count = self.db.query(func.count(Welder.id)).filter(
            Welder.company_id == workspace_context.company_id,
            Welder.workspace_type == WorkspaceType.ENTERPRISE,
            Welder.is_active == True
        ).scalar() or 0

        # 设备统计
        equipment_count = self.db.query(func.count(Equipment.id)).filter(
            Equipment.company_id == workspace_context.company_id,
            Equipment.workspace_type == WorkspaceType.ENTERPRISE,
            Equipment.is_active == True
        ).scalar() or 0

        # 生产任务统计
        production_count = self.db.query(func.count(ProductionTask.id)).filter(
            ProductionTask.company_id == workspace_context.company_id,
            ProductionTask.workspace_type == WorkspaceType.ENTERPRISE,
            ProductionTask.is_active == True
        ).scalar() or 0

        # 质量检验统计
        quality_count = self.db.query(func.count(QualityInspection.id)).filter(
            QualityInspection.company_id == workspace_context.company_id,
            QualityInspection.workspace_type == WorkspaceType.ENTERPRISE,
            QualityInspection.is_active == True
        ).scalar() or 0
        
        # 存储使用情况 (暂时使用默认值,因为Company模型中还没有这些字段)
        storage_used_mb = getattr(company, 'storage_quota_used', 0) or 0
        max_storage_gb = getattr(company, 'max_storage_gb', None)
        storage_limit_mb = max_storage_gb * 1024 if max_storage_gb else 1024

        # 员工数量统计
        employee_count = self.db.query(func.count(CompanyEmployee.id)).filter(
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == 'active'
        ).scalar() or 0

        # 工厂数量统计
        factory_count = self.db.query(func.count(Factory.id)).filter(
            Factory.company_id == workspace_context.company_id
        ).scalar() or 0

        return {
            "wps_count": wps_count,
            "pqr_count": pqr_count,
            "ppqr_count": ppqr_count,
            "materials_count": materials_count,
            "welders_count": welders_count,
            "equipment_count": equipment_count,
            "production_count": production_count,
            "quality_count": quality_count,
            "storage_used_mb": storage_used_mb,
            "storage_limit_mb": storage_limit_mb,
            "membership_usage": {
                "wps_usage": wps_count,  # 使用实际统计的数量
                "wps_limit": company.max_wps_records or 0,
                "pqr_usage": pqr_count,  # 使用实际统计的数量
                "pqr_limit": company.max_pqr_records or 0,
                "ppqr_usage": ppqr_count,  # 使用实际统计的数量
                "ppqr_limit": getattr(company, 'max_ppqr_records', 0) or 0,
            },
            "company_info": {
                "name": company.name,
                "employee_count": employee_count,
                "factory_count": factory_count,
            }
        }
    
    def get_recent_activities(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最近活动记录

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            limit: 返回记录数

        Returns:
            活动记录列表
        """
        activities = []

        # 获取最近的WPS记录
        if workspace_context.is_personal():
            # 个人工作区: 只查询个人工作区的WPS
            wps_query = self.db.query(WPS).filter(
                WPS.user_id == current_user.id,
                WPS.workspace_type == WorkspaceType.PERSONAL,
                WPS.is_active == True
            ).order_by(desc(WPS.created_at)).limit(limit // 3)
        else:
            # 企业工作区: 只查询企业工作区的WPS
            wps_query = self.db.query(WPS).filter(
                WPS.company_id == workspace_context.company_id,
                WPS.workspace_type == WorkspaceType.ENTERPRISE,
                WPS.is_active == True
            ).order_by(desc(WPS.created_at)).limit(limit // 3)

        for wps in wps_query:
            activities.append({
                "type": "wps",
                "id": wps.id,
                "wps_number": wps.wps_number,
                "title": wps.title or "WPS记录",
                "description": wps.title or "WPS记录",
                "status": wps.status,
                "created_at": wps.created_at.isoformat() if wps.created_at else None,
                "updated_at": wps.updated_at.isoformat() if wps.updated_at else None
            })

        # 获取最近的PQR记录
        if workspace_context.is_personal():
            # 个人工作区: 只查询个人工作区的PQR
            pqr_query = self.db.query(PQR).filter(
                PQR.user_id == current_user.id,
                PQR.workspace_type == WorkspaceType.PERSONAL,
                PQR.is_active == True
            ).order_by(desc(PQR.created_at)).limit(limit // 3)
        else:
            # 企业工作区: 只查询企业工作区的PQR
            pqr_query = self.db.query(PQR).filter(
                PQR.company_id == workspace_context.company_id,
                PQR.workspace_type == WorkspaceType.ENTERPRISE,
                PQR.is_active == True
            ).order_by(desc(PQR.created_at)).limit(limit // 3)

        for pqr in pqr_query:
            activities.append({
                "type": "pqr",
                "id": pqr.id,
                "pqr_number": pqr.pqr_number,
                "title": pqr.title or "PQR记录",
                "description": pqr.title or "PQR记录",
                "status": pqr.status,
                "qualification_date": pqr.qualification_date.isoformat() if pqr.qualification_date else None,
                "created_at": pqr.created_at.isoformat() if pqr.created_at else None,
                "updated_at": pqr.updated_at.isoformat() if pqr.updated_at else None
            })

        # 按时间排序
        activities.sort(key=lambda x: x["created_at"] or "", reverse=True)

        return activities[:limit]


def get_dashboard_service(db: Session) -> DashboardService:
    """获取仪表盘服务实例"""
    return DashboardService(db)

