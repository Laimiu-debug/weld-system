"""
同步订阅到期时间字段
将 subscription_expires_at 同步到 subscription_end_date
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from datetime import datetime

def sync_subscription_dates():
    """同步订阅到期时间字段"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("同步订阅到期时间字段")
        print("=" * 80)
        
        # 查找所有有 subscription_expires_at 但与 subscription_end_date 不一致的用户
        users = db.query(User).filter(User.subscription_expires_at.isnot(None)).all()
        
        print(f"\n找到 {len(users)} 个有 subscription_expires_at 的用户")
        
        updated_count = 0
        
        for user in users:
            needs_update = False
            
            # 检查两个字段是否一致
            if user.subscription_expires_at and user.subscription_end_date:
                expires_at_date = user.subscription_expires_at.date()
                end_date = user.subscription_end_date.date()
                
                if expires_at_date != end_date:
                    print(f"\n用户: {user.email}")
                    print(f"  - subscription_expires_at: {expires_at_date}")
                    print(f"  - subscription_end_date: {end_date}")
                    print(f"  - 将 subscription_end_date 更新为 subscription_expires_at 的值")
                    
                    user.subscription_end_date = user.subscription_expires_at
                    needs_update = True
            elif user.subscription_expires_at and not user.subscription_end_date:
                print(f"\n用户: {user.email}")
                print(f"  - subscription_expires_at: {user.subscription_expires_at.date()}")
                print(f"  - subscription_end_date: None")
                print(f"  - 将 subscription_end_date 设置为 subscription_expires_at 的值")
                
                user.subscription_end_date = user.subscription_expires_at
                needs_update = True
            
            # 如果是企业会员，同步更新企业的订阅到期时间
            if needs_update and user.membership_type == "enterprise":
                company = db.query(Company).filter(Company.owner_id == user.id).first()
                if company:
                    company.subscription_end_date = user.subscription_end_date
                    print(f"  - 同步更新企业 {company.name} 的订阅到期时间")
            
            if needs_update:
                user.updated_at = datetime.utcnow()
                db.commit()
                updated_count += 1
        
        print("\n" + "=" * 80)
        print(f"同步完成！共更新 {updated_count} 个用户")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_subscription_dates()

