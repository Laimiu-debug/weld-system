#!/usr/bin/env python3
"""
测试会员等级自动切换逻辑

测试场景：
1. 用户购买低等级会员（1年）
2. 用户购买高等级会员（1个月）
3. 验证当前会员等级为高等级
4. 模拟高等级会员到期
5. 验证自动切换到低等级会员
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan
from app.services.membership_tier_service import MembershipTierService


def create_test_user(db):
    """创建测试用户"""
    # 检查是否已存在测试用户
    test_user = db.query(User).filter(User.email == "test_tier_switch@example.com").first()
    
    if test_user:
        print(f"✓ 使用现有测试用户: {test_user.email} (ID: {test_user.id})")
        return test_user
    
    # 创建新测试用户
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    test_user = User(
        email="test_tier_switch@example.com",
        username="test_tier_switch",
        hashed_password=pwd_context.hash("test123"),
        full_name="测试用户-会员切换",
        member_tier="free",
        membership_type="personal",
        subscription_status="inactive",
        is_active=True
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    print(f"✓ 创建测试用户: {test_user.email} (ID: {test_user.id})")
    return test_user


def clear_user_subscriptions(db, user_id):
    """清除用户的所有订阅"""
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    db.commit()
    print(f"✓ 清除用户 {user_id} 的所有订阅")


def create_subscription(db, user_id, plan_id, duration_months, start_offset_days=0):
    """
    创建订阅
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        plan_id: 套餐ID
        duration_months: 订阅时长（月）
        start_offset_days: 开始时间偏移（天，负数表示过去）
    """
    now = datetime.utcnow()
    start_date = now + timedelta(days=start_offset_days)
    end_date = start_date + timedelta(days=duration_months * 30)
    
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="active",
        billing_cycle="monthly" if duration_months == 1 else "yearly",
        price=99.0 if duration_months == 1 else 999.0,
        currency="CNY",
        start_date=start_date,
        end_date=end_date,
        auto_renew=False
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    print(f"✓ 创建订阅: {plan_id}, 时长: {duration_months}个月, 到期: {end_date.strftime('%Y-%m-%d')}")
    return subscription


def print_user_tier_info(db, user_id):
    """打印用户会员等级信息"""
    tier_service = MembershipTierService(db)
    summary = tier_service.get_user_subscription_summary(user_id)
    
    print("\n" + "="*60)
    print("当前会员等级信息:")
    print("="*60)
    print(f"当前等级: {summary['current_tier']}")
    
    if summary['current_subscription']:
        sub = summary['current_subscription']
        print(f"当前订阅: {sub['plan_id']} (优先级: {sub['priority']})")
        print(f"  到期时间: {sub['end_date']}")
    else:
        print("当前订阅: 无")
    
    if summary['next_subscription']:
        sub = summary['next_subscription']
        print(f"次高订阅: {sub['plan_id']} (优先级: {sub['priority']})")
        print(f"  到期时间: {sub['end_date']}")
    else:
        print("次高订阅: 无")
    
    print(f"\n所有有效订阅数量: {len(summary['all_active_subscriptions'])}")
    for i, sub in enumerate(summary['all_active_subscriptions'], 1):
        print(f"  {i}. {sub['plan_id']} (优先级: {sub['priority']}, 到期: {sub['end_date']})")
    print("="*60 + "\n")


def test_scenario_1():
    """
    测试场景1: 先购买低等级长期会员，再购买高等级短期会员
    
    步骤：
    1. 购买 personal_pro (1年)
    2. 购买 personal_flagship (1个月)
    3. 验证当前等级为 personal_flagship
    4. 模拟 personal_flagship 到期
    5. 验证自动切换到 personal_pro
    """
    print("\n" + "🧪 " + "="*58)
    print("测试场景1: 先购买低等级长期会员，再购买高等级短期会员")
    print("="*60 + "\n")
    
    db = SessionLocal()
    try:
        # 1. 创建测试用户
        user = create_test_user(db)
        clear_user_subscriptions(db, user.id)
        
        tier_service = MembershipTierService(db)
        
        # 2. 购买 personal_pro (1年)
        print("\n步骤1: 购买 personal_pro (1年)")
        sub_pro = create_subscription(db, user.id, "personal_pro", 12)
        
        # 更新用户等级
        result = tier_service.update_user_tier(user.id)
        print(f"✓ 会员等级更新: {result['old_tier']} -> {result['new_tier']}")
        print_user_tier_info(db, user.id)
        
        assert result['new_tier'] == 'personal_pro', "应该是 personal_pro"
        
        # 3. 购买 personal_flagship (1个月)
        print("\n步骤2: 购买 personal_flagship (1个月)")
        sub_flagship = create_subscription(db, user.id, "personal_flagship", 1)
        
        # 更新用户等级
        result = tier_service.update_user_tier(user.id)
        print(f"✓ 会员等级更新: {result['old_tier']} -> {result['new_tier']}")
        print_user_tier_info(db, user.id)
        
        assert result['new_tier'] == 'personal_flagship', "应该是 personal_flagship"
        assert result['next_subscription'] is not None, "应该有次高等级订阅"
        assert result['next_subscription'].plan_id == 'personal_pro', "次高等级应该是 personal_pro"
        
        # 4. 模拟 personal_flagship 到期
        print("\n步骤3: 模拟 personal_flagship 到期")
        sub_flagship.end_date = datetime.utcnow() - timedelta(days=1)
        # 不修改status,让check_and_switch_expired_subscriptions来处理
        db.commit()
        print(f"✓ 将 personal_flagship 订阅的到期时间设置为过去")
        
        # 5. 运行自动切换逻辑
        print("\n步骤4: 运行自动切换逻辑")
        results = tier_service.check_and_switch_expired_subscriptions()
        
        for result in results:
            if result['user_id'] == user.id:
                print(f"✓ 会员等级自动切换: {result['old_tier']} -> {result['new_tier']}")
                assert result['new_tier'] == 'personal_pro', "应该自动切换到 personal_pro"
                assert result['changed'] == True, "等级应该发生变化"
        
        print_user_tier_info(db, user.id)
        
        print("\n✅ 测试场景1通过！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        raise
    finally:
        db.close()


def test_scenario_2():
    """
    测试场景2: 购买多个不同等级的会员
    
    步骤：
    1. 购买 personal_pro (6个月)
    2. 购买 personal_advanced (3个月)
    3. 购买 personal_flagship (1个月)
    4. 验证当前等级为 personal_flagship
    5. 模拟 personal_flagship 到期，验证切换到 personal_advanced
    6. 模拟 personal_advanced 到期，验证切换到 personal_pro
    7. 模拟 personal_pro 到期，验证切换到 free
    """
    print("\n" + "🧪 " + "="*58)
    print("测试场景2: 购买多个不同等级的会员")
    print("="*60 + "\n")
    
    db = SessionLocal()
    try:
        # 1. 创建测试用户
        user = create_test_user(db)
        clear_user_subscriptions(db, user.id)
        
        tier_service = MembershipTierService(db)
        
        # 2. 购买三个不同等级的会员
        print("\n步骤1: 购买三个不同等级的会员")
        create_subscription(db, user.id, "personal_pro", 6)
        create_subscription(db, user.id, "personal_advanced", 3)
        create_subscription(db, user.id, "personal_flagship", 1)
        
        result = tier_service.update_user_tier(user.id)
        print(f"✓ 会员等级更新: {result['old_tier']} -> {result['new_tier']}")
        print_user_tier_info(db, user.id)
        
        assert result['new_tier'] == 'personal_flagship', "应该是 personal_flagship"
        
        # 3. 模拟 personal_flagship 到期
        print("\n步骤2: 模拟 personal_flagship 到期")
        flagship_sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.plan_id == 'personal_flagship'
        ).first()
        flagship_sub.end_date = datetime.utcnow() - timedelta(days=1)
        # 不修改status,让check_and_switch_expired_subscriptions来处理
        db.commit()

        results = tier_service.check_and_switch_expired_subscriptions()
        print_user_tier_info(db, user.id)

        # 刷新用户对象以获取最新数据
        db.expire_all()
        user = db.query(User).filter(User.id == user.id).first()
        assert user.member_tier == 'personal_advanced', f"应该切换到 personal_advanced，实际为 {user.member_tier}"
        
        # 4. 模拟 personal_advanced 到期
        print("\n步骤3: 模拟 personal_advanced 到期")
        advanced_sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.plan_id == 'personal_advanced'
        ).first()
        advanced_sub.end_date = datetime.utcnow() - timedelta(days=1)
        # 不修改status,让check_and_switch_expired_subscriptions来处理
        db.commit()

        tier_service.check_and_switch_expired_subscriptions()
        print_user_tier_info(db, user.id)

        # 刷新用户对象以获取最新数据
        db.expire_all()
        user = db.query(User).filter(User.id == user.id).first()
        assert user.member_tier == 'personal_pro', f"应该切换到 personal_pro，实际为 {user.member_tier}"
        
        # 5. 模拟 personal_pro 到期
        print("\n步骤4: 模拟 personal_pro 到期")
        pro_sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.plan_id == 'personal_pro'
        ).first()
        pro_sub.end_date = datetime.utcnow() - timedelta(days=1)
        # 不修改status,让check_and_switch_expired_subscriptions来处理
        db.commit()

        tier_service.check_and_switch_expired_subscriptions()
        print_user_tier_info(db, user.id)

        # 刷新用户对象以获取最新数据
        db.expire_all()
        user = db.query(User).filter(User.id == user.id).first()
        assert user.member_tier == 'free', f"应该切换到 free，实际为 {user.member_tier}"
        
        print("\n✅ 测试场景2通过！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("会员等级自动切换逻辑测试")
    print("="*60)
    
    try:
        # 运行测试场景
        test_scenario_1()
        test_scenario_2()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ 测试失败: {e}")
        print("="*60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

