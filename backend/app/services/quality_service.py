"""
Quality Service for the welding system backend.
质量管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from fastapi import status as http_status

from app.models.quality import QualityInspection, NonconformanceRecord, QualityMetric
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole, Factory
from app.schemas.quality import QualityInspectionCreate, QualityInspectionUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService


class QualityService:
    """质量管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)

    # ==================== 质量检验基础管理 ====================

    def create_quality_inspection(
        self,
        current_user: User,
        inspection_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> QualityInspection:
        """
        创建新质量检验

        Args:
            current_user: 当前用户
            inspection_data: 检验数据
            workspace_context: 工作区上下文

        Returns:
            QualityInspection: 创建的检验对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)

            # 检查配额（物理资产模块会自动跳过）
            self.quota_service.check_quota(current_user, workspace_context, "quality", 1)
            # 前置外键有效性校验，避免数据库外键错误
            if workspace_context.workspace_type == "enterprise":
                # 校验企业是否存在
                if workspace_context.company_id is not None:
                    company = self.db.query(Company).filter(Company.id == workspace_context.company_id).first()
                    if not company:
                        raise HTTPException(
                            status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="企业不存在或无权访问"
                        )
                # 校验工厂是否存在且属于该企业
                if workspace_context.factory_id is not None:
                    factory = self.db.query(Factory).filter(
                        Factory.id == workspace_context.factory_id,
                        Factory.company_id == workspace_context.company_id
                    ).first()
                    if not factory:
                        raise HTTPException(
                            status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="工厂不存在或不属于该企业"
                        )

            # 校验检验员是否存在（如果提供）
            inspector_id = inspection_data.get("inspector_id")
            if inspector_id is not None:
                inspector = self.db.query(User).filter(User.id == inspector_id).first()
                if not inspector:
                    raise HTTPException(
                        status_code=http_status.HTTP_400_BAD_REQUEST,
                        detail="检验员不存在"
                    )

            # 工厂级别数据权限：成员仅能在所属工厂创建
            if workspace_context.workspace_type == "enterprise":
                company = self.db.query(Company).filter(Company.id == workspace_context.company_id).first()
                if not company or company.owner_id != current_user.id:
                    employee = self.db.query(CompanyEmployee).filter(
                        CompanyEmployee.user_id == current_user.id,
                        CompanyEmployee.company_id == workspace_context.company_id,
                        CompanyEmployee.status == "active"
                    ).first()
                    if employee and employee.factory_id and workspace_context.factory_id and employee.factory_id != workspace_context.factory_id:
                        raise HTTPException(
                            status_code=http_status.HTTP_403_FORBIDDEN,
                            detail="权限不足：您只能在所属工厂创建数据"
                        )


            # 检查检验编号是否重复
            inspection_number = inspection_data.get("inspection_number")
            if inspection_number:
                existing = self._check_inspection_number_exists(
                    inspection_number, workspace_context
                )
                if existing:
                    raise HTTPException(
                        status_code=http_status.HTTP_400_BAD_REQUEST,
                        detail=f"检验编号 {inspection_number} 已存在"
                    )

            # 创建检验对象，处理字段映射
            inspection_data_dict = inspection_data.copy()

            # 处理字段映射：前端发送的result映射到数据库的inspection_result
            if "result" in inspection_data_dict:
                inspection_data_dict["inspection_result"] = inspection_data_dict.pop("result")

            # 移除数据库中不存在的虚拟字段
            virtual_fields = [
                "is_qualified", "user_id", "workspace_type", "access_level",
                "is_shared", "created_by", "updated_by", "welder_name",
                "inspection_method", "ndt_method", "quality_level", "weld_location",
                "equipment_id", "witness_id", "item_description", "item_quantity",
                "item_unit", "batch_number", "serial_number", "inspection_location",
                "weld_joint_number", "inspection_standard", "inspection_procedure",
                "acceptance_criteria", "actual_measurements", "defect_details",
                "defect_locations", "max_defect_severity", "corrective_actions",
                "rework_description", "follow_up_date",
                "temperature", "humidity", "environmental_conditions",
                "equipment_used", "equipment_calibration_date", "description",
                "recommendations", "report_file_url", "images", "attachments",
                "reviewed_by", "reviewed_date", "approved_by", "approved_date",
                "inspection_time", "report_date", "witness_name",
                "inspector_certification", "inspector_name", "joint_number",
                "wps_id", "pqr_id", "production_record_id",
                "defects_found", "rework_required", "follow_up_required",
                "inspection_type", "welder_id"
            ]

            for field in virtual_fields:
                if field in inspection_data_dict:
                    del inspection_data_dict[field]

            # 调试：打印最终的数据字典
            print(f"DEBUG: 最终传递给QualityInspection的数据: {inspection_data_dict}")

            inspection = QualityInspection(**inspection_data_dict)

            # 设置数据隔离字段
            inspection.owner_id = current_user.id
            inspection.company_id = workspace_context.company_id
            inspection.factory_id = workspace_context.factory_id

            # 注意：access_level字段不存在于数据库中，已移除

            # 保存到数据库
            self.db.add(inspection)
            self.db.commit()
            self.db.refresh(inspection)

            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "quality", 1)

            return inspection

        except HTTPException:
            raise
        except IntegrityError as e:
            self.db.rollback()
            msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            lower = msg.lower()
            if "unique" in lower and "inspection_number" in lower:
                detail = "检验编号已存在"
            elif "foreign key" in lower or "fk" in lower:
                detail = "关联ID无效（企业/工厂/检验员），请检查company_id、factory_id、inspector_id是否有效"
            else:
                detail = "数据库约束错误"
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建质量检验失败: {str(e)}"
            )

    def get_quality_inspection_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        inspection_type: Optional[str] = None,
        result: Optional[str] = None,
        inspector_id: Optional[int] = None
    ) -> tuple[List[QualityInspection], int]:
        """
        获取质量检验列表

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            skip: 跳过记录数
            limit: 返回记录数
            search: 搜索关键词
            inspection_type: 检验类型筛选
            result: 检验结果筛选
            inspector_id: 检验员ID筛选

        Returns:
            tuple: (检验列表, 总数)
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 检查查看权限并获取访问范围
            permission_result = self._check_list_permission(current_user, workspace_context)

            # 构建基础查询
            query = self.db.query(QualityInspection)

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query,
                QualityInspection,
                current_user,
                workspace_context
            )

            # 搜索过滤 (只使用数据库中实际存在的字段)
            if search:
                search_filter = QualityInspection.inspection_number.ilike(f"%{search}%")
                query = query.filter(search_filter)

            # 检验类型筛选 (inspection_type是虚拟字段，暂时跳过)
            # if inspection_type:
            #     query = query.filter(QualityInspection.inspection_type == inspection_type)

            # 检验结果筛选 (result映射到inspection_result)
            if result:
                query = query.filter(QualityInspection.inspection_result == result)

            # 检验员筛选
            if inspector_id:
                query = query.filter(QualityInspection.inspector_id == inspector_id)

            # 获取总数
            total = query.count()

            # 分页和排序
            inspections = query.order_by(QualityInspection.created_at.desc()).offset(skip).limit(limit).all()

            return inspections, total

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取质量检验列表失败: {str(e)}"
            )

    def get_quality_inspection_by_id(
        self,
        inspection_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> QualityInspection:
        """
        获取质量检验详情

        Args:
            inspection_id: 检验ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            QualityInspection: 检验对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询检验
            inspection = self.db.query(QualityInspection).filter(
                QualityInspection.id == inspection_id
            ).first()

            if not inspection:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="质量检验不存在"
                )

            # 检查查看权限
            self.data_access.check_access(
                current_user,
                inspection,
                "VIEW",
                workspace_context
            )

            return inspection

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取质量检验详情失败: {str(e)}"
            )

    def update_quality_inspection(
        self,
        inspection_id: int,
        current_user: User,
        inspection_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> QualityInspection:
        """
        更新质量检验

        Args:
            inspection_id: 检验ID
            current_user: 当前用户
            inspection_data: 更新数据
            workspace_context: 工作区上下文

        Returns:
            QualityInspection: 更新后的检验对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询检验
            inspection = self.db.query(QualityInspection).filter(
                QualityInspection.id == inspection_id
            ).first()

            if not inspection:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="质量检验不存在"
                )

            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                inspection,
                "EDIT",
                workspace_context
            )

            # 更新字段，处理字段映射
            inspection_data_dict = inspection_data.copy()

            # 处理字段映射：前端发送的result映射到数据库的inspection_result
            if "result" in inspection_data_dict:
                inspection_data_dict["inspection_result"] = inspection_data_dict.pop("result")

            # 只更新数据库中实际存在的字段
            for key, value in inspection_data_dict.items():
                if hasattr(inspection, key) and value is not None:
                    setattr(inspection, key, value)

            # updated_at will be automatically updated by SQLAlchemy

            self.db.commit()
            self.db.refresh(inspection)

            return inspection

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新质量检验失败: {str(e)}"
            )

    def delete_quality_inspection(
        self,
        inspection_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除质量检验（软删除）

        Args:
            inspection_id: 检验ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            bool: 是否成功
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询检验
            inspection = self.db.query(QualityInspection).filter(
                QualityInspection.id == inspection_id
            ).first()

            if not inspection:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="质量检验不存在"
                )

            # 检查删除权限
            self.data_access.check_access(
                current_user,
                inspection,
                "DELETE",
                workspace_context
            )

            # 硬删除（因为数据库没有is_active字段）
            self.db.delete(inspection)
            self.db.commit()

            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "quality", -1)

            return True

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除质量检验失败: {str(e)}"
            )

    # ==================== 权限检查辅助方法 ====================

    def _check_create_permission(self, current_user: User, workspace_context: WorkspaceContext):
        """检查创建权限"""
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if not company:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="企业不存在"
            )

        if company.owner_id == current_user.id:
            return

        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="权限不足：您不是该企业的成员"
            )

        if employee.role == "admin":
            return

        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id
            ).first()

            if role and role.permissions:
                permissions = role.permissions
                if permissions.get("quality", {}).get("create", False):
                    return

        return

    def _check_list_permission(self, current_user: User, workspace_context: WorkspaceContext) -> Dict:
        """检查查看权限"""
        if workspace_context.workspace_type == "personal":
            return {
                "can_view": True,
                "data_access_scope": "personal",
                "factory_id": None
            }

        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()

        if company and company.owner_id == current_user.id:
            return {
                "can_view": True,
                "data_access_scope": "company",
                "factory_id": None
            }

        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="权限不足：您不是该企业的成员"
            )

        if employee.role == "admin":
            return {
                "can_view": True,
                "data_access_scope": "company",
                "factory_id": None
            }

        if employee.company_role_id:
            role = self.db.query(CompanyRole).filter(
                CompanyRole.id == employee.company_role_id
            ).first()

            if role:
                if role.permissions and role.permissions.get("quality", {}).get("view", False):
                    if role.data_access_scope == "company":
                        return {
                            "can_view": True,
                            "data_access_scope": "company",
                            "factory_id": None
                        }
                    elif role.data_access_scope == "factory":
                        return {
                            "can_view": True,
                            "data_access_scope": "factory",
                            "factory_id": employee.factory_id
                        }

        return {
            "can_view": True,
            "data_access_scope": "personal",
            "factory_id": None
        }

    def _check_inspection_number_exists(
        self,
        inspection_number: str,
        workspace_context: WorkspaceContext
    ) -> bool:
        """检查检验编号是否存在"""
        query = self.db.query(QualityInspection).filter(
            QualityInspection.inspection_number == inspection_number
        )

        if workspace_context.workspace_type == "personal":
            query = query.filter(
                QualityInspection.company_id == None,
                QualityInspection.owner_id == workspace_context.user_id
            )
        else:
            query = query.filter(
                QualityInspection.company_id == workspace_context.company_id
            )

        return query.first() is not None

