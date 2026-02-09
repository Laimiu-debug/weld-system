"""
简化的管理员管理端点，避免ORM字段访问问题
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.admin_deps import get_current_active_admin
from app.models.admin import Admin
from app.core.database import get_db

router = APIRouter()


@router.get("/users", response_model=Dict[str, Any])
async def get_users_admin_simple(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    membership_tier: Optional[str] = Query(None, description="会员等级筛选"),
    is_active: Optional[bool] = Query(None, description="用户状态筛选"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取所有用户列表（管理员专用）- 使用原始SQL查询
    """

    # 构建基础查询
    where_conditions = []
    params = {}

    # 搜索条件
    if search:
        where_conditions.append("(email ILIKE :search OR username ILIKE :search OR full_name ILIKE :search)")
        params['search'] = f"%{search}%"

    # 会员等级筛选
    if membership_tier:
        where_conditions.append("member_tier = :membership_tier")
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
            is_active, is_verified, is_superuser, is_admin,
            member_tier, membership_type, subscription_status,
            created_at, updated_at, last_login_at,
            wps_quota_used, pqr_quota_used, ppqr_quota_used, storage_quota_used
        FROM users
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :page_size OFFSET :offset
    """)

    users = db.execute(users_query, {**params, 'page_size': page_size, 'offset': offset}).fetchall()

    # 转换为响应格式
    user_items = []
    for user in users:
        # 安全获取会员等级相关数据
        tier = user[10] if user[10] else "free"  # member_tier
        membership_type = user[11] if user[11] else "personal"

        user_data = {
            "id": str(user[0]),
            "email": user[1],
            "username": user[2],
            "full_name": user[3] if user[3] else "",
            "phone": user[4],
            "company": user[5],
            "is_active": user[6],
            "is_verified": user[7] if user[7] else False,
            "is_admin": user[8] if user[8] else False,
            "membership_tier": tier,
            "membership_type": membership_type,
            "subscription_status": user[12] if user[12] else "inactive",
            "created_at": user[13].isoformat() if user[13] else None,
            "updated_at": user[14].isoformat() if user[14] else None,
            "last_login_at": user[15].isoformat() if user[15] else None,
            "quotas": {
                "wps_limit": _get_wps_limit(tier),
                "pqr_limit": _get_pqr_limit(tier),
                "ppqr_limit": _get_ppqr_limit(tier),
                "current_wps": user[16] if user[16] else 0,
                "current_pqr": user[17] if user[17] else 0,
                "current_ppqr": user[18] if user[18] else 0,
                "current_storage": user[19] if user[19] else 0,
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


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_detail_admin_simple(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取指定用户详细信息（管理员专用）- 使用原始SQL查询
    """
    try:
        # 验证用户ID格式
        int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )

    # 查询用户详情
    user_query = text("""
        SELECT
            id, email, username, full_name, phone, company,
            is_active, is_verified, is_superuser, is_admin,
            member_tier, membership_type, subscription_status,
            subscription_start_date, subscription_end_date, subscription_expires_at,
            auto_renewal, created_at, updated_at, last_login_at,
            wps_quota_used, pqr_quota_used, ppqr_quota_used, storage_quota_used,
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

    # 安全获取用户数据
    tier = user[10] if user[10] else "free"  # member_tier

    return {
        "success": True,
        "data": {
            "id": str(user[0]),
            "email": user[1],
            "username": user[2],
            "full_name": user[3] if user[3] else "",
            "phone": user[4],
            "company": user[5],
            "is_active": user[6],
            "is_verified": user[7] if user[7] else False,
            "is_admin": user[8] if user[8] else False,
            "membership_tier": tier,
            "membership_type": user[11] if user[11] else "personal",
            "subscription_status": user[12] if user[12] else "inactive",
            "subscription_start_date": user[13].isoformat() if user[13] else None,
            "subscription_end_date": user[14].isoformat() if user[14] else None,
            "subscription_expires_at": user[15].isoformat() if user[15] else None,
            "auto_renewal": user[16] if user[16] else False,
            "created_at": user[17].isoformat() if user[17] else None,
            "updated_at": user[18].isoformat() if user[18] else None,
            "last_login_at": user[19].isoformat() if user[19] else None,
            "last_login_ip": user[24] if user[24] else None,
            "quotas": {
                "wps_limit": _get_wps_limit(tier),
                "pqr_limit": _get_pqr_limit(tier),
                "ppqr_limit": _get_ppqr_limit(tier),
                "current_wps": user[20] if user[20] else 0,
                "current_pqr": user[21] if user[21] else 0,
                "current_ppqr": user[22] if user[22] else 0,
                "current_storage": user[23] if user[23] else 0,
            }
        }
    }


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


@router.post("/init-database")
async def init_database_columns(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    初始化数据库表结构 - 添加缺失的会员相关字段
    """
    try:
        # 检查当前表结构
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))

        current_columns = [row[0] for row in result.fetchall()]

        # 需要添加的字段
        required_columns = [
            ('member_tier', 'VARCHAR', "'free'"),
            ('membership_type', 'VARCHAR', "'personal'"),
            ('subscription_status', 'VARCHAR', "'inactive'"),
            ('subscription_start_date', 'TIMESTAMP', 'NULL'),
            ('subscription_end_date', 'TIMESTAMP', 'NULL'),
            ('subscription_expires_at', 'TIMESTAMP', 'NULL'),
            ('auto_renewal', 'BOOLEAN', 'FALSE'),
            ('wps_quota_used', 'INTEGER', '0'),
            ('pqr_quota_used', 'INTEGER', '0'),
            ('ppqr_quota_used', 'INTEGER', '0'),
            ('storage_quota_used', 'INTEGER', '0'),
            ('last_login_at', 'TIMESTAMP', 'NULL'),
            ('last_login_ip', 'VARCHAR', 'NULL'),
            ('is_admin', 'BOOLEAN', 'FALSE')
        ]

        # 添加缺失的字段
        added_columns = []
        for column_name, data_type, default_value in required_columns:
            if column_name not in current_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {data_type} DEFAULT {default_value}"
                    db.execute(text(sql))
                    added_columns.append(column_name)
                except Exception as e:
                    db.rollback()
                    return {
                        "success": False,
                        "message": f"添加字段 {column_name} 失败: {str(e)}"
                    }

        db.commit()

        return {
            "success": True,
            "message": f"数据库表结构初始化成功，添加了 {len(added_columns)} 个新字段",
            "data": {
                "added_columns": added_columns,
                "total_columns": len(current_columns) + len(added_columns)
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"数据库初始化失败: {str(e)}"
        }