"""
最小化管理员门户数据初始化脚本 - 只创建必要的用户数据
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


def init_minimal_data():
    """初始化最小的管理员门户数据"""

    # 创建数据库会话
    db = SessionLocal()

    try:
        print("开始初始化最小管理员数据...")

        # 1. 检查现有数据库表结构
        print("检查数据库表结构...")
        users_columns_result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)).fetchall()

        users_columns = [col[0] for col in users_columns_result]
        print(f"现有用户表字段: {users_columns}")

        # 2. 确保管理员用户存在
        admin_email = "Laimiu.new@gmail.com"
        admin_password = "ghzzz123"

        # 检查管理员用户是否存在
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}).fetchone()

        if not result:
            print(f"创建管理员用户: {admin_email}")

            # 构建基础插入字段
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

            # 如果有member_tier字段，添加它
            if "member_tier" in users_columns:
                insert_fields.append("member_tier")
                insert_values["member_tier"] = "enterprise_pro_max"

            # 构建SQL插入语句
            fields_str = ", ".join(insert_fields)
            values_str = ", ".join([f":{field}" for field in insert_fields])

            insert_sql = f"""
                INSERT INTO users ({fields_str})
                VALUES ({values_str})
            """

            db.execute(text(insert_sql), insert_values)
            print("管理员用户创建成功")
        else:
            print(f"管理员用户已存在: {admin_email}")

        # 3. 创建一些测试用户
        test_users_data = [
            {
                "email": "test1@example.com",
                "username": "testuser1",
                "full_name": "测试用户1",
                "member_tier": "personal_pro"
            },
            {
                "email": "test2@example.com",
                "username": "testuser2",
                "full_name": "测试用户2",
                "member_tier": "personal_advanced"
            },
            {
                "email": "test3@example.com",
                "username": "testuser3",
                "full_name": "测试用户3",
                "member_tier": "free"
            },
            {
                "email": "enterprise@example.com",
                "username": "enterprise_user",
                "full_name": "企业用户",
                "member_tier": "enterprise"
            }
        ]

        created_count = 0
        for user_data in test_users_data:
            existing_user = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data["email"]}).fetchone()
            if not existing_user:
                print(f"创建测试用户: {user_data['email']}")

                # 基础字段
                insert_fields = ["email", "username", "full_name", "hashed_password", "is_active", "is_verified", "created_at", "updated_at"]
                insert_values = {
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data["full_name"],
                    "hashed_password": get_password_hash("password123"),
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow() - timedelta(days=30),
                    "updated_at": datetime.utcnow()
                }

                # 如果有member_tier字段
                if "member_tier" in users_columns:
                    insert_fields.append("member_tier")
                    insert_values["member_tier"] = user_data["member_tier"]

                # 构建SQL插入语句
                fields_str = ", ".join(insert_fields)
                values_str = ", ".join([f":{field}" for field in insert_fields])

                insert_sql = f"""
                    INSERT INTO users ({fields_str})
                    VALUES ({values_str})
                """

                db.execute(text(insert_sql), insert_values)
                created_count += 1

        print(f"创建了 {created_count} 个测试用户")

        # 4. 提交所有更改
        db.commit()

        print("最小管理员数据初始化完成！")
        print(f"管理员账号: {admin_email}")
        print(f"管理员密码: {admin_password}")
        print("测试用户密码: password123")
        print("系统已准备就绪，可以开始使用管理员门户！")

        return True

    except Exception as e:
        print(f"初始化失败: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = init_minimal_data()
    if success:
        print("\n初始化成功！现在可以启动后端服务并测试管理员门户了。")
    else:
        print("\n初始化失败！请检查错误信息并重试。")