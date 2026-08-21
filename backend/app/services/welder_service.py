"""
Welder Service for the welding system backend.
焊工管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import HTTPException, status
import logging

from app.models.welder import Welder, WelderCertification, WelderCertifiedProject
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.schemas.welder import WelderCreate, WelderUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService
from app.services.welder_career_mixin import WelderCareerMixin
import json

logger = logging.getLogger(__name__)


def _project_to_dict(project: WelderCertifiedProject) -> Dict[str, Any]:
    return {
        "id": project.id,
        "certification_id": project.certification_id,
        "welder_id": project.welder_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "issue_date": project.issue_date.isoformat() if project.issue_date else None,
        "expiry_date": project.expiry_date.isoformat() if project.expiry_date else None,
        "renewal_date": project.renewal_date.isoformat() if project.renewal_date else None,
        "renewal_count": project.renewal_count or 0,
        "next_renewal_date": project.next_renewal_date.isoformat() if project.next_renewal_date else None,
        "renewal_result": project.renewal_result,
        "renewal_notes": project.renewal_notes,
        "status": project.status,
        "is_active": project.is_active,
        "notes": project.notes,
        "created_by": project.created_by,
        "updated_by": project.updated_by,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _compute_project_status(expiry: Optional[date]) -> str:
    if not expiry:
        return "valid"
    today = date.today()
    if expiry < today:
        return "expired"
    if expiry <= today + timedelta(days=30):
        return "expiring_soon"
    return "valid"


class WelderService(WelderCareerMixin):
    """焊工管理服务类（基础 CRUD / 证书 / 持证项目 + 履历 Mixin）"""

    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)
        self.quota_service = QuotaService(db)
    
    # ==================== 焊工基础管理 ====================
    
    def create_welder(
        self,
        current_user: User,
        welder_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> Welder:
        """
        创建新焊工
        
        Args:
            current_user: 当前用户
            welder_data: 焊工数据
            workspace_context: 工作区上下文
            
        Returns:
            Welder: 创建的焊工对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 企业工作区：检查创建权限
            if workspace_context.workspace_type == "enterprise":
                self._check_create_permission(current_user, workspace_context)
            
            # 检查配额（物理资产模块会自动跳过）
            self.quota_service.check_quota(current_user, workspace_context, "welders", 1)
            
            # 检查焊工编号是否重复
            welder_code = welder_data.get("welder_code")
            if welder_code:
                existing = self._check_welder_code_exists(
                    welder_code, workspace_context
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"焊工编号 {welder_code} 已存在"
                    )
            
            # 创建焊工对象
            welder = Welder(**welder_data)
            
            # 设置数据隔离字段
            welder.workspace_type = workspace_context.workspace_type
            welder.user_id = current_user.id
            welder.company_id = workspace_context.company_id
            welder.factory_id = workspace_context.factory_id
            welder.created_by = current_user.id
            
            # 设置访问级别
            if workspace_context.workspace_type == "enterprise":
                welder.access_level = "company"
            else:
                welder.access_level = "private"
            
            # 保存到数据库
            self.db.add(welder)
            self.db.commit()
            self.db.refresh(welder)
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "welders", 1)
            
            return welder
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建焊工失败: {str(e)}"
            )
    
    def get_welder_list(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        skill_level: Optional[str] = None,
        welder_status: Optional[str] = None,
        certification_status: Optional[str] = None
    ) -> tuple[List[Welder], int]:
        """
        获取焊工列表

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文
            skip: 跳过记录数
            limit: 返回记录数
            search: 搜索关键词
            skill_level: 技能等级筛选
            welder_status: 状态筛选
            certification_status: 证书状态筛选

        Returns:
            tuple: (焊工列表, 总数)
        """
        try:
            logger.info(f"[服务层] 开始获取焊工列表 - user_id={current_user.id}, workspace={workspace_context}")

            # 验证工作区上下文
            logger.info(f"[服务层] 验证工作区上下文...")
            workspace_context.validate()
            logger.info(f"[服务层] 工作区上下文验证成功")

            # 检查查看权限并获取访问范围
            logger.info(f"[服务层] 检查查看权限...")
            permission_result = self._check_list_permission(current_user, workspace_context)
            logger.info(f"[服务层] 权限检查成功 - data_access_scope={permission_result['data_access_scope']}, factory_id={permission_result.get('factory_id')}")

            # 构建基础查询
            logger.info(f"[服务层] 构建基础查询...")
            query = self.db.query(Welder).filter(
                Welder.is_active == True
            )

            # 应用数据隔离过滤
            logger.info(f"[服务层] 应用数据隔离过滤...")
            query = self.data_access.apply_workspace_filter(
                query,
                Welder,
                current_user,
                workspace_context
            )
            logger.info(f"[服务层] 数据隔离过滤应用成功")

            # 搜索过滤
            if search:
                logger.info(f"[服务层] 应用搜索过滤: {search}")
                search_filter = or_(
                    Welder.welder_code.ilike(f"%{search}%"),
                    Welder.full_name.ilike(f"%{search}%"),
                    Welder.english_name.ilike(f"%{search}%"),
                    Welder.phone.ilike(f"%{search}%"),
                    Welder.primary_certification_number.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)

            # 技能等级筛选
            if skill_level:
                logger.info(f"[服务层] 应用技能等级筛选: {skill_level}")
                query = query.filter(Welder.skill_level == skill_level)

            # 状态筛选
            if welder_status:
                logger.info(f"[服务层] 应用状态筛选: {welder_status}")
                query = query.filter(Welder.status == welder_status)

            # 证书状态筛选（优先按持证项目子表风险，兼容证书级 expiry）
            if certification_status:
                logger.info(f"[服务层] 应用证书状态筛选: {certification_status}")
                today = date.today()
                soon = today + timedelta(days=30)

                project_q = self.db.query(WelderCertifiedProject.welder_id).filter(
                    WelderCertifiedProject.is_active == True,  # noqa: E712
                )
                legacy_q = self.db.query(WelderCertification.welder_id).filter(
                    WelderCertification.is_active == True,  # noqa: E712
                )
                # 无项目记录的旧证书才走 legacy expiry
                has_project = self.db.query(WelderCertifiedProject.certification_id).filter(
                    WelderCertifiedProject.is_active == True,  # noqa: E712
                )

                if certification_status == "expiring_soon":
                    project_q = project_q.filter(
                        WelderCertifiedProject.expiry_date.isnot(None),
                        WelderCertifiedProject.expiry_date >= today,
                        WelderCertifiedProject.expiry_date <= soon,
                    )
                    legacy_q = legacy_q.filter(
                        ~WelderCertification.id.in_(has_project),
                        WelderCertification.expiry_date.isnot(None),
                        WelderCertification.expiry_date >= today,
                        WelderCertification.expiry_date <= soon,
                    )
                    query = query.filter(
                        or_(
                            Welder.id.in_(project_q.distinct()),
                            Welder.id.in_(legacy_q.distinct()),
                        )
                    )
                    certification_status = None
                elif certification_status == "expired":
                    project_q = project_q.filter(
                        WelderCertifiedProject.expiry_date.isnot(None),
                        WelderCertifiedProject.expiry_date < today,
                    )
                    legacy_q = legacy_q.filter(
                        ~WelderCertification.id.in_(has_project),
                        WelderCertification.expiry_date.isnot(None),
                        WelderCertification.expiry_date < today,
                    )
                    query = query.filter(
                        or_(
                            Welder.id.in_(project_q.distinct()),
                            Welder.id.in_(legacy_q.distinct()),
                        )
                    )
                    certification_status = None
                elif certification_status == "valid":
                    risky_ids = (
                        self.db.query(WelderCertifiedProject.welder_id)
                        .filter(
                            WelderCertifiedProject.is_active == True,  # noqa: E712
                            WelderCertifiedProject.expiry_date.isnot(None),
                            WelderCertifiedProject.expiry_date <= soon,
                        )
                        .distinct()
                    )
                    legacy_risky = (
                        self.db.query(WelderCertification.welder_id)
                        .filter(
                            WelderCertification.is_active == True,  # noqa: E712
                            ~WelderCertification.id.in_(has_project),
                            WelderCertification.expiry_date.isnot(None),
                            WelderCertification.expiry_date <= soon,
                        )
                        .distinct()
                    )
                    has_any = (
                        self.db.query(WelderCertification.welder_id)
                        .filter(WelderCertification.is_active == True)  # noqa: E712
                        .distinct()
                    )
                    query = query.filter(
                        Welder.id.in_(has_any),
                        ~Welder.id.in_(risky_ids),
                        ~Welder.id.in_(legacy_risky),
                    )
                    certification_status = None
                elif certification_status == "none":
                    has_cert = self.db.query(WelderCertification.welder_id).filter(
                        WelderCertification.is_active == True,  # noqa: E712
                    )
                    query = query.filter(~Welder.id.in_(has_cert.distinct()))
                    certification_status = None

                if certification_status:
                    query = query.filter(Welder.certification_status == certification_status)

            # 获取总数
            logger.info(f"[服务层] 获取总数...")
            total = query.count()
            logger.info(f"[服务层] 总数: {total}")

            # 分页和排序
            logger.info(f"[服务层] 执行分页查询 - skip={skip}, limit={limit}")
            welders = query.order_by(Welder.created_at.desc()).offset(skip).limit(limit).all()
            logger.info(f"[服务层] 查询成功 - 返回 {len(welders)} 条记录")

            return welders, total

        except HTTPException as he:
            logger.error(f"[服务层] HTTPException: {he.detail}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"[服务层] 未知错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取焊工列表失败: {str(e)}"
            )
    
    def get_welder_by_id(
        self,
        welder_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Welder:
        """
        获取焊工详情
        
        Args:
            welder_id: 焊工ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            Welder: 焊工对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊工
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()
            
            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )
            
            # 检查查看权限
            self.data_access.check_access(
                current_user,
                welder,
                "VIEW",
                workspace_context
            )
            
            return welder
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取焊工详情失败: {str(e)}"
            )
    
    def update_welder(
        self,
        welder_id: int,
        current_user: User,
        welder_data: Dict[str, Any],
        workspace_context: WorkspaceContext
    ) -> Welder:
        """
        更新焊工
        
        Args:
            welder_id: 焊工ID
            current_user: 当前用户
            welder_data: 更新数据
            workspace_context: 工作区上下文
            
        Returns:
            Welder: 更新后的焊工对象
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊工
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()
            
            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )
            
            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",
                workspace_context
            )
            
            # 更新字段
            for key, value in welder_data.items():
                if hasattr(welder, key) and value is not None:
                    setattr(welder, key, value)
            
            welder.updated_by = current_user.id
            welder.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(welder)
            
            return welder
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新焊工失败: {str(e)}"
            )
    
    def delete_welder(
        self,
        welder_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除焊工（软删除）
        
        Args:
            welder_id: 焊工ID
            current_user: 当前用户
            workspace_context: 工作区上下文
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()
            
            # 查询焊工
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()
            
            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )
            
            # 检查删除权限
            self.data_access.check_access(
                current_user,
                welder,
                "DELETE",
                workspace_context
            )
            
            # 软删除
            welder.is_active = False
            welder.updated_by = current_user.id
            welder.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新配额使用（物理资产模块会自动跳过）
            self.quota_service.update_quota_usage(current_user, workspace_context, "welders", -1)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除焊工失败: {str(e)}"
            )
    
    # ==================== 权限检查辅助方法 ====================
    
    def _check_create_permission(self, current_user: User, workspace_context: WorkspaceContext):
        """检查创建权限"""
        company = self.db.query(Company).filter(
            Company.id == workspace_context.company_id
        ).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
                status_code=status.HTTP_403_FORBIDDEN,
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
                if permissions.get("welders", {}).get("create", False):
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
                status_code=status.HTTP_403_FORBIDDEN,
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
                if role.permissions and role.permissions.get("welders", {}).get("view", False):
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
    
    def _check_welder_code_exists(
        self,
        welder_code: str,
        workspace_context: WorkspaceContext
    ) -> bool:
        """检查焊工编号是否存在"""
        query = self.db.query(Welder).filter(
            Welder.welder_code == welder_code,
            Welder.is_active == True
        )
        
        if workspace_context.workspace_type == "personal":
            query = query.filter(
                Welder.workspace_type == "personal",
                Welder.user_id == workspace_context.user_id
            )
        else:
            query = query.filter(
                Welder.workspace_type == "enterprise",
                Welder.company_id == workspace_context.company_id
            )
        
        return query.first() is not None

    # ==================== 证书管理 ====================

    def get_certifications(
        self,
        welder_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        获取焊工证书列表

        Args:
            welder_id: 焊工ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            tuple: (证书列表, 总数)
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊工并检查权限
            welder = self.get_welder_by_id(welder_id, current_user, workspace_context)

            # 查询证书列表
            certifications = self.db.query(WelderCertification).filter(
                WelderCertification.welder_id == welder_id,
                WelderCertification.is_active == True
            ).order_by(WelderCertification.issue_date.desc()).all()

            # 转换为字典列表
            cert_list = []
            for cert in certifications:
                cert_dict = {
                    "id": cert.id,
                    "welder_id": cert.welder_id,
                    "certification_number": cert.certification_number,
                    "certification_type": cert.certification_type,
                    "certification_level": cert.certification_level,
                    "certification_standard": cert.certification_standard,
                    "certification_system": cert.certification_system,
                    "project_name": cert.project_name,

                    # 颁发信息
                    "issuing_authority": cert.issuing_authority,
                    "issuing_country": cert.issuing_country,
                    "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                    "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,

                    # 合格项目和范围（JSON格式）
                    "qualified_items": cert.qualified_items,
                    "qualified_range": cert.qualified_range,

                    # 考试信息
                    "exam_date": cert.exam_date.isoformat() if cert.exam_date else None,
                    "exam_location": cert.exam_location,
                    "exam_score": cert.exam_score,
                    "practical_test_result": cert.practical_test_result,
                    "theory_test_result": cert.theory_test_result,

                    # 复审信息
                    "renewal_date": cert.renewal_date.isoformat() if cert.renewal_date else None,
                    "renewal_count": cert.renewal_count,
                    "next_renewal_date": cert.next_renewal_date.isoformat() if cert.next_renewal_date else None,
                    "renewal_result": cert.renewal_result,
                    "renewal_notes": cert.renewal_notes,

                    # 状态和附件
                    "status": cert.status,
                    "is_primary": cert.is_primary,
                    "certificate_file_url": cert.certificate_file_url,
                    "attachments": cert.attachments,
                    "notes": cert.notes,

                    "created_at": cert.created_at.isoformat() if cert.created_at else None,
                    "updated_at": cert.updated_at.isoformat() if cert.updated_at else None,
                    "projects": self._ensure_and_list_projects(cert, current_user),
                }
                cert_list.append(cert_dict)

            return cert_list, len(cert_list)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取证书列表失败: {str(e)}"
            )

    def add_certification(
        self,
        welder_id: int,
        certification_data: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        添加焊工证书

        Args:
            welder_id: 焊工ID
            certification_data: 证书数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Dict: 创建的证书信息
        """
        try:
            # 添加详细日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"=== 开始添加证书 ===")
            logger.info(f"焊工ID: {welder_id}")
            logger.info(f"证书数据类型: {type(certification_data)}")
            logger.info(f"证书数据: {certification_data}")

            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊工并检查编辑权限
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()

            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )

            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",
                workspace_context
            )

            # 创建证书对象
            from datetime import datetime as dt, date
            logger.info("开始创建证书对象...")

            # 处理日期字段，确保正确的类型转换
            def parse_date(date_str):
                if not date_str:
                    return None
                if isinstance(date_str, (date, dt)):
                    return date_str
                try:
                    # 尝试解析 ISO 格式日期
                    return dt.fromisoformat(date_str.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError):
                    try:
                        # 尝试解析其他格式
                        return dt.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        logger.warning(f"无法解析日期格式: {date_str}")
                        return None

            certification = WelderCertification(
                welder_id=welder_id,
                user_id=current_user.id,
                company_id=workspace_context.company_id,

                # 证书基本信息
                certification_number=certification_data.get("certification_number"),
                certification_type=certification_data.get("certification_type"),
                certification_level=certification_data.get("certification_level"),
                certification_standard=certification_data.get("certification_standard"),
                certification_system=certification_data.get("certification_system"),
                project_name=certification_data.get("project_name"),

                # 颁发信息
                issuing_authority=certification_data.get("issuing_authority"),
                issuing_country=certification_data.get("issuing_country"),
                issue_date=parse_date(certification_data.get("issue_date")),
                expiry_date=parse_date(certification_data.get("expiry_date")),

                # 合格项目和范围（JSON格式）
                qualified_items=certification_data.get("qualified_items"),
                qualified_range=certification_data.get("qualified_range"),

                # 考试信息
                exam_date=parse_date(certification_data.get("exam_date")),
                exam_location=certification_data.get("exam_location"),
                exam_score=certification_data.get("exam_score"),
                practical_test_result=certification_data.get("practical_test_result"),
                theory_test_result=certification_data.get("theory_test_result"),

                # 复审信息
                renewal_date=parse_date(certification_data.get("renewal_date")),
                renewal_count=certification_data.get("renewal_count", 0),
                next_renewal_date=parse_date(certification_data.get("next_renewal_date")),
                renewal_result=certification_data.get("renewal_result"),
                renewal_notes=certification_data.get("renewal_notes"),

                # 状态和附件
                status=certification_data.get("status", "valid"),
                is_primary=certification_data.get("is_primary", False),
                certificate_file_url=certification_data.get("certificate_file_url"),
                attachments=certification_data.get("attachments"),
                notes=certification_data.get("notes"),

                created_by=current_user.id
            )

            logger.info("证书对象创建成功，准备保存到数据库...")
            self.db.add(certification)
            logger.info("开始提交事务...")
            self.db.commit()
            logger.info("事务提交成功，刷新对象...")
            self.db.refresh(certification)
            logger.info(f"证书添加成功，ID: {certification.id}")

            # 如果是第一个证书，更新焊工的主证书信息
            if not welder.primary_certification_number:
                welder.primary_certification_number = certification.certification_number
                welder.primary_certification_level = certification.certification_level
                welder.certification_status = certification.status
                welder.updated_by = current_user.id
                welder.updated_at = datetime.utcnow()
                self.db.commit()

            # Phase2：同步创建首个持证项目（若有项目名或到期日）
            projects = []
            if certification_data.get("project_name") or certification_data.get("expiry_date"):
                project = self._create_project_row(
                    certification=certification,
                    data={
                        "project_name": certification_data.get("project_name")
                        or certification.certification_type
                        or "持证项目",
                        "project_code": certification_data.get("project_code"),
                        "issue_date": certification_data.get("issue_date"),
                        "expiry_date": certification_data.get("expiry_date"),
                        "renewal_date": certification_data.get("renewal_date"),
                        "renewal_count": certification_data.get("renewal_count", 0),
                        "next_renewal_date": certification_data.get("next_renewal_date"),
                        "renewal_result": certification_data.get("renewal_result"),
                        "renewal_notes": certification_data.get("renewal_notes"),
                        "status": certification_data.get("status", "valid"),
                        "notes": certification_data.get("notes"),
                    },
                    current_user=current_user,
                )
                projects = [_project_to_dict(project)]

            # 返回完整的证书信息
            return {
                "id": certification.id,
                "welder_id": certification.welder_id,
                "user_id": certification.user_id,
                "company_id": certification.company_id,

                # 证书基本信息
                "certification_number": certification.certification_number,
                "certification_type": certification.certification_type,
                "certification_level": certification.certification_level,
                "certification_standard": certification.certification_standard,
                "certification_system": certification.certification_system,
                "project_name": certification.project_name,

                # 颁发信息
                "issuing_authority": certification.issuing_authority,
                "issuing_country": certification.issuing_country,
                "issue_date": certification.issue_date.isoformat() if certification.issue_date else None,
                "expiry_date": certification.expiry_date.isoformat() if certification.expiry_date else None,

                # 合格项目和范围（JSON格式）
                "qualified_items": certification.qualified_items,
                "qualified_range": certification.qualified_range,

                # 考试信息
                "exam_date": certification.exam_date.isoformat() if certification.exam_date else None,
                "exam_location": certification.exam_location,
                "exam_score": certification.exam_score,
                "practical_test_result": certification.practical_test_result,
                "theory_test_result": certification.theory_test_result,

                # 复审信息
                "renewal_date": certification.renewal_date.isoformat() if certification.renewal_date else None,
                "renewal_count": certification.renewal_count,
                "next_renewal_date": certification.next_renewal_date.isoformat() if certification.next_renewal_date else None,
                "renewal_result": certification.renewal_result,
                "renewal_notes": certification.renewal_notes,

                # 状态和附件
                "status": certification.status,
                "is_primary": certification.is_primary,
                "certificate_file_url": certification.certificate_file_url,
                "attachments": certification.attachments,
                "notes": certification.notes,

                # 审计字段
                "created_by": certification.created_by,
                "updated_by": certification.updated_by,
                "created_at": certification.created_at.isoformat() if certification.created_at else None,
                "updated_at": certification.updated_at.isoformat() if certification.updated_at else None,
                "is_active": certification.is_active,
                "projects": projects,
            }

        except HTTPException:
            raise
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"=== 添加证书失败 ===")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"添加证书失败: {str(e)}"
            )

    def update_certification(
        self,
        welder_id: int,
        certification_id: int,
        certification_data: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        更新焊工证书

        Args:
            welder_id: 焊工ID
            certification_id: 证书ID
            certification_data: 证书数据
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Dict: 更新后的证书信息
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊工并检查编辑权限
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()

            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )

            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",
                workspace_context
            )

            # 查询证书
            certification = self.db.query(WelderCertification).filter(
                WelderCertification.id == certification_id,
                WelderCertification.welder_id == welder_id,
                WelderCertification.is_active == True
            ).first()

            if not certification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="证书不存在"
                )

            # 更新证书字段
            from datetime import datetime as dt, date

            # 处理日期字段，确保正确的类型转换
            def parse_date(date_str):
                if not date_str:
                    return None
                if isinstance(date_str, (date, dt)):
                    return date_str
                try:
                    # 尝试解析 ISO 格式日期
                    return dt.fromisoformat(date_str.replace('Z', '+00:00')).date()
                except (ValueError, AttributeError):
                    try:
                        # 尝试解析其他格式
                        return dt.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return None

            if "certification_number" in certification_data:
                certification.certification_number = certification_data["certification_number"]
            if "certification_type" in certification_data:
                certification.certification_type = certification_data["certification_type"]
            if "certification_level" in certification_data:
                certification.certification_level = certification_data["certification_level"]
            if "certification_standard" in certification_data:
                certification.certification_standard = certification_data["certification_standard"]
            if "certification_system" in certification_data:
                certification.certification_system = certification_data["certification_system"]
            if "project_name" in certification_data:
                certification.project_name = certification_data["project_name"]

            if "issuing_authority" in certification_data:
                certification.issuing_authority = certification_data["issuing_authority"]
            if "issuing_country" in certification_data:
                certification.issuing_country = certification_data["issuing_country"]
            if "issue_date" in certification_data:
                certification.issue_date = parse_date(certification_data["issue_date"])
            if "expiry_date" in certification_data:
                certification.expiry_date = parse_date(certification_data["expiry_date"])

            # 更新合格项目和范围（JSON格式）
            if "qualified_items" in certification_data:
                certification.qualified_items = certification_data["qualified_items"]
            if "qualified_range" in certification_data:
                certification.qualified_range = certification_data["qualified_range"]

            if "exam_date" in certification_data:
                certification.exam_date = parse_date(certification_data["exam_date"])
            if "exam_location" in certification_data:
                certification.exam_location = certification_data["exam_location"]
            if "exam_score" in certification_data:
                certification.exam_score = certification_data["exam_score"]
            if "practical_test_result" in certification_data:
                certification.practical_test_result = certification_data["practical_test_result"]
            if "theory_test_result" in certification_data:
                certification.theory_test_result = certification_data["theory_test_result"]

            if "renewal_date" in certification_data:
                certification.renewal_date = parse_date(certification_data["renewal_date"])
            if "renewal_count" in certification_data:
                certification.renewal_count = certification_data["renewal_count"]
            if "next_renewal_date" in certification_data:
                certification.next_renewal_date = parse_date(certification_data["next_renewal_date"])
            if "renewal_result" in certification_data:
                certification.renewal_result = certification_data["renewal_result"]
            if "renewal_notes" in certification_data:
                certification.renewal_notes = certification_data["renewal_notes"]

            if "status" in certification_data:
                certification.status = certification_data["status"]
            if "is_primary" in certification_data:
                certification.is_primary = certification_data["is_primary"]
                if certification_data["is_primary"]:
                    # 取消同焊工其他证的主要标记，并回写列表摘要字段
                    self.db.query(WelderCertification).filter(
                        WelderCertification.welder_id == welder_id,
                        WelderCertification.id != certification_id,
                        WelderCertification.is_active == True,  # noqa: E712
                    ).update({"is_primary": False}, synchronize_session=False)
                    welder.primary_certification_number = certification.certification_number
                    welder.primary_certification_level = certification.certification_level
                    welder.primary_certification_date = certification.issue_date
                    welder.primary_expiry_date = certification.expiry_date
                    welder.primary_issuing_authority = certification.issuing_authority
                    if certification.expiry_date:
                        days_left = (certification.expiry_date - date.today()).days
                        if days_left < 0:
                            welder.certification_status = "expired"
                        elif days_left <= 30:
                            welder.certification_status = "expiring_soon"
                        else:
                            welder.certification_status = "valid"
            if "certificate_file_url" in certification_data:
                certification.certificate_file_url = certification_data["certificate_file_url"]
            if "attachments" in certification_data:
                certification.attachments = certification_data["attachments"]
            if "notes" in certification_data:
                certification.notes = certification_data["notes"]

            certification.updated_by = current_user.id
            certification.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(certification)

            # 返回更新后的证书信息
            return {
                "id": certification.id,
                "welder_id": certification.welder_id,
                "certification_number": certification.certification_number,
                "certification_type": certification.certification_type,
                "certification_level": certification.certification_level,
                "certification_system": certification.certification_system,
                "status": certification.status,
                "updated_at": certification.updated_at.isoformat() if certification.updated_at else None
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新证书失败: {str(e)}"
            )

    def delete_certification(
        self,
        welder_id: int,
        certification_id: int,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        删除焊工证书（软删除）

        Args:
            welder_id: 焊工ID
            certification_id: 证书ID
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            bool: 是否删除成功
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 查询焊工并检查编辑权限
            welder = self.db.query(Welder).filter(
                Welder.id == welder_id,
                Welder.is_active == True
            ).first()

            if not welder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="焊工不存在"
                )

            # 检查编辑权限
            self.data_access.check_access(
                current_user,
                welder,
                "EDIT",
                workspace_context
            )

            # 查询证书
            certification = self.db.query(WelderCertification).filter(
                WelderCertification.id == certification_id,
                WelderCertification.welder_id == welder_id,
                WelderCertification.is_active == True
            ).first()

            if not certification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="证书不存在"
                )

            # 软删除
            certification.is_active = False
            certification.updated_by = current_user.id
            certification.updated_at = datetime.utcnow()
            self.db.query(WelderCertifiedProject).filter(
                WelderCertifiedProject.certification_id == certification_id,
                WelderCertifiedProject.is_active == True,  # noqa: E712
            ).update(
                {
                    "is_active": False,
                    "updated_by": current_user.id,
                    "updated_at": datetime.utcnow(),
                },
                synchronize_session=False,
            )

            self.db.commit()

            return True

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除证书失败: {str(e)}"
            )

    # ==================== 持证项目（Phase 2） ====================

    def _parse_date_value(self, date_str: Any) -> Optional[date]:
        if not date_str:
            return None
        if isinstance(date_str, date) and not isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, datetime):
            return date_str.date()
        try:
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            try:
                return datetime.strptime(str(date_str), "%Y-%m-%d").date()
            except ValueError:
                return None

    def _create_project_row(
        self,
        certification: WelderCertification,
        data: Dict[str, Any],
        current_user: User,
    ) -> WelderCertifiedProject:
        expiry = self._parse_date_value(data.get("expiry_date"))
        project = WelderCertifiedProject(
            certification_id=certification.id,
            welder_id=certification.welder_id,
            project_code=data.get("project_code"),
            project_name=data.get("project_name") or "持证项目",
            issue_date=self._parse_date_value(data.get("issue_date")),
            expiry_date=expiry,
            renewal_date=self._parse_date_value(data.get("renewal_date")),
            renewal_count=data.get("renewal_count") or 0,
            next_renewal_date=self._parse_date_value(data.get("next_renewal_date")),
            renewal_result=data.get("renewal_result"),
            renewal_notes=data.get("renewal_notes"),
            status=data.get("status") or _compute_project_status(expiry),
            notes=data.get("notes"),
            created_by=current_user.id,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        self._sync_cert_expiry_from_projects(certification.id)
        return project

    def _ensure_and_list_projects(
        self,
        cert: WelderCertification,
        current_user: User,
    ) -> List[Dict[str, Any]]:
        """列出项目；若为空则从证书旧字段 / qualified_items 迁移."""
        projects = (
            self.db.query(WelderCertifiedProject)
            .filter(
                WelderCertifiedProject.certification_id == cert.id,
                WelderCertifiedProject.is_active == True,  # noqa: E712
            )
            .order_by(WelderCertifiedProject.expiry_date.asc())
            .all()
        )
        if projects:
            return [_project_to_dict(p) for p in projects]

        created: List[WelderCertifiedProject] = []
        # 1) 证书级 project_name / expiry
        if cert.project_name or cert.expiry_date:
            created.append(
                self._create_project_row(
                    certification=cert,
                    data={
                        "project_name": cert.project_name or cert.certification_type or "持证项目",
                        "issue_date": cert.issue_date,
                        "expiry_date": cert.expiry_date,
                        "renewal_date": cert.renewal_date,
                        "renewal_count": cert.renewal_count or 0,
                        "next_renewal_date": cert.next_renewal_date,
                        "renewal_result": cert.renewal_result,
                        "renewal_notes": cert.renewal_notes,
                        "status": cert.status or "valid",
                    },
                    current_user=current_user,
                )
            )
        # 2) qualified_items JSON（只读兼容迁移）
        elif cert.qualified_items:
            try:
                items = json.loads(cert.qualified_items) if isinstance(cert.qualified_items, str) else cert.qualified_items
            except (TypeError, json.JSONDecodeError):
                items = []
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("item") or item.get("name") or item.get("description")
                    if not name:
                        continue
                    created.append(
                        self._create_project_row(
                            certification=cert,
                            data={
                                "project_code": item.get("item"),
                                "project_name": item.get("description") or name,
                                "issue_date": cert.issue_date,
                                "expiry_date": cert.expiry_date,
                                "status": cert.status or "valid",
                                "notes": item.get("notes"),
                            },
                            current_user=current_user,
                        )
                    )
        return [_project_to_dict(p) for p in created]

    def _sync_cert_expiry_from_projects(self, certification_id: int) -> None:
        """用项目最近到期回写证书摘要字段，兼容旧列表."""
        cert = (
            self.db.query(WelderCertification)
            .filter(WelderCertification.id == certification_id)
            .first()
        )
        if not cert:
            return
        projects = (
            self.db.query(WelderCertifiedProject)
            .filter(
                WelderCertifiedProject.certification_id == certification_id,
                WelderCertifiedProject.is_active == True,  # noqa: E712
            )
            .all()
        )
        if not projects:
            return
        nearest = None
        for p in projects:
            if p.expiry_date and (nearest is None or p.expiry_date < nearest):
                nearest = p.expiry_date
        if nearest:
            cert.expiry_date = nearest
            cert.status = _compute_project_status(nearest)
        if projects:
            primary_p = projects[0]
            if primary_p.project_name:
                cert.project_name = primary_p.project_name
        self.db.commit()

    def get_certified_projects(
        self,
        welder_id: int,
        certification_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> List[Dict[str, Any]]:
        workspace_context.validate()
        self.get_welder_by_id(welder_id, current_user, workspace_context)
        cert = (
            self.db.query(WelderCertification)
            .filter(
                WelderCertification.id == certification_id,
                WelderCertification.welder_id == welder_id,
                WelderCertification.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="证书不存在")
        return self._ensure_and_list_projects(cert, current_user)

    def add_certified_project(
        self,
        welder_id: int,
        certification_id: int,
        project_data: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        workspace_context.validate()
        welder = self.get_welder_by_id(welder_id, current_user, workspace_context)
        self.data_access.check_access(current_user, welder, "EDIT", workspace_context)
        cert = (
            self.db.query(WelderCertification)
            .filter(
                WelderCertification.id == certification_id,
                WelderCertification.welder_id == welder_id,
                WelderCertification.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not cert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="证书不存在")
        if not project_data.get("project_name"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="持证项目名称必填")
        project = self._create_project_row(cert, project_data, current_user)
        return _project_to_dict(project)

    def update_certified_project(
        self,
        welder_id: int,
        certification_id: int,
        project_id: int,
        project_data: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        workspace_context.validate()
        welder = self.get_welder_by_id(welder_id, current_user, workspace_context)
        self.data_access.check_access(current_user, welder, "EDIT", workspace_context)
        project = (
            self.db.query(WelderCertifiedProject)
            .filter(
                WelderCertifiedProject.id == project_id,
                WelderCertifiedProject.certification_id == certification_id,
                WelderCertifiedProject.welder_id == welder_id,
                WelderCertifiedProject.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="持证项目不存在")

        for field in (
            "project_code",
            "project_name",
            "renewal_result",
            "renewal_notes",
            "status",
            "notes",
            "renewal_count",
        ):
            if field in project_data and project_data[field] is not None:
                setattr(project, field, project_data[field])
        for date_field in ("issue_date", "expiry_date", "renewal_date", "next_renewal_date"):
            if date_field in project_data:
                setattr(project, date_field, self._parse_date_value(project_data[date_field]))
        if "expiry_date" in project_data and "status" not in project_data:
            project.status = _compute_project_status(project.expiry_date)
        project.updated_by = current_user.id
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        self._sync_cert_expiry_from_projects(certification_id)
        return _project_to_dict(project)

    def delete_certified_project(
        self,
        welder_id: int,
        certification_id: int,
        project_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> bool:
        workspace_context.validate()
        welder = self.get_welder_by_id(welder_id, current_user, workspace_context)
        self.data_access.check_access(current_user, welder, "EDIT", workspace_context)
        project = (
            self.db.query(WelderCertifiedProject)
            .filter(
                WelderCertifiedProject.id == project_id,
                WelderCertifiedProject.certification_id == certification_id,
                WelderCertifiedProject.welder_id == welder_id,
                WelderCertifiedProject.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="持证项目不存在")
        project.is_active = False
        project.updated_by = current_user.id
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self._sync_cert_expiry_from_projects(certification_id)
        return True

    # ==================== 统计分析 ====================

    def get_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, Any]:
        """
        获取焊工统计信息

        Args:
            current_user: 当前用户
            workspace_context: 工作区上下文

        Returns:
            Dict: 统计信息
        """
        try:
            # 验证工作区上下文
            workspace_context.validate()

            # 检查查看权限并获取访问范围
            permission_result = self._check_list_permission(current_user, workspace_context)

            # 构建基础查询
            query = self.db.query(Welder).filter(
                Welder.is_active == True
            )

            # 应用数据隔离过滤
            query = self.data_access.apply_workspace_filter(
                query,
                Welder,
                current_user,
                workspace_context
            )

            # 统计总数
            total_welders = query.count()

            # 统计在职焊工
            active_welders = query.filter(Welder.status == "active").count()

            # 统计持证焊工
            certified_welders = query.filter(
                Welder.certification_status == "valid"
            ).count()

            # 统计即将到期的证书（30天内）
            from datetime import datetime, timedelta
            expiry_threshold = datetime.now() + timedelta(days=30)

            expiring_count = 0
            welders_with_certs = query.filter(
                Welder.certification_status == "valid"
            ).all()

            for welder in welders_with_certs:
                # 查询该焊工的证书
                certs = self.db.query(WelderCertification).filter(
                    WelderCertification.welder_id == welder.id,
                    WelderCertification.is_active == True,
                    WelderCertification.status == "valid",
                    WelderCertification.expiry_date <= expiry_threshold
                ).count()
                if certs > 0:
                    expiring_count += 1

            return {
                "total_welders": total_welders,
                "active_welders": active_welders,
                "certified_welders": certified_welders,
                "expiring_certifications": expiring_count
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取统计信息失败: {str(e)}"
            )
