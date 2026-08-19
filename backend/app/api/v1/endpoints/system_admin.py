"""
System administration endpoints for the welding system backend.
系统管理API端点
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.admin_deps import get_current_active_admin
from app.models.admin import Admin
from app.models.system_announcement import SystemAnnouncement
from app.models.system_log import SystemLog
from app.services.system_service import SystemService
from app.services.notification_service import NotificationService
from app.core.database import get_db

router = APIRouter()


@router.get("/system/status")
def get_system_status(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取系统状态（管理员专用）
    """
    system_service = SystemService(db)
    status_data = system_service.get_system_status()

    return {
        "success": True,
        "data": status_data
    }


@router.get("/statistics/overview")
def get_overview_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取总览统计数据（管理员专用）
    """
    system_service = SystemService(db)

    # 获取用户统计
    user_stats = system_service.get_user_statistics()

    # 获取订阅统计
    subscription_stats = system_service.get_subscription_statistics()

    # 获取系统状态
    system_status = system_service.get_system_status()

    return {
        "success": True,
        "data": {
            "users": user_stats,
            "subscriptions": subscription_stats,
            "system": system_status
        }
    }


@router.get("/statistics/users")
def get_user_statistics_admin(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取用户统计数据（管理员专用）
    """
    system_service = SystemService(db)

    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

    stats = system_service.get_user_statistics(start_datetime, end_datetime)

    return {
        "success": True,
        "data": stats
    }


