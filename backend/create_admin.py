"""
创建管理员用户脚本
"""
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin_user():
    """创建管理员用户"""

    # 确保数据库表存在
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)

    # 获取数据库会话
    db = next(get_db())

    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(User.email == "Laimiu.new@gmail.com").first()
        if existing_admin:
            print("管理员用户已存在")
            print(f"邮箱: {existing_admin.email}")
            print(f"用户名: {existing_admin.username}")
            print(f"是否管理员: {existing_admin.is_superuser}")
            print(f"是否激活: {existing_admin.is_active}")
            if not existing_admin.is_superuser:
                # 设置为管理员
                existing_admin.is_superuser = True
                existing_admin.member_tier = "enterprise"
                existing_admin.is_verified = True
                db.commit()
                print("已将用户设置为管理员")
            return existing_admin

        # 创建管理员用户
        admin_user = User(
            email="Laimiu.new@gmail.com",
            username="admin",
            full_name="系统管理员",
            hashed_password=get_password_hash("ghzzz123"),  # 使用你的密码
            is_active=True,
            is_verified=True,
            is_superuser=True,  # 设置为超级管理员
            member_tier="enterprise",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # 保存到数据库
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("管理员用户创建成功！")
        print(f"邮箱: {admin_user.email}")
        print(f"用户名: {admin_user.username}")
        print(f"密码: ghzzz123")
        print(f"是否管理员: {admin_user.is_superuser}")
        print(f"会员等级: {admin_user.member_tier}")

        return admin_user

    except Exception as e:
        print(f"创建管理员用户失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())