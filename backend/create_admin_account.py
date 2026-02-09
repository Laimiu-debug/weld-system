
import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.admin import Admin
from app.core.security import get_password_hash
from datetime import datetime

def create_admin():
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(Admin).filter(Admin.email == "Laimiu.new@gmail.com").first()
        
        if existing:
            print(f"管理员已存在，更新密码...")
            existing.hashed_password = get_password_hash("ghzzz123")
            existing.is_active = True
            existing.is_super_admin = True
            existing.admin_level = "super_admin"
            existing.updated_at = datetime.utcnow()
            db.commit()
            print(f"✅ 管理员账户已更新")
        else:
            print(f"创建新管理员账户...")
            admin = Admin(
                email="Laimiu.new@gmail.com",
                username="Laimiu.new@gmail.com",
                full_name="超级管理员",
                hashed_password=get_password_hash("ghzzz123"),
                is_active=True,
                is_super_admin=True,
                admin_level="super_admin",
                permissions={
                    "user_management": True,
                    "system_management": True,
                    "membership_management": True,
                    "announcement_management": True,
                    "log_management": True,
                    "config_management": True
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"✅ 管理员账户已创建")
        
        # 验证
        admin = db.query(Admin).filter(Admin.email == "Laimiu.new@gmail.com").first()
        if admin:
            print(f"\n验证信息:")
            print(f"  ID: {admin.id}")
            print(f"  邮箱: {admin.email}")
            print(f"  用户名: {admin.username}")
            print(f"  全名: {admin.full_name}")
            print(f"  激活状态: {admin.is_active}")
            print(f"  超级管理员: {admin.is_super_admin}")
            print(f"  管理员级别: {admin.admin_level}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    exit(create_admin())
