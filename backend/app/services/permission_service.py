"""
Permission service for managing user permissions and access control.
"""
from typing import Dict, List, Optional, Any, Set
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.admin import Admin


class Permission(Enum):
    """权限枚举"""
    # 用户管理权限
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"
    
    # WPS管理权限
    WPS_READ = "wps:read"
    WPS_CREATE = "wps:create"
    WPS_UPDATE = "wps:update"
    WPS_DELETE = "wps:delete"
    WPS_MANAGE = "wps:manage"
    WPS_EXPORT = "wps:export"
    
    # PQR管理权限
    PQR_READ = "pqr:read"
    PQR_CREATE = "pqr:create"
    PQR_UPDATE = "pqr:update"
    PQR_DELETE = "pqr:delete"
    PQR_MANAGE = "pqr:manage"
    PQR_EXPORT = "pqr:export"
    
    # pPQR管理权限
    PPQR_READ = "ppqr:read"
    PPQR_CREATE = "ppqr:create"
    PPQR_UPDATE = "ppqr:update"
    PPQR_DELETE = "ppqr:delete"
    PPQR_MANAGE = "ppqr:manage"
    PPQR_EXPORT = "ppqr:export"
    
    # 设备管理权限
    EQUIPMENT_READ = "equipment:read"
    EQUIPMENT_CREATE = "equipment:create"
    EQUIPMENT_UPDATE = "equipment:update"
    EQUIPMENT_DELETE = "equipment:delete"
    EQUIPMENT_MANAGE = "equipment:manage"
    
    # 焊材管理权限
    MATERIAL_READ = "material:read"
    MATERIAL_CREATE = "material:create"
    MATERIAL_UPDATE = "material:update"
    MATERIAL_DELETE = "material:delete"
    MATERIAL_MANAGE = "material:manage"
    
    # 焊工管理权限
    WELDER_READ = "welder:read"
    WELDER_CREATE = "welder:create"
    WELDER_UPDATE = "welder:update"
    WELDER_DELETE = "welder:delete"
    WELDER_MANAGE = "welder:manage"
    
    # 生产管理权限
    PRODUCTION_READ = "production:read"
    PRODUCTION_CREATE = "production:create"
    PRODUCTION_UPDATE = "production:update"
    PRODUCTION_DELETE = "production:delete"
    PRODUCTION_MANAGE = "production:manage"
    
    # 质量管理权限
    QUALITY_READ = "quality:read"
    QUALITY_CREATE = "quality:create"
    QUALITY_UPDATE = "quality:update"
    QUALITY_DELETE = "quality:delete"
    QUALITY_MANAGE = "quality:manage"
    
    # 报表统计权限
    REPORT_READ = "report:read"
    REPORT_CREATE = "report:create"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"
    REPORT_MANAGE = "report:manage"
    
    # 会员管理权限
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_CREATE = "membership:create"
    MEMBERSHIP_UPDATE = "membership:update"
    MEMBERSHIP_DELETE = "membership:delete"
    MEMBERSHIP_MANAGE = "membership:manage"
    MEMBERSHIP_UPGRADE = "membership:upgrade"
    
    # 订阅管理权限
    SUBSCRIPTION_READ = "subscription:read"
    SUBSCRIPTION_CREATE = "subscription:create"
    SUBSCRIPTION_UPDATE = "subscription:update"
    SUBSCRIPTION_DELETE = "subscription:delete"
    SUBSCRIPTION_MANAGE = "subscription:manage"
    SUBSCRIPTION_RENEW = "subscription:renew"
    SUBSCRIPTION_CANCEL = "subscription:cancel"
    
    # 系统管理权限
    SYSTEM_READ = "system:read"
    SYSTEM_UPDATE = "system:update"
    SYSTEM_MANAGE = "system:manage"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOG = "system:log"
    SYSTEM_MONITOR = "system:monitor"
    
    # 公告管理权限
    ANNOUNCEMENT_READ = "announcement:read"
    ANNOUNCEMENT_CREATE = "announcement:create"
    ANNOUNCEMENT_UPDATE = "announcement:update"
    ANNOUNCEMENT_DELETE = "announcement:delete"
    ANNOUNCEMENT_MANAGE = "announcement:manage"
    
    # 企业管理权限
    ENTERPRISE_READ = "enterprise:read"
    ENTERPRISE_CREATE = "enterprise:create"
    ENTERPRISE_UPDATE = "enterprise:update"
    ENTERPRISE_DELETE = "enterprise:delete"
    ENTERPRISE_MANAGE = "enterprise:manage"
    
    # 文件管理权限
    FILE_READ = "file:read"
    FILE_CREATE = "file:create"
    FILE_UPDATE = "file:update"
    FILE_DELETE = "file:delete"
    FILE_MANAGE = "file:manage"
    FILE_UPLOAD = "file:upload"
    FILE_DOWNLOAD = "file:download"


