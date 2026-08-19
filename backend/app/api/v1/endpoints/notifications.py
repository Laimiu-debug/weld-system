"""
Notifications endpoints for the welding system backend.
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.models.system_announcement import SystemAnnouncement
from app.models.user_notification import UserNotificationReadStatus

router = APIRouter()


@router.get("/")
def get_notifications(
    unread_only: bool = Query(False, description="只获取未读通知"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取用户通知列表"""
    user_id = current_user.id

    # 获取用户注册时间
    user_created_at = current_user.created_at

    # 查询有效的系统公告 - 只显示用户注册后发布的通知
    query = db.query(SystemAnnouncement).filter(
        and_(
            SystemAnnouncement.is_published == True,
            SystemAnnouncement.publish_at <= datetime.utcnow(),
            SystemAnnouncement.publish_at >= user_created_at,  # 只显示用户注册后发布的通知
            or_(
                SystemAnnouncement.expire_at.is_(None),
                SystemAnnouncement.expire_at > datetime.utcnow()
            ),
            or_(
                SystemAnnouncement.target_audience == "all",
                SystemAnnouncement.target_audience == "user",
                SystemAnnouncement.created_by == user_id
            )
        )
    )

    # 获取所有符合条件的公告ID
    all_announcements = query.all()
    announcement_ids = [a.id for a in all_announcements]

    # 获取用户的已读/已删除状态
    read_status_map = {}
    deleted_ids = set()
    if announcement_ids:
        read_statuses = db.query(UserNotificationReadStatus).filter(
            and_(
                UserNotificationReadStatus.user_id == user_id,
                UserNotificationReadStatus.announcement_id.in_(announcement_ids)
            )
        ).all()

        for status in read_statuses:
            read_status_map[status.announcement_id] = status
            # 记录已删除的通知ID
            if status.is_deleted:
                deleted_ids.add(status.announcement_id)

    # 构建通知列表
    notifications = []
    for announcement in all_announcements:
        # 跳过已删除的通知
        if announcement.id in deleted_ids:
            continue

        read_status = read_status_map.get(announcement.id)
        is_read = read_status.is_read if read_status else False

        # 如果只要未读的，跳过已读的
        if unread_only and is_read:
            continue

        notifications.append({
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "type": announcement.announcement_type or "info",
            "priority": announcement.priority,
            "is_read": is_read,
            "is_pinned": announcement.is_pinned,
            "publish_at": announcement.publish_at.isoformat() if announcement.publish_at else None,
            "expire_at": announcement.expire_at.isoformat() if announcement.expire_at else None,
            "read_at": read_status.read_at.isoformat() if read_status and read_status.read_at else None,
            "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
        })

    # 排序：置顶的在前，然后按发布时间倒序
    notifications.sort(key=lambda x: (not x["is_pinned"], x["publish_at"] or ""), reverse=True)

    # 分页
    total = len(notifications)
    start = (page - 1) * page_size
    end = start + page_size
    items = notifications[start:end]

    # 统计未读数量
    unread_count = sum(1 for n in notifications if not n["is_read"])

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "unread_count": unread_count
        },
        "message": "获取通知列表成功"
    }


