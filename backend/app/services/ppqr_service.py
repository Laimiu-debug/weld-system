"""
pPQR Service
处理pPQR相关的业务逻辑
"""
from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException
from fastapi import status as http_status

from app.models.ppqr import PPQR
from app.models.pqr import PQR
from app.models.user import User
from app.core.data_access import WorkspaceContext, DataAccessMiddleware
from app.services.quota_service import QuotaService
from app.schemas.ppqr import PPQRUpdate


PPQR_EDITABLE_FIELDS = frozenset(PPQRUpdate.model_fields) - {
    "reviewed_by", "approved_by", "convert_to_pqr",
}


PPQR_TO_PQR_FIELD_MAP = {
    "title": "title",
    "company": "company",
    "project_name": "project_name",
    "test_location": "test_location",
    "welding_process": "welding_process",
    "process_type": "process_type",
    "process_specification": "process_specification",
    "base_material_group": "base_material_group",
    "base_material_spec": "base_material_spec",
    "base_material_thickness": "base_material_thickness",
    "filler_material_spec": "filler_material_spec",
    "filler_material_classification": "filler_material_classification",
    "filler_material_diameter": "filler_material_diameter",
    "shielding_gas": "shielding_gas",
    "gas_flow_rate": "gas_flow_rate",
    "gas_composition": "gas_composition",
    "current_type": "current_type",
    "actual_current": "current_actual",
    "actual_voltage": "voltage_actual",
    "actual_wire_feed_speed": "wire_feed_speed_actual",
    "actual_welding_speed": "welding_speed_actual",
    "actual_heat_input": "heat_input_calculated",
    "heat_input_min": "heat_input_range_min",
    "heat_input_max": "heat_input_range_max",
    "joint_design": "joint_design",
    "groove_type": "groove_type",
    "actual_preheat_temp": "preheat_temp_actual",
    "actual_interpass_temp": "interpass_temp_max_actual",
    "ambient_temperature": "ambient_temperature",
    "humidity": "humidity",
    "pwht_required": "pwht_performed",
    "pwht_temperature": "pwht_temperature_actual",
    "pwht_time": "pwht_time_actual",
    "visual_inspection_result": "visual_inspection_result",
    "rt_result": "rt_result",
    "ut_result": "ut_result",
    "mt_result": "mt_result",
    "pt_result": "pt_result",
    "template_id": "template_id",
    "module_data": "modules_data",
    "document_html": "document_html",
    "welder_name": "welding_operator",
    "notes": "test_notes",
    "deviation_notes": "deviation_notes",
    "recommendations": "recommendations",
    "test_reports": "test_reports",
    "attachments": "attachments",
}


def map_ppqr_to_pqr_fields(ppqr: Any) -> dict:
    """把 pPQR 可复用字段映射到 PQR 创建载荷。"""
    payload: dict = {}
    for source, target in PPQR_TO_PQR_FIELD_MAP.items():
        value = getattr(ppqr, source, None)
        if value is not None:
            payload[target] = value

    test_date = getattr(ppqr, "actual_test_date", None) or getattr(ppqr, "planned_test_date", None)
    if test_date:
        payload["test_date"] = datetime.combine(test_date, datetime.min.time()) if not isinstance(test_date, datetime) else test_date

    conclusion = getattr(ppqr, "test_conclusion", None)
    if conclusion == "qualified":
        payload["qualification_result"] = "qualified"
    elif conclusion == "failed":
        payload["qualification_result"] = "not qualified"

    payload.setdefault("title", getattr(ppqr, "title", None) or f"由 {getattr(ppqr, 'ppqr_number', 'pPQR')} 转换")
    payload.setdefault("status", "draft")
    return payload


def generate_pqr_number_from_ppqr(ppqr_number: str, suffix: int = 0) -> str:
    base = f"PQR-{ppqr_number}"
    if suffix:
        base = f"{base}-{suffix}"
    return base[:50]


