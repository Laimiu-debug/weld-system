"""
Production Service for the welding system backend.
生产管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from fastapi import status as http_status

from app.models.production import ProductionTask, ProductionRecord
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.schemas.production import ProductionTaskCreate, ProductionTaskUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService


class ProductionService:
    """生产管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
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