@router.get("/unread-count")
def get_unread_count(
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取未读通知数量"""
    user_id = current_user.id

    # 获取用户注册时间
    user_created_at = current_user.created_at

    # 查询有效的系统公告 - 只显示用户注册后发布的通知
    all_announcements = db.query(SystemAnnouncement).filter(
        and_(
            SystemAnnouncement.is_published == True,
            SystemAnnouncement.publish_at <= datetime.utcnow(),
            SystemAnnouncement.publish_at >= user_created_at,  # 只显示用户注册后发布的通知
            or_(
                SystemAnnouncement.expire_at.is_(None),
                SystemAnnouncement.expire_at > datetime.utcnow()
            ),
            or_(
                SystemAnnouncement.target_audience == "all",
                SystemAnnouncement.target_audience == "user",
                SystemAnnouncement.created_by == user_id
            )
        )
    ).all()

    announcement_ids = [a.id for a in all_announcements]

    # 获取已删除的通知ID
    deleted_ids = set()
    # 获取已读的数量（排除已删除的）
    read_count = 0
    if announcement_ids:
        # 获取所有状态记录
        statuses = db.query(UserNotificationReadStatus).filter(
            and_(
                UserNotificationReadStatus.user_id == user_id,
                UserNotificationReadStatus.announcement_id.in_(announcement_ids)
            )
        ).all()

        for status in statuses:
            if status.is_deleted:
                deleted_ids.add(status.announcement_id)
            elif status.is_read:
                read_count += 1

    # 总数 = 所有公告 - 已删除的
    total_count = len(announcement_ids) - len(deleted_ids)
    # 未读数 = 总数 - 已读数
    unread_count = total_count - read_count

    return {
        "success": True,
        "data": {
            "unread_count": unread_count,
            "total_count": total_count
        },
        "message": "获取未读数量成功"
    }


@router.post("/{notification_id}/mark-read")
def mark_notification_as_read(
    notification_id: int,
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """标记通知为已读"""
    user_id = current_user.id
    
    # 检查通知是否存在
    announcement = db.query(SystemAnnouncement).filter(
        SystemAnnouncement.id == notification_id
    ).first()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 查找或创建已读状态
    read_status = db.query(UserNotificationReadStatus).filter(
        and_(
            UserNotificationReadStatus.user_id == user_id,
            UserNotificationReadStatus.announcement_id == notification_id
        )
    ).first()
    
    if read_status:
        if not read_status.is_read:
            read_status.is_read = True
            read_status.read_at = datetime.utcnow()
    else:
        read_status = UserNotificationReadStatus(
            user_id=user_id,
            announcement_id=notification_id,
            is_read=True,
            read_at=datetime.utcnow()
        )
        db.add(read_status)
    
    db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "标记已读成功"
    }


@router.post("/mark-all-read")
def mark_all_notifications_as_read(
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """标记所有通知为已读"""
    user_id = current_user.id

    # 获取用户注册时间
    user_created_at = current_user.created_at

    # 获取所有有效的公告 - 只显示用户注册后发布的通知
    all_announcements = db.query(SystemAnnouncement).filter(
        and_(
            SystemAnnouncement.is_published == True,
            SystemAnnouncement.publish_at <= datetime.utcnow(),
            SystemAnnouncement.publish_at >= user_created_at,  # 只显示用户注册后发布的通知
            or_(
                SystemAnnouncement.expire_at.is_(None),
                SystemAnnouncement.expire_at > datetime.utcnow()
            ),
            or_(
                SystemAnnouncement.target_audience == "all",
                SystemAnnouncement.target_audience == "user",
                SystemAnnouncement.created_by == user_id
            )
        )
    ).all()
    
    # 为每个公告创建或更新已读状态
    for announcement in all_announcements:
        read_status = db.query(UserNotificationReadStatus).filter(
            and_(
                UserNotificationReadStatus.user_id == user_id,
                UserNotificationReadStatus.announcement_id == announcement.id
            )
        ).first()
        
        if read_status:
            if not read_status.is_read:
                read_status.is_read = True
                read_status.read_at = datetime.utcnow()
                read_status.is_deleted = False
        else:
            read_status = UserNotificationReadStatus(
                user_id=user_id,
                announcement_id=announcement.id,
                is_read=True,
                read_at=datetime.utcnow()
            )
            db.add(read_status)
    
    db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "全部标记已读成功"
    }


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """删除通知（软删除）"""
    user_id = current_user.id
    
    # 检查通知是否存在
    announcement = db.query(SystemAnnouncement).filter(
        SystemAnnouncement.id == notification_id
    ).first()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 查找或创建已读状态，并标记为删除
    read_status = db.query(UserNotificationReadStatus).filter(
        and_(
            UserNotificationReadStatus.user_id == user_id,
            UserNotificationReadStatus.announcement_id == notification_id
        )
    ).first()
    
    if read_status:
        read_status.is_deleted = True
        read_status.deleted_at = datetime.utcnow()
    else:
        read_status = UserNotificationReadStatus(
            user_id=user_id,
            announcement_id=notification_id,
            is_deleted=True,
            deleted_at=datetime.utcnow()
        )
        db.add(read_status)
    
    db.commit()
    
    return {
        "success": True,
        "data": None,
        "message": "删除通知成功"
    }

