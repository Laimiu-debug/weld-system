"""
WPS (Welding Procedure Specification) service for the welding system backend.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.wps import WPS, WPSRevision
from app.models.user import User
from app.schemas.wps import WPSCreate, WPSUpdate, WPSRevisionCreate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext, WorkspaceType


class WPSService:
    """WPS service class with workspace context support."""

    def __init__(self, db: Session):
        """Initialize WPS service with database session."""
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get(
        self,
        db: Session,
        *,
        id: int,
        current_user: Optional[User] = None,
        workspace_context: Optional[WorkspaceContext] = None
    ) -> Optional[WPS]:
        """
        Get WPS by ID with workspace filtering.

        Args:
            db: Database session
            id: WPS ID
            current_user: Current user (optional for backward compatibility)
            workspace_context: Workspace context (optional for backward compatibility)

        Returns:
            WPS object or None
        """
        query = db.query(WPS).filter(WPS.id == id)

        # Apply workspace filter if context is provided
        if current_user and workspace_context:
            query = self.data_access.apply_workspace_filter(
                query, WPS, current_user, workspace_context
            )

        return query.first()

    def get_by_number(
        self,
        db: Session,
        *,
        wps_number: str,
        current_user: Optional[User] = None,
        workspace_context: Optional[WorkspaceContext] = None
    ) -> Optional[WPS]:
        """
        Get WPS by WPS number with workspace filtering.

        Args:
            db: Database session
            wps_number: WPS number
            current_user: Current user (optional)
            workspace_context: Workspace context (optional)

        Returns:
            WPS object or None
        """
        query = db.query(WPS).filter(WPS.wps_number == wps_number)

        # Apply workspace filter if context is provided
        if current_user and workspace_context:
            query = self.data_access.apply_workspace_filter(
                query, WPS, current_user, workspace_context
            )

        return query.first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        current_user: User,
        workspace_context: WorkspaceContext,
        owner_id: Optional[int] = None,
        status: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[WPS]:
        """
        Get multiple WPS with workspace filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current user
            workspace_context: Workspace context
            owner_id: Filter by owner ID (optional)
            status: Filter by status (optional)
            search_term: Search term (optional)

        Returns:
            List of WPS objects
        """
        # Build base query
        query = db.query(WPS).filter(WPS.is_active == True)

        # Apply workspace filter - CRITICAL for data isolation
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            # Personal workspace: only user's own WPS
            query = query.filter(
                WPS.workspace_type == WorkspaceType.PERSONAL,
                WPS.user_id == current_user.id
            )
        elif workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            # Enterprise workspace: only company's WPS
            if workspace_context.company_id:
                query = query.filter(
                    WPS.workspace_type == WorkspaceType.ENTERPRISE,
                    WPS.company_id == workspace_context.company_id
                )

                # Apply factory filter if specified
                if workspace_context.factory_id:
                    query = query.filter(WPS.factory_id == workspace_context.factory_id)
            else:
                # No company_id, return empty result
                query = query.filter(WPS.id == -1)
        else:
            # Unknown workspace type, return empty result
            query = query.filter(WPS.id == -1)

        # Apply additional filters
        if owner_id:
            query = query.filter(WPS.user_id == owner_id)

        if status:
            query = query.filter(WPS.status == status)

        if search_term:
            search_filter = or_(
                WPS.title.ilike(f"%{search_term}%"),
                WPS.wps_number.ilike(f"%{search_term}%"),
                WPS.company.ilike(f"%{search_term}%"),
                WPS.project_name.ilike(f"%{search_term}%"),
                WPS.welding_process.ilike(f"%{search_term}%"),
                WPS.base_material_spec.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Order by creation date (newest first)
        query = query.order_by(desc(WPS.created_at))

        return query.offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        *,
        obj_in: WPSCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPS:
        """
        Create new WPS with workspace context.

        Args:
            db: Database session
            obj_in: WPS creation data
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            Created WPS object

        Raises:
            ValueError: If WPS number already exists in the workspace
        """
        # Validate workspace context
        workspace_context.validate()

        # Check if WPS number already exists in the same workspace
        existing_wps = self.get_by_number(
            db,
            wps_number=obj_in.wps_number,
            current_user=current_user,
            workspace_context=workspace_context
        )
        if existing_wps:
            raise ValueError(f"WPS number {obj_in.wps_number} already exists in this workspace")

        # Determine access level
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            default_access_level = "company"
        else:
            default_access_level = "private"

        # Create WPS with workspace context
        # 新架构：直接保存所有数据到 modules_data JSONB 字段
        # 同时保留对旧字段的支持（向后兼容）

        obj_data = obj_in.model_dump()

        # 提取必要的基本字段
        basic_fields = {
            'title', 'wps_number', 'revision', 'status', 'template_id',
            'process_specification', 'company', 'project_name',
            'welding_process', 'process_type',
            'base_material_group', 'base_material_spec', 'base_material_thickness_range',
            'filler_material_spec', 'filler_material_classification', 'filler_material_diameter',
            'shielding_gas', 'gas_flow_rate', 'gas_composition',
            'current_type', 'current_polarity', 'current_range',
            'voltage_range', 'wire_feed_speed',
            'welding_speed', 'travel_speed',
            'heat_input_min', 'heat_input_max',
            'weld_passes', 'weld_layer',
            'joint_design', 'groove_type', 'groove_angle', 'root_gap', 'root_face',
            'preheat_temp_min', 'preheat_temp_max', 'interpass_temp_max',
            'pwht_required', 'pwht_temperature', 'pwht_time',
            'ndt_required', 'ndt_methods', 'mechanical_testing',
            'critical_application', 'special_requirements',
            'notes', 'supporting_documents', 'attachments',
            'reviewed_by', 'reviewed_date', 'approved_by', 'approved_date'
        }

        # 提取基本字段
        filtered_data = {k: v for k, v in obj_data.items() if k in basic_fields and v is not None}

        # 提取模块数据（新架构）
        # modules_data 包含所有模块实例的数据
        modules_data = obj_data.get('modules_data', {})

        # 为了向后兼容，也保留旧的 JSONB 字段
        # 如果提供了 modules_data，则使用它；否则使用旧字段
        if modules_data:
            filtered_data['modules_data'] = modules_data
        else:
            # 向后兼容：保留旧的 JSONB 字段
            old_jsonb_fields = {'header_info', 'summary_info', 'diagram_info', 'weld_layers', 'additional_info'}
            for field in old_jsonb_fields:
                if field in obj_data and obj_data[field] is not None:
                    filtered_data[field] = obj_data[field]

        db_obj = WPS(
            **filtered_data,
            # Data isolation fields
            user_id=current_user.id,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            access_level=getattr(obj_in, 'access_level', default_access_level),
            # Backward compatibility
            owner_id=current_user.id,
            created_by=current_user.id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: WPS,
        obj_in: WPSUpdate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPS:
        """
        Update WPS with permission check.

        Args:
            db: Database session
            db_obj: WPS object to update
            obj_in: Update data
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            Updated WPS object

        Raises:
            ValueError: If WPS number already exists or permission denied
        """
        # Check if user has permission to update this WPS
        if not self._check_update_permission(db_obj, current_user, workspace_context):
            raise ValueError("No permission to update this WPS")

        update_data = obj_in.model_dump(exclude_unset=True)

        # Check if WPS number is being changed and if it already exists
        if "wps_number" in update_data and update_data["wps_number"] != db_obj.wps_number:
            existing_wps = self.get_by_number(
                db,
                wps_number=update_data["wps_number"],
                current_user=current_user,
                workspace_context=workspace_context
            )
            if existing_wps and existing_wps.id != db_obj.id:
                raise ValueError(f"WPS number {update_data['wps_number']} already exists in this workspace")

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(
        self,
        db: Session,
        *,
        id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> WPS:
        """
        Soft delete WPS with permission check.

        Args:
            db: Database session
            id: WPS ID
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            Deleted WPS object

        Raises:
            ValueError: If WPS not found or permission denied
        """
        # Get WPS with workspace filter
        obj = self.get(db, id=id, current_user=current_user, workspace_context=workspace_context)
        if not obj:
            raise ValueError("WPS not found or no permission to access")

        # Check delete permission
        if not self._check_delete_permission(obj, current_user, workspace_context):
            raise ValueError("No permission to delete this WPS")

        obj.is_active = False
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get_revisions(self, db: Session, *, wps_id: int) -> List[WPSRevision]:
        """Get all revisions for a WPS."""
        return db.query(WPSRevision).filter(
            WPSRevision.wps_id == wps_id
        ).order_by(WPSRevision.change_date.desc()).all()

    def create_revision(
        self,
        db: Session,
        *,
        wps_id: int,
        obj_in: WPSRevisionCreate,
        changed_by: int
    ) -> WPSRevision:
        """Create new WPS revision."""
        db_obj = WPSRevision(
            **obj_in.model_dump(),
            wps_id=wps_id,
            changed_by=changed_by,
            change_date=datetime.utcnow()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self,
        db: Session,
        *,
        wps_id: int,
        status: str,
        reviewed_by: Optional[int] = None,
        approved_by: Optional[int] = None
    ) -> WPS:
        """Update WPS status."""
        wps = self.get(db, id=wps_id)
        if not wps:
            raise ValueError("WPS not found")

        wps.status = status

        if reviewed_by:
            wps.reviewed_by = reviewed_by
            wps.reviewed_date = datetime.utcnow()

        if approved_by:
            wps.approved_by = approved_by
            wps.approved_date = datetime.utcnow()

        db.add(wps)
        db.commit()
        db.refresh(wps)
        return wps

    def search_wps(
        self,
        db: Session,
        *,
        search_params: dict
    ) -> List[WPS]:
        """Advanced WPS search."""
        query = db.query(WPS).filter(WPS.is_active == True)

        # Search term
        if search_params.get("search_term"):
            search_term = search_params["search_term"]
            search_filter = or_(
                WPS.title.ilike(f"%{search_term}%"),
                WPS.wps_number.ilike(f"%{search_term}%"),
                WPS.company.ilike(f"%{search_term}%"),
                WPS.project_name.ilike(f"%{search_term}%"),
                WPS.welding_process.ilike(f"%{search_term}%"),
                WPS.base_material_spec.ilike(f"%{search_term}%"),
                WPS.filler_material_classification.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Status filter
        if search_params.get("status"):
            query = query.filter(WPS.status == search_params["status"])

        # Welding process filter
        if search_params.get("welding_process"):
            query = query.filter(WPS.welding_process == search_params["welding_process"])

        # Base material group filter
        if search_params.get("base_material_group"):
            query = query.filter(WPS.base_material_group == search_params["base_material_group"])

        # Company filter
        if search_params.get("company"):
            query = query.filter(WPS.company.ilike(f"%{search_params['company']}%"))

        # Date range filter
        if search_params.get("date_from"):
            query = query.filter(WPS.created_at >= search_params["date_from"])

        if search_params.get("date_to"):
            query = query.filter(WPS.created_at <= search_params["date_to"])

        # Owner filter
        if search_params.get("owner_id"):
            query = query.filter(WPS.owner_id == search_params["owner_id"])

        # Sorting
        sort_by = search_params.get("sort_by", "created_at")
        sort_order = search_params.get("sort_order", "desc")

        if hasattr(WPS, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(getattr(WPS, sort_by).desc())
            else:
                query = query.order_by(getattr(WPS, sort_by).asc())

        # Pagination
        skip = search_params.get("skip", 0)
        limit = search_params.get("limit", 100)

        return query.offset(skip).limit(limit).all()

    def get_wps_by_status(
        self,
        db: Session,
        *,
        status: str,
        owner_id: Optional[int] = None
    ) -> List[WPS]:
        """Get WPS by status."""
        query = db.query(WPS).filter(
            and_(WPS.status == status, WPS.is_active == True)
        )

        if owner_id:
            query = query.filter(WPS.owner_id == owner_id)

        return query.order_by(WPS.updated_at.desc()).all()

    def get_wps_by_company(
        self,
        db: Session,
        *,
        company: str,
        owner_id: Optional[int] = None
    ) -> List[WPS]:
        """Get WPS by company."""
        query = db.query(WPS).filter(
            and_(WPS.company.ilike(f"%{company}%"), WPS.is_active == True)
        )

        if owner_id:
            query = query.filter(WPS.owner_id == owner_id)

        return query.order_by(WPS.updated_at.desc()).all()

    def get_wps_count(
        self,
        db: Session,
        *,
        owner_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get WPS count by status."""
        query = db.query(WPS).filter(WPS.is_active == True)

        if owner_id:
            query = query.filter(WPS.owner_id == owner_id)

        total = query.count()
        draft = query.filter(WPS.status == "draft").count()
        approved = query.filter(WPS.status == "approved").count()
        obsolete = query.filter(WPS.status == "obsolete").count()

        return {
            "total": total,
            "draft": draft,
            "approved": approved,
            "obsolete": obsolete
        }

    def get_wps_statistics(
        self,
        db: Session,
        *,
        owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get WPS statistics."""
        query = db.query(WPS).filter(WPS.is_active == True)

        if owner_id:
            query = query.filter(WPS.owner_id == owner_id)

        # Total count
        total_count = query.count()

        # Count by status
        status_counts = {}
        for status in ["draft", "approved", "obsolete"]:
            count = query.filter(WPS.status == status).count()
            status_counts[status] = count

        # Count by welding process
        process_counts = {}
        processes = db.query(WPS.welding_process).filter(
            and_(WPS.welding_process.isnot(None), WPS.is_active == True)
        ).distinct().all()

        for (process,) in processes:
            if process:
                count = query.filter(WPS.welding_process == process).count()
                process_counts[process] = count

        # Recently created
        recent_count = query.filter(
            WPS.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()

        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "process_counts": process_counts,
            "recent_count": recent_count
        }

    # ==================== Permission Check Methods ====================

    def _check_update_permission(
        self,
        wps: WPS,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        Check if user has permission to update WPS.

        Args:
            wps: WPS object
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            True if user has permission, False otherwise
        """
        # Personal workspace: only owner can update
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            return wps.user_id == current_user.id

        # Enterprise workspace: check company membership and role
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            # Must be in the same company
            if wps.company_id != workspace_context.company_id:
                return False

            # Owner can always update
            if wps.user_id == current_user.id:
                return True

            # Check if user is company admin or has edit permission
            from app.models.company import CompanyEmployee
            employee = self.db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()

            if employee and employee.role == "admin":
                return True

            # Check access level
            if wps.access_level == "company" or wps.is_shared:
                return True

        return False

    def _check_delete_permission(
        self,
        wps: WPS,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        Check if user has permission to delete WPS.

        Args:
            wps: WPS object
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            True if user has permission, False otherwise
        """
        # Personal workspace: only owner can delete
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            return wps.user_id == current_user.id

        # Enterprise workspace: owner or admin can delete
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            # Must be in the same company
            if wps.company_id != workspace_context.company_id:
                return False

            # Owner can always delete
            if wps.user_id == current_user.id:
                return True

            # Check if user is company admin
            from app.models.company import CompanyEmployee
            employee = self.db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()

            if employee and employee.role == "admin":
                return True

        return False


# Note: WPSService now requires db parameter in __init__
# Create instance when needed with: wps_service = WPSService(db)
# For backward compatibility, we keep the old global instance pattern
class _WPSServiceSingleton:
    """Singleton wrapper for backward compatibility."""

    def __getattribute__(self, name):
        # This will be replaced by proper dependency injection in API endpoints
        raise RuntimeError(
            "WPSService now requires database session. "
            "Use WPSService(db) instead of wps_service global instance."
        )

wps_service = _WPSServiceSingleton()