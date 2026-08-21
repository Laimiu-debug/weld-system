"""
PQR (Procedure Qualification Record) service for the welding system backend.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.pqr import PQR, PQRTestSpecimen
from app.models.user import User
from app.schemas.pqr import PQRCreate, PQRUpdate, PQRTestSpecimenCreate, PQRQualificationUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext, WorkspaceType


class PQRService:
    """PQR service class."""

    def __init__(self, db: Session):
        """Initialize PQR service with database session."""
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    def get(
        self,
        db: Session,
        *,
        id: int,
        current_user: Optional[User] = None,
        workspace_context: Optional[WorkspaceContext] = None
    ) -> Optional[PQR]:
        """
        Get PQR by ID with workspace filtering.

        Args:
            db: Database session
            id: PQR ID
            current_user: Current user (optional for backward compatibility)
            workspace_context: Workspace context (optional for backward compatibility)

        Returns:
            PQR object or None
        """
        query = db.query(PQR).filter(PQR.id == id)

        # Apply workspace filter if context is provided
        if current_user and workspace_context:
            query = self.data_access.apply_workspace_filter(
                query, PQR, current_user, workspace_context
            )

        return query.first()

    def get_by_number(self, db: Session, *, pqr_number: str) -> Optional[PQR]:
        """Get PQR by PQR number."""
        return db.query(PQR).filter(PQR.pqr_number == pqr_number).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        current_user: Optional[User] = None,
        workspace_context: Optional[WorkspaceContext] = None,
        owner_id: Optional[int] = None,
        qualification_result: Optional[str] = None,
        search_term: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[PQR]:
        """
        Get multiple PQR with filtering options and workspace isolation.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Current user (required for workspace filtering)
            workspace_context: Workspace context (required for workspace filtering)
            owner_id: Filter by owner ID
            qualification_result: Filter by qualification result
            search_term: Search term for filtering
            status: Filter by status

        Returns:
            List of PQR objects
        """
        query = db.query(PQR).filter(PQR.is_active == True)

        # Apply workspace filter - CRITICAL for data isolation
        if current_user and workspace_context:
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=PQR,
                user=current_user,
                workspace_context=workspace_context,
            )

        # Apply additional filters
        if owner_id:
            query = query.filter(PQR.user_id == owner_id)

        if qualification_result:
            query = query.filter(PQR.qualification_result == qualification_result)

        if status:
            query = query.filter(PQR.status == status)

        if search_term:
            search_filter = or_(
                PQR.title.ilike(f"%{search_term}%"),
                PQR.pqr_number.ilike(f"%{search_term}%"),
                PQR.wps_number.ilike(f"%{search_term}%"),
                PQR.company.ilike(f"%{search_term}%"),
                PQR.project_name.ilike(f"%{search_term}%"),
                PQR.welding_process.ilike(f"%{search_term}%"),
                PQR.base_material_spec.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        return query.order_by(PQR.created_at.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        db: Session,
        *,
        current_user: Optional[User] = None,
        workspace_context: Optional[WorkspaceContext] = None,
        owner_id: Optional[int] = None,
        qualification_result: Optional[str] = None,
        search_term: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Count PQR with filtering options and workspace isolation.

        Args:
            db: Database session
            current_user: Current user (required for workspace filtering)
            workspace_context: Workspace context (required for workspace filtering)
            owner_id: Filter by owner ID
            qualification_result: Filter by qualification result
            search_term: Search term for filtering
            status: Filter by status

        Returns:
            Count of PQR records
        """
        query = db.query(PQR).filter(PQR.is_active == True)

        # Apply workspace filter - CRITICAL for data isolation
        if current_user and workspace_context:
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=PQR,
                user=current_user,
                workspace_context=workspace_context,
            )

        # Apply additional filters
        if owner_id:
            query = query.filter(PQR.user_id == owner_id)

        if qualification_result:
            query = query.filter(PQR.qualification_result == qualification_result)

        if status:
            query = query.filter(PQR.status == status)

        if search_term:
            search_filter = or_(
                PQR.title.ilike(f"%{search_term}%"),
                PQR.pqr_number.ilike(f"%{search_term}%"),
                PQR.wps_number.ilike(f"%{search_term}%"),
                PQR.company.ilike(f"%{search_term}%"),
                PQR.project_name.ilike(f"%{search_term}%"),
                PQR.welding_process.ilike(f"%{search_term}%"),
                PQR.base_material_spec.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        return query.count()

    def create(
        self,
        db: Session,
        *,
        obj_in: PQRCreate,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> PQR:
        """
        Create new PQR with workspace context.

        Args:
            db: Database session
            obj_in: PQR creation data
            current_user: Current user
            workspace_context: Workspace context

        Returns:
            Created PQR object
        """
        # Check if PQR number already exists in the same workspace
        existing_pqr = self.get_by_number(db, pqr_number=obj_in.pqr_number)
        if existing_pqr:
            # Check if it's in the same workspace
            if workspace_context.workspace_type == WorkspaceType.PERSONAL:
                if existing_pqr.user_id == current_user.id:
                    raise ValueError(f"PQR number {obj_in.pqr_number} already exists in your workspace")
            elif workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
                if existing_pqr.company_id == workspace_context.company_id:
                    raise ValueError(f"PQR number {obj_in.pqr_number} already exists in this company")

        # 准备数据，排除未设置的字段
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Set workspace-related fields
        workspace_fields = {
            "user_id": current_user.id,
            "workspace_type": workspace_context.workspace_type,
            "created_by": current_user.id,
            "updated_by": current_user.id,
            "owner_id": current_user.id,  # For backward compatibility
        }

        # Set company and factory for enterprise workspace
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            workspace_fields["company_id"] = workspace_context.company_id
            workspace_fields["factory_id"] = workspace_context.factory_id

        # 创建PQR对象
        db_obj = PQR(**obj_data, **workspace_fields)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: PQR,
        obj_in: PQRUpdate
    ) -> PQR:
        """Update PQR."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Check if PQR number is being changed and if it already exists
        if "pqr_number" in update_data and update_data["pqr_number"] != db_obj.pqr_number:
            existing_pqr = self.get_by_number(db, pqr_number=update_data["pqr_number"])
            if existing_pqr and existing_pqr.id != db_obj.id:
                raise ValueError(f"PQR number {update_data['pqr_number']} already exists")

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> PQR:
        """Soft delete PQR."""
        obj = db.query(PQR).get(id)
        if not obj:
            raise ValueError("PQR not found")

        obj.is_active = False
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update_qualification(
        self,
        db: Session,
        *,
        pqr_id: int,
        qualification_update: PQRQualificationUpdate
    ) -> PQR:
        """Update PQR qualification."""
        pqr = self.get(db, id=pqr_id)
        if not pqr:
            raise ValueError("PQR not found")

        update_data = qualification_update.model_dump()
        for field, value in update_data.items():
            if hasattr(pqr, field):
                setattr(pqr, field, value)

        db.add(pqr)
        db.commit()
        db.refresh(pqr)
        return pqr

    def get_specimens(self, db: Session, *, pqr_id: int) -> List[PQRTestSpecimen]:
        """Get all test specimens for a PQR."""
        return db.query(PQRTestSpecimen).filter(
            PQRTestSpecimen.pqr_id == pqr_id
        ).order_by(PQRTestSpecimen.created_at.asc()).all()

    def create_specimen(
        self,
        db: Session,
        *,
        obj_in: PQRTestSpecimenCreate
    ) -> PQRTestSpecimen:
        """Create new test specimen."""
        db_obj = PQRTestSpecimen(
            **obj_in.model_dump(),
            created_at=datetime.utcnow()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_specimen(
        self,
        db: Session,
        *,
        specimen_id: int,
        update_data: dict
    ) -> PQRTestSpecimen:
        """Update test specimen."""
        specimen = db.query(PQRTestSpecimen).get(specimen_id)
        if not specimen:
            raise ValueError("Test specimen not found")

        for field, value in update_data.items():
            if hasattr(specimen, field):
                setattr(specimen, field, value)

        db.add(specimen)
        db.commit()
        db.refresh(specimen)
        return specimen

    def delete_specimen(self, db: Session, *, specimen_id: int) -> PQRTestSpecimen:
        """Delete test specimen."""
        specimen = db.query(PQRTestSpecimen).get(specimen_id)
        if not specimen:
            raise ValueError("Test specimen not found")

        db.delete(specimen)
        db.commit()
        return specimen

    def search_pqr(
        self,
        db: Session,
        *,
        search_params: dict
    ) -> List[PQR]:
        """Advanced PQR search."""
        query = db.query(PQR).filter(PQR.is_active == True)

        # Search term
        if search_params.get("search_term"):
            search_term = search_params["search_term"]
            search_filter = or_(
                PQR.title.ilike(f"%{search_term}%"),
                PQR.pqr_number.ilike(f"%{search_term}%"),
                PQR.wps_number.ilike(f"%{search_term}%"),
                PQR.company.ilike(f"%{search_term}%"),
                PQR.project_name.ilike(f"%{search_term}%"),
                PQR.welding_process.ilike(f"%{search_term}%"),
                PQR.base_material_spec.ilike(f"%{search_term}%"),
                PQR.filler_material_classification.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)

        # Qualification result filter
        if search_params.get("qualification_result"):
            query = query.filter(PQR.qualification_result == search_params["qualification_result"])

        # Welding process filter
        if search_params.get("welding_process"):
            query = query.filter(PQR.welding_process == search_params["welding_process"])

        # Base material group filter
        if search_params.get("base_material_group"):
            query = query.filter(PQR.base_material_group == search_params["base_material_group"])

        # Company filter
        if search_params.get("company"):
            query = query.filter(PQR.company.ilike(f"%{search_params['company']}%"))

        # Date range filter
        if search_params.get("date_from"):
            query = query.filter(PQR.test_date >= search_params["date_from"])

        if search_params.get("date_to"):
            query = query.filter(PQR.test_date <= search_params["date_to"])

        # Owner filter
        if search_params.get("owner_id"):
            query = query.filter(PQR.owner_id == search_params["owner_id"])

        # Sorting
        sort_by = search_params.get("sort_by", "created_at")
        sort_order = search_params.get("sort_order", "desc")

        if hasattr(PQR, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(getattr(PQR, sort_by).desc())
            else:
                query = query.order_by(getattr(PQR, sort_by).asc())

        # Pagination
        skip = search_params.get("skip", 0)
        limit = search_params.get("limit", 100)

        return query.offset(skip).limit(limit).all()

    def get_pqr_by_qualification_result(
        self,
        db: Session,
        *,
        qualification_result: str,
        owner_id: Optional[int] = None
    ) -> List[PQR]:
        """Get PQR by qualification result."""
        query = db.query(PQR).filter(
            and_(
                PQR.qualification_result == qualification_result,
                PQR.is_active == True
            )
        )

        if owner_id:
            query = query.filter(PQR.owner_id == owner_id)

        return query.order_by(PQR.test_date.desc()).all()

    def get_pqr_by_wps_number(
        self,
        db: Session,
        *,
        wps_number: str,
        owner_id: Optional[int] = None
    ) -> List[PQR]:
        """Get PQR by WPS number."""
        query = db.query(PQR).filter(
            and_(
                PQR.wps_number.ilike(f"%{wps_number}%"),
                PQR.is_active == True
            )
        )

        if owner_id:
            query = query.filter(PQR.owner_id == owner_id)

        return query.order_by(PQR.test_date.desc()).all()

    def get_pqr_count(
        self,
        db: Session,
        *,
        owner_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get PQR count by qualification result."""
        query = db.query(PQR).filter(PQR.is_active == True)

        if owner_id:
            query = query.filter(PQR.owner_id == owner_id)

        total = query.count()
        qualified = query.filter(PQR.qualification_result == "qualified").count()
        not_qualified = query.filter(PQR.qualification_result == "not qualified").count()

        return {
            "total": total,
            "qualified": qualified,
            "not_qualified": not_qualified
        }

    def get_pqr_statistics(
        self,
        db: Session,
        *,
        owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get PQR statistics."""
        query = db.query(PQR).filter(PQR.is_active == True)

        if owner_id:
            query = query.filter(PQR.owner_id == owner_id)

        # Total count
        total_count = query.count()

        # Count by qualification result
        qualification_counts = {}
        for result in ["qualified", "not qualified"]:
            count = query.filter(PQR.qualification_result == result).count()
            qualification_counts[result] = count

        # Count by welding process
        process_counts = {}
        processes = db.query(PQR.welding_process).filter(
            and_(PQR.welding_process.isnot(None), PQR.is_active == True)
        ).distinct().all()

        for (process,) in processes:
            if process:
                count = query.filter(PQR.welding_process == process).count()
                process_counts[process] = count

        # Count by base material group
        material_counts = {}
        materials = db.query(PQR.base_material_group).filter(
            and_(PQR.base_material_group.isnot(None), PQR.is_active == True)
        ).distinct().all()

        for (material,) in materials:
            if material:
                count = query.filter(PQR.base_material_group == material).count()
                material_counts[material] = count

        # Recently tested
        recent_count = query.filter(
            PQR.test_date >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()

        # Test results summary
        tensile_pass_count = query.filter(
            PQR.tensile_test_result == "pass"
        ).count()

        bend_pass_count = query.filter(
            or_(
                PQR.root_bend_result == "pass",
                PQR.face_bend_result == "pass"
            )
        ).count()

        ndt_pass_count = query.filter(
            or_(
                PQR.rt_result == "pass",
                PQR.ut_result == "pass",
                PQR.mt_result == "pass",
                PQR.pt_result == "pass"
            )
        ).count()

        return {
            "total_count": total_count,
            "qualification_counts": qualification_counts,
            "process_counts": process_counts,
            "material_counts": material_counts,
            "recent_count": recent_count,
            "test_summary": {
                "tensile_pass_count": tensile_pass_count,
                "bend_pass_count": bend_pass_count,
                "ndt_pass_count": ndt_pass_count
            }
        }

    def get_pqr_heat_input_stats(
        self,
        db: Session,
        *,
        owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get PQR heat input statistics."""
        query = db.query(PQR).filter(
            and_(
                PQR.heat_input_calculated.isnot(None),
                PQR.is_active == True
            )
        )

        if owner_id:
            query = query.filter(PQR.owner_id == owner_id)

        # Get all heat input values
        heat_inputs = [pqr.heat_input_calculated for pqr in query.all()]

        if not heat_inputs:
            return {
                "min_heat_input": 0,
                "max_heat_input": 0,
                "avg_heat_input": 0,
                "count": 0
            }

        return {
            "min_heat_input": min(heat_inputs),
            "max_heat_input": max(heat_inputs),
            "avg_heat_input": sum(heat_inputs) / len(heat_inputs),
            "count": len(heat_inputs)
        }
