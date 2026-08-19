"""
完整的管理员管理API端点，提供真实的后端功能
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_

from app.api.admin_deps import get_current_active_admin
from app.models.admin import Admin
from app.core.database import get_db

router = APIRouter()


def get_user_statistics(db: Session) -> Dict[str, Any]:
    """获取用户统计数据"""
    try:
        # 总用户数
        total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0

        # 今日新增用户
        today = datetime.now().date()
        today_users = db.execute(
            text("SELECT COUNT(*) FROM users WHERE DATE(created_at) = :today"),
            {"today": today}
        ).scalar() or 0

        # 活跃用户数（最近30天登录）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users = db.execute(
            text("SELECT COUNT(*) FROM users WHERE last_login_at > :date"),
            {"date": thirty_days_ago}
        ).scalar() or 0

        # 各会员等级用户数
        tier_stats = db.execute(text("""
            SELECT
                COALESCE(member_tier, 'free') as tier,
                COUNT(*) as count
            FROM users
            GROUP BY COALESCE(member_tier, 'free')
        """)).fetchall()

        membership_stats = {row[0]: row[1] for row in tier_stats}

        return {
            "total_users": total_users,
            "today_users": today_users,
            "active_users": active_users,
            "membership_stats": membership_stats
        }
    except Exception as e:
        return {
            "total_users": 0,
            "today_users": 0,
            "active_users": 0,
            "membership_stats": {"free": 0}
        }


def get_system_statistics(db: Session) -> Dict[str, Any]:
    """获取系统统计数据"""
    try:
        # WPS和PQR文件统计
        wps_count = db.execute(text("SELECT COUNT(*) FROM wps")).scalar() or 0
        pqr_count = db.execute(text("SELECT COUNT(*) FROM pqr")).scalar() or 0

        # 系统日志统计（今日）
        today = datetime.now().date()
        system_logs_today = db.execute(
            text("SELECT COUNT(*) FROM system_logs WHERE DATE(created_at) = :today"),
            {"today": today}
        ).scalar() or 0

        # 存储使用情况（模拟数据）
        storage_used = db.execute(text("""
            SELECT SUM(storage_quota_used) FROM users WHERE storage_quota_used IS NOT NULL
        """)).scalar() or 0

        return {
            "wps_files": wps_count,
            "pqr_files": pqr_count,
            "system_logs_today": system_logs_today,
            "storage_used_mb": storage_used,
            "storage_total_mb": 10240  # 假设总存储10GB
        }
    except Exception as e:
        return {
            "wps_files": 0,
            "pqr_files": 0,
            "system_logs_today": 0,
            "storage_used_mb": 0,
            "storage_total_mb": 10240
        }


@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取仪表板数据"""
    try:
        user_stats = get_user_statistics(db)
        system_stats = get_system_statistics(db)

        # 最近的系统活动
        recent_activities = db.execute(text("""
            SELECT
                al.action,
                al.details,
                al.ip_address,
                al.created_at,
                u.username as user_name
            FROM system_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 10
        """)).fetchall()

        activities = []
        for activity in recent_activities:
            activities.append({
                "action": activity[0],
                "details": activity[1],
                "ip_address": activity[2],
                "created_at": activity[3].isoformat() if activity[3] else None,
                "user_name": activity[4] or "系统"
            })

        # 最新用户注册
        new_users = db.execute(text("""
            SELECT id, username, email, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 5
        """)).fetchall()

        latest_users = []
        for user in new_users:
            latest_users.append({
                "id": str(user[0]),
                "username": user[1] or "未知用户",
                "email": user[2],
                "created_at": user[3].isoformat() if user[3] else None
            })

        return {
            "success": True,
            "data": {
                "user_statistics": user_stats,
                "system_statistics": system_stats,
                "recent_activities": activities,
                "latest_users": latest_users
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取仪表板数据失败: {str(e)}"
        }


@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    membership_tier: Optional[str] = Query(None, description="会员等级筛选"),
    is_active: Optional[bool] = Query(None, description="用户状态筛选"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取用户列表"""
    try:
        # 构建基础查询
        where_conditions = []
        params = {}

        # 搜索条件
        if search:
            where_conditions.append("(email ILIKE :search OR username ILIKE :search OR full_name ILIKE :search)")
            params['search'] = f"%{search}%"

        # 会员等级筛选
        if membership_tier:
            where_conditions.append("COALESCE(member_tier, 'free') = :membership_tier")
            params['membership_tier'] = membership_tier

        # 用户状态筛选
        if is_active is not None:
            where_conditions.append("is_active = :is_active")
            params['is_active'] = is_active

        # 构建完整的SQL查询
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 获取总数
        count_query = text(f"SELECT COUNT(*) FROM users WHERE {where_clause}")
        total = db.execute(count_query, params).scalar() or 0

        # 获取用户数据
        offset = (page - 1) * page_size
        users_query = text(f"""
            SELECT
                id, email, username, full_name, phone, company,
                is_active, is_verified, is_superuser,
                COALESCE(member_tier, 'free') as member_tier,
                COALESCE(membership_type, 'personal') as membership_type,
                COALESCE(subscription_status, 'inactive') as subscription_status,
                created_at, updated_at, last_login_at,
                COALESCE(wps_quota_used, 0) as wps_quota_used,
                COALESCE(pqr_quota_used, 0) as pqr_quota_used,
                COALESCE(ppqr_quota_used, 0) as ppqr_quota_used,
                COALESCE(storage_quota_used, 0) as storage_quota_used
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :page_size OFFSET :offset
        """)

        users = db.execute(users_query, {**params, 'page_size': page_size, 'offset': offset}).fetchall()

        # 转换为响应格式
        user_items = []
        for user in users:
            tier = user[9] if user[9] else "free"
            membership_type = user[10] if user[10] else "personal"

            user_data = {
                "id": str(user[0]),
                "email": user[1],
                "username": user[2] or "未知用户",
                "full_name": user[3] if user[3] else "",
                "phone": user[4] if user[4] else "",
                "company": user[5] if user[5] else "",
                "is_active": user[6],
                "is_verified": user[7] if user[7] else False,
                "is_superuser": user[8] if user[8] else False,
                "membership_tier": tier,
                "membership_type": membership_type,
                "subscription_status": user[11] if user[11] else "inactive",
                "created_at": user[12].isoformat() if user[12] else None,
                "updated_at": user[13].isoformat() if user[13] else None,
                "last_login_at": user[14].isoformat() if user[14] else None,
                "quotas": {
                    "wps_limit": _get_wps_limit(tier),
                    "pqr_limit": _get_pqr_limit(tier),
                    "ppqr_limit": _get_ppqr_limit(tier),
                    "current_wps": user[15],
                    "current_pqr": user[16],
                    "current_ppqr": user[17],
                    "current_storage": user[18],
                }
            }
            user_items.append(user_data)

        return {
            "success": True,
            "data": {
                "items": user_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取用户列表失败: {str(e)}"
        }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取用户详情"""
    try:
        # 验证用户ID格式
        int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )

    try:
        # 查询用户详情
        user_query = text("""
            SELECT
                id, email, username, full_name, phone, company,
                is_active, is_verified, is_superuser,
                COALESCE(member_tier, 'free') as member_tier,
                COALESCE(membership_type, 'personal') as membership_type,
                COALESCE(subscription_status, 'inactive') as subscription_status,
                subscription_start_date, subscription_end_date, subscription_expires_at,
                auto_renewal, created_at, updated_at, last_login_at,
                COALESCE(wps_quota_used, 0) as wps_quota_used,
                COALESCE(pqr_quota_used, 0) as pqr_quota_used,
                COALESCE(ppqr_quota_used, 0) as ppqr_quota_used,
                COALESCE(storage_quota_used, 0) as storage_quota_used,
                last_login_ip
            FROM users
            WHERE id = :user_id
        """)

        user = db.execute(user_query, {"user_id": user_id}).fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        tier = user[9] if user[9] else "free"

        return {
            "success": True,
            "data": {
                "id": str(user[0]),
                "email": user[1],
                "username": user[2] or "未知用户",
                "full_name": user[3] if user[3] else "",
                "phone": user[4] if user[4] else "",
                "company": user[5] if user[5] else "",
                "is_active": user[6],
                "is_verified": user[7] if user[7] else False,
                "is_superuser": user[8] if user[8] else False,
                "membership_tier": tier,
                "membership_type": user[10] if user[10] else "personal",
                "subscription_status": user[11] if user[11] else "inactive",
                "subscription_start_date": user[12].isoformat() if user[12] else None,
                "subscription_end_date": user[13].isoformat() if user[13] else None,
                "subscription_expires_at": user[14].isoformat() if user[14] else None,
                "auto_renewal": user[15] if user[15] else False,
                "created_at": user[16].isoformat() if user[16] else None,
                "updated_at": user[17].isoformat() if user[17] else None,
                "last_login_at": user[18].isoformat() if user[18] else None,
                "last_login_ip": user[23] if user[23] else None,
                "quotas": {
                    "wps_limit": _get_wps_limit(tier),
                    "pqr_limit": _get_pqr_limit(tier),
                    "ppqr_limit": _get_ppqr_limit(tier),
                    "current_wps": user[19],
                    "current_pqr": user[20],
                    "current_ppqr": user[21],
                    "current_storage": user[22],
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"获取用户详情失败: {str(e)}"
        }


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """更新用户信息"""
    try:
        # 验证用户ID格式
        int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )

    try:
        # 检查用户是否存在
        user_exists = db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 构建更新字段
        update_fields = []
        params = {"user_id": user_id}

        if "is_active" in user_data:
            update_fields.append("is_active = :is_active")
            params["is_active"] = user_data["is_active"]

        if "is_verified" in user_data:
            update_fields.append("is_verified = :is_verified")
            params["is_verified"] = user_data["is_verified"]

        if "member_tier" in user_data:
            update_fields.append("member_tier = :member_tier")
            params["member_tier"] = user_data["member_tier"]

        if "subscription_status" in user_data:
            update_fields.append("subscription_status = :subscription_status")
            params["subscription_status"] = user_data["subscription_status"]

        if "full_name" in user_data:
            update_fields.append("full_name = :full_name")
            params["full_name"] = user_data["full_name"]

        if "phone" in user_data:
            update_fields.append("phone = :phone")
            params["phone"] = user_data["phone"]

        if "company" in user_data:
            update_fields.append("company = :company")
            params["company"] = user_data["company"]

        if update_fields:
            update_fields.append("updated_at = :updated_at")
            params["updated_at"] = datetime.utcnow()

            sql = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = :user_id
            """

            db.execute(text(sql), params)
            db.commit()

        return {
            "success": True,
            "message": "用户信息更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"更新用户信息失败: {str(e)}"
        }


@router.get("/system-stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取系统统计数据"""
    try:
        user_stats = get_user_statistics(db)
        system_stats = get_system_statistics(db)

        # 会员等级分布
        tier_distribution = user_stats.get("membership_stats", {})

        # 最近7天用户注册趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_registrations = []

        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            count = db.execute(
                text("SELECT COUNT(*) FROM users WHERE DATE(created_at) = :date"),
                {"date": date}
            ).scalar() or 0
            daily_registrations.append({
                "date": date.isoformat(),
                "count": count
            })

        daily_registrations.reverse()  # 按时间正序

        return {
            "success": True,
            "data": {
                "user_stats": user_stats,
                "system_stats": system_stats,
                "tier_distribution": tier_distribution,
                "daily_registrations": daily_registrations
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取系统统计数据失败: {str(e)}"
        }


@router.get("/system-logs")
def get_system_logs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取系统日志"""
    try:
        # 构建基础查询
        where_conditions = []
        params = {}

        if action:
            where_conditions.append("action ILIKE :action")
            params['action'] = f"%{action}%"

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 获取总数
        count_query = text(f"SELECT COUNT(*) FROM system_logs WHERE {where_clause}")
        total = db.execute(count_query, params).scalar() or 0

        # 获取日志数据
        offset = (page - 1) * page_size
        logs_query = text(f"""
            SELECT
                sl.id, sl.action, sl.details, sl.ip_address, sl.created_at,
                u.username as user_name, u.email as user_email
            FROM system_logs sl
            LEFT JOIN users u ON sl.user_id = u.id
            WHERE {where_clause}
            ORDER BY sl.created_at DESC
            LIMIT :page_size OFFSET :offset
        """)

        logs = db.execute(logs_query, {**params, 'page_size': page_size, 'offset': offset}).fetchall()

        # 转换为响应格式
        log_items = []
        for log in logs:
            log_items.append({
                "id": str(log[0]),
                "action": log[1],
                "details": log[2] if log[2] else "",
                "ip_address": log[3] if log[3] else "",
                "created_at": log[4].isoformat() if log[4] else None,
                "user_name": log[5] if log[5] else "系统",
                "user_email": log[6] if log[6] else ""
            })

        return {
            "success": True,
            "data": {
                "items": log_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取系统日志失败: {str(e)}"
        }


@router.post("/users/{user_id}/reset-quota")
def reset_user_quota(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """重置用户配额"""
    try:
        # 验证用户ID格式
        int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )

    try:
        # 检查用户是否存在
        user_exists = db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 重置配额
        db.execute(text("""
            UPDATE users
            SET wps_quota_used = 0,
                pqr_quota_used = 0,
                ppqr_quota_used = 0,
                storage_quota_used = 0,
                updated_at = :updated_at
            WHERE id = :user_id
        """), {"user_id": user_id, "updated_at": datetime.utcnow()})

        # 记录操作日志
        db.execute(text("""
            INSERT INTO system_logs (action, details, user_id, ip_address, created_at)
            VALUES (:action, :details, :admin_id, :ip_address, :created_at)
        """), {
            "action": "重置用户配额",
            "details": f"管理员重置了用户 {user_id} 的配额",
            "admin_id": current_admin.user_id,
            "ip_address": "127.0.0.1",  # 可以从请求中获取真实IP
            "created_at": datetime.utcnow()
        })

        db.commit()

        return {
            "success": True,
            "message": "用户配额重置成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"重置用户配额失败: {str(e)}"
        }


# 辅助函数
def _get_wps_limit(tier: str) -> int:
    """根据会员等级获取WPS限制"""
    limits = {
        "free": 10,
        "personal_pro": 30,
        "personal_advanced": 50,
        "personal_flagship": 100,
        "enterprise": 200,
        "enterprise_pro": 400,
        "enterprise_pro_max": 500
    }
    return limits.get(tier, 10)


def _get_pqr_limit(tier: str) -> int:
    """根据会员等级获取PQR限制"""
    limits = {
        "free": 10,
        "personal_pro": 30,
        "personal_advanced": 50,
        "personal_flagship": 100,
        "enterprise": 200,
        "enterprise_pro": 400,
        "enterprise_pro_max": 500
    }
    return limits.get(tier, 10)


def _get_ppqr_limit(tier: str) -> int:
    """根据会员等级获取pPQR限制"""
    limits = {
        "free": 0,
        "personal_pro": 30,
        "personal_advanced": 50,
        "personal_flagship": 100,
        "enterprise": 200,
        "enterprise_pro": 400,
        "enterprise_pro_max": 500
    }
    return limits.get(tier, 0)