"""
测试企业会员等级更新功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.company import Company
from datetime import datetime

def test_enterprise_tier_update():
    """测试企业会员等级更新"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("测试企业会员等级更新")
        print("=" * 80)
        
        # 查找 testuser176070001@example.com
        user = db.query(User).filter(User.email == "testuser176070001@example.com").first()
        
        if not user:
            print("❌ 未找到用户 testuser176070001@example.com")
            return
        
        print(f"\n用户信息:")
        print(f"  - 邮箱: {user.email}")
        print(f"  - 会员等级: {user.member_tier}")
        print(f"  - 会员类型: {user.membership_type}")
        print(f"  - 订阅状态: {user.subscription_status}")
        print(f"  - 订阅开始日期: {user.subscription_start_date}")
        print(f"  - 订阅结束日期: {user.subscription_end_date}")
        
        # 查找用户的企业
        company = db.query(Company).filter(Company.owner_id == user.id).first()
        
        if not company:
            print("\n❌ 未找到用户的企业")
            return
        
        print(f"\n企业信息:")
        print(f"  - 企业ID: {company.id}")
        print(f"  - 企业名称: {company.name}")
        print(f"  - 会员等级: {company.membership_tier}")
        print(f"  - 最大员工数: {company.max_employees}")
        print(f"  - 最大工厂数: {company.max_factories}")
        print(f"  - 最大WPS记录: {company.max_wps_records}")
        print(f"  - 最大PQR记录: {company.max_pqr_records}")
        print(f"  - 订阅状态: {company.subscription_status}")
        print(f"  - 订阅开始日期: {company.subscription_start_date}")
        print(f"  - 订阅结束日期: {company.subscription_end_date}")
        
        # 验证配额是否正确
        print("\n" + "=" * 80)
        print("验证配额设置")
        print("=" * 80)
        
        expected_quotas = {
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
        
        if company.membership_tier in expected_quotas:
            expected = expected_quotas[company.membership_tier]
            
            checks = [
                ("员工配额", company.max_employees, expected["max_employees"]),
                ("工厂配额", company.max_factories, expected["max_factories"]),
                ("WPS配额", company.max_wps_records, expected["max_wps_records"]),
                ("PQR配额", company.max_pqr_records, expected["max_pqr_records"])
            ]
            
            all_correct = True
            for name, actual, expected_val in checks:
                if actual == expected_val:
                    print(f"✅ {name}: {actual} (正确)")
                else:
                    print(f"❌ {name}: {actual} (应为 {expected_val})")
                    all_correct = False
            
            if all_correct:
                print("\n✅ 所有配额设置正确！")
            else:
                print("\n❌ 配额设置有误，需要修复")
        
        # 验证订阅到期时间
        print("\n" + "=" * 80)
        print("验证订阅到期时间")
        print("=" * 80)
        
        if user.subscription_end_date and company.subscription_end_date:
            user_end = user.subscription_end_date.strftime('%Y-%m-%d')
            company_end = company.subscription_end_date.strftime('%Y-%m-%d')
            
            print(f"用户订阅到期时间: {user_end}")
            print(f"企业订阅到期时间: {company_end}")
            
            if user_end == company_end:
                print("✅ 用户和企业的订阅到期时间一致")
            else:
                print("❌ 用户和企业的订阅到期时间不一致")
        else:
            print("⚠️  用户或企业的订阅到期时间未设置")
            if not user.subscription_end_date:
                print("   - 用户订阅到期时间: None")
            if not company.subscription_end_date:
                print("   - 企业订阅到期时间: None")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_enterprise_tier_update()

