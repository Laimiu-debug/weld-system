"""焊工履历相关：工作记录 / 培训 / 考核 / 工作履历。

由 WelderService 混入，保持对外 API 不变。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from app.core.data_access import WorkspaceContext


class WelderCareerMixin:
    @staticmethod
    def _career_record_dict(record: Any) -> dict:
        """Serialize a career row, including update audit fields."""
        result: dict[str, Any] = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            result[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
        return result

    def _update_career_record(
        self,
        model: Any,
        label: str,
        welder_id: int,
        record_id: int,
        record_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext,
    ) -> dict:
        welder = self.get_welder_by_id(welder_id, current_user, workspace_context)
        record = self.db.query(model).filter(
            model.id == record_id,
            model.welder_id == welder_id,
        ).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label}不存在")
        self.data_access.check_access(current_user, welder, "EDIT", workspace_context)
        protected = {"id", "welder_id", "workspace_type", "user_id", "company_id", "factory_id", "created_by", "created_at"}
        for key, value in record_data.items():
            if key not in protected and hasattr(record, key):
                setattr(record, key, value)
        if hasattr(record, "updated_by"):
            record.updated_by = current_user.id
        if hasattr(record, "updated_at"):
            record.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(record)
        return self._career_record_dict(record)

    # ==================== 工作经历管理 ====================

    def get_work_records(
        self,
        welder_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> tuple[list[dict], int]:
        """获取焊工工作记录列表"""
        try:
            from app.models.welder import WelderWorkRecord

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 构建查询
            query = self.db.query(WelderWorkRecord).filter(
                WelderWorkRecord.welder_id == welder_id
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=WelderWorkRecord,
                user=current_user,
                workspace_context=workspace_context
            )

            # 按日期倒序排列
            query = query.order_by(WelderWorkRecord.work_date.desc())

            # 获取记录
            records = query.all()
            total = query.count()

            # 转换为字典
            records_list = [
                {
                    "id": record.id,
                    "welder_id": record.welder_id,
                    "work_date": record.work_date.isoformat() if record.work_date else None,
                    "work_shift": record.work_shift,
                    "work_hours": record.work_hours,
                    "welding_process": record.welding_process,
                    "welding_position": record.welding_position,
                    "base_material": record.base_material,
                    "filler_material": record.filler_material,
                    "weld_length": record.weld_length,
                    "weld_weight": record.weld_weight,
                    "quality_result": record.quality_result,
                    "defect_count": record.defect_count,
                    "rework_count": record.rework_count,
                    "production_task_id": record.production_task_id,
                    "wps_id": record.wps_id,
                    "notes": record.notes,
                    "created_by": record.created_by,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "updated_by": record.updated_by,
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                }
                for record in records
            ]

            return records_list, total

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取工作记录失败: {str(e)}"
            )

    def add_work_record(
        self,
        welder_id: int,
        record_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> dict:
        """添加焊工工作记录"""
        try:
            from app.models.welder import WelderWorkRecord

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 检查创建权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 添加记录需要编辑权限
                workspace_context
            )

            # 创建工作记录
            work_record = WelderWorkRecord(
                welder_id=welder_id,
                workspace_type=workspace_context.workspace_type,
                user_id=workspace_context.user_id,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                **record_data,
                created_by=current_user.id
            )

            self.db.add(work_record)
            self.db.commit()
            self.db.refresh(work_record)

            # 返回记录信息
            return {
                "id": work_record.id,
                "welder_id": work_record.welder_id,
                "work_date": work_record.work_date.isoformat() if work_record.work_date else None,
                "work_shift": work_record.work_shift,
                "work_hours": work_record.work_hours,
                "welding_process": work_record.welding_process,
                "welding_position": work_record.welding_position,
                "base_material": work_record.base_material,
                "filler_material": work_record.filler_material,
                "weld_length": work_record.weld_length,
                "weld_weight": work_record.weld_weight,
                "quality_result": work_record.quality_result,
                "defect_count": work_record.defect_count,
                "rework_count": work_record.rework_count,
                "production_task_id": work_record.production_task_id,
                "wps_id": work_record.wps_id,
                "notes": work_record.notes,
                "created_by": work_record.created_by,
                "created_at": work_record.created_at.isoformat() if work_record.created_at else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"添加工作记录失败: {str(e)}"
            )

    def update_work_record(self, welder_id: int, record_id: int, record_data: dict, current_user: Any, workspace_context: WorkspaceContext) -> dict:
        from app.models.welder import WelderWorkRecord
        try:
            return self._update_career_record(WelderWorkRecord, "工作记录", welder_id, record_id, record_data, current_user, workspace_context)
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"更新工作记录失败: {e}")

    def delete_work_record(
        self,
        welder_id: int,
        record_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> None:
        """删除焊工工作记录"""
        try:
            from app.models.welder import WelderWorkRecord

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 查询记录
            record = self.db.query(WelderWorkRecord).filter(
                WelderWorkRecord.id == record_id,
                WelderWorkRecord.welder_id == welder_id
            ).first()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工作记录不存在"
                )

            # 检查删除权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 删除记录需要编辑权限
                workspace_context
            )

            self.db.delete(record)
            self.db.commit()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除工作记录失败: {str(e)}"
            )

    # ==================== 培训记录管理 ====================

    def get_training_records(
        self,
        welder_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> tuple[list[dict], int]:
        """获取焊工培训记录列表"""
        try:
            from app.models.welder import WelderTraining

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 构建查询
            query = self.db.query(WelderTraining).filter(
                WelderTraining.welder_id == welder_id
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=WelderTraining,
                user=current_user,
                workspace_context=workspace_context
            )

            # 按开始日期倒序排列
            query = query.order_by(WelderTraining.start_date.desc())

            # 获取记录
            records = query.all()
            total = query.count()

            # 转换为字典
            records_list = [
                {
                    "id": record.id,
                    "welder_id": record.welder_id,
                    "training_code": record.training_code,
                    "training_name": record.training_name,
                    "training_type": record.training_type,
                    "training_category": record.training_category,
                    "start_date": record.start_date.isoformat() if record.start_date else None,
                    "end_date": record.end_date.isoformat() if record.end_date else None,
                    "duration_hours": record.duration_hours,
                    "training_organization": record.training_organization,
                    "trainer_name": record.trainer_name,
                    "training_location": record.training_location,
                    "training_content": record.training_content,
                    "training_objectives": record.training_objectives,
                    "training_materials": record.training_materials,
                    "assessment_method": record.assessment_method,
                    "assessment_score": record.assessment_score,
                    "assessment_result": record.assessment_result,
                    "pass_status": record.pass_status,
                    "certificate_issued": record.certificate_issued,
                    "certificate_number": record.certificate_number,
                    "certificate_file_url": record.certificate_file_url,
                    "notes": record.notes,
                    "attachments": record.attachments,
                    "created_by": record.created_by,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "updated_by": record.updated_by,
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                }
                for record in records
            ]

            return records_list, total

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取培训记录失败: {str(e)}"
            )

    def add_training_record(
        self,
        welder_id: int,
        record_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> dict:
        """添加焊工培训记录"""
        try:
            from app.models.welder import WelderTraining

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 检查创建权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 添加记录需要编辑权限
                workspace_context
            )

            # 创建培训记录
            new_record = WelderTraining(
                welder_id=welder_id,
                workspace_type=workspace_context.workspace_type,
                user_id=workspace_context.user_id,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                created_by=current_user.id,
                **record_data
            )

            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)

            # 转换为字典返回
            return {
                "id": new_record.id,
                "welder_id": new_record.welder_id,
                "training_code": new_record.training_code,
                "training_name": new_record.training_name,
                "training_type": new_record.training_type,
                "training_category": new_record.training_category,
                "start_date": new_record.start_date.isoformat() if new_record.start_date else None,
                "end_date": new_record.end_date.isoformat() if new_record.end_date else None,
                "duration_hours": new_record.duration_hours,
                "training_organization": new_record.training_organization,
                "trainer_name": new_record.trainer_name,
                "training_location": new_record.training_location,
                "training_content": new_record.training_content,
                "training_objectives": new_record.training_objectives,
                "training_materials": new_record.training_materials,
                "assessment_method": new_record.assessment_method,
                "assessment_score": new_record.assessment_score,
                "assessment_result": new_record.assessment_result,
                "pass_status": new_record.pass_status,
                "certificate_issued": new_record.certificate_issued,
                "certificate_number": new_record.certificate_number,
                "certificate_file_url": new_record.certificate_file_url,
                "notes": new_record.notes,
                "attachments": new_record.attachments,
                "created_by": new_record.created_by,
                "created_at": new_record.created_at.isoformat() if new_record.created_at else None,
                "updated_at": new_record.updated_at.isoformat() if new_record.updated_at else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"添加培训记录失败: {str(e)}"
            )

    def update_training_record(self, welder_id: int, record_id: int, record_data: dict, current_user: Any, workspace_context: WorkspaceContext) -> dict:
        from app.models.welder import WelderTraining
        try:
            return self._update_career_record(WelderTraining, "培训记录", welder_id, record_id, record_data, current_user, workspace_context)
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"更新培训记录失败: {e}")

    def delete_training_record(
        self,
        welder_id: int,
        record_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> None:
        """删除焊工培训记录"""
        try:
            from app.models.welder import WelderTraining

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 查询培训记录
            record = self.db.query(WelderTraining).filter(
                WelderTraining.id == record_id,
                WelderTraining.welder_id == welder_id
            ).first()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="培训记录不存在"
                )

            # 检查删除权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 删除记录需要编辑权限
                workspace_context
            )

            # 删除记录
            self.db.delete(record)
            self.db.commit()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除培训记录失败: {str(e)}"
            )

    # ==================== 考核记录管理 ====================

    def get_assessment_records(
        self,
        welder_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> tuple[list[dict], int]:
        """获取焊工考核记录列表"""
        try:
            from app.models.welder import WelderAssessment

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 构建查询
            query = self.db.query(WelderAssessment).filter(
                WelderAssessment.welder_id == welder_id
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=WelderAssessment,
                user=current_user,
                workspace_context=workspace_context
            )

            # 按考核日期倒序排列
            query = query.order_by(WelderAssessment.assessment_date.desc())

            # 获取记录
            records = query.all()
            total = query.count()

            # 转换为字典
            records_list = [
                {
                    "id": record.id,
                    "welder_id": record.welder_id,
                    "assessment_code": record.assessment_code,
                    "assessment_name": record.assessment_name,
                    "assessment_type": record.assessment_type,
                    "assessment_category": record.assessment_category,
                    "assessment_date": record.assessment_date.isoformat() if record.assessment_date else None,
                    "duration_minutes": record.duration_minutes,
                    "assessment_content": record.assessment_content,
                    "assessment_standards": record.assessment_standards,
                    "assessment_items": record.assessment_items,
                    "assessor_name": record.assessor_name,
                    "assessor_organization": record.assessor_organization,
                    "assessment_location": record.assessment_location,
                    "theory_score": record.theory_score,
                    "practical_score": record.practical_score,
                    "total_score": record.total_score,
                    "pass_score": record.pass_score,
                    "assessment_result": record.assessment_result,
                    "pass_status": record.pass_status,
                    "grade_level": record.grade_level,
                    "certificate_issued": record.certificate_issued,
                    "certificate_number": record.certificate_number,
                    "certificate_file_url": record.certificate_file_url,
                    "notes": record.notes,
                    "attachments": record.attachments,
                    "created_by": record.created_by,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "updated_by": record.updated_by,
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                }
                for record in records
            ]

            return records_list, total

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取考核记录失败: {str(e)}"
            )

    def add_assessment_record(
        self,
        welder_id: int,
        record_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> dict:
        """添加焊工考核记录"""
        try:
            from app.models.welder import WelderAssessment

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 检查创建权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 添加记录需要编辑权限
                workspace_context
            )

            # 创建考核记录
            new_record = WelderAssessment(
                welder_id=welder_id,
                workspace_type=workspace_context.workspace_type,
                user_id=workspace_context.user_id,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                created_by=current_user.id,
                **record_data
            )

            self.db.add(new_record)
            self.db.commit()
            self.db.refresh(new_record)

            # 转换为字典返回
            return {
                "id": new_record.id,
                "welder_id": new_record.welder_id,
                "assessment_code": new_record.assessment_code,
                "assessment_name": new_record.assessment_name,
                "assessment_type": new_record.assessment_type,
                "assessment_category": new_record.assessment_category,
                "assessment_date": new_record.assessment_date.isoformat() if new_record.assessment_date else None,
                "duration_minutes": new_record.duration_minutes,
                "assessment_content": new_record.assessment_content,
                "assessment_standards": new_record.assessment_standards,
                "assessment_items": new_record.assessment_items,
                "assessor_name": new_record.assessor_name,
                "assessor_organization": new_record.assessor_organization,
                "assessment_location": new_record.assessment_location,
                "theory_score": new_record.theory_score,
                "practical_score": new_record.practical_score,
                "total_score": new_record.total_score,
                "pass_score": new_record.pass_score,
                "assessment_result": new_record.assessment_result,
                "pass_status": new_record.pass_status,
                "grade_level": new_record.grade_level,
                "certificate_issued": new_record.certificate_issued,
                "certificate_number": new_record.certificate_number,
                "certificate_file_url": new_record.certificate_file_url,
                "notes": new_record.notes,
                "attachments": new_record.attachments,
                "created_by": new_record.created_by,
                "created_at": new_record.created_at.isoformat() if new_record.created_at else None,
                "updated_at": new_record.updated_at.isoformat() if new_record.updated_at else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"添加考核记录失败: {str(e)}"
            )

    def update_assessment_record(self, welder_id: int, record_id: int, record_data: dict, current_user: Any, workspace_context: WorkspaceContext) -> dict:
        from app.models.welder import WelderAssessment
        try:
            return self._update_career_record(WelderAssessment, "考核记录", welder_id, record_id, record_data, current_user, workspace_context)
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"更新考核记录失败: {e}")

    def delete_assessment_record(
        self,
        welder_id: int,
        record_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> None:
        """删除焊工考核记录"""
        try:
            from app.models.welder import WelderAssessment

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 查询考核记录
            record = self.db.query(WelderAssessment).filter(
                WelderAssessment.id == record_id,
                WelderAssessment.welder_id == welder_id
            ).first()

            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="考核记录不存在"
                )

            # 检查删除权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 删除记录需要编辑权限
                workspace_context
            )

            # 删除记录
            self.db.delete(record)
            self.db.commit()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除考核记录失败: {str(e)}"
            )

    # ==================== 工作履历管理 ====================

    def get_work_histories(
        self,
        welder_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> tuple[list[dict], int]:
        """获取焊工工作履历列表"""
        try:
            from app.models.welder import WelderWorkHistory

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 构建查询
            query = self.db.query(WelderWorkHistory).filter(
                WelderWorkHistory.welder_id == welder_id
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query=query,
                model=WelderWorkHistory,
                user=current_user,
                workspace_context=workspace_context
            )

            # 按开始日期倒序排列
            query = query.order_by(WelderWorkHistory.start_date.desc())

            # 获取记录
            records = query.all()
            total = query.count()

            # 转换为字典
            records_list = [
                {
                    "id": record.id,
                    "welder_id": record.welder_id,
                    "company_name": record.company_name,
                    "position": record.position,
                    "start_date": record.start_date.isoformat() if record.start_date else None,
                    "end_date": record.end_date.isoformat() if record.end_date else None,
                    "department": record.department,
                    "location": record.location,
                    "job_description": record.job_description,
                    "achievements": record.achievements,
                    "leaving_reason": record.leaving_reason,
                    "created_by": record.created_by,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                }
                for record in records
            ]

            return records_list, total

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取工作履历列表失败: {str(e)}"
            )

    def add_work_history(
        self,
        welder_id: int,
        history_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> dict:
        """添加焊工工作履历"""
        try:
            from app.models.welder import WelderWorkHistory

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 检查创建权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 添加记录需要编辑权限
                workspace_context
            )

            # 创建工作履历
            work_history = WelderWorkHistory(
                welder_id=welder_id,
                workspace_type=workspace_context.workspace_type,
                user_id=workspace_context.user_id,
                company_id=workspace_context.company_id,
                factory_id=workspace_context.factory_id,
                **history_data,
                created_by=current_user.id
            )

            self.db.add(work_history)
            self.db.commit()
            self.db.refresh(work_history)

            return {
                "id": work_history.id,
                "welder_id": work_history.welder_id,
                "company_name": work_history.company_name,
                "position": work_history.position,
                "start_date": work_history.start_date.isoformat() if work_history.start_date else None,
                "end_date": work_history.end_date.isoformat() if work_history.end_date else None,
                "department": work_history.department,
                "location": work_history.location,
                "job_description": work_history.job_description,
                "achievements": work_history.achievements,
                "leaving_reason": work_history.leaving_reason,
                "created_by": work_history.created_by,
                "created_at": work_history.created_at.isoformat() if work_history.created_at else None,
                "updated_at": work_history.updated_at.isoformat() if work_history.updated_at else None,
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"添加工作履历失败: {str(e)}"
            )

    def update_work_history(
        self,
        welder_id: int,
        history_id: int,
        history_data: dict,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> dict:
        """更新焊工工作履历"""
        try:
            from app.models.welder import WelderWorkHistory

            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)
            history = self.db.query(WelderWorkHistory).filter(
                WelderWorkHistory.id == history_id,
                WelderWorkHistory.welder_id == welder_id
            ).first()
            if not history:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工作履历不存在"
                )

            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",
                workspace_context
            )

            required = {'company_name', 'position', 'start_date'}
            if any(history_data[key] is None or history_data[key] == '' for key in required & history_data.keys()):
                raise HTTPException(422, '公司名称、职位和开始日期不能清空')
            start = history_data.get('start_date', history.start_date)
            end = history_data.get('end_date', history.end_date)
            if start and end and end < start:
                raise HTTPException(422, '结束日期不能早于开始日期')
            for key, value in history_data.items():
                if hasattr(history, key):
                    setattr(history, key, value)
            history.updated_at = datetime.utcnow()
            if hasattr(history, "updated_by"):
                history.updated_by = current_user.id
            self.db.commit()
            self.db.refresh(history)

            return {
                "id": history.id,
                "welder_id": history.welder_id,
                "company_name": history.company_name,
                "position": history.position,
                "start_date": history.start_date.isoformat() if history.start_date else None,
                "end_date": history.end_date.isoformat() if history.end_date else None,
                "department": history.department,
                "location": history.location,
                "job_description": history.job_description,
                "achievements": history.achievements,
                "leaving_reason": history.leaving_reason,
                    "created_by": history.created_by,
                    "created_at": history.created_at.isoformat() if history.created_at else None,
                    "updated_by": history.updated_by,
                    "updated_at": history.updated_at.isoformat() if history.updated_at else None,
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新工作履历失败: {str(e)}"
            )

    def delete_work_history(
        self,
        welder_id: int,
        history_id: int,
        current_user: Any,
        workspace_context: WorkspaceContext
    ) -> None:
        """删除焊工工作履历"""
        try:
            from app.models.welder import WelderWorkHistory

            # 验证焊工是否存在且有权限访问
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 查询工作履历
            history = self.db.query(WelderWorkHistory).filter(
                WelderWorkHistory.id == history_id,
                WelderWorkHistory.welder_id == welder_id
            ).first()

            if not history:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="工作履历不存在"
                )

            # 检查删除权限（基于焊工的权限）
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",  # 删除记录需要编辑权限
                workspace_context
            )

            # 删除记录
            self.db.delete(history)
            self.db.commit()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除工作履历失败: {str(e)}"
            )

