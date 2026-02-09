#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清理测试用户的订阅数据"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTransaction
from app.models.company import Company, CompanyEmployee, Factory

def cleanup_test_user(email: str):
    """清理测试用户的所有订阅和企业数据"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ 用户不存在: {email}")
            return
        
        print(f"开始清理用户: {email} (ID: {user.id})")
        print("="*80)

        # 1. 获取所有订阅记录
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).all()

        # 2. 删除所有订阅交易记录
        transaction_count = 0
        for sub in subscriptions:
            transactions = db.query(SubscriptionTransaction).filter(
                SubscriptionTransaction.subscription_id == sub.id
            ).all()
            transaction_count += len(transactions)
            for trans in transactions:
                db.delete(trans)
        print(f"删除 {transaction_count} 条订阅交易记录...")

        # 3. 删除所有订阅记录
        print(f"删除 {len(subscriptions)} 条订阅记录...")
        for sub in subscriptions:
            db.delete(sub)
        
        # 4. 删除企业员工记录
        employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id
        ).all()
        print(f"删除 {len(employees)} 条员工记录...")
        for emp in employees:
            db.delete(emp)

        # 5. 删除企业拥有的工厂
        companies = db.query(Company).filter(
            Company.owner_id == user.id
        ).all()
        for company in companies:
            factories = db.query(Factory).filter(
                Factory.company_id == company.id
            ).all()
            print(f"删除企业 {company.name} 的 {len(factories)} 个工厂...")
            for factory in factories:
                db.delete(factory)

        # 6. 删除企业记录
        print(f"删除 {len(companies)} 条企业记录...")
        for company in companies:
            db.delete(company)

        # 7. 重置用户会员信息
        print("重置用户会员信息...")
        user.member_tier = "free"
        user.membership_type = "personal"
        user.subscription_status = "inactive"
        user.subscription_start_date = None
        user.subscription_end_date = None
        user.subscription_expires_at = None
        user.auto_renewal = False
        
        db.commit()
        
        print("="*80)
        print("✅ 清理完成!")
        print()
        print("用户当前状态:")
        print(f"  会员等级: {user.member_tier}")
        print(f"  会员类型: {user.membership_type}")
        print(f"  订阅状态: {user.subscription_status}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    email = "testuser176070002@example.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    confirm = input(f"确认要清理用户 {email} 的所有订阅和企业数据吗? (yes/no): ")
    if confirm.lower() == 'yes':
        cleanup_test_user(email)
    else:
        print("已取消")

