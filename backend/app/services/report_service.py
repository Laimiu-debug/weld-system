"""报表统计：基于现有业务表聚合，不伪造数据。"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.models.equipment import Equipment
from app.models.material import WeldingMaterial
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.production import ProductionTask
from app.models.quality import QualityInspection
from app.models.user import User
from app.models.welder import Welder
from app.models.wps import WPS


REPORT_CATALOG = [
    {"key": "wps", "name": "WPS统计报表", "path": "/reports/wps"},
    {"key": "pqr", "name": "PQR统计报表", "path": "/reports/pqr"},
    {"key": "quality", "name": "质量检验报表", "path": "/reports"},
    {"key": "usage", "name": "使用统计报表", "path": "/reports/usage"},
    {"key": "production", "name": "生产任务报表", "path": "/production"},
]


class ReportService:
    """工作区范围内的报表聚合。"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    @staticmethod
    def get_catalog() -> list[dict[str, str]]:
        return list(REPORT_CATALOG)

    def _apply(self, query, model, user: User, workspace_context: WorkspaceContext):
        return self.data_access.apply_workspace_filter(
            query, model, user, workspace_context
        )

    def _created_between(self, query, model, start: Optional[date], end: Optional[date]):
        if start:
            query = query.filter(model.created_at >= datetime.combine(start, datetime.min.time()))
        if end:
            query = query.filter(
                model.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time())
            )
        return query

    def get_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict[str, Any]:
        workspace_context.validate()

        wps_query = self._created_between(
            self._apply(self.db.query(WPS).filter(WPS.is_active == True), WPS, current_user, workspace_context),
            WPS,
            start_date,
            end_date,
        )
        pqr_query = self._created_between(
            self._apply(self.db.query(PQR).filter(PQR.is_active == True), PQR, current_user, workspace_context),
            PQR,
            start_date,
            end_date,
        )
        ppqr_query = self._created_between(
            self._apply(self.db.query(PPQR).filter(PPQR.is_active == True), PPQR, current_user, workspace_context),
            PPQR,
            start_date,
            end_date,
        )
        quality_query = self._apply(
            self.db.query(QualityInspection),
            QualityInspection,
            current_user,
            workspace_context,
        )
        if start_date:
            quality_query = quality_query.filter(QualityInspection.inspection_date >= start_date)
        if end_date:
            quality_query = quality_query.filter(QualityInspection.inspection_date <= end_date)

        production_query = self._created_between(
            self._apply(
                self.db.query(ProductionTask).filter(ProductionTask.is_active == True),
                ProductionTask,
                current_user,
                workspace_context,
            ),
            ProductionTask,
            start_date,
            end_date,
        )
        materials_query = self._apply(
            self.db.query(WeldingMaterial).filter(WeldingMaterial.is_active == True),
            WeldingMaterial,
            current_user,
            workspace_context,
        )
        welders_query = self._apply(
            self.db.query(Welder).filter(Welder.is_active == True),
            Welder,
            current_user,
            workspace_context,
        )
        equipment_query = self._apply(
            self.db.query(Equipment).filter(Equipment.is_active == True),
            Equipment,
            current_user,
            workspace_context,
        )

        wps_total = wps_query.count()
        wps_approved = wps_query.filter(WPS.status == "approved").count()
        wps_pending = wps_query.filter(WPS.status.in_(["draft", "review", "pending"])).count()
        wps_rejected = wps_query.filter(WPS.status.in_(["rejected", "obsolete"])).count()

        pqr_total = pqr_query.count()
        pqr_completed = pqr_query.filter(PQR.status.in_(["approved", "completed"])).count()
        pqr_in_progress = pqr_query.filter(PQR.status.in_(["draft", "review"])).count()

        ppqr_total = ppqr_query.count()
        ppqr_converted = ppqr_query.filter(PPQR.converted_to_pqr == True).count()

        quality_total = quality_query.count()
        quality_passed = quality_query.filter(QualityInspection.inspection_result == "pass").count()
        quality_failed = quality_query.filter(QualityInspection.inspection_result == "fail").count()

        production_total = production_query.count()
        production_completed = production_query.filter(ProductionTask.status == "completed").count()
        production_in_progress = production_query.filter(ProductionTask.status == "in_progress").count()
        today = date.today()
        production_overdue = production_query.filter(
            ProductionTask.status.in_(["pending", "in_progress", "paused"]),
            ProductionTask.planned_end_date.isnot(None),
            ProductionTask.planned_end_date < today,
        ).count()

        low_stock = materials_query.filter(
            WeldingMaterial.min_stock_level.isnot(None),
            WeldingMaterial.current_stock <= WeldingMaterial.min_stock_level,
        ).count()
        out_of_stock = materials_query.filter(WeldingMaterial.current_stock <= 0).count()

        return {
            "wps": {
                "total": wps_total,
                "approved": wps_approved,
                "pending": wps_pending,
                "rejected": wps_rejected,
            },
            "pqr": {
                "total": pqr_total,
                "completed": pqr_completed,
                "in_progress": pqr_in_progress,
            },
            "ppqr": {
                "total": ppqr_total,
                "converted": ppqr_converted,
            },
            "quality": {
                "total": quality_total,
                "passed": quality_passed,
                "failed": quality_failed,
                "pass_rate": round((quality_passed / quality_total) * 100, 2) if quality_total else 0,
            },
            "production": {
                "total": production_total,
                "completed": production_completed,
                "in_progress": production_in_progress,
                "overdue": production_overdue,
            },
            "materials": {
                "total": materials_query.count(),
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
            },
            "welders": {"total": welders_query.count()},
            "equipment": {"total": equipment_query.count()},
        }
