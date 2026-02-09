"""
Welder Service for the welding system backend.
焊工管理服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
import logging

from app.models.welder import Welder, WelderCertification
from app.models.user import User
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.schemas.welder import WelderCreate, WelderUpdate
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.services.quota_service import QuotaService

logger = logging.getLogger(__name__)


class WelderService:
    """焊工管理服务类"""

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

            # 证书状态筛选
            if certification_status:
                logger.info(f"[服务层] 应用证书状态筛选: {certification_status}")
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
                    "updated_at": cert.updated_at.isoformat() if cert.updated_at else None
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
                "is_active": certification.is_active
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

