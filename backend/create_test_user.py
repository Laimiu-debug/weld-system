
import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from datetime import datetime

def create_test_user():
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(User).filter(User.email == "test@example.com").first()
        
        if existing:
            print(f"测试用户已存在，更新密码...")
            existing.hashed_password = get_password_hash("test123456")
            existing.is_active = True
            existing.is_verified = True
            existing.updated_at = datetime.utcnow()
            db.commit()
            print(f"✅ 测试用户已更新")
        else:
            print(f"创建新测试用户...")
            user = User(
                email="test@example.com",
                username="testuser",
                full_name="测试用户",
                hashed_password=get_password_hash("test123456"),
                is_active=True,
                is_verified=True,
                is_superuser=False,
                member_tier="free",
                membership_type="personal",
                subscription_status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ 测试用户已创建")
        
        # 验证
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            print(f"\n验证信息:")
            print(f"  ID: {user.id}")
            print(f"  邮箱: {user.email}")
            print(f"  用户名: {user.username}")
            print(f"  激活状态: {user.is_active}")
            print(f"  验证状态: {user.is_verified}")
        
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
    exit(create_test_user())
