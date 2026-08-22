"""
Main API router for the welding system backend v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    admin_auth,
    auth,
    users,
    members,
    roles,
    wps,
    wps_export,
    wps_templates,
    custom_modules,
    shared_library,
    pqr,
    pqr_export,
    ppqr,
    ppqr_export,
    welders,
    materials,
    equipment,
    production,
    quality,
    reports,
    files,
    system,
    system_admin,
    membership_admin,
    upload,
    enterprise,
    enterprise_org,
    enterprise_invitations,
    company_roles,
    workspace,
    dashboard,
    payments,
    notifications,
    approvals,
    business_mvp,
    feedback,
)

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 文件上传路由
api_router.include_router(upload.router, prefix="/upload", tags=["文件上传"])

# 仪表盘路由
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])

# 管理员认证路由
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["管理员认证"])
# 添加注释触发重新加载 - v2

# 管理员路由（最高优先级） - 使用我们的新管理员API
api_router.include_router(admin.router, prefix="/admin", tags=["管理员功能"])
api_router.include_router(system_admin.router, prefix="/admin/system", tags=["系统管理"])
api_router.include_router(membership_admin.router, prefix="/admin/membership", tags=["会员管理"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# 会员管理路由
api_router.include_router(members.router, prefix="/members", tags=["会员管理"])

# 支付管理路由
api_router.include_router(payments.router, prefix="/payments", tags=["支付管理"])

# 通知管理路由
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知管理"])

# 用户意见反馈
api_router.include_router(feedback.router, prefix="/feedback", tags=["用户反馈"])
api_router.include_router(feedback.admin_router, prefix="/admin/feedback", tags=["用户反馈管理"])

# 角色权限管理路由
api_router.include_router(roles.router, prefix="/roles", tags=["角色权限管理"])

# WPS管理路由
api_router.include_router(wps.router, prefix="/wps", tags=["WPS管理"])

# WPS导出路由
api_router.include_router(wps_export.router, prefix="/wps", tags=["WPS导出"])

# WPS模板管理路由
api_router.include_router(wps_templates.router, prefix="/wps-templates", tags=["WPS模板管理"])

# 自定义模块管理路由
api_router.include_router(custom_modules.router, prefix="/custom-modules", tags=["自定义模块管理"])

# 共享库路由
api_router.include_router(shared_library.router, prefix="/shared-library", tags=["共享库管理"])

# PQR管理路由
api_router.include_router(pqr.router, prefix="/pqr", tags=["PQR管理"])

# PQR导出路由
api_router.include_router(pqr_export.router, prefix="/pqr", tags=["PQR导出"])

# pPQR管理路由
api_router.include_router(ppqr.router, prefix="/ppqr", tags=["pPQR管理"])

# pPQR导出路由
api_router.include_router(ppqr_export.router, prefix="/ppqr", tags=["pPQR导出"])

# 焊工管理路由
api_router.include_router(welders.router, prefix="/welders", tags=["焊工管理"])

# 焊材管理路由
api_router.include_router(materials.router, prefix="/materials", tags=["焊材管理"])

# 设备管理路由
api_router.include_router(equipment.router, prefix="/equipment", tags=["设备管理"])

# 生产管理路由
api_router.include_router(production.router, prefix="/production", tags=["生产管理"])

# 质量管理路由
api_router.include_router(quality.router, prefix="/quality", tags=["质量管理"])

# 报表统计路由
api_router.include_router(reports.router, prefix="/reports", tags=["报表统计"])

# 文件管理路由
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])

# 企业管理路由
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["企业管理"])
api_router.include_router(enterprise_org.router, prefix="/enterprise", tags=["企业组织"])
api_router.include_router(enterprise_invitations.router, prefix="/enterprise", tags=["企业邀请"])

# 企业角色管理路由
api_router.include_router(company_roles.router, prefix="/enterprise", tags=["企业角色管理"])

# 工作区管理路由
api_router.include_router(workspace.router, prefix="/workspace", tags=["工作区管理"])

# 审批管理路由
api_router.include_router(approvals.router, prefix="/approvals", tags=["审批管理"])

# 业务扩展 MVP
api_router.include_router(business_mvp.router, tags=["业务扩展"])

# 系统管理路由
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])