class PermissionService:
    """权限服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_permissions(self, user_id: int) -> Set[str]:
        """获取用户权限集合"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()
        
        # 基础权限
        permissions = self._get_base_permissions(user)
        
        # 会员等级权限
        membership_permissions = self._get_membership_permissions(user)
        permissions.update(membership_permissions)
        
        # 自定义权限（如果有）
        custom_permissions = self._get_custom_permissions(user)
        permissions.update(custom_permissions)
        
        return permissions
    
    def get_admin_permissions(self, admin_id: int) -> Set[str]:
        """获取管理员权限集合"""
        admin = self.db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            return set()
        
        # 管理员基础权限
        permissions = self._get_admin_base_permissions(admin)
        
        # 角色权限
        role_permissions = self._get_role_permissions(admin)
        permissions.update(role_permissions)
        
        # 自定义权限（如果有）
        custom_permissions = self._get_admin_custom_permissions(admin)
        permissions.update(custom_permissions)
        
        return permissions
    
    def has_permission(self, user_id: int, permission: str, is_admin: bool = False) -> bool:
        """检查用户是否有指定权限"""
        if is_admin:
            permissions = self.get_admin_permissions(user_id)
        else:
            permissions = self.get_user_permissions(user_id)
        
        return permission in permissions
    
    def has_any_permission(self, user_id: int, permissions: List[str], is_admin: bool = False) -> bool:
        """检查用户是否有任意一个指定权限"""
        if is_admin:
            user_permissions = self.get_admin_permissions(user_id)
        else:
            user_permissions = self.get_user_permissions(user_id)
        
        return any(permission in user_permissions for permission in permissions)
    
    def has_all_permissions(self, user_id: int, permissions: List[str], is_admin: bool = False) -> bool:
        """检查用户是否有所有指定权限"""
        if is_admin:
            user_permissions = self.get_admin_permissions(user_id)
        else:
            user_permissions = self.get_user_permissions(user_id)
        
        return all(permission in user_permissions for permission in permissions)
    
    def check_permission(self, user_id: int, permission: str, is_admin: bool = False):
        """检查权限，如果没有则抛出异常"""
        if not self.has_permission(user_id, permission, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要权限: {permission}"
            )
    
    def _get_base_permissions(self, user: User) -> Set[str]:
        """获取用户基础权限"""
        permissions = set()
        
        # 所有用户都有读取自己信息的权限
        permissions.add(Permission.USER_READ.value)
        
        # 根据用户状态添加权限
        if user.is_active:
            permissions.add(Permission.WPS_READ.value)
            permissions.add(Permission.PQR_READ.value)
            permissions.add(Permission.FILE_READ.value)
            permissions.add(Permission.FILE_DOWNLOAD.value)
        
        return permissions
    
    def _get_membership_permissions(self, user: User) -> Set[str]:
        """根据会员等级获取权限"""
        permissions = set()
        
        if not user.member_tier:
            return permissions
        
        # 免费版权限
        if user.member_tier == "free":
            permissions.add(Permission.WPS_CREATE.value)
            permissions.add(Permission.PQR_CREATE.value)
            permissions.add(Permission.FILE_UPLOAD.value)
        
        # 个人专业版权限
        elif user.member_tier == "personal_pro":
            permissions.update([
                Permission.WPS_CREATE.value,
                Permission.WPS_UPDATE.value,
                Permission.WPS_DELETE.value,
                Permission.PQR_CREATE.value,
                Permission.PQR_UPDATE.value,
                Permission.PQR_DELETE.value,
                Permission.PPQR_CREATE.value,
                Permission.PPQR_UPDATE.value,
                Permission.PPQR_DELETE.value,
                Permission.FILE_UPLOAD.value,
                Permission.FILE_DOWNLOAD.value,
            ])
        
        # 个人高级版权限
        elif user.member_tier == "personal_advanced":
            permissions.update([
                Permission.WPS_CREATE.value,
                Permission.WPS_UPDATE.value,
                Permission.WPS_DELETE.value,
                Permission.WPS_EXPORT.value,
                Permission.PQR_CREATE.value,
                Permission.PQR_UPDATE.value,
                Permission.PQR_DELETE.value,
                Permission.PQR_EXPORT.value,
                Permission.PPQR_CREATE.value,
                Permission.PPQR_UPDATE.value,
                Permission.PPQR_DELETE.value,
                Permission.PPQR_EXPORT.value,
                Permission.EQUIPMENT_CREATE.value,
                Permission.EQUIPMENT_UPDATE.value,
                Permission.EQUIPMENT_DELETE.value,
                Permission.PRODUCTION_READ.value,
                Permission.PRODUCTION_CREATE.value,
                Permission.PRODUCTION_UPDATE.value,
                Permission.PRODUCTION_DELETE.value,
                Permission.QUALITY_READ.value,
                Permission.QUALITY_CREATE.value,
                Permission.QUALITY_UPDATE.value,
                Permission.QUALITY_DELETE.value,
                Permission.FILE_UPLOAD.value,
                Permission.FILE_DOWNLOAD.value,
            ])
        
        # 个人旗舰版权限
        elif user.member_tier == "personal_flagship":
            permissions.update([
                Permission.WPS_CREATE.value,
                Permission.WPS_UPDATE.value,
                Permission.WPS_DELETE.value,
                Permission.WPS_EXPORT.value,
                Permission.PQR_CREATE.value,
                Permission.PQR_UPDATE.value,
                Permission.PQR_DELETE.value,
                Permission.PQR_EXPORT.value,
                Permission.PPQR_CREATE.value,
                Permission.PPQR_UPDATE.value,
                Permission.PPQR_DELETE.value,
                Permission.PPQR_EXPORT.value,
                Permission.EQUIPMENT_CREATE.value,
                Permission.EQUIPMENT_UPDATE.value,
                Permission.EQUIPMENT_DELETE.value,
                Permission.MATERIAL_CREATE.value,
                Permission.MATERIAL_UPDATE.value,
                Permission.MATERIAL_DELETE.value,
                Permission.WELDER_CREATE.value,
                Permission.WELDER_UPDATE.value,
                Permission.WELDER_DELETE.value,
                Permission.PRODUCTION_READ.value,
                Permission.PRODUCTION_CREATE.value,
                Permission.PRODUCTION_UPDATE.value,
                Permission.PRODUCTION_DELETE.value,
                Permission.QUALITY_READ.value,
                Permission.QUALITY_CREATE.value,
                Permission.QUALITY_UPDATE.value,
                Permission.QUALITY_DELETE.value,
                Permission.REPORT_READ.value,
                Permission.FILE_UPLOAD.value,
                Permission.FILE_DOWNLOAD.value,
            ])
        
        # 企业版及以上权限
        elif user.member_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]:
            # 企业版拥有所有权限
            permissions.update([p.value for p in Permission])
        
        return permissions
    
    def _get_custom_permissions(self, user: User) -> Set[str]:
        """获取用户自定义权限"""
        # 这里可以从数据库中获取用户的自定义权限
        # 暂时返回空集合
        return set()
    
    def _get_admin_base_permissions(self, admin: Admin) -> Set[str]:
        """获取管理员基础权限"""
        permissions = set()
        
        # 所有管理员都有读取权限
        permissions.update([
            Permission.USER_READ.value,
            Permission.WPS_READ.value,
            Permission.PQR_READ.value,
            Permission.PPQR_READ.value,
            Permission.EQUIPMENT_READ.value,
            Permission.MATERIAL_READ.value,
            Permission.WELDER_READ.value,
            Permission.PRODUCTION_READ.value,
            Permission.QUALITY_READ.value,
            Permission.REPORT_READ.value,
            Permission.MEMBERSHIP_READ.value,
            Permission.SUBSCRIPTION_READ.value,
            Permission.SYSTEM_READ.value,
            Permission.ANNOUNCEMENT_READ.value,
            Permission.ENTERPRISE_READ.value,
            Permission.FILE_READ.value,
        ])
        
        return permissions
    
    def _get_role_permissions(self, admin: Admin) -> Set[str]:
        """根据管理员角色获取权限"""
        permissions = set()
        
        # 普通管理员权限
        if admin.admin_level == "admin":
            permissions.update([
                Permission.USER_CREATE.value,
                Permission.USER_UPDATE.value,
                Permission.USER_DELETE.value,
                Permission.WPS_MANAGE.value,
                Permission.PQR_MANAGE.value,
                Permission.PPQR_MANAGE.value,
                Permission.EQUIPMENT_MANAGE.value,
                Permission.MATERIAL_MANAGE.value,
                Permission.WELDER_MANAGE.value,
                Permission.PRODUCTION_MANAGE.value,
                Permission.QUALITY_MANAGE.value,
                Permission.REPORT_MANAGE.value,
                Permission.MEMBERSHIP_MANAGE.value,
                Permission.SUBSCRIPTION_MANAGE.value,
                Permission.ANNOUNCEMENT_MANAGE.value,
                Permission.ENTERPRISE_MANAGE.value,
                Permission.FILE_MANAGE.value,
            ])
        
        # 超级管理员权限
        elif admin.admin_level == "super_admin":
            # 超级管理员拥有所有权限
            permissions.update([p.value for p in Permission])
        
        return permissions
    
    def _get_admin_custom_permissions(self, admin: Admin) -> Set[str]:
        """获取管理员自定义权限"""
        # 这里可以从数据库中获取管理员的自定义权限
        # 暂时返回空集合
        return set()


def get_permission_service(db: Session) -> PermissionService:
    """获取权限服务实例"""
    return PermissionService(db)