"""检查企业员工关联"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.company import Company, CompanyEmployee
from app.models.user import User
from sqlalchemy import text

db = SessionLocal()
try:
    print('=' * 80)
    print('检查企业员工关联')
    print('=' * 80)
    
    # 查询 testuser176070001@example.com 用户
    user = db.query(User).filter(User.email == 'testuser176070001@example.com').first()
    
    if user:
        print(f'\n用户信息:')
        print(f'  ID: {user.id}')
        print(f'  邮箱: {user.email}')
        print(f'  会员等级: {user.member_tier}')
        print(f'  会员类型: {user.membership_type}')
        
        # 查询该用户是否是企业员工
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == user.id
        ).first()
        
        if employee:
            print(f'\n企业员工信息:')
            print(f'  员工ID: {employee.id}')
            print(f'  企业ID: {employee.company_id}')
            print(f'  状态: {employee.status}')
            print(f'  角色: {employee.role}')
            
            # 查询企业信息
            company = db.query(Company).filter(Company.id == employee.company_id).first()
            if company:
                print(f'\n关联企业信息:')
                print(f'  企业ID: {company.id}')
                print(f'  企业名称: {company.name}')
                print(f'  所有者ID: {company.owner_id}')
                print(f'  会员等级: {company.membership_tier}')
                print(f'  订阅状态: {company.subscription_status}')
                print(f'  订阅开始日期: {company.subscription_start_date}')
                print(f'  订阅结束日期: {company.subscription_end_date}')
                
                if company.owner_id == user.id:
                    print(f'\n  ✅ 该用户是企业所有者')
                else:
                    print(f'\n  ℹ️  该用户是企业员工（非所有者）')
        else:
            print(f'\n❌ 该用户不是任何企业的员工')
            
            # 查询该用户是否拥有企业
            owned_company = db.query(Company).filter(Company.owner_id == user.id).first()
            if owned_company:
                print(f'\n但该用户拥有企业:')
                print(f'  企业ID: {owned_company.id}')
                print(f'  企业名称: {owned_company.name}')
                print(f'  会员等级: {owned_company.membership_tier}')
                print(f'  订阅状态: {owned_company.subscription_status}')
                print(f'  订阅开始日期: {owned_company.subscription_start_date}')
                print(f'  订阅结束日期: {owned_company.subscription_end_date}')
    else:
        print('未找到该用户')
    
finally:
    db.close()

