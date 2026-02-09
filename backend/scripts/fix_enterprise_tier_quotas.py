"""
修复企业会员等级配额和订阅到期时间
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from datetime import datetime

def fix_enterprise_tier_quotas():
    """修复企业会员等级配额和订阅到期时间"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("修复企业会员等级配额和订阅到期时间")
        print("=" * 80)
        
        # 定义配额标准
        tier_limits = {
            "enterprise": {
                "max_employees": 10,
                "max_factories": 1,
                "max_wps_records": 200,
                "max_pqr_records": 200
            },
            "enterprise_pro": {
                "max_employees": 20,
                "max_factories": 3,
                "max_wps_records": 400,
                "max_pqr_records": 400
            },
            "enterprise_pro_max": {
                "max_employees": 50,
                "max_factories": 5,
                "max_wps_records": 500,
                "max_pqr_records": 500
            }
        }
        
        # 查找所有企业会员用户
        enterprise_users = db.query(User).filter(
            User.membership_type == "enterprise"
        ).all()
        
        print(f"\n找到 {len(enterprise_users)} 个企业会员用户")
        
        updated_count = 0
        
        for user in enterprise_users:
            # 查找用户的企业
            company = db.query(Company).filter(Company.owner_id == user.id).first()
            
            if not company:
                print(f"\n⚠️  用户 {user.email} 没有企业记录，跳过")
                continue
            
            print(f"\n处理用户: {user.email}")
            print(f"  - 用户会员等级: {user.member_tier}")
            print(f"  - 企业会员等级: {company.membership_tier}")
            
            needs_update = False
            update_data = {}
            
            # 检查会员等级是否一致
            if user.member_tier != company.membership_tier:
                print(f"  ⚠️  会员等级不一致，将企业等级更新为 {user.member_tier}")
                update_data["membership_tier"] = user.member_tier
                needs_update = True
            
            # 检查配额是否正确
            if user.member_tier in tier_limits:
                expected = tier_limits[user.member_tier]
                
                if company.max_employees != expected["max_employees"]:
                    print(f"  ⚠️  员工配额不正确: {company.max_employees} -> {expected['max_employees']}")
                    update_data["max_employees"] = expected["max_employees"]
                    needs_update = True
                
                if company.max_factories != expected["max_factories"]:
                    print(f"  ⚠️  工厂配额不正确: {company.max_factories} -> {expected['max_factories']}")
                    update_data["max_factories"] = expected["max_factories"]
                    needs_update = True
                
                if company.max_wps_records != expected["max_wps_records"]:
                    print(f"  ⚠️  WPS配额不正确: {company.max_wps_records} -> {expected['max_wps_records']}")
                    update_data["max_wps_records"] = expected["max_wps_records"]
                    needs_update = True
                
                if company.max_pqr_records != expected["max_pqr_records"]:
                    print(f"  ⚠️  PQR配额不正确: {company.max_pqr_records} -> {expected['max_pqr_records']}")
                    update_data["max_pqr_records"] = expected["max_pqr_records"]
                    needs_update = True
            
            # 检查订阅到期时间是否一致
            if user.subscription_end_date and company.subscription_end_date:
                user_end = user.subscription_end_date.date()
                company_end = company.subscription_end_date.date()
                
                if user_end != company_end:
                    print(f"  ⚠️  订阅到期时间不一致:")
                    print(f"     用户: {user_end}")
                    print(f"     企业: {company_end}")
                    print(f"     将企业到期时间更新为用户的到期时间")
                    update_data["subscription_end_date"] = user.subscription_end_date
                    needs_update = True
            elif user.subscription_end_date and not company.subscription_end_date:
                print(f"  ⚠️  企业没有订阅到期时间，将设置为用户的到期时间")
                update_data["subscription_end_date"] = user.subscription_end_date
                needs_update = True
            
            # 执行更新
            if needs_update:
                for key, value in update_data.items():
                    setattr(company, key, value)
                
                company.updated_at = datetime.utcnow()
                db.commit()
                
                print(f"  ✅ 企业 {company.name} 已更新")
                updated_count += 1
            else:
                print(f"  ✅ 企业 {company.name} 配额和到期时间正确，无需更新")
        
        print("\n" + "=" * 80)
        print(f"修复完成！共更新 {updated_count} 个企业")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_enterprise_tier_quotas()

