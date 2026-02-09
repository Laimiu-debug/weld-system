"""
检查数据库中的用户
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    """检查用户"""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        print(f"\n找到 {len(users)} 个用户:\n")
        print("=" * 80)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  用户名: {user.username if hasattr(user, 'username') else 'N/A'}")
            print(f"  激活: {user.is_active}")
            print(f"  超级用户: {user.is_superuser}")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users()

