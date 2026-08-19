"""
初始化管理员门户的测试数据
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.core.security import get_password_hash
from app.core.bootstrap_secrets import require_admin_initial_password
from app.models.admin import Admin
from app.models.system_announcement import SystemAnnouncement
from app.models.system_log import SystemLog


def init_admin_data():
    """初始化管理员门户的测试数据"""

    # 创建数据库会话
    db = SessionLocal()

    try:
        print("开始初始化管理员门户数据...")

        # 1. 确保管理员用户存在
        admin_email = "Laimiu.new@gmail.com"
        admin_password = require_admin_initial_password()

        # 使用原始SQL查询来避免字段不存在的问题
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()

        if not result:
            print(f"创建管理员用户: {admin_email}")
            # 使用原始SQL插入用户
            db.execute(text("""
                INSERT INTO users (email, username, full_name, hashed_password, is_active, is_verified, is_superuser,
                                 member_tier, membership_type, subscription_status, created_at, updated_at)
                VALUES (:email, :username, :full_name, :hashed_password, :is_active, :is_verified, :is_superuser,
                        :member_tier, :membership_type, :subscription_status, :created_at, :updated_at)
                RETURNING id
            """), {
                "email": admin_email,
                "username": "admin",
                "full_name": "系统管理员",
                "hashed_password": get_password_hash(admin_password),
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "member_tier": "enterprise_pro_max",
                "membership_type": "enterprise",
                "subscription_status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()
        else:
            print(f"管理员用户已存在: {admin_email}")
            # 更新管理员信息
            db.execute(text("""
                UPDATE users SET
                    is_active = :is_active,
                    is_verified = :is_verified,
                    is_superuser = :is_superuser,
                    member_tier = :member_tier,
                    membership_type = :membership_type,
                    subscription_status = :subscription_status,
                    updated_at = :updated_at
                WHERE email = :email
            """), {
                "email": admin_email,
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "member_tier": "enterprise_pro_max",
                "membership_type": "enterprise",
                "subscription_status": "active",
                "updated_at": datetime.utcnow()
            })

        user_id = result[0]

        # 2. 确保管理员记录存在
        admin_record = db.query(Admin).filter(Admin.user_id == user_id).first()
        if not admin_record:
            print("创建管理员记录...")
            admin_record = Admin(
                user_id=user_id,
                admin_level="super_admin",
                is_active=True,
                permissions={
                    "user_management": True,
                    "system_admin": True,
                    "membership_management": True,
                    "content_management": True,
                    "analytics": True
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin_record)
        else:
            print("管理员记录已存在，更新权限...")
            admin_record.is_active = True
            admin_record.admin_level = "super_admin"
            admin_record.permissions = {
                "user_management": True,
                "system_admin": True,
                "membership_management": True,
                "content_management": True,
                "analytics": True
            }
            admin_record.updated_at = datetime.utcnow()

        # 3. 创建一些测试用户
        test_users_data = [
            {
                "email": "test1@example.com",
                "username": "testuser1",
                "full_name": "测试用户1",
                "member_tier": "personal_pro",
                "membership_type": "personal",
                "subscription_status": "active"
            },
            {
                "email": "test2@example.com",
                "username": "testuser2",
                "full_name": "测试用户2",
                "member_tier": "personal_advanced",
                "membership_type": "personal",
                "subscription_status": "active"
            },
            {
                "email": "test3@example.com",
                "username": "testuser3",
                "full_name": "测试用户3",
                "member_tier": "free",
                "membership_type": "personal",
                "subscription_status": "inactive"
            },
            {
                "email": "enterprise@example.com",
                "username": "enterprise_user",
                "full_name": "企业用户",
                "member_tier": "enterprise",
                "membership_type": "enterprise",
                "subscription_status": "active"
            }
        ]

        for user_data in test_users_data:
            existing_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data["email"]}).fetchone()
            if not existing_user:
                print(f"创建测试用户: {user_data['email']}")
                # 使用原始SQL插入测试用户
                db.execute(text("""
                    INSERT INTO users (email, username, full_name, hashed_password, is_active, is_verified,
                                     member_tier, membership_type, subscription_status, created_at, last_login_at,
                                     wps_quota_used, pqr_quota_used, ppqr_quota_used, storage_quota_used)
                    VALUES (:email, :username, :full_name, :hashed_password, :is_active, :is_verified,
                            :member_tier, :membership_type, :subscription_status, :created_at, :last_login_at,
                            :wps_quota_used, :pqr_quota_used, :ppqr_quota_used, :storage_quota_used)
                """), {
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data["full_name"],
                    "hashed_password": get_password_hash("password123"),
                    "is_active": True,
                    "is_verified": True,
                    "member_tier": user_data["member_tier"],
                    "membership_type": user_data["membership_type"],
                    "subscription_status": user_data["subscription_status"],
                    "created_at": datetime.utcnow() - timedelta(days=30),  # 30天前创建
                    "last_login_at": datetime.utcnow() - timedelta(days=1),  # 1天前登录
                    "wps_quota_used": 5,
                    "pqr_quota_used": 3,
                    "ppqr_quota_used": 2,
                    "storage_quota_used": 100
                })

        # 4. 创建系统公告
        announcements_data = [
            {
                "title": "欢迎使用焊接系统管理门户",
                "content": "这是一个功能强大的管理门户，提供用户管理、系统监控、会员管理等功能。请熟悉各项功能并合理使用管理员权限。",
                "type": "welcome",
                "priority": "high",
                "is_active": True,
                "target_audience": "all"
            },
            {
                "title": "系统维护通知",
                "content": "系统将于本周六凌晨2:00-4:00进行例行维护，期间服务可能暂时中断。请提前做好相关安排。",
                "type": "maintenance",
                "priority": "medium",
                "is_active": True,
                "target_audience": "all"
            },
            {
                "title": "新功能上线通知",
                "content": "新增会员等级升级功能和详细的统计分析报表，欢迎各位用户体验并提供反馈意见。",
                "type": "feature",
                "priority": "low",
                "is_active": True,
                "target_audience": "all"
            }
        ]

        for ann_data in announcements_data:
            existing_ann = db.query(SystemAnnouncement).filter(
                SystemAnnouncement.title == ann_data["title"]
            ).first()
            if not existing_ann:
                print(f"创建系统公告: {ann_data['title']}")
                announcement = SystemAnnouncement(
                    title=ann_data["title"],
                    content=ann_data["content"],
                    type=ann_data["type"],
                    priority=ann_data["priority"],
                    is_active=ann_data["is_active"],
                    target_audience=ann_data["target_audience"],
                    created_by=admin_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(announcement)

        # 5. 创建系统日志
        log_entries_data = [
            {
                "action": "用户登录",
                "details": "管理员登录系统",
                "ip_address": "192.168.1.100"
            },
            {
                "action": "查看用户列表",
                "details": "管理员查看了系统用户列表",
                "ip_address": "192.168.1.100"
            },
            {
                "action": "系统监控",
                "details": "检查了系统运行状态",
                "ip_address": "192.168.1.100"
            },
            {
                "action": "发布公告",
                "details": "发布了新的系统公告",
                "ip_address": "192.168.1.100"
            }
        ]

        for log_data in log_entries_data:
            log_entry = SystemLog(
                action=log_data["action"],
                details=log_data["details"],
                ip_address=log_data["ip_address"],
                user_id=admin_user.id,
                created_at=datetime.utcnow() - timedelta(hours=len(log_entries_data))
            )
            db.add(log_entry)

        # 提交所有更改
        db.commit()

        print("✅ 管理员门户数据初始化完成！")
        print(f"✅ 管理员账号: {admin_email}")
        print(f"✅ 管理员密码: {admin_password}")
        print("✅ 测试用户密码: password123")
        print("✅ 系统已准备就绪，可以开始使用管理员门户！")

        return True

    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = init_admin_data()
    if success:
        print("\n🎉 初始化成功！现在可以启动后端服务并测试管理员门户了。")
    else:
        print("\n💥 初始化失败！请检查错误信息并重试。")