@router.get("/statistics/subscriptions")
def get_subscription_statistics_admin(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅统计数据（管理员专用）
    """
    system_service = SystemService(db)

    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

    stats = system_service.get_subscription_statistics(start_datetime, end_datetime)

    return {
        "success": True,
        "data": stats
    }


@router.get("/logs/errors")
def get_error_logs_admin(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取错误日志（管理员专用）
    """
    system_service = SystemService(db)

    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

    logs = system_service.get_error_logs(
        page=page,
        page_size=page_size,
        level=level,
        start_date=start_datetime,
        end_date=end_datetime
    )

    return {
        "success": True,
        "data": logs
    }


@router.get("/config")
def get_system_config_admin(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取系统配置（管理员专用）
    """
    system_service = SystemService(db)
    config = system_service.get_system_config()

    return {
        "success": True,
        "data": config
    }


@router.put("/config")
def update_system_config_admin(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    更新系统配置（管理员专用）
    """
    system_service = SystemService(db)

    # 检查是否有超级管理员权限
    if current_admin.admin_level != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    updated_config = system_service.update_system_config(config_data)

    return {
        "success": True,
        "message": "系统配置已更新",
        "data": updated_config
    }


# 公告管理
@router.get("/announcements")
def get_announcements_admin(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_published: Optional[bool] = Query(None, description="发布状态筛选"),
    announcement_type: Optional[str] = Query(None, description="公告类型筛选"),
    is_auto_generated: Optional[bool] = Query(None, description="是否为自动生成"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取系统公告列表（管理员专用）
    """
    query = db.query(SystemAnnouncement)

    # 应用筛选
    if is_published is not None:
        query = query.filter(SystemAnnouncement.is_published == is_published)

    if announcement_type:
        query = query.filter(SystemAnnouncement.announcement_type == announcement_type)

    if is_auto_generated is not None:
        query = query.filter(SystemAnnouncement.is_auto_generated == is_auto_generated)

    # 总数统计
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    announcements = query.order_by(SystemAnnouncement.created_at.desc()).offset(offset).limit(page_size).all()

    # 转换为响应格式
    announcement_items = []
    for announcement in announcements:
        announcement_items.append({
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "announcement_type": announcement.announcement_type,
            "priority": announcement.priority,
            "is_published": announcement.is_published,
            "is_pinned": announcement.is_pinned,
            "is_auto_generated": getattr(announcement, 'is_auto_generated', False),
            "target_audience": announcement.target_audience,
            "publish_at": announcement.publish_at.isoformat() if announcement.publish_at else None,
            "expire_at": announcement.expire_at.isoformat() if announcement.expire_at else None,
            "view_count": announcement.view_count,
            "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
            "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None,
        })

    return {
        "success": True,
        "data": {
            "items": announcement_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.post("/announcements")
def create_announcement_admin(
    announcement_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    创建系统公告（管理员专用）
    """
    announcement = SystemAnnouncement(
        title=announcement_data.get("title"),
        content=announcement_data.get("content"),
        announcement_type=announcement_data.get("announcement_type", "info"),
        priority=announcement_data.get("priority", "normal"),
        target_audience=announcement_data.get("target_audience", "all"),
        is_pinned=announcement_data.get("is_pinned", False),
        publish_at=datetime.fromisoformat(announcement_data["publish_at"]) if announcement_data.get("publish_at") else None,
        expire_at=datetime.fromisoformat(announcement_data["expire_at"]) if announcement_data.get("expire_at") else None,
        created_by=current_admin.user_id,
        is_published=announcement_data.get("is_published", False)
    )

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # 记录操作日志
    system_service = SystemService(db)
    admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {admin_email} 创建了公告: {announcement.title}",
        user_id=current_admin.user_id,
        details={"announcement_id": announcement.id}
    )

    return {
        "success": True,
        "message": "公告创建成功",
        "data": {
            "id": announcement.id,
            "title": announcement.title
        }
    }


@router.put("/announcements/{announcement_id}")
def update_announcement_admin(
    announcement_id: int,
    announcement_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    更新系统公告（管理员专用）
    """
    announcement = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    # 更新字段
    if "title" in announcement_data:
        announcement.title = announcement_data["title"]
    if "content" in announcement_data:
        announcement.content = announcement_data["content"]
    if "announcement_type" in announcement_data:
        announcement.announcement_type = announcement_data["announcement_type"]
    if "priority" in announcement_data:
        announcement.priority = announcement_data["priority"]
    if "target_audience" in announcement_data:
        announcement.target_audience = announcement_data["target_audience"]
    if "is_published" in announcement_data:
        announcement.is_published = announcement_data["is_published"]
    if "is_pinned" in announcement_data:
        announcement.is_pinned = announcement_data["is_pinned"]
    if "publish_at" in announcement_data and announcement_data["publish_at"]:
        announcement.publish_at = datetime.fromisoformat(announcement_data["publish_at"])
    if "expire_at" in announcement_data and announcement_data["expire_at"]:
        announcement.expire_at = datetime.fromisoformat(announcement_data["expire_at"])

    announcement.updated_at = datetime.utcnow()
    announcement.updated_by = current_admin.user_id

    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {admin_email} 更新了公告: {announcement.title}",
        user_id=current_admin.user_id,
        details={"announcement_id": announcement.id}
    )

    return {
        "success": True,
        "message": "公告更新成功",
        "data": {
            "id": announcement.id,
            "title": announcement.title
        }
    }


@router.post("/announcements/{announcement_id}/publish")
def publish_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    发布系统公告（管理员专用）
    """
    announcement = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    announcement.is_published = True
    announcement.publish_at = datetime.utcnow()
    announcement.updated_at = datetime.utcnow()
    announcement.updated_by = current_admin.user_id

    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {admin_email} 发布了公告: {announcement.title}",
        user_id=current_admin.user_id,
        details={"announcement_id": announcement.id}
    )

    return {
        "success": True,
        "message": "公告发布成功",
        "data": {
            "id": announcement.id,
            "title": announcement.title,
            "publish_at": announcement.publish_at.isoformat()
        }
    }


@router.delete("/announcements/{announcement_id}")
def delete_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    删除系统公告（管理员专用）
    """
    announcement = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    announcement_title = announcement.title
    db.delete(announcement)
    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {admin_email} 删除了公告: {announcement_title}",
        user_id=current_admin.user_id,
        details={"announcement_id": announcement_id}
    )

    return {
        "success": True,
        "message": f"公告 '{announcement_title}' 已删除",
        "data": {
            "deleted_announcement_id": announcement_id
        }
    }


@router.post("/announcements/{announcement_id}/unpublish")
def unpublish_announcement_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    取消发布系统公告（管理员专用）
    """
    announcement = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    announcement.is_published = False
    announcement.updated_at = datetime.utcnow()
    announcement.updated_by = current_admin.user_id

    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {admin_email} 取消发布了公告: {announcement.title}",
        user_id=current_admin.user_id,
        details={"announcement_id": announcement.id}
    )

    return {
        "success": True,
        "message": "公告已取消发布",
        "data": {
            "id": announcement.id,
            "title": announcement.title
        }
    }


# ==================== 自动通知任务 ====================

@router.post("/notifications/tasks/daily")
def run_daily_notification_tasks(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    手动触发每日通知任务
    包括：会员到期提醒、过期处理、自动续费、配额警告
    """
    try:
        notification_service = NotificationService(db)

        # 1. 检查并通知即将到期的会员
        expiring_count = notification_service.send_expiration_reminders(days_ahead=7)

        # 2. 检查并通知已过期的会员
        expired_count = notification_service.process_expired_subscriptions()

        # 3. 处理自动续费
        renewed_count = notification_service.process_auto_renewals()

        # 4. 检查配额使用情况
        quota_count = notification_service.check_and_notify_quota_usage()

        # 记录操作日志
        system_service = SystemService(db)
        admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
        system_service.create_system_log(
            log_level="info",
            log_type="admin",
            message=f"管理员 {admin_email} 手动触发了每日通知任务",
            user_id=current_admin.user_id,
            details={
                "expiring_count": expiring_count,
                "expired_count": expired_count,
                "renewed_count": renewed_count,
                "quota_count": quota_count,
            }
        )

        return {
            "success": True,
            "message": "每日通知任务执行完成",
            "data": {
                "expiring_count": expiring_count,
                "expired_count": expired_count,
                "renewed_count": renewed_count,
                "quota_count": quota_count,
                "total_notifications": expiring_count + expired_count + renewed_count + quota_count,
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行通知任务失败: {str(e)}"
        )


@router.post("/notifications/tasks/expiring")
def run_expiring_notification_task(
    days_ahead: int = Query(7, ge=1, le=30, description="提前多少天通知"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    手动触发会员到期提醒任务
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.send_expiration_reminders(days_ahead=days_ahead)

        # 记录操作日志
        system_service = SystemService(db)
        admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
        system_service.create_system_log(
            log_level="info",
            log_type="admin",
            message=f"管理员 {admin_email} 手动触发了会员到期提醒任务（提前{days_ahead}天）",
            user_id=current_admin.user_id,
            details={"days_ahead": days_ahead, "count": count}
        )

        return {
            "success": True,
            "message": f"已发送 {count} 条会员到期提醒",
            "data": {
                "count": count,
                "days_ahead": days_ahead
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行会员到期提醒任务失败: {str(e)}"
        )


@router.post("/notifications/tasks/quota")
def run_quota_notification_task(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    手动触发配额使用警告任务
    """
    try:
        notification_service = NotificationService(db)
        count = notification_service.check_and_notify_quota_usage()

        # 记录操作日志
        system_service = SystemService(db)
        admin_email = current_admin.email if current_admin.email else f"ID:{current_admin.id}"
        system_service.create_system_log(
            log_level="info",
            log_type="admin",
            message=f"管理员 {admin_email} 手动触发了配额警告任务",
            user_id=current_admin.user_id,
            details={"count": count}
        )

        return {
            "success": True,
            "message": f"已发送 {count} 条配额警告",
            "data": {
                "count": count
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行配额警告任务失败: {str(e)}"
        )