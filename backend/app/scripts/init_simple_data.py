"""
简化版本的管理员门户数据初始化脚本
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


def init_simple_data():
    """初始化基础的管理员门户数据"""

    # 创建数据库会话
    db = SessionLocal()

    try:
        print("开始初始化基础管理员数据...")

        # 1. 检查现有数据库表结构
        print("检查数据库表结构...")
        columns_result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)).fetchall()

        existing_columns = [col[0] for col in columns_result]
        print(f"现有用户表字段: {existing_columns}")

        # 2. 确保管理员用户存在（只使用基础字段）
        admin_email = "Laimiu.new@gmail.com"
        admin_password = require_admin_initial_password()

        # 检查管理员用户是否存在
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()

        if not result:
            print(f"创建管理员用户: {admin_email}")
            # 只使用基础字段
            insert_fields = ["email", "username", "full_name", "hashed_password", "is_active", "is_verified", "is_superuser", "created_at", "updated_at"]
            insert_values = {
                "email": admin_email,
                "username": "admin",
                "full_name": "系统管理员",
                "hashed_password": get_password_hash(admin_password),
                "is_active": True,
                "is_verified": True,
                "is_superuser": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # 检查是否有member_tier字段
            if "member_tier" in existing_columns:
                insert_fields.append("member_tier")
                insert_values["member_tier"] = "enterprise_pro_max"

            # 检查是否有membership_type字段
            if "membership_type" in existing_columns:
                insert_fields.append("membership_type")
                insert_values["membership_type"] = "enterprise"

            # 检查是否有subscription_status字段
            if "subscription_status" in existing_columns:
                insert_fields.append("subscription_status")
                insert_values["subscription_status"] = "active"

            # 构建SQL插入语句
            fields_str = ", ".join(insert_fields)
            values_str = ", ".join([f":{field}" for field in insert_fields])

            insert_sql = f"""
                INSERT INTO users ({fields_str})
                VALUES ({values_str})
                RETURNING id
            """

            db.execute(text(insert_sql), insert_values)
            result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()
        else:
            print(f"管理员用户已存在: {admin_email}")

        user_id = result[0]

        # 3. 确保管理员记录存在
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

        # 4. 创建一些基础测试用户
        test_users_data = [
            {
                "email": "test1@example.com",
                "username": "testuser1",
                "full_name": "测试用户1"
            },
            {
                "email": "test2@example.com",
                "username": "testuser2",
                "full_name": "测试用户2"
            },
            {
                "email": "test3@example.com",
                "username": "testuser3",
                "full_name": "测试用户3"
            }
        ]

        for user_data in test_users_data:
            existing_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data["email"]}).fetchone()
            if not existing_user:
                print(f"创建测试用户: {user_data['email']}")

                # 基础字段
                insert_fields = ["email", "username", "full_name", "hashed_password", "is_active", "is_verified", "created_at"]
                insert_values = {
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data["full_name"],
                    "hashed_password": get_password_hash("password123"),
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow() - timedelta(days=30)
                }

                # 可选字段
                optional_fields = ["member_tier", "membership_type", "subscription_status", "last_login_at"]
                optional_values = {
                    "member_tier": "free",
                    "membership_type": "personal",
                    "subscription_status": "inactive",
                    "last_login_at": datetime.utcnow() - timedelta(days=1)
                }

                for field in optional_fields:
                    if field in existing_columns:
                        insert_fields.append(field)
                        insert_values[field] = optional_values[field]

                # 构建SQL插入语句
                fields_str = ", ".join(insert_fields)
                values_str = ", ".join([f":{field}" for field in insert_fields])

                insert_sql = f"""
                    INSERT INTO users ({fields_str})
                    VALUES ({values_str})
                """

                db.execute(text(insert_sql), insert_values)

        # 5. 创建系统日志
        # 先检查system_logs表是否存在
        tables_result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'system_logs'
        """)).fetchone()

        if tables_result:
            print("创建系统日志...")
            log_entries_data = [
                {
                    "action": "用户登录",
                    "details": "管理员登录系统"
                },
                {
                    "action": "查看用户列表",
                    "details": "管理员查看了系统用户列表"
                },
                {
                    "action": "系统监控",
                    "details": "检查了系统运行状态"
                }
            ]

            for log_data in log_entries_data:
                log_entry = text("""
                    INSERT INTO system_logs (action, details, user_id, created_at)
                    VALUES (:action, :details, :user_id, :created_at)
                """)
                db.execute(log_entry, {
                    "action": log_data["action"],
                    "details": log_data["details"],
                    "user_id": user_id,
                    "created_at": datetime.utcnow() - timedelta(hours=1)
                })

        # 提交所有更改
        db.commit()

        print("✅ 基础管理员数据初始化完成！")
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
    success = init_simple_data()
    if success:
        print("\n🎉 初始化成功！现在可以启动后端服务并测试管理员门户了。")
    else:
        print("\n💥 初始化失败！请检查错误信息并重试。")