class PPQRService:
    """pPQR业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        current_user: User,
        workspace_context: WorkspaceContext,
        status: Optional[str] = None,
        test_conclusion: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[PPQR]:
        """
        获取pPQR列表（带工作区上下文数据隔离）

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            current_user: 当前用户
            workspace_context: 工作区上下文
            status: 状态筛选
            test_conclusion: 试验结论筛选
            search_term: 搜索关键词

        Returns:
            pPQR列表
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 构建基础查询
        query = db.query(PPQR)

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        # 应用状态筛选
        if status:
            query = query.filter(PPQR.status == status)

        # 应用试验结论筛选
        if test_conclusion:
            query = query.filter(PPQR.test_conclusion == test_conclusion)

        # 应用搜索
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    PPQR.ppqr_number.ilike(search_pattern),
                    PPQR.title.ilike(search_pattern),
                    PPQR.test_purpose.ilike(search_pattern)
                )
            )

        # 排序和分页
        query = query.order_by(PPQR.created_at.desc())
        query = query.offset(skip).limit(limit)

        return query.all()

    def count(
        self,
        db: Session,
        *,
        current_user: User,
        workspace_context: WorkspaceContext,
        status: Optional[str] = None,
        test_conclusion: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> int:
        """
        获取pPQR总数（带工作区上下文数据隔离）

        Args:
            db: 数据库会话
            current_user: 当前用户
            workspace_context: 工作区上下文
            status: 状态筛选
            test_conclusion: 试验结论筛选
            search_term: 搜索关键词

        Returns:
            pPQR总数
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 构建基础查询
        query = db.query(func.count(PPQR.id))

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        # 应用状态筛选
        if status:
            query = query.filter(PPQR.status == status)

        # 应用试验结论筛选
        if test_conclusion:
            query = query.filter(PPQR.test_conclusion == test_conclusion)

        # 应用搜索
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    PPQR.ppqr_number.ilike(search_pattern),
                    PPQR.title.ilike(search_pattern),
                    PPQR.test_purpose.ilike(search_pattern)
                )
            )

        return query.scalar()

    def get(
        self,
        db: Session,
        *,
        id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[PPQR]:
        """
        获取单个pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            pPQR对象或None
        """
        query = db.query(PPQR).filter(PPQR.id == id)

        # 应用工作区过滤
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )

        return query.first()

    def create(
        self,
        db: Session,
        *,
        ppqr_data: dict,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> PPQR:
        """
        创建pPQR（带工作区上下文）

        Args:
            db: 数据库会话
            ppqr_data: pPQR数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            创建的pPQR对象

        Raises:
            ValueError: 如果pPQR编号已存在
        """
        # 验证工作区上下文
        workspace_context.validate()

        # 检查pPQR编号是否已存在
        existing = db.query(PPQR).filter(
            PPQR.ppqr_number == ppqr_data.get("ppqr_number")
        ).first()
        if existing:
            raise ValueError(f"pPQR编号 {ppqr_data.get('ppqr_number')} 已存在")

        # 获取模块数据（支持 module_data 和 modules_data 两种字段名）
        module_data = ppqr_data.get("module_data") or ppqr_data.get("modules_data", {})

        # 创建pPQR对象
        ppqr = PPQR(
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,  # 已经是字符串，不需要.value
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            ppqr_number=ppqr_data.get("ppqr_number"),
            title=ppqr_data.get("title"),
            revision=ppqr_data.get("revision", "A"),
            status=ppqr_data.get("status", "draft"),
            template_id=ppqr_data.get("template_id"),
            module_data=module_data,
            created_by=current_user.id  # 添加创建人ID
        )

        db.add(ppqr)
        db.commit()
        db.refresh(ppqr)

        return ppqr

    def update(
        self,
        db: Session,
        *,
        id: int,
        ppqr_data: dict,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Optional[PPQR]:
        """
        更新pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            ppqr_data: 更新数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            更新后的pPQR对象或None
        """
        ppqr = self.get(db, id=id, current_user=current_user, workspace_context=workspace_context)
        if not ppqr:
            return None

        self.data_access.check_access(current_user, ppqr, "edit", workspace_context)
        update_data = dict(ppqr_data)
        if "modules_data" in update_data:
            if "module_data" in update_data and update_data["module_data"] != update_data["modules_data"]:
                raise HTTPException(422, "module_data 与 modules_data 不能提供不同内容")
            update_data["module_data"] = update_data.pop("modules_data")
        forbidden = set(update_data) - PPQR_EDITABLE_FIELDS
        if forbidden:
            raise HTTPException(422, "包含不可编辑字段：" + ", ".join(sorted(forbidden)))
        target_status = update_data.get("status")
        if target_status is not None and target_status != ppqr.status and target_status not in {"draft", "testing", "completed"}:
            raise HTTPException(409, "转换状态必须通过转换为 PQR 操作产生")

        # 字段名映射（前端使用 modules_data，数据库使用 module_data）
        field_mapping = {
            'modules_data': 'module_data'
        }

        # 更新字段
        for key, value in update_data.items():
            # 转换字段名
            db_field_name = field_mapping.get(key, key)

            if hasattr(ppqr, db_field_name) and value is not None:
                setattr(ppqr, db_field_name, value)

        # 设置更新人
        ppqr.updated_by = current_user.id

        db.commit()
        db.refresh(ppqr)

        return ppqr

    def delete(
        self,
        db: Session,
        *,
        id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除pPQR（带工作区上下文权限检查）

        Args:
            db: 数据库会话
            id: pPQR ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            是否删除成功
        """
        ppqr = self.get(db, id=id, current_user=current_user, workspace_context=workspace_context)
        if not ppqr:
            return False

        db.delete(ppqr)
        db.commit()

        return True

    def get_statistics(
        self,
        db: Session,
        *,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> dict:
        """按工作区汇总 pPQR 状态。"""
        workspace_context.validate()
        query = db.query(PPQR).filter(PPQR.is_active == True)
        query = self.data_access.apply_workspace_filter(
            query, PPQR, current_user, workspace_context
        )
        total = query.count()
        by_status = dict(
            query.with_entities(PPQR.status, func.count(PPQR.id))
            .group_by(PPQR.status)
            .all()
        )
        converted = query.filter(
            or_(PPQR.converted_to_pqr == True, PPQR.status == "converted")
        ).count()
        return {
            "total": total,
            "converted": converted,
            "draft": int(by_status.get("draft") or 0),
            "testing": int(by_status.get("testing") or 0),
            "completed": int(by_status.get("completed") or 0),
            "by_status": {str(key): int(value) for key, value in by_status.items() if key is not None},
        }

    def convert_to_pqr(
        self,
        db: Session,
        *,
        ppqr_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
        overrides: Optional[dict] = None,
    ) -> dict:
        """将 pPQR 转换为 PQR，已转换时返回原记录。"""
        ppqr = self.get(
            db,
            id=ppqr_id,
            current_user=current_user,
            workspace_context=workspace_context,
        )
        if not ppqr:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="pPQR不存在或无权访问",
            )

        self.data_access.check_access(current_user, ppqr, "EDIT", workspace_context)

        if ppqr.converted_to_pqr_id:
            existing = db.query(PQR).filter(PQR.id == ppqr.converted_to_pqr_id).first()
            if existing:
                return {
                    "already_converted": True,
                    "pqr_id": existing.id,
                    "pqr_number": existing.pqr_number,
                    "ppqr_id": ppqr.id,
                }

        quota_service = QuotaService(db)
        quota_service.check_quota(current_user, workspace_context, "pqr", 1)

        payload = map_ppqr_to_pqr_fields(ppqr)
        if overrides:
            payload.update({key: value for key, value in overrides.items() if value is not None})

        pqr_number = payload.get("pqr_number") or generate_pqr_number_from_ppqr(ppqr.ppqr_number)
        suffix = 1
        while db.query(PQR).filter(PQR.pqr_number == pqr_number).first():
            suffix += 1
            pqr_number = generate_pqr_number_from_ppqr(ppqr.ppqr_number, suffix)
        payload["pqr_number"] = pqr_number

        allowed = {column.name for column in PQR.__table__.columns}
        filtered = {key: value for key, value in payload.items() if key in allowed}
        filtered.update({
            "user_id": current_user.id,
            "workspace_type": workspace_context.workspace_type,
            "company_id": workspace_context.company_id,
            "factory_id": workspace_context.factory_id,
            "created_by": current_user.id,
            "updated_by": current_user.id,
            "owner_id": current_user.id,
            "status": filtered.get("status") or "draft",
        })

        pqr = PQR(**filtered)
        db.add(pqr)
        db.flush()

        ppqr.converted_to_pqr = True
        ppqr.convert_to_pqr = True
        ppqr.converted_to_pqr_id = pqr.id
        ppqr.converted_at = datetime.utcnow()
        ppqr.converted_by = current_user.id
        ppqr.status = "converted"
        ppqr.updated_by = current_user.id

        quota_service.update_quota_usage(current_user, workspace_context, "pqr", 1)
        db.commit()
        db.refresh(pqr)

        return {
            "already_converted": False,
            "pqr_id": pqr.id,
            "pqr_number": pqr.pqr_number,
            "ppqr_id": ppqr.id,
        }

