"""
测试支付系统会员升级功能
验证支付确认后membership_type和企业记录是否正确更新

注意:此测试直接使用项目的PostgreSQL数据库,不创建独立测试数据库
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.company import Company, CompanyEmployee
from app.services.membership_tier_service import MembershipTierService


def setup_test_data(db):
    """设置测试数据"""
    print("\n" + "="*80)
    print("设置测试数据...")
    print("="*80)

    # 先检查并删除已存在的测试用户
    existing_user = db.query(User).filter(User.email == "payment@test.com").first()
    if existing_user:
        print(f"⚠️ 发现已存在的测试用户,先清理...")
        cleanup_test_data(db, existing_user.id)

    # 创建测试用户
    user = User(
        username="test_payment_user",
        email="payment@test.com",
        full_name="支付测试用户",
        hashed_password="test_hash",
        member_tier="free",
        membership_type="personal",
        subscription_status="inactive"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ 创建测试用户: {user.email}")
    print(f"   - 初始会员等级: {user.member_tier}")
    print(f"   - 初始会员类型: {user.membership_type}")

    # 注意: 假设订阅计划已经在数据库中存在
    # 如果不存在,需要先在数据库中创建订阅计划

    return user


def test_personal_tier_upgrade(db, user):
    """测试个人会员升级"""
    print("\n" + "="*80)
    print("测试场景1: 个人会员升级 (free -> personal_pro)")
    print("="*80)
    
    # 模拟支付确认流程: 创建订阅记录
    subscription = Subscription(
        user_id=user.id,
        plan_id="personal_pro",
        status="active",
        billing_cycle="monthly",
        price=99.00,
        currency="CNY",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    print(f"✅ 创建订阅记录: {subscription.plan_id}")
    
    # 使用MembershipTierService更新用户会员等级
    tier_service = MembershipTierService(db)
    result = tier_service.update_user_tier(user.id)
    
    print(f"\n会员等级更新结果:")
    print(f"   - 旧等级: {result['old_tier']}")
    print(f"   - 新等级: {result['new_tier']}")
    print(f"   - 是否变化: {result['changed']}")
    
    # 刷新用户数据
    db.expire_all()
    user = db.query(User).filter(User.id == user.id).first()
    
    print(f"\n用户信息验证:")
    print(f"   - member_tier: {user.member_tier}")
    print(f"   - membership_type: {user.membership_type}")
    print(f"   - subscription_status: {user.subscription_status}")
    
    # 验证结果
    assert user.member_tier == "personal_pro", f"❌ member_tier应为personal_pro, 实际为{user.member_tier}"
    assert user.membership_type == "personal", f"❌ membership_type应为personal, 实际为{user.membership_type}"
    assert user.subscription_status == "active", f"❌ subscription_status应为active, 实际为{user.subscription_status}"
    
    print(f"\n✅ 测试通过: 个人会员升级成功")
    
    return user


def test_enterprise_tier_upgrade(db, user):
    """测试企业会员升级"""
    print("\n" + "="*80)
    print("测试场景2: 企业会员升级 (personal_pro -> enterprise)")
    print("="*80)
    
    # 模拟支付确认流程: 创建企业版订阅记录
    subscription = Subscription(
        user_id=user.id,
        plan_id="enterprise",
        status="active",
        billing_cycle="monthly",
        price=999.00,
        currency="CNY",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    print(f"✅ 创建企业版订阅记录: {subscription.plan_id}")
    
    # 使用MembershipTierService更新用户会员等级
    tier_service = MembershipTierService(db)
    result = tier_service.update_user_tier(user.id)
    
    print(f"\n会员等级更新结果:")
    print(f"   - 旧等级: {result['old_tier']}")
    print(f"   - 新等级: {result['new_tier']}")
    print(f"   - 是否变化: {result['changed']}")
    
    # 刷新用户数据
    db.expire_all()
    user = db.query(User).filter(User.id == user.id).first()
    
    print(f"\n用户信息验证:")
    print(f"   - member_tier: {user.member_tier}")
    print(f"   - membership_type: {user.membership_type}")
    print(f"   - subscription_status: {user.subscription_status}")
    
    # 验证用户信息
    assert user.member_tier == "enterprise", f"❌ member_tier应为enterprise, 实际为{user.member_tier}"
    assert user.membership_type == "enterprise", f"❌ membership_type应为enterprise, 实际为{user.membership_type}"
    assert user.subscription_status == "active", f"❌ subscription_status应为active, 实际为{user.subscription_status}"
    
    print(f"✅ 用户信息验证通过")
    
    # 验证企业记录是否创建
    company = db.query(Company).filter(Company.owner_id == user.id).first()
    assert company is not None, "❌ 企业记录未创建"
    assert company.membership_tier == "enterprise", f"❌ 企业会员等级应为enterprise, 实际为{company.membership_tier}"
    
    print(f"\n企业信息验证:")
    print(f"   - 企业名称: {company.name}")
    print(f"   - 会员等级: {company.membership_tier}")
    print(f"   - 最大员工数: {company.max_employees}")
    print(f"   - 最大工厂数: {company.max_factories}")
    print(f"✅ 企业记录验证通过")
    
    # 验证员工记录是否创建
    employee = db.query(CompanyEmployee).filter(
        CompanyEmployee.company_id == company.id,
        CompanyEmployee.user_id == user.id
    ).first()
    assert employee is not None, "❌ 员工记录未创建"
    assert employee.role == "admin", f"❌ 员工角色应为admin, 实际为{employee.role}"
    
    print(f"\n员工信息验证:")
    print(f"   - 员工编号: {employee.employee_number}")
    print(f"   - 角色: {employee.role}")
    print(f"   - 状态: {employee.status}")
    print(f"✅ 员工记录验证通过")
    
    print(f"\n✅ 测试通过: 企业会员升级成功,企业和员工记录已创建")
    
    return user, company


def test_enterprise_tier_upgrade_to_pro(db, user, company):
    """测试企业会员升级到更高等级"""
    print("\n" + "="*80)
    print("测试场景3: 企业会员升级 (enterprise -> enterprise_pro)")
    print("="*80)
    
    # 模拟支付确认流程: 创建企业专业版订阅记录
    subscription = Subscription(
        user_id=user.id,
        plan_id="enterprise_pro",
        status="active",
        billing_cycle="monthly",
        price=1999.00,
        currency="CNY",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    print(f"✅ 创建企业专业版订阅记录: {subscription.plan_id}")
    
    # 使用MembershipTierService更新用户会员等级
    tier_service = MembershipTierService(db)
    result = tier_service.update_user_tier(user.id)
    
    print(f"\n会员等级更新结果:")
    print(f"   - 旧等级: {result['old_tier']}")
    print(f"   - 新等级: {result['new_tier']}")
    print(f"   - 是否变化: {result['changed']}")
    
    # 刷新数据
    db.expire_all()
    user = db.query(User).filter(User.id == user.id).first()
    company = db.query(Company).filter(Company.id == company.id).first()
    
    print(f"\n用户信息验证:")
    print(f"   - member_tier: {user.member_tier}")
    print(f"   - membership_type: {user.membership_type}")
    
    # 验证用户信息
    assert user.member_tier == "enterprise_pro", f"❌ member_tier应为enterprise_pro, 实际为{user.member_tier}"
    assert user.membership_type == "enterprise", f"❌ membership_type应为enterprise, 实际为{user.membership_type}"
    
    print(f"✅ 用户信息验证通过")
    
    # 验证企业配额是否更新
    print(f"\n企业配额验证:")
    print(f"   - 会员等级: {company.membership_tier}")
    print(f"   - 最大员工数: {company.max_employees}")
    print(f"   - 最大工厂数: {company.max_factories}")
    
    assert company.membership_tier == "enterprise_pro", f"❌ 企业会员等级应为enterprise_pro, 实际为{company.membership_tier}"
    assert company.max_employees == 20, f"❌ 最大员工数应为20, 实际为{company.max_employees}"
    assert company.max_factories == 3, f"❌ 最大工厂数应为3, 实际为{company.max_factories}"
    
    print(f"✅ 企业配额验证通过")
    
    print(f"\n✅ 测试通过: 企业会员升级成功,企业配额已更新")


def cleanup_test_data(db, user_id):
    """清理测试数据"""
    print("\n" + "="*80)
    print("清理测试数据...")
    print("="*80)

    # 删除员工记录
    db.query(CompanyEmployee).filter(CompanyEmployee.user_id == user_id).delete()

    # 删除企业记录
    db.query(Company).filter(Company.owner_id == user_id).delete()

    # 删除订阅记录
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()

    # 删除用户
    db.query(User).filter(User.id == user_id).delete()

    db.commit()
    print("✅ 测试数据已清理")


def main():
    """主测试函数"""
    db = SessionLocal()
    user_id = None

    try:
        # 设置测试数据
        user = setup_test_data(db)
        user_id = user.id

        # 测试1: 个人会员升级
        user = test_personal_tier_upgrade(db, user)

        # 测试2: 企业会员升级
        user, company = test_enterprise_tier_upgrade(db, user)

        # 测试3: 企业会员升级到更高等级
        test_enterprise_tier_upgrade_to_pro(db, user, company)

        print("\n" + "="*80)
        print("🎉 所有测试通过!")
        print("="*80)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        if user_id:
            try:
                cleanup_test_data(db, user_id)
            except Exception as e:
                print(f"⚠️ 清理测试数据时出错: {e}")

        db.close()


if __name__ == "__main__":
    main()

