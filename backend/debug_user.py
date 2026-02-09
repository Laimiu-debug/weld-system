#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试用户会员信息"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.subscription import Subscription
from app.models.company import Company, CompanyEmployee

def debug_user(email: str):
    """调试用户信息"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ 用户不存在: {email}")
            return
        
        print("="*80)
        print(f"用户信息: {email}")
        print("="*80)
        print(f"  ID: {user.id}")
        print(f"  用户名: {user.username}")
        print(f"  会员等级 (member_tier): {user.member_tier}")
        print(f"  会员类型 (membership_type): {user.membership_type}")
        print(f"  订阅状态 (subscription_status): {user.subscription_status}")
        print(f"  订阅开始时间: {user.subscription_start_date}")
        print(f"  订阅结束时间: {user.subscription_end_date}")
        print()
        
        # 查询所有订阅
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).order_by(Subscription.created_at.desc()).all()
        
        print("="*80)
        print(f"订阅记录 (共 {len(subscriptions)} 条)")
        print("="*80)
        for i, sub in enumerate(subscriptions, 1):
            print(f"{i}. 订阅ID: {sub.id}")
            print(f"   套餐ID (plan_id): {sub.plan_id}")
            print(f"   状态 (status): {sub.status}")
            print(f"   计费周期: {sub.billing_cycle}")
            print(f"   价格: {sub.price} {sub.currency}")
            print(f"   开始时间: {sub.start_date}")
            print(f"   结束时间: {sub.end_date}")
            print(f"   创建时间: {sub.created_at}")
            print()
        
        # 查询企业信息
        company = db.query(Company).filter(
            Company.owner_id == user.id,
            Company.is_active == True
        ).first()
        
        if company:
            print("="*80)
            print("企业信息")
            print("="*80)
            print(f"  企业ID: {company.id}")
            print(f"  企业名称: {company.name}")
            print(f"  会员等级: {company.membership_tier}")
            print(f"  最大员工数: {company.max_employees}")
            print(f"  最大工厂数: {company.max_factories}")
            print()
            
            # 查询员工记录
            employee = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.user_id == user.id
            ).first()
            
            if employee:
                print(f"  员工记录: 存在 (角色: {employee.role})")
            else:
                print(f"  ❌ 员工记录: 不存在")
        else:
            print("="*80)
            print("企业信息: 无")
            print("="*80)
        
    finally:
        db.close()

if __name__ == "__main__":
    email = "testuser176070002@example.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    debug_user(email)

