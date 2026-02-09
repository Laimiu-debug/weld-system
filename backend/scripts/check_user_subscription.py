"""
检查用户订阅信息
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company

def check_user_subscription():
    """检查用户订阅信息"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("检查用户订阅信息")
        print("=" * 80)
        
        # 查找 testuser176070001@example.com
        user = db.query(User).filter(User.email == "testuser176070001@example.com").first()
        
        if not user:
            print("❌ 未找到用户 testuser176070001@example.com")
            return
        
        print(f"\n用户表信息:")
        print(f"  - 邮箱: {user.email}")
        print(f"  - 会员等级: {user.member_tier}")
        print(f"  - 订阅状态: {user.subscription_status}")
        print(f"  - 订阅开始日期 (subscription_start_date): {user.subscription_start_date}")
        print(f"  - 订阅结束日期 (subscription_end_date): {user.subscription_end_date}")
        print(f"  - 订阅到期时间 (subscription_expires_at): {user.subscription_expires_at}")
        print(f"  - 自动续费: {user.auto_renewal}")
        
        # 查找用户的企业
        company = db.query(Company).filter(Company.owner_id == user.id).first()
        
        if company:
            print(f"\n企业表信息:")
            print(f"  - 企业ID: {company.id}")
            print(f"  - 企业名称: {company.name}")
            print(f"  - 会员等级: {company.membership_tier}")
            print(f"  - 订阅状态: {company.subscription_status}")
            print(f"  - 订阅开始日期: {company.subscription_start_date}")
            print(f"  - 订阅结束日期: {company.subscription_end_date}")
            print(f"  - 自动续费: {company.auto_renewal}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_user_subscription()

