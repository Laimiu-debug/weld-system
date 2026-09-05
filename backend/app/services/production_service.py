"""
Production Service for the welding system backend.
生产管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import HTTPException
from fastapi import status as http_status

from app.models.production import ProductionTask, ProductionRecord
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.models.wps import WPS
from app.models.welder import Welder
from app.models.equipment import Equipment
from app.schemas.production import ProductionTaskCreate, ProductionTaskUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService


class ProductionService:
    """生产管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    def _guard_plan_execution(self, task):
        plan_id = getattr(task, 'plan_id', None)
        if plan_id is None:
            return
        from app.models.production import ProductionPlan
        plan = self.db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
        if plan and plan.status in ('completed', 'cancelled'):
            raise HTTPException(409, '所属计划已结束，不能改变任务执行结果')

    # ==================== 生产任务基础管理 ====================
    
    def create_production_task(
        self,
        current_user: User,
        task_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> ProductionTask:
        """
        创建新生产任务
        
        Args:
            current_user: 当前用户
            task_data: 任务数据
            workspace_context: 工作区上下文
            
        Returns:
            ProductionTask: 创建的任务对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)
            
            # 检查配额（物理资产模块会自动跳过）
            self.quota_service.check_quota(current_user, workspace_context, "production", 1)
            
            # 检查任务编号是否重复
            task_number = task_data.get("task_number")
            if task_number:
                existing = self._check_task_number_exists(
                    task_number, workspace_context
                )
                if existing:
                    raise HTTPException(
                        status_code=http_status.HTTP_400_BAD_REQUEST,
                        detail=f"任务编号 {task_number} 已存在"
                    )

            valid_columns = {column.name for column in ProductionTask.__table__.columns}
            task_data = {key: value for key, value in task_data.items() if key in valid_columns}

            # 创建任务对象
            task = ProductionTask(**task_data)
            
            # 设置数据隔离字段
            task.workspace_type = workspace_context.workspace_type
            task.user_id = current_user.id
            task.company_id = workspace_context.company_id
            task.factory_id = workspace_context.factory_id
            task.created_by = current_user.id
            
            # 设置访问级别
            if workspace_context.workspace_type == "enterprise":
                task.access_level = "company"
            else:
                task.access_level = "private"
            
            # 保存到数据库
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "production", 1)
            
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建生产任务失败: {str(e)}"
            )
    
    def get_production_task_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_welder_id: Optional[int] = None
    ) -> tuple[List[ProductionTask], int]:
        """
        获取生产任务列表

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            skip: 跳过记录数
            limit: 返回记录数
            search: 搜索关键词
            status: 状态筛选
            priority: 优先级筛选
            assigned_welder_id: 分配焊工ID筛选

        Returns:
            tuple: (任务列表, 总数)
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            print(f"[生产任务列表] 用户ID: {current_user.id}")
            print(f"[生产任务列表] 工作区类型: {workspace_context.workspace_type}")
            print(f"[生产任务列表] 企业ID: {workspace_context.company_id}")
            print(f"[生产任务列表] 工厂ID: {workspace_context.factory_id}")

            # 检查查看权限并获取访问范围
            permission_result = self._check_list_permission(current_user, workspace_context)

            # 构建基础查询
            query = self.db.query(ProductionTask).filter(
                ProductionTask.is_active == True
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query,
                ProductionTask,
                current_user,
                workspace_context
            )

            print(f"[生产任务列表] 过滤后的SQL: {str(query)}")
            
            # 搜索过滤
            if search:
                search_filter = or_(
                    ProductionTask.task_number.ilike(f"%{search}%"),
                    ProductionTask.task_name.ilike(f"%{search}%"),
                    ProductionTask.description.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            # 状态筛选
            if status:
                query = query.filter(ProductionTask.status == status)
            
            # 优先级筛选
            if priority:
                query = query.filter(ProductionTask.priority == priority)
            
            # 分配焊工筛选
            if assigned_welder_id:
                query = query.filter(ProductionTask.assigned_welder_id == assigned_welder_id)
            
            # 获取总数
            total = query.count()
            
            # 分页和排序
            tasks = query.order_by(ProductionTask.created_at.desc()).offset(skip).limit(limit).all()
            
            return tasks, total
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取生产任务列表失败: {str(e)}"
            )
    
    def get_production_task_by_id(
        self,
        task_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> ProductionTask:
        """
        获取生产任务详情
        
        Args:
            task_id: 任务ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            ProductionTask: 任务对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询任务
            task = self.db.query(ProductionTask).filter(
                ProductionTask.id == task_id,
                ProductionTask.is_active == True
            ).first()
            
            if not task:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="生产任务不存在"
                )
            
            # 检查查看权限
            self.data_access.check_access(
                current_user,
                task,
                "VIEW",
                workspace_context
            )
            
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取生产任务详情失败: {str(e)}"
            )

    def enrich_task(self, task: ProductionTask) -> Dict[str, Any]:
        from app.schemas.production import ProductionTaskResponse

        payload = ProductionTaskResponse.model_validate(task).model_dump()
        if task.wps_id:
            wps = self.db.query(WPS).filter(WPS.id == task.wps_id).first()
            if wps:
                payload["wps_number"] = wps.wps_number
                payload["wps_title"] = wps.title
        if task.assigned_welder_id:
            welder = self.db.query(Welder).filter(Welder.id == task.assigned_welder_id).first()
            if welder:
                payload["welder_name"] = welder.full_name
                payload["welder_code"] = welder.welder_code
        if task.assigned_equipment_id:
            equipment = self.db.query(Equipment).filter(Equipment.id == task.assigned_equipment_id).first()
            if equipment:
                payload["equipment_name"] = equipment.equipment_name
                payload["equipment_code"] = equipment.equipment_code
        return payload
    
    def update_production_task(
        self,
        task_id: int,
        current_user: User,
        task_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> ProductionTask:
        """
        更新生产任务
        
        Args:
            task_id: 任务ID
            current_user: 当前用户
            task_data: 更新数据
            workspace_context: 工作区上下文
            
        Returns:
            ProductionTask: 更新后的任务对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询任务
            task = self.db.query(ProductionTask).filter(
                ProductionTask.id == task_id,
                ProductionTask.is_active == True
            ).first()
            
            if not task:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="生产任务不存在"
                )
            
            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                task,
                "EDIT",
                workspace_context
            )
            
            if 'plan_id' in task_data:
                raise HTTPException(422, '请通过计划关联任务操作修改归属')
            if {'status', 'progress_percentage', 'completed_quantity', 'actual_end_date'} & task_data.keys():
                self._guard_plan_execution(task)
            self.db.refresh(task, with_for_update=True)
            if task.production_release_id:
                editable = {"notes", "priority", "planned_start_date", "planned_end_date", "estimated_duration_hours"}
                blocked = [key for key, value in task_data.items()
                           if key not in editable and value is not None
                           and value != getattr(task, key, None)]
                if blocked:
                    raise HTTPException(409, "已放行焊序任务的工艺、资源和执行状态必须通过焊序派工、执行或变更流程修改")
            # 更新字段
            for key, value in task_data.items():
                if hasattr(task, key) and value is not None:
                    setattr(task, key, value)
            
            task.updated_by = current_user.id
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新生产任务失败: {str(e)}"
            )
    
    def delete_production_task(
        self,
        task_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除生产任务（软删除）
        
        Args:
            task_id: 任务ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询任务
            task = self.db.query(ProductionTask).filter(
                ProductionTask.id == task_id,
                ProductionTask.is_active == True
            ).first()
            
            if not task:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="生产任务不存在"
                )
            
            # 检查删除权限
            self.data_access.check_access(
                current_user,
                task,
                "DELETE",
                workspace_context
            )
            
            if getattr(task, 'plan_id', None) is not None:
                raise HTTPException(409, '请先在计划中解除任务关联再删除')
            self.db.refresh(task, with_for_update=True)
            if task.production_release_id:
                raise HTTPException(409, "已放行焊序任务不能直接删除，请通过焊序变更流程处理")
            # 软删除
            task.is_active = False
            task.updated_by = current_user.id
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "production", -1)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除生产任务失败: {str(e)}"
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
                if permissions.get("production", {}).get("create", False):
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
                if role.permissions and role.permissions.get("production", {}).get("view", False):
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
    
    def _check_task_number_exists(
        self,
        task_number: str,
        workspace_context: WorkspaceContext
    ) -> bool:
        """检查任务编号是否存在"""
        query = self.db.query(ProductionTask).filter(
            ProductionTask.task_number == task_number,
            ProductionTask.is_active == True
        )
        
        if workspace_context.workspace_type == "personal":
            query = query.filter(
                ProductionTask.workspace_type == "personal",
                ProductionTask.user_id == workspace_context.user_id
            )
        else:
            query = query.filter(
                ProductionTask.workspace_type == "enterprise",
                ProductionTask.company_id == workspace_context.company_id
            )
        
        return query.first() is not None

    # ==================== 进度 / 生产记录 / 统计 ====================

    def update_task_progress(
        self,
        task_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
        progress_percentage: float,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ProductionTask:
        """更新任务进度，并按进度自动推导状态。"""
        task = self.get_production_task_by_id(task_id, current_user, workspace_context)
        self.data_access.check_access(
            current_user, task, "EDIT", workspace_context
        )

        self.db.refresh(task, with_for_update=True)
        if task.production_release_id:
            raise HTTPException(409, "已放行焊序任务必须通过执行记录更新进度")
        self._guard_plan_execution(task)
        progress = max(0.0, min(100.0, float(progress_percentage)))
        task.progress_percentage = progress

        if status:
            task.status = status
        elif progress >= 100:
            task.status = "completed"
            task.actual_end_date = task.actual_end_date or date.today()
        elif progress > 0 and task.status in (None, "pending"):
            task.status = "in_progress"
            task.actual_start_date = task.actual_start_date or date.today()

        if notes:
            task.notes = notes

        task.updated_by = current_user.id
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task

    def create_production_record(
        self,
        task_id: int,
        current_user: User,
        record_data: Dict[str, Any],
        workspace_context: WorkspaceContext,
    ) -> ProductionRecord:
        """为任务追加一条生产记录，并回写完成量/工时。"""
        task = self.get_production_task_by_id(task_id, current_user, workspace_context)
        self.data_access.check_access(
            current_user, task, "EDIT", workspace_context
        )

        self.db.refresh(task, with_for_update=True)
        if task.production_release_id:
            raise HTTPException(409, "已放行焊序任务必须通过焊序执行入口登记，不能使用普通生产记录")
        payload = record_data.copy()
        progress_percentage = payload.pop("progress_percentage", None)
        payload.pop("task_id", None)

        record_date = payload.get("record_date") or date.today()
        start_time = payload.get("start_time") or datetime.utcnow()
        payload["record_date"] = record_date
        payload["start_time"] = start_time
        if not payload.get("record_number"):
            payload["record_number"] = f"PR-{task.task_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        allowed = {column.name for column in ProductionRecord.__table__.columns}
        filtered = {key: value for key, value in payload.items() if key in allowed}

        record = ProductionRecord(
            **filtered,
            task_id=task.id,
            user_id=current_user.id,
            company_id=task.company_id,
            factory_id=task.factory_id,
            created_by=current_user.id,
        )
        if not record.welder_id:
            record.welder_id = task.assigned_welder_id
        if not record.equipment_id:
            record.equipment_id = task.assigned_equipment_id
        if not record.wps_id:
            record.wps_id = task.wps_id

        self.db.add(record)

        if record.quantity_completed:
            task.completed_quantity = (task.completed_quantity or 0) + record.quantity_completed
        if record.weld_length:
            task.weld_length_actual = (task.weld_length_actual or 0) + record.weld_length
        if record.duration_hours:
            task.actual_duration_hours = (task.actual_duration_hours or 0) + record.duration_hours
        if progress_percentage is not None:
            task.progress_percentage = max(0.0, min(100.0, float(progress_percentage)))
            if task.progress_percentage >= 100:
                task.status = "completed"
            elif task.status == "pending":
                task.status = "in_progress"
        elif task.status == "pending":
            task.status = "in_progress"
            task.actual_start_date = task.actual_start_date or date.today()

        task.updated_by = current_user.id
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_production_records(
        self,
        task_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[ProductionRecord], int]:
        """获取任务下的生产记录。"""
        task = self.get_production_task_by_id(task_id, current_user, workspace_context)
        query = self.db.query(ProductionRecord).filter(ProductionRecord.task_id == task.id)
        total = query.count()
        records = (
            query.order_by(ProductionRecord.record_date.desc(), ProductionRecord.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return records, total

    def _scoped_task_query(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
    ):
        workspace_context.validate()
        self._check_list_permission(current_user, workspace_context)
        query = self.db.query(ProductionTask).filter(ProductionTask.is_active == True)
        return self.data_access.apply_workspace_filter(
            query, ProductionTask, current_user, workspace_context
        )

    def get_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        """生产任务概览统计。"""
        query = self._scoped_task_query(current_user, workspace_context)
        today = date.today()

        total = query.count()
        pending = query.filter(ProductionTask.status == "pending").count()
        in_progress = query.filter(ProductionTask.status == "in_progress").count()
        completed = query.filter(ProductionTask.status == "completed").count()
        paused = query.filter(ProductionTask.status == "paused").count()
        cancelled = query.filter(ProductionTask.status == "cancelled").count()
        overdue = query.filter(
            ProductionTask.status.in_(["pending", "in_progress", "paused"]),
            ProductionTask.planned_end_date.isnot(None),
            ProductionTask.planned_end_date < today,
        ).count()

        totals = query.with_entities(
            func.coalesce(func.sum(ProductionTask.weld_length_actual), 0),
            func.coalesce(func.sum(ProductionTask.actual_duration_hours), 0),
            func.coalesce(func.avg(ProductionTask.progress_percentage), 0),
        ).one()

        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "completed_tasks": completed,
            "paused_tasks": paused,
            "cancelled_tasks": cancelled,
            "overdue_tasks": overdue,
            "total_weld_length": float(totals[0] or 0),
            "total_work_hours": float(totals[1] or 0),
            "average_progress": round(float(totals[2] or 0), 2),
        }

    def get_efficiency_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """按日汇总完成量与工时。"""
        query = self._scoped_task_query(current_user, workspace_context)
        start = start_date or (date.today() - timedelta(days=29))
        end = end_date or date.today()
        query = query.filter(
            ProductionTask.created_at >= datetime.combine(start, datetime.min.time()),
            ProductionTask.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time()),
        )
        return self._efficiency_by_day(query, start, end)

    def _efficiency_by_day(self, query, start: date, end: date) -> Dict[str, Any]:
        rows = (
            query.with_entities(
                func.date(ProductionTask.created_at).label("day"),
                func.count(ProductionTask.id),
                func.sum(case((ProductionTask.status == "completed", 1), else_=0)),
                func.coalesce(func.sum(ProductionTask.actual_duration_hours), 0),
                func.coalesce(func.sum(ProductionTask.weld_length_actual), 0),
            )
            .group_by(func.date(ProductionTask.created_at))
            .order_by(func.date(ProductionTask.created_at))
            .all()
        )

        series = []
        for day, total, completed, hours, length in rows:
            total_count = int(total or 0)
            completed_count = int(completed or 0)
            series.append({
                "date": str(day),
                "total_tasks": total_count,
                "completed_tasks": completed_count,
                "completion_rate": round((completed_count / total_count) * 100, 2) if total_count else 0,
                "work_hours": float(hours or 0),
                "weld_length": float(length or 0),
            })

        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "series": series,
        }